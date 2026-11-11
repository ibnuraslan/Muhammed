"""Sets, props, lights, world, render settings.
blender -b people.blend --python 02_build_scene.py -- <assets_root> <out.blend>
assets_root holds ph/ (Poly Haven) and objv/ (Objaverse GLBs)."""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

argv = sys.argv[sys.argv.index("--") + 1:]
A, OUT = argv[0], argv[1]
PH, OB = os.path.join(A, "ph"), os.path.join(A, "objv")
exec(open(os.path.join(os.path.dirname(__file__), "lib.py")).read())
random.seed(5)
FPS, END = 60, 1710

# ------------------------------------------------------------------ render settings
sc.render.fps, sc.render.fps_base = FPS, 1.0
sc.frame_start, sc.frame_end = 1, END
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'; c.samples = 48; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
c.max_bounces = 8; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 8; c.transparent_max_bounces = 8
c.caustics_reflective = c.caustics_refractive = False
c.texture_limit_render = '2048'
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.use_persistent_data = True
sc.display_settings.display_device = 'sRGB'
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'; vs.exposure = 0.0; vs.gamma = 1.0
im = sc.render.image_settings; im.file_format = 'PNG'; im.color_mode = 'RGB'; im.color_depth = '8'; im.compression = 15
sc.render.filepath = "//render/SurgeonBrandsLivers_v001_"

PEOPLE = coll("People")
for o in list(sc.collection.objects):
    link(o, PEOPLE)
ORC, STU, HOME, HEAR, COR = coll("OR_Set"), coll("Studio_Set"), coll("Home_Set"), coll("Hearing_Set"), coll("Corridor_Set")

# ------------------------------------------------------------------ world: hospital HDRI, low (reflections only; rooms are closed)
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links; wn.clear()
env = wn.new('ShaderNodeTexEnvironment'); env.image = img(os.path.join(PH, "hdri/hospital_room_2_2k.hdr"))
bg = wn.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 0.3
wo = wn.new('ShaderNodeOutputWorld'); wl.new(env.outputs[0], bg.inputs[0]); wl.new(bg.outputs[0], wo.inputs[0])

