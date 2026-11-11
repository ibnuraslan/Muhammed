"""BelugaRescue scene: render settings, arctic tank, gallery, deck, water, lights, beluga (procedural + rig), diver gear.
blender -b work/people.blend --python 02_build_scene.py -- <assets_dir> <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
sc = bpy.context.scene
FPS, END = 60, 2190
R_ = math.radians
random.seed(22)
WATER_Z = 6.0
DECK_Z = 6.25
TX, TY = 6.0, 5.0          # tank half extents (x), (y)

# ------------------------------------------------------------------ timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, END, 1
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 8
c.volume_bounces = 1; c.volume_step_rate = 4.0; c.volume_max_steps = 256
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings
vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings
im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/BelugaRescue_"

# ------------------------------------------------------------------ helpers
def img(path, nc=False):
    if not os.path.exists(path):
        import glob
        d_, b_ = os.path.split(path); stem = os.path.splitext(b_)[0]
        path = (glob.glob(os.path.join(d_, "textures", stem + ".*")) + glob.glob(os.path.join(d_, stem + ".*")))[0]
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def pbr(name, folder, base, scale, tint=(1, 1, 1), sat=1.0, val=1.0, bump=1.0, rough_mul=1.0, coord='Object'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(os.path.join(folder, base + "_diff_2k.jpg"))
    r = n.new('ShaderNodeTexImage'); r.image = img(os.path.join(folder, base + "_rough_2k.jpg"), True)
    nm = n.new('ShaderNodeTexImage'); nm.image = img(os.path.join(folder, base + "_nor_gl_2k.jpg"), True)
    for t in (d, r, nm):
        t.projection = 'BOX'; t.projection_blend = 0.3
    nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    mx = n.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
    mx.inputs['B'].default_value = (*tint, 1)
    rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
    for a, b in ((mp.outputs['Vector'], d.inputs['Vector']), (mp.outputs['Vector'], r.inputs['Vector']), (mp.outputs['Vector'], nm.inputs['Vector']),
                 (d.outputs['Color'], hsv.inputs['Color']), (hsv.outputs['Color'], mx.inputs['A']), (mx.outputs['Result'], p.inputs['Base Color']),
                 (r.outputs['Color'], rm.inputs[0]), (rm.outputs[0], p.inputs['Roughness']),
                 (nm.outputs['Color'], nmap.inputs['Color']), (nmap.outputs['Normal'], p.inputs['Normal'])):
        l.new(a, b)
    return m

def simple_mat(name, rgb, rough=0.5, metal=0.0, trans=0.0, ior=1.45, emit=None, estr=0.0, sss=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Transmission Weight'].default_value = trans; p.inputs['IOR'].default_value = ior
    p.inputs['Subsurface Weight'].default_value = sss; p.inputs['Alpha'].default_value = alpha
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    return m

def link(o, coll=None):
    (coll or sc.collection).objects.link(o); return o

def box(name, x0, x1, y0, y1, z0, z1, mat=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    o = bpy.context.active_object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 3
    if mat: o.data.materials.append(mat)
    return o

def grid(name, sx, sy, nx, ny, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1)
    bpy.ops.object.transform_apply(scale=True, rotation=True, location=False)
    if mat: o.data.materials.append(mat)
    return o

PH = A
# ------------------------------------------------------------------ world: hall HDRI above water
w = bpy.data.worlds.new("World_Hall"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(PH, "hdri", "events_hall_interior_2k.hdr"))
bg = wn["Background"]; bg.inputs['Strength'].default_value = 0.8; bg.name = "SkyStrength"
tintw = wn.new('ShaderNodeMix'); tintw.data_type = 'RGBA'; tintw.blend_type = 'MULTIPLY'; tintw.inputs['Factor'].default_value = 1.0
tintw.inputs['B'].default_value = (0.85, 0.95, 1.05, 1); tintw.name = "SkyTint"
wl.new(env.outputs['Color'], tintw.inputs['A']); wl.new(tintw.outputs['Result'], bg.inputs['Color'])

# ------------------------------------------------------------------ materials
M_TILE = pbr("M_PoolTiles", os.path.join(PH, "long_white_tiles"), "long_white_tiles", 1.2, tint=(0.78, 0.92, 0.95), bump=0.8)
M_ICE = pbr("M_IceRock", os.path.join(PH, "rock_face_03"), "rock_face_03", 2.6, tint=(0.82, 0.92, 1.0), sat=0.15, val=1.35, bump=1.4, rough_mul=0.7)
# snow/frost on upward faces of the ice rock
nt = M_ICE.node_tree; n, l = nt.nodes, nt.links
p = n["Principled BSDF"]
snow = n.new('ShaderNodeTexImage'); snow.image = img(os.path.join(PH, "snow_02", "snow_02_diff_2k.jpg")); snow.projection = 'BOX'
tc = n.new('ShaderNodeTexCoord'); smp = n.new('ShaderNodeMapping'); smp.inputs['Scale'].default_value = (0.6, 0.6, 0.6)
l.new(tc.outputs['Object'], smp.inputs['Vector']); l.new(smp.outputs['Vector'], snow.inputs['Vector'])
geo = n.new('ShaderNodeNewGeometry'); sep = n.new('ShaderNodeSeparateXYZ'); l.new(geo.outputs['Normal'], sep.inputs['Vector'])
nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0
add = n.new('ShaderNodeMath'); add.operation = 'ADD'; l.new(sep.outputs['Z'], add.inputs[0]); l.new(nz.outputs['Fac'], add.inputs[1])
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.85; mr.inputs['From Max'].default_value = 1.2
l.new(add.outputs[0], mr.inputs['Value'])
smx = n.new('ShaderNodeMix'); smx.data_type = 'RGBA'
base_link = p.inputs['Base Color'].links[0].from_socket
l.new(mr.outputs['Result'], smx.inputs['Factor']); l.new(base_link, smx.inputs['A']); l.new(snow.outputs['Color'], smx.inputs['B'])
l.new(smx.outputs['Result'], p.inputs['Base Color'])
p.inputs['Subsurface Weight'].default_value = 0.15; p.inputs['Subsurface Radius'].default_value = (0.3, 0.5, 0.9)
M_CONC = pbr("M_Concrete", os.path.join(PH, "rock_face_03"), "rock_face_03", 6.0, tint=(0.75, 0.78, 0.8), sat=0.0, val=1.1, bump=0.25)
M_DECK = pbr("M_Deck", os.path.join(PH, "long_white_tiles"), "long_white_tiles", 0.8, tint=(0.62, 0.66, 0.68), bump=0.6, rough_mul=0.8)
M_ACRYL = simple_mat("M_Acrylic", (0.92, 0.97, 1.0), rough=0.02, trans=1.0, ior=1.49)
M_STEEL = simple_mat("M_Steel", (0.75, 0.76, 0.78), rough=0.25, metal=1.0)
M_GALLERY = simple_mat("M_GalleryWall", (0.06, 0.08, 0.11), rough=0.7)
M_GFLOOR = simple_mat("M_GalleryFloor", (0.09, 0.09, 0.1), rough=0.35)
M_RING = simple_mat("M_RingToy", (0.95, 0.38, 0.06), rough=0.45)
M_ICEFLOE = simple_mat("M_IceFloe", (0.85, 0.93, 1.0), rough=0.15, trans=0.6, ior=1.31, sss=0.3)

# ------------------------------------------------------------------ tank shell
TANK = bpy.data.collections.new("Tank"); sc.collection.children.link(TANK)
def mv(o, coll=TANK):
    for cl in list(o.users_collection): cl.objects.unlink(o)
    coll.objects.link(o); return o
floor = mv(grid("TankFloor", 2 * TX, 2 * TY, 2, 2, (0, 0, 0), mat=M_TILE))
# a drain grate + floor lane lines (detail)
mv(box("FloorDrain", -0.35, 0.35, 2.2, 2.9, -0.01, 0.004, simple_mat("M_Drain", (0.2, 0.22, 0.24), rough=0.4, metal=0.8)))
for i in range(-4, 5, 2):
    mv(box("FloorLine_%d" % i, i - 0.04, i + 0.04, -4.6, 4.6, -0.005, 0.0015, simple_mat("M_Line_%d" % i, (0.15, 0.32, 0.45), rough=0.3)))

def ice_wall(name, size_u, size_v, loc, rot, amp=0.55, seed=0):
    o = mv(grid(name, size_u, size_v, 90, 70, loc, rot, M_ICE))
    me = o.data
    nrm = (Matrix.Rotation(rot[2], 3, 'Z') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[0], 3, 'X')) @ Vector((0, 0, 1))
    for v in me.vertices:
        p_ = v.co + Vector((seed, seed * 0.7, 0))
        h = noise.fractal(p_ * 0.55, 0.6, 2.2, 5) * 0.6 + abs(noise.noise(p_ * 0.25)) * 1.0 + noise.noise(p_ * 2.5) * 0.08
        v.co += nrm * (amp * (0.4 + h))
    me.update()
    sm = o.modifiers.new("Sub", 'SUBSURF'); sm.levels = 1; sm.render_levels = 1
    for f_ in me.polygons: f_.use_smooth = True
    return o
H_ROCK = 7.8
ice_wall("IceWall_Back", 2 * TX + 1, H_ROCK, (0, TY + 0.6, H_ROCK / 2 - 0.2), (R_(90), 0, R_(180)), seed=1)
ice_wall("IceWall_L", 2 * TY + 1.4, H_ROCK, (-TX - 0.6, 0, H_ROCK / 2 - 0.2), (R_(90), 0, R_(-90)), seed=7)
ice_wall("IceWall_R", 2 * TY + 1.4, H_ROCK, (TX + 0.6, 0, H_ROCK / 2 - 0.2), (R_(90), 0, R_(90)), seed=13)
# boulders on the floor along the rock walls (mid-ground layers)
ROCKS = []
for i, (x, y, s) in enumerate([(-5.0, 3.8, 1.3), (-3.6, 4.4, 0.9), (4.8, 3.6, 1.5), (5.2, 0.5, 1.0), (-5.3, -1.2, 1.1), (2.6, 4.5, 0.8),
                               (-5.4, -3.6, 0.8), (5.3, -3.4, 0.9), (0.4, 4.6, 1.1)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=s, location=(x, y, s * 0.35))
    o = mv(bpy.context.active_object); o.name = "IceBoulder_%d" % i
    for v in o.data.vertices:
        v.co *= 1 + 0.28 * noise.fractal(v.co * 1.3 + Vector((i, i, i)), 0.6, 2.0, 4)
    o.scale = (1.0, 0.8, 0.75); o.rotation_euler.z = random.uniform(0, 6.28)
    o.data.materials.append(M_ICE); [setattr(f_, 'use_smooth', True) for f_ in o.data.polygons]
    ROCKS.append(o)

# front wall (concrete) with the viewing window; gallery behind
WIN = (-3.6, 3.6, 0.35, 3.15)        # x0, x1, z0, z1
WY0, WY1 = -TY - 0.45, -TY           # wall thickness in y
for nm, a in (("FrontWall_L", (-TX - 1, WIN[0], WY0, WY1, 0, DECK_Z)), ("FrontWall_R", (WIN[1], TX + 1, WY0, WY1, 0, DECK_Z)),
              ("FrontWall_Bot", (WIN[0], WIN[1], WY0, WY1, 0, WIN[2])), ("FrontWall_Top", (WIN[0], WIN[1], WY0, WY1, WIN[3], DECK_Z))):
    mv(box(nm, *a, mat=M_CONC))
acr = mv(box("Acrylic_Window", WIN[0], WIN[1], WY0 + 0.1, WY1 - 0.1, WIN[2], WIN[3], M_ACRYL))
# steel frame around the window
for nm, a in (("WinFrame_B", (WIN[0] - 0.08, WIN[1] + 0.08, WY1 - 0.02, WY1 + 0.03, WIN[2] - 0.08, WIN[2])),
              ("WinFrame_T", (WIN[0] - 0.08, WIN[1] + 0.08, WY1 - 0.02, WY1 + 0.03, WIN[3], WIN[3] + 0.08)),
              ("WinFrame_L", (WIN[0] - 0.08, WIN[0], WY1 - 0.02, WY1 + 0.03, WIN[2], WIN[3])),
              ("WinFrame_R", (WIN[1], WIN[1] + 0.08, WY1 - 0.02, WY1 + 0.03, WIN[2], WIN[3]))):
    mv(box(nm, *a, mat=M_STEEL))
GAL = bpy.data.collections.new("Gallery"); sc.collection.children.link(GAL)
mv(box("Gallery_Floor", -TX - 1, TX + 1, -9.5, WY0, -0.1, 0.0, M_GFLOOR), GAL)
mv(box("Gallery_Ceiling", -TX - 1, TX + 1, -9.5, WY0, 3.5, 3.6, M_GALLERY), GAL)
mv(box("Gallery_BackWall", -TX - 1, TX + 1, -9.6, -9.5, 0, 3.6, M_GALLERY), GAL)
for i, x in enumerate((-4.5, -1.5, 1.5, 4.5)):
    lg = bpy.data.lights.new("GalleryDown_%d" % i, 'AREA'); lg.energy = 60; lg.size = 0.6; lg.color = (1.0, 0.85, 0.65)
    lo = bpy.data.objects.new("GalleryDown_%d" % i, lg); lo.location = (x, -8.0, 3.45); GAL.objects.link(lo)
# bench in the gallery
mv(box("Gallery_Bench", -2.0, 2.0, -8.3, -7.8, 0.0, 0.45, simple_mat("M_Bench", (0.25, 0.18, 0.12), rough=0.5), bevel=0.02), GAL)

# deck above the front wall + coping + railing + ladder
mv(box("Deck", -TX - 1, TX + 1, -9.5, WY1, DECK_Z - 0.3, DECK_Z, M_DECK))
cop = mv(box("Coping", -TX - 1, TX + 1, WY1 - 0.05, WY1 + 0.14, DECK_Z - 0.35, DECK_Z + 0.06, simple_mat("M_Coping", (0.82, 0.83, 0.82), rough=0.45), bevel=0.05))
for i, x in enumerate([x * 0.5 for x in range(-12, 13)]):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.025, depth=1.0, location=(x, -6.4, DECK_Z + 0.5))
    o = mv(bpy.context.active_object); o.name = "Rail_Post_%d" % i; o.data.materials.append(M_STEEL)
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.03, depth=13.0, location=(0, -6.4, DECK_Z + 1.0), rotation=(0, R_(90), 0))
o = mv(bpy.context.active_object); o.name = "Rail_Top"; o.data.materials.append(M_STEEL)
# ladder on the front wall (x = 3.8)
for sx in (-0.22, 0.22):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.022, depth=4.0, location=(4.4 + sx, WY1 + 0.12, DECK_Z - 1.6))
    o = mv(bpy.context.active_object); o.name = "Ladder_Rail"; o.data.materials.append(M_STEEL)
for k in range(9):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.016, depth=0.44, location=(4.4, WY1 + 0.12, DECK_Z - 0.3 - k * 0.38), rotation=(0, R_(90), 0))
    o = mv(bpy.context.active_object); o.name = "Ladder_Rung_%d" % k; o.data.materials.append(M_STEEL)
# hall structure above (walls of the building beyond the rock, roof trusses) — the HDRI does the rest
for i, x in enumerate(range(-8, 9, 4)):
    mv(box("Truss_%d" % i, x - 0.1, x + 0.1, -10, 7, 12.0, 12.4, simple_mat("M_Truss_%d" % i, (0.3, 0.32, 0.35), rough=0.5, metal=0.6)))

# ------------------------------------------------------------------ water: volume + surface + floes
WAT = bpy.data.collections.new("Water"); sc.collection.children.link(WAT)
vol = mv(box("Water_Volume", -TX - 1.2, TX + 1.2, WY1 - 0.02, TY + 1.2, -0.05, WATER_Z), WAT)
vm = bpy.data.materials.new("M_WaterVolume"); vm.use_nodes = True
vn, vl = vm.node_tree.nodes, vm.node_tree.links
vn.remove(vn["Principled BSDF"])
pv = vn.new('ShaderNodeVolumePrincipled'); pv.name = "WaterVol"
pv.inputs['Color'].default_value = (0.45, 0.85, 1.0, 1); pv.inputs['Density'].default_value = 0.03
pv.inputs['Anisotropy'].default_value = 0.65; pv.inputs['Absorption Color'].default_value = (0.08, 0.45, 0.62, 1)
vl.new(pv.outputs['Volume'], vn["Material Output"].inputs['Volume'])
vol.data.materials.append(vm)
vol.visible_shadow = True
# surface: ocean modifier on a plane (procedural; time keyed in 03)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, WATER_Z))
surf = mv(bpy.context.active_object, WAT); surf.name = "Water_Surface"
om = surf.modifiers.new("Ocean", 'OCEAN'); om.geometry_mode = 'GENERATE'; om.size = 1.0; om.spatial_size = 16; om.resolution = 10
om.repeat_x = om.repeat_y = 1; om.wave_scale = 0.14; om.choppiness = 0.9; om.wind_velocity = 4.0; om.random_seed = 3
sm_ = bpy.data.materials.new("M_WaterSurface"); sm_.use_nodes = True
sp = sm_.node_tree.nodes["Principled BSDF"]; sp.inputs['Base Color'].default_value = (0.85, 0.97, 1.0, 1)
sp.inputs['Roughness'].default_value = 0.06; sp.inputs['Transmission Weight'].default_value = 1.0; sp.inputs['IOR'].default_value = 1.333
surf.data.materials.append(sm_)
surf.visible_shadow = False          # caustics off: let light through, the gobo spot paints caustics
for i in range(9):
    x, y = random.uniform(-5, 5), random.uniform(-1.5, 4.2)
    if abs(x) < 2.0 and y < -2.5: continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(0.18, 0.4), location=(x, y, WATER_Z + 0.02))
    o = mv(bpy.context.active_object, WAT); o.name = "IceFloe_%d" % i; o.scale = (1.0, random.uniform(0.6, 1.0), 0.22)
    for v in o.data.vertices: v.co *= 1 + 0.2 * noise.noise(v.co * 3 + Vector((i, 0, 0)))
    o.data.materials.append(M_ICEFLOE); [setattr(f_, 'use_smooth', True) for f_ in o.data.polygons]

# ------------------------------------------------------------------ props: ring toy
bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.045, major_segments=40, minor_segments=14, location=(-2.6, -3.0, 2.2))
ring = bpy.context.active_object; ring.name = "RingToy"; ring.data.materials.append(M_RING)
[setattr(f_, 'use_smooth', True) for f_ in ring.data.polygons]

# ------------------------------------------------------------------ lights
LIG = bpy.data.collections.new("Lights"); sc.collection.children.link(LIG)
def light(name, typ, loc, rot, energy, color=(1, 1, 1), **kw):
    ld = bpy.data.lights.new(name, typ); ld.energy = energy; ld.color = color
    for k, v in kw.items(): setattr(ld, k, v)
    o = bpy.data.objects.new(name, ld); o.location = loc; o.rotation_euler = rot; LIG.objects.link(o); return o
key = light("Key_Sun", 'SUN', (0, 0, 15), (R_(18), R_(-10), 0), 3.2, (0.92, 0.97, 1.0), angle=R_(2))
# caustic gobo spot (voronoi on the light's normal) — W animated in 03
cau = light("Caustic_Spot", 'SPOT', (0.5, -1.0, 13.5), (0, 0, 0), 9000, (0.85, 0.97, 1.0), spot_size=R_(75), spot_blend=0.4, shadow_soft_size=0.05)
cau.data.use_nodes = True
cn, cl_ = cau.data.node_tree.nodes, cau.data.node_tree.links
ctc = cn.new('ShaderNodeTexCoord'); cvor = cn.new('ShaderNodeTexVoronoi'); cvor.voronoi_dimensions = '4D'; cvor.feature = 'SMOOTH_F1'
cvor.name = "CausticVoronoi"; cvor.inputs['Scale'].default_value = 26.0; cvor.inputs['Smoothness'].default_value = 0.6
cvor.distance = 'EUCLIDEAN'
cpow = cn.new('ShaderNodeMath'); cpow.operation = 'POWER'; cpow.inputs[1].default_value = 3.0
cmul = cn.new('ShaderNodeMath'); cmul.operation = 'MULTIPLY'; cmul.inputs[1].default_value = 3.0
cl_.new(ctc.outputs['Normal'], cvor.inputs['Vector']); cl_.new(cvor.outputs['Distance'], cpow.inputs[0]); cl_.new(cpow.outputs[0], cmul.inputs[0])
cl_.new(cmul.outputs[0], cn["Emission"].inputs['Strength'])
# light shafts through the volume
SHAFTS = []
for i, (x, y, rx, ry) in enumerate([(-2.2, 0.5, 8, -10), (1.6, -1.8, -6, 8), (3.4, 2.2, 10, 6), (-0.4, 3.0, -8, -4), (-4.0, -2.4, 4, 12)]):
    SHAFTS.append(light("Shaft_%d" % i, 'SPOT', (x, y, 14.0), (R_(rx), R_(ry), 0), 5200, (0.88, 0.97, 1.0), spot_size=R_(7), spot_blend=0.5, shadow_soft_size=0.15))
fill = light("Underwater_Fill", 'AREA', (0, -2.0, 2.5), (R_(80), 0, 0), 400, (0.45, 0.8, 0.95), size=8.0)
fill.data.cycles.is_caustics_light = False
deckfill = light("Deck_Fill", 'AREA', (0, -8.0, 10.0), (R_(30), 0, 0), 900, (1.0, 0.92, 0.82), size=6.0)

# ------------------------------------------------------------------ beluga (procedural): head toward -Y, origin at mid-body
L_W = 4.3
def prof(s):
    """(half width, top height, bottom depth, centre z) at s = 0 snout .. 1 fluke notch"""
    def lerp_tab(tab):
        for (s0, v0), (s1, v1) in zip(tab, tab[1:]):
            if s <= s1:
                t = (s - s0) / (s1 - s0); t = t * t * (3 - 2 * t); return v0 + (v1 - v0) * t
        return tab[-1][1]
    wv = lerp_tab([(0, 0.02), (0.025, 0.09), (0.06, 0.15), (0.1, 0.25), (0.16, 0.31), (0.21, 0.27), (0.3, 0.40), (0.42, 0.46),
                   (0.55, 0.42), (0.68, 0.28), (0.8, 0.12), (0.88, 0.065), (0.94, 0.05), (1.0, 0.03)])
    top = lerp_tab([(0, 0.02), (0.025, 0.06), (0.045, 0.13), (0.08, 0.29), (0.13, 0.35), (0.19, 0.27), (0.24, 0.29), (0.4, 0.40),
                    (0.55, 0.37), (0.68, 0.27), (0.8, 0.16), (0.88, 0.10), (0.94, 0.06), (1.0, 0.035)])
    bot = lerp_tab([(0, 0.02), (0.025, 0.06), (0.06, 0.11), (0.12, 0.19), (0.2, 0.24), (0.3, 0.34), (0.42, 0.42), (0.55, 0.36),
                    (0.68, 0.24), (0.8, 0.13), (0.88, 0.085), (0.94, 0.055), (1.0, 0.03)])
    cz = lerp_tab([(0, -0.06), (0.06, -0.06), (0.15, -0.02), (0.4, 0.0), (0.8, 0.02), (1.0, 0.03)])
    return wv, top, bot, cz
NS, NR = 72, 28
bm = bmesh.new()
rings = []
for i in range(NS + 1):
    s = (i / NS) ** 1.0
    wv, top, bot, cz = prof(s)
    y = -L_W * 0.42 + s * L_W * 0.94          # snout at -0.42 L, notch at +0.52 L
    ring_ = []
    for j in range(NR):
        a = 2 * math.pi * j / NR
        cx, cyz = math.sin(a), math.cos(a)
        hz = top if cyz > 0 else bot
        # superellipse-ish to keep the belly fuller
        ring_.append(bm.verts.new((wv * cx, y, cz + hz * cyz)))
    rings.append(ring_)
for i in range(NS):
    for j in range(NR):
        bm.faces.new((rings[i][j], rings[i][(j + 1) % NR], rings[i + 1][(j + 1) % NR], rings[i + 1][j]))
tip = bm.verts.new((0, -L_W * 0.42 - 0.01, prof(0)[3])); end = bm.verts.new((0, L_W * 0.52 + 0.01, prof(1)[3]))
for j in range(NR):
    bm.faces.new((rings[0][(j + 1) % NR], rings[0][j], tip)); bm.faces.new((rings[NS][j], rings[NS][(j + 1) % NR], end))
bme = bpy.data.meshes.new("Beluga_Body"); bm.to_mesh(bme); bm.free()
bel = bpy.data.objects.new("Beluga", bme); link(bel)
def flat_part(name, outline, thick, loc, rot):
    """flattened lofted blade from a 2D outline [(u, v_half_width)] along local Y; thickness tapers to the edge"""
    bm = bmesh.new(); prev = None; NRr = 12
    for (u, hw) in outline:
        r_ = []
        for j in range(NRr):
            a = 2 * math.pi * j / NRr
            r_.append(bm.verts.new((hw * math.cos(a), u, thick * max(0.15, hw / max(1e-3, max(o[1] for o in outline))) * math.sin(a))))
        if prev:
            for j in range(NRr):
                bm.faces.new((prev[j], prev[(j + 1) % NRr], r_[(j + 1) % NRr], r_[j]))
        prev = r_
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.transform(Matrix.Translation(loc) @ rot.to_4x4())
    return me
# flukes: spread along X, swept back
fl_bm = bmesh.new()
def fluke_half(side):
    pts = []
    for k in range(13):
        t = k / 12
        x = side * (0.06 + t * 0.55)
        lead = L_W * 0.47 + t * 0.20 + 0.05 * t * t
        trail = L_W * 0.53 + t * 0.06 - 0.12 * math.sin(t * math.pi) * 0.0 + (0.13 * t if t > 0.6 else 0)
        trail = max(trail, lead + 0.03)
        thick = 0.045 * (1 - t) + 0.006
        pts.append((x, lead, trail, thick))
    return pts
for side in (-1, 1):
    pts = fluke_half(side); prev = None
    for (x, y0, y1, th) in pts:
        cy = (y0 + y1) / 2; hl = (y1 - y0) / 2
        r_ = [fl_bm.verts.new((x, cy + hl * math.cos(2 * math.pi * j / 10), prof(1)[3] + th * math.sin(2 * math.pi * j / 10))) for j in range(10)]
        if prev:
            for j in range(10):
                f_ = (prev[j], prev[(j + 1) % 10], r_[(j + 1) % 10], r_[j])
                fl_bm.faces.new(f_ if side > 0 else f_[::-1])
        prev = r_
fme = bpy.data.meshes.new("Beluga_Flukes"); fl_bm.to_mesh(fme); fl_bm.free()
fobj = bpy.data.objects.new("Beluga_Flukes", fme); link(fobj)
fl_objs = [fobj]
for side in (-1, 1):
    outline = [(0.0, 0.055), (0.06, 0.085), (0.15, 0.09), (0.24, 0.075), (0.32, 0.045), (0.37, 0.012)]
    me = flat_part("Beluga_Flipper", outline, 0.03, Vector((side * 0.36, -L_W * 0.42 + 0.27 * L_W, -0.2)),
                   Matrix.Rotation(R_(side * 115), 3, 'Z') @ Matrix.Rotation(R_(side * -25), 3, 'Y'))
    fo = bpy.data.objects.new("Beluga_Flipper", me); link(fo); fl_objs.append(fo)
for o in bpy.data.objects: o.select_set(False)
for o in fl_objs + [bel]: o.select_set(True)
bpy.context.view_layer.objects.active = bel; bpy.ops.object.join()
bm_n = bmesh.new(); bm_n.from_mesh(bel.data); bmesh.ops.recalc_face_normals(bm_n, faces=bm_n.faces); bm_n.to_mesh(bel.data); bm_n.free()
for f_ in bel.data.polygons: f_.use_smooth = True
# mouth line + jaw open shape key (hinge at s ~ 0.12)
S_HINGE = -L_W * 0.42 + 0.115 * L_W
Y_N0, Y_N1 = -L_W * 0.42 + 0.17 * L_W * 0.94, -L_W * 0.42 + 0.30 * L_W * 0.94
MOUTH_Z = lambda y: prof(max(0, (y + L_W * 0.42) / (L_W * 0.94)))[3] - 0.015
# dorsal ridge along the back (belugas have a ridge instead of a dorsal fin)
for v in bel.data.vertices:
    s_ = (v.co.y + L_W * 0.42) / (L_W * 0.94)
    if 0.42 < s_ < 0.8 and v.co.z > 0:
        w_ = math.sin((s_ - 0.42) / 0.38 * math.pi)
        v.co.z += 0.03 * w_ * math.exp(-(v.co.x / 0.05) ** 2)
# mouth: flatten the underside of the head in front of the hinge into a palate; the lower jaw is its own closed mesh on a jaw bone
S_H = 0.115
for v in bel.data.vertices:
    s_ = (v.co.y + L_W * 0.42) / (L_W * 0.94)
    if s_ < S_H + 0.05 and abs(v.co.x) < 0.33:
        mz = MOUTH_Z(v.co.y)
        if v.co.z < mz:
            k = 1.0 if s_ <= S_H else max(0.0, 1 - (s_ - S_H) / 0.05)
            v.co.z = v.co.z + (mz - v.co.z) * k
bm_j = bmesh.new(); rings_j = []; NJ = 20
SJ = [i / 28 * (S_H + 0.04) for i in range(29)]
for s_ in SJ:
    wv, top, bot, cz = prof(max(s_, 0.004))
    y = -L_W * 0.42 + s_ * L_W * 0.94
    mz = MOUTH_Z(y); zb = cz - bot
    r_ = []
    for j in range(NJ):
        a_ = 2 * math.pi * j / NJ; ca, sa = math.cos(a_), math.sin(a_)
        z = mz + (0.012 * ca if ca > 0 else (mz - zb) * ca * 0.98)
        r_.append(bm_j.verts.new((wv * 0.96 * sa, y + 0.004, z)))
    rings_j.append(r_)
for i in range(len(rings_j) - 1):
    for j in range(NJ):
        bm_j.faces.new((rings_j[i][j], rings_j[i][(j + 1) % NJ], rings_j[i + 1][(j + 1) % NJ], rings_j[i + 1][j]))
bm_j.faces.new(rings_j[0][::-1]); bm_j.faces.new(rings_j[-1])
bmesh.ops.recalc_face_normals(bm_j, faces=bm_j.faces)
jme = bpy.data.meshes.new("Beluga_Jaw"); bm_j.to_mesh(jme); bm_j.free()
jawo = bpy.data.objects.new("Beluga_Jaw", jme); link(jawo)
for f_ in jme.polygons: f_.use_smooth = True
jsm = jawo.modifiers.new("Sub", 'SUBSURF'); jsm.levels = 1; jsm.render_levels = 2
ssm = bel.modifiers.new("Sub", 'SUBSURF'); ssm.levels = 1; ssm.render_levels = 2
# skin material: SSS white with faint grey mottling, mouth crease, scars
bm_ = bpy.data.materials.new("M_BelugaSkin"); bm_.use_nodes = True
bn, bl = bm_.node_tree.nodes, bm_.node_tree.links
bp = bn["Principled BSDF"]
bp.inputs['Roughness'].default_value = 0.42; bp.inputs['Subsurface Weight'].default_value = 0.5
bp.inputs['Subsurface Radius'].default_value = (0.4, 0.3, 0.25); bp.inputs['Subsurface Scale'].default_value = 0.05
bp.inputs['Coat Weight'].default_value = 0.25; bp.inputs['Coat Roughness'].default_value = 0.08
btc = bn.new('ShaderNodeTexCoord')
bnz = bn.new('ShaderNodeTexNoise'); bnz.inputs['Scale'].default_value = 1.6; bnz.inputs['Detail'].default_value = 6
bramp = bn.new('ShaderNodeValToRGB'); bramp.color_ramp.elements[0].color = (0.55, 0.58, 0.6, 1); bramp.color_ramp.elements[1].color = (0.9, 0.9, 0.86, 1)
bl.new(btc.outputs['Object'], bnz.inputs['Vector']); bl.new(bnz.outputs['Fac'], bramp.inputs['Fac'])
# mouth crease: dark line at the mouth height in the front of the head
bsep = bn.new('ShaderNodeSeparateXYZ'); bl.new(btc.outputs['Object'], bsep.inputs['Vector'])
def mnode(op, a=None, b=None):
    m_ = bn.new('ShaderNodeMath'); m_.operation = op
    if a is not None:
        if isinstance(a, (int, float)): m_.inputs[0].default_value = a
        else: bl.new(a, m_.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)): m_.inputs[1].default_value = b
        else: bl.new(b, m_.inputs[1])
    return m_.outputs[0]
dz = mnode('ABSOLUTE', mnode('SUBTRACT', bsep.outputs['Z'], mnode('ADD', mnode('MULTIPLY', bsep.outputs['Y'], 0.04), -0.0)))
# mouth z ~ -0.075 near the front: line where |z - (-0.075 + 0.04 * (y - y0))| < 0.01 and y < hinge
yfront = mnode('LESS_THAN', bsep.outputs['Y'], S_HINGE)
zline = mnode('LESS_THAN', mnode('ABSOLUTE', mnode('SUBTRACT', bsep.outputs['Z'], -0.078)), 0.008)
mouth = mnode('MULTIPLY', yfront, zline)
bmix = bn.new('ShaderNodeMix'); bmix.data_type = 'RGBA'; bmix.inputs['B'].default_value = (0.32, 0.33, 0.35, 1)
bl.new(mouth, bmix.inputs['Factor']); bl.new(bramp.outputs['Color'], bmix.inputs['A']); bl.new(bmix.outputs['Result'], bp.inputs['Base Color'])
bbump = bn.new('ShaderNodeBump'); bbump.inputs['Strength'].default_value = 0.18; bbump.inputs['Distance'].default_value = 0.01
bnz2 = bn.new('ShaderNodeTexNoise'); bnz2.inputs['Scale'].default_value = 40.0
bl.new(btc.outputs['Object'], bnz2.inputs['Vector'])
# fine wrinkles (crackle voronoi) + neck creases (bands across the body between s 0.17 and 0.30)
bvo = bn.new('ShaderNodeTexNoise'); bvo.inputs['Scale'].default_value = 14.0; bvo.inputs['Detail'].default_value = 3; bvo.inputs['Distortion'].default_value = 2.5
bvo.noise_type = 'RIDGED_MULTIFRACTAL' if hasattr(bvo, 'noise_type') else bvo.noise_type
bl.new(btc.outputs['Object'], bvo.inputs['Vector'])
wr = mnode('MULTIPLY', bvo.outputs['Fac'], 0.25)
bwv = bn.new('ShaderNodeTexWave'); bwv.wave_type = 'BANDS'; bwv.bands_direction = 'Y'; bwv.inputs['Scale'].default_value = 3.2
bwv.inputs['Distortion'].default_value = 1.5; bwv.inputs['Detail'].default_value = 2
bl.new(btc.outputs['Object'], bwv.inputs['Vector'])
nk = mnode('MULTIPLY', mnode('GREATER_THAN', bsep.outputs['Y'], Y_N0), mnode('LESS_THAN', bsep.outputs['Y'], Y_N1))
crease = mnode('MULTIPLY', mnode('MULTIPLY', bwv.outputs['Fac'], nk), 1.2)
hgt = mnode('ADD', mnode('ADD', mnode('MULTIPLY', bnz2.outputs['Fac'], 0.3), wr), crease)
bl.new(hgt, bbump.inputs['Height']); bl.new(bbump.outputs['Normal'], bp.inputs['Normal'])
# darker grey in the creases
cmx = bn.new('ShaderNodeMix'); cmx.data_type = 'RGBA'; cmx.inputs['B'].default_value = (0.62, 0.64, 0.66, 1)
bl.new(mnode('MULTIPLY', crease, 0.35), cmx.inputs['Factor']); bl.new(bmix.outputs['Result'], cmx.inputs['A']); bl.new(cmx.outputs['Result'], bp.inputs['Base Color'])
bel.data.materials.append(bm_)
jawo.data.materials.append(bm_)
# mouth interior (dark, wet) seen through the open slit; rides on the head bone
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0, location=(0, -L_W * 0.42 + 0.075 * L_W, MOUTH_Z(-L_W * 0.42 + 0.075 * L_W) - 0.01))
mi = bpy.context.active_object; mi.name = "Beluga_MouthInterior"; mi.scale = (0.12, 0.2, 0.03)
mim = simple_mat("M_BelugaMouth", (0.22, 0.09, 0.1), rough=0.25, sss=0.3); mi.data.materials.append(mim)
[setattr(f_, 'use_smooth', True) for f_ in mi.data.polygons]
# eyes
M_EYE = simple_mat("M_BelugaEye", (0.02, 0.02, 0.025), rough=0.05)
EYE_Y = -L_W * 0.42 + 0.155 * L_W
for side in (-1, 1):
    wv, top, bot, cz = prof(0.155)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(side * (wv - 0.012), EYE_Y, cz - 0.02))
    e = bpy.context.active_object; e.name = "Beluga_Eye_" + ("L" if side > 0 else "R"); e.data.materials.append(M_EYE)
    e.scale = (0.7, 1.0, 0.8)

# rig: torso root, head forward, tail chain backward
arm = bpy.data.armatures.new("Beluga_Rig"); rig = bpy.data.objects.new("Beluga_Rig", arm); link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(False)
rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
Y = lambda s: -L_W * 0.42 + s * L_W * 0.94
eb = arm.edit_bones
t = eb.new("torso"); t.head = (0, Y(0.30), 0); t.tail = (0, Y(0.40), 0)
h = eb.new("neck"); h.head = (0, Y(0.30), 0); h.tail = (0, Y(0.22), 0); h.parent = t
hd = eb.new("head"); hd.head = (0, Y(0.22), 0); hd.tail = (0, Y(0.02), 0); hd.parent = h
jb = eb.new("jaw"); jb.head = (0, Y(0.125), MOUTH_Z(Y(0.125))); jb.tail = (0, Y(0.0), MOUTH_Z(Y(0.0))); jb.parent = hd
ml_ = eb.new("melon"); ml_.head = (0, Y(0.17), 0.05); ml_.tail = (0, Y(0.07), 0.16); ml_.parent = hd
CH = [0.40, 0.52, 0.64, 0.75, 0.85, 0.93, 1.0]
prev = t
for k in range(len(CH) - 1):
    b = eb.new("tail%d" % k); b.head = (0, Y(CH[k]), prof(CH[k])[3]); b.tail = (0, Y(CH[k + 1]), prof(CH[k + 1])[3]); b.parent = prev; b.use_connect = (k > 0)
    prev = b
bpy.ops.object.mode_set(mode='OBJECT')
# weights along the body axis
centres = [("head", 0.10), ("neck", 0.25), ("torso", 0.35)] + [("tail%d" % k, (CH[k] + CH[k + 1]) / 2) for k in range(len(CH) - 1)]
vg = {n_: bel.vertex_groups.new(name=n_) for n_, _ in centres}
for v in bel.data.vertices:
    s = (v.co.y + L_W * 0.42) / (L_W * 0.94)
    if abs(v.co.x) > 0.5 and s < 0.5:      # flippers ride on the torso/neck
        s = min(s, 0.33)
    s = max(centres[0][1], min(centres[-1][1], s))
    for (n0, s0), (n1, s1) in zip(centres, centres[1:]):
        if s0 <= s <= s1:
            t_ = (s - s0) / (s1 - s0); t_ = t_ * t_ * (3 - 2 * t_)
            vg[n0].add([v.index], 1 - t_, 'REPLACE'); vg[n1].add([v.index], t_, 'REPLACE'); break
vg["melon"] = bel.vertex_groups.new(name="melon")
MC = Vector((0, Y(0.10), 0.14))
for v in bel.data.vertices:
    s_ = (v.co.y + L_W * 0.42) / (L_W * 0.94)
    if s_ < 0.22 and v.co.z > prof(max(0, s_))[3] - 0.02:
        w_ = max(0.0, 1 - (v.co - MC).length / 0.26); w_ = w_ * w_ * (3 - 2 * w_)
        if w_ > 0:
            vg["melon"].add([v.index], w_, 'REPLACE')
            for g in v.groups:
                if g.group == vg["head"].index: g.weight = max(0.0, g.weight - w_)
am = bel.modifiers.new("Armature", 'ARMATURE'); am.object = rig
bel.modifiers.move(len(bel.modifiers) - 1, 0)
bel.parent = rig
for nm_, bn_ in [("Beluga_Eye_L", "head"), ("Beluga_Eye_R", "head"), ("Beluga_MouthInterior", "head"), ("Beluga_Jaw", "jaw")]:
    e = bpy.data.objects[nm_]; e.parent = rig; e.parent_type = 'BONE'; e.parent_bone = bn_
    hb = rig.data.bones[bn_]
    e.matrix_parent_inverse = (rig.matrix_world @ Matrix.Translation(hb.tail_local) @ hb.matrix_local.to_3x3().to_4x4()).inverted()
for pb in rig.pose.bones: pb.rotation_mode = 'XYZ'
# mouth socket empty (where her ankle sits), riding on the head bone
ms = bpy.data.objects.new("Beluga_MouthSocket", None); link(ms)
ms.parent = rig; ms.parent_type = 'BONE'; ms.parent_bone = "head"
hb = rig.data.bones["head"]
ms.matrix_parent_inverse = (Matrix.Translation(hb.tail_local) @ hb.matrix_local.to_3x3().to_4x4()).inverted()
ms.location = (0, 0, 0)
ms.matrix_world = Matrix.Translation(Vector((0, Y(0.05), -0.075)))
BEL_COLL = bpy.data.collections.new("Beluga"); sc.collection.children.link(BEL_COLL)
for o in [bel, rig, ms, bpy.data.objects["Beluga_MouthInterior"], jawo] + [bpy.data.objects["Beluga_Eye_" + s] for s in "LR"]:
    mv(o, BEL_COLL)

# ------------------------------------------------------------------ diver: wetsuit on the body, mask, fins
D = bpy.data.objects["Diver"]; DB = bpy.data.objects["Diver.body"]
for ch in list(D.children):
    if ch.name.endswith("female_sportsuit01"):
        bpy.data.objects.remove(ch, do_unlink=True)
if DB.data.shape_keys:
    for o in bpy.context.selected_objects: o.select_set(False)
    bpy.context.view_layer.objects.active = DB; DB.select_set(True)
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
for md in list(DB.modifiers):
    if md.type == 'MASK' and md.name.startswith("Delete."): DB.modifiers.remove(md)
print("DIVER_HEIGHT", max(v.co.z for v in DB.data.vertices))
M_NEO = bpy.data.materials.new("M_Neoprene"); M_NEO.use_nodes = True
nn, nl = M_NEO.node_tree.nodes, M_NEO.node_tree.links
npb = nn["Principled BSDF"]; npb.inputs['Roughness'].default_value = 0.48; npb.inputs['Sheen Weight'].default_value = 0.3
npb.inputs['Sheen Tint'].default_value = (0.7, 0.75, 0.8, 1)
ntc = nn.new('ShaderNodeTexCoord'); nsep = nn.new('ShaderNodeSeparateXYZ'); nl.new(ntc.outputs['Object'], nsep.inputs['Vector'])
# side panels lighter grey (|x| band), main body charcoal-grey
nabs = nn.new('ShaderNodeMath'); nabs.operation = 'ABSOLUTE'; nl.new(nsep.outputs['X'], nabs.inputs[0])
nmr = nn.new('ShaderNodeMapRange'); nmr.inputs['From Min'].default_value = 0.11; nmr.inputs['From Max'].default_value = 0.115
nl.new(nabs.outputs[0], nmr.inputs['Value'])
ncol = nn.new('ShaderNodeMix'); ncol.data_type = 'RGBA'; ncol.inputs['A'].default_value = (0.045, 0.047, 0.05, 1); ncol.inputs['B'].default_value = (0.12, 0.125, 0.13, 1)
nl.new(nmr.outputs['Result'], ncol.inputs['Factor']); nl.new(ncol.outputs['Result'], npb.inputs['Base Color'])
nnz = nn.new('ShaderNodeTexNoise'); nnz.inputs['Scale'].default_value = 900.0
nbmp = nn.new('ShaderNodeBump'); nbmp.inputs['Strength'].default_value = 0.08
nl.new(ntc.outputs['Object'], nnz.inputs['Vector']); nl.new(nnz.outputs['Fac'], nbmp.inputs['Height']); nl.new(nbmp.outputs['Normal'], npb.inputs['Normal'])
DB.data.materials.append(M_NEO); neo_idx = len(DB.data.materials) - 1
# faces covered by the suit: dominant bone is not head/neck03/hand/finger
gname = {g.index: g.name for g in DB.vertex_groups}
BONESET = set(b.name for b in D.data.bones)
HELP = set(g.index for g in DB.vertex_groups if g.name in ("HelperGeometry", "JointCubes"))
def is_helper(v): return any(g.group in HELP and g.weight > 0.5 for g in v.groups)
def dom(v):
    best = max((g for g in v.groups if gname.get(g.group) in BONESET), key=lambda g: g.weight, default=None)
    return gname.get(best.group, "") if best else ""
SKIN_PREFIX = ("head", "jaw", "eye", "oris", "levator", "special", "orbicularis", "oculi", "temporalis", "risorius", "tongue", "neck02", "neck03",
               "wrist", "finger", "metacarpal")
vdom = [("" if is_helper(v) else dom(v)) for v in DB.data.vertices]
NECK_CUT = D.data.bones["neck02"].head_local.z + 0.01
FACEB = ("oris", "levator", "special", "eye", "orbic", "oculi", "temporalis", "risorius", "tongue")
suit = [0.0] * len(DB.data.vertices)
wr = {s_: (D.data.bones["wrist." + s_].head_local, (D.data.bones["wrist." + s_].head_local - D.data.bones["lowerarm02." + s_].head_local).normalized()) for s_ in "LR"}
for i, v in enumerate(DB.data.vertices):
    nm_ = vdom[i]
    if not nm_: continue
    if v.co.z > NECK_CUT - 0.25 and abs(v.co.x) < 0.14:
        suit[i] = max(0.0, min(1.0, 0.5 + (NECK_CUT - 0.006 * math.cos(math.atan2(v.co.y, v.co.x) * 2) - v.co.z) / 0.03))
    elif nm_.startswith(("lowerarm02", "wrist", "finger", "metacarpal")):
        side = nm_[-1]; h_, d_ = wr[side]
        suit[i] = max(0.0, min(1.0, 0.5 + (-0.012 - (v.co - h_).dot(d_)) / 0.03))
    else:
        suit[i] = 0.0 if nm_.startswith(SKIN_PREFIX) else 1.0
at = DB.data.attributes.new("suit", 'FLOAT', 'POINT')
at.data.foreach_set("value", suit)
# neoprene as a node group, mixed into every body material by the smooth 'suit' attribute
NG = bpy.data.node_groups.new("NeopreneShader", 'ShaderNodeTree')
NG.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
gn_, gl_ = NG.nodes, NG.links
go_ = gn_.new('NodeGroupOutput')
for nd in list(M_NEO.node_tree.nodes):
    pass
gp = gn_.new('ShaderNodeBsdfPrincipled'); gp.inputs['Roughness'].default_value = 0.48; gp.inputs['Sheen Weight'].default_value = 0.3
gp.inputs['Sheen Tint'].default_value = (0.7, 0.75, 0.8, 1); gp.inputs['Base Color'].default_value = (0.045, 0.047, 0.05, 1)
gtc = gn_.new('ShaderNodeTexCoord'); gnz = gn_.new('ShaderNodeTexNoise'); gnz.inputs['Scale'].default_value = 900.0
gbm = gn_.new('ShaderNodeBump'); gbm.inputs['Strength'].default_value = 0.08
gl_.new(gtc.outputs['Object'], gnz.inputs['Vector']); gl_.new(gnz.outputs['Fac'], gbm.inputs['Height']); gl_.new(gbm.outputs['Normal'], gp.inputs['Normal'])
gl_.new(gp.outputs['BSDF'], go_.inputs[0])
for m in DB.data.materials:
    if not m or m == M_NEO or not m.node_tree: continue
    nt = m.node_tree; out = next((x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL' and x.is_active_output), None)
    if not out or not out.inputs['Surface'].links: continue
    src = out.inputs['Surface'].links[0].from_socket
    ga = nt.nodes.new('ShaderNodeAttribute'); ga.attribute_name = "suit"
    mr_ = nt.nodes.new('ShaderNodeMapRange'); mr_.inputs['From Min'].default_value = 0.45; mr_.inputs['From Max'].default_value = 0.55
    gnode = nt.nodes.new('ShaderNodeGroup'); gnode.node_tree = NG
    mx_ = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(ga.outputs['Fac'], mr_.inputs['Value']); nt.links.new(mr_.outputs['Result'], mx_.inputs['Fac'])
    nt.links.new(src, mx_.inputs[1]); nt.links.new(gnode.outputs[0], mx_.inputs[2]); nt.links.new(mx_.outputs['Shader'], out.inputs['Surface'])
# dark hair tint
for ch in D.children:
    if ch.name.endswith("ponytail01"):
        for m in ch.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'BSDF_PRINCIPLED': nd.inputs['Base Color'].default_value = (0.05, 0.035, 0.025, 1)

def bone_world(o, b, which="head"):
    bb = o.data.bones[b]
    return o.matrix_world @ (bb.head_local if which == "head" else bb.tail_local)
def parent_to_bone(ob, rigobj, bone):
    mw = ob.matrix_world.copy()
    ob.parent = rigobj; ob.parent_type = 'BONE'; ob.parent_bone = bone
    pb = rigobj.pose.bones[bone]
    ob.matrix_world = mw
    bpy.context.view_layer.update()
    ob.matrix_parent_inverse = (rigobj.matrix_world @ pb.matrix @ Matrix.Translation(Vector((0, pb.length, 0)))).inverted()
    ob.matrix_world = mw
# foot pockets: copy of the foot/toe region of the body, offset outward, black rubber; blades parented to the foot bones
M_FIN = simple_mat("M_FinBlade", (0.04, 0.045, 0.05), rough=0.35)
M_POCKET = simple_mat("M_FootPocket", (0.03, 0.03, 0.03), rough=0.55)
bpy.context.view_layer.update()
for side in "LR":
    keep = set(i for i, nm_ in enumerate(vdom) if nm_.startswith(("foot." + side, "toe")) and nm_.endswith(side))
    # include the ankle ring
    keep |= set(i for i, v in enumerate(DB.data.vertices) if vdom[i] == "lowerleg02." + side and v.co.z < bone_world(D, "foot." + side).z + 0.06)
    keep = set(i for i in keep if vdom[i])
    bm = bmesh.new(); bm.from_mesh(DB.data)
    bm.verts.ensure_lookup_table()
    for v in [v for v in bm.verts if v.index not in keep]: bm.verts.remove(v)
    me = bpy.data.meshes.new("FootPocket_" + side); bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(M_POCKET)
    po = bpy.data.objects.new("Diver.FootPocket_" + side, me); link(po); po.parent = D
    for g in DB.vertex_groups: po.vertex_groups.new(name=g.name)
    am_ = po.modifiers.new("Armature", 'ARMATURE'); am_.object = D
    so = po.modifiers.new("Solid", 'SOLIDIFY'); so.thickness = 0.006; so.offset = 1.0
    # copy weights (vertex order preserved by from_mesh minus removed verts: rebuild by position)
    src = {tuple(round(c, 5) for c in v.co): v for v in DB.data.vertices}
    for v in me.vertices:
        sv = src.get(tuple(round(c, 5) for c in v.co))
        if sv:
            for g in sv.groups:
                po.vertex_groups[gname[g.group]].add([v.index], g.weight, 'REPLACE')
    for f_ in me.polygons: f_.use_smooth = True
    # blade from the toes along the foot direction, in the sole plane
    fb = D.data.bones["foot." + side]
    heel = D.matrix_world @ fb.head_local; toe = D.matrix_world @ fb.tail_local
    fwd = (toe - heel); fwd.z = 0; fwd.normalize()
    sole_z = min((D.matrix_world @ DB.data.vertices[i].co).z for i in keep)
    root = Vector((toe.x, toe.y, sole_z + 0.03)) + fwd * 0.02
    bm = bmesh.new()
    NB = 14
    verts = []
    for k in range(NB + 1):
        u = k / NB; Lb = 0.78
        hw = 0.055 + 0.055 * math.sin(min(1, u * 1.3) * math.pi / 2) - 0.012 * u
        th = 0.010 * (1 - u) + 0.002
        cpos = root + fwd * (Lb * u)
        side_v = fwd.cross(Vector((0, 0, 1))).normalized()
        row = [bm.verts.new(cpos + side_v * hw * x + Vector((0, 0, th * zz))) for x, zz in ((-1, 0), (-0.85, 1), (0, 1.3), (0.85, 1), (1, 0), (0.85, -1), (0, -1.3), (-0.85, -1))]
        verts.append(row)
    for k in range(NB):
        for j in range(8):
            bm.faces.new((verts[k][j], verts[k][(j + 1) % 8], verts[k + 1][(j + 1) % 8], verts[k + 1][j]))
    bm.faces.new(verts[0][::-1]); bm.faces.new(verts[-1])
    me = bpy.data.meshes.new("FinBlade_" + side); bm.to_mesh(me); bm.free()
    me.materials.append(M_FIN)
    bo = bpy.data.objects.new("Diver.FinBlade_" + side, me); link(bo)
    for f_ in me.polygons: f_.use_smooth = True
    # rails along the blade edges (stiffer side rails)
    parent_to_bone(bo, D, "foot." + side)
# mask: frame + skirt whose back rim is shrinkwrapped onto the face; strap around the head
eyeL, eyeR = bone_world(D, "eye.L"), bone_world(D, "eye.R")
ec = (eyeL + eyeR) / 2
face_front_y = min((D.matrix_world @ v.co).y for v in DB.data.vertices if not is_helper(v) and abs((D.matrix_world @ v.co).z - ec.z) < 0.02 and abs((D.matrix_world @ v.co).x) < 0.03)
bm = bmesh.new()
W2, H2, DEP = 0.072, 0.034, 0.03
def rr(t, w, h, r):
    """rounded-rect point at parameter t in [0,1)"""
    a = 2 * math.pi * t
    x = math.copysign(min(1, abs(math.cos(a)) ** 0.5), math.cos(a)) * w
    z = math.copysign(min(1, abs(math.sin(a)) ** 0.5), math.sin(a)) * h
    if z < 0 and abs(x) < 0.022:           # nose pocket notch on the lower edge
        z -= 0.03 * (1 - abs(x) / 0.022)
    return x, z
N = 48; loops = []
for k, (scale, yoff) in enumerate(((1.0, 0.0), (1.02, -0.015), (1.0, -0.032), (0.97, -DEP))):
    row = []
    for j in range(N):
        x, z = rr(j / N, W2 * scale, H2 * scale, 0.02)
        row.append(bm.verts.new((ec.x + x, face_front_y + 0.02 + yoff - 0.02, ec.z + 0.004 + z)))
    loops.append(row)
for k in range(len(loops) - 1):
    for j in range(N):
        bm.faces.new((loops[k][j], loops[k][(j + 1) % N], loops[k + 1][(j + 1) % N], loops[k + 1][j]))
me = bpy.data.meshes.new("Mask"); bm.to_mesh(me); bm.free()
mask = bpy.data.objects.new("Diver.Mask", me); link(mask)
rimg = mask.vertex_groups.new(name="rim"); rimg.add(list(range(0, N)), 1.0, 'REPLACE')
M_MASKSKIRT = simple_mat("M_MaskSkirt", (0.015, 0.016, 0.018), rough=0.3)
mask.data.materials.append(M_MASKSKIRT)
shw = mask.modifiers.new("Rim", 'SHRINKWRAP'); shw.target = DB; shw.vertex_group = "rim"; shw.offset = 0.007; shw.wrap_method = 'NEAREST_SURFACEPOINT'
sol = mask.modifiers.new("Solid", 'SOLIDIFY'); sol.thickness = 0.004
# lens: flat tinted glass in the frame front loop
bm = bmesh.new()
lv = [bm.verts.new((ec.x + rr(j / N, W2 * 0.98, H2 * 0.95, 0.02)[0], face_front_y - DEP - 0.001, ec.z + 0.004 + rr(j / N, W2 * 0.98, H2 * 0.95, 0.02)[1])) for j in range(N)]
bm.faces.new(lv)
lme = bpy.data.meshes.new("MaskLens"); bm.to_mesh(lme); bm.free()
lens = bpy.data.objects.new("Diver.MaskLens", lme); link(lens)
lens.data.materials.append(simple_mat("M_MaskLens", (0.95, 0.98, 1.0), rough=0.0, trans=1.0, ior=1.05))
fr = mask.copy(); fr.data = mask.data.copy(); fr.name = "Diver.MaskFrame"; link(fr)
for md in list(fr.modifiers): fr.modifiers.remove(md)
fr.data.materials.clear(); fr.data.materials.append(simple_mat("M_MaskFrame", (0.02, 0.02, 0.022), rough=0.3))
bmf = bmesh.new(); bmf.from_mesh(fr.data)
for v in [v for v in bmf.verts if v.index < 3 * N]: bmf.verts.remove(v)
bmf.to_mesh(fr.data); bmf.free()
fso = fr.modifiers.new("Solid", 'SOLIDIFY'); fso.thickness = 0.006; fso.offset = 0
# strap: ring around the head at eye height, shrinkwrapped (offset over the hair)
hb_ = D.data.bones["head"]
bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.006, major_segments=48, minor_segments=6,
                                 location=(ec.x, ec.y + 0.09, ec.z + 0.012), rotation=(R_(90 - 12), 0, 0))
strap = bpy.context.active_object; strap.name = "Diver.MaskStrap"
strap.scale = (0.86, 1.15, 1.0)
strap.data.materials.append(M_MASKSKIRT)
sws = strap.modifiers.new("Wrap", 'SHRINKWRAP'); sws.target = DB; sws.offset = 0.018; sws.wrap_method = 'NEAREST_SURFACEPOINT'
strap.modifiers.new("Smooth", 'SMOOTH').iterations = 6; strap.modifiers.new("Sub", 'SUBSURF').levels = 1
for o in (mask, lens, fr, strap):
    parent_to_bone(o, D, "head")
for o in (mask, fr, lens):
    for f_ in o.data.polygons: f_.use_smooth = True

for o in [o for o in bpy.data.objects if o.name.startswith(("Diver.Fin", "Diver.Mask")) and o.type == 'MESH']:
    bm_n = bmesh.new(); bm_n.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm_n, faces=bm_n.faces); bm_n.to_mesh(o.data); bm_n.free()
# ------------------------------------------------------------------ people placement (posed in 03)
print("DIVER faces suit", sum(1 for f_ in DB.data.polygons if f_.material_index == neo_idx), "of", len(DB.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_DONE", OUT)
