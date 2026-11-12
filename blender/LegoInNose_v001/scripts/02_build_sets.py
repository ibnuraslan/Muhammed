"""Sets for LegoInNose: living room, bedroom, bathroom/shower, cyan studio + sagittal cross-section, toy bricks.
blender -b humans.blend --python 02_build_sets.py -- <assets_dir> <out.blend>"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

A = sys.argv[sys.argv.index("--") + 1:]
AS, OUT = A[0], A[1]
R_ = math.radians
random.seed(3)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, 2310
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.image_settings.file_format = "PNG"

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in sc.collection.children: sc.collection.children.link(c)
    return c
ROOM, BED, BATH, STUDIO, PROPS = coll("Set_LivingRoom"), coll("Set_Bedroom"), coll("Set_Bathroom"), coll("Set_Studio"), coll("Props")

# ------------------------------------------------------------------ materials
def img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im
def pbr(name, tex, scale=1.0, tint=None, rough_mul=1.0, bump=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bs = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["UV"], mp.inputs[0])
    d = os.path.join(AS, tex, "textures")
    fs = sorted(os.listdir(d))
    def f(key):
        for x in fs:
            if key in x: return os.path.join(d, x)
    di = N.new("ShaderNodeTexImage"); di.image = img(f("_diff_") or f("_col_")); L.new(mp.outputs[0], di.inputs[0])
    if tint:
        mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
        L.new(di.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); L.new(mx.outputs[2], bs.inputs["Base Color"])
    else:
        L.new(di.outputs[0], bs.inputs["Base Color"])
    r = f("_rough_")
    if r:
        ri = N.new("ShaderNodeTexImage"); ri.image = img(r, True); L.new(mp.outputs[0], ri.inputs[0])
        mm = N.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = rough_mul
        L.new(ri.outputs[0], mm.inputs[0]); L.new(mm.outputs[0], bs.inputs["Roughness"])
    n = f("_nor_gl_")
    if n:
        ni = N.new("ShaderNodeTexImage"); ni.image = img(n, True); L.new(mp.outputs[0], ni.inputs[0])
        nm = N.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = bump
        L.new(ni.outputs[0], nm.inputs[1]); L.new(nm.outputs[0], bs.inputs["Normal"])
    return m
def flat(name, col, rough=0.5, metal=0.0, sss=0.0, transm=0.0, emit=None, es=0.0, alpha=1.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if sss: b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.02, 0.01, 0.005)
    if transm: b.inputs["Transmission Weight"].default_value = transm
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    if coat: b.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*col, 1)
    return m

def link(o, c):
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o); return o
def box(name, c, size, loc, mat=None, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bm_ = o.modifiers.new("bev", "BEVEL"); bm_.width = bevel; bm_.segments = 2
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode="OBJECT")
    if mat: o.data.materials.append(mat)
    return link(o, c)
def cyl(name, c, r, d, loc, mat=None, rot=(0, 0, 0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object; o.name = name
    if mat: o.data.materials.append(mat)
    return link(o, c)
def append_model(key, c, loc, rot_z=0.0, scale=1.0, name=None):
    p = os.path.join(AS, key, key + "_1k.blend")
    with bpy.data.libraries.load(p, link=False) as (s, d):
        d.objects = [n for n in s.objects if not n.startswith("wdg_")]
    root = bpy.data.objects.new(name or ("M_" + key), None); c.objects.link(root)
    for o in d.objects:
        if o is None: continue
        c.objects.link(o)
        if o.parent is None: o.parent = root
    root.location = loc; root.rotation_euler = (0, 0, rot_z); root.scale = (scale,) * 3
    return root

# ------------------------------------------------------------------ clothes: remove the printed logo from the T-shirts (non-blue pixels -> plain shirt blue)
for ob in bpy.data.objects:
    if ob.type != "MESH" or not any(k in ob.name for k in ("casualsuit04", "casualsuit02", "female_casualsuit01")): continue
    for ms in ob.material_slots:
        m = ms.material
        if not m or not m.use_nodes: continue
        nt = m.node_tree
        for lk in list(nt.links):
            if lk.from_node.type == "TEX_IMAGE" and lk.from_node.name == "diffuseTexture" and lk.to_socket.name != "Alpha":
                src = lk.from_socket; dst = lk.to_socket
                sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(src, sep.inputs[0])
                sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
                nt.links.new(sep.outputs[2], sub.inputs[0]); nt.links.new(sep.outputs[0], sub.inputs[1])
                mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.05; mr.inputs[2].default_value = 0.18
                nt.links.new(sub.outputs[0], mr.inputs[0])
                mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
                mx.inputs[6].default_value = (0.03, 0.12, 0.36, 1)
                # also replace bright (light-blue / white) print lines: keep only blue pixels that are not bright
                mr2 = nt.nodes.new("ShaderNodeMapRange"); mr2.inputs[1].default_value = 0.22; mr2.inputs[2].default_value = 0.34
                nt.links.new(sep.outputs[1], mr2.inputs[0])
                inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; nt.links.new(mr2.outputs[0], inv.inputs[1])
                mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; nt.links.new(mr.outputs[0], mul.inputs[0]); nt.links.new(inv.outputs[0], mul.inputs[1])
                nt.links.new(mul.outputs[0], mx.inputs[0]); nt.links.new(src, mx.inputs[7])
                nt.links.new(mx.outputs[2], dst)
                print("DELOGO", ob.name, m.name)

# eyes: no refraction through the cornea (refractive caustics are off, which would leave the iris black)
for m_ in bpy.data.materials:
    if m_.use_nodes and m_.name.endswith("high-poly"):
        for n_ in m_.node_tree.nodes:
            if n_.type == "GROUP" and "OuterLayerTransmission" in n_.inputs:
                pass
                print("EYES", m_.name)

# ------------------------------------------------------------------ living room  (x -2.8..2.8, y -2.6..2.4, h 2.7)
M_FLOOR = pbr("M_Floor", "laminate_floor_02", 1.0)
M_WALL = pbr("M_Wall_Living", "painted_plaster_wall", 0.7, tint=(0.95, 0.86, 0.72), bump=0.15)
M_WALLB = pbr("M_Wall_Bed", "beige_wall_001", 0.7, tint=(0.75, 0.82, 0.92), bump=0.15)
M_TILE = pbr("M_Tiles", "long_white_tiles", 1.0, rough_mul=0.5, bump=0.4)
M_RUG = pbr("M_Rug", "fabric_pattern_07", 2.0, bump=0.5)
M_CEIL = flat("M_Ceiling", (0.85, 0.83, 0.8), 0.9)
M_FRAME = flat("M_WindowFrame", (0.92, 0.92, 0.9), 0.4)
M_TRIM = flat("M_Trim", (0.9, 0.88, 0.84), 0.5)
M_CURT = flat("M_Curtain", (0.55, 0.32, 0.22), 0.9, sss=0.1)
H = 2.7
def room_shell(prefix, c, x0, x1, y0, y1, mat_wall, holes, floor_mat, ceil=True, thick=0.12):
    """walls as boxes, leaving rectangular holes: holes = [(wall, centre_along, width, z0, z1)] wall in N,S,E,W"""
    box(prefix + "_Floor", c, (x1 - x0 + 0.3, y1 - y0 + 0.3, 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, -0.05), floor_mat)
    if ceil: box(prefix + "_Ceiling", c, (x1 - x0 + 0.3, y1 - y0 + 0.3, 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, H + 0.05), M_CEIL)
    walls = {"N": ((x0, y1), (x1, y1)), "S": ((x0, y0), (x1, y0)), "W": ((x0, y0), (x0, y1)), "E": ((x1, y0), (x1, y1))}
    for w, (a, b) in walls.items():
        horiz = w in "NS"
        lo, hi = (a[0], b[0]) if horiz else (a[1], b[1])
        fixed = a[1] if horiz else a[0]
        hs = sorted([h for h in holes if h[0] == w], key=lambda h: h[1])
        segs = []; cur = lo
        for _, cen, wd, z0, z1 in hs:
            segs.append((cur, cen - wd / 2, 0, H)); segs.append((cen - wd / 2, cen + wd / 2, 0, z0)); segs.append((cen - wd / 2, cen + wd / 2, z1, H))
            cur = cen + wd / 2
        segs.append((cur, hi, 0, H))
        for i, (s0, s1, z0, z1) in enumerate(segs):
            if s1 - s0 < 1e-3 or z1 - z0 < 1e-3: continue
            ctr = (s0 + s1) / 2
            loc = (ctr, fixed, (z0 + z1) / 2) if horiz else (fixed, ctr, (z0 + z1) / 2)
            size = (s1 - s0, thick, z1 - z0) if horiz else (thick, s1 - s0, z1 - z0)
            box("%s_Wall%s%d" % (prefix, w, i), c, size, loc, mat_wall)
        # skirting
        loc = ((lo + hi) / 2, fixed + (0.065 if w == "S" else -0.065), 0.05) if horiz else (fixed + (0.065 if w == "W" else -0.065), (lo + hi) / 2, 0.05)
        box("%s_Skirt%s" % (prefix, w), c, ((hi - lo), 0.02, 0.1) if horiz else (0.02, hi - lo, 0.1), loc, M_TRIM)

WIN = (-1.2, 1.7, 0.75, 2.25)        # living room window: centre x, width, sill z, top z  (north wall y=2.4)
DOOR = (1.65, 0.95, 0.0, 2.1)          # door in east wall x=2.8: centre y, width
room_shell("LR", ROOM, -2.8, 2.8, -2.6, 2.4, M_WALL, [("N", WIN[0], WIN[1], WIN[2], WIN[3]), ("E", DOOR[0], DOOR[1], DOOR[2], DOOR[3])], M_FLOOR)
# window frame + mullion + sill + curtains
wx, ww, wz0, wz1 = WIN
for nm, sz, lc in (("L", (0.07, 0.16, wz1 - wz0), (wx - ww / 2, 2.4, (wz0 + wz1) / 2)), ("R", (0.07, 0.16, wz1 - wz0), (wx + ww / 2, 2.4, (wz0 + wz1) / 2)),
                   ("T", (ww, 0.16, 0.07), (wx, 2.4, wz1)), ("B", (ww + 0.2, 0.3, 0.05), (wx, 2.32, wz0)), ("M", (0.05, 0.08, wz1 - wz0), (wx, 2.4, (wz0 + wz1) / 2)),
                   ("H", (ww, 0.08, 0.05), (wx, 2.4, wz0 + (wz1 - wz0) * 0.62))):
    box("LR_Window" + nm, ROOM, sz, lc, M_FRAME)
for s in (-1, 1):
    cur = box("LR_Curtain%d" % s, ROOM, (0.45, 0.06, 2.4), (wx + s * (ww / 2 + 0.2), 2.28, 1.3), M_CURT)
    sw = cur.modifiers.new("wave", "WAVE"); sw.use_normal = False; sw.use_x = False; sw.use_y = True; sw.height = 0.04; sw.width = 0.12; sw.speed = 0.0
    sub = cur.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2; cur.modifiers.move(1, 0)
# door frame
for nm, sz, lc in (("A", (0.16, 0.06, 2.1), (2.8, DOOR[0] - DOOR[1] / 2, 1.05)), ("B", (0.16, 0.06, 2.1), (2.8, DOOR[0] + DOOR[1] / 2, 1.05)),
                   ("T", (0.16, DOOR[1] + 0.12, 0.06), (2.8, DOOR[0], 2.1))):
    box("LR_Door" + nm, ROOM, sz, lc, M_TRIM)
# rug
rug = box("LR_Rug", ROOM, (2.6, 1.9, 0.012), (0.1, 0.05, 0.006), M_RUG, bevel=0.004)
# furniture (Poly Haven CC0)
append_model("Sofa_01", ROOM, (1.25, 1.85, 0), R_(0), name="LR_Sofa")
append_model("throw_pillows_01", ROOM, (0.65, 1.85, 0.45), R_(-10), name="LR_Pillows")
append_model("CoffeeTable_01", ROOM, (-1.9, -0.4, 0), R_(90), name="LR_CoffeeTable")
append_model("painted_wooden_bench", ROOM, (WIN[0], 2.0, 0), R_(180), name="LR_Bench")
append_model("wooden_bookshelf_worn", ROOM, (-2.55, 0.9, 0), R_(-90), name="LR_Bookshelf")
append_model("potted_plant_01", ROOM, (-2.4, 2.05, 0), 0, 1.3, name="LR_Plant")
append_model("potted_plant_01", ROOM, (2.45, -1.9, 0), 1.0, 1.1, name="LR_Plant2")
append_model("wall_clock", ROOM, (1.25, 2.33, 1.85), 0, 1.0, name="LR_WallClock")
append_model("modern_ceiling_lamp_01", ROOM, (0.0, 0.0, H), 0, 1.0, name="LR_CeilingLamp")
append_model("Television_01", ROOM, (-1.9, -0.4, 0.45), R_(90), name="LR_TV")
# sleeping cat on the sofa (CC-BY scan, see CREDITS.md); breathing keyed in 03b
cp = os.path.join(AS, "cat", "cat.glb")
if os.path.exists(cp):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=cp)
    new = [o for o in bpy.data.objects if o not in before]
    catr = bpy.data.objects.new("LR_Cat", None); ROOM.objects.link(catr)
    for o in new:
        link(o, ROOM)
        if o.parent is None: o.parent = catr
    bpy.context.view_layer.update()
    cs = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(c[i] for c in cs) for i in range(3)]); hi = Vector([max(c[i] for c in cs) for i in range(3)])
    s_ = 0.62 / max(hi.x - lo.x, hi.y - lo.y)
    for o in new:
        if o.parent is catr: o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    catr.scale = (s_,) * 3; catr.location = (1.62, 1.82, 0.43); catr.rotation_euler = (0, 0, R_(160))
    print("CAT", [o.name for o in new], s_, hi - lo)
# time-lapse props: the teen's gamepad and the man's laptop
append_model("gamepad", PROPS, (50, 50, 0), 0, 1.0, name="Prop_Gamepad")
# picture frames (abstract colour fields, no text)
for i, (x, col) in enumerate(((-0.1, (0.3, 0.45, 0.6)), (0.25, (0.75, 0.55, 0.3)))):
    box("LR_Frame%d" % i, ROOM, (0.3, 0.03, 0.4), (x, 2.33, 1.75 + 0.05 * i), flat("M_Art%d" % i, col, 0.8), bevel=0.004)

# ------------------------------------------------------------------ bedroom (x 2.8..6.4, y -1.2..2.4)
room_shell("BR", BED, 2.8, 6.4, -1.2, 2.4, M_WALLB, [("W", DOOR[0], DOOR[1], DOOR[2], DOOR[3]), ("N", 3.6, 1.0, 0.9, 2.1)], M_FLOOR)
append_model("old_bed_frame", BED, (5.1, 1.35, 0), R_(180), name="BR_Bed")
append_model("ClassicNightstand_01", BED, (6.0, 2.1, 0), 0, name="BR_Nightstand")
append_model("alarm_clock_01", BED, (6.0, 2.1, 0.62), R_(200), name="BR_AlarmClock")
# blinds over the bedroom window (slats cast moonlight stripes)
M_BLIND = flat("M_Blind", (0.85, 0.85, 0.82), 0.6)
for i in range(14):
    box("BR_Slat%02d" % i, BED, (1.0, 0.05, 0.012), (3.6, 2.33, 0.95 + i * 0.083), M_BLIND, rot=(R_(35), 0, 0))
M_SHEET = flat("M_Sheet", (0.78, 0.8, 0.86), 0.85, sss=0.05)
M_DUVET = flat("M_Duvet", (0.25, 0.33, 0.5), 0.9, sss=0.05)
box("BR_Mattress", BED, (0.86, 1.92, 0.2), (5.1, 1.35, 0.46), M_SHEET, bevel=0.05)
box("BR_Pillow", BED, (0.6, 0.38, 0.12), (5.1, 2.08, 0.6), M_SHEET, bevel=0.05)
# tissues + box on the living-room bench and floor
M_TISSUE = flat("M_Tissue", (0.95, 0.95, 0.93), 0.9, sss=0.2)
box("LR_TissueBox", ROOM, (0.24, 0.12, 0.1), (WIN[0] - 0.38, 2.0, 0.52), flat("M_TissueBox", (0.35, 0.55, 0.65), 0.6), bevel=0.005)
for i in range(14):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.035, subdivisions=2, location=(WIN[0] + random.uniform(-0.7, 0.6), random.uniform(1.0, 1.7), 0.02))
    t_ = bpy.context.active_object; t_.name = "LR_TissueBall%02d" % i; t_.scale = (1, 1, 0.6); link(t_, ROOM); t_.data.materials.append(M_TISSUE)
    d_ = t_.modifiers.new("d", "DISPLACE"); tx = bpy.data.textures.get("TissueNoise") or bpy.data.textures.new("TissueNoise", "CLOUDS"); tx.noise_scale = 0.02; d_.texture = tx; d_.strength = 0.02
    t_.hide_render = True

# ------------------------------------------------------------------ bathroom (x 6.4..9.0, y -0.2..2.4)
room_shell("BA", BATH, 6.4, 9.0, -0.2, 2.4, M_TILE, [], M_TILE)
M_GLASS = flat("M_FrostedGlass", (0.5, 0.56, 0.6), 0.38, transm=1.0)
M_CHROME = flat("M_Chrome", (0.9, 0.9, 0.9), 0.08, metal=1.0)
M_GROUT = flat("M_ShowerTray", (0.95, 0.95, 0.95), 0.2, coat=0.5)
box("BA_ShowerTray", BATH, (1.2, 1.1, 0.06), (8.35, 1.8, 0.03), M_GROUT, bevel=0.01)
M_CLEAR = flat("M_ClearGlass", (0.95, 0.98, 1.0), 0.03, transm=1.0)
# frosted up to 1.42 m (modesty: everything below the chest is behind frosted glass from every camera angle), clear above
box("BA_GlassPanel", BATH, (0.015, 1.05, 1.36), (7.73, 1.82, 0.74), M_GLASS)
box("BA_GlassPanelTop", BATH, (0.015, 1.05, 0.56), (7.73, 1.82, 1.70), M_CLEAR)
box("BA_GlassFront", BATH, (0.6, 0.015, 1.36), (8.05, 1.26, 0.74), M_GLASS)
box("BA_GlassFrontTop", BATH, (0.6, 0.015, 0.56), (8.05, 1.26, 1.70), M_CLEAR)
box("BA_GlassRail", BATH, (0.02, 1.05, 0.02), (7.73, 1.82, 1.42), M_CHROME)
box("BA_GlassRailF", BATH, (0.6, 0.02, 0.02), (8.05, 1.26, 1.42), M_CHROME)
cyl("BA_ShowerPipe", BATH, 0.012, 1.0, (8.85, 2.25, 1.6), M_CHROME)
cyl("BA_ShowerArm", BATH, 0.012, 0.35, (8.75, 2.1, 2.1), M_CHROME, rot=(0, R_(90), R_(35)))
head = cyl("BA_ShowerHead", BATH, 0.1, 0.03, (8.6, 1.95, 2.08), M_CHROME, verts=40)
box("BA_Niche", BATH, (0.5, 0.12, 0.3), (8.35, 2.35, 1.25), flat("M_Niche", (0.85, 0.85, 0.85), 0.3))
for i, (col, h_) in enumerate((((0.2, 0.5, 0.7), 0.2), ((0.85, 0.55, 0.65), 0.17), ((0.95, 0.9, 0.8), 0.15))):
    cyl("BA_Bottle%d" % i, BATH, 0.03, h_, (8.18 + i * 0.1, 2.33, 1.12 + h_ / 2), flat("M_Bottle%d" % i, col, 0.25, coat=0.3), verts=20)
append_model("rubber_duck_toy", BATH, (8.6, 2.3, 1.11), R_(200), 0.35, name="BA_Duck")
append_model("ornate_mirror_01", BATH, (6.48, 0.9, 1.5), R_(-90), 0.8, name="BA_Mirror")
box("BA_Towel", BATH, (0.06, 0.5, 0.7), (6.5, 1.8, 1.2), flat("M_Towel", (0.85, 0.55, 0.35), 0.95), bevel=0.02)

# ------------------------------------------------------------------ toy bricks (generic: studs only, no text)
BRICK_COLS = [(0.75, 0.04, 0.03), (0.95, 0.72, 0.02), (0.05, 0.25, 0.7), (0.08, 0.45, 0.12), (0.95, 0.95, 0.93), (0.9, 0.35, 0.05)]
def brick_mat(col, nm):
    m = flat(nm, col, 0.18, coat=0.6); return m
def make_brick(name, nx, ny, mat, c, unit=0.0080, h=0.0096):
    """real toy-brick proportions: 8 mm pitch, 9.6 mm height, 1.7 mm studs (no lettering)"""
    bm_ = bmesh.new()
    w, d = nx * unit - 0.0002, ny * unit - 0.0002
    bmesh.ops.create_cube(bm_, size=1.0)
    bmesh.ops.scale(bm_, vec=(w, d, h), verts=bm_.verts); bmesh.ops.translate(bm_, vec=(0, 0, h / 2), verts=bm_.verts)
    for i in range(nx):
        for j in range(ny):
            r = bmesh.ops.create_cone(bm_, cap_ends=True, segments=20, radius1=0.0024, radius2=0.0024, depth=0.0017)
            bmesh.ops.translate(bm_, vec=((i - (nx - 1) / 2) * unit, (j - (ny - 1) / 2) * unit, h + 0.00085), verts=r["verts"])
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); me.materials.append(mat)
    bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.0003; bv.segments = 2; bv.limit_method = "ANGLE"
    for p in me.polygons: p.use_smooth = True
    return o
MB_RED = brick_mat(BRICK_COLS[0], "M_Brick_Red"); MB_YEL = brick_mat(BRICK_COLS[1], "M_Brick_Yellow")
big = make_brick("Brick_Big", 2, 1, MB_RED, PROPS)
small = make_brick("Brick_Small", 1, 1, MB_YEL, PROPS)
# yellow glow (for the 'hidden' beat): emission keyed in 03
nt = MB_YEL.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Emission Color"].default_value = (1.0, 0.8, 0.2, 1); b.inputs["Emission Strength"].default_value = 0.0
# brick library for the tub + floor scatter
lib = []
for k, col in enumerate(BRICK_COLS):
    m = MB_RED if k == 0 else (MB_YEL if k == 1 else brick_mat(col, "M_Brick_%d" % k))
    for (nx, ny) in ((2, 2), (2, 4), (1, 2), (2, 3)):
        o = make_brick("BrickLib_%d_%dx%d" % (k, nx, ny), nx, ny, m, PROPS); o.hide_render = True; o.hide_viewport = True
        o.location = (50, 50, 0); lib.append(o)
# tub (clear blue plastic) at the boy's right
TUB = Vector((-0.27, 0.0, 0.0))
M_TUB = flat("M_Tub", (0.25, 0.55, 0.85), 0.25, transm=0.0, coat=0.5)
bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=0.16, location=TUB + Vector((0, 0, 0.08)), vertices=48)
tub = bpy.context.active_object; tub.name = "Prop_Tub"; link(tub, PROPS); tub.data.materials.append(M_TUB)
bpy.ops.object.mode_set(mode="EDIT"); bm_ = bmesh.from_edit_mesh(tub.data)
top = [f for f in bm_.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm_, geom=top, context="FACES")
bmesh.update_edit_mesh(tub.data); bpy.ops.object.mode_set(mode="OBJECT")
so = tub.modifiers.new("sol", "SOLIDIFY"); so.thickness = 0.006; tb = tub.modifiers.new("bev", "BEVEL"); tb.width = 0.003
def place_copy(src, loc, rot, c, name):
    o = src.copy(); o.data = src.data; o.hide_render = False; o.hide_viewport = False; o.name = name
    c.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
n = 0
for layer in range(5):
    for i in range(22 if layer < 4 else 12):
        a = random.random() * 2 * math.pi; r = 0.135 * math.sqrt(random.random())
        place_copy(random.choice(lib), TUB + Vector((r * math.cos(a), r * math.sin(a), 0.012 + layer * 0.018 + random.random() * 0.008)),
                   (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.random() * 6.3), PROPS, "TubBrick%03d" % n); n += 1
for i in range(40):     # spilled on the rug
    a = random.random() * 2 * math.pi; r = 0.2 + 0.55 * random.random()
    p = TUB + Vector((r * math.cos(a) - 0.25, r * math.sin(a) * 0.8 - 0.05, 0.012))
    rx = random.choice((0, 0, 0, math.pi / 2))
    if p.x > -0.12 and p.y < 0.5: p.x -= 0.45
    place_copy(random.choice(lib), p, (rx, 0, random.random() * 6.3), PROPS, "RugBrick%03d" % i)
# a little brick house the boy has been building
for i in range(9):
    place_copy(lib[4 * 2 + 1] if i % 2 else lib[4 * 3 + 1], Vector((-0.45 + (i % 3) * 0.033, -0.45, 0.012 + (i // 3) * 0.0096)), (0, 0, R_(90) * (i % 2)), PROPS, "HouseBrick%d" % i)

# ------------------------------------------------------------------ studio (soft cyan-to-white gradient sphere) below the floor
SC = Vector((0.0, 0.0, -7.0)); SR = 4.6
bpy.ops.mesh.primitive_uv_sphere_add(radius=SR, location=SC, segments=64, ring_count=32)
sph = bpy.context.active_object; sph.name = "Studio_Sphere"; link(sph, STUDIO)
for p in sph.data.polygons: p.use_smooth = True
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.flip_normals(); bpy.ops.object.mode_set(mode="OBJECT")
m = bpy.data.materials.new("M_StudioGradient"); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links
for n_ in list(N): N.remove(n_)
o_ = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); gc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
ramp = N.new("ShaderNodeValToRGB"); L.new(gc.outputs["Object"], sep.inputs[0])
mth = N.new("ShaderNodeMapRange"); mth.inputs[1].default_value = -SR; mth.inputs[2].default_value = SR
L.new(sep.outputs[2], mth.inputs[0]); L.new(mth.outputs[0], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (0.01, 0.04, 0.12, 1); ramp.color_ramp.elements[0].position = 0.1
ramp.color_ramp.elements[1].color = (0.08, 0.42, 0.52, 1); ramp.color_ramp.elements[1].position = 0.9
L.new(ramp.outputs[0], em.inputs[0]); em.inputs[1].default_value = 0.9; L.new(em.outputs[0], o_.inputs[0])
sph.data.materials.append(m)
box("Studio_Floor", STUDIO, (6, 6, 0.02), SC + Vector((0, 0, -1.6)), flat("M_StudioFloor", (0.05, 0.16, 0.22), 0.3))
st_floor = bpy.data.objects["Studio_Floor"]; st_floor.visible_camera = True
for i, (loc, e, sz) in enumerate(((Vector((-2.5, -2.5, 2.5)), 900, 2.5), (Vector((2.8, -1.0, 1.5)), 500, 2.0), (Vector((0.5, 2.8, 2.0)), 600, 2.0))):
    ld = bpy.data.lights.new("Studio_Key%d" % i, "AREA"); ld.energy = e; ld.size = sz; ld.color = (1.0, 0.98, 0.95) if i != 2 else (0.75, 0.9, 1.0)
    lo = bpy.data.objects.new("Studio_Key%d" % i, ld); STUDIO.objects.link(lo); lo.location = SC + loc
    tt = lo.constraints.new("TRACK_TO"); tt.target = sph; tt.track_axis = "TRACK_NEGATIVE_Z"; tt.up_axis = "UP_Y"
# --- cross-section head: the boy's own head, x6, sagittal cut through the left nasal cavity
boy = bpy.data.objects["Boy_Body"]
XS = 6.0
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(boy.evaluated_get(dg))
head_o = bpy.data.objects.new("XS_Head", me); STUDIO.objects.link(head_o)
head_o.matrix_world = boy.matrix_world.copy()
bm_ = bmesh.new(); bm_.from_mesh(me)
zs = [v.co.z for v in bm_.verts]
# neck cut: keep everything above the chin-ish level (head bone height - 0.13 m)
arm = bpy.data.objects["Boy"]
HB = arm.data.bones["head"].head_local.copy(); NB = arm.data.bones["neck01"].head_local.copy()
zcut = NB.z - 0.02
bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z < zcut], context="VERTS")
bm_.to_mesh(me); bm_.free()
# nostril landmark: the lowest-frontmost vertex region of the nose
vs = [v.co.copy() for v in me.vertices]
nose_tip = min(vs, key=lambda v: v.y)
print("NOSE_TIP", tuple(round(c, 4) for c in nose_tip), "HEAD", tuple(round(c, 3) for c in HB))
for p in me.polygons: p.use_smooth = True
me.materials.clear()
# skin material (front faces) + flat cut colour (back faces => reads as the cut surface)
mk = bpy.data.materials.new("M_XS_Skin"); mk.use_nodes = True; N = mk.node_tree.nodes; L = mk.node_tree.links
bs = N["Principled BSDF"]
skin_img = None
for mm in boy.data.materials:
    if mm and mm.use_nodes:
        for nn in mm.node_tree.nodes:
            if nn.type == "TEX_IMAGE" and nn.image and "diffuse" in nn.image.name.lower(): skin_img = nn.image
if skin_img:
    ti = N.new("ShaderNodeTexImage"); ti.image = skin_img; L.new(ti.outputs[0], bs.inputs["Base Color"])
else:
    bs.inputs["Base Color"].default_value = (0.8, 0.55, 0.45, 1)
bs.inputs["Roughness"].default_value = 0.5; bs.inputs["Subsurface Weight"].default_value = 0.15
bs.inputs["Subsurface Radius"].default_value = (0.05, 0.02, 0.01)
cut = N.new("ShaderNodeBsdfPrincipled"); cut.inputs["Base Color"].default_value = (0.55, 0.13, 0.14, 1); cut.inputs["Roughness"].default_value = 0.3
cut.inputs["Coat Weight"].default_value = 0.6; cut.inputs["Subsurface Weight"].default_value = 0.2
cnz = N.new("ShaderNodeTexNoise"); cnz.inputs["Scale"].default_value = 300; cbp = N.new("ShaderNodeBump"); cbp.inputs["Strength"].default_value = 0.4
L.new(cnz.outputs[0], cbp.inputs["Height"]); L.new(cbp.outputs[0], cut.inputs["Normal"])
ccr = N.new("ShaderNodeValToRGB"); ccr.color_ramp.elements[0].color = (0.4, 0.07, 0.08, 1); ccr.color_ramp.elements[1].color = (0.7, 0.24, 0.22, 1)
L.new(cnz.outputs[0], ccr.inputs[0]); L.new(ccr.outputs[0], cut.inputs["Base Color"])
geo = N.new("ShaderNodeNewGeometry"); mix = N.new("ShaderNodeMixShader")
L.new(geo.outputs["Backfacing"], mix.inputs[0]); L.new(bs.outputs[0], mix.inputs[1]); L.new(cut.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], N["Material Output"].inputs[0]); me.materials.append(mk)
# inner shell (front faces toward the cut): the camera sees real front-facing cut tissue, not back faces (QA INSIDE rule)
mcut = bpy.data.materials.new("M_XS_InnerCut"); mcut.use_nodes = True; bci = mcut.node_tree.nodes["Principled BSDF"]
bci.inputs["Base Color"].default_value = (0.78, 0.3, 0.32, 1); bci.inputs["Roughness"].default_value = 0.4; bci.inputs["Coat Weight"].default_value = 0.4
me.materials.append(mcut)
# sagittal cut: keep x > XCUT (the boy's left half). Boolean with a big box.
XCUT = nose_tip.x + 0.0085
bm_ = bmesh.new(); bm_.from_mesh(me)
bmesh.ops.bisect_plane(bm_, geom=bm_.verts[:] + bm_.edges[:] + bm_.faces[:], plane_co=(XCUT, 0, 0), plane_no=(-1, 0, 0), clear_outer=True)
bm_.to_mesh(me); bm_.free()
hair_src = [o for o in bpy.data.objects if o.name.startswith("Boy_") and "short02" in o.name]
XS_HAIR = None
if hair_src:
    hm_ = bpy.data.meshes.new_from_object(hair_src[0].evaluated_get(dg))
    bmh = bmesh.new(); bmh.from_mesh(hm_)
    bmesh.ops.bisect_plane(bmh, geom=bmh.verts[:] + bmh.edges[:] + bmh.faces[:], plane_co=(XCUT, 0, 0), plane_no=(-1, 0, 0), clear_outer=True)
    bmh.to_mesh(hm_); bmh.free()
    XS_HAIR = bpy.data.objects.new("XS_Hair", hm_); STUDIO.objects.link(XS_HAIR)
    for p in hm_.polygons: p.use_smooth = True
sol_ = head_o.modifiers.new("inner", "SOLIDIFY"); sol_.thickness = 0.004; sol_.offset = -1.0; sol_.use_flip_normals = False
sol_.use_rim = True; sol_.material_offset = 1; sol_.material_offset_rim = 1
# place: x6 in the studio, cut face toward -X (camera side), nose pointing -Y
PIV = Vector((XCUT, nose_tip.y + 0.05, HB.z))
head_o.matrix_world = Matrix.Translation(SC + Vector((0.0, 0.0, 0.25))) @ Matrix.Rotation(R_(-90), 4, "Z") @ Matrix.Scale(XS, 4) @ Matrix.Translation(-PIV)
# after rotation -90 about Z: model -Y (face front) -> world -X ; model +X (left side, kept) -> world -Y...
# we want the cut face (model -X normal) to face the camera, which sits at world -Y: model -X -> rot(-90) -> world +Y. Use +90 instead.
head_o.matrix_world = Matrix.Translation(SC + Vector((0.0, 0.0, 0.25))) @ Matrix.Rotation(R_(90), 4, "Z") @ Matrix.Scale(XS, 4) @ Matrix.Translation(-PIV)
XSM = head_o.matrix_world.copy()
if XS_HAIR: XS_HAIR.matrix_world = XSM
def xs(p):   # boy rest-space point -> studio world point
    return XSM @ Vector(p)
# inlays drawn on the cut plane (model x = XCUT + tiny offset into the head), in model (y, z) coords of the boy's rest head
def inlay(name, pts_yz, mat, depth=0.004, off=0.0006, bevel=0.0012):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "2D"; cu.fill_mode = "BOTH"; cu.extrude = depth / 2
    cu.bevel_depth = bevel
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts_yz) - 1); sp.use_cyclic_u = True
    for bp, (y, z) in zip(sp.bezier_points, pts_yz):
        bp.co = (y, z, 0); bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu); STUDIO.objects.link(o); cu.materials.append(mat)
    # curve plane (local x,y)=(model y, z) ; local z = model x
    Mloc = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    o.matrix_world = XSM @ Matrix.Translation((XCUT + off + depth / 2, 0, 0)) @ Mloc
    return o
# landmarks (boy rest space)
ny, nz = nose_tip.y, nose_tip.z
hy_back = max(v.y for v in vs if v.z > HB.z); top = max(v.z for v in vs)
L_ = hy_back - ny; Hh = top - zcut
def P(u, v):  # u: 0 = nose tip .. 1 = back of head ; v: 0 = cut level .. 1 = top
    return (ny + u * L_, zcut + v * Hh)
def tissue(name, c0, c1, rough=0.4, sss=0.0, coat=0.0, scale=600.0, bump=0.3, kind="noise", spec=0.5, sssr=(0.006, 0.002, 0.001)):
    """realistic tissue: colour varied between c0/c1 by noise, bump from noise / voronoi pores / wave folds, SSS + wet coat"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt_ = m.node_tree; N_ = nt_.nodes; L2 = nt_.links
    b_ = N_["Principled BSDF"]
    tc_ = N_.new("ShaderNodeTexCoord")
    nz_ = N_.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = scale * 0.15; nz_.inputs["Detail"].default_value = 8
    L2.new(tc_.outputs["Object"], nz_.inputs["Vector"])
    cr_ = N_.new("ShaderNodeValToRGB"); cr_.color_ramp.elements[0].color = (*c0, 1); cr_.color_ramp.elements[1].color = (*c1, 1)
    L2.new(nz_.outputs[0], cr_.inputs[0]); L2.new(cr_.outputs[0], b_.inputs["Base Color"])
    if kind == "pores":
        vo = N_.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale; L2.new(tc_.outputs["Object"], vo.inputs["Vector"]); hsrc = vo.outputs["Distance"]
    elif kind == "folds":
        wv = N_.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.inputs["Scale"].default_value = scale * 0.25; wv.inputs["Distortion"].default_value = 16
        wv.inputs["Detail"].default_value = 4; L2.new(tc_.outputs["Object"], wv.inputs["Vector"]); hsrc = wv.outputs[1]
    elif kind == "fibres":
        mp_ = N_.new("ShaderNodeMapping"); mp_.inputs["Scale"].default_value = (1, 1, 8); L2.new(tc_.outputs["Object"], mp_.inputs[0])
        nz2 = N_.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = scale; L2.new(mp_.outputs[0], nz2.inputs["Vector"]); hsrc = nz2.outputs[0]
    else:
        nz2 = N_.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = scale; nz2.inputs["Detail"].default_value = 10
        L2.new(tc_.outputs["Object"], nz2.inputs["Vector"]); hsrc = nz2.outputs[0]
    bp_ = N_.new("ShaderNodeBump"); bp_.inputs["Strength"].default_value = bump; L2.new(hsrc, bp_.inputs["Height"]); L2.new(bp_.outputs[0], b_.inputs["Normal"])
    b_.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in b_.inputs: b_.inputs["Specular IOR Level"].default_value = spec
    if sss: b_.inputs["Subsurface Weight"].default_value = sss; b_.inputs["Subsurface Radius"].default_value = sssr
    if coat:
        b_.inputs["Coat Weight"].default_value = coat; b_.inputs["Coat Roughness"].default_value = 0.05
        L2.new(bp_.outputs[0], b_.inputs["Coat Normal"])
    m.diffuse_color = (*c0, 1)
    return m