# ------------------------------------------------------------------ materials
T = lambda n: os.path.join(PH, n)
M_ORFLOOR = pbr("OR_Floor", T("large_grey_tiles"), scale=2.0, tint=(0.85, 0.9, 0.92), rough_mul=0.6)
M_ORWALL = pbr("OR_Wall", T("long_white_tiles"), scale=1.6, tint=(0.78, 0.9, 0.88), rough_mul=0.5)
M_CEIL = pbr("Ceiling", T("white_plaster_02") if os.path.isdir(T("white_plaster_02/textures")) else T("beige_wall_001"), scale=2.0, tint=(0.95, 0.95, 0.95))
M_HFLOOR = pbr("Home_Floor", T("laminate_floor_02"), scale=2.5)
M_HWALL = pbr("Home_Wall", T("beige_wall_001"), scale=2.0, tint=(1.0, 0.93, 0.85))
M_PANEL = pbr("Hearing_Wall", T("dark_paneled_wood"), scale=2.2, tint=(0.9, 0.75, 0.6))
M_DESK = pbr("Desk_Wood", T("white_oak_veneer"), scale=1.0, tint=(0.55, 0.36, 0.22), rough_mul=0.7)
M_FABRIC = pbr("Fabric", T("fabric_pattern_07"), scale=0.3)
M_STEEL = mat("Steel", (0.75, 0.76, 0.78), 0.22, 1.0)
M_STEEL_D = mat("SteelDark", (0.35, 0.36, 0.38), 0.35, 1.0)
M_PLASTIC_W = mat("PlasticWhite", (0.85, 0.86, 0.86), 0.35)
M_PLASTIC_G = mat("PlasticGrey", (0.25, 0.27, 0.28), 0.45)
M_SCREEN = mat("ScreenBlack", (0.01, 0.012, 0.015), 0.15)
M_DRAPE = mat("Drape", (0.05, 0.20, 0.38), 0.85)
M_DRAPE.node_tree.nodes["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.5
M_SKIN = mat("Skin_Abdomen", (0.70, 0.50, 0.40), 0.45, sss=0.25)
M_INCISION = mat("Incision", (0.45, 0.08, 0.08), 0.35)
M_SUTURE = mat("Suture", (0.06, 0.05, 0.25), 0.4)
M_PAPER = mat("Paper", (0.92, 0.9, 0.84), 0.75)
M_GOLD = mat("Gold", (0.85, 0.62, 0.25), 0.3, 1.0)
M_RED_INK = mat("RedInk", (0.62, 0.03, 0.03), 0.6)

def fabric_override(ob, rgb):
    m = M_FABRIC.copy(); m.name = "Scrubs_" + ob.name
    tnode = m.node_tree.nodes; mx = tnode.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['Factor'].default_value = 1.0; mx.inputs['A'].default_value = (0.9, 0.9, 0.9, 1); mx.inputs['B'].default_value = (*rgb, 1)
    m.node_tree.links.new(mx.outputs['Result'], tnode["Principled BSDF"].inputs['Base Color'])
    tnode["Principled BSDF"].inputs['Sheen Weight'].default_value = 0.4
    ob.data.materials.clear(); ob.data.materials.append(m)

fabric_override(bpy.data.objects["Surgeon1.male_casualsuit01"], (0.10, 0.36, 0.36))
fabric_override(bpy.data.objects["Nurse.male_casualsuit01"], (0.16, 0.26, 0.42))
fabric_override(bpy.data.objects["Surgeon2.female_casualsuit01"], (0.17, 0.27, 0.55))
fabric_override(bpy.data.objects["Patient.female_casualsuit02"], (0.42, 0.24, 0.28))    # plain lounge set: the stock T-shirt print looked like a logo
# purple nitrile gloves on the studio hands
M_GLOVE = mat("Nitrile", (0.36, 0.32, 0.78), 0.32, sss=0.1, coat=0.3)
gb = bpy.data.objects["GloveHands.body"]; gb.data.materials.clear(); gb.data.materials.append(M_GLOVE)
for ch in bpy.data.objects["GloveHands"].children:
    if ch.type == 'MESH' and ch != gb:
        ch.hide_render = True; ch.hide_viewport = True
# keep forearms and hands only
vg_keep = gb.vertex_groups.new(name="keep_hands")
idx = {g.index: g.name for g in gb.vertex_groups}
want = lambda n: any(n.startswith(p) for p in ("lowerarm02", "wrist", "finger", "metacarpal"))
for v in gb.data.vertices:
    wsum = sum(g.weight for g in v.groups if want(idx.get(g.group, "")))
    if wsum > 0.4:
        vg_keep.add([v.index], 1.0, 'REPLACE')
mk = gb.modifiers.new("hands_only", 'MASK'); mk.vertex_group = "keep_hands"
bpy.context.view_layer.objects.active = gb
while gb.modifiers.find("hands_only") > 0:
    bpy.ops.object.modifier_move_up(modifier="hands_only")

# ------------------------------------------------------------------ OPERATING ROOM  x[-3.5,3.5] y[-3.5,3.5] h 3.0
OR = room("OR", -3.5, 3.5, -3.5, 3.5, 3.0, M_ORFLOOR, M_ORWALL, M_CEIL, ORC, holes=[("N", 1.6, 0.0, 1.7, 2.25)])
# ceiling light panels
for x, y in ((-1.8, -1.8), (1.8, -1.8), (-1.8, 1.8), (1.8, 1.8)):
    p = box("OR_CeilPanel", (1.0, 1.0, 0.02), (x, y, 2.985), emis("CeilPanel", (0.95, 0.97, 1.0), 6.0), ORC)
    L = bpy.data.lights.new("OR_CeilLight", 'AREA'); L.shape = 'SQUARE'; L.size = 1.0; L.energy = 110; L.color = (0.95, 0.98, 1.0)
    lo = bpy.data.objects.new("OR_CeilLight", L); ORC.objects.link(lo); lo.location = (x, y, 2.95)
# operating table + lamp model
# operating table (procedural): pedestal, base, padded top in three sections, side rails
box("ORTable_Base", (1.1, 0.55, 0.08), (0.2, 0, 0.04), M_STEEL_D, ORC, bevel=0.02)
box("ORTable_Column", (0.36, 0.28, 0.72), (0.2, 0, 0.44), M_PLASTIC_W, ORC, bevel=0.03)
box("ORTable_Frame", (2.0, 0.5, 0.06), (0.2, 0, 0.86), M_STEEL, ORC, bevel=0.01)
M_PAD = mat("TablePad", (0.08, 0.09, 0.1), 0.45)
for x0, ln in ((-0.85, 0.5), (-0.33, 0.62), (0.32, 0.68), (0.88, 0.4)):
    box("ORTable_Pad", (ln - 0.02, 0.52, 0.07), (x0 + 0.05, 0, 0.91), M_PAD, ORC, bevel=0.025)
for y in (-0.27, 0.27):
    box("ORTable_Rail", (1.9, 0.015, 0.03), (0.2, y, 0.86), M_STEEL, ORC, bevel=0.004)
# twin surgical lamps on ceiling arms; spotlights aimed at the abdomen window
LAMPS = []
M_LAMPSHELL = mat("LampShell", (0.88, 0.9, 0.9), 0.3)
M_LED = emis("LampLED", (1.0, 0.98, 0.95), 25.0)
for k, (hx, hy, hz) in enumerate(((-0.55, -0.55, 2.02), (0.35, 0.55, 2.08))):
    tgt = Vector((-0.28, -0.06, 1.15))
    root = bpy.data.objects.new("SurgLamp_%d" % k, None); ORC.objects.link(root); root.location = (hx, hy, hz)
    root.rotation_euler = (tgt - Vector((hx, hy, hz))).to_track_quat('-Z', 'Y').to_euler()
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=16, radius=0.36)
    for v in list(bm.verts):
        if v.co.z < -0.02: bm.verts.remove(v)
    for v in bm.verts: v.co.z *= 0.42
    me = bpy.data.meshes.new("LampDish"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    dish = bpy.data.objects.new("SurgLampDish_%d" % k, me); ORC.objects.link(dish); dish.parent = root; me.materials.append(M_LAMPSHELL)
    dish.modifiers.new("t", 'SOLIDIFY').thickness = 0.02
    for i in range(7):
        a_ = i * 2 * math.pi / 6
        pos = (0, 0, 0.0) if i == 6 else (0.18 * math.cos(a_), 0.18 * math.sin(a_), 0.0)
        led = cyl("SurgLampLED", 0.06, 0.012, pos, M_LED, ORC, verts=20); led.parent = root
    hnd = cyl("SurgLampHandle", 0.02, 0.12, (0, 0, -0.05), M_PLASTIC_G, ORC, verts=12); hnd.parent = root
    # arm up to the ceiling mount
    cu = bpy.data.curves.new("LampArm", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.03
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(hx, hy, hz + 0.16), (hx * 0.4, hy * 0.4, hz + 0.55), (0.0, 0.0, 2.99)]):
        bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    ao = bpy.data.objects.new("SurgLampArm_%d" % k, cu); ORC.objects.link(ao); cu.materials.append(M_LAMPSHELL)
    sp_ = bpy.data.lights.new("SurgLampSpot_%d" % k, 'SPOT'); sp_.energy = 260; sp_.spot_size = math.radians(38); sp_.spot_blend = 0.6
    sp_.shadow_soft_size = 0.25; sp_.color = (1.0, 0.98, 0.95)
    so_ = bpy.data.objects.new("SurgLampSpot_%d" % k, sp_); ORC.objects.link(so_); so_.parent = root; so_.location = (0, 0, -0.03)
    LAMPS.append(root)
cyl("LampMount", 0.12, 0.08, (0, 0, 2.96), M_LAMPSHELL, ORC)

