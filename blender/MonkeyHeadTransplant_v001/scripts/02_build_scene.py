"""MonkeyHeadTransplant scene: render settings, 1970s OR + recovery corner, props, monkeys, people, x-ray parts.
blender -b --python scripts/02_build_scene.py -- <v001_dir> <out.blend>"""
import sys, os, math, glob, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
ROOT, OUT = argv[0], argv[1]
AS = os.path.join(ROOT, "assets"); PH = os.path.join(AS, "ph"); BU = os.path.join(ROOT, "build")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
FPS, END = 60, 1770
random.seed(7)
# ------------------------------------------------------------------ render settings (farm baseline)
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = "CYCLES"
c = sc.cycles
c.device = "CPU"; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 12
c.caustics_reflective = c.caustics_refractive = False
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = "sRGB"
vs = sc.view_settings; vs.view_transform = "AgX"; vs.look = "AgX - Medium High Contrast"; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings; im.file_format = "PNG"; im.color_mode = "RGB"; im.color_depth = "8"; im.compression = 15
sc.render.filepath = "//render/MonkeyHeadTransplant_"
V = lambda *a: Vector(a)
col = sc.collection

# ------------------------------------------------------------------ material helpers
def img(path, nc=False):
    i = bpy.data.images.load(path, check_existing=True)
    if nc: i.colorspace_settings.name = "Non-Color"
    return i
def find(folder, key):
    g = sorted(glob.glob(os.path.join(PH, folder, "textures", f"*_{key}_*")))
    return g[0] if g else None
def pbr(name, folder, scale, tint=(1, 1, 1, 1), sat=1.0, val=1.0, bump=0.6, rough_add=0.0, coord="Object"):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / scale,) * 3
    l.new(tc.outputs[coord], mp.inputs["Vector"])
    d = n.new("ShaderNodeTexImage"); d.image = img(find(folder, "diff"))
    hsv = n.new("ShaderNodeHueSaturation"); hsv.inputs["Saturation"].default_value = sat; hsv.inputs["Value"].default_value = val
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0; mx.inputs["B"].default_value = tint
    l.new(mp.outputs["Vector"], d.inputs["Vector"]); l.new(d.outputs["Color"], hsv.inputs["Color"]); l.new(hsv.outputs["Color"], mx.inputs["A"])
    l.new(mx.outputs["Result"], p.inputs["Base Color"])
    rf = find(folder, "rough")
    if rf:
        r = n.new("ShaderNodeTexImage"); r.image = img(rf, True); l.new(mp.outputs["Vector"], r.inputs["Vector"])
        ra = n.new("ShaderNodeMath"); ra.operation = "ADD"; ra.inputs[1].default_value = rough_add; ra.use_clamp = True
        l.new(r.outputs["Color"], ra.inputs[0]); l.new(ra.outputs[0], p.inputs["Roughness"])
    nf = find(folder, "nor_gl")
    if nf:
        nm = n.new("ShaderNodeTexImage"); nm.image = img(nf, True); l.new(mp.outputs["Vector"], nm.inputs["Vector"])
        nmap = n.new("ShaderNodeNormalMap"); nmap.inputs["Strength"].default_value = bump
        l.new(nm.outputs["Color"], nmap.inputs["Color"]); l.new(nmap.outputs["Normal"], p.inputs["Normal"])
    return m
