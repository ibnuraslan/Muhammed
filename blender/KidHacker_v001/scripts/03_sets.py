"""B32 KidHacker sets: night library (girl's carrel desk + old PC, shelves, door to a lit corridor, wall clock),
FBI office (x=40), interrogation room (x=80). Screen UIs are flat emissive shapes on the CRT (no text anywhere).
blender -b --factory-startup --python 03_sets.py -- /tmp/claude-0/kh/work/sets.blend"""
import bpy, bmesh, sys, math, random
from mathutils import Vector, Matrix, Euler
OUT = sys.argv[sys.argv.index("--") + 1]
A = "/tmp/claude-0/kh_assets/"; BR = "/home/user/Muhammed/blender/assets/brand/"
R_ = math.radians
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
random.seed(32)

def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c

def mat(name, rgb, rough=0.5, metal=0.0, emit=None, estr=1.0, coat=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; P = m.node_tree.nodes["Principled BSDF"]
    P.inputs["Base Color"].default_value = (*rgb, 1); P.inputs["Roughness"].default_value = rough; P.inputs["Metallic"].default_value = metal
    if coat: P.inputs["Coat Weight"].default_value = coat
    if emit:
        P.inputs["Emission Color"].default_value = (*emit, 1); P.inputs["Emission Strength"].default_value = estr
    return m

def emat(name, rgb, strength=1.0):
    """screen pixels: pure emission (reads as a lit CRT, not a sticker)"""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*rgb, 1); e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m

def box(name, c, loc, size, m, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", 'BEVEL'); b.width = bevel; b.segments = 3
    o.data.materials.append(m)
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); return o

def plane(name, c, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0], size[1], 1); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); return o

def append_coll(path, cname, c, loc, rot_z=0.0, scale=1.0, name=None):
    with bpy.data.libraries.load(path, link=False) as (fd, td): td.collections = [cname]
    src = td.collections[0]
    root = bpy.data.objects.new(name or cname, None); c.objects.link(root)
    for o in src.all_objects:
        if o.type != 'MESH': continue
        c.objects.link(o)
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale,) * 3
    return root

def dup_tree(root, c, loc, rot_z=0.0, name=None):
    """linked duplicate of an empty + its mesh children"""
    r2 = bpy.data.objects.new(name or root.name + "_d", None); c.objects.link(r2)
    for ch in root.children:
        o = ch.copy(); c.objects.link(o); o.parent = r2
    r2.location = loc; r2.rotation_euler = (0, 0, rot_z); r2.scale = root.scale
    return r2

def import_glb(path, c, keep=None, drop=()):
    bpy.ops.import_scene.gltf(filepath=path)
    sel = list(bpy.context.selected_objects); out = []
    for o in sel:
        if o.type == 'MESH' and (keep is None or o.name in keep) and o.name not in drop:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
            for cc in o.users_collection: cc.objects.unlink(o)
            c.objects.link(o); out.append(o)
    for o in sel:
        if o not in out: bpy.data.objects.remove(o)
    return out

def soften(m, rough_min=0.4):
    if not m or not m.use_nodes: return
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs["Roughness"].default_value = max(rough_min, n.inputs["Roughness"].default_value)
        if n.type == 'NORMAL_MAP': n.inputs["Strength"].default_value = min(0.35, n.inputs["Strength"].default_value)
        if n.type == 'BUMP': n.inputs["Strength"].default_value = min(0.35, n.inputs["Strength"].default_value)

def wood_mat(name, base=(0.36, 0.2, 0.1), plank=(0.6, 0.12)):
    m = bpy.data.materials.get(name)
    if m: return m
    m = mat(name, base, 0.45); nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); br = nt.nodes.new("ShaderNodeTexBrick")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    br.inputs["Color1"].default_value = (*base, 1); br.inputs["Color2"].default_value = tuple(min(1, x * 1.25) for x in base) + (1,)
    br.inputs["Mortar"].default_value = tuple(x * 0.5 for x in base) + (1,)
    br.inputs["Scale"].default_value = 3.0; br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Brick Width"].default_value = plank[0]; br.inputs["Row Height"].default_value = plank[1]
    nt.links.new(br.outputs["Color"], P.inputs["Base Color"])
    return m

