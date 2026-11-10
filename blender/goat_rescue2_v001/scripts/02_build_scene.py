"""Goat rescue scene: timeline, render settings, farm set, hospital set, animals, props, light rig.

blender -b farmer.blend --python 02_build_scene.py -- <assets_root> <work_dir> <out.blend>
assets_root: /opt/assets (ph/ = Poly Haven, objv/ = Objaverse GLBs)
work_dir:    holds goat_rig.blend, cow_rig.blend, scratch_narration.wav
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, W, OUT = argv[0], argv[1], argv[2]
PH, OB = os.path.join(A, "ph"), os.path.join(A, "objv")
sc = bpy.context.scene
FPS, END = 60, 2340
GZ = 0.0

# ------------------------------------------------------------------ timeline / render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end, sc.frame_step = 1, END, 1
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings
vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings
im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/GoatRescue2_v001_"

# ------------------------------------------------------------------ helpers
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc:
        i.colorspace_settings.name = 'Non-Color'
    return i

def pbr(name, folder, base, scale, sat=1.0, val=1.0, bump=1.0, rough_mul=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    l.new(tc.outputs['Object'], mp.inputs['Vector'])
    d = n.new('ShaderNodeTexImage'); d.image = img(os.path.join(folder, base + "_diff_2k.jpg"))
    r = n.new('ShaderNodeTexImage'); r.image = img(os.path.join(folder, base + "_rough_2k.jpg"), True)
    nm = n.new('ShaderNodeTexImage'); nm.image = img(os.path.join(folder, base + "_nor_gl_2k.jpg"), True)
    nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat; hsv.inputs['Value'].default_value = val
    rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
    for a, b in ((mp.outputs['Vector'], d.inputs['Vector']), (mp.outputs['Vector'], r.inputs['Vector']), (mp.outputs['Vector'], nm.inputs['Vector']),
                 (d.outputs['Color'], hsv.inputs['Color']), (hsv.outputs['Color'], p.inputs['Base Color']),
                 (r.outputs['Color'], rm.inputs[0]), (rm.outputs[0], p.inputs['Roughness']),
                 (nm.outputs['Color'], nmap.inputs['Color']), (nmap.outputs['Normal'], p.inputs['Normal'])):
        l.new(a, b)
    return m, n, l

def import_glb(path, name, height=None, length=None, loc=(0, 0, 0), rot_z=0.0, coll=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    for o in bpy.data.objects:
        o.select_set(False)
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    pts = [Vector(v.co) for v in ob.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    dims = mx - mn
    s = 1.0
    if height:
        s = height / dims.z
    elif length:
        s = length / max(dims.x, dims.y)
    ob.data.transform(Matrix.Translation(Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))))
    ob.data.transform(Matrix.Scale(s, 4))
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    if coll:
        for c_ in ob.users_collection:
            c_.objects.unlink(ob)
        coll.objects.link(ob)
    return ob

def coll(name):
    c_ = bpy.data.collections.new(name); sc.collection.children.link(c_); return c_

FARM, HOSP, ANIM, PROPS = coll("Farm_Set"), coll("Hospital_Set"), coll("Animals"), coll("Props")

# ------------------------------------------------------------------ world + light rig (keyable)
w = bpy.data.worlds.new("World_Farm"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
tc = wn.new('ShaderNodeTexCoord')
# blue sky (Poly Haven kloofendal_48d_partly_cloudy_puresky), rotated so its sun is front-left of camera
mp = wn.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(269.3))
sky_tex = wn.new('ShaderNodeTexEnvironment'); sky_tex.image = img(os.path.join(PH, "hdri/kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
sky_hsv = wn.new('ShaderNodeHueSaturation'); sky_hsv.inputs['Saturation'].default_value = 1.2
# tree-line horizon band from the meadow HDRI
mp2 = wn.new('ShaderNodeMapping'); mp2.inputs['Rotation'].default_value = (0, 0, math.radians(300))
hor = wn.new('ShaderNodeTexEnvironment'); hor.image = img(os.path.join(PH, "hdri/hausdorf_meadow_2k.hdr"))
hor_gain = wn.new('ShaderNodeMix'); hor_gain.data_type = 'RGBA'; hor_gain.blend_type = 'MULTIPLY'
hor_gain.inputs['Factor'].default_value = 1.0; hor_gain.inputs['B'].default_value = (1.25, 1.3, 1.25, 1)
sep = wn.new('ShaderNodeSeparateXYZ')
band = wn.new('ShaderNodeMapRange'); band.inputs['From Min'].default_value = 0.035; band.inputs['From Max'].default_value = 0.11
blend = wn.new('ShaderNodeMix'); blend.data_type = 'RGBA'
tint = wn.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.name = "SkyTint"
tint.inputs['Factor'].default_value = 1.0; tint.inputs['B'].default_value = (1, 1, 1, 1)
bg = wn.new('ShaderNodeBackground'); bg.name = "SkyStrength"; bg.inputs['Strength'].default_value = 1.0
out = wn.new('ShaderNodeOutputWorld')
for a_, b_ in ((tc.outputs['Generated'], mp.inputs['Vector']), (mp.outputs['Vector'], sky_tex.inputs['Vector']),
               (sky_tex.outputs['Color'], sky_hsv.inputs['Color']),
               (tc.outputs['Generated'], mp2.inputs['Vector']), (mp2.outputs['Vector'], hor.inputs['Vector']),
               (hor.outputs['Color'], hor_gain.inputs['A']),
               (tc.outputs['Generated'], sep.inputs['Vector']), (sep.outputs['Z'], band.inputs['Value']),
               (band.outputs['Result'], blend.inputs['Factor']), (hor_gain.outputs['Result'], blend.inputs['A']),
               (sky_hsv.outputs['Color'], blend.inputs['B']), (blend.outputs['Result'], tint.inputs['A']),
               (tint.outputs['Result'], bg.inputs['Color']), (bg.outputs['Background'], out.inputs['Surface'])):
    wl.new(a_, b_)
sun = bpy.data.objects.new("Key_Sun", bpy.data.lights.new("Key_Sun", 'SUN'))
sun.data.energy = 4.2; sun.data.angle = math.radians(2.5); sun.data.color = (1.0, 0.96, 0.9)
sc.collection.objects.link(sun)
moon = bpy.data.objects.new("Moon_Fill", bpy.data.lights.new("Moon_Fill", 'SUN'))
moon.data.energy = 0.0; moon.data.angle = math.radians(3); moon.data.color = (0.55, 0.68, 1.0)
moon.rotation_euler = (math.radians(40), 0, math.radians(-140))
sc.collection.objects.link(moon)

# ------------------------------------------------------------------ ground
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, GZ))
ground = bpy.context.active_object; ground.name = "Ground_Field"; ground.scale = (220, 220, 1)
bpy.ops.object.transform_apply(scale=True)
gm, _, _ = pbr("M_Field_Grass", os.path.join(PH, "grass_ground"), "grass_ground", 2.4, sat=0.9, val=0.95)
ground.data.materials.append(gm)
for c_ in ground.users_collection: c_.objects.unlink(ground)
FARM.objects.link(ground)

# ------------------------------------------------------------------ manure heap (plateau top, body hollow)
PILE_C = Vector((0.0, 0.0)); PILE_R = (2.7, 2.3); PILE_H = 0.78
LIE = dict(center=Vector((0.15, 0.05)), angle=math.radians(12), length=1.0, width=0.28, depth=0.0)  # imprint is carved at landing by 03_animate
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=160, y_segments=120, size=1.0)
for v in bm.verts:
    x, y = v.co.x * PILE_R[0] * 1.35, v.co.y * PILE_R[1] * 1.35
    r = math.sqrt((x / PILE_R[0]) ** 2 + (y / PILE_R[1]) ** 2)
    t = max(0.0, 1.0 - r)
    # broad, nearly flat top (he lies fully on it), steeper sides
    h = PILE_H * (1.0 - (1.0 - t) ** 3.2) if t > 0 else 0.0
    n1 = noise.fractal(Vector((x * 0.9, y * 0.9, 0.3)), 0.5, 2.0, 4) * 0.05
    n2 = noise.noise(Vector((x * 5.0, y * 5.0, 1.7))) * 0.015
    h = h + (n1 + n2) * min(1.0, t * 4)
    # hollow where he lies (soft body-shaped dip)
    ca, sa = math.cos(-LIE["angle"]), math.sin(-LIE["angle"])
    lx = (x - LIE["center"].x) * ca - (y - LIE["center"].y) * sa
    ly = (x - LIE["center"].x) * sa + (y - LIE["center"].y) * ca
    q = (lx / (LIE["length"] * 0.62)) ** 2 + (ly / (LIE["width"] * 1.25)) ** 2
    if q < 1.0:
        h -= LIE["depth"] * (1 - q) ** 1.5
    v.co = Vector((x, y, max(h, -0.02) - 0.02))
bm.normal_update()
pm = bpy.data.meshes.new("ManureHeap"); bm.to_mesh(pm); bm.free()
pile = bpy.data.objects.new("ManureHeap", pm); FARM.objects.link(pile)
for p_ in pm.polygons: p_.use_smooth = True
mm, mn, ml = pbr("M_Manure_Heap", os.path.join(PH, "brown_mud_02"), "brown_mud_02", 0.9, sat=1.25, val=0.62, bump=1.4, rough_mul=0.8)
hsv0 = [nd for nd in mn if nd.type == "HUE_SAT"][0]; hsv0.inputs["Hue"].default_value = 0.47
# straw: hay-coloured fibres mixed through the top layer (procedural streak mask)
p = mn["Principled BSDF"]
wave = mn.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.inputs['Scale'].default_value = 38
wave.inputs['Distortion'].default_value = 14; wave.inputs['Detail'].default_value = 3
nz = mn.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0
mul = mn.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
ramp = mn.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.50; ramp.color_ramp.elements[1].position = 0.66
mixc = mn.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; mixc.inputs['B'].default_value = (0.42, 0.33, 0.17, 1)
tco = mn.new('ShaderNodeTexCoord')
for a, b in ((tco.outputs['Object'], wave.inputs['Vector']), (tco.outputs['Object'], nz.inputs['Vector']),
             (wave.outputs['Fac'], mul.inputs[0]), (nz.outputs['Fac'], mul.inputs[1]),
             (mul.outputs[0], ramp.inputs['Fac']), (ramp.outputs['Color'], mixc.inputs['Factor'])):
    ml.new(a, b)
hsvn = [nd for nd in mn if nd.type == 'HUE_SAT'][0]
ml.new(hsvn.outputs['Color'], mixc.inputs['A'])
ml.new(mixc.outputs['Result'], p.inputs['Base Color'])
pile.data.materials.append(mm)
sc["lie_center"] = (LIE["center"].x, LIE["center"].y)
sc["lie_angle"] = LIE["angle"]

bpy.context.view_layer.update()
def pile_height(x, y):
    """ray-cast the heap from above"""
    hit, loc, nrm, idx = pile.ray_cast(Vector((x, y, 5)), Vector((0, 0, -1)))
    return loc.z if hit else 0.0
sc["pile_top"] = pile_height(LIE["center"].x, LIE["center"].y)

# ------------------------------------------------------------------ farm props
barn = import_glb(os.path.join(OB, "barn.glb"), "Barn", height=7.5, loc=(-5.5, 16.0, 0), rot_z=math.radians(200), coll=FARM)
for i, (x, y, r) in enumerate([(4.8, 6.5, 10), (5.9, 6.9, -5), (5.3, 7.6, 40), (-7.5, 9.0, 80)]):
    import_glb(os.path.join(OB, "hay_bale.glb"), "HayBale_%d" % i, length=1.0, loc=(x, y, 0), rot_z=math.radians(r), coll=FARM)
for o in [o for o in bpy.data.objects if o.name.startswith("HayBale_")]:
    for m in o.data.materials:
        for nd in m.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                lk = nd.inputs['Base Color'].links
                if lk:
                    hs = m.node_tree.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 0.55; hs.inputs['Value'].default_value = 0.8
                    m.node_tree.links.new(lk[0].from_socket, hs.inputs['Color']); m.node_tree.links.new(hs.outputs['Color'], nd.inputs['Base Color'])
                nd.inputs['Roughness'].default_value = 0.9
for i, (x, y, r) in enumerate([(14, 22, 0), (19, 30, 30), (-16, 26, 60), (24, 14, 10)]):
    import_glb(os.path.join(OB, "hay_round.glb"), "HayRound_%d" % i, height=1.5, loc=(x, y, 0), rot_z=math.radians(r), coll=FARM)
for i in range(7):
    import_glb(os.path.join(OB, "fence.glb"), "Fence_%d" % i, length=3.0, loc=(-9.0 + i * 3.0, 10.5, 0), rot_z=0, coll=FARM)
fork = import_glb(os.path.join(OB, "pitchfork.glb"), "Pitchfork", length=1.45, loc=(-2.9, -0.6, 0.6), coll=PROPS)

# ------------------------------------------------------------------ animals (rigged)
def append_rig(path, prefix):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(prefix)]
    for o in dst.objects:
        ANIM.objects.link(o)
    return bpy.data.objects[prefix + "_rig"]
goat = append_rig(os.path.join(W, "goat_rig.blend"), "goat")
cow = append_rig(os.path.join(W, "cow_rig.blend"), "cow")
goat.location = (3.2, 2.6, 0); cow.location = (-7.0, -3.5, 0)

# ------------------------------------------------------------------ ambulance (rear doors face the heap) + spine board + paramedics
AMB_C = Vector((-3.6, -6.4, 0.0)); AMB_R = Vector((3.6, 6.4, 0)).normalized()        # rear (tall box end, local +X) points at the heap
amb = import_glb(os.path.join(OB, "ambulance.glb"), "Ambulance", length=5.6, loc=AMB_C, rot_z=math.atan2(AMB_R.y, AMB_R.x), coll=PROPS)
sc["amb_rear"] = tuple(AMB_C + AMB_R * 2.8); sc["amb_dir"] = tuple(AMB_R)
for f_, h_ in ((1, True), (1960, False)):
    amb.hide_render = h_; amb.hide_viewport = False; amb.keyframe_insert("hide_render", frame=f_)
def box(name, size, loc, mat, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    for c_ in o.users_collection: c_.objects.unlink(o)
    PROPS.objects.link(o)
    if parent: o.parent = parent
    return o
def flat(name, rgb, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    pp = m.node_tree.nodes["Principled BSDF"]; pp.inputs['Base Color'].default_value = (*rgb, 1)
    pp.inputs['Roughness'].default_value = rough; pp.inputs['Metallic'].default_value = metal
    return m
bpy.ops.mesh.primitive_cube_add(size=1)
board = bpy.context.active_object; board.name = "SpineBoard"; board.scale = (0.46, 1.85, 0.045)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
board.modifiers.new("Bevel", 'BEVEL').width = 0.015
board.data.materials.append(flat("M_SpineBoard", (0.85, 0.28, 0.05), 0.45))
for c_ in board.users_collection: c_.objects.unlink(board)
PROPS.objects.link(board)
MED = coll("Medics")
with bpy.data.libraries.load(os.path.join(W, "medics.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("Medic")]
for o in dst.objects:
    MED.objects.link(o)

# ------------------------------------------------------------------ hospital (separate location at x=400, own grounds)
HX = Vector((400.0, 0.0, 0.0))
def to_hosp(o):
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    HOSP.objects.link(o); return o
def hbox(name, size, loc, mat):
    return to_hosp(box(name, size, HX + Vector(loc), mat))
# note: these Poly Haven maps were downloaded at 1K and stored under *_2k names for the shared loader
m_int_wall = flat("M_Hosp_Wall_Interior", (0.66, 0.74, 0.69), 0.9)   # plain pale hospital green
m_floor, _, _ = pbr("M_Hosp_Floor", os.path.join(PH, "floor_tiles_02"), "floor_tiles_02", 1.2, sat=0.5, val=1.1, rough_mul=0.6)
m_facade, _, _ = pbr("M_Hosp_Facade", os.path.join(PH, "beige_wall_001"), "beige_wall_001", 2.5, sat=0.8, val=1.0)
m_path, _, _ = pbr("M_Hosp_Path", os.path.join(PH, "concrete_pavement"), "concrete_pavement", 2.0)
m_lawn, nl, ll = pbr("M_Hosp_Lawn", os.path.join(PH, "grass_ground"), "grass_ground", 2.0, sat=1.45, val=1.0)
[nd for nd in nl if nd.type == 'HUE_SAT'][0].inputs['Hue'].default_value = 0.53
m_frame = flat("M_Window_Frame", (0.85, 0.86, 0.84), 0.35)
m_winpane = flat("M_Facade_Window", (0.08, 0.11, 0.14), 0.08, 0.0)
m_hedge = flat("M_Hedge", (0.06, 0.16, 0.05), 0.85)
m_ceiling = flat("M_Hosp_Ceiling", (0.82, 0.83, 0.82), 0.9)
# grounds
lawn = hbox("Hosp_Lawn", (80, 90, 0.04), (43.25, 0, -0.02), m_lawn)   # starts at the outer wall, never under the room
hbox("Hosp_Path", (2.2, 60, 0.05), (7.0, 0, 0.0), m_path)
for i in range(6):
    hbox("Hosp_Hedge_%d" % i, (1.0, 3.6, 0.9), (10.0, -10 + i * 4.0, 0.45), m_hedge)
# opposite hospital wing (facade with a window grid)
hbox("Hosp_Wing", (8, 44, 11), (24, 0, 5.5), m_facade)
for r in range(3):
    for k in range(10):
        hbox("Hosp_Wing_Win_%d_%d" % (r, k), (0.12, 1.5, 1.4), (19.95, -18 + k * 4.0, 1.8 + r * 3.3), m_winpane)
# our building: room interior 6 x 6 x 3, window in the +X wall facing the lawn
hbox("Hosp_Floor", (6.2, 6.2, 0.1), (0, 0, -0.048), m_floor)
hbox("Hosp_Ceiling", (6.2, 6.2, 0.1), (0, 0, 3.05), m_ceiling)
for nm, size, loc in (("Back", (6, 0.14, 3.0), (0, 3.07, 1.5)), ("Front", (6, 0.14, 3.0), (0, -3.07, 1.5)), ("Left", (0.14, 6, 3.0), (-3.07, 0, 1.5))):
    hbox("Hosp_Wall_" + nm, size, loc, m_int_wall)
WY, WZ0, WZ1 = 0.85, 0.55, 1.85              # window half-width, sill, head
for nm, size, loc in (("R_low", (0.14, 6, WZ0), (3.07, 0, WZ0 / 2)), ("R_high", (0.14, 6, 3.0 - WZ1), (3.07, 0, (3.0 + WZ1) / 2)),
                      ("R_a", (0.14, 3 - WY, WZ1 - WZ0), (3.07, -(3 + WY) / 2, (WZ0 + WZ1) / 2)), ("R_b", (0.14, 3 - WY, WZ1 - WZ0), (3.07, (3 + WY) / 2, (WZ0 + WZ1) / 2))):
    hbox("Hosp_Wall_" + nm, size, loc, m_int_wall)
# exterior facade of our building (two storeys, wider than the room) around the same opening
FX = 3.16
for nm, size, loc in (("low", (0.06, 20, WZ0), (FX, 0, WZ0 / 2)), ("high", (0.06, 20, 6.5 - WZ1), (FX, 0, (6.5 + WZ1) / 2)),
                      ("a", (0.06, 10 - WY, WZ1 - WZ0), (FX, -(10 + WY) / 2, (WZ0 + WZ1) / 2)), ("b", (0.06, 10 - WY, WZ1 - WZ0), (FX, (10 + WY) / 2, (WZ0 + WZ1) / 2))):
    hbox("Hosp_Facade_" + nm, size, loc, m_facade)
for k, yy in enumerate((-7.0, -4.0, 4.0, 7.0)):
    hbox("Hosp_Facade_Win_%d" % k, (0.04, 1.6, 1.3), (FX + 0.035, yy, 1.2), m_winpane)
for k, yy in enumerate((-7.0, -4.0, 0.0, 4.0, 7.0)):
    hbox("Hosp_Facade_Win2_%d" % k, (0.04, 1.6, 1.3), (FX + 0.035, yy, 4.4), m_winpane)
# window frame + sill (outside and in)
for nm, size, loc in (("top", (0.2, 2 * WY + 0.12, 0.06), (3.07, 0, WZ1)), ("bot", (0.34, 2 * WY + 0.12, 0.05), (3.07, 0, WZ0)),
                      ("l", (0.2, 0.06, WZ1 - WZ0), (3.07, -WY, (WZ0 + WZ1) / 2)), ("r", (0.2, 0.06, WZ1 - WZ0), (3.07, WY, (WZ0 + WZ1) / 2))):
    hbox("Hosp_Frame_" + nm, size, loc, m_frame)
# ceiling light panel
bpy.ops.mesh.primitive_plane_add(size=1, location=HX + Vector((0.4, 0.4, 2.99)))
panel = to_hosp(bpy.context.active_object); panel.name = "Hosp_Ceiling_Panel"; panel.scale = (1.2, 0.6, 1)
pm_ = bpy.data.materials.new("M_Light_Panel"); pm_.use_nodes = True
pn = pm_.node_tree.nodes; pn.clear(); po = pn.new('ShaderNodeOutputMaterial'); pe = pn.new('ShaderNodeEmission')
pe.inputs['Strength'].default_value = 6.0; pe.inputs['Color'].default_value = (1.0, 0.97, 0.92, 1)
pm_.node_tree.links.new(pe.outputs[0], po.inputs['Surface']); panel.data.materials.append(pm_)
panel.rotation_euler = (math.radians(180), 0, 0)
# bed, pillow, blanket, IV stand, curtain, flowers on the sill
bed = import_glb(os.path.join(OB, "hospital_bed.glb"), "Hospital_Bed", length=2.15, loc=HX + Vector((1.0, 0.45, 0)), rot_z=0, coll=HOSP)
m_linen = flat("M_Linen", (0.86, 0.88, 0.9), 0.85)
m_blanket = flat("M_Blanket", (0.55, 0.66, 0.74), 0.9)
pillow = hbox("Hosp_Pillow", (0.62, 0.36, 0.13), (1.0, 1.3, 0.0), m_linen)   # z placed by 03_animate on the mattress
bpy.ops.mesh.primitive_grid_add(x_subdivisions=24, y_subdivisions=36, size=1.0, location=HX + Vector((1.0, 0.1, 0.0)))
blanket = to_hosp(bpy.context.active_object); blanket.name = "Hosp_Blanket"; blanket.scale = (1.05, 1.5, 1)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
blanket.data.materials.append(m_blanket)
sol = blanket.modifiers.new("Thick", 'SOLIDIFY'); sol.thickness = 0.02
sub = blanket.modifiers.new("Smooth", 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
m_steel = flat("M_Steel", (0.7, 0.71, 0.72), 0.3, 1.0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=1.85, location=HX + Vector((2.0, 1.45, 0.95)))
to_hosp(bpy.context.active_object).name = "Hosp_IV_Pole"; bpy.context.active_object.data.materials.append(m_steel)
bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.03, location=HX + Vector((2.0, 1.45, 0.04)))
to_hosp(bpy.context.active_object).name = "Hosp_IV_Base"; bpy.context.active_object.data.materials.append(m_steel)
bag = hbox("Hosp_IV_Bag", (0.14, 0.05, 0.24), (2.0, 1.45, 1.66), flat("M_IV_Bag", (0.85, 0.9, 0.92), 0.2))
bpy.ops.mesh.primitive_plane_add(size=1, location=HX + Vector((2.93, -1.4, 1.5)))
curt = to_hosp(bpy.context.active_object); curt.name = "Hosp_Curtain"; curt.scale = (1, 1.0, 2.9)
curt.rotation_euler = (math.radians(90), 0, math.radians(90))
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.subdivide(number_cuts=40); bpy.ops.object.mode_set(mode='OBJECT')
for v in curt.data.vertices:
    v.co.z += 0.045 * math.sin(v.co.x * 38.0)
curt.data.materials.append(flat("M_Curtain", (0.62, 0.72, 0.66), 0.9))
curt.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.01
vase = import_glb(os.path.join(OB, "flowers_vase.glb"), "Flowers_Vase", height=0.48, loc=HX + Vector((3.12, -0.45, WZ0 + 0.025)), coll=HOSP)
# trees on the hospital lawn
with bpy.data.libraries.load(os.path.join(PH, "tree_small_02/tree_small_02_1k.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
tree_src = [o for o in dst.objects if o and o.type == 'MESH']
for i, (tx, ty, tz) in enumerate(((13.0, -7.0, 0), (15.5, 6.0, 0), (12.0, 11.0, 0), (16.0, -13.0, 0))):
    for j, o in enumerate(tree_src):
        inst = o.copy(); inst.name = "Hosp_Tree_%d_%d" % (i, j)
        inst.location = HX + Vector((tx, ty, tz)) + Vector(o.location)
        inst.rotation_euler.z += i * 1.3
        HOSP.objects.link(inst)
# daylight through the window + interior fill
light_h = bpy.data.objects.new("Hosp_Window_Light", bpy.data.lights.new("Hosp_Window_Light", 'AREA'))
light_h.data.energy = 220; light_h.data.size = 1.8; light_h.data.color = (1.0, 0.96, 0.9)
light_h.location = HX + Vector((2.9, 0, 1.25)); light_h.rotation_euler = (0, math.radians(90), 0)
light_h.data.energy = 140
HOSP.objects.link(light_h)
sc["hosp_x"] = HX.x

# ------------------------------------------------------------------ x-ray bones (hidden until the fracture beat)
femur = import_glb(os.path.join(OB, "femur.glb"), "XRay_Femur", length=0.46, coll=PROPS)
pelvis = import_glb(os.path.join(OB, "pelvis.glb"), "XRay_Pelvis", length=0.28, coll=PROPS)
xr = bpy.data.materials.new("M_XRay_Bone"); xr.use_nodes = True
xn, xl = xr.node_tree.nodes, xr.node_tree.links; xn.clear()
xo = xn.new('ShaderNodeOutputMaterial'); xe = xn.new('ShaderNodeEmission'); xe.inputs['Color'].default_value = (0.75, 0.9, 1.0, 1)
xe.inputs['Strength'].default_value = 2.0
xf = xn.new('ShaderNodeLayerWeight'); xf.inputs['Blend'].default_value = 0.35
xt = xn.new('ShaderNodeBsdfTransparent'); xm = xn.new('ShaderNodeMixShader')
xl.new(xf.outputs['Facing'], xm.inputs['Fac']); xl.new(xt.outputs['BSDF'], xm.inputs[1]); xl.new(xe.outputs['Emission'], xm.inputs[2])
xl.new(xm.outputs['Shader'], xo.inputs['Surface'])
for o in (femur, pelvis):
    o.data.materials.clear(); o.data.materials.append(xr)
    o.hide_render = True

# ------------------------------------------------------------------ farmer to collection, scratch narration
farmer = bpy.data.objects["Farmer"]
sc.sequence_editor_create()
wav = os.path.join(W, "scratch_narration.wav")
try:
    strips = sc.sequence_editor.strips
except AttributeError:
    strips = sc.sequence_editor.sequences
snd = strips.new_sound("SCRATCH_reference_narration_DO_NOT_PUBLISH", wav, channel=1, frame_start=1)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SCENE_OK pile_top=%.3f" % sc["pile_top"], "objects", len(bpy.data.objects))