def mat(name, colr, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0, trans=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = colr; p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    if emit: p.inputs["Emission Color"].default_value = emit; p.inputs["Emission Strength"].default_value = estr
    if trans: p.inputs["Transmission Weight"].default_value = trans
    if coat: p.inputs["Coat Weight"].default_value = coat
    p.inputs["Alpha"].default_value = alpha
    return m
def link(o, coll=None):
    (coll or col).objects.link(o); return o
def box(name, size, loc, m=None, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    if m: o.data.materials.append(m)
    return o
def cyl(name, r, h, loc, m=None, verts=32, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts, rotation=rot)
    o = bpy.context.active_object; o.name = name
    if m: o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); return o
def glb(name, path, scale, loc, rot=(0, 0, 0), ground=True):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    ms = [o for o in new if o.type == "MESH"]
    for o in ms:
        M = o.matrix_world.copy(); o.parent = None; o.matrix_world = M
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in ms: o.select_set(True)
    bpy.context.view_layer.objects.active = ms[0]
    if len(ms) > 1: bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs_ = [v.co for v in o.data.vertices]
    mn = V(*[min(v[i] for v in vs_) for i in range(3)]); mx = V(*[max(v[i] for v in vs_) for i in range(3)])
    ctr = V((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z if ground else (mn.z + mx.z) / 2)
    for v in o.data.vertices: v.co -= ctr
    o.scale = (scale,) * 3; o.rotation_euler = rot; o.location = loc
    print("GLB", name, "size", tuple(round((mx - mn)[i] * scale, 3) for i in range(3)))
    return o

FADES = {}   # name -> Value node list (keyed later in 03): 1 = visible, 0 = gone (transparent)
def add_fade(m, group):
    if not m or not m.use_nodes or m.get("fade"): return
    nt = m.node_tree; out = next((x for x in nt.nodes if x.type == "OUTPUT_MATERIAL" and x.is_active_output), None)
    if not out or not out.inputs["Surface"].links: return
    src = out.inputs["Surface"].links[0].from_socket
    v = nt.nodes.new("ShaderNodeValue"); v.name = v.label = "Fade_" + group; v.outputs[0].default_value = 1.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(v.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(src, mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"]); m["fade"] = group
    FADES.setdefault(group, []).append(m.name)

# ------------------------------------------------------------------ materials
M_wall = pbr("M_WallTiles", "interior_tiles", 0.9, tint=(0.70, 0.86, 0.78, 1), sat=0.3, val=1.0, bump=0.5)
M_floor = pbr("M_Floor", "granite_tile", 1.6, tint=(0.92, 0.9, 0.84, 1), sat=0.6, val=0.85, bump=0.4)
M_ceil = mat("M_Ceiling", (0.82, 0.83, 0.8, 1), 0.8)
M_chrome = mat("M_Chrome", (0.85, 0.86, 0.88, 1), 0.12, 1.0)
M_steel = mat("M_SteelBrushed", (0.7, 0.71, 0.72, 1), 0.28, 1.0)
M_enamel = mat("M_EnamelCream", (0.80, 0.78, 0.68, 1), 0.35, coat=0.4)
M_vinyl = mat("M_VinylGreen", (0.10, 0.25, 0.20, 1), 0.38, coat=0.3)
M_drape = pbr("M_DrapeGreen", "cotton_jersey", 0.12, tint=(0.40, 0.62, 0.55, 1), sat=0.0, val=0.9, bump=0.5)
M_towel = pbr("M_TowelWhite", "cotton_jersey", 0.08, tint=(0.95, 0.95, 0.92, 1), sat=0.0, val=1.0, bump=0.7)
M_gauze = pbr("M_Gauze", "cotton_jersey", 0.02, tint=(1.0, 0.99, 0.96, 1), sat=0.0, val=1.15, bump=0.8)
M_glass = mat("M_FrostedGlass", (0.85, 0.95, 0.97, 1), 0.35, trans=1.0)
M_cyanglow = mat("M_CyanGlow", (0, 0, 0, 1), 1.0, emit=(0.45, 0.85, 1.0, 1), estr=2.2)
M_lampin = mat("M_LampLens", (1, 1, 1, 1), 0.2, emit=(1.0, 0.95, 0.85, 1), estr=30.0)
M_rubber = mat("M_Rubber", (0.03, 0.03, 0.03, 1), 0.7)
M_wood = mat("M_WoodDark", (0.22, 0.12, 0.06, 1), 0.45)
M_glove = mat("M_Glove", (0.86, 0.80, 0.66, 1), 0.35)
M_glove.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.2
M_cap = pbr("M_CapGreen", "cotton_jersey", 0.05, tint=(0.40, 0.62, 0.55, 1), sat=0.0, val=0.95, bump=0.6)
M_mask = pbr("M_MaskWhite", "cotton_jersey", 0.03, tint=(0.88, 0.92, 0.9, 1), sat=0.0, val=1.0, bump=0.6)
M_ink = mat("M_MarkerInk", (0.12, 0.03, 0.2, 1), 0.4)
M_thread = mat("M_Thread", (0.05, 0.05, 0.08, 1), 0.4)

# ------------------------------------------------------------------ room
room = bpy.data.collections.new("Room"); col.children.link(room)
def to_room(o):
    for c_ in o.users_collection: c_.objects.unlink(o)
    room.objects.link(o); return o
fl = box("Floor", (8.5, 7.5, 0.1), (0.6, -0.25, -0.05), M_floor); to_room(fl)
to_room(box("Ceiling", (8.5, 7.5, 0.1), (0.6, -0.25, 3.05), M_ceil))
to_room(box("Wall_Back", (8.5, 0.12, 3.0), (0.6, 3.06, 1.5), M_wall))
to_room(box("Wall_Left", (0.12, 7.5, 3.0), (-3.66, -0.25, 1.5), M_wall))
to_room(box("Wall_Right", (0.12, 7.5, 3.0), (4.86, -0.25, 1.5), M_wall))
to_room(box("Wall_Front", (8.5, 0.12, 3.0), (0.6, -4.0, 1.5), M_wall))
# skirting + frosted glass partition in the back wall, cyan studio glow beyond it
to_room(box("Skirting", (8.5, 0.03, 0.12), (0.6, 2.99, 0.06), M_enamel))
win = to_room(box("Partition_Glass", (3.2, 0.03, 1.5), (-0.7, 2.86, 1.6), M_glass))
to_room(box("Partition_Frame_T", (3.3, 0.06, 0.06), (-0.7, 2.86, 2.38), M_enamel))
to_room(box("Partition_Frame_B", (3.3, 0.06, 0.06), (-0.7, 2.86, 0.82), M_enamel))
for i in range(5):
    to_room(box(f"Partition_Mullion_{i}", (0.05, 0.06, 1.6), (-2.3 + i * 0.8, 2.86, 1.6), M_enamel))
glow = to_room(box("CyanBeyond", (3.4, 0.02, 1.8), (-0.7, 2.97, 1.6), M_cyanglow))
to_room(box("Partition_Box", (3.4, 0.14, 0.02), (-0.7, 2.92, 2.5), M_enamel)); to_room(box("Partition_BoxB", (3.4, 0.14, 0.02), (-0.7, 2.92, 0.7), M_enamel))
gn = M_cyanglow.node_tree; gp = gn.nodes["Principled BSDF"]
gtc = gn.nodes.new("ShaderNodeTexCoord"); gsep = gn.nodes.new("ShaderNodeSeparateXYZ"); gmr = gn.nodes.new("ShaderNodeMapRange")
gmr.inputs["From Min"].default_value = 0.7; gmr.inputs["From Max"].default_value = 2.4
gcr = gn.nodes.new("ShaderNodeValToRGB"); gcr.color_ramp.elements[0].color = (0.25, 0.75, 0.95, 1); gcr.color_ramp.elements[1].color = (0.92, 0.98, 1.0, 1)
gn.links.new(gtc.outputs["Generated"], gsep.inputs[0]); gn.links.new(gsep.outputs["Z"], gcr.inputs["Fac"]); gn.links.new(gcr.outputs["Color"], gp.inputs["Emission Color"])
# wall cabinets with glass doors and bottles (back wall right) + a clock without numerals
for i in range(3):
    x = 1.6 + i * 0.75
    to_room(box(f"Cabinet_{i}", (0.7, 0.35, 1.9), (x, 2.8, 0.95), M_enamel, 0.01))
    to_room(box(f"CabinetGlass_{i}", (0.6, 0.02, 1.0), (x, 2.62, 1.35), M_glass))
    for k in range(5):
        h = random.uniform(0.12, 0.25)
        bt = to_room(cyl(f"Bottle_{i}_{k}", random.uniform(0.03, 0.05), h, (x - 0.22 + k * 0.11, 2.75, 1.0 + h / 2),
                         mat(f"M_Bottle_{i}_{k}", random.choice([(0.35, 0.2, 0.05, 1), (0.9, 0.95, 0.97, 1), (0.2, 0.35, 0.3, 1)]), 0.1, trans=0.9)))
    for k in range(4):
        h = random.uniform(0.1, 0.22)
        to_room(cyl(f"Jar_{i}_{k}", 0.05, h, (x - 0.2 + k * 0.13, 2.75, 1.45 + h / 2), mat(f"M_Jar_{i}_{k}", (0.85, 0.9, 0.92, 1), 0.08, trans=0.95)))
clk = to_room(cyl("Clock", 0.16, 0.04, (0.9, 2.98, 2.45), M_enamel, 48, rot=(math.radians(90), 0, 0)))
to_room(cyl("ClockFace", 0.145, 0.01, (0.9, 2.955, 2.45), mat("M_ClockFace", (0.92, 0.91, 0.86, 1), 0.4), 48, rot=(math.radians(90), 0, 0)))
for i in range(12):
    a = i * math.pi / 6
    to_room(box(f"ClockTick_{i}", (0.008, 0.004, 0.025), (0.9 + 0.12 * math.sin(a), 2.948, 2.45 + 0.12 * math.cos(a)), M_rubber, rot=(0, -a, 0)))
hand_m = to_room(box("ClockHandMin", (0.006, 0.004, 0.12), (0.9, 2.944, 2.45 + 0.05), M_rubber))
hand_h = to_room(box("ClockHandHour", (0.009, 0.004, 0.08), (0.9, 2.942, 2.45 + 0.035), M_rubber))
for hnd in (hand_m, hand_h):
    bpy.context.view_layer.objects.active = hnd; sc.cursor.location = (0.9, 2.944, 2.45)
    bpy.ops.object.select_all(action="DESELECT"); hnd.select_set(True); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
# radiator + wall pipes on the left wall, ceiling light panels
to_room(box("Radiator", (0.08, 1.2, 0.6), (-3.55, 0.5, 0.45), M_enamel, 0.01))
for i in range(14): to_room(box(f"RadFin_{i}", (0.1, 0.03, 0.56), (-3.53, -0.05 + i * 0.085, 0.45), M_enamel))
to_room(cyl("Pipe_A", 0.025, 7.0, (-3.56, -0.25, 2.6), M_enamel, 16, rot=(math.radians(90), 0, 0)))
to_room(cyl("Pipe_B", 0.018, 7.0, (-3.56, -0.25, 2.5), M_steel, 16, rot=(math.radians(90), 0, 0)))
for i, (x, y) in enumerate(((-1.8, -1.5), (1.0, -1.5), (3.2, 0.8), (-1.8, 1.5))):
    to_room(box(f"CeilPanel_{i}", (1.0, 0.5, 0.04), (x, y, 2.99), mat(f"M_CeilPanel_{i}", (1, 1, 1, 1), 0.4, emit=(1.0, 0.97, 0.9, 1), estr=3.0)))

# ------------------------------------------------------------------ operating tables (top surface z = 0.92), centres x = -0.42 / +0.42
TZ = 0.92
TABLES = {}
for k, x in (("1", -0.42), ("2", 0.42)):
    parts = []
    parts.append(cyl(f"T{k}_Pedestal", 0.07, 0.72, (x, 0.2, 0.42), M_chrome))
    parts.append(box(f"T{k}_Foot", (0.42, 0.62, 0.06), (x, 0.2, 0.03), M_enamel, 0.02))
    parts.append(box(f"T{k}_Frame", (0.5, 0.86, 0.05), (x, 0.2, TZ - 0.085), M_chrome, 0.01))
    parts.append(box(f"T{k}_Pad", (0.48, 0.84, 0.05), (x, 0.2, TZ - 0.035), M_vinyl, 0.015))
    parts.append(box(f"T{k}_Drape", (0.52, 0.88, 0.012), (x, 0.2, TZ - 0.004), M_drape, 0.004))
    for sx in (-1, 1):
        parts.append(box(f"T{k}_DrapeSide{sx}", (0.012, 0.88, 0.22), (x + sx * 0.262, 0.2, TZ - 0.11), M_drape))
    parts.append(box(f"T{k}_DrapeEnd", (0.52, 0.012, 0.22), (x, 0.2 + 0.442, TZ - 0.11), M_drape))
    parts.append(box(f"T{k}_Crank", (0.03, 0.08, 0.03), (x + 0.12, -0.1, 0.35), M_chrome))
    parts.append(cyl(f"T{k}_Pump", 0.03, 0.12, (x, -0.05, 0.12), M_enamel, rot=(0, math.radians(70), 0)))
    TABLES[k] = parts
    for p in parts: to_room(p)
# rolled towel head-rests (one per table) - placed after the monkeys are posed
# ------------------------------------------------------------------ surgical lamp (dome on a ceiling arm)
lamp_root = link(bpy.data.objects.new("Lamp_Root", None)); lamp_root.location = (0, 0.15, 2.98)
arm1 = cyl("Lamp_ArmV", 0.025, 0.55, (0, 0.15, 2.7), M_enamel); arm1.parent = lamp_root; arm1.matrix_parent_inverse = lamp_root.matrix_world.inverted()
lamp_piv = link(bpy.data.objects.new("Lamp_Pivot", None)); lamp_piv.location = (0, 0.15, 2.42); lamp_piv.parent = lamp_root
lamp_piv.matrix_parent_inverse = lamp_root.matrix_world.inverted()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.34, location=(0, 0.15, 1.95), segments=48, ring_count=24)
dome = bpy.context.active_object; dome.name = "Lamp_Dome"
bm = bmesh.new(); bm.from_mesh(dome.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS"); bm.to_mesh(dome.data); bm.free()
dome.modifiers.new("solid", "SOLIDIFY").thickness = 0.012; dome.data.materials.append(M_enamel); bpy.ops.object.shade_smooth()
lens = cyl("Lamp_Lens", 0.3, 0.01, (0, 0.15, 1.905), M_lampin, 48)
ring = cyl("Lamp_Ring", 0.335, 0.03, (0, 0.15, 1.905), M_chrome, 48)
handle = cyl("Lamp_Handle", 0.02, 0.14, (0, 0.15, 1.84), M_steel, 16)
yoke = cyl("Lamp_Yoke", 0.02, 0.45, (0, 0.15, 2.2), M_enamel, 16)
for i in range(6):
    a = i * math.pi / 3
    cyl(f"Lamp_Bulb_{i}", 0.05, 0.012, (0.17 * math.cos(a), 0.15 + 0.17 * math.sin(a), 1.898), mat(f"M_Bulb_{i}", (1, 1, 1, 1), 0.1, emit=(1, 0.96, 0.88, 1), estr=60.0), 24)
spot_d = bpy.data.lights.new("Lamp_Spot", "SPOT"); spot_d.energy = 900; spot_d.spot_size = math.radians(55); spot_d.spot_blend = 0.6
spot_d.shadow_soft_size = 0.25; spot_d.color = (1.0, 0.96, 0.9)
spot = link(bpy.data.objects.new("Lamp_Spot", spot_d)); spot.location = (0, 0.15, 1.88)
for o in [dome, lens, ring, handle, yoke, spot] + [o for o in bpy.data.objects if o.name.startswith("Lamp_Bulb_")]:
    M = o.matrix_world.copy(); o.parent = lamp_piv; o.matrix_world = M
for o in [arm1, lamp_piv, dome, lens, ring, handle, yoke, spot] + [o for o in bpy.data.objects if o.name.startswith("Lamp_Bulb_")]:
    pass
# ------------------------------------------------------------------ props: trolley with tray + instruments, IV stand, stools, bowl
cart = to_room(glb("Trolley", os.path.join(AS, "cart.glb"), 0.0095, (-1.12, -0.05, 0), rot=(0, 0, math.radians(90))))
tray = to_room(box("Tray", (0.46, 0.32, 0.02), (-1.12, -0.05, 0.86), M_steel, 0.006))
tools = to_room(glb("Instruments", os.path.join(AS, "tools.glb"), 0.95, (-1.12, -0.05, 0.871), rot=(math.radians(90), 0, math.radians(90))))
bowl = to_room(cyl("Bowl", 0.08, 0.04, (-1.02, 0.1, 0.89), M_steel, 32))
bowlb = bowl  # dropped by the nurse in beat 5 (animated in 03)
ivp = to_room(cyl("IV_Pole", 0.012, 1.8, (1.05, 0.55, 0.9), M_chrome, 16))
to_room(cyl("IV_Base", 0.2, 0.03, (1.05, 0.55, 0.02), M_chrome, 5))
to_room(box("IV_Hook", (0.3, 0.012, 0.012), (1.05, 0.55, 1.8), M_chrome))
ivb = to_room(box("IV_Bag", (0.1, 0.04, 0.16), (1.17, 0.55, 1.68), mat("M_IVBag", (0.9, 0.95, 0.95, 1), 0.1, trans=0.8), 0.015))
to_room(cyl("IV_Tube", 0.003, 0.9, (1.17, 0.55, 1.15), mat("M_Tube", (0.9, 0.9, 0.85, 1), 0.2, trans=0.5), 8))
for i, (x, y) in enumerate(((-1.6, 1.4), (-2.6, -1.9))):
    to_room(cyl(f"Stool_{i}", 0.17, 0.05, (x, y, 0.6), M_vinyl, 24))
    to_room(cyl(f"StoolLeg_{i}", 0.02, 0.58, (x, y, 0.3), M_chrome, 12))
    to_room(cyl(f"StoolBase_{i}", 0.2, 0.02, (x, y, 0.01), M_chrome, 5))
# old anaesthesia machine silhouette behind table 1 (boxes, gauges, hose) for depth
am = [box("Anaes_Body", (0.45, 0.4, 0.9), (-1.35, 1.25, 0.55), M_enamel, 0.02), box("Anaes_Top", (0.5, 0.42, 0.04), (-1.35, 1.25, 1.02), M_steel),
      cyl("Anaes_Cyl1", 0.06, 0.7, (-1.62, 1.3, 0.45), mat("M_CylBlue", (0.1, 0.2, 0.5, 1), 0.3)), cyl("Anaes_Cyl2", 0.06, 0.7, (-1.62, 1.15, 0.45), mat("M_CylGrey", (0.5, 0.5, 0.5, 1), 0.3)),
      cyl("Anaes_Gauge1", 0.05, 0.03, (-1.25, 1.04, 0.9), M_chrome, 24, rot=(math.radians(90), 0, 0)), cyl("Anaes_Gauge2", 0.05, 0.03, (-1.45, 1.04, 0.9), M_chrome, 24, rot=(math.radians(90), 0, 0)),
      cyl("Anaes_Bag", 0.08, 0.2, (-1.1, 1.05, 0.7), mat("M_BlackBag", (0.03, 0.03, 0.03, 1), 0.6), 16)]
for o in am: to_room(o)
for nm in ("Anaes_Gauge1", "Anaes_Gauge2"):
    to_room(cyl(nm + "_Face", 0.044, 0.005, bpy.data.objects[nm].location + V(0, -0.017, 0), mat("M_GaugeFace", (0.92, 0.9, 0.85, 1), 0.3), 24, rot=(math.radians(90), 0, 0)))

# ------------------------------------------------------------------ recovery corner: chair, monitor cart with the oscilloscope, side lamp
CH = V(2.35, 1.0, 0.0)    # chair position (faces -Y)
chair = to_room(glb("Chair", os.path.join(AS, "chair.glb"), 0.036, CH))
# measure the seat height by ray cast down the chair centre
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
hit = sc.ray_cast(dg, CH + V(0, 0, 2.0), V(0, 0, -1))
SEAT = hit[1].z if hit[0] else 0.45
print("CHAIR seat z", SEAT, "hit", hit[0], hit[4].name if hit[0] else None)
mcart = to_room(box("MonCart_Top", (0.5, 0.42, 0.03), (3.05, 0.95, 0.78), M_enamel, 0.008))
to_room(box("MonCart_Shelf", (0.48, 0.4, 0.02), (3.05, 0.95, 0.25), M_enamel, 0.005))
for sx in (-1, 1):
    for sy in (-1, 1):
        to_room(cyl(f"MonCart_Leg{sx}{sy}", 0.012, 0.76, (3.05 + sx * 0.22, 0.95 + sy * 0.18, 0.4), M_chrome, 12))
        to_room(cyl(f"MonCart_Wheel{sx}{sy}", 0.025, 0.02, (3.05 + sx * 0.22, 0.95 + sy * 0.18, 0.025), M_rubber, 16, rot=(0, math.radians(90), 0)))
scope = to_room(glb("Monitor", os.path.join(AS, "scope.glb"), 1.9, (3.05, 0.95, 0.795), rot=(0, 0, 0)))
to_room(box("Lamp2_Base", (0.12, 0.12, 0.02), (1.75, 1.45, 0.01), M_steel))
to_room(cyl("Lamp2_Pole", 0.01, 1.3, (1.75, 1.45, 0.66), M_chrome, 12))
to_room(cyl("Lamp2_Shade", 0.12, 0.16, (1.75, 1.45, 1.35), mat("M_Shade", (0.85, 0.8, 0.6, 1), 0.6), 24))
pl = bpy.data.lights.new("Lamp2_Light", "POINT"); pl.energy = 35; pl.color = (1.0, 0.85, 0.6); pl.shadow_soft_size = 0.1
to_room(link(bpy.data.objects.new("Lamp2_Light", pl))).location = (1.75, 1.45, 1.3)

# ------------------------------------------------------------------ world: hospital HDRI (dim) for reflections
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn = w.node_tree; bg = wn.nodes["Background"]
env = wn.nodes.new("ShaderNodeTexEnvironment"); env.image = img(os.path.join(PH, "hdri", "childrens_hospital_2k.hdr"))
wn.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.35
# fill lights (room)
for nm, loc, e, sz in (("Fill_Front", (0.4, -2.6, 2.3), 220, 1.5), ("Fill_Right", (3.6, -0.5, 2.4), 160, 1.2), ("Rim_Back", (-1.2, 2.4, 2.4), 140, 1.0)):
    ld = bpy.data.lights.new(nm, "AREA"); ld.energy = e; ld.size = sz; ld.color = (0.92, 0.97, 1.0)
    lo = link(bpy.data.objects.new(nm, ld)); lo.location = loc
    lo.rotation_euler = (V(0.2, 0.3, 0.9) - V(*loc)).to_track_quat("-Z", "Y").to_euler()

# ------------------------------------------------------------------ monkeys (append from build/monkey.blend)
with bpy.data.libraries.load(os.path.join(BU, "monkey.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
mk = {o.name: o for o in dst.objects if o}
for o in mk.values(): col.objects.link(o)
head, bodyA, bodyB, neckref = mk["MK_Head"], mk["MK_BodyA"], mk["MK_BodyB"], mk["NeckRef"]
# lying-on-side pose (model X->+Z, Y->-X, Z->-Y): belly faces +X, head points to -Y (toward the surgeon)
R_LIE = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0))).to_4x4()
mn_x = min(v.co.x for v in bodyA.data.vertices)          # becomes the lowest z after the rotation
def lie(x):
    return Matrix.Translation(V(x - 0.28, 0.36, TZ - mn_x + 0.004)) @ R_LIE
M_LIE1, M_LIE2 = lie(-0.42), lie(0.42)
rootA = link(bpy.data.objects.new("MonkeyRootA", None)); rootA.matrix_world = M_LIE1
rootB = link(bpy.data.objects.new("MonkeyRootB", None)); rootB.matrix_world = M_LIE2
rootB.rotation_mode = "QUATERNION"
bodyA.parent = rootA; bodyB.parent = rootB
head.parent = rootB; head.matrix_parent_inverse = Matrix.Identity(4)
head.matrix_basis = Matrix.Translation(V(0, 0, 0))   # head local (in B frame); 03 keys it from table 1 to table 2
print("LIE1 neck world", M_LIE1 @ neckref.location, "LIE2", M_LIE2 @ neckref.location)
# head-rest towels under each monkey's head (keeps the head from floating above the drape)
bpy.context.view_layer.update()
for k, R in (("1", M_LIE1), ("2", M_LIE2)):
    hw = [R @ v.co for v in head.data.vertices]
    hz = min(p.z for p in hw); hx = sum(p.x for p in hw) / len(hw); hy = sum(p.y for p in hw) / len(hw)
    t = cyl(f"T{k}_HeadRest", 0.04, 0.16, (hx, hy, TZ + 0.04), M_towel, 24, rot=(math.radians(90), 0, 0))
    t.scale = (1.0, max(0.3, (hz - TZ) / 0.08 + 0.05), 1.0); t.location.z = TZ + (hz - TZ) / 2 + 0.002
    TABLES[k].append(to_room(t))
    print("HEADREST", k, "gap", hz - TZ)
# surgical drape over each lower body: a heightfield sheet ray-cast down onto monkey + table, smoothed, edges hanging
for k, R, bd in (("1", M_LIE1, bodyA), ("2", M_LIE2, bodyB)):
    bpy.context.view_layer.update()
    tx = -0.42 if k == "1" else 0.42
    Mw = R; bv = BVHTree.FromPolygons([Mw @ v.co for v in bd.data.vertices], [tuple(p_.vertices) for p_ in bd.data.polygons])
    NX, NY = 36, 30; x0, x1, y0, y1 = tx - 0.33, tx + 0.33, 0.24, 0.68
    H = [[0.0] * (NX + 1) for _ in range(NY + 1)]
    for j in range(NY + 1):
        for i in range(NX + 1):
            x = x0 + (x1 - x0) * i / NX; y = y0 + (y1 - y0) * j / NY
            hz = TZ
            hit = bv.ray_cast(V(x, y, TZ + 1.0), V(0, 0, -1))
            if hit[0] is not None: hz = max(hz, hit[0].z)
            if abs(x - tx) > 0.262 or y > 0.642: hz = TZ - 0.03
            H[j][i] = hz + 0.028
    for it in range(3):   # dilate: the sheet rests on the highest point nearby (no fingers poking through)
        H2 = [row[:] for row in H]
        for j in range(NY + 1):
            for i in range(NX + 1):
                H2[j][i] = max(H[jj][ii] for jj in range(max(0, j - 1), min(NY, j + 1) + 1) for ii in range(max(0, i - 1), min(NX, i + 1) + 1))
        H = H2
    for it in range(7):
        H2 = [row[:] for row in H]
        for j in range(1, NY):
            for i in range(1, NX):
                H2[j][i] = max(H[j][i], (H[j][i] * 2 + H[j - 1][i] + H[j + 1][i] + H[j][i - 1] + H[j][i + 1]) / 6)
        H = H2
    bm = bmesh.new(); vv_ = {}
    for j in range(NY + 1):
        for i in range(NX + 1):
            x = x0 + (x1 - x0) * i / NX; y = y0 + (y1 - y0) * j / NY
            z = H[j][i]
            if abs(x - tx) > 0.262: z = TZ - 0.03 - (abs(x - tx) - 0.262) * 2.2
            if y > 0.642: z = min(z, TZ - 0.03 - (y - 0.642) * 2.2)
            vv_[i, j] = bm.verts.new((x, y, z))
    for j in range(NY):
        for i in range(NX):
            bm.faces.new((vv_[i, j], vv_[i + 1, j], vv_[i + 1, j + 1], vv_[i, j + 1]))
    me = bpy.data.meshes.new(f"T{k}_BodyDrape"); bm.to_mesh(me); bm.free()
    dr = to_room(link(bpy.data.objects.new(f"T{k}_BodyDrape", me))); dr.data.materials.append(M_drape)
    for p_ in me.polygons: p_.use_smooth = True
    dr.modifiers.new("s", "SOLIDIFY").thickness = 0.004
    TABLES[k].append(dr)
# gauze collars at the cut: one on the head, one on each body (sits on the neck plane)
def collar(name, parent, r_out, z_off):
    bpy.ops.mesh.primitive_torus_add(major_radius=r_out, minor_radius=0.0075, major_segments=48, minor_segments=12)
    t = bpy.context.active_object; t.name = name; t.data.materials.append(M_gauze); bpy.ops.object.shade_smooth()
    t.scale = (1.0, 0.85, 0.55)
    t.matrix_world = neckref.matrix_world @ Matrix.Translation(V(0, 0, z_off)) @ Matrix.Diagonal((1.0, 0.85, 0.55, 1))
    M = t.matrix_world.copy(); t.parent = parent; t.matrix_parent_inverse = Matrix.Identity(4); t.matrix_basis = M
    return t
# neck radius at the cut plane
nv = [v.co for v in bodyA.data.vertices if abs((v.co - neckref.location).dot(neckref.matrix_world.to_3x3().col[2])) < 0.004]
nc = sum(nv, Vector()) / max(1, len(nv)); NR = sum((v - nc).length for v in nv) / max(1, len(nv))
print("NECK centre", nc, "mean radius", NR, "n", len(nv))
neckref.location = nc
cA = collar("Collar_BodyA", bodyA, NR * 0.98, -0.006); cB = collar("Collar_BodyB", bodyB, NR * 0.98, -0.006)
cH = collar("Collar_Head", head, NR * 0.96, 0.008)
# seam ring + stitches (comp, under body B) - revealed in 03
bpy.ops.mesh.primitive_torus_add(major_radius=NR * 1.0, minor_radius=0.0009, major_segments=64, minor_segments=8)
seam = bpy.context.active_object; seam.name = "Seam"; seam.data.materials.append(mat("M_Seam", (0.22, 0.07, 0.06, 1), 0.45))
seam.matrix_world = neckref.matrix_world @ Matrix.Diagonal((1.0, 0.85, 1.0, 1)); M = seam.matrix_world.copy(); seam.parent = bodyB; seam.matrix_parent_inverse = Matrix.Identity(4); seam.matrix_basis = M
STITCH_N = 18
for i in range(STITCH_N):
    a = 2 * math.pi * i / STITCH_N
    loc = neckref.matrix_world @ V(NR * 1.02 * math.cos(a), NR * 0.85 * 1.02 * math.sin(a), 0.0)
    nrm = (neckref.matrix_world.to_3x3() @ V(math.cos(a), math.sin(a) / 0.85, 0)).normalized()
    up = neckref.matrix_world.to_3x3().col[2].normalized()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0009, depth=0.014, vertices=8)
    s_ = bpy.context.active_object; s_.name = f"Stitch_{i:02d}"; s_.data.materials.append(M_thread)
    Rm = Matrix((nrm.cross(up), nrm, up)).transposed()
    s_.matrix_world = Matrix.Translation(loc + nrm * 0.001) @ Rm.to_4x4()
    M = s_.matrix_world.copy(); s_.parent = bodyB; s_.matrix_parent_inverse = Matrix.Identity(4); s_.matrix_basis = M
# marker line on monkey A (dashed ring on the head/neck boundary), revealed by an angle mask in 03
bpy.ops.mesh.primitive_torus_add(major_radius=NR * 1.035, minor_radius=0.0016, major_segments=96, minor_segments=6)
mk_line = bpy.context.active_object; mk_line.name = "MarkerLine"
mm = mat("M_MarkerLine", (0.12, 0.03, 0.22, 1), 0.4); mk_line.data.materials.append(mm)
mk_line.matrix_world = neckref.matrix_world @ Matrix.Translation(V(0, 0, 0.003)) @ Matrix.Diagonal((1.0, 0.85, 1.0, 1))
M = mk_line.matrix_world.copy(); mk_line.parent = bodyA; mk_line.matrix_parent_inverse = Matrix.Identity(4); mk_line.matrix_basis = M
nt = mm.node_tree; tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
at = nt.nodes.new("ShaderNodeMath"); at.operation = "ARCTAN2"
nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], at.inputs[0]); nt.links.new(sep.outputs["X"], at.inputs[1])
rv = nt.nodes.new("ShaderNodeValue"); rv.name = rv.label = "Reveal"; rv.outputs[0].default_value = 0.0
mp_ = nt.nodes.new("ShaderNodeMapRange"); mp_.inputs["From Min"].default_value = -math.pi; mp_.inputs["From Max"].default_value = math.pi
nt.links.new(at.outputs[0], mp_.inputs["Value"])
cmp = nt.nodes.new("ShaderNodeMath"); cmp.operation = "LESS_THAN"; nt.links.new(mp_.outputs["Result"], cmp.inputs[0]); nt.links.new(rv.outputs[0], cmp.inputs[1])
dash = nt.nodes.new("ShaderNodeMath"); dash.operation = "SINE"; dmul = nt.nodes.new("ShaderNodeMath"); dmul.operation = "MULTIPLY"; dmul.inputs[1].default_value = 22
nt.links.new(at.outputs[0], dmul.inputs[0]); nt.links.new(dmul.outputs[0], dash.inputs[0])
dgt = nt.nodes.new("ShaderNodeMath"); dgt.operation = "GREATER_THAN"; dgt.inputs[1].default_value = -0.3; nt.links.new(dash.outputs[0], dgt.inputs[0])
both = nt.nodes.new("ShaderNodeMath"); both.operation = "MULTIPLY"; nt.links.new(cmp.outputs[0], both.inputs[0]); nt.links.new(dgt.outputs[0], both.inputs[1])
trn = nt.nodes.new("ShaderNodeBsdfTransparent"); mix = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes["Material Output"]
nt.links.new(both.outputs[0], mix.inputs["Fac"]); nt.links.new(trn.outputs[0], mix.inputs[1]); nt.links.new(nt.nodes["Principled BSDF"].outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
# marker pen + needle holder + curved needle + forceps (procedural, held by the surgeon in 03)
pen = cyl("MarkerPen", 0.0055, 0.13, (0, 0, 0), mat("M_PenBody", (0.85, 0.85, 0.82, 1), 0.3), 16)
pen_tip = cyl("MarkerPenTip", 0.0035, 0.02, (0, 0, -0.072), mat("M_PenCap", (0.25, 0.05, 0.35, 1), 0.4), 12); pen_tip.parent = pen
nh = box("NeedleHolder", (0.006, 0.004, 0.15), (0, 0, 0), M_chrome, 0.001)
for sx in (-1, 1):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.0022, location=(sx * 0.012, 0, 0.085), rotation=(math.radians(90), 0, 0))
    r_ = bpy.context.active_object; r_.name = f"NeedleHolderRing{sx}"; r_.data.materials.append(M_chrome); r_.parent = nh