def logo_decal(name, c, parent, loc_world, normal, up, width, dark=True):
    """flat logo plane on a surface (image with alpha), parented so it never floats"""
    img = bpy.data.images.load(BR + ("DaKrasFilms_logo_dark.png" if dark else "DaKrasFilms_logo_white.png"), check_existing=True)
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.interpolation = 'Cubic'
    nt.links.new(t.outputs["Color"], P.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], P.inputs["Alpha"])
    P.inputs["Roughness"].default_value = 0.5
    m.blend_method = 'HASHED' if hasattr(m, "blend_method") else None
    h = width * 414 / 967
    bpy.ops.mesh.primitive_plane_add(size=1); o = bpy.context.object; o.name = name
    o.scale = (width, h, 1); bpy.ops.object.transform_apply(scale=True)
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); o.data.materials.append(m)
    n = Vector(normal).normalized(); u = Vector(up).normalized(); x = u.cross(n)
    o.matrix_world = Matrix.Translation(Vector(loc_world)) @ Matrix((x, u, n)).transposed().to_4x4()
    if parent:
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted(); o.matrix_world = mw
    return o

# =================================================================== world + render
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920; sc.render.fps = 60
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
W = bpy.data.worlds.new("World"); sc.world = W; W.use_nodes = True
W.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.07, 0.14, 1); W.node_tree.nodes["Background"].inputs[1].default_value = 0.6

# =================================================================== the old PC (template, library copy)
CP = col("PC_Template")
pc = import_glb(A + "oldpc.glb", CP, drop=("Object_4",))
PCR = bpy.data.objects.new("PC_Lib", None); col("SetLibrary").objects.link(PCR)
for o in pc:
    for cc in o.users_collection: cc.objects.unlink(o)
    bpy.data.collections["SetLibrary"].objects.link(o); o.parent = PCR; o.name = "PCL_" + o.name
    for m in o.data.materials: soften(m, 0.35)
bpy.data.materials["Material.001"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.74, 0.64, 1)
glass = bpy.data.materials["Material.002"].node_tree.nodes["Principled BSDF"]
glass.inputs["Base Color"].default_value = (0.02, 0.03, 0.035, 1); glass.inputs["Roughness"].default_value = 0.25
S_PC = 0.19

# =================================================================== LIBRARY  (girl at origin facing -Y)
CL = col("SetLibrary")
wood_floor = wood_mat("LibFloor", (0.3, 0.17, 0.09))
fl = plane("LibFloor", CL, (0, 0, 0), (14, 14), wood_floor)
plane("LibCeiling", CL, (0, 0, 3.4), (14, 14), mat("LibCeil", (0.55, 0.6, 0.7), 0.8), rot=(R_(180), 0, 0))
wall_m = mat("LibWall", (0.42, 0.52, 0.66), 0.75)
for nm, loc, size, rot in (("LibWallBack", (0, -2.6, 1.7), (14, 3.4), (R_(90), 0, 0)), ("LibWallFront", (0, 3.6, 1.7), (14, 3.4), (R_(90), 0, 0)),
                           ("LibWallL", (-3.4, 0, 1.7), (14, 3.4), (R_(90), 0, R_(90))), ("LibWallR", (3.6, 0, 1.7), (14, 3.4), (R_(90), 0, R_(90)))):
    plane(nm, CL, loc, size, wall_m, rot)
