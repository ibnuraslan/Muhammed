"""Build every set of ElectricianPolice in one scene: town road, substation, utility office, police station.
blender -b --python 02_build_scene.py -- <out_scene.blend>"""
import bpy, bmesh, math, random, os, sys, glob
from mathutils import Vector, Matrix
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "common.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
R_ = math.radians
random.seed(14)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.frame_start, sc.frame_end = 1, FRAME_END
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 3; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 8; sc.cycles.transparent_max_bounces = 8; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
COLS = {}
def coll(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLS[name] = c
    return COLS[name]

# ------------------------------------------------------------------ materials
def pbr(name, col, rough=0.6, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["IOR"].default_value = ior
    if trans: b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = estr
    if alpha < 1: b.inputs["Alpha"].default_value = alpha
    return m

def ph_mat(pid, scale=1.0, tint=None, name=None):
    """append a Poly Haven texture material; drive it with object coords + box projection (no UVs needed)"""
    key = name or (pid if tint is None else "%s_%s" % (pid, "_".join("%02d" % int(c * 99) for c in tint)))
    if key in bpy.data.materials: return bpy.data.materials[key]
    base = bpy.data.materials.get("PH_" + pid)
    if base is None:
        f = glob.glob(f"{ASSETS}/ph/{pid}/*.blend")[0]
        with bpy.data.libraries.load(f) as (src, dst):
            dst.materials = [n for n in src.materials if n == pid] or [src.materials[0]]
        base = dst.materials[0]; base.name = "PH_" + pid
        nt = base.node_tree
        tc = next((n for n in nt.nodes if n.type == "TEX_COORD"), None) or nt.nodes.new("ShaderNodeTexCoord")
        mp = next((n for n in nt.nodes if n.type == "MAPPING"), None)
        if mp is None:
            mp = nt.nodes.new("ShaderNodeMapping")
            for n in nt.nodes:
                if n.type == "TEX_IMAGE": nt.links.new(mp.outputs[0], n.inputs["Vector"])
        for l in list(mp.inputs["Vector"].links): nt.links.remove(l)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        for n in nt.nodes:
            if n.type == "TEX_IMAGE":
                n.projection = "BOX"; n.projection_blend = 0.3
                if not n.inputs["Vector"].links: nt.links.new(mp.outputs[0], n.inputs["Vector"])
            if n.type == "DISPLACEMENT":
                for l in list(n.outputs[0].links): nt.links.remove(l)
        base["s0"] = tuple(mp.inputs["Scale"].default_value)
    m = base.copy(); m.name = key
    nt = m.node_tree; mp = next(n for n in nt.nodes if n.type == "MAPPING")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    if tint is not None:
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        inp = bsdf.inputs["Base Color"]
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0; mix.inputs["B"].default_value = (*tint, 1)
        if inp.links:
            nt.links.new(inp.links[0].from_socket, mix.inputs["A"])
        else:
            mix.inputs["A"].default_value = inp.default_value
        nt.links.new(mix.outputs["Result"], inp)
    return m

ASPH = ph_mat("asphalt_02", 0.25)
DIRT = ph_mat("dry_ground_01", 0.3)
GRAVEL = ph_mat("gravel_concrete_03", 0.35)
CONC = ph_mat("concrete_wall_008", 0.3)
BRICK = ph_mat("brick_wall_10", 0.4)
CORR = ph_mat("corrugated_iron_02", 0.5)
WOOD = ph_mat("wood_floor_deck", 0.5)
PLASTER_TINTS = [(1.0, 0.82, 0.72), (0.98, 0.93, 0.70), (0.72, 0.92, 0.90), (0.95, 0.95, 0.92), (0.95, 0.78, 0.80),
                 (0.80, 0.88, 0.70), (1.0, 0.88, 0.60), (0.78, 0.84, 0.95)]
def plaster(t): return ph_mat("painted_plaster_wall", 0.35, tint=t)
GLASS_DARK = pbr("WindowGlass", (0.03, 0.04, 0.05), rough=0.08, metal=0.3)
FRAME_W = pbr("WindowFrame", (0.85, 0.85, 0.82), rough=0.5)
BLACK = pbr("BlackPlastic", (0.02, 0.02, 0.02), rough=0.45)
STEEL = pbr("Steel", (0.55, 0.56, 0.58), rough=0.35, metal=1.0)
GALV = pbr("Galvanised", (0.62, 0.64, 0.66), rough=0.5, metal=0.9)
PORC = pbr("Porcelain", (0.55, 0.32, 0.22), rough=0.15)
WIRE = pbr("Wire", (0.03, 0.03, 0.03), rough=0.5)

# ------------------------------------------------------------------ mesh helpers
def link(o, c="Set"):
    coll(c).objects.link(o); return o
def box(name, lo, hi, mat, c="Set", bevel=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    lo, hi = Vector(lo), Vector(hi); s = hi - lo
    for v in bm.verts: v.co = Vector((v.co.x * s.x, v.co.y * s.y, v.co.z * s.z))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); o.location = (lo + hi) / 2
    me.materials.append(mat); link(o, c)
    if bevel:
        md = o.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = 2
    return o
def cyl(name, loc, r, h, mat, c="Set", verts=16, r2=None, rot=None):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); o.location = loc
    if rot: o.rotation_euler = rot
    me.materials.append(mat); link(o, c); return o
def sphere(name, loc, r, mat, c="Set", scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); o.location = loc; o.scale = scale
    me.materials.append(mat); link(o, c); return o
def inst(src, name, loc, rotz=0.0, scale=1.0, c="Set"):
    o = src.copy(); o.name = name; o.location = loc; o.rotation_euler = (0, 0, rotz)
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    link(o, c); return o
def wire_curve(name, pts_list, r=0.012, mat=WIRE, c="Set"):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 1
    for pts in pts_list:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new(name, cu); cu.materials.append(mat); link(o, c); return o
def sag(a, b, s=0.6, n=16):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, s * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]

# ------------------------------------------------------------------ assets
LIB = coll("_lib"); LIB.hide_render = True
lib_layer = bpy.context.view_layer.layer_collection.children["_lib"]; lib_layer.exclude = False
def ph_model(pid, names=None):
    f = glob.glob(f"{ASSETS}/ph/{pid}/*.blend")[0]
    with bpy.data.libraries.load(f) as (src, dst):
        dst.objects = [n for n in src.objects if (names is None or n in names)]
    out = {}
    for o in dst.objects:
        if o is None or o.type not in ("MESH", "EMPTY", "ARMATURE"): continue
        LIB.objects.link(o); out[o.name] = o
    return out