bpy.ops.curve.primitive_bezier_circle_add(radius=0.009)
ndl = bpy.context.active_object; ndl.name = "Needle"; ndl.data.bevel_depth = 0.0006; ndl.data.materials.append(M_chrome)
ndl.data.splines[0].use_cyclic_u = False
ndl.parent = nh; ndl.location = (0, 0, -0.085)
fc = box("Forceps", (0.005, 0.003, 0.12), (0, 0, 0), M_steel, 0.001)
# thread (curve hooked between needle and the seam: updated by hooks in 03)
bpy.ops.curve.primitive_bezier_curve_add()
thr = bpy.context.active_object; thr.name = "Thread"; thr.data.bevel_depth = 0.0004; thr.data.materials.append(M_thread)

# ------------------------------------------------------------------ x-ray internals: brain + spinal cord (in model space, parented to head / bodyB)
brain = glb("XR_Brain", os.path.join(AS, "brain.glb"), 0.068, (0, 0, 0), ground=False)
FW = V(-0.385, -0.923, 0).normalized()
eyemid = V(-0.0844, -0.4668, 0.2635 + 0.181)
brain.rotation_euler = (0, 0, math.atan2(FW.y, FW.x) + math.pi / 2 + math.pi)
brain.location = eyemid - FW * 0.05 + V(0, 0, 0.018)
brain.parent = head
M_xbrain = mat("M_XR_Brain", (1.0, 0.35, 0.45, 1), 0.3, emit=(1.0, 0.22, 0.38, 1), estr=9.0)
brain.data.materials.clear(); brain.data.materials.append(M_xbrain)
M_xcord = mat("M_XR_Cord", (1.0, 0.85, 0.5, 1), 0.3, emit=(1.0, 0.8, 0.35, 1), estr=6.0)
M_xbone = mat("M_XR_Vertebra", (0.85, 1.0, 0.9, 1), 0.4, emit=(0.6, 1.0, 0.8, 1), estr=1.2)
# spine line: ray cast the back surface from behind (+Y) along the body centre line
bodyA.hide_set(False)
bvh_obj = bodyA
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(bvh_obj, bpy.context.evaluated_depsgraph_get())
Mi = bvh_obj.matrix_world.inverted()
def back_pt(z):
    o_ = V(0.003, 0.6, z); hit = bvh.ray_cast(o_, V(0, -1, 0))
    return hit[0]