# desk (carrel): wooden table + back panel + side panels
desk = append_coll(A + "ph/wooden_table_02/wooden_table_02_1k.blend", "wooden_table_02", CL, (0, -0.66, 0), 0, 0.9, "LibDesk")
desk.scale = (0.9, 0.9 * 1.25, 0.9)   # deeper desk: CRT + keyboard fit
DESK_TOP = 0.799 * 0.9
panel_m = wood_mat("CarrelWood", (0.42, 0.26, 0.13), (0.9, 0.3))
box("CarrelBack", CL, (0, -1.12, DESK_TOP + 0.24), (1.12, 0.03, 0.48), panel_m, 0.006)
# PC on the desk: monitor faces +Y (toward the girl)
PCR.scale = (S_PC,) * 3; PCR.rotation_euler = (0, 0, R_(90)); PCR.location = (-0.02, -0.79, DESK_TOP + 0.089 * S_PC)
bpy.context.view_layer.update()
def wbb(objs):
    pts = [o.matrix_world @ Vector(b) for o in objs for b in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
kb = [bpy.data.objects["PCL_Object_%d" % i] for i in (11, 12, 13)]
mon = [bpy.data.objects["PCL_Object_%d" % i] for i in (6, 7)]
tower = [bpy.data.objects["PCL_Object_%d" % i] for i in (15, 16, 17, 18, 19, 20)]
lo, hi = wbb(kb); print("KB", lo, hi)
# keyboard nearer the desk edge (girl's reach): move the keyboard pieces toward +Y
dy = (-0.29) - hi.y
for o in kb: o.location += PCR.matrix_world.inverted().to_3x3() @ Vector((0, dy, 0)) * 1.0
# tower beside the monitor on the desk's right (+X) side
bpy.context.view_layer.update()
lo, hi = wbb(kb); print("KB2", lo, hi); KB_TOP = hi.z; KB_LO, KB_HI = lo.copy(), hi.copy()
mlo, mhi = wbb(mon); print("MON", mlo, mhi)
tlo, thi = wbb(tower); print("TOWER", tlo, thi)
# screen frame (model space): glass face at x=0.423, y -0.85..0.87, z 0.61..1.89 -> a Screen empty in model space
def make_screen(pcroot, name):
    s = bpy.data.objects.new(name, None); pcroot.users_collection[0].objects.link(s); s.parent = pcroot
    s.location = (0.428, 0.01, 1.25); s.rotation_euler = (R_(90), 0, R_(90))   # local X -> model +Y (u), local Y -> model +Z (v), normal model +X
    return s
SCR = make_screen(PCR, "Screen_Lib")
# mouse on a mat to the right of the keyboard
mouse_m = mat("MouseBeige", (0.8, 0.76, 0.66), 0.45)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
ms = bpy.context.object; ms.name = "Mouse"; ms.scale = (0.03, 0.05, 0.018); bpy.ops.object.transform_apply(scale=True)
bm = bmesh.new(); bm.from_mesh(ms.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.002], context='VERTS'); bm.to_mesh(ms.data); bm.free()
ms.location = (KB_LO.x - 0.11, (KB_LO.y + KB_HI.y) / 2, DESK_TOP + 0.004); ms.data.materials.append(mouse_m)
for cc in ms.users_collection: cc.objects.unlink(ms)
CL.objects.link(ms)
for p in ms.data.polygons: p.use_smooth = True
plane("MousePad", CL, (ms.location.x, ms.location.y, DESK_TOP + 0.002), (0.2, 0.17), mat("PadBlue", (0.1, 0.2, 0.45), 0.8))
# cable: mouse -> behind monitor, and modem/phone cable: tower back -> wall jack on the carrel back panel
def cable(name, pts, r=0.004, m=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_endpoint_u = True; sp.order_u = 3
    o = bpy.data.objects.new(name, cu); CL.objects.link(o); cu.materials.append(m or mat("CableGrey", (0.6, 0.6, 0.6), 0.5)); return o
cable("MouseCable", [tuple(ms.location + Vector((0, -0.05, 0.005))), (ms.location.x, ms.location.y - 0.25, DESK_TOP + 0.006), (-0.25, -0.75, DESK_TOP + 0.006), (-0.12, -0.95, DESK_TOP + 0.01)], 0.0025)
JACK = Vector((0.48, -1.12 + 0.016, DESK_TOP + 0.20))
jp = box("WallJack", CL, (JACK.x, JACK.y + 0.006, JACK.z), (0.07, 0.012, 0.11), mat("JackWhite", (0.9, 0.9, 0.88), 0.4), 0.003)
box("JackSocket", CL, (JACK.x, JACK.y + 0.013, JACK.z + 0.015), (0.022, 0.004, 0.018), mat("JackHole", (0.05, 0.05, 0.05), 0.6), 0.001)
plug = box("JackPlug", CL, (JACK.x, JACK.y + 0.024, JACK.z + 0.015), (0.016, 0.022, 0.013), mat("PlugClear", (0.85, 0.75, 0.25), 0.3), 0.002)
tb = Vector((thi.x - 0.03, tlo.y + 0.02, tlo.z + 0.25))
cable("PhoneCable", [tuple(JACK + Vector((0, 0.036, 0.015))), tuple(JACK + Vector((-0.02, 0.09, 0.0))), (JACK.x - 0.02, JACK.y + 0.10, DESK_TOP + 0.02),
                     (tb.x, tb.y - 0.04, DESK_TOP + 0.02), tuple(tb)], 0.003, mat("CableYellow", (0.85, 0.65, 0.12), 0.4))
# chair (back toward +Y, behind the girl)
chair = append_coll(A + "ph/dining_chair_02/dining_chair_02_1k.blend", "dining_chair_02", CL, (0, 0.06, 0), 0, 1.0, "LibChair")   # model back is at +Y
# bookshelves: real shelf model (scaled), rows on the back wall, left wall and behind the girl
SH = import_glb(A + "shelf.glb", CL)
shroot = bpy.data.objects.new("ShelfTpl", None); CL.objects.link(shroot)
for o in SH:
    o.parent = shroot
    for m in o.data.materials: soften(m, 0.45)
shroot.scale = (6.6, 3.0, 6.6); shroot.location = (-50, -50, 0)
SHELVES = []
for i, x in enumerate((-3.0, -1.5, 0.0, 1.5, 3.0)):
    SHELVES.append(dup_tree(shroot, CL, (x + 0.76, -2.54, 0), R_(180), "ShelfBack%d" % i))
for i, y in enumerate((-1.6, -0.1, 1.4)):
    SHELVES.append(dup_tree(shroot, CL, (-3.34, y - 0.76, 0), R_(90), "ShelfL%d" % i))
for i, x in enumerate((-3.0, -1.5)):
    SHELVES.append(dup_tree(shroot, CL, (x - 0.76, 3.54, 0), 0, "ShelfFront%d" % i))
for i, x in enumerate((3.0,)):
    SHELVES.append(dup_tree(shroot, CL, (3.54, -1.5 + 0.76, 0), R_(-90), "ShelfR%d" % i))
# door to the lit corridor (front wall, x 0.2..2.0) + corridor
door_m = mat("DoorWood", (0.32, 0.18, 0.09), 0.5); frame_m = mat("DoorFrame", (0.85, 0.85, 0.82), 0.5)
box("DoorFrameL", CL, (0.15, 3.6, 1.15), (0.1, 0.25, 2.3), frame_m); box("DoorFrameR", CL, (2.05, 3.6, 1.15), (0.1, 0.25, 2.3), frame_m)
box("DoorFrameTop", CL, (1.1, 3.6, 2.35), (2.0, 0.25, 0.12), frame_m)
for sx, x in ((-1, 0.2), (1, 2.0)):
    d = box("DoorLeaf%+d" % sx, CL, (0, 0, 0), (0.88, 0.05, 2.25), door_m, 0.005)
    d.data.transform(Matrix.Translation(Vector((-sx * 0.44, 0, 1.125))))
    d.location = (x, 3.62, 0); d.rotation_euler = (0, 0, R_(sx * 80))
    box("DoorPanel%+d" % sx, CL, (0, 0, 0), (0.6, 0.06, 0.9), mat("DoorPanel", (0.4, 0.24, 0.12), 0.45), 0.01).parent = d
    bpy.data.objects["DoorPanel%+d" % sx].location = (-sx * 0.44, 0, 1.45)
# hole in the front wall for the door: split the wall into pieces
fw = bpy.data.objects["LibWallFront"]; bpy.data.objects.remove(fw)
plane("LibWallFrontL", CL, (-3.4, 3.6, 1.7), (7.2, 3.4), wall_m, (R_(90), 0, 0))
plane("LibWallFrontR", CL, (5.4, 3.6, 1.7), (6.8, 3.4), wall_m, (R_(90), 0, 0))
plane("LibWallFrontTop", CL, (1.1, 3.6, 2.85), (2.0, 1.1), wall_m, (R_(90), 0, 0))
CO = col("SetCorridor")
plane("CorrFloor", CO, (1.1, 6.0, 0.001), (4.0, 5.0), mat("CorrFloor", (0.55, 0.55, 0.52), 0.4))
plane("CorrWall", CO, (1.1, 8.0, 1.7), (6.0, 3.4), mat("CorrWall", (0.85, 0.8, 0.68), 0.7), (R_(90), 0, 0))
plane("CorrWallL", CO, (-0.6, 6.0, 1.7), (5.0, 3.4), mat("CorrWall", (0.85, 0.8, 0.68), 0.7), (R_(90), 0, R_(90)))
plane("CorrWallR", CO, (2.8, 6.0, 1.7), (5.0, 3.4), mat("CorrWall", (0.85, 0.8, 0.68), 0.7), (R_(90), 0, R_(90)))
plane("CorrCeil", CO, (1.1, 6.0, 3.0), (4.0, 5.0), mat("CorrCeil", (0.9, 0.9, 0.9), 0.7), (R_(180), 0, 0))
L = bpy.data.lights.new("CorrLight", 'AREA'); L.energy = 150; L.size = 2.0; L.color = (1.0, 0.9, 0.75)
lo_ = bpy.data.objects.new("CorrLight", L); CO.objects.link(lo_); lo_.location = (1.1, 5.8, 2.9)
# wall clock above the back shelves (no numbers: 12 tick marks + hands)
CK = bpy.data.objects.new("Clock", None); CL.objects.link(CK); CK.location = (0.0, -2.58, 2.72); CK.rotation_euler = (R_(-90), 0, 0)   # face toward +Y (the room)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.24, depth=0.05); o = bpy.context.object; o.name = "ClockRim"
o.data.materials.append(mat("ClockRim", (0.12, 0.13, 0.16), 0.35, 0.6)); o.parent = CK
for cc in o.users_collection: cc.objects.unlink(o)
CL.objects.link(o)
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.215, depth=0.01, location=(0, 0, 0.026)); o = bpy.context.object; o.name = "ClockFace"
o.data.materials.append(mat("ClockFace", (0.95, 0.94, 0.9), 0.5)); o.parent = CK
for cc in o.users_collection: cc.objects.unlink(o)
CL.objects.link(o)
for i in range(12):
    a = i * math.pi / 6; r = 0.18
    t = box("ClockTick%d" % i, CL, (r * math.sin(a), r * math.cos(a), 0.033), (0.012, 0.035 if i % 3 == 0 else 0.022, 0.004), mat("ClockInk", (0.05, 0.05, 0.06), 0.5), rot=(0, 0, -a))
    t.parent = CK