M_BONE = tissue("M_XS_Bone", (0.5, 0.4, 0.27), (0.78, 0.7, 0.55), rough=0.62, sss=0.05, scale=1600, bump=0.45, kind="pores")
M_BRAIN = tissue("M_XS_Brain", (0.5, 0.3, 0.32), (0.68, 0.46, 0.47), rough=0.38, sss=0.3, coat=0.4, scale=700, bump=0.7, kind="folds")
M_MUC = tissue("M_XS_Mucosa", (0.45, 0.05, 0.07), (0.78, 0.22, 0.24), rough=0.2, sss=0.45, coat=1.0, scale=900, bump=0.35)
M_AIR = tissue("M_XS_Airway", (0.12, 0.02, 0.03), (0.32, 0.06, 0.07), rough=0.25, sss=0.2, coat=1.0, scale=700, bump=0.5)
M_TONGUE = tissue("M_XS_Tongue", (0.5, 0.1, 0.12), (0.72, 0.25, 0.27), rough=0.3, sss=0.4, coat=0.8, scale=2200, bump=0.4, kind="pores")
M_CART = tissue("M_XS_Cartilage", (0.7, 0.74, 0.78), (0.9, 0.9, 0.93), rough=0.22, sss=0.6, coat=0.7, scale=500, bump=0.1, sssr=(0.01, 0.01, 0.012))
# brain (upper back) and skull band around it
brain_pts = [P(0.30, 0.62), P(0.33, 0.80), P(0.45, 0.93), P(0.62, 0.96), P(0.80, 0.88), P(0.90, 0.70), P(0.86, 0.52), P(0.70, 0.46), P(0.52, 0.48), P(0.38, 0.52)]
skull_pts = [P(0.26, 0.60), P(0.29, 0.83), P(0.43, 0.97), P(0.62, 1.0), P(0.83, 0.92), P(0.95, 0.70), P(0.92, 0.45), P(0.86, 0.38),
             P(0.70, 0.40), P(0.52, 0.42), P(0.40, 0.45), P(0.32, 0.47)]