pts = []
for i in range(14):
    z = 0.10 + i * 0.024
    if z > neckref.location.z + 0.01: break
    p = back_pt(z)
    if p is not None and p.y > -0.4: pts.append(p + V(0, -0.028, 0))
nb = neckref.location
pts = [p for p in pts if p.z < 0.31]
p_end = nb + V(0, 0.0, -0.012); p_last = pts[-1]
ctrl = p_last.lerp(p_end, 0.5) + V(0, 0.035, 0.03)       # cervical curve: rises and comes forward to the skull base
for k in range(1, 6):
    t = k / 5.0
    pts.append(p_last * (1 - t) ** 2 + ctrl * 2 * t * (1 - t) + p_end * t * t)
print("SPINE pts", len(pts), pts[0], pts[-1])
def tube(name, P, r, m, parent):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 4
    sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
    for i, p in enumerate(P): sp.points[i].co = (p.x, p.y, p.z, 1)
    o = link(bpy.data.objects.new(name, cu)); cu.materials.append(m); o.parent = parent
    return o
cord_b = tube("XR_CordBody", pts, 0.0045, M_xcord, bodyB)
brain_base = brain.location + V(0, 0, -0.022) - FW * 0.005
cord_h = tube("XR_CordHead", [brain_base, nb + V(0, 0, 0.022)], 0.0045, M_xcord, head)
verts_ = []
for i, p in enumerate(pts[:-1]):
    t = cyl(f"XR_Vert_{i:02d}", 0.011, 0.012, p, M_xbone, 16)
    d = (pts[i + 1] - p).normalized(); t.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); t.parent = bodyB; verts_.append(t)