def joined(objs, name):
    """bake a set of objects into one mesh at their world transforms, origin at bbox bottom centre"""
    objs = [o for o in objs if o.type == "MESH"]
    bm = bmesh.new(); mats = []
    for o in objs:
        me = o.data.copy(); me.transform(o.matrix_world)
        remap = []
        for m in me.materials:
            if m not in mats: mats.append(m)
            remap.append(mats.index(m))
        for p in me.polygons: p.material_index = remap[p.material_index] if remap else 0
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    pts = [v.co for v in me.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    me.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    o = bpy.data.objects.new(name, me); LIB.objects.link(o)
    o["dims"] = tuple(mx - mn)
    return o
def glb(name, scale=1.0, rot=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f"{ASSETS}/glb/{name}.glb")
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        LIB.objects.link(o)
    j = joined(new, "SRC_" + name)
    if rot: j.data.transform(rot)
    j.data.transform(Matrix.Scale(scale, 4))
    pts = [v.co for v in j.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    j.data.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    j["dims"] = tuple(mx - mn)
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    print("GLB", name, tuple(round(x, 2) for x in j["dims"]))
    return j
def ph_joined(pid, names=None, nm=None):
    d = ph_model(pid, names); bpy.context.view_layer.update()
    j = joined(list(d.values()), "SRC_" + (nm or pid))
    print("PHM", pid, tuple(round(x, 2) for x in j["dims"]))
    return j, d

MOTO = glb("motorcycle", 0.8)
TRANSF = glb("transformer", 1.7)
SWG = glb("switchgear", 1.0)
PYLON = glb("pylon", 1.55)
STALL = glb("stall", 0.0105)
PHONE = glb("phone", 1.0)
OCHAIR = glb("officechair", 1.0)
LAPTOP, _lap = ph_joined("classic_laptop")
DESK_M, _ = ph_joined("metal_office_desk")
CLOCK_PARTS = ph_model("wall_clock")
FENCE, _ = ph_joined("modular_chainlink_fence", ["modular_chainlink_fence_double"], "fence")
FPOST, _ = ph_joined("modular_chainlink_fence", ["modular_chainlink_fence_post"], "fencepost")
GATE_M, _ = ph_joined("modular_chainlink_fence", ["modular_chainlink_fence_door_gate"], "gate")
MCHAIR, _ = ph_joined("plastic_monobloc_chair_01")
LAMP, _ = ph_joined("street_lamp_01")
NOTEP, _ = ph_joined("office_notepads", ["office_notepads_a4_stack", "office_notepads_yellow_pad"], "notepads")
A4, _ = ph_joined("office_notepads", ["office_notepads_a4_a"], "a4")
CLIP, _ = ph_joined("clipboard")
SHUT, _ = ph_joined("rollershutter_door", ["rollershutter_door"], "shutter")
SHUTW, _ = ph_joined("rollershutter_window_01", ["rollershutter_window_01"], "shutterwin")
CRATE, _ = ph_joined("plastic_crate_01")
BOXC, _ = ph_joined("cardboard_box_01")
FAN_D = ph_model("ceiling_fan")
AC, _ = ph_joined("exterior_aircon_unit", ["exterior_aircon_unit"], "aircon")
WCRATE, _ = ph_joined("wooden_crate_01")
BAN, _ = ph_joined("bananas", ["bananas_bunch"], "bananas")
BASKET, _ = ph_joined("wicker_basket_01")
DRAWER, _ = ph_joined("drawer_cabinet")
PLANT, _ = ph_joined("potted_plant_01")
TRASH, _ = ph_joined("metal_trash_can", ["metal_trash_can", "metal_trash_can_lid"], "trash")
LIME, _ = ph_joined("food_lime_01")
PBOX, _ = ph_joined("power_box_01", ["power_box_01_box", "power_box_01_door"], "powerbox")
UBOX, _ = ph_joined("utility_box_02")

def face_fit(src, name, centre, facing, w, h, c="Set", depth_scale=1.0):
    """place a planar asset (shutter) so its thin axis is along the facing direction and it spans w x h"""
    d = Vector(src["dims"]); thin = 0 if d.x < d.y else 1
    sw = (d.y if thin == 0 else d.x); o = src.copy(); o.name = name; link(o, c)
    base_rot = (R_(90) if thin == 0 else 0.0)
    ang = math.atan2(facing.y, facing.x) - math.atan2(-1, 0)   # asset front assumed -Y
    o.rotation_euler = (0, 0, ang + base_rot)
    o.scale = (w / sw, depth_scale, h / d.z) if thin == 1 else (depth_scale, w / sw, h / d.z)
    o.location = centre; return o

# ------------------------------------------------------------------ ground: road, shoulders, curbs, markings
box("Road", (-ROAD_W / 2, -40, -0.05), (ROAD_W / 2, 140, 0.0), ASPH)
for s in (-1, 1):
    box("Shoulder_%d" % s, (min(s * 4, s * 7.2), -40, -0.05), (max(s * 4, s * 7.2), 140, 0.03), DIRT)
    box("Curb_%d" % s, (min(s * 3.95, s * 4.15), -40, -0.05), (max(s * 3.95, s * 4.15), 140, 0.08), CONC)
box("Backlots", (-120, -60, -0.12), (120, 200, -0.04), DIRT)
PAINT = pbr("RoadPaint", (0.8, 0.78, 0.7), rough=0.7)
for i in range(-10, 70):
    box("Dash_%d" % i, (-0.06, i * 2.0, 0.0), (0.06, i * 2.0 + 1.1, 0.004), PAINT, c="Road")
# random potholes / patches / litter so the road isn't clean
PATCH = ph_mat("asphalt_02", 0.4, tint=(0.6, 0.6, 0.6))
for i in range(0):
    x = random.uniform(-3.6, 3.6); y = random.uniform(-30, 130); r = random.uniform(0.3, 1.1)
    cyl("Patch_%d" % i, (x, y, 0.001), r, 0.004, PATCH, c="Road", verts=10)

# ------------------------------------------------------------------ town buildings along the road
WIN_T = {}
def window(name, centre, facing, w=1.1, h=1.3, c="Town", lit_mat=None):
    """frame + glass + sill + iron grill; facing = outward normal (unit X)"""
    s = 1 if facing.x > 0 else -1
    x = centre.x
    box(name + "_frame", (min(x, x + s * 0.06), centre.y - w / 2 - 0.08, centre.z - h / 2 - 0.08),
        (max(x, x + s * 0.06), centre.y + w / 2 + 0.08, centre.z + h / 2 + 0.08), FRAME_W, c=c)
    g = box(name + "_glass", (min(x + s * 0.061, x + s * 0.07), centre.y - w / 2, centre.z - h / 2),
            (max(x + s * 0.061, x + s * 0.07), centre.y + w / 2, centre.z + h / 2), lit_mat or GLASS_DARK, c=c)
    box(name + "_sill", (min(x, x + s * 0.2), centre.y - w / 2 - 0.12, centre.z - h / 2 - 0.16),
        (max(x, x + s * 0.2), centre.y + w / 2 + 0.12, centre.z - h / 2 - 0.08), CONC, c=c)
    for k in range(5):
        yy = centre.y - w / 2 + w * (k + 0.5) / 5
        cyl(name + "_bar%d" % k, (x + s * 0.12, yy, centre.z), 0.008, h, BLACK, c=c, verts=6)
    return g
SIGN_COLS = [(0.8, 0.12, 0.1), (0.1, 0.3, 0.7), (0.95, 0.7, 0.1), (0.1, 0.55, 0.3), (0.9, 0.9, 0.85), (0.6, 0.1, 0.5)]
AWN_COLS = [(0.15, 0.35, 0.75), (0.85, 0.2, 0.15), (0.2, 0.6, 0.3), (0.9, 0.65, 0.1)]
def building(name, s, y0, y1, floors, depth=10.0, tint=None, shop="shutter", c="Town"):
    xf = s * BUILD_X; xb = s * (BUILD_X + depth); h = floors * 3.2 + 0.4
    m = plaster(tint or random.choice(PLASTER_TINTS))
    box(name, (min(xf, xb), y0, 0), (max(xf, xb), y1, h), m, c=c)
    box(name + "_parapet", (min(xf, xf + s * 0.25), y0, h), (max(xf, xf + s * 0.25), y1, h + 0.9), m, c=c)
    for k in range(1, floors):
        box(name + "_band%d" % k, (min(xf, xf - s * 0.12), y0, k * 3.2 - 0.1), (max(xf, xf - s * 0.12), y1, k * 3.2 + 0.12), m, c=c)
    face = Vector((-s, 0, 0)); w = y1 - y0
    # ground floor shop front
    if shop == "shutter":
        face_fit(SHUT, name + "_shutter", Vector((xf - s * 0.03, (y0 + y1) / 2, 0.0)), face, min(3.6, w - 1.0), 2.8, c=c, depth_scale=1.0)
    else:
        box(name + "_shopdark", (min(xf, xf + s * 0.8), y0 + 0.6, 0.0), (max(xf, xf + s * 0.8), y1 - 0.6, 2.8), pbr("ShopInterior", (0.08, 0.06, 0.05), 0.9), c=c)
        for k in range(int((w - 1.6) // 0.7)):
            yy = y0 + 0.9 + k * 0.7
            inst(CRATE if k % 2 else WCRATE, name + "_goods%d" % k, (xf - s * 0.35, yy + 0.3, 0.0), rotz=random.uniform(-0.2, 0.2), scale=0.9, c=c)
            inst(BAN if k % 3 == 0 else LIME, name + "_fruit%d" % k, (xf - s * 0.35, yy + 0.3, 0.35), scale=(1.0 if k % 3 == 0 else 4.0), c=c)
    # sign board (blank colour, no text) + awning
    sc_ = random.choice(SIGN_COLS)
    box(name + "_sign", (min(xf, xf - s * 0.1), y0 + 0.4, 2.95), (max(xf, xf - s * 0.1), y1 - 0.4, 3.15 + 0.5), pbr("Sign_%d" % SIGN_COLS.index(sc_), sc_, 0.4), c=c)
    aw = box(name + "_awning", (min(xf - s * 0.1, xf - s * 1.6), y0 + 0.3, 2.75), (max(xf - s * 0.1, xf - s * 1.6), y1 - 0.3, 2.8),
             pbr("Awning_%d" % (hash(name) % 4), random.choice(AWN_COLS), 0.8) if random.random() < 0.6 else CORR, c=c)
    aw.rotation_euler = (0, s * R_(-12), 0)
    # upper floor windows, balcony, AC units
    for k in range(1, floors):
        n = max(1, int((w - 1.0) // 2.4))
        for i in range(n):
            yy = y0 + (i + 0.5) * w / n
            window(f"{name}_w{k}_{i}", Vector((xf - s * 0.0, yy, k * 3.2 + 1.5)), face, c=c)
            if random.random() < 0.3:
                inst(AC, f"{name}_ac{k}_{i}", (xf - s * 0.35, yy + 0.95, k * 3.2 + 0.6), rotz=(R_(90) if s < 0 else R_(-90)), c=c)
        if random.random() < 0.5:
            box(f"{name}_balc{k}", (min(xf, xf - s * 0.9), y0 + 0.5, k * 3.2), (max(xf, xf - s * 0.9), y1 - 0.5, k * 3.2 + 0.15), CONC, c=c)
            box(f"{name}_rail{k}", (min(xf - s * 0.85, xf - s * 0.9), y0 + 0.5, k * 3.2 + 0.15), (max(xf - s * 0.85, xf - s * 0.9), y1 - 0.5, k * 3.2 + 1.0), BLACK, c=c)
            # washing on the line
            for j in range(4):
                cl = box(f"{name}_cloth{k}_{j}", (min(xf - s * 0.9, xf - s * 0.92), y0 + 0.9 + j * 0.6, k * 3.2 + 0.4), (max(xf - s * 0.9, xf - s * 0.92), y0 + 1.35 + j * 0.6, k * 3.2 + 0.98),
                         pbr("Cloth_%d" % j, [(0.8, 0.2, 0.2), (0.9, 0.85, 0.3), (0.2, 0.4, 0.8), (0.95, 0.95, 0.95)][j], 0.9), c=c)
    # roof: water tank + clutter
    cyl(name + "_tank", (xf + s * depth * 0.6, (y0 + y1) / 2, h + 0.6), 0.6, 1.2, BLACK, c=c)
    return h

def street_side(s, y_ranges, c="Town"):
    for (ya, yb) in y_ranges:
        y = ya
        while y < yb - 3:
            w = random.uniform(5.5, 8.5); w = min(w, yb - y)
            building("B_%s_%d" % ("E" if s > 0 else "W", int(y)), s, y + 0.1, y + w - 0.1, random.choice([2, 2, 3, 3, 4]),
                     depth=random.uniform(8, 12), shop=random.choice(["shutter", "open", "open"]), c=c)
            y += w
street_side(-1, [(-40, 49.5), (64.5, 140)])
street_side(1, [(-40, 9.5), (46.5, 140)])

# street furniture: stalls, lamps, poles, wires, parked bikes, trees, rickshaws (procedural)
for i, (x, y, r) in enumerate([(-5.6, 6.0, R_(90)), (5.6, 2.0, R_(-90)), (-5.6, 30.0, R_(90)), (5.7, 52.0, R_(-90)), (-5.6, 40.0, R_(90)), (5.7, 64.0, R_(-90))]):
    inst(STALL, "Stall_%d" % i, (x, y, 0.03), rotz=r, c="Town")
    for k in range(3):
        inst(BAN, f"Stall_{i}_ban{k}", (x + (0.3 if x < 0 else -0.3), y - 0.7 + k * 0.6, 0.95), rotz=random.uniform(0, 6), c="Town")
        inst(BASKET, f"Stall_{i}_bask{k}", (x + (0.9 if x < 0 else -0.9), y - 0.8 + k * 0.8, 0.03), rotz=random.uniform(0, 6), c="Town")
POLE_M = ph_mat("concrete_wall_008", 0.8, tint=(0.75, 0.75, 0.72), name="PoleConc")
pole_tops = {-1: [], 1: []}
for s in (-1, 1):
    for i, y in enumerate(range(-30, 140, 16)):
        x = s * 4.6
        if s > 0 and 10 < y < 46: x = s * 7.8
        cyl("Pole_%d_%d" % (s, i), (x, y, 4.5), 0.13, 9.0, POLE_M, c="Town", verts=10, r2=0.09)
        box("Arm_%d_%d" % (s, i), (x - 0.9, y - 0.06, 8.4), (x + 0.9, y + 0.06, 8.52), STEEL, c="Town")
        pole_tops[s].append([Vector((x + dx, y, 8.55)) for dx in (-0.8, -0.3, 0.3, 0.8)])
        if i % 2 == 0:
            inst(LAMP, "Lamp_%d_%d" % (s, i), (x - s * 0.3, y + 1.0, 0.0), rotz=(R_(-90) if s < 0 else R_(90)), c="Town")
for s in (-1, 1):
    tops = pole_tops[s]; spl = []
    for a, b in zip(tops, tops[1:]):
        for k in range(4): spl.append(sag(a[k], b[k], 0.35 + 0.08 * k))
    # messy service drops to the buildings
    for i, t in enumerate(tops):
        for k in range(3):
            spl.append(sag(t[k], Vector((s * 7.0, t[k].y + random.uniform(-3, 3), random.uniform(5.5, 7.5))), 0.25, 8))
    wire_curve("Wires_%d" % s, spl, 0.012)
# cross-street banner wires with bunting flags
FLAGS = []
for j, y in enumerate((14.0, 36.0, 76.0)):
    a, b = Vector((-7.0, y, 7.0)), Vector((7.0, y + 1, 7.0)); pts = sag(a, b, 0.8, 20)
    wire_curve("Bunting_%d" % j, [pts], 0.006)
    for k in range(1, 20, 1):
        p = pts[k]; f = bpy.data.meshes.new("flag"); bm = bmesh.new()
        v1 = bm.verts.new((-0.12, 0, 0)); v2 = bm.verts.new((0.12, 0, 0)); v3 = bm.verts.new((0, 0, -0.3)); bm.faces.new((v1, v2, v3)); bm.to_mesh(f); bm.free()
        fo = bpy.data.objects.new("Flag_%d_%d" % (j, k), f); fo.location = p; fo.rotation_euler = (0, 0, math.atan2(b.y - a.y, b.x - a.x))
        f.materials.append(pbr("Flag_%d" % (k % 4), [(0.95, 0.5, 0.05), (0.98, 0.98, 0.95), (0.1, 0.55, 0.2), (0.85, 0.15, 0.2)][k % 4], 0.8))
        link(fo, "Town"); FLAGS.append(fo)
# parked bikes and clutter
for i, (x, y, r) in enumerate([(-5.0, 12.0, R_(20)), (5.0, 16.0, R_(160)), (-5.2, 45.0, R_(-15)), (5.1, 70.0, R_(200)), (-5.0, 68.0, R_(10))]):
    inst(MOTO, "ParkedBike_%d" % i, (x, y, 0.03), rotz=r, c="Town")
for i in range(14):
    s = random.choice((-1, 1)); y = random.uniform(-20, 110)
    if s > 0 and 9 < y < 47: continue
    inst(random.choice([CRATE, WCRATE, BOXC, TRASH, PLANT]), "Clutter_%d" % i, (s * random.uniform(6.2, 6.8), y, 0.03), rotz=random.uniform(0, 6), c="Town")
LEAF = pbr("Leaves", (0.12, 0.25, 0.06), rough=0.8)
BARK = pbr("Bark", (0.18, 0.12, 0.08), rough=0.9)
for i, (x, y) in enumerate([(-6.3, -6.0), (6.4, 26.0 + 22), (-6.4, 80.0), (6.3, 96.0), (-6.3, 18.0)]):
    cyl("TreeTrunk_%d" % i, (x, y, 2.0), 0.22, 4.0, BARK, c="Town", r2=0.14)
    for k in range(5):
        o = sphere("TreeLeaf_%d_%d" % (i, k), (x + random.uniform(-1.2, 1.2), y + random.uniform(-1.2, 1.2), 4.6 + random.uniform(0, 1.4)), random.uniform(1.0, 1.6), LEAF, c="Town")
        d = o.modifiers.new("d", "DISPLACE"); t = bpy.data.textures.get("leafnoise") or bpy.data.textures.new("leafnoise", "CLOUDS"); t.noise_scale = 0.35; d.texture = t; d.strength = 0.5

RICK_BODY = [pbr("RickGreen", (0.12, 0.45, 0.12), 0.35), pbr("RickYellow", (0.95, 0.75, 0.05), 0.35)]
def rickshaw(name, c="Traffic"):
    root = bpy.data.objects.new(name, None); link(root, c)
    parts = []
    b = box(name + "_body", (-0.62, -1.3, 0.3), (0.62, 0.9, 1.05), RICK_BODY[0], c=c, bevel=0.12)
    nose = box(name + "_nose", (-0.35, -1.75, 0.3), (0.35, -1.25, 1.2), RICK_BODY[0], c=c, bevel=0.1)
    canopy = box(name + "_canopy", (-0.68, -1.45, 1.6), (0.68, 1.0, 1.75), RICK_BODY[1], c=c, bevel=0.08)
    pillars = [box(name + "_pil%d" % i, (x - 0.03, y - 0.03, 1.05), (x + 0.03, y + 0.03, 1.62), BLACK, c=c) for i, (x, y) in enumerate([(-0.6, -1.25), (0.6, -1.25), (-0.6, 0.85), (0.6, 0.85)])]
    ws = box(name + "_screen", (-0.35, -1.55, 1.2), (0.35, -1.5, 1.6), GLASS_DARK, c=c)
    seat = box(name + "_seat", (-0.55, 0.2, 0.9), (0.55, 0.8, 1.05), BLACK, c=c)
    lamp = sphere(name + "_lamp", (0, -1.77, 0.95), 0.08, pbr("Headlamp", (1, 1, 0.9), 0.1, emit=(1, 0.95, 0.8), estr=3), c=c)
    wheels = []
    for i, (x, y) in enumerate([(0.0, -1.5), (-0.58, 0.55), (0.58, 0.55)]):
        w = cyl(name + "_wheel%d" % i, (x, y, 0.25), 0.25, 0.14, BLACK, c=c, verts=14, rot=(0, R_(90), 0)); wheels.append(w)
    for o in [b, nose, canopy, ws, seat, lamp] + pillars + wheels:
        o.parent = root
    root["wheels"] = [w.name for w in wheels]
    return root
for i in range(5):
    r = rickshaw("Rick_%d" % i)
    r.location = (random.choice((-1.9, 1.9)), -20 + i * 25, 0.0)
    for o in r.children:
        if o.name.endswith("_body") or o.name.endswith("_nose"):
            o.data.materials[0] = RICK_BODY[0] if i % 2 == 0 else pbr("RickBlack", (0.05, 0.05, 0.05), 0.35)

# ------------------------------------------------------------------ substation
S_ = SUB
box("Sub_Ground", (S_["x0"], S_["y0"], -0.05), (S_["x1"], S_["y1"], 0.05), GRAVEL, c="Substation")
fd = Vector(FENCE["dims"]); flen = max(fd.x, fd.y); fx_is_len = fd.x > fd.y
def fence_line(a, b, gap=None):
    a, b = Vector(a), Vector(b); L = (b - a).length; d = (b - a).normalized(); n = int(L // flen)
    ang = math.atan2(d.y, d.x) - (0 if fx_is_len else R_(90))
    for i in range(n):
        p = a + d * (flen * (i + 0.5))
        if gap and (p - Vector(gap)).length < flen * 0.9:
            g = inst(GATE_M, "Gate", p, rotz=ang, c="Substation"); continue
        inst(FENCE, "Fence_%d_%d" % (int(a.x), int(a.y) + i * 100), p, rotz=ang, c="Substation")
fence_line((8.0, 10.0, 0.05), (8.0, 46.0, 0.05), gap=GATE)
fence_line((8.0, 10.0, 0.05), (34.0, 10.0, 0.05)); fence_line((34.0, 10.0, 0.05), (34.0, 46.0, 0.05)); fence_line((8.0, 46.0, 0.05), (17.0, 46.0, 0.05))
# warning plate on the gate: red triangle + lightning bolt, no text
tri = bpy.data.meshes.new("warn"); bm = bmesh.new()
vs = [bm.verts.new(p) for p in ((0, -0.22, 0), (0, 0.22, 0), (0, 0, 0.38))]; bm.faces.new(vs); bm.to_mesh(tri); bm.free()
wo = bpy.data.objects.new("WarnSign", tri); wo.location = (7.93, GATE.y + 0.8, 1.1); tri.materials.append(pbr("WarnYellow", (0.95, 0.75, 0.05), 0.4)); link(wo, "Substation")
bolt = bpy.data.meshes.new("bolt"); bm = bmesh.new()
vs = [bm.verts.new(p) for p in ((0, 0.03, 0.31), (0, -0.07, 0.15), (0, 0.0, 0.16), (0, -0.04, 0.04), (0, 0.07, 0.2), (0, 0.0, 0.19))]; bm.faces.new(vs); bm.to_mesh(bolt); bm.free()
bo = bpy.data.objects.new("WarnBolt", bolt); bo.location = (7.92, GATE.y + 0.8, 1.1); bolt.materials.append(BLACK); link(bo, "Substation")
TRANS_POS = [Vector((13.5, 22.0, 0.05)), Vector((19.0, 22.0, 0.05)), Vector((24.5, 22.0, 0.05)), Vector((13.5, 30.0, 0.05)), Vector((19.0, 30.0, 0.05))]
for i, p in enumerate(TRANS_POS):
    box("TransPad_%d" % i, (p.x - 1.8, p.y - 2.0, 0.0), (p.x + 1.8, p.y + 2.0, 0.25), CONC, c="Substation")
    inst(TRANSF, "Transformer_%d" % i, p + Vector((0, 0, 0.25)), rotz=R_(90), c="Substation")
    # bushings + busbar frame
    for k in range(3):
        cyl(f"Bushing_{i}_{k}", (p.x - 0.8 + k * 0.8, p.y, 3.4), 0.09, 0.9, PORC, c="Substation", verts=12)
        cyl(f"BusPost_{i}_{k}", (p.x - 0.8 + k * 0.8, p.y + 2.6, 2.5), 0.07, 5.0, GALV, c="Substation", verts=8)
    box("BusBeam_%d" % i, (p.x - 1.2, p.y + 2.55, 4.95), (p.x + 1.2, p.y + 2.65, 5.05), GALV, c="Substation")
    wire_curve("Jumpers_%d" % i, [sag((p.x - 0.8 + k * 0.8, p.y, 3.85), (p.x - 0.8 + k * 0.8, p.y + 2.6, 5.0), 0.3, 8) for k in range(3)], 0.02, GALV, c="Substation")
INDICATORS = []
for i, p in enumerate(TRANS_POS):
    o = sphere("Indicator_%d" % i, (p.x + 0.95, p.y - 1.05, 1.5), 0.05, pbr("IndOn_%d" % i, (0.2, 1, 0.2), 0.2, emit=(0.2, 1.0, 0.25), estr=8.0), c="Substation")
    INDICATORS.append(o)
inst(PBOX, "Sub_PowerBox", (9.0, 27.5, 0.05), rotz=R_(-90), c="Substation")
inst(UBOX, "Sub_UtilBox", (9.0, 19.0, 0.05), rotz=R_(-90), c="Substation")
# pylons: two inside the yard, lines spreading out over the town
PYL = [(Vector((12.0, 36.0, 0.0)), R_(0)), (Vector((29.0, 34.0, 0.0)), R_(0)),
       (Vector((-26.0, 40.0, 0.0)), R_(5)), (Vector((-62.0, 46.0, 0.0)), R_(8)),
       (Vector((14.0, 82.0, 0.0)), R_(90)), (Vector((16.0, 126.0, 0.0)), R_(90)),
       (Vector((60.0, 30.0, 0.0)), R_(-5)), (Vector((-30.0, 84.0, 0.0)), R_(40))]
pd = Vector(PYLON["dims"])
def pylon_tips(p, rz):
    R = Matrix.Rotation(rz, 3, "Z")
    return [p + R @ Vector((dx, 0, pd.z - 2.2)) for dx in (-pd.x / 2 + 0.5, 0.0, pd.x / 2 - 0.5)]
PYLON.data.materials.clear(); PYLON.data.materials.append(GALV)
for i, (p, rz) in enumerate(PYL):
    inst(PYLON, "Pylon_%d" % i, p, rotz=rz, c="Grid")
LINES = []
for a, b in ((0, 2), (2, 3), (0, 4), (4, 5), (1, 6), (0, 1), (1, 7)):
    ta, tb = pylon_tips(*PYL[a]), pylon_tips(*PYL[b])
    pts = [sag(ta[k], tb[k], 1.6, 24) for k in range(3)]
    LINES.append(pts); wire_curve("Line_%d_%d" % (a, b), pts, 0.025, pbr("Conductor", (0.25, 0.25, 0.27), 0.4, metal=0.8), c="Grid")
# low-voltage line from the substation over the road to the police station (the one he cuts)
st_feed = [Vector((12.0, 36.0, 9.0)), Vector((4.6, 48.0, 8.55)), Vector((-7.2, 57.0, 6.9))]
wire_curve("FeedLine", [sag(st_feed[0], st_feed[1], 0.6), sag(st_feed[1], st_feed[2], 0.5)], 0.015, c="Grid")

# ------------------------------------------------------------------ utility office (walls as slabs, window opening in the south wall)
O = OFFICE; t = 0.2
INT_W = ph_mat("painted_plaster_wall", 0.5, tint=(0.75, 0.9, 0.82), name="OfficeWall")
EXT_W = plaster((0.95, 0.93, 0.85))
FLOOR_T = ph_mat("gravel_concrete_03", 0.6, tint=(0.8, 0.75, 0.7), name="Terrazzo")
def walled_room(name, x0, x1, y0, y1, h, ext, intm, holes, c):
    """four walls with rectangular holes. holes: list of (wall, centre_along, z0, z1, width) wall in 'S','N','W','E'"""
    def wall(wn, a0, a1, fixed, axis):
        hs = sorted([hh for hh in holes if hh[0] == wn], key=lambda hh: hh[1])
        segs = []; cur = a0
        for _, ca, z0, z1, w in hs:
            segs.append((cur, ca - w / 2, 0, h)); segs.append((ca - w / 2, ca + w / 2, 0, z0)); segs.append((ca - w / 2, ca + w / 2, z1, h)); cur = ca + w / 2
        segs.append((cur, a1, 0, h))
        for i, (b0, b1, z0, z1) in enumerate(segs):
            if b1 - b0 < 1e-3 or z1 - z0 < 1e-3: continue
            if axis == "x":
                lo, hi = (b0, fixed - t / 2, z0), (b1, fixed + t / 2, z1)
            else:
                lo, hi = (fixed - t / 2, b0, z0), (fixed + t / 2, b1, z1)
            o = box(f"{name}_{wn}{i}", lo, hi, ext, c=c); o.data.materials.append(intm)
            # interior faces get the interior material
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            for p in o.data.polygons:
                n = p.normal; ctr = o.location + p.center
                inward = (Vector((cx, cy, 0)) - Vector((ctr.x, ctr.y, 0))).normalized()
                if Vector((n.x, n.y, 0)).dot(inward) > 0.7: p.material_index = 1
    wall("S", x0, x1, y0, "x"); wall("N", x0, x1, y1, "x"); wall("W", y0 + t / 2, y1 - t / 2, x0, "y"); wall("E", y0 + t / 2, y1 - t / 2, x1, "y")
    box(name + "_floor", (x0, y0, -0.02), (x1, y1, 0.02), FLOOR_T, c=c)
    box(name + "_ceiling", (x0, y0, h), (x1, y1, h + 0.25), intm, c=c)
    box(name + "_roof", (x0 - 0.3, y0 - 0.3, h + 0.25), (x1 + 0.3, y1 + 0.3, h + 0.4), CONC, c=c)
walled_room("Office", O["x0"], O["x1"], O["y0"], O["y1"], O["h"], EXT_W, INT_W,
            [("S", OFFICE_WIN.x, OFFICE_WIN.z - 0.7, OFFICE_WIN.z + 0.7, 1.6), ("W", 40.5, 0.0, 2.2, 1.0)], "Office")
box("OfficeWin_sill", (OFFICE_WIN.x - 0.9, O["y0"] - 0.25, OFFICE_WIN.z - 0.78), (OFFICE_WIN.x + 0.9, O["y0"] + 0.15, OFFICE_WIN.z - 0.7), CONC, c="Office")
OFFICE_LIGHT_MAT = pbr("TubeLight", (1, 1, 1), 0.3, emit=(1.0, 0.97, 0.9), estr=6.0)
box("Office_tube", (21.0, 41.8, O["h"] - 0.06), (22.2, 41.9, O["h"] - 0.02), OFFICE_LIGHT_MAT, c="Office")
L = bpy.data.lights.new("OfficeFill", "AREA"); L.energy = 250; L.size = 1.2; L.color = (1.0, 0.95, 0.88)
lo = bpy.data.objects.new("OfficeFill", L); lo.location = (21.5, 42.0, O["h"] - 0.1); link(lo, "Office")
desk = inst(DESK_M, "Office_Desk", DESK, rotz=R_(0), c="Office")
dd = Vector(DESK_M["dims"]); DESK_TOP = DESK.z + dd.z
lap = inst(LAPTOP, "Office_Laptop", (DESK.x, DESK.y - 0.15, DESK_TOP), rotz=R_(0), c="Office")
inst(OCHAIR, "Office_Chair", CHAIR, rotz=R_(180), c="Office")
inst(NOTEP, "Office_Notes", (DESK.x - 0.55, DESK.y - 0.05, DESK_TOP), rotz=R_(15), c="Office")
inst(CLIP, "Office_Clip", (DESK.x + 0.55, DESK.y + 0.1, DESK_TOP), rotz=R_(-20), c="Office")
TEA = pbr("TeaGlass", (0.9, 0.95, 0.95), 0.05, trans=1.0, ior=1.5)
cyl("Office_TeaGlass", (DESK.x + 0.4, DESK.y - 0.2, DESK_TOP + 0.055), 0.03, 0.11, TEA, c="Office", r2=0.035)
cyl("Office_Tea", (DESK.x + 0.4, DESK.y - 0.2, DESK_TOP + 0.04), 0.028, 0.075, pbr("Chai", (0.55, 0.33, 0.15), 0.2), c="Office", r2=0.032)
inst(DRAWER, "Office_Drawers", (18.0, 45.3, 0.0), rotz=R_(180), c="Office")
for i in range(6):
    box("Office_Binder_%d" % i, (17.2, 41.0 + i * 0.09, 1.4), (17.5, 41.07 + i * 0.09, 1.72), pbr("Binder_%d" % (i % 3), [(0.6, 0.1, 0.1), (0.1, 0.2, 0.5), (0.1, 0.4, 0.2)][i % 3], 0.5), c="Office")
box("Office_Shelf", (17.1, 40.8, 1.38), (17.6, 41.8, 1.4), WOOD, c="Office")
inst(PLANT, "Office_Plant", (25.2, 38.6, 0.0), c="Office")
inst(MCHAIR, "Office_Visitor", (19.4, 42.4, 0.0), rotz=R_(60), c="Office")
swg = inst(SWG, "Switchgear", (O["x1"] - t / 2 - 0.02, CABINET.y, 0.0), rotz=R_(-90), c="Office")
for k, yy in enumerate((CABINET.y - 1.1, CABINET.y + 1.1)):
    inst(SWG, "Switchgear_%d" % k, (O["x1"] - t / 2 - 0.02, yy, 0.0), rotz=R_(-90), c="Office")
for k, nm in enumerate(("ceiling_fan", "ceiling_fan_blades")):
    o = FAN_D[nm].copy(); o.name = "OfficeFan_" + nm; o.location = (20.0, 43.5, O["h"] - 0.6); link(o, "Office")

# ------------------------------------------------------------------ police station
ST = STATION
ST_EXT = plaster((0.93, 0.85, 0.62))
ST_INT = ph_mat("painted_plaster_wall", 0.5, tint=(0.9, 0.88, 0.8), name="StationWall")
holes = [("E", y, 0.95, 2.25, 1.2) for y in ST_WIN_Y] + [("E", ST_DOOR.y, 0.0, 2.4, 1.5)]
walled_room("Station", ST["x0"], ST["x1"], ST["y0"], ST["y1"], 3.4, ST_EXT, ST_INT, holes, "Station")
box("Station_upper", (ST["x0"], ST["y0"], 3.65), (ST["x1"] + 0.1, ST["y1"], ST["h"]), ST_EXT, c="Station")
box("Station_parapet", (ST["x1"] - 0.15, ST["y0"], ST["h"]), (ST["x1"] + 0.1, ST["y1"], ST["h"] + 0.8), ST_EXT, c="Station")
box("Station_band", (ST["x1"], ST["y0"], 3.4), (ST["x1"] + 0.25, ST["y1"], 3.7), plaster((0.55, 0.2, 0.15)), c="Station")
WIN_LIT = []
for i, y in enumerate(ST_WIN_Y):
    m = pbr("StWinLit_%d" % i, (0.2, 0.18, 0.12), 0.15, emit=(1.0, 0.85, 0.55), estr=5.0)
    window("StWinUp_%d" % i, Vector((ST["x1"] + 0.1, y, 5.2)), Vector((1, 0, 0)), w=1.2, h=1.3, c="Station", lit_mat=m); WIN_LIT.append(m.name)
    # ground floor: frame + grill only, open (no glass) so the camera can fly in through window 1
    xg = ST["x1"] + 0.1
    box(f"StWinG_{i}_frameT", (xg - 0.1, y - 0.68, 2.25), (xg + 0.06, y + 0.68, 2.33), FRAME_W, c="Station")
    box(f"StWinG_{i}_sill", (xg - 0.1, y - 0.72, 0.87), (xg + 0.2, y + 0.72, 0.95), CONC, c="Station")
    if i != 1:
        for k in range(5):
            cyl(f"StWinG_{i}_bar{k}", (xg, y - 0.5 + k * 0.25, 1.6), 0.01, 1.3, BLACK, c="Station", verts=6)
        m2 = pbr("StWinGLit_%d" % i, (0.2, 0.18, 0.12), 0.1, emit=(1.0, 0.85, 0.55), estr=0.0, alpha=1.0)
box("Station_steps1", (ST["x1"], ST_DOOR.y - 1.4, 0.0), (ST["x1"] + 1.4, ST_DOOR.y + 1.4, 0.15), CONC, c="Station")
box("Station_steps2", (ST["x1"], ST_DOOR.y - 1.2, 0.15), (ST["x1"] + 0.8, ST_DOOR.y + 1.2, 0.3), CONC, c="Station")
box("Station_canopy", (ST["x1"], ST_DOOR.y - 1.6, 2.7), (ST["x1"] + 1.8, ST_DOOR.y + 1.6, 2.85), CONC, c="Station")
SIGN_BLUE = pbr("StationSign", (0.05, 0.15, 0.45), 0.4)
box("Station_sign", (ST["x1"] + 0.25, ST_DOOR.y - 2.6, 3.9), (ST["x1"] + 0.32, ST_DOOR.y + 2.6, 4.8), SIGN_BLUE, c="Station")
box("Station_signborder", (ST["x1"] + 0.22, ST_DOOR.y - 2.7, 3.85), (ST["x1"] + 0.25, ST_DOOR.y + 2.7, 4.85), FRAME_W, c="Station")
# police badge emblem (generic: star in a circle) on the sign
def star_mesh(name, r1, r2, n=5):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((0, (r1 if k % 2 == 0 else r2) * math.sin(math.pi * k / n), (r1 if k % 2 == 0 else r2) * math.cos(math.pi * k / n))) for k in range(2 * n)]
    bm.faces.new(vs); bm.to_mesh(me); bm.free(); return me
GOLD = pbr("BadgeGold", (0.9, 0.65, 0.15), 0.3, metal=1.0)
st_badge = bpy.data.objects.new("Station_badge", star_mesh("star", 0.34, 0.14)); st_badge.location = (ST["x1"] + 0.33, ST_DOOR.y, 4.35)
st_badge.data.materials.append(GOLD); link(st_badge, "Station")
cyl("Station_badgering", (ST["x1"] + 0.325, ST_DOOR.y, 4.35), 0.4, 0.01, FRAME_W, c="Station", rot=(0, R_(90), 0), verts=24)
for k, dy in enumerate((-1.3, 1.3)):
    cyl("Station_lamp%d" % k, (ST["x1"] + 0.18, ST_DOOR.y + dy, 2.4), 0.09, 0.25, pbr("StLamp", (1, 1, 1), 0.2, emit=(1, 0.9, 0.7), estr=6.0), c="Station")
inst(MOTO, "Station_Bike", (ST["x1"] + 2.2, ST_DOOR.y + 3.5, 0.03), rotz=R_(70), c="Station")
for k, y in enumerate((ST["y0"] + 0.4, ST["y1"] - 0.4)):
    inst(PLANT, "Station_Plant%d" % k, (ST["x1"] + 0.6, y, 0.0), c="Station")
# interior: three desks, chairs, almirah, files, fan, wall clock, tube lights
ST_DESKS = [Vector((-10.5, 53.5, 0.0)), Vector((-10.5, 60.5, 0.0)), Vector((-15.5, 57.0, 0.0))]
for i, p in enumerate(ST_DESKS):
    inst(DESK_M, "St_Desk_%d" % i, p, rotz=R_(90) if i < 2 else R_(-90), c="Station")
    inst(NOTEP, "St_Notes_%d" % i, p + Vector((0.1, 0.3, dd.z)), rotz=R_(10 * i), c="Station")
    for k in range(3):
        box(f"St_File_{i}_{k}", (p.x - 0.2, p.y - 0.5 + k * 0.05, dd.z), (p.x + 0.15, p.y - 0.25, dd.z + 0.04 + k * 0.03), pbr("FileTan", (0.75, 0.6, 0.35), 0.8), c="Station")
for i in range(4):
    box("St_Almirah_%d" % i, (-18.8, 51.0 + i * 1.0, 0.0), (-18.3, 51.9 + i * 1.0, 1.95), pbr("AlmirahGrey", (0.35, 0.38, 0.36), 0.4, metal=0.6), c="Station")
for k, nm in enumerate(("ceiling_fan", "ceiling_fan_blades")):
    o = FAN_D[nm].copy(); o.name = "StationFan_" + nm; o.location = (-12.5, 57.0, 3.4 - 0.6); link(o, "Station")
for nm, o0 in CLOCK_PARTS.items():
    o = o0.copy(); o.name = "St_" + nm; link(o, "Station")
ST_TUBES = []
for i, y in enumerate((53.0, 61.0)):
    ST_TUBES.append(box("St_tube_%d" % i, (-12.6, y - 0.6, 3.33), (-12.5, y + 0.6, 3.38), pbr("StTube", (1, 1, 1), 0.3, emit=(1.0, 0.97, 0.9), estr=6.0), c="Station").name)
for i, y in enumerate((53.0, 61.0)):
    L = bpy.data.lights.new("StFill_%d" % i, "AREA"); L.energy = 300; L.size = 1.2; L.color = (1.0, 0.96, 0.9)
    lo = bpy.data.objects.new("StFill_%d" % i, L); lo.location = (-12.5, y, 3.25); link(lo, "Station")
box("St_Notice", (-18.85, 59.5, 1.3), (-18.82, 61.5, 2.3), pbr("Cork", (0.55, 0.4, 0.25), 0.9), c="Station")
for k in range(6):
    box("St_Paper_%d" % k, (-18.82, 59.65 + (k % 3) * 0.6, 1.4 + (k // 3) * 0.45), (-18.80, 60.05 + (k % 3) * 0.6, 1.8 + (k // 3) * 0.45), pbr("Paper", (0.92, 0.9, 0.85), 0.8), c="Station")
box("St_Cooler", (-18.6, 63.0, 0.0), (-18.2, 63.5, 1.2), pbr("CoolerBlue", (0.6, 0.75, 0.85), 0.3), c="Station")

# ------------------------------------------------------------------ props for the characters
HAT_Y = pbr("HardHatYellow", (0.95, 0.72, 0.03), 0.25)
def hard_hat(name):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.135)
    for v in [v for v in bm.verts if v.co.z < -0.005]: bm.verts.remove(v)
    for v in bm.verts: v.co.y *= 1.12; v.co.x *= 0.98; v.co.z *= 1.0
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(HAT_Y); link(o, "Props")
    for p in me.polygons: p.use_smooth = True
    so = o.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.006
    brim = cyl(name + "_brim", (0, 0, 0.0), 0.142, 0.008, HAT_Y, c="Props", verts=24); brim.scale = (1.0, 1.15, 1.0); brim.parent = o
    peak = box(name + "_peak", (-0.06, -0.2, -0.004), (0.06, -0.14, 0.004), HAT_Y, c="Props", bevel=0.01); peak.parent = o
    ridge = box(name + "_ridge", (-0.01, -0.11, 0.115), (0.01, 0.11, 0.14), HAT_Y, c="Props", bevel=0.008); ridge.parent = o
    return o
hard_hat("HardHat_Road"); hard_hat("HardHat_Work")
inst(PHONE, "St_Phone", (0, 0, 0), c="Props")
for i in range(2):
    inst(A4, "FanPaper_%d" % i, (0, 0, 0), c="Props")
inst(CLIP, "TicketPad", (0, 0, 0), scale=0.55, c="Props")
box("TicketSlip", (-0.045, -0.07, 0.0), (0.045, 0.07, 0.001), pbr("SlipPink", (0.95, 0.8, 0.8), 0.8), c="Props")
bike = inst(MOTO, "Bike", (STOP.x, -12.0, 0.0), c="Props")

# ------------------------------------------------------------------ world: day HDRI and dusk HDRI, mix keyed in 03
W = bpy.data.worlds.new("World"); sc.world = W; W.use_nodes = True
nt = W.node_tree; n = nt.nodes; l = nt.links
for x in list(n): n.remove(x)
out = n.new("ShaderNodeOutputWorld")
e1 = n.new("ShaderNodeTexEnvironment"); e1.image = bpy.data.images.load(f"{ASSETS}/ph/hdri/kloppenheim_06_puresky_2k.hdr")
e2 = n.new("ShaderNodeTexEnvironment"); e2.image = bpy.data.images.load(f"{ASSETS}/ph/hdri/venice_sunset_2k.hdr")
mp = n.new("ShaderNodeMapping"); tc = n.new("ShaderNodeTexCoord"); l.new(tc.outputs["Generated"], mp.inputs["Vector"])
mp.inputs["Rotation"].default_value = (0, 0, R_(200)); l.new(mp.outputs[0], e1.inputs[0]); l.new(mp.outputs[0], e2.inputs[0])
mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.name = "DuskMix"; mx.inputs["Factor"].default_value = 0.0
l.new(e1.outputs["Color"], mx.inputs["A"]); l.new(e2.outputs["Color"], mx.inputs["B"])
bg = n.new("ShaderNodeBackground"); bg.name = "WorldBG"; bg.inputs["Strength"].default_value = 1.0
l.new(mx.outputs["Result"], bg.inputs["Color"]); l.new(bg.outputs[0], out.inputs[0])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 4.5; sun_d.angle = R_(1.5); sun_d.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("Sun", sun_d); sun.rotation_euler = (R_(40), R_(0), R_(-140)); link(sun, "Lights")
print("SCENE_DONE", len(bpy.data.objects), "objects")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