# ------------------------------------------------------------------ studio dome under the OR (explainer look)
SZ = -6.0
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=4.5)
me = bpy.data.meshes.new("StudioDome"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
dome = bpy.data.objects.new("StudioDome", me); STU.objects.link(dome); dome.location = (0, 0, SZ)
md = bpy.data.materials.new("StudioGradient"); md.use_nodes = True
n, l = md.node_tree.nodes, md.node_tree.links; n.clear()
o_ = n.new('ShaderNodeOutputMaterial'); tc = n.new('ShaderNodeTexCoord'); sep = n.new('ShaderNodeSeparateXYZ')
mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -3.0; mr.inputs['From Max'].default_value = 3.5
ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (0.02, 0.38, 0.62, 1); ramp.color_ramp.elements[1].color = (0.96, 0.99, 1.0, 1)
ramp.color_ramp.elements.new(0.45).color = (0.15, 0.68, 0.85, 1)
em = n.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
l.new(tc.outputs['Object'], sep.inputs[0]); l.new(sep.outputs['Z'], mr.inputs['Value']); l.new(mr.outputs[0], ramp.inputs[0])
l.new(ramp.outputs[0], em.inputs[0]); l.new(em.outputs[0], o_.inputs[0])
me.materials.append(md)
LIVER_POS = Vector((0.0, 0.0, SZ + 0.4))
def studio_light(name, loc, energy, size, col=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.size = size; L.energy = energy; L.color = col
    lo = bpy.data.objects.new(name, L); STU.objects.link(lo); lo.location = loc
    lo.rotation_euler = (LIVER_POS - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return lo
studio_light("Studio_Key", LIVER_POS + Vector((-1.2, -1.4, 1.5)), 160, 1.2, (1.0, 0.97, 0.92))
studio_light("Studio_Rim", LIVER_POS + Vector((1.4, 1.2, 0.9)), 220, 0.8, (0.8, 0.93, 1.0))
studio_light("Studio_Fill", LIVER_POS + Vector((1.5, -1.6, -0.6)), 50, 1.5, (0.85, 0.95, 1.0))
# the donor liver
liver = import_glb(os.path.join(OB, "liver.glb"), "Liver", length=0.26, loc=LIVER_POS - Vector((0, 0, 0.084)), rot_z=math.radians(180), c_=STU)
lm = liver.data.materials[0]; lp = lm.node_tree.nodes.get("Principled BSDF")
if lp:
    for lk in list(lp.inputs['Base Color'].links):
        mx = lm.node_tree.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (0.48, 0.15, 0.11, 1); lm.node_tree.links.new(lk.from_socket, mx.inputs['A']); lm.node_tree.links.new(mx.outputs['Result'], lp.inputs['Base Color'])
    lp.inputs['Roughness'].default_value = 0.32; lp.inputs['Coat Weight'].default_value = 0.7; lp.inputs['Coat Roughness'].default_value = 0.08
    lp.inputs['Subsurface Weight'].default_value = 0.12; lp.inputs['Subsurface Radius'].default_value = (0.01, 0.003, 0.002)
print("LIVER mats", [m.name for m in liver.data.materials], tuple(round(d, 3) for d in liver.dimensions))

# ------------------------------------------------------------------ CORRIDOR beyond the OR doors  x[0,3.2] y[3.6,7.0]
CR = room("COR", -0.2, 3.4, 3.6, 7.2, 2.8, M_ORFLOOR, M_HWALL, M_CEIL, COR)
bpy.data.objects.remove(CR['S'], do_unlink=True)
for y in (4.6, 6.2):
    box("COR_Panel", (0.6, 1.2, 0.02), (1.6, y, 2.79), emis("CorPanel", (1, 0.98, 0.95), 5.0), COR)
    L = bpy.data.lights.new("COR_Light", 'AREA'); L.size = 0.8; L.energy = 160
    lo = bpy.data.objects.new("COR_Light", L); COR.objects.link(lo); lo.location = (1.6, y, 2.75)
# swing doors (hinged at the jambs, open into the OR)
for side, hx in (("L", 0.75), ("R", 2.45)):
    h = bpy.data.objects.new("DoorHinge_" + side, None); ORC.objects.link(h); h.location = (hx, 3.55, 0)
    d = box("Door_" + side, (0.84, 0.05, 2.2), (0.42 if side == "L" else -0.42, 0, 1.11), M_PLASTIC_W, ORC, bevel=0.01)
    d.parent = h
    win = box("DoorWin_" + side, (0.3, 0.06, 0.4), (0.42 if side == "L" else -0.42, 0, 1.6), mat("DoorGlass", (0.6, 0.7, 0.75), 0.05, trans=0.9), ORC)
    win.parent = h
    kick = box("DoorKick_" + side, (0.84, 0.06, 0.25), (0.42 if side == "L" else -0.42, 0, 0.14), M_STEEL, ORC); kick.parent = h

# ------------------------------------------------------------------ HOME  x[3.8,9.8] y[-3,3] h 2.7
HM = room("HOME", 3.8, 9.8, -3.0, 3.0, 2.7, M_HFLOOR, M_HWALL, M_CEIL, HOME, holes=[("S", 7.0, 0.85, 1.9, 1.45)])
sky = box("HOME_Outside", (6.0, 0.05, 4.0), (7.0, -4.2, 1.6), emis("Outside", (0.85, 0.92, 1.0), 3.0), HOME)
for x in (5.6, 8.6):
    box("HOME_Tree", (0.8, 0.3, 3.0), (x, -5.0, 1.2), emis("TreeSil", (0.25, 0.4, 0.25), 1.2), HOME)
sun = bpy.data.lights.new("HOME_Sun", 'SUN'); sun.energy = 4.0; sun.angle = 0.05; sun.color = (1.0, 0.92, 0.8)
so = bpy.data.objects.new("HOME_Sun", sun); HOME.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(20))
L = bpy.data.lights.new("HOME_WindowFill", 'AREA'); L.size = 1.8; L.energy = 300; L.color = (0.85, 0.92, 1.0)
lo = bpy.data.objects.new("HOME_WindowFill", L); HOME.objects.link(lo); lo.location = (7.0, -2.85, 1.6); lo.rotation_euler = (math.radians(-90), 0, 0)
L = bpy.data.lights.new("HOME_Ceil", 'AREA'); L.size = 2.0; L.energy = 120; L.color = (1.0, 0.9, 0.78)
lo = bpy.data.objects.new("HOME_Ceil", L); HOME.objects.link(lo); lo.location = (6.8, 0.2, 2.65)
sofa = import_glb(os.path.join(OB, "sofa.glb"), "Sofa", length=2.0, loc=(7.2, 2.25, 0), rot_z=math.radians(180), c_=HOME)
ct = append_ph(os.path.join(PH, "coffee_table_round_01/coffee_table_round_01_1k.blend"), HOME, loc=(7.2, 0.9, 0))
tv = append_ph(os.path.join(PH, "Television_01/Television_01_1k.blend"), HOME, loc=(9.45, 0.4, 0.55), rot_z=math.radians(90))
box("HOME_TVStand", (0.5, 1.6, 0.55), (9.5, 0.4, 0.275), M_DESK, HOME, bevel=0.01)
pl = append_ph(os.path.join(PH, "potted_plant_04/potted_plant_04_1k.blend"), HOME, loc=(9.3, 2.5, 0))
ac = append_ph(os.path.join(PH, "ArmChair_01/ArmChair_01_1k.blend"), HOME, loc=(5.0, 1.9, 0), rot_z=math.radians(200))
# floor lamp
cyl("HOME_LampPole", 0.015, 1.5, (9.2, -2.2, 0.75), M_STEEL_D, HOME)
cyl("HOME_LampBase", 0.15, 0.03, (9.2, -2.2, 0.015), M_STEEL_D, HOME)
cyl("HOME_LampShade", 0.2, 0.3, (9.2, -2.2, 1.55), emis("LampShade", (1.0, 0.8, 0.55), 4.0), HOME)
pt_ = bpy.data.lights.new("HOME_LampLight", 'POINT'); pt_.energy = 60; pt_.color = (1.0, 0.75, 0.5); pt_.shadow_soft_size = 0.15
lo = bpy.data.objects.new("HOME_LampLight", pt_); HOME.objects.link(lo); lo.location = (9.2, -2.2, 1.5)
# rug, picture frames (abstract, no text), curtains, shelves with books (plain spines)
rug = box("HOME_Rug", (2.6, 1.8, 0.01), (7.2, 0.9, 0.005), M_FABRIC.copy(), HOME)
rug.data.materials[0].node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.5, 0.3, 0.25, 1)
for y, col in ((-1.2, (0.7, 0.45, 0.3)), (0.9, (0.3, 0.45, 0.55))):
    box("HOME_Frame", (0.04, 0.8, 0.6), (3.84, y, 1.6), M_DESK, HOME)
    box("HOME_Art", (0.01, 0.7, 0.5), (3.87, y, 1.6), mat("Art", col, 0.8), HOME)
CURT = []
for x in (5.75, 8.25):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=24, y_segments=8, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.7, 0.04 * math.sin(v.co.x * 28), (v.co.y + 0.5) * 2.4))
    me = bpy.data.meshes.new("Curtain"); bm.to_mesh(me); bm.free()
    cu = bpy.data.objects.new("HOME_Curtain", me); HOME.objects.link(cu); cu.location = (x, -2.9, 0.1)
    cm = mat("Curtain", (0.85, 0.82, 0.75), 0.8); cm.node_tree.nodes["Principled BSDF"].inputs['Transmission Weight'].default_value = 0.3
    me.materials.append(cm)
    for p in me.polygons: p.use_smooth = True
    CURT.append(cu)