for nm, p in (("XR_GapGlowBody", nb + V(0, 0, -0.012)), ("XR_GapGlowHead", nb + V(0, 0, 0.022))):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, location=p); g = bpy.context.active_object; g.name = nm
    g.data.materials.append(mat("M_" + nm, (1, 0.3, 0.2, 1), 0.3, emit=(1.0, 0.25, 0.1, 1), estr=12.0))
    g.parent = bodyB if "Body" in nm else head
# a travelling pulse along the head cord (keyed in 03) that stops at the gap
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0065); pulse = bpy.context.active_object; pulse.name = "XR_Pulse"
pulse.data.materials.append(mat("M_XR_Pulse", (1, 1, 1, 1), 0.2, emit=(1.0, 0.95, 0.7, 1), estr=25.0)); pulse.parent = head
XR_OBJS = [brain, cord_b, cord_h, pulse] + verts_ + [bpy.data.objects["XR_GapGlowBody"], bpy.data.objects["XR_GapGlowHead"]]
for o in XR_OBJS: o["xray"] = 1
# x-ray skin: fresnel green glass mixed in by a value node per monkey material
def xray_mix(m):
    nt = m.node_tree; out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL" and x.is_active_output)
    src = out.inputs["Surface"].links[0].from_socket
    v = nt.nodes.new("ShaderNodeValue"); v.name = v.label = "XRay"; v.outputs[0].default_value = 0.0
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.25, 1.0, 0.55, 1)
    emm = nt.nodes.new("ShaderNodeMath"); emm.operation = "MULTIPLY"; emm.inputs[1].default_value = 3.0
    nt.links.new(lw.outputs["Facing"], emm.inputs[0]); nt.links.new(emm.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.7, 1.0, 0.8, 1)
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(tr.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
    mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(v.outputs[0], mx.inputs["Fac"]); nt.links.new(src, mx.inputs[1]); nt.links.new(ad.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
for mn_ in ("M_MonkeyHead", "M_MonkeyGinger", "M_NeckCap", "M_Gauze", "M_Seam", "M_MonkeyPale"):
    if bpy.data.materials.get(mn_): xray_mix(bpy.data.materials[mn_])

# ------------------------------------------------------------------ x-ray void: camera-centred opaque studio-gradient sphere (keyed in 03)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, segments=48, ring_count=24); void = bpy.context.active_object; void.name = "XR_Void"
bpy.ops.object.shade_smooth()
vm = bpy.data.materials.new("M_XR_Void"); vm.use_nodes = True; vn = vm.node_tree
for n_ in list(vn.nodes):
    if n_.type != "OUTPUT_MATERIAL": vn.nodes.remove(n_)
vtc = vn.nodes.new("ShaderNodeTexCoord"); vsep = vn.nodes.new("ShaderNodeSeparateXYZ"); vmr = vn.nodes.new("ShaderNodeMapRange")
vmr.inputs["From Min"].default_value = -0.75; vmr.inputs["From Max"].default_value = 0.6
vcr = vn.nodes.new("ShaderNodeValToRGB"); vcr.color_ramp.elements[0].color = (0.02, 0.42, 0.70, 1); vcr.color_ramp.elements[1].color = (0.62, 0.90, 1.0, 1)
vem = vn.nodes.new("ShaderNodeEmission"); vem.inputs["Strength"].default_value = 1.0
vtr = vn.nodes.new("ShaderNodeBsdfTransparent"); vmx = vn.nodes.new("ShaderNodeMixShader")
vv = vn.nodes.new("ShaderNodeValue"); vv.name = vv.label = "VoidOn"; vv.outputs[0].default_value = 0.0
vn.links.new(vtc.outputs["Object"], vsep.inputs[0]); vn.links.new(vsep.outputs["Y"], vmr.inputs["Value"]); vn.links.new(vmr.outputs["Result"], vcr.inputs["Fac"])
vn.links.new(vcr.outputs["Color"], vem.inputs["Color"]); vn.links.new(vv.outputs[0], vmx.inputs["Fac"])
vn.links.new(vtr.outputs[0], vmx.inputs[1]); vn.links.new(vem.outputs[0], vmx.inputs[2]); vn.links.new(vmx.outputs[0], vn.nodes["Material Output"].inputs["Surface"])
void.data.materials.append(vm)
void.visible_shadow = False
# fades for objects that can sit inside the void sphere at its fade-in (table 2) and fade-out (chair corner)
def fade_objects(objs, group):
    cache = {}
    for o in objs:
        if o.type not in ("MESH", "CURVE"): continue
        for slot in o.material_slots:
            m = slot.material
            if not m: continue
            if m.name not in cache:
                m2 = m.copy(); m2.name = m.name + "_" + group; add_fade(m2, group); cache[m.name] = m2
            slot.link = "OBJECT"; slot.material = cache[m.name]
fade_objects(TABLES["2"] + [cB, seam] + [o for o in bpy.data.objects if o.name.startswith(("IV_", "T1_"))], "T2")
fade_objects([chair, fl] + [o for o in bpy.data.objects if o.name.startswith(("MonCart", "Monitor", "Lamp2"))], "Corner")
print("FADES", {k: len(v) for k, v in FADES.items()})

# ------------------------------------------------------------------ people
with bpy.data.libraries.load(os.path.join(BU, "people.blend"), link=False) as (src, dst):
    dst.objects = [n for n in src.objects]
for o in dst.objects:
    if o: col.objects.link(o)
for nm in ("Surgeon", "Nurse"):
    rig = bpy.data.objects[nm]
    # surgical cap (squashed half sphere) and mask (curved plate) on the head bone; pale gloves = hands of the skin painted over by a glove shell
    pb = rig.pose.bones["head"]; hb = rig.data.bones["head"]
    hm = rig.matrix_world @ hb.matrix_local
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.105, segments=32, ring_count=16)
    cap = bpy.context.active_object; cap.name = nm + "_Cap"
    bm = bmesh.new(); bm.from_mesh(cap.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01], context="VERTS"); bm.to_mesh(cap.data); bm.free()
    cap.data.materials.append(M_cap); cap.modifiers.new("s", "SOLIDIFY").thickness = 0.004; bpy.ops.object.shade_smooth()
    body = bpy.data.objects[nm + ".body"]
    hgi = body.vertex_groups["head"].index
    bpy.context.view_layer.update(); be = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); bme = be.to_mesh()
    allv = [be.matrix_world @ v.co for v in bme.vertices]; be.to_mesh_clear()
    top = max(p.z for p in allv)
    hv = [p for p in allv if p.z > top - 0.26]
    cx = rig.matrix_world.translation.x; cy = sum(p.y for p in hv) / len(hv)
    nose = min((p for p in hv if abs(p.x - cx) < 0.015 and top - 0.17 < p.z < top - 0.09), key=lambda p: p.y)
    print("HEADTOP", nm, top, cx, cy, "nose", nose)
    cap.location = V(cx, nose.y + 0.122, top - 0.088); cap.scale = (1.02, 1.12, 1.05)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, segments=32, ring_count=16)
    mask = bpy.context.active_object; mask.name = nm + "_Mask"
    bm = bmesh.new(); bm.from_mesh(mask.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y > -0.045 or v.co.z > 0.03 or v.co.z < -0.07], context="VERTS"); bm.to_mesh(mask.data); bm.free()
    mask.data.materials.append(M_mask); mask.modifiers.new("s", "SOLIDIFY").thickness = 0.003; bpy.ops.object.shade_smooth()
    mask.location = V(cx, nose.y + 0.079, nose.z + 0.006); mask.scale = (0.82, 1.0, 0.95)
    for o in (cap, mask):
        M = o.matrix_world.copy(); o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "head"
        bpy.context.view_layer.update(); o.matrix_world = M
    # gloves: tint the skin material of the hands via a mask on the body's generated coords is fiddly - use the body's
    # vertex groups for the hands instead and give those faces a glove material
    body.data.materials.append(M_glove); gi = len(body.data.materials) - 1
    vg_ids = {g.index for g in body.vertex_groups if g.name.split(".")[0] in ("wrist", "metacarpal1", "metacarpal2", "metacarpal3", "metacarpal4")
              or g.name.startswith("finger")}
    hand_v = set()
    for v in body.data.vertices:
        if sum(g.weight for g in v.groups if g.group in vg_ids) > 0.5: hand_v.add(v.index)
    n_ = 0
    for p in body.data.polygons:
        if all(i in hand_v for i in p.vertices): p.material_index = gi; n_ += 1
    print("GLOVES", nm, n_, "faces")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