for nm, ln, w in (("ClockHour", 0.11, 0.016), ("ClockMinute", 0.165, 0.011)):
    h = bpy.data.objects.new(nm, None); CL.objects.link(h); h.parent = CK; h.location = (0, 0, 0.036 if nm == "ClockHour" else 0.04)
    b_ = box(nm + "Hand", CL, (0, ln / 2 - 0.02, 0), (w, ln, 0.004), mat("ClockInk", (0.05, 0.05, 0.06), 0.5)); b_.parent = h
box("ClockPin", CL, (0, 0, 0.044), (0.02, 0.02, 0.006), mat("ClockRed", (0.8, 0.1, 0.1), 0.4)).parent = CK
# lights: CRT glow (area at the screen), soft cool fill, blue moonlight rim, a few warm shelf lamps
def light(name, kind, loc, energy, color, size=0.5, rot=None, target=None, c=CL):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = color
    if kind == 'AREA': L.size = size
    if kind in ('POINT', 'SPOT'): L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L); c.objects.link(o); o.location = loc
    if target is not None:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    elif rot: o.rotation_euler = rot
    return o
light("ScreenGlow", 'AREA', (-0.02, -0.66, DESK_TOP + 0.22), 14, (0.75, 0.88, 1.0), 0.3, target=(0, 0.1, 1.0))
light("LibFill", 'AREA', (1.4, -0.9, 1.6), 9, (0.7, 0.8, 1.0), 1.2, target=(0, 0, 0.95))
light("LibMoon", 'SUN', (0, 0, 5), 0.35, (0.55, 0.7, 1.0), rot=(R_(55), 0, R_(150)))
light("LibRim", 'AREA', (-1.2, 1.4, 2.2), 30, (0.45, 0.6, 1.0), 1.5, target=(0, 0, 1.0))
for i, (x, y) in enumerate(((-2.2, -1.9), (2.2, -1.9), (-2.7, 1.5), (-1.5, 2.9))):
    light("ShelfLamp%d" % i, 'POINT', (x, y, 2.6), 25, (1.0, 0.8, 0.55), 0.3)