mug = cyl("Mug", 0.04, 0.095, (0, 0, 0), mat("MugCeramic", (0.75, 0.25, 0.18), 0.25, coat=0.6), HOME)
mug.data.transform(Matrix.Translation((0, 0, 0.0475)))
handle = bpy.data.objects.new("MugHandle", None)
coffee = cyl("MugCoffee", 0.036, 0.004, (0, 0, 0.085), mat("Coffee", (0.12, 0.06, 0.03), 0.1), HOME); coffee.parent = mug

# ------------------------------------------------------------------ HEARING ROOM  x[-12,-3.8] y[-3.5,3.5] h 3.2
HR = room("HEAR", -12.0, -3.8, -3.5, 3.5, 3.2, M_HFLOOR, M_PANEL, M_CEIL, HEAR, holes=[("S", -8.0, 1.0, 1.4, 1.8), ("S", -5.6, 1.0, 1.0, 1.8)])
box("HEAR_Outside", (8.0, 0.05, 4.0), (-7.0, -4.4, 1.8), emis("Outside2", (0.9, 0.93, 1.0), 1.2), HEAR)
hs = bpy.data.lights.new("HEAR_Sun", 'SUN'); hs.energy = 3.5; hs.angle = 0.03; hs.color = (1.0, 0.88, 0.7)
ho = bpy.data.objects.new("HEAR_Sun", hs); HEAR.objects.link(ho); ho.rotation_euler = (math.radians(50), 0, math.radians(-25))
for x in (-10.0, -7.0, -5.0):
    L = bpy.data.lights.new("HEAR_Ceil", 'AREA'); L.size = 1.2; L.energy = 140; L.color = (1.0, 0.88, 0.72)
    lo = bpy.data.objects.new("HEAR_Ceil", L); HEAR.objects.link(lo); lo.location = (x, 0, 3.15)
    box("HEAR_Fixture", (0.7, 0.7, 0.03), (x, 0, 3.18), emis("Fixture", (1, 0.9, 0.75), 4.0), HEAR)
