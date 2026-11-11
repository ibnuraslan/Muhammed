"""RingBullet set: render settings, antiques-shop back office at night, props, lights, bullet, ring, FX objects.
blender -b humans.blend --python 02_build_scene.py -- <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AS = os.path.join(ROOT, "assets")
sc = bpy.context.scene
FPS, END = 60, 1410
random.seed(21)

# ------------------------------------------------------------------ render
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 6; c.volume_bounces = 0
c.caustics_reflective = c.caustics_refractive = False
c.texture_limit_render = '2048'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'
sc.render.filepath = "//render/RingBullet_v001_"

def coll(name):
    cl = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if cl.name not in sc.collection.children: sc.collection.children.link(cl)
    return cl
C_SET, C_PROPS, C_FX, C_LIGHT = coll("Set"), coll("Props"), coll("FX"), coll("Lights")

def link(o, cl):
    for c_ in list(o.users_collection): c_.objects.unlink(o)
    cl.objects.link(o); return o

# ------------------------------------------------------------------ materials
def img(p, nc=False):
    i = bpy.data.images.load(p, check_existing=True)
    if nc: i.colorspace_settings.name = 'Non-Color'
    return i

def pbr_tex(name, folder, base, scale, val=1.0, bump=1.0, rough_mul=1.0, proj='BOX', coords='Object', rot=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / scale,) * 3
    mp.inputs['Rotation'].default_value[2] = math.radians(rot)
    l.new(tc.outputs[coords], mp.inputs['Vector'])
    T = os.path.join(AS, folder, "textures")
    d = n.new('ShaderNodeTexImage'); d.image = img(os.path.join(T, base + "_diff_2k.jpg"))
    r = n.new('ShaderNodeTexImage'); r.image = img(os.path.join(T, base + "_rough_2k.exr"), True)
    nm = n.new('ShaderNodeTexImage'); nm.image = img(os.path.join(T, base + "_nor_gl_2k.exr"), True)
    for t in (d, r, nm):
        t.projection = proj; t.projection_blend = 0.2
        l.new(mp.outputs['Vector'], t.inputs['Vector'])
    hsv = n.new('ShaderNodeHueSaturation'); hsv.inputs['Value'].default_value = val
    rm = n.new('ShaderNodeMath'); rm.operation = 'MULTIPLY'; rm.inputs[1].default_value = rough_mul; rm.use_clamp = True
    nmap = n.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = bump
    l.new(d.outputs['Color'], hsv.inputs['Color']); l.new(hsv.outputs['Color'], p.inputs['Base Color'])
    l.new(r.outputs['Color'], rm.inputs[0]); l.new(rm.outputs[0], p.inputs['Roughness'])
    l.new(nm.outputs['Color'], nmap.inputs['Color']); l.new(nmap.outputs['Normal'], p.inputs['Normal'])
    return m

def flat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal; p.inputs['Alpha'].default_value = alpha
    p.inputs['Transmission Weight'].default_value = trans; p.inputs['IOR'].default_value = ior
    p.inputs['Coat Weight'].default_value = coat
    if emit:
        p.inputs['Emission Color'].default_value = (*emit, 1); p.inputs['Emission Strength'].default_value = estr
    return m

def noisy(name, rgb, rgb2, scale=40.0, rough=0.6, metal=0.0, bump=0.1, rough2=None):
    """flat colour broken up by noise (fabric/metal wear)"""
    m = flat(name, rgb, rough, metal); n, l = m.node_tree.nodes, m.node_tree.links; p = n["Principled BSDF"]
    nz = n.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 8
    cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*rgb, 1); cr.color_ramp.elements[1].color = (*rgb2, 1)
    l.new(nz.outputs['Fac'], cr.inputs['Fac']); l.new(cr.outputs['Color'], p.inputs['Base Color'])
    bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; l.new(nz.outputs['Fac'], bp.inputs['Height'])
    l.new(bp.outputs['Normal'], p.inputs['Normal'])
    if rough2 is not None:
        mr = n.new('ShaderNodeMapRange'); mr.inputs[3].default_value = rough; mr.inputs[4].default_value = rough2
        l.new(nz.outputs['Fac'], mr.inputs[0]); l.new(mr.outputs[0], p.inputs['Roughness'])
    return m

M_WALL = pbr_tex("M_WallPanel", "dark_paneled_wood", "dark_paneled_wood", 1.6, val=1.1, bump=0.6)
M_FLOOR = pbr_tex("M_Parquet", "herringbone_parquet", "herringbone_parquet", 1.2, val=0.75, bump=0.5, rough_mul=0.8)
M_CEIL = noisy("M_Ceiling", (0.36, 0.31, 0.25), (0.28, 0.24, 0.19), 6, 0.9, bump=0.2)
M_DESK = pbr_tex("M_DeskWood", "dark_paneled_wood", "dark_paneled_wood", 3.0, val=0.8, bump=0.3, rough_mul=0.55)
M_LEATHER = noisy("M_DeskLeather", (0.08, 0.16, 0.09), (0.05, 0.1, 0.06), 90, 0.45, bump=0.05)
M_GOLD = noisy("M_Gold", (1.0, 0.72, 0.32), (0.92, 0.62, 0.25), 300, 0.16, 1.0, 0.02, 0.28)
M_BRASS = noisy("M_Brass", (0.85, 0.62, 0.3), (0.6, 0.42, 0.2), 60, 0.3, 1.0, 0.03, 0.5)
M_COPPER = noisy("M_BulletCopper", (0.95, 0.55, 0.36), (0.8, 0.45, 0.28), 400, 0.18, 1.0, 0.01, 0.3)
M_LEAD = noisy("M_Fragment", (0.75, 0.5, 0.36), (0.45, 0.42, 0.4), 500, 0.35, 1.0, 0.3, 0.6)
M_GUN = noisy("M_GunDark", (0.025, 0.025, 0.028), (0.05, 0.05, 0.055), 120, 0.4, 0.6, 0.02, 0.55)
M_GLASS = flat("M_Glass", (0.9, 0.95, 0.95), 0.02, trans=1.0, ior=1.5)
M_GREENGLASS = flat("M_LampShade", (0.02, 0.22, 0.07), 0.12, coat=1.0, emit=(0.1, 0.5, 0.2), estr=0.15)
M_BULB = flat("M_Bulb", (1, 0.85, 0.6), 0.3, emit=(1.0, 0.78, 0.5), estr=40)
M_PAPER = noisy("M_Paper", (0.85, 0.82, 0.74), (0.78, 0.74, 0.66), 30, 0.85)
M_RUG = noisy("M_Rug", (0.32, 0.07, 0.05), (0.18, 0.05, 0.04), 18, 0.95, bump=0.3)
M_BANDAGE = noisy("M_Bandage", (0.92, 0.9, 0.86), (0.8, 0.78, 0.74), 400, 0.9, bump=0.3)
M_PLASTER = noisy("M_Plaster", (0.86, 0.68, 0.55), (0.8, 0.62, 0.5), 200, 0.6, bump=0.05)
M_NICK = flat("M_Nick", (0.28, 0.06, 0.05), 0.55)
M_MARK = flat("M_NeckMark", (0.55, 0.18, 0.16), 0.6)

# ------------------------------------------------------------------ helpers
def box(name, size, loc, mat, cl=C_SET, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    if bevel:
        bv = o.modifiers.new("bv", 'BEVEL'); bv.width = bevel; bv.segments = 2
    return link(o, cl)

def cyl(name, r, h, loc, mat, cl=C_PROPS, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat)
    bpy.ops.object.shade_smooth(); return link(o, cl)

def lathe(name, prof, mat, segs=48, cl=C_PROPS):
    """profile [(r, z)] revolved about Z"""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs; rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in prof])
    for i in range(segs):
        A, B = rings[i], rings[(i + 1) % segs]
        for j in range(len(prof) - 1):
            bm.faces.new((A[j], B[j], B[j + 1], A[j + 1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); me.materials.append(mat); cl.objects.link(o)
    return o

def append_blend(path, names=None, cl=C_PROPS):
    with bpy.data.libraries.load(path, link=False) as (s, d):
        d.objects = [n for n in s.objects if names is None or n in names]
    out = []
    for o in d.objects:
        if o is None: continue
        cl.objects.link(o); out.append(o)
    return out

def place(objs, loc, rot_z=0.0, scale=1.0):
    """move a set of appended roots"""
    roots = [o for o in objs if o.parent is None or o.parent not in objs]
    for o in roots:
        o.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(math.radians(rot_z), 4, 'Z') @ Matrix.Scale(scale, 4) @ o.matrix_world

# ------------------------------------------------------------------ room
H = 2.8; XL, XR, YB, YF = -2.6, 2.6, 1.7, -4.2; T = 0.12
box("Floor", (XR - XL + 2 * T, YB - YF + 2 * T, 0.1), (0, (YB + YF) / 2, -0.05), M_FLOOR)
box("Ceiling", (XR - XL + 2 * T, YB - YF + 2 * T, 0.1), (0, (YB + YF) / 2, H + 0.05), M_CEIL)
# back wall with window x [-1.55,-0.35] z [0.95,2.15]
WX0, WX1, WZ0, WZ1 = -1.55, -0.35, 0.95, 2.15
by = YB + T / 2
box("WallBack_L", (WX0 - XL, T, H), ((XL + WX0) / 2, by, H / 2), M_WALL)
box("WallBack_R", (XR - WX1, T, H), ((WX1 + XR) / 2, by, H / 2), M_WALL)
box("WallBack_B", (WX1 - WX0, T, WZ0), ((WX0 + WX1) / 2, by, WZ0 / 2), M_WALL)
box("WallBack_T", (WX1 - WX0, T, H - WZ1), ((WX0 + WX1) / 2, by, (WZ1 + H) / 2), M_WALL)
# right wall with door y [0.05,1.05] z<2.1
DY0, DY1, DZ = 0.05, 1.05, 2.1
rx = XR + T / 2
box("WallRight_F", (T, DY0 - YF, H), (rx, (YF + DY0) / 2, H / 2), M_WALL)
box("WallRight_B", (T, YB - DY1, H), (rx, (DY1 + YB) / 2, H / 2), M_WALL)
box("WallRight_T", (T, DY1 - DY0, H - DZ), (rx, (DY0 + DY1) / 2, (DZ + H) / 2), M_WALL)
box("WallLeft", (T, YB - YF, H), (XL - T / 2, (YB + YF) / 2, H / 2), M_WALL)
box("WallFront", (XR - XL, T, H), (0, YF - T / 2, H / 2), M_WALL)
# ceiling beams
for yy in (-3.3, -2.1, -0.9, 0.3, 1.3):
    box("CeilBeam%+.1f" % yy, (XR - XL, 0.16, 0.14), (0, yy, H - 0.07), M_DESK, bevel=0.006)
# trims: skirting + picture rail, window frame, door frame
M_TRIM = flat("M_Trim", (0.12, 0.06, 0.03), 0.35, coat=0.3)
for nm, sz, lc in (("SkirtBack", (XR - XL, 0.03, 0.14), (0, YB - 0.015, 0.07)), ("SkirtLeft", (0.03, YB - YF, 0.14), (XL + 0.015, (YB + YF) / 2, 0.07)),
                   ("RailBack", (XR - XL, 0.03, 0.05), (0, YB - 0.015, 2.3)), ("RailLeft", (0.03, YB - YF, 0.05), (XL + 0.015, (YB + YF) / 2, 2.3))):
    box(nm, sz, lc, M_TRIM)
for nm, sz, lc in (("WinFrameB", (WX1 - WX0 + 0.12, 0.2, 0.06), ((WX0 + WX1) / 2, YB - 0.02, WZ0)),
                   ("WinFrameT", (WX1 - WX0 + 0.12, 0.16, 0.06), ((WX0 + WX1) / 2, YB, WZ1)),
                   ("WinFrameL", (0.06, 0.16, WZ1 - WZ0), (WX0, YB, (WZ0 + WZ1) / 2)), ("WinFrameR", (0.06, 0.16, WZ1 - WZ0), (WX1, YB, (WZ0 + WZ1) / 2)),
                   ("WinMullionV", (0.035, 0.05, WZ1 - WZ0), ((WX0 + WX1) / 2, YB + 0.02, (WZ0 + WZ1) / 2)),
                   ("WinMullionH", (WX1 - WX0, 0.05, 0.035), ((WX0 + WX1) / 2, YB + 0.02, (WZ0 + WZ1) / 2 + 0.15)),
                   ("DoorFrameF", (0.18, 0.07, DZ), (XR, DY0 - 0.035, DZ / 2)), ("DoorFrameB", (0.18, 0.07, DZ), (XR, DY1 + 0.035, DZ / 2)),
                   ("DoorFrameT", (0.18, DY1 - DY0 + 0.14, 0.07), (XR, (DY0 + DY1) / 2, DZ + 0.035))):
    box(nm, sz, lc, M_TRIM, bevel=0.005)
# window glass with rain drops (animated noise in the normal)
glass = box("WindowGlass", (WX1 - WX0, 0.01, WZ1 - WZ0), ((WX0 + WX1) / 2, YB + 0.03, (WZ0 + WZ1) / 2), flat("M_WinGlass", (0.8, 0.85, 0.9), 0.05, trans=1.0, ior=1.33))
mg = glass.data.materials[0]; n, l = mg.node_tree.nodes, mg.node_tree.links
tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, 0.25)
l.new(tc.outputs['Object'], mp.inputs['Vector'])
vor = n.new('ShaderNodeTexVoronoi'); vor.feature = 'SMOOTH_F1'; vor.voronoi_dimensions = '4D'; vor.inputs['Scale'].default_value = 60
drv = vor.inputs['W'].driver_add("default_value"); drv.driver.expression = "frame/120"
l.new(mp.outputs['Vector'], vor.inputs['Vector'])
bp = n.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.4; l.new(vor.outputs['Distance'], bp.inputs['Height'])
l.new(bp.outputs['Normal'], n["Principled BSDF"].inputs['Normal'])
# door: open, swung outward against the outside wall
door = box("Door", (0.05, DY1 - DY0 - 0.02, DZ - 0.02), (XR + T + 0.03, DY1 + 0.5, DZ / 2), M_TRIM, bevel=0.006)
door.rotation_euler = (0, 0, math.radians(75)); door.location = (XR + T + 0.5, DY0 - 0.15, DZ / 2)
# rug
rug = box("Rug", (2.6, 1.8, 0.012), (0.0, -1.2, 0.006), M_RUG, bevel=0.004)

# ------------------------------------------------------------------ outside: street, rain, backdrop
M_ASPH = noisy("M_WetAsphalt", (0.03, 0.03, 0.035), (0.08, 0.08, 0.09), 25, 0.08, 0.0, 0.2, 0.5)
box("Street", (12, 14, 0.1), (XR + 6.2, 0, -0.06), M_ASPH)
box("Sidewalk", (1.6, 14, 0.12), (XR + 0.95, 0, 0.0), noisy("M_Curb", (0.25, 0.25, 0.26), (0.18, 0.18, 0.2), 15, 0.3, bump=0.3))
box("YardBack", (8, 4, 0.1), (0, YB + 2.2, -0.04), M_ASPH)
bd = box("NightBackdrop", (14, 0.1, 7), (0, YB + 4.2, 3.0), flat("M_Backdrop", (0, 0, 0), 1.0))
mb = bd.data.materials[0]; n, l = mb.node_tree.nodes, mb.node_tree.links
em = n.new('ShaderNodeEmission'); vor = n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 1.4
cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = (1.0, 0.65, 0.3, 1)
cr.color_ramp.elements[1].position = 0.07; cr.color_ramp.elements[1].color = (0.01, 0.015, 0.03, 1)
l.new(vor.outputs['Distance'], cr.inputs['Fac']); l.new(cr.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = 2.0
l.new(em.outputs[0], n["Material Output"].inputs['Surface'])
bd.visible_shadow = False
# building across the street (seen through the door)
box("FacadeAcross", (0.3, 14, 6), (XR + 9.0, 0, 3), pbr_tex("M_Facade", "dark_paneled_wood", "dark_paneled_wood", 2.5, val=0.35))

# rain: geometry-nodes points in a box, falling with scene time (deterministic per frame)
def make_rain(name, size, loc, count, speed, streak, mat):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); C_FX.objects.link(o); o.location = loc
    gm = o.modifiers.new("GN", 'NODES'); ng = bpy.data.node_groups.new(name + "_GN", 'GeometryNodeTree'); gm.node_group = ng
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    out = N.new('NodeGroupOutput'); pts = N.new('GeometryNodeMeshToPoints')
    grid = N.new('GeometryNodeMeshLine'); grid.inputs['Count'].default_value = count
    rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT_VECTOR'; rnd.inputs['Min'].default_value = (-size[0] / 2, -size[1] / 2, 0); rnd.inputs['Max'].default_value = (size[0] / 2, size[1] / 2, size[2])
    tm = N.new('GeometryNodeInputSceneTime')
    sep = N.new('ShaderNodeSeparateXYZ'); L.new(rnd.outputs['Value'], sep.inputs[0])
    mz = N.new('ShaderNodeMath'); mz.operation = 'MULTIPLY'; mz.inputs[1].default_value = speed; L.new(tm.outputs['Seconds'], mz.inputs[0])
    sub = N.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; L.new(sep.outputs['Z'], sub.inputs[0]); L.new(mz.outputs[0], sub.inputs[1])
    wr = N.new('ShaderNodeMath'); wr.operation = 'WRAP'; wr.inputs[1].default_value = size[2]; wr.inputs[2].default_value = 0.0; L.new(sub.outputs[0], wr.inputs[0])
    cmb = N.new('ShaderNodeCombineXYZ'); L.new(sep.outputs['X'], cmb.inputs['X']); L.new(sep.outputs['Y'], cmb.inputs['Y']); L.new(wr.outputs[0], cmb.inputs['Z'])
    setp = N.new('GeometryNodeSetPosition')
    L.new(grid.outputs['Mesh'], pts.inputs['Mesh']); L.new(pts.outputs['Points'], setp.inputs['Geometry']); L.new(cmb.outputs[0], setp.inputs['Position'])
    inst = N.new('GeometryNodeInstanceOnPoints'); cy_ = N.new('GeometryNodeMeshCylinder')
    cy_.inputs['Vertices'].default_value = 4; cy_.inputs['Radius'].default_value = 0.0012; cy_.inputs['Depth'].default_value = streak
    L.new(setp.outputs['Geometry'], inst.inputs['Points']); L.new(cy_.outputs['Mesh'], inst.inputs['Instance'])
    sm = N.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = mat
    L.new(inst.outputs['Instances'], sm.inputs['Geometry']); L.new(sm.outputs[0], out.inputs[0])
    o.visible_shadow = False
    return o
M_RAIN = flat("M_Rain", (0.8, 0.85, 0.9), 0.05, trans=1.0, ior=1.33, emit=(0.5, 0.6, 0.8), estr=0.4)
make_rain("RainWindow", (3.0, 2.5, 4.0), (-0.9, YB + 1.6, -0.5), 900, 6.0, 0.09, M_RAIN)
make_rain("RainDoor", (5.0, 6.0, 4.0), (XR + 3.0, 0.5, -0.5), 1600, 6.0, 0.09, M_RAIN)

# dust motes in the lamp light: points drifting with noise over time
def make_dust(name, size, loc, count):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); C_FX.objects.link(o); o.location = loc
    gm = o.modifiers.new("GN", 'NODES'); ng = bpy.data.node_groups.new(name + "_GN", 'GeometryNodeTree'); gm.node_group = ng
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    out = N.new('NodeGroupOutput'); grid = N.new('GeometryNodeMeshLine'); grid.inputs['Count'].default_value = count
    pts = N.new('GeometryNodeMeshToPoints'); pts.inputs['Radius'].default_value = 0.0006
    rnd = N.new('FunctionNodeRandomValue'); rnd.data_type = 'FLOAT_VECTOR'; rnd.inputs['Min'].default_value = tuple(-s / 2 for s in size); rnd.inputs['Max'].default_value = tuple(s / 2 for s in size)
    tm = N.new('GeometryNodeInputSceneTime'); nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 1.5
    mt = N.new('ShaderNodeMath'); mt.operation = 'MULTIPLY'; mt.inputs[1].default_value = 0.05; L.new(tm.outputs['Seconds'], mt.inputs[0])
    L.new(rnd.outputs['Value'], nz.inputs['Vector']); L.new(mt.outputs[0], nz.inputs['W'])
    sub = N.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5); L.new(nz.outputs['Color'], sub.inputs[0])
    scl = N.new('ShaderNodeVectorMath'); scl.operation = 'SCALE'; scl.inputs['Scale'].default_value = 0.5; L.new(sub.outputs[0], scl.inputs[0])
    add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'; L.new(rnd.outputs['Value'], add.inputs[0]); L.new(scl.outputs[0], add.inputs[1])
    setp = N.new('GeometryNodeSetPosition')
    L.new(grid.outputs['Mesh'], pts.inputs['Mesh']); L.new(pts.outputs['Points'], setp.inputs['Geometry']); L.new(add.outputs[0], setp.inputs['Position'])
    sm = N.new('GeometryNodeSetMaterial'); sm.inputs['Material'].default_value = flat("M_Dust", (1, 0.9, 0.7), 0.5, emit=(1, 0.85, 0.6), estr=3.0)
    L.new(setp.outputs['Geometry'], sm.inputs['Geometry']); L.new(sm.outputs[0], out.inputs[0])
    o.visible_shadow = False
    return o
make_dust("DustMotes", (2.4, 3.0, 1.6), (0.0, -1.0, 1.4), 2500)

# ------------------------------------------------------------------ furniture & props
# desk: y [-1.02,-0.3], x [-0.8,0.8], top at 0.78
DESK_Y, DESK_TOP = -0.66, 0.78
box("DeskTop", (1.6, 0.72, 0.045), (0, DESK_Y, DESK_TOP - 0.0225), M_DESK, cl=C_PROPS, bevel=0.008)
box("DeskInlay", (1.3, 0.5, 0.004), (0, DESK_Y, DESK_TOP + 0.002), M_LEATHER, cl=C_PROPS)
for sx in (-1, 1):
    box("DeskPedestal%+d" % sx, (0.42, 0.66, DESK_TOP - 0.045), (sx * 0.56, DESK_Y, (DESK_TOP - 0.045) / 2), M_DESK, cl=C_PROPS, bevel=0.006)
    for k in range(3):
        z = 0.14 + k * 0.22
        box("Drawer%+d_%d" % (sx, k), (0.38, 0.012, 0.19), (sx * 0.56, DESK_Y - 0.335, z + 0.02), M_DESK, cl=C_PROPS, bevel=0.004)
        cyl("Knob%+d_%d" % (sx, k), 0.012, 0.02, (sx * 0.56, DESK_Y - 0.35, z + 0.02), M_BRASS, rot=(math.pi / 2, 0, 0))
box("DeskModesty", (0.7, 0.02, 0.6), (0, DESK_Y - 0.3, 0.45), M_DESK, cl=C_PROPS)
# banker's lamp on desk (left), shade faces the man
LAMP = Vector((-0.5, DESK_Y + 0.12, DESK_TOP))
lathe("LampBase", [(0.0, 0.0), (0.075, 0.0), (0.075, 0.012), (0.05, 0.025), (0.012, 0.035), (0.0, 0.035)], M_BRASS).location = LAMP
cyl("LampStem", 0.008, 0.33, LAMP + Vector((0, 0, 0.18)), M_BRASS)
me = bpy.data.meshes.new("LampShade"); bm = bmesh.new(); N_ = 24; rows = []
for xx in (-0.16, 0.16):
    rows.append([bm.verts.new((xx, 0.075 * math.cos(math.pi * i / N_), 0.06 * math.sin(math.pi * i / N_))) for i in range(N_ + 1)])
for i in range(N_): bm.faces.new((rows[0][i], rows[0][i + 1], rows[1][i + 1], rows[1][i]))
for row in rows: bm.faces.new(row)          # end caps (half discs)
bm.to_mesh(me); bm.free()
for p_ in me.polygons: p_.use_smooth = True
sh = bpy.data.objects.new("LampShade", me); C_PROPS.objects.link(sh); me.materials.append(M_GREENGLASS)
sh.location = LAMP + Vector((0, 0, 0.33)); sh.modifiers.new("sol", 'SOLIDIFY').thickness = 0.003
cyl("LampBulb", 0.018, 0.22, LAMP + Vector((0, 0, 0.345)), M_BULB, rot=(0, math.pi / 2, 0))
# papers on desk (will flutter)
for i in range(5):
    p_ = box("Paper%d" % i, (0.21, 0.297, 0.0008), (0.15 + 0.07 * i - 0.1, DESK_Y + random.uniform(-0.12, 0.08), DESK_TOP + 0.005 + 0.001 * i), M_PAPER,
             cl=C_PROPS, rot=(0, 0, math.radians(random.uniform(-25, 25))))
    p_.data.vertices  # keep simple
# ledger + pen + tea set
box("Ledger", (0.24, 0.32, 0.035), (0.48, DESK_Y + 0.05, DESK_TOP + 0.018), flat("M_Ledger", (0.25, 0.05, 0.04), 0.5), cl=C_PROPS, bevel=0.004, rot=(0, 0, 0.15))
cyl("Pen", 0.005, 0.14, (0.3, DESK_Y - 0.12, DESK_TOP + 0.006), flat("M_Pen", (0.02, 0.02, 0.02), 0.2, coat=1.0), rot=(0, math.pi / 2, 0.4))
tea = append_blend(os.path.join(AS, "tea_set_01/tea_set_01_1k.blend"), ["tea_set_01_cup_small_01", "tea_set_01_saucer_circular_03"])
for o in tea: o.location = (-0.15, DESK_Y + 0.2, DESK_TOP + (0.0 if "saucer" in o.name else 0.008)); o.rotation_euler = (0, 0, 0.6)
mc = append_blend(os.path.join(AS, "mantel_clock_01/mantel_clock_01_1k.blend"))
for o in mc:
    if o.name.startswith("wdg"): bpy.data.objects.remove(o)
mc = [o for o in bpy.data.objects if o.name.startswith(("rig_mantel", "mantel_clock"))]
place(mc, Vector((0.6, DESK_Y + 0.22, DESK_TOP)), 180 + 15)
# armchair, front-left of the room
ac = append_blend(os.path.join(AS, "ArmChair_01/ArmChair_01_1k.blend")); place(ac, Vector((-1.15, -2.45, 0)), -30)
# bookshelf on back wall right
bs = append_blend(os.path.join(AS, "wooden_bookshelf_worn/wooden_bookshelf_worn_1k.blend")); place(bs, Vector((1.2, YB - 0.3, 0)), 180)
books = append_blend(os.path.join(AS, "book_encyclopedia_set_01/book_encyclopedia_set_01_1k.blend"))
for o in list(books):
    if o.name.startswith("Sphere"): bpy.data.objects.remove(o); books.remove(o)
books_src = list(books)
k = 0
for shelf_z in (0.42, 0.86, 1.3, 1.72):
    x = 0.62
    while x < 1.75:
        src = books_src[k % len(books_src)]; k += 1
        o = src if k <= len(books_src) else src.copy()
        if o.name not in C_PROPS.objects: C_PROPS.objects.link(o)
        w = o.dimensions.x
        o.location = (x + w / 2, YB - 0.33, shelf_z + o.dimensions.z / 2 - 0.12 + random.uniform(-0.005, 0.005)); o.rotation_euler = (0, 0, math.pi)
        x += w + 0.003
        if random.random() < 0.08: x += 0.12
# grandfather clock back-left with swinging pendulum disc added
gc = append_blend(os.path.join(AS, "vintage_grandfather_clock_01/vintage_grandfather_clock_01_1k.blend"))
for o in list(gc):
    if o.name.startswith("wdg"): bpy.data.objects.remove(o); gc.remove(o)
place(gc, Vector((-2.15, YB - 0.28, 0)), 180)
pend = bpy.data.objects.new("PendulumPivot", None); C_PROPS.objects.link(pend); pend.location = (-2.15, YB - 0.27 - 0.2, 1.42)
rod = cyl("PendulumRod", 0.003, 0.6, (0, 0, -0.3), M_BRASS); rod.parent = pend
bob = cyl("PendulumBob", 0.07, 0.01, (0, 0, -0.62), M_BRASS, rot=(math.pi / 2, 0, 0)); bob.parent = pend
# glass-front antiques cabinet on the left wall, filled with brass and porcelain
cab = append_blend(os.path.join(AS, "vintage_cabinet_01/vintage_cabinet_01_1k.blend"), ["vintage_cabinet_01_body"]); place(cab, Vector((XL + 0.36, -0.95, 0)), 90)
for i, (y, z) in enumerate([(y_, z_) for z_ in (1.02, 1.42, 1.8) for y_ in (-1.7, -1.35, -0.95, -0.55, -0.2)]):
    kind = i % 4
    if kind == 0:
        v = lathe("CabVase%d" % i, [(0, 0), (0.04, 0), (0.055, 0.04), (0.045, 0.1), (0.022, 0.14), (0.028, 0.16), (0, 0.16)], M_BRASS)
    elif kind == 1:
        v = lathe("CabUrn%d" % i, [(0, 0), (0.03, 0), (0.06, 0.05), (0.05, 0.09), (0.035, 0.1), (0, 0.1)], flat("M_CabPorc%d" % i, (0.75, 0.74, 0.7), 0.12, coat=1.0))
    elif kind == 2:
        v = lathe("CabCup%d" % i, [(0, 0), (0.025, 0), (0.03, 0.01), (0.018, 0.03), (0.03, 0.09), (0, 0.09)], M_BRASS)
    else:
        v = lathe("CabBowl%d" % i, [(0, 0), (0.03, 0), (0.07, 0.04), (0.068, 0.045), (0, 0.045)], flat("M_CabBlue%d" % i, (0.1, 0.2, 0.45), 0.1, coat=1.0))
    v.location = (XL + 0.3, y, z)
for yy in (-1.45, -0.45):
    box("CabGlass%+.2f" % yy, (0.004, 0.98, 1.0), (-1.866, yy, 1.5), M_GLASS, cl=C_PROPS)
wc = append_blend(os.path.join(AS, "wall_clock/wall_clock_1k.blend")); place(wc, Vector((0.12, YB - 0.002, 2.08)), 0)
for o in wc: o.name = o.name.replace("wall_clock", "WallClock")
mir = append_blend(os.path.join(AS, "ornate_mirror_01/ornate_mirror_01_1k.blend")); place(mir, Vector((XR - 0.002, -1.0, 1.55)), -90)
for y in (-2.3,):
    pf = append_blend(os.path.join(AS, "fancy_picture_frame_01/fancy_picture_frame_01_1k.blend")); place(pf, Vector((XR - 0.002, y, 1.6)), -90)
pf = append_blend(os.path.join(AS, "fancy_picture_frame_01/fancy_picture_frame_01_1k.blend")); place(pf, Vector((-1.1, YF + 0.002, 1.6)), 180)
pp = append_blend(os.path.join(AS, "potted_plant_01/potted_plant_01_1k.blend")); place(pp, Vector((2.15, YB - 0.4, 0)), 30, 0.9)
pp2 = append_blend(os.path.join(AS, "potted_plant_01/potted_plant_01_1k.blend")); place(pp2, Vector((2.0, -3.6, 0)), 120, 0.75)
pw = append_blend(os.path.join(AS, "pocket_watch/pocket_watch_1k.blend"))
for o in pw:
    if o.parent is None: o.matrix_world = Matrix.Translation((0.33, DESK_Y - 0.02, DESK_TOP + 0.008)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(0.4, 4, 'Z') @ o.matrix_world
mgl = append_blend(os.path.join(AS, "magnifying_glass_01/magnifying_glass_01_1k.blend")); place(mgl, Vector((-0.2, DESK_Y - 0.1, DESK_TOP + 0.015)), 30)
mgl[0].rotation_euler.x += math.radians(90)
ol = append_blend(os.path.join(AS, "vintage_oil_lamp/vintage_oil_lamp_1k.blend")); place(ol, Vector((XL + 0.5, -2.4, 0.957)), 0)
bc = append_blend(os.path.join(AS, "brass_candleholders/brass_candleholders_1k.blend"), ["brass_candleholder_01", "brass_candleholder_02"])
place(bc, Vector((XL + 0.5, -3.7, 0.957)), 90)
# shop counter + display shelves toward the front (antiques), seen in wides
box("Counter", (0.6, 2.2, 0.95), (XL + 0.5, -3.1, 0.475), M_DESK, cl=C_PROPS, bevel=0.01)
box("CounterGlass", (0.56, 2.16, 0.004), (XL + 0.5, -3.1, 0.955), M_GLASS, cl=C_PROPS)
for i in range(6):
    v = lathe("Vase%d" % i, [(0, 0), (0.05, 0), (0.07, 0.05), (0.06, 0.12), (0.03, 0.17), (0.035, 0.2), (0, 0.2)], M_BRASS if i % 2 else flat("M_Porcelain%d" % i, (0.7, 0.72, 0.75), 0.15, coat=1.0))
    v.location = (XL + 0.5, -2.2 - i * 0.35, 0.957); v.scale = (1, 1, 1 + 0.4 * (i % 3))

# ------------------------------------------------------------------ hero props: bullet, ring, gun, FX
# 9 mm round-nose bullet along +Z (nose at +Z), real size
BUL = [(0.0, 0.0), (0.0042, 0.0), (0.00452, 0.0006), (0.00452, 0.0075), (0.0043, 0.0095), (0.0037, 0.0115), (0.0027, 0.0132), (0.0014, 0.0144), (0.0, 0.0148)]
bullet = lathe("Bullet", BUL, M_COPPER, 48); link(bullet, C_FX)
bullet.data.shape_keys or bullet.shape_key_add(name="Basis")
sk = bullet.shape_key_add(name="Squash")
for i, v in enumerate(bullet.data.vertices):
    co = v.co.copy(); z = co.z / 0.0148
    f = 1.0 + 0.9 * z * z; sk.data[i].co = Vector((co.x * f * 1.15, co.y * f * 0.8, co.z * (0.55 + 0.15 * (1 - z))))
# fragments (two irregular lumps)
def frag(name, seed, s):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0); o = bpy.context.active_object; o.name = name
    rr = random.Random(seed)
    for v in o.data.vertices:
        v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2])) * (1 + 0.25 * rr.uniform(-1, 1))
    o.data.materials.append(M_LEAD); bpy.ops.object.shade_smooth(); return link(o, C_FX)
fragA = frag("FragmentA", 1, (0.0034, 0.0026, 0.0048)); fragB = frag("FragmentB", 2, (0.003, 0.0024, 0.0042))
# muzzle-side casing
casing = lathe("Casing", [(0.0, 0.0), (0.0048, 0.0), (0.0048, 0.0012), (0.0043, 0.0014), (0.0048, 0.0018), (0.0048, 0.019), (0.0045, 0.019), (0.0045, 0.002), (0.0, 0.002)], M_BRASS, 32)
link(casing, C_FX)
# wedding band: inner radius fits finger4-1.L (set in animate step); width 4 mm, thickness 1.6 mm, comfort fit
RIN, RT, RW = 0.0095, 0.0016, 0.0042
prof = []
for i in range(17):
    a = math.pi * i / 16
    prof.append((RIN + RT * 0.5 + RT * 0.5 * math.sin(a) * 1.0 + (0 if 0 < i < 16 else 0), -RW / 2 * math.cos(a)))
inner = [(RIN, RW / 2 * math.cos(math.pi * i / 8)) for i in range(9)][1:-1]
ring = lathe("WeddingRing", prof + [(RIN, RW / 2)] + inner + [(RIN, -RW / 2), prof[0]], M_GOLD, 96)
link(ring, C_FX)
ring.shape_key_add(name="Basis"); dk = ring.shape_key_add(name="Dented")
for i, v in enumerate(ring.data.vertices):
    co = v.co.copy(); ang = math.atan2(co.y, co.x)
    d = math.exp(-((ang - math.pi / 2) / 0.45) ** 2)            # dent centred on +Y side
    rr_ = co.to_2d().length; outer = max(0.0, min(1.0, (rr_ - RIN) / RT)); nr = rr_ - (0.0003 + 0.0021 * outer) * d
    bend = 0.0004 * math.cos(ang) ** 2                           # slight oval
    dk.data[i].co = Vector((co.x / rr_ * (nr + bend), co.y / rr_ * nr, co.z + 0.0008 * d * (1 if co.z > 0 else -1)))
# simple dark pistol silhouette (no detail): slide + frame + grip, barrel along +X, muzzle at x=0.19
gun = bpy.data.objects.new("Gun", None); C_PROPS.objects.link(gun)
for nm, sz, lc, rot in (("GunSlide", (0.19, 0.03, 0.035), (0.095, 0, 0.0), 0), ("GunFrame", (0.13, 0.027, 0.02), (0.08, 0, -0.025), 0),
                        ("GunGrip", (0.045, 0.03, 0.11), (0.005, 0, -0.07), -0.25), ("GunGuard", (0.04, 0.012, 0.006), (0.06, 0, -0.055), 0)):
    g = box(nm, sz, lc, M_GUN, cl=C_PROPS, bevel=0.004, rot=(0, rot, 0)); g.parent = gun
# muzzle flash: crossed emissive cards, star shaped via a radial gradient
M_FLASH = flat("M_MuzzleFlash", (1, 0.7, 0.3), 1.0, emit=(1.0, 0.72, 0.35), estr=0.0)
nf, lf = M_FLASH.node_tree.nodes, M_FLASH.node_tree.links
tcf = nf.new('ShaderNodeTexCoord'); grd = nf.new('ShaderNodeTexGradient'); grd.gradient_type = 'SPHERICAL'
mpf = nf.new('ShaderNodeMapping'); mpf.inputs['Scale'].default_value = (2.0, 2.0, 1.0); mpf.inputs['Location'].default_value = (-0.7, -1.0, 0.0)
lf.new(tcf.outputs['UV'], mpf.inputs['Vector']); lf.new(mpf.outputs[0], grd.inputs['Vector'])
mix = nf.new('ShaderNodeMixShader'); trn = nf.new('ShaderNodeBsdfTransparent'); emn = nf.new('ShaderNodeEmission'); emn.inputs['Color'].default_value = (1, 0.7, 0.32, 1)
pw = nf.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.0; lf.new(grd.outputs['Fac'], pw.inputs[0])
ms = nf.new('ShaderNodeMath'); ms.operation = 'MULTIPLY'; ms.inputs[1].default_value = 60.0; ms.name = "FlashGain"; lf.new(pw.outputs[0], ms.inputs[0])
lf.new(ms.outputs[0], emn.inputs['Strength']); lf.new(pw.outputs[0], mix.inputs['Fac']); lf.new(trn.outputs[0], mix.inputs[1]); lf.new(emn.outputs[0], mix.inputs[2])
lf.new(mix.outputs[0], nf["Material Output"].inputs['Surface'])
flash = bpy.data.objects.new("MuzzleFlash", None); C_FX.objects.link(flash)
for i in range(3):
    bpy.ops.mesh.primitive_plane_add(size=1); pl = bpy.context.active_object; pl.name = "FlashCard%d" % i
    pl.scale = (0.16, 0.07, 1); pl.rotation_euler = (math.radians(60 * i), 0, 0); pl.location = (0.0, 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # card lies in the XY/XZ planes around X axis
    pl.data.materials.append(M_FLASH); link(pl, C_FX); pl.parent = flash; pl.location = (0.07, 0, 0)
    pl.visible_shadow = False
# smoke puff: volume sphere
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1); smoke = bpy.context.active_object; smoke.name = "MuzzleSmoke"
M_SMOKE = bpy.data.materials.new("M_Smoke"); M_SMOKE.use_nodes = True; ns, ls = M_SMOKE.node_tree.nodes, M_SMOKE.node_tree.links
ns.remove(ns["Principled BSDF"]); vol = ns.new('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (0.6, 0.58, 0.55, 1)
nzs = ns.new('ShaderNodeTexNoise'); nzs.inputs['Scale'].default_value = 3.0; nzs.inputs['Detail'].default_value = 6
grs = ns.new('ShaderNodeTexGradient'); grs.gradient_type = 'SPHERICAL'; tcs = ns.new('ShaderNodeTexCoord'); ls.new(tcs.outputs['Object'], grs.inputs['Vector'])
ms2 = ns.new('ShaderNodeMath'); ms2.operation = 'MULTIPLY'; ls.new(nzs.outputs['Fac'], ms2.inputs[0]); ls.new(grs.outputs['Fac'], ms2.inputs[1])
dn = ns.new('ShaderNodeMath'); dn.operation = 'MULTIPLY'; dn.inputs[1].default_value = 6.0; dn.name = "SmokeDensity"; ls.new(ms2.outputs[0], dn.inputs[0])
ls.new(dn.outputs[0], vol.inputs['Density']); ls.new(vol.outputs[0], ns["Material Output"].inputs['Volume'])
smoke.data.materials.append(M_SMOKE); link(smoke, C_FX); smoke.scale = (0.001,) * 3
# sparks: 40 small emissive streaks (keyed in animate step)
M_SPARK = flat("M_Spark", (1, 0.6, 0.2), 0.5, emit=(1.0, 0.55, 0.15), estr=25)
for i in range(40):
    s_ = cyl("Spark%02d" % i, 0.00012, 0.0035, (0, 0, -10), M_SPARK, cl=C_FX, verts=4); s_.visible_shadow = False
# impact flash point + ring glint light
def light(name, kind, energy, color, loc, size=0.1, cl=C_LIGHT):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'AREA': ld.size = size
    elif kind in ('POINT', 'SPOT'): ld.shadow_soft_size = size
    o = bpy.data.objects.new(name, ld); cl.objects.link(o); o.location = loc; return o
light("L_ImpactFlash", 'POINT', 0.0, (1.0, 0.85, 0.6), (0, -10, 0), 0.005)
light("L_MuzzleFlash", 'POINT', 0.0, (1.0, 0.7, 0.35), (0, -10, 0), 0.02)
light("L_RingGlint", 'POINT', 0.0, (1.0, 0.9, 0.7), (0, -10, 0), 0.002)
# injuries (decals) + bandage + plaster (parented in animate step)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1); nick = bpy.context.active_object; nick.name = "FingerNick"
nick.scale = (0.0016, 0.0008, 0.004); nick.data.materials.append(M_NICK); link(nick, C_FX)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1); mark = bpy.context.active_object; mark.name = "NeckMark"
mark.scale = (0.005, 0.0012, 0.0025); mark.data.materials.append(M_MARK); link(mark, C_FX)
band = lathe("FingerBandage", [(0.0, -0.016), (0.0098, -0.016), (0.0106, -0.012), (0.0108, 0.0), (0.0106, 0.012), (0.0098, 0.016), (0.0, 0.016)], M_BANDAGE, 32)
link(band, C_FX)
bpy.ops.mesh.primitive_cube_add(size=1); plas = bpy.context.active_object; plas.name = "NeckPlaster"
plas.scale = (0.03, 0.003, 0.022); bpy.ops.object.transform_apply(scale=True)
bvp = plas.modifiers.new("bv", 'BEVEL'); bvp.width = 0.0012; bvp.segments = 3
plas.data.materials.append(M_PLASTER); link(plas, C_FX)
# rack-focus target
foc = bpy.data.objects.new("FocusTarget", None); C_FX.objects.link(foc)

# ------------------------------------------------------------------ lights
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(AS, "hdri/warm_restaurant_night_2k.hdr"))
wl.new(env.outputs['Color'], wn["Background"].inputs['Color']); wn["Background"].inputs['Strength'].default_value = 0.15
lamp = light("L_DeskLamp", 'POINT', 18.0, (1.0, 0.72, 0.42), LAMP + Vector((0, 0, 0.34)), 0.03)
light("L_LampPool", 'SPOT', 60.0, (1.0, 0.72, 0.42), LAMP + Vector((0.0, 0.0, 0.33)), 0.05).rotation_euler = (math.radians(0), 0, 0)
key = light("L_KeyWarm", 'AREA', 30.0, (1.0, 0.75, 0.5), (-1.2, -1.6, 2.3), 0.8); key.rotation_euler = (math.radians(50), 0, math.radians(-35))
rim = light("L_RimCool", 'AREA', 35.0, (0.55, 0.7, 1.0), (0.9, 1.3, 2.2), 0.6); rim.rotation_euler = (math.radians(-55), 0, math.radians(150))
fill = light("L_FillBounce", 'AREA', 15.0, (1.0, 0.8, 0.6), (0.0, -3.5, 1.2), 2.0); fill.rotation_euler = (math.radians(90), 0, 0)
light("L_OilLamp", 'POINT', 6.0, (1.0, 0.6, 0.3), (XL + 0.5, -2.4, 1.25), 0.02)
cl_ = light("L_CabinetDisplay", 'AREA', 18.0, (1.0, 0.75, 0.45), (-2.15, -0.95, 2.02), 0.3); cl_.data.shape = 'RECTANGLE'; cl_.data.size = 0.3; cl_.data.size_y = 1.8
sconce = light("L_Sconce", 'POINT', 25.0, (1.0, 0.68, 0.38), (XL + 0.2, -1.0, 2.0), 0.08)
moon = light("L_Moon", 'AREA', 30.0, (0.5, 0.62, 1.0), ((WX0 + WX1) / 2, YB + 0.8, 2.0), 1.0); moon.rotation_euler = (math.radians(-60), 0, 0)
light("L_StreetDoor", 'AREA', 60.0, (0.5, 0.6, 0.9), (XR + 1.2, 0.55, 2.4), 1.5).rotation_euler = (0, math.radians(-55), 0)
for nm, col, loc in (("L_PoliceRed_Win", (1.0, 0.05, 0.03), ((WX0 + WX1) / 2 - 0.4, YB + 1.5, 1.3)), ("L_PoliceBlue_Win", (0.05, 0.2, 1.0), ((WX0 + WX1) / 2 + 0.4, YB + 1.5, 1.3)),
                     ("L_PoliceRed_Door", (1.0, 0.05, 0.03), (XR + 3.0, -0.6, 1.4)), ("L_PoliceBlue_Door", (0.05, 0.2, 1.0), (XR + 3.0, 1.6, 1.4))):
    L_ = light(nm, 'AREA', 0.0, col, loc, 1.2)
    tgt = Vector((0, 0, 1.2)) - Vector(loc); L_.rotation_euler = tgt.to_track_quat('-Z', 'Y').to_euler()
# police light bar outside the door (generic, no markings): emissive red/blue blocks on a dark car-height post
for nm, col, y in (("PoliceBarRed", (1, 0.05, 0.03), -0.2), ("PoliceBarBlue", (0.05, 0.2, 1), 1.3)):
    pb_ = box(nm, (0.25, 0.6, 0.12), (XR + 3.6, y, 1.5), flat("M_" + nm, col, 0.3, emit=col, estr=0.0), cl=C_FX, bevel=0.02)
box("PoliceCarShape", (1.8, 4.4, 0.9), (XR + 3.6, 0.55, 0.75), flat("M_CarDark", (0.02, 0.02, 0.025), 0.15, 0.6, coat=1.0), cl=C_PROPS, bevel=0.2)

# ------------------------------------------------------------------ humans: tint robber dark, drop his shoes, hide owner jacket? (keep)
for o in bpy.data.objects:
    if o.name.startswith("Robber.") and o.type == 'MESH':
        if o.name.endswith(".body"):
            o.data.materials.clear(); o.data.materials.append(noisy("M_RobberGlove", (0.02, 0.02, 0.022), (0.05, 0.05, 0.05), 200, 0.45))
        if "shoes" in o.name: bpy.data.objects.remove(o); continue
        if "casualsuit" in o.name:
            m = flat("M_RobberClothes", (0.015, 0.015, 0.018), 0.8); o.data.materials.clear(); o.data.materials.append(m)
        if o.name.endswith(".body"):
            pass
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith(".high-poly"):
        for m in o.data.materials:
            for n in m.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeGroup' and "OuterLayerTransmission" in n.inputs:
                    n.inputs["OuterLayerTransmission"].default_value = 1.0; n.inputs["OuterLayerAlpha"].default_value = 1.0; n.inputs["OuterLayerRoughness"].default_value = 0.0   # MPFB default cornea; works once the eye mesh casts no shadow
                    n.inputs["IrisMajorColor"].default_value = (0.25, 0.14, 0.06, 1); n.inputs["IrisMinorColor"].default_value = (0.1, 0.05, 0.02, 1)
        o.visible_shadow = False
# skin: more pore relief and SSS (less plastic); clearcoat (sweat) is keyed in 03b
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith(".body") and not o.name.startswith("Robber"):
        for m in o.data.materials:
            for n in m.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeGroup' and "Pore strength" in n.inputs:
                    n.inputs["Pore strength"].default_value = 0.4; n.inputs["SSS strength"].default_value = 0.35
                    n.inputs["Roughness"].default_value = 0.5; n.inputs["Clearcoat Roughness"].default_value = 0.22
                    n.name = "SkinGroup"
# officer: navy work uniform, no markings, waits outside the door as a backlit silhouette
for o in bpy.data.objects:
    if o.name.startswith("Officer.") and "worksuit" in o.name:
        o.data.materials.clear(); o.data.materials.append(noisy("M_OfficerUniform", (0.02, 0.03, 0.07), (0.035, 0.045, 0.09), 150, 0.75, bump=0.05))
sc["desk_y"] = DESK_Y; sc["desk_top"] = DESK_TOP; sc["door"] = (XR, DY0, DY1)
print("SCENE objects", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