light("CeilBlue", 'AREA', (0, 0, 3.3), 60, (0.5, 0.65, 1.0), 4.0, rot=(0, 0, 0))

# =================================================================== FBI OFFICE (x = 40): agent at a desk facing -Y
CF = col("SetOffice"); OX = 40.0
plane("OffFloor", CF, (OX, 0, 0), (12, 12), mat("OffCarpet", (0.2, 0.25, 0.33), 0.9))
plane("OffCeil", CF, (OX, 0, 3.0), (12, 12), mat("OffCeil", (0.85, 0.87, 0.9), 0.8), (R_(180), 0, 0))
owm = mat("OffWall", (0.72, 0.76, 0.8), 0.75)
plane("OffWallBack", CF, (OX, -2.4, 1.5), (12, 3.0), owm, (R_(90), 0, 0))
plane("OffWallFront", CF, (OX, 3.4, 1.5), (12, 3.0), owm, (R_(90), 0, 0))
plane("OffWallL", CF, (OX - 3.2, 0, 1.5), (12, 3.0), owm, (R_(90), 0, R_(90)))
plane("OffWallR", CF, (OX + 3.2, 0, 1.5), (12, 3.0), owm, (R_(90), 0, R_(90)))
odesk = append_coll(A + "ph/metal_office_desk/metal_office_desk_1k.blend", "metal_office_desk", CF, (OX, -0.75, 0), 0, 0.95, "OffDesk")
OD_TOP = 0.788 * 0.95
PCO = dup_tree(PCR, CF, (OX + 0.15, -0.95, OD_TOP + 0.089 * S_PC), R_(90), "PC_Off")
SCR_O = make_screen(PCO, "Screen_Off")
# drop the keyboard copy's offset (keep as in template)
ochair = dup_tree(chair, CF, (OX, 0.08, 0), 0, "OffChair")
cab = append_coll(A + "ph/drawer_cabinet/drawer_cabinet_1k.blend", "drawer_cabinet", CF, (OX + 2.5, -2.05, 0.084), 0, 0.85, "OffCabinet")
# archive box with our logo on its front (faces +Y, toward the room)
card = mat("Cardboard", (0.62, 0.45, 0.27), 0.7)
bx = box("ArchiveBox", CF, (OX - 0.62, -0.62, OD_TOP + 0.13), (0.42, 0.3, 0.26), card, 0.006)
box("ArchiveLid", CF, (OX - 0.62, -0.62, OD_TOP + 0.27), (0.44, 0.32, 0.04), card, 0.004)
logo_decal("Logo_Box", CF, bx, (OX - 0.62, -0.62 + 0.151, OD_TOP + 0.13), (0, 1, 0), (0, 0, 1), 0.34, dark=True)
box("FolderStack", CF, (OX + 0.62, -0.6, OD_TOP + 0.02), (0.3, 0.22, 0.04), mat("FolderBuff", (0.85, 0.7, 0.35), 0.6), 0.003)
# pinboard: cork, photos (generic silhouettes, no text), red string between pins
pb_ = box("Pinboard", CF, (OX + 0.0, -2.36, 1.75), (2.2, 0.03, 1.1), mat("Cork", (0.62, 0.42, 0.24), 0.85), 0.01)
box("PinboardFrame", CF, (OX + 0.0, -2.375, 1.75), (2.3, 0.02, 1.2), mat("PinFrame", (0.25, 0.2, 0.15), 0.5))
PHOTOS = []
for i, (u, v) in enumerate(((-0.8, 0.25), (-0.25, -0.25), (0.3, 0.3), (0.85, -0.2), (-0.65, -0.35), (0.6, 0.35))):
    p = box("Photo%d" % i, CF, (OX + u, -2.335, 1.75 + v), (0.24, 0.006, 0.3), mat("PhotoWhite", (0.92, 0.92, 0.9), 0.5))
    box("PhotoImg%d" % i, CF, (OX + u, -2.330, 1.77 + v), (0.2, 0.004, 0.2), mat("PhotoBlue%d" % (i % 3), [(0.35, 0.5, 0.7), (0.5, 0.55, 0.45), (0.6, 0.45, 0.4)][i % 3], 0.6))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(OX + u, -2.326, 1.80 + v)); hh = bpy.context.object; hh.name = "PhotoHead%d" % i
    hh.scale = (1, 0.15, 1.15); hh.data.materials.append(mat("Silhouette", (0.15, 0.17, 0.2), 0.7))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, location=(OX + u, -2.326, 1.70 + v)); bb_ = bpy.context.object; bb_.name = "PhotoBody%d" % i
    bb_.scale = (1, 0.15, 0.55); bb_.data.materials.append(mat("Silhouette", (0.15, 0.17, 0.2), 0.7))
    box("Pin%d" % i, CF, (OX + u, -2.322, 1.89 + v), (0.018, 0.012, 0.018), mat("PinRed", (0.85, 0.08, 0.08), 0.35), 0.004)
    PHOTOS.append(Vector((OX + u, -2.318, 1.89 + v)))