DAIS_H = 0.4
box("HEAR_Dais", (2.6, 6.4, DAIS_H), (-10.7, 0, DAIS_H / 2), M_DESK, HEAR, bevel=0.01)
box("HEAR_DeskTop", (0.9, 5.2, 0.05), (-10.0, 0, DAIS_H + 0.76), M_DESK, HEAR, bevel=0.005)
box("HEAR_DeskFront", (0.05, 5.2, 0.76 + DAIS_H), (-9.53, 0, (0.76 + DAIS_H) / 2), M_DESK, HEAR, bevel=0.005)
box("HEAR_Lectern", (0.5, 0.6, 1.1), (-7.15, 0, 0.55), M_DESK, HEAR, bevel=0.01)
box("HEAR_LecternTop", (0.6, 0.7, 0.04), (-7.1, 0, 1.12), M_DESK, HEAR, bevel=0.005, rot=(0, math.radians(-12), 0))
for y in (-1.2, 0.0, 1.2):
    box("HEAR_ChairSeat", (0.5, 0.5, 0.08), (-10.65, y, DAIS_H + 0.46), mat("Leather", (0.12, 0.07, 0.05), 0.4), HEAR, bevel=0.02)
    box("HEAR_ChairBack", (0.08, 0.5, 0.75), (-10.95, y, DAIS_H + 0.85), mat("Leather", (0.12, 0.07, 0.05), 0.4), HEAR, bevel=0.02)
    if y > -1.0:
        box("HEAR_Folder", (0.3, 0.22, 0.012), (-9.85, y + 0.42, DAIS_H + 0.79), mat("Folder", (0.2, 0.25, 0.35), 0.6), HEAR)
    cyl("HEAR_Glass", 0.035, 0.11, (-9.75, y - 0.3, DAIS_H + 0.84), mat("Glass", (0.9, 0.95, 1.0), 0.02, trans=1.0), HEAR)
# gavel + sound block, certificate, stamp
gav = import_glb(os.path.join(OB, "gavel.glb"), "Gavel_src", c_=HEAR, join=False)
for o in gav:
    print("GAVEL part", o.name, [m.name for m in o.data.materials], tuple(round(d, 3) for d in o.dimensions))
cert = box("Certificate", (0.30, 0.22, 0.003), (-9.8, -0.75, DAIS_H + 0.79), M_PAPER, HEAR)
for i in range(6):
    box("CertLine", (0.012 if i else 0.02, 0.15 - 0.02 * (i % 2), 0.001), (-9.8 + 0.07 - i * 0.022, -0.75 + 0.01, DAIS_H + 0.7925), mat("Ink", (0.2, 0.2, 0.22), 0.6), HEAR)
cyl("CertSeal", 0.025, 0.002, (-9.8 - 0.07, -0.75 - 0.07, DAIS_H + 0.7925), M_GOLD, HEAR)
box("CertBorder", (0.29, 0.21, 0.0005), (-9.8, -0.75, DAIS_H + 0.7918), mat("Border", (0.3, 0.35, 0.5), 0.6), HEAR)
stamp_mark = bpy.data.objects.new("StampMark", None); HEAR.objects.link(stamp_mark); stamp_mark.location = (-9.8, -0.75, DAIS_H + 0.7935); stamp_mark.rotation_euler = (0, 0, math.radians(35))
for nm, sz, lc in (("a", (0.13, 0.008, 0.001), (0, 0.03, 0)), ("b", (0.13, 0.008, 0.001), (0, -0.03, 0)), ("c", (0.008, 0.068, 0.001), (0.061, 0, 0)), ("d", (0.008, 0.068, 0.001), (-0.061, 0, 0)), ("e", (0.11, 0.014, 0.001), (0, 0, 0))):
    box("StampMark_" + nm, sz, lc, M_RED_INK, HEAR).parent = stamp_mark
stamp = bpy.data.objects.new("Stamp", None); HEAR.objects.link(stamp); stamp.location = (-9.85, -1.05, DAIS_H + 0.785)
sb = box("StampBase", (0.07, 0.09, 0.025), (0, 0, 0.0125), mat("StampRubber", (0.4, 0.05, 0.05), 0.6), HEAR); sb.parent = stamp
sh = cyl("StampHandle", 0.017, 0.08, (0, 0, 0.065), mat("StampWood", (0.25, 0.14, 0.08), 0.5), HEAR); sh.parent = stamp
sk = bpy.data.objects.new("StampKnob", None)
cyl("StampTop", 0.026, 0.025, (0, 0, 0.115), mat("StampWood", (0.25, 0.14, 0.08), 0.5), HEAR).parent = stamp
# wall clock (ticks only), bookshelves with plain spines
cyl("HEAR_Clock", 0.22, 0.04, (-11.97, 0, 2.5), M_PAPER, HEAR, rot=(0, math.radians(90), 0))
for i in range(12):
    a = i * math.pi / 6
    box("ClockTick", (0.01, 0.012, 0.04), (-11.94, 0.18 * math.sin(a), 2.5 + 0.18 * math.cos(a)), M_PLASTIC_G, HEAR, rot=(-a, 0, 0))
for y0 in (-3.0, 2.2):
    box("HEAR_Shelf", (0.35, 0.8, 2.0), (-11.8, y0 + 0.4, 1.0), M_DESK, HEAR)
    for k in range(4):
        for j in range(9):
            col = random.choice([(0.35, 0.1, 0.08), (0.12, 0.2, 0.3), (0.2, 0.25, 0.15), (0.5, 0.42, 0.3)])
            box("Book", (0.25, 0.06, 0.28 + random.random() * 0.06), (-11.65, y0 + 0.07 + j * 0.075, 0.35 + k * 0.45 + 0.15), mat("Book", col, 0.6), HEAR)
# audience chairs along the side
for x in (-8.6, -7.8, -6.0, -5.2):
    for y in (2.6, -2.6):
        box("HEAR_Seat", (0.45, 0.45, 0.05), (x, y, 0.45), mat("SeatFabric", (0.22, 0.12, 0.1), 0.8), HEAR, bevel=0.01)
        box("HEAR_SeatBack", (0.45, 0.05, 0.45), (x, y + (0.22 if y > 0 else -0.22), 0.7), mat("SeatFabric", (0.22, 0.12, 0.1), 0.8), HEAR, bevel=0.01)
        for dx in (-0.2, 0.2):
            for dy in (-0.2, 0.2):
                cyl("HEAR_SeatLeg", 0.012, 0.45, (x + dx, y + dy, 0.225), M_STEEL_D, HEAR, verts=8)