def organ(name, ctr_uv, rad, mat, cut_col, tex_type="STUCCI", tsize=0.01, strength=0.004, rot_x=0.0, gyri=False):
    """displaced organic solid (not a slab): ellipsoid + procedural displacement, applied, then cut on the sagittal plane"""
    y_, z_ = P(*ctr_uv)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0, location=(XCUT + rad[0] * 0.35, y_, z_))
    o = bpy.context.active_object; o.name = name; o.scale = rad; o.rotation_euler = (R_(rot_x), 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    sb = o.modifiers.new("sub", "SUBSURF"); sb.levels = 2
    tx = bpy.data.textures.new(name + "_Tex", tex_type); tx.noise_scale = tsize
    if gyri: tx.noise_basis = "VORONOI_F2"; tx.turbulence = 8.0
    dm = o.modifiers.new("dsp", "DISPLACE"); dm.texture = tx; dm.strength = strength; dm.texture_coords = "GLOBAL"
    sm = o.modifiers.new("sm", "SMOOTH"); sm.iterations = 2; sm.factor = 0.4
    dg2 = bpy.context.evaluated_depsgraph_get(); me3 = bpy.data.meshes.new_from_object(o.evaluated_get(dg2))
    o.modifiers.clear(); old = o.data; o.data = me3; bpy.data.meshes.remove(old)
    cut_keep_left(me3)
    for p_ in me3.polygons: p_.use_smooth = True
    me3.materials.clear(); me3.materials.append(two_sided(name + "_M", mat, cut_col, 0.5))
    link(o, STUDIO); o.matrix_world = XSM @ o.matrix_world
    return o
# --- real anatomy: a scanned human skull and a CT-style nasal cavity / paranasal sinus cast (CC-BY, see CREDITS.md),
#     fitted into the boy's head, cut on the same sagittal plane, shaded as wet mucosa / porous bone with cut faces.
def import_glb_mesh(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    bpy.context.view_layer.update()
    bm2 = bmesh.new()
    for o in meshes:
        me2 = o.data.copy(); me2.transform(o.matrix_world); bm2.from_mesh(me2); bpy.data.meshes.remove(me2)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    me2 = bpy.data.meshes.new(name); bm2.to_mesh(me2); bm2.free()
    return me2
def fit(me2, y0, y1, z_top=None, z_bot=None, x_c=0.0):
    vs2 = [v.co for v in me2.vertices]
    lo = Vector([min(v[i] for v in vs2) for i in range(3)]); hi = Vector([max(v[i] for v in vs2) for i in range(3)])
    s2 = (y1 - y0) / (hi.y - lo.y)
    tz = (z_top - hi.z * s2) if z_top is not None else (z_bot - lo.z * s2)
    me2.transform(Matrix.Translation(Vector((x_c - (lo.x + hi.x) / 2 * s2, y0 - lo.y * s2, tz))) @ Matrix.Scale(s2, 4))
    return s2
def cut_keep_left(me2):
    bm2 = bmesh.new(); bm2.from_mesh(me2)
    bmesh.ops.bisect_plane(bm2, geom=bm2.verts[:] + bm2.edges[:] + bm2.faces[:], plane_co=(XCUT, 0, 0), plane_no=(-1, 0, 0), clear_outer=True)
    bm2.to_mesh(me2); bm2.free()
def two_sided(name, front, back_col, back_rough=0.45):
    m = front.copy(); m.name = name; nt_ = m.node_tree; N_ = nt_.nodes; L2 = nt_.links
    outn = N_["Material Output"]; src_ = outn.inputs["Surface"].links[0].from_socket
    bb = N_.new("ShaderNodeBsdfPrincipled"); bb.inputs["Base Color"].default_value = (*back_col, 1); bb.inputs["Roughness"].default_value = back_rough
    nzb = N_.new("ShaderNodeTexNoise"); nzb.inputs["Scale"].default_value = 2500; bpb = N_.new("ShaderNodeBump"); bpb.inputs["Strength"].default_value = 0.5
    L2.new(nzb.outputs[0], bpb.inputs["Height"]); L2.new(bpb.outputs[0], bb.inputs["Normal"])
    g_ = N_.new("ShaderNodeNewGeometry"); mx_ = N_.new("ShaderNodeMixShader")
    L2.new(g_.outputs["Backfacing"], mx_.inputs[0]); L2.new(src_, mx_.inputs[1]); L2.new(bb.outputs[0], mx_.inputs[2]); L2.new(mx_.outputs[0], outn.inputs["Surface"])
    return m
ANAT = os.path.join(AS, "anat")
sk_me = import_glb_mesh(os.path.join(ANAT, "skull.glb"), "XS_RealSkull")

sk_s = fit(sk_me, ny + 0.02, hy_back - 0.007, z_top=top - 0.007)
cut_keep_left(sk_me)
sk = bpy.data.objects.new("XS_RealSkull", sk_me); STUDIO.objects.link(sk); sk.matrix_world = XSM
for p_ in sk_me.polygons: p_.use_smooth = True
sk_me.materials.append(two_sided("M_XS_SkullCut", M_BONE, (0.86, 0.74, 0.55), 0.7))
si_me = import_glb_mesh(os.path.join(ANAT, "sinus.glb"), "XS_RealSinus")
vs_s = [v.co for v in si_me.vertices]; dep = max(v.y for v in vs_s) - min(v.y for v in vs_s)
sk_depth = (hy_back - 0.007) - (ny + 0.02)
si_depth = sk_depth * 0.62
fit(si_me, ny + 0.003, ny + 0.003 + si_depth, z_bot=nz - 0.02)
cut_keep_left(si_me)
si = bpy.data.objects.new("XS_RealSinus", si_me); STUDIO.objects.link(si); si.matrix_world = XSM
for p_ in si_me.polygons: p_.use_smooth = True
si_me.materials.append(two_sided("M_XS_SinusCut", M_MUC, (0.16, 0.02, 0.03), 0.25))
# brain with gyri (cut face shows grey/white matter), tongue with papillae, alar cartilage: displaced solids
organ("XS_Brain", (0.6, 0.73), (0.06, 0.29 * L_, 0.23 * Hh), M_BRAIN, (0.52, 0.38, 0.4), "STUCCI", 0.006, 0.006, gyri=True)
organ("XS_Tongue", (0.36, 0.13), (0.022, 0.17 * L_, 0.08 * Hh), M_TONGUE, (0.62, 0.16, 0.18), "STUCCI", 0.002, 0.0015, rot_x=-12)
print("REALANAT skull", len(sk_me.vertices), "sinus", len(si_me.vertices), "scale", round(sk_s, 5))
# cross-section bricks (same bricks, x6)
for src, nm in ((big, "XS_Brick_Big"), (small, "XS_Brick_Small")):
    o = src.copy(); o.data = src.data; o.name = nm; STUDIO.objects.link(o); o.scale = (XS,) * 3
# record landmarks for 03
sc["XS_P"] = [ny, zcut, L_, Hh, XCUT]
sc["NOSE_TIP_REST"] = list(nose_tip)

# ------------------------------------------------------------------ world: three seasons outside the living-room window
w = bpy.data.worlds.new("World_Seasons"); sc.world = w; w.use_nodes = True; N = w.node_tree.nodes; L = w.node_tree.links
for n_ in list(N): N.remove(n_)
out_ = N.new("ShaderNodeOutputWorld"); prev = None
mixes = []
for i, hd in enumerate(("residential_garden_2k.hdr", "autumn_park_2k.hdr", "snowy_park_01_2k.hdr")):
    e = N.new("ShaderNodeTexEnvironment"); e.image = img(os.path.join(AS, "hdri", hd)); e.name = "Env%d" % i
    bg = N.new("ShaderNodeBackground"); bg.name = "BG%d" % i; L.new(e.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 1.0
    if prev is None: prev = bg.outputs[0]
    else:
        mx = N.new("ShaderNodeMixShader"); mx.name = "SeasonMix%d" % i; mx.inputs[0].default_value = 0.0
        L.new(prev, mx.inputs[1]); L.new(bg.outputs[0], mx.inputs[2]); prev = mx.outputs[0]
L.new(prev, out_.inputs[0])
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 4.0; sun.data.angle = R_(2); sun.rotation_euler = (R_(55), 0, R_(200)); sun.data.color = (1.0, 0.93, 0.82)
# interior practical/fill lights
def area(name, c, loc, e, size, col, rot=(0, 0, 0), shape="RECTANGLE", sy=None):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = e; ld.size = size; ld.color = col; ld.shape = shape
    if sy: ld.size_y = sy
    o = bpy.data.objects.new(name, ld); c.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("LR_WindowFill", ROOM, (WIN[0], 2.30, 1.5), 260, 1.6, (0.85, 0.92, 1.0), rot=(R_(90), 0, 0), sy=1.4)
area("LR_CeilBounce", ROOM, (0.2, 0.0, 2.6), 220, 3.0, (1.0, 0.9, 0.78))
area("LR_FrontFill", ROOM, (0.4, -2.4, 1.6), 120, 2.0, (1.0, 0.92, 0.84), rot=(R_(-90), 0, 0))
area("BR_Moon", BED, (3.6, 2.6, 1.6), 0, 1.0, (0.55, 0.68, 1.0), rot=(R_(110), 0, R_(180)))
area("BR_Ceil", BED, (4.6, 0.6, 2.6), 150, 2.0, (1.0, 0.9, 0.78))
lamp = bpy.data.objects.new("BR_NightLamp", bpy.data.lights.new("BR_NightLamp", "POINT")); BED.objects.link(lamp)
lamp.location = (6.0, 2.05, 0.95); lamp.data.energy = 12; lamp.data.color = (1.0, 0.62, 0.32); lamp.data.shadow_soft_size = 0.08
area("BA_Ceil", BATH, (7.7, 1.1, 2.62), 90, 1.6, (1.0, 0.97, 0.92))
area("BA_ShowerLight", BATH, (8.35, 1.8, 2.6), 45, 0.8, (1.0, 0.97, 0.92))
print("SETS_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