for o in list(bpy.context.scene.collection.objects):
    if o.name.startswith(("PhotoHead", "PhotoBody")):
        bpy.context.scene.collection.objects.unlink(o); CF.objects.link(o)
for a_, b_ in ((0, 1), (1, 2), (2, 3), (1, 4), (2, 5), (0, 2)):
    cu = bpy.data.curves.new("String%d%d" % (a_, b_), 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0025
    sp = cu.splines.new('POLY'); sp.points.add(1); sp.points[0].co = (*PHOTOS[a_], 1); sp.points[1].co = (*PHOTOS[b_], 1)
    o = bpy.data.objects.new("String%d%d" % (a_, b_), cu); CF.objects.link(o); cu.materials.append(mat("StringRed", (0.8, 0.05, 0.05), 0.5))
light("OffPanel1", 'AREA', (OX, -0.2, 2.95), 180, (0.95, 0.97, 1.0), 2.0, rot=(0, 0, 0), c=CF)
light("OffPanel2", 'AREA', (OX, 2.0, 2.95), 120, (0.95, 0.97, 1.0), 2.0, rot=(0, 0, 0), c=CF)
light("OffFill", 'AREA', (OX - 1.2, -1.8, 1.6), 8, (0.9, 0.95, 1.0), 1.0, target=(OX, 0, 1.2), c=CF)
light("OffMagenta", 'AREA', (OX + 2.8, 1.5, 2.2), 40, (0.9, 0.4, 0.8), 1.5, target=(OX, 0, 1.2), c=CF)

# =================================================================== INTERROGATION ROOM (x = 80): table along X, kid/mom at -X side facing +X
CI = col("SetInterrogation"); IX = 80.0
plane("IntFloor", CI, (IX, 0, 0), (10, 10), mat("IntFloor", (0.32, 0.34, 0.36), 0.6))
plane("IntCeil", CI, (IX, 0, 2.9), (10, 10), mat("IntCeil", (0.6, 0.62, 0.65), 0.8), (R_(180), 0, 0))
iwm = mat("IntWall", (0.5, 0.55, 0.6), 0.8)
plane("IntWallBack", CI, (IX, 2.0, 1.45), (10, 2.9), iwm, (R_(90), 0, 0))
plane("IntWallFront", CI, (IX, -2.6, 1.45), (10, 2.9), iwm, (R_(90), 0, 0))
plane("IntWallL", CI, (IX - 2.4, 0, 1.45), (10, 2.9), iwm, (R_(90), 0, R_(90)))
plane("IntWallR", CI, (IX + 2.4, 0, 1.45), (10, 2.9), iwm, (R_(90), 0, R_(90)))
# wall panel seams so the walls are not flat sheets
for i in range(-4, 5):
    box("IntSeamB%d" % i, CI, (IX + i * 1.0, 1.985, 1.45), (0.012, 0.01, 2.9), mat("IntSeam", (0.38, 0.42, 0.47), 0.8))
box("IntDado", CI, (IX, 1.97, 0.9), (4.8, 0.04, 0.08), mat("IntSeam", (0.38, 0.42, 0.47), 0.8))
itab = append_coll(A + "ph/wooden_table_02/wooden_table_02_1k.blend", "wooden_table_02", CI, (IX, 0, 0), R_(90), 0.95, "IntTable")
for o in itab.children:
    o.data = o.data.copy()
    mm = mat("IntTableTop", (0.55, 0.58, 0.6), 0.35, 0.5)
    o.data.materials.clear(); o.data.materials.append(mm)
IT_TOP = 0.799 * 0.95
chA = append_coll(A + "ph/plastic_monobloc_chair_01/plastic_monobloc_chair_01_1k.blend", "plastic_monobloc_chair_01", CI, (IX - 0.62, 0, 0), R_(-90), 1.0, "IntChairKid")
chB = dup_tree(chA, CI, (IX + 0.62, 0, 0), R_(90), "IntChairAgent")
for o in chA.children + chB.children:
    for m in o.data.materials:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED' and not n.inputs["Base Color"].links: n.inputs["Base Color"].default_value = (0.2, 0.25, 0.32, 1)
# hanging lamp over the table
bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.28, radius2=0.08, depth=0.22, location=(IX, 0, 2.15)); sh_ = bpy.context.object; sh_.name = "IntLampShade"
sh_.data.materials.append(mat("LampShade", (0.15, 0.2, 0.18), 0.4, 0.6))
so_ = sh_.modifiers.new("s", 'SOLIDIFY'); so_.thickness = 0.01
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.006, depth=0.65, location=(IX, 0, 2.58)); cb_ = bpy.context.object; cb_.name = "IntLampCord"
cb_.data.materials.append(mat("CordBlack", (0.05, 0.05, 0.05), 0.5))
for o in (sh_, cb_):
    for cc in o.users_collection: cc.objects.unlink(o)
    CI.objects.link(o)
light("IntLamp", 'SPOT', (IX, 0, 2.05), 260, (1.0, 0.92, 0.8), 0.15, rot=(0, 0, 0), c=CI).data.spot_size = R_(110)
light("IntFill", 'AREA', (IX - 1.6, -1.6, 1.7), 8, (0.85, 0.92, 1.0), 1.2, target=(IX, 0, 1.1), c=CI)
light("IntFill2", 'AREA', (IX + 1.6, -1.6, 1.7), 8, (0.85, 0.92, 1.0), 1.2, target=(IX, 0, 1.1), c=CI)
light("IntAmb", 'AREA', (IX, 0, 2.85), 70, (0.75, 0.82, 0.95), 3.5, rot=(0, 0, 0), c=CI)

for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons: pass
bpy.data.collections.remove(bpy.data.collections["PC_Template"]) if not bpy.data.collections["PC_Template"].objects else None
shroot.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SETS_OK", "DESK_TOP", DESK_TOP, "KB_TOP", KB_TOP, "KB", KB_LO, KB_HI, "JACK", JACK)