# anatomy overlay wall behind the surgeon (east wall of the hearing room)
M_XRAY = bpy.data.materials.new("XRayLiver"); M_XRAY.use_nodes = True
n, l = M_XRAY.node_tree.nodes, M_XRAY.node_tree.links; n.clear()
out_ = n.new('ShaderNodeOutputMaterial'); lw = n.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
em = n.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (0.35, 0.85, 1.0, 1)
gain = n.new('ShaderNodeMath'); gain.operation = 'MULTIPLY'; gain.inputs[1].default_value = 6.0; gain.name = "XRayGain"
tr = n.new('ShaderNodeBsdfTransparent'); mix = n.new('ShaderNodeMixShader')
l.new(lw.outputs['Facing'], gain.inputs[0]); l.new(gain.outputs[0], em.inputs['Strength'])
l.new(lw.outputs['Facing'], mix.inputs['Fac']); l.new(tr.outputs[0], mix.inputs[1]); l.new(em.outputs[0], mix.inputs[2]); l.new(mix.outputs[0], out_.inputs[0])
GHOSTS = []
for i, y in enumerate((-2.2, -1.1, 0.0, 1.1, 2.2)):
    g = bpy.data.objects.new("GhostLiver_%d" % i, liver.data); HEAR.objects.link(g)
    g.data = liver.data.copy(); g.data.materials.clear(); g.data.materials.append(M_XRAY.copy())
    g.location = (-4.3, y, 1.7 + 0.12 * math.sin(i * 1.7)); g.scale = (3.4, 3.4, 3.4); g.rotation_euler = (0, 0, math.radians(-90))
    GHOSTS.append(g)
glow = box("AnatomyLightbox", (0.03, 6.2, 2.0), (-3.86, 0, 1.75), emis("Lightbox", (0.04, 0.14, 0.22), 1.6), HEAR)

# ------------------------------------------------------------------ OR props: drape over the patient, abdomen window, trolley, monitors, IV, ether screen
TABLE_TOP = 0.95
WIN = Vector((-0.28, -0.06))     # abdomen window centre (xy); patient's head at -X, right side at -Y
WIN_HALF = Vector((0.15, 0.11))
def body_h(x, y):
    """drape surface height above the table top: torso bump + sloping sides"""
    u = (x + 0.15) / 0.75; v = y / 0.36
    torso = 0.21 * max(0.0, 1 - u * u) ** 0.5 * max(0.0, 1 - v ** 4) if abs(u) < 1 else 0.0
    legs = 0.14 * max(0.0, 1 - (y / 0.3) ** 2) if 0.4 < x < 1.15 else 0.0
    return max(torso, legs)
bm = bmesh.new(); NX, NY = 120, 70
X0, X1, Y0, Y1 = -0.72, 1.25, -0.75, 0.75
verts = {}
for i in range(NX + 1):
    for j in range(NY + 1):
        x = X0 + (X1 - X0) * i / NX; y = Y0 + (Y1 - Y0) * j / NY
        if abs(y) <= 0.42:
            z = TABLE_TOP + 0.02 + body_h(x, y)
        else:
            z = TABLE_TOP + 0.02 + body_h(x, math.copysign(0.42, y)) - (abs(y) - 0.42) * 0.9
        z += 0.006 * noise.noise(Vector((x * 9, y * 9, 0.3)))
        verts[i, j] = bm.verts.new((x, y, z))
for i in range(NX):
    for j in range(NY):
        cx = X0 + (X1 - X0) * (i + 0.5) / NX; cy = Y0 + (Y1 - Y0) * (j + 0.5) / NY
        if abs(cx - WIN.x) < WIN_HALF.x and abs(cy - WIN.y) < WIN_HALF.y:
            continue
        bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
me = bpy.data.meshes.new("Drape"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
drape = bpy.data.objects.new("Drape", me); ORC.objects.link(drape); me.materials.append(M_DRAPE)
sol = drape.modifiers.new("thick", 'SOLIDIFY'); sol.thickness = 0.006
# abdomen skin patch under the window (slightly below the drape)
bm = bmesh.new(); N2 = 40
vv = {}
for i in range(N2 + 1):
    for j in range(N2 + 1):
        x = WIN.x + WIN_HALF.x * 1.25 * (2 * i / N2 - 1); y = WIN.y + WIN_HALF.y * 1.25 * (2 * j / N2 - 1)
        vv[i, j] = bm.verts.new((x, y, TABLE_TOP + 0.012 + body_h(x, y)))
for i in range(N2):
    for j in range(N2):
        bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
me = bpy.data.meshes.new("AbdomenSkin"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
skin = bpy.data.objects.new("AbdomenSkin", me); ORC.objects.link(skin); me.materials.append(M_SKIN)
# incision: a neat line along X in the window
INC0, INC1 = Vector((WIN.x - 0.11, WIN.y + 0.01)), Vector((WIN.x + 0.11, WIN.y - 0.01))
def surf(xy, dz=0.0):
    return Vector((xy.x, xy.y, TABLE_TOP + 0.012 + body_h(xy.x, xy.y) + dz))
bm = bmesh.new(); NS = 30
prev = None
for k in range(NS + 1):
    t = k / NS; p = INC0.lerp(INC1, t)
    w_ = 0.0035 * math.sin(math.pi * t) ** 0.5 + 0.0005
    a = bm.verts.new(surf(p + Vector((0, w_)), 0.0007)); b = bm.verts.new(surf(p - Vector((0, w_)), 0.0007))
    if prev:
        bm.faces.new((prev[0], prev[1], b, a))
    prev = (a, b)
me = bpy.data.meshes.new("Incision"); bm.to_mesh(me); bm.free()
inc = bpy.data.objects.new("Incision", me); ORC.objects.link(inc); me.materials.append(M_INCISION)
# sutures: small arcs across the incision, revealed one by one in 03
SUTURES = []
for k in range(9):
    t = (k + 0.5) / 9; p = INC0.lerp(INC1, t)
    cu = bpy.data.curves.new("Suture_%d" % k, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0006; cu.bevel_resolution = 2
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    pts = [surf(p + Vector((0.0015, 0.008)), 0.0004), surf(p, 0.0035), surf(p + Vector((-0.0015, -0.008)), 0.0004)]
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    so_ = bpy.data.objects.new("Suture_%d" % k, cu); ORC.objects.link(so_); cu.materials.append(M_SUTURE)
    SUTURES.append(so_)
# ether screen at the head end
for y in (-0.5, 0.5):
    cyl("EtherPost", 0.012, 0.75, (-0.72, y, TABLE_TOP + 0.375), M_STEEL, ORC, verts=12)
cyl("EtherBar", 0.012, 1.0, (-0.72, 0, TABLE_TOP + 0.75), M_STEEL, ORC, verts=12, rot=(math.radians(90), 0, 0))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=20, size=0.5)
for v in bm.verts:
    v.co = Vector((-0.72 + 0.03 * math.sin(v.co.y * 20), v.co.y * 1.0, TABLE_TOP + 0.75 - (v.co.x + 0.5) * 0.4))
me = bpy.data.meshes.new("EtherDrape"); bm.to_mesh(me); bm.free()
ed = bpy.data.objects.new("EtherDrape", me); ORC.objects.link(ed); me.materials.append(M_DRAPE)
ed.modifiers.new("t", 'SOLIDIFY').thickness = 0.004
# Mayo instrument tray beside surgeon 1, with instruments
cyl("Mayo_Post", 0.02, 1.0, (0.32, -0.98, 0.5), M_STEEL, ORC, verts=12)
box("Mayo_Tray", (0.48, 0.34, 0.02), (0.32, -0.98, 1.01), M_STEEL, ORC, bevel=0.004)
box("Mayo_Towel", (0.44, 0.3, 0.004), (0.32, -0.98, 1.022), M_DRAPE, ORC)
for i in range(7):
    box("Instrument", (0.16, 0.008, 0.004), (0.30 + 0.02 * (i % 2), -1.12 + i * 0.03, 1.027), M_STEEL, ORC, rot=(0, 0, random.uniform(-0.1, 0.1)))
# argon pen (held by surgeon 1 / the studio glove hand), needle driver
def pen(name, c_):
    root = bpy.data.objects.new(name, None); c_.objects.link(root)
    b = cyl(name + "_Body", 0.0065, 0.15, (0, 0, 0.075), M_PLASTIC_W, c_, verts=16); b.parent = root
    g = cyl(name + "_Grip", 0.0072, 0.05, (0, 0, 0.04), M_PLASTIC_G, c_, verts=16); g.parent = root
    t = cyl(name + "_Tip", 0.0018, 0.035, (0, 0, -0.012), M_STEEL, c_, verts=10); t.parent = root
    btn = box(name + "_Btn", (0.004, 0.006, 0.012), (0, -0.0068, 0.07), mat("PenBtn", (0.1, 0.4, 0.75), 0.4), c_); btn.parent = root
    cab = bpy.data.curves.new(name + "_Cable", 'CURVE'); cab.dimensions = '3D'; cab.bevel_depth = 0.002
    sp = cab.splines.new('BEZIER'); sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(0, 0, 0.15), (0.05, 0.02, 0.32), (0.2, 0.1, 0.5)]):
        bp.co = co; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    co_ = bpy.data.objects.new(name + "_Cable", cab); c_.objects.link(co_); cab.materials.append(M_PLASTIC_G); co_.parent = root
    return root
pen("ArgonPen_OR", ORC); pen("ArgonPen_Studio", STU)
nd = bpy.data.objects.new("NeedleDriver", None); ORC.objects.link(nd)
for sx in (-1, 1):
    j = box("ND_Jaw", (0.004, 0.003, 0.11), (sx * 0.002, 0, 0.055), M_STEEL, ORC, rot=(0, math.radians(sx * 2), 0)); j.parent = nd
    r_ = cyl("ND_Ring", 0.011, 0.003, (sx * 0.012, 0, 0.125), M_STEEL, ORC, verts=16, rot=(math.radians(90), 0, 0)); r_.parent = nd
cu = bpy.data.curves.new("ND_Needle", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0005
sp = cu.splines.new('POLY'); sp.points.add(11)
for k, p in enumerate(sp.points):
    a = math.pi * k / 11; p.co = (0.008 * math.cos(a), 0, -0.004 - 0.008 * math.sin(a), 1)
nn = bpy.data.objects.new("ND_Needle", cu); ORC.objects.link(nn); cu.materials.append(M_STEEL); nn.parent = nd
# monitors on a boom (waveform lines, no text)
def monitor(name, loc, rot_z, c_):
    root = bpy.data.objects.new(name, None); c_.objects.link(root); root.location = loc; root.rotation_euler = (0, 0, rot_z)
    b = box(name + "_Case", (0.56, 0.06, 0.38), (0, 0.03, 0), M_PLASTIC_G, c_, bevel=0.01); b.parent = root
    s_ = box(name + "_Screen", (0.5, 0.005, 0.32), (0, -0.002, 0), M_SCREEN, c_); s_.parent = root
    lines = []
    for k, (col, z) in enumerate((((0.2, 1.0, 0.35), 0.09), ((1.0, 0.85, 0.2), 0.0), ((0.3, 0.75, 1.0), -0.09))):
        cu = bpy.data.curves.new(name + "_Wave%d" % k, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0018
        sp = cu.splines.new('POLY'); NP = 160; sp.points.add(NP - 1)
        for i, p in enumerate(sp.points):
            x = -0.23 + 0.46 * i / (NP - 1); ph = (i / (NP - 1) * 4.0) % 1.0
            if k == 0:
                yv = 0.05 if 0.30 < ph < 0.33 else (-0.02 if 0.33 <= ph < 0.36 else 0.008 * math.sin(ph * 6.28))
            elif k == 1:
                yv = 0.025 * math.sin(ph * 6.28) ** 3
            else:
                yv = 0.02 * math.sin(i / (NP - 1) * 12.0)
            p.co = (x, -0.006, z + yv, 1)
        wo_ = bpy.data.objects.new(name + "_Wave%d" % k, cu); c_.objects.link(wo_); wo_.parent = root
        mm = bpy.data.materials.new("Wave"); mm.use_nodes = True
        nn_, ll = mm.node_tree.nodes, mm.node_tree.links; nn_.clear()
        o2 = nn_.new('ShaderNodeOutputMaterial'); e2 = nn_.new('ShaderNodeEmission'); e2.inputs['Color'].default_value = (*col, 1)
        tc2 = nn_.new('ShaderNodeTexCoord'); sx_ = nn_.new('ShaderNodeSeparateXYZ'); mp2 = nn_.new('ShaderNodeMapping'); mp2.name = "Sweep"
        fr = nn_.new('ShaderNodeMath'); fr.operation = 'FRACT'
        pw = nn_.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3.0
        st_ = nn_.new('ShaderNodeMath'); st_.operation = 'MULTIPLY'; st_.inputs[1].default_value = 7.0
        ll.new(tc2.outputs['Object'], mp2.inputs['Vector']); ll.new(mp2.outputs['Vector'], sx_.inputs[0]); ll.new(sx_.outputs['X'], fr.inputs[0])
        ll.new(fr.outputs[0], pw.inputs[0]); ll.new(pw.outputs[0], st_.inputs[0]); ll.new(st_.outputs[0], e2.inputs['Strength']); ll.new(e2.outputs[0], o2.inputs[0])
        mp2.inputs['Scale'].default_value = (2.0, 1, 1)
        mp2.inputs['Location'].default_value = (0, 0, 0); mp2.inputs['Location'].keyframe_insert("default_value", frame=1)
        mp2.inputs['Location'].default_value = (-END / 60.0 * 1.4, 0, 0); mp2.inputs['Location'].keyframe_insert("default_value", frame=END)
        for fc in mm.node_tree.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        cu.materials.append(mm); lines.append(wo_)
    return root
monitor("Monitor_A", (-1.15, 1.05, 1.75), math.radians(200), ORC)
cyl("MonitorBoom", 0.025, 1.3, (-1.15, 1.1, 2.35), M_STEEL, ORC, verts=12)
box("AnesthesiaCart", (0.6, 0.55, 1.15), (-1.55, 0.95, 0.575), M_PLASTIC_W, ORC, bevel=0.02)
monitor("Monitor_B", (-1.55, 0.92, 1.4), math.radians(170), ORC)
# IV pole + bag
cyl("IV_Pole", 0.012, 2.0, (-0.95, -0.75, 1.0), M_STEEL, ORC, verts=12)
cyl("IV_Base", 0.25, 0.03, (-0.95, -0.75, 0.06), M_STEEL_D, ORC, verts=5)
ivb = box("IV_Bag", (0.12, 0.04, 0.2), (-0.95, -0.75, 1.82), mat("IVBag", (0.9, 0.95, 1.0), 0.1, trans=0.8), ORC, bevel=0.015)
# back table with drapes, kick bucket, wall cabinets
box("BackTable", (1.4, 0.7, 0.9), (1.9, -2.6, 0.45), M_STEEL, ORC, bevel=0.01)
box("BackTable_Drape", (1.45, 0.75, 0.01), (1.9, -2.6, 0.905), M_DRAPE, ORC)
for i in range(5):
    box("BackTable_Pack", (0.25, 0.18, 0.06), (1.4 + i * 0.25, -2.55, 0.94), mat("Pack", (0.85, 0.85, 0.8), 0.6), ORC)
for x in (-2.6, -1.4, 0.0):
    box("WallCabinet", (1.1, 0.4, 1.9), (x, -3.28, 1.15), M_STEEL, ORC, bevel=0.01)
    box("WallCabinetGlass", (1.0, 0.02, 1.7), (x, -3.07, 1.15), mat("CabGlass", (0.5, 0.6, 0.65), 0.05, trans=0.7), ORC)
cyl("KickBucket", 0.18, 0.35, (1.0, 0.9, 0.18), M_STEEL, ORC)
# wall calendar beside the door, on the east wall: 8 pages, blank grid, a red cross per day (no numbers/words)
CAL = bpy.data.objects.new("Calendar", None); ORC.objects.link(CAL); CAL.location = (3.47, -0.9, 1.55); CAL.rotation_euler = (0, 0, math.radians(-90))
box("CalBack", (0.42, 0.01, 0.58), (0, 0.005, 0), mat("CalBoard", (0.2, 0.22, 0.25), 0.5), ORC).parent = CAL
box("CalHeader", (0.40, 0.004, 0.10), (0, -0.003, 0.22), mat("CalHeader", (0.15, 0.4, 0.55), 0.5), ORC).parent = CAL
PAGES = []
for pg in range(8):
    hinge = bpy.data.objects.new("CalPage_%d" % pg, None); ORC.objects.link(hinge); hinge.parent = CAL
    hinge.location = (0, -0.004 - 0.0006 * (8 - pg), 0.165)
    p = box("CalPaper_%d" % pg, (0.38, 0.0005, 0.38), (0, 0, -0.19), M_PAPER, ORC); p.parent = hinge
    for r in range(5):
        for cc in range(7):
            cell = box("CalCell", (0.045, 0.0002, 0.06), (-0.165 + cc * 0.055, -0.0004, -0.03 - r * 0.07), mat("Cell", (0.82, 0.82, 0.8), 0.7), ORC)
            cell.parent = hinge
    day = 9 + pg
    r, cc = divmod(day, 7)
    for sgn in (1, -1):
        x_ = box("CalX", (0.05, 0.0003, 0.008), (-0.165 + cc * 0.055, -0.0008, -0.03 - r * 0.07), M_RED_INK, ORC, rot=(0, math.radians(45 * sgn), 0))
        x_.parent = hinge
    PAGES.append(hinge)
# floor marks, wall scrub sink area
box("OR_ScrubSink", (1.2, 0.5, 0.9), (-2.7, 3.2, 0.45), M_STEEL, ORC, bevel=0.01)
print("SCENE_BUILT")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
