"""Set: street, lawn, house with clay roof, his room (one continuous world).
blender -b --python 02_build_scene.py -- <teen.blend> <out.blend>"""
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]
TEEN, OUT = a[0], a[1]
random.seed(20)

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)

# ------------------------------------------------------------------ render settings
r = sc.render
r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0; sc.frame_start, sc.frame_end = 1, 1500
cy = sc.cycles; cy.device = 'CPU'; cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 8; cy.transparent_max_bounces = 8
cy.caustics_reflective = cy.caustics_refractive = False
r.use_motion_blur = True; r.motion_blur_shutter = 0.5; r.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'

# ------------------------------------------------------------------ world + sun
w = bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
N, L = w.node_tree.nodes, w.node_tree.links
env = N.new("ShaderNodeTexEnvironment"); env.image = img(os.path.join(ASSETS, "hdri", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
mp = N.new("ShaderNodeMapping"); tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Generated"], mp.inputs[0]); L.new(mp.outputs[0], env.inputs[0])
mp.inputs["Rotation"].default_value = (0, 0, R_(200))
bg = N["Background"]; bg.inputs["Strength"].default_value = 1.0; L.new(env.outputs[0], bg.inputs[0])
sun_d = bpy.data.lights.new("Key_Sun", 'SUN'); sun_d.energy = 4.0; sun_d.angle = R_(1.5); sun_d.color = (1.0, 0.95, 0.86)
sun = bpy.data.objects.new("Key_Sun", sun_d); link(sun, "Lights")
sun.rotation_euler = Euler((R_(55), 0, R_(-28)))   # light travels +Y (into the window) and down

# ------------------------------------------------------------------ materials
M = {}
M["grass"] = pbr("Lawn", "leafy_grass", scale=0.5, box=True, tint=(0.55, 0.85, 0.45))
M["asphalt"] = pbr("Asphalt", "asphalt_02", scale=0.25, box=True)
M["concrete"] = pbr("Sidewalk", "concrete_floor_02", scale=0.4, box=True)
M["roof"] = pbr("RoofTiles", "clay_roof_tiles", scale=0.45, box=True)
M["ext"] = pbr("ExtPlaster", "painted_plaster_wall", scale=0.35, box=True, tint=(0.95, 0.88, 0.74))
M["int"] = pbr("IntPaint", "painted_plaster_wall", scale=0.5, box=True, tint=(0.30, 0.42, 0.50), normal=0.4)
M["ceil"] = pbr("Ceiling", "white_plaster_02", scale=0.5, box=True)
M["floor"] = pbr("Laminate", "laminate_floor_02", scale=0.45, box=True, tint=(0.78, 0.56, 0.38))
M["white"] = mat("WhitePVC", (0.85, 0.85, 0.83), 0.35)
M["trim"] = mat("TrimWood", (0.32, 0.22, 0.14), 0.5)
M["glass"] = mat("WindowGlass", (0.95, 0.98, 1.0), 0.02, trans=1.0, ior=1.5)
M["dark_glass"] = mat("DarkGlass", (0.06, 0.07, 0.08), 0.05, metal=0.3)
M["curtain"] = mat("Curtain", (0.55, 0.42, 0.30), 0.85, sss=0.0)
M["desk"] = mat("DeskTop", (0.05, 0.05, 0.055), 0.65)
M["metal"] = mat("DeskMetal", (0.6, 0.6, 0.62), 0.3, metal=1.0)
M["door"] = mat("FrontDoor", (0.18, 0.28, 0.32), 0.45)
M["fence"] = mat("FenceWhite", (0.88, 0.88, 0.85), 0.55)
M["gutter"] = mat("Gutter", (0.45, 0.45, 0.47), 0.4, metal=0.7)

def apply_bool(o, cutters):
    for k, cut in enumerate(cutters):
        md = o.modifiers.new("cut%d" % k, 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers):
        if md.type == 'BOOLEAN':
            with bpy.context.temp_override(object=o, active_object=o):
                bpy.ops.object.modifier_apply(modifier=md.name)
    for cut in cutters: bpy.data.objects.remove(cut, do_unlink=True)

# ------------------------------------------------------------------ ground, street, fence
gnd = box("Lawn", (70, 50, 0.1), (0, -10, -0.07), M["grass"])
box("Street", (90, 9, 0.1), (0, -24.5, -0.11), M["asphalt"])
box("Sidewalk", (90, 2.4, 0.14), (0, -18.8, -0.06), M["concrete"])
box("Curb", (90, 0.18, 0.2), (0, -20.05, -0.05), M["concrete"])
box("FrontPath", (1.3, 17.6, 0.1), (3.4, -9.6, -0.03), M["concrete"])
box("Driveway", (3.2, 18, 0.1), (-8.5, -9.5, -0.035), M["concrete"])
# picket fence along the lawn front (gap for the path)
pick = box("Picket", (0.08, 0.025, 0.95), (0, 0, 0), M["fence"], c="Props")
pick.data.vertices[0].co.z += 0  # noqa
for x in [i * 0.16 - 12.0 for i in range(150)]:
    if 2.6 < x < 4.2 or -10.3 < x < -6.7: continue
    p = pick.copy(); p.location = (x, -17.4, 0.45); link(p, "Fence")
bpy.data.objects.remove(pick)
for z in (0.25, 0.75):
    box("FenceRail", (24, 0.03, 0.07), (0, -17.37, z), M["fence"], c="Fence")
# mailbox
box("MailboxPost", (0.08, 0.08, 1.1), (4.5, -17.0, 0.55), M["trim"], c="Props")
box("Mailbox", (0.22, 0.45, 0.22), (4.5, -17.0, 1.2), mat("MailboxGrey", (0.25, 0.27, 0.3), 0.4, metal=0.6), c="Props", bevel=0.02)

# ------------------------------------------------------------------ house shell
HX0, HX1, HY0, HY1, HZ = -6.0, 5.0, 0.0, 9.0, 2.9
WIN = (-1.95, -0.65, 0.85, 2.05)          # room window x0,x1,z0,z1 (front wall)
def wall(name, x0, x1, y0, y1, z0, z1, m):
    return box(name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), m)
front = wall("Wall_Front", HX0, HX1, HY0, 0.2, 0, HZ, M["ext"])
cuts = [box("c", (WIN[1] - WIN[0], 1, WIN[3] - WIN[2]), ((WIN[0] + WIN[1]) / 2, 0.1, (WIN[2] + WIN[3]) / 2)),
        box("c", (1.1, 1, 1.0), (-4.4, 0.1, 1.55)), box("c", (1.0, 1, 2.1), (3.4, 0.1, 1.05))]
apply_bool(front, cuts)
wall("Wall_Back", HX0, HX1, HY1 - 0.2, HY1, 0, HZ, M["ext"])
wall("Wall_L", HX0, HX0 + 0.2, HY0, HY1, 0, HZ, M["ext"]); wall("Wall_R", HX1 - 0.2, HX1, HY0, HY1, 0, HZ, M["ext"])
box("Plinth", (HX1 - HX0 + 0.1, HY1 - HY0 + 0.1, 0.25), ((HX0 + HX1) / 2, (HY0 + HY1) / 2, 0.08), mat("PlinthGrey", (0.35, 0.34, 0.33), 0.8))
# gable roof (ridge along X)
OV = 0.55; RZ = 5.0; RY = (HY0 + HY1) / 2
def roof_plane(name, y_eave, z_eave):
    v = [(HX0 - OV, y_eave, z_eave), (HX1 + OV, y_eave, z_eave), (HX1 + OV, RY, RZ), (HX0 - OV, RY, RZ)]
    o = from_pydata(name, v, [(0, 1, 2, 3)], M["roof"])
    s = o.modifiers.new("thick", 'SOLIDIFY'); s.thickness = 0.12; s.offset = 1.0
    return o
roof_plane("Roof_Front", HY0 - OV, HZ - 0.2); roof_plane("Roof_Back", HY1 + OV, HZ - 0.2)
for x, nm in ((HX0, "Gable_L"), (HX1 - 0.2, "Gable_R")):
    g = from_pydata(nm, [(x, HY0, HZ), (x, HY1, HZ), (x, RY, RZ - 0.05)], [(0, 1, 2)], M["ext"])
    s = g.modifiers.new("t", 'SOLIDIFY'); s.thickness = 0.2; s.offset = -1.0 if x == HX0 else 1.0
box("RidgeCap", (HX1 - HX0 + 2 * OV, 0.25, 0.1), ((HX0 + HX1) / 2, RY, RZ + 0.1), M["roof"])
box("Gutter_F", (HX1 - HX0 + 2 * OV, 0.12, 0.1), ((HX0 + HX1) / 2, HY0 - OV - 0.02, HZ - 0.26), M["gutter"])
box("Fascia_F", (HX1 - HX0 + 2 * OV, 0.04, 0.22), ((HX0 + HX1) / 2, HY0 - OV + 0.04, HZ - 0.18), M["white"])
box("Downpipe", (0.08, 0.08, 2.8), (HX1 + 0.3, HY0 - OV + 0.0, 1.4), M["gutter"])
# other front window (dark room behind, curtains) and the front door
def window_frame(prefix, x0, x1, z0, z1, y=0.1, depth=0.2, glass=True, gm=None):
    t = 0.06
    box(prefix + "_FT", (x1 - x0 + 2 * t, depth + 0.02, t), ((x0 + x1) / 2, y, z1 + t / 2), M["white"])
    box(prefix + "_FB", (x1 - x0 + 2 * t, depth + 0.02, t), ((x0 + x1) / 2, y, z0 - t / 2), M["white"])
    box(prefix + "_FL", (t, depth + 0.02, z1 - z0), (x0 - t / 2, y, (z0 + z1) / 2), M["white"])
    box(prefix + "_FR", (t, depth + 0.02, z1 - z0), (x1 + t / 2, y, (z0 + z1) / 2), M["white"])
    box(prefix + "_Sill", (x1 - x0 + 0.3, 0.28, 0.05), ((x0 + x1) / 2, -0.08, z0 - 0.07), M["white"])
    if glass:
        return box(prefix + "_Glass", (x1 - x0, 0.008, z1 - z0), ((x0 + x1) / 2, y - 0.02, (z0 + z1) / 2), gm or M["glass"])
window_frame("Win2", -4.95, -3.85, 1.05, 2.05, gm=M["dark_glass"])
box("Win2_Curtain", (1.0, 0.02, 0.95), (-4.4, 0.35, 1.55), M["curtain"])
box("Door", (1.0, 0.06, 2.1), (3.4, 0.1, 1.05), M["door"], bevel=0.01)
box("DoorKnob", (0.05, 0.08, 0.05), (3.75, 0.04, 1.0), M["metal"])
box("DoorStep", (1.5, 0.6, 0.12), (3.4, -0.3, 0.06), M["concrete"])
glass = window_frame("RoomWin", WIN[0], WIN[1], WIN[2], WIN[3])
glass.name = "RoomWin_Glass"
cross = box("RoomWin_Transom", (WIN[1] - WIN[0], 0.06, 0.05), ((WIN[0] + WIN[1]) / 2, 0.14, 1.72), M["white"])

# ------------------------------------------------------------------ neighbours, trees, shrubs
for nx, tint in ((-17.0, (0.78, 0.82, 0.86)), (15.5, (0.9, 0.8, 0.7))):
    mm = mat("NeighbourWall%d" % int(nx), tint, 0.8)
    box("Neighbour_%d" % int(nx), (9, 9, 2.9), (nx, 4.0, 1.45), mm)
    v = [(nx - 5, -1.0, 2.8), (nx + 5, -1.0, 2.8), (nx + 5, 4.0, 4.9), (nx - 5, 4.0, 4.9)]
    o = from_pydata("NeighbourRoof_%d" % int(nx), v, [(0, 1, 2, 3)], M["roof"]); o.modifiers.new("t", 'SOLIDIFY').thickness = 0.12
    for wx in (-2.5, 0.5, 2.8):
        box("NWin", (1.0, 0.05, 1.0), (nx + wx, -0.52, 1.6), M["dark_glass"])
tree = append_objects(os.path.join(ASSETS, "tree_small_02", "tree_small_02_1k.blend"), "Plants")
tg = place_group(tree, "Tree_A", 6.5, 2, Vector((-7.5, -6.0, 0)))
tg2 = bpy.data.objects.new("Tree_B", None); link(tg2, "Plants"); tg2.instance_type = 'COLLECTION'
tcoll = bpy.data.collections.new("TreeInst");
for o in [tg] + tree:
    tcoll.objects.link(o)
tg2.instance_collection = tcoll; tg2.location = (9.5, -9.0, 0); tg2.rotation_euler = (0, 0, R_(140)); tg2.scale = (0.9, 0.9, 0.9)
tcoll.instance_offset = (-7.5, -6.0, 0)
shr = []
for nm, f in (("shrub_01", "shrub_01_1k.blend"), ("shrub_02", "shrub_02_1k.blend")):
    obs = append_objects(os.path.join(ASSETS, nm, f), "Plants")
    g = place_group(obs, "Shrub_" + nm, 1.0, 2, Vector((0, 0, 0)))
    c = bpy.data.collections.new("Inst_" + nm)
    for o in [g] + obs: c.objects.link(o)
    shr.append(c)
for i, x in enumerate([-5.3, -3.0, -2.2, -0.2, 0.9, 1.9, 4.5]):
    e = bpy.data.objects.new("ShrubI%d" % i, None); link(e, "Plants"); e.instance_type = 'COLLECTION'
    e.instance_collection = shr[i % 2]; e.location = (x + random.uniform(-0.2, 0.2), -0.9 + random.uniform(-0.2, 0.2), 0)
    s = random.uniform(0.8, 1.2); e.scale = (s, s, s); e.rotation_euler = (0, 0, random.uniform(0, 6.28))
# a parked car shape in the driveway (simple, unbranded)
carm = mat("CarPaint", (0.12, 0.22, 0.36), 0.25, metal=0.6, coat=1.0)
box("Car_Body", (1.8, 4.3, 0.75), (-8.5, -4.0, 0.62), carm, bevel=0.15)
box("Car_Cabin", (1.6, 2.2, 0.6), (-8.5, -4.2, 1.25), M["dark_glass"], bevel=0.18)
for wx in (-0.85, 0.85):
    for wy in (-1.35, 1.35):
        cyl("Car_Wheel", 0.33, 0.24, (-8.5 + wx, -4.0 + wy, 0.33), mat("Tyre", (0.03, 0.03, 0.03), 0.8), rot=(0, R_(90), 0))

# ------------------------------------------------------------------ his room
RX0, RX1, RY0, RY1, RZ1 = -2.2, 2.2, 0.2, 4.0, 2.6
box("Room_Floor", (RX1 - RX0, RY1 - RY0, 0.04), (0, (RY0 + RY1) / 2, -0.02), M["floor"])
box("Room_Ceiling", (RX1 - RX0, RY1 - RY0, 0.06), (0, (RY0 + RY1) / 2, RZ1 + 0.03), M["ceil"])
wall("Room_WallL", RX0 - 0.12, RX0, RY0, RY1 + 0.12, 0, RZ1, M["int"])
wall("Room_WallR", RX1, RX1 + 0.12, RY0, RY1 + 0.12, 0, RZ1, M["int"])
wall("Room_WallB", RX0, RX1, RY1, RY1 + 0.12, 0, RZ1, M["int"])
inner = wall("Room_WallF_In", RX0, RX1, 0.2, 0.205, 0, RZ1, M["int"])
apply_bool(inner, [box("c", (WIN[1] - WIN[0], 1, WIN[3] - WIN[2]), ((WIN[0] + WIN[1]) / 2, 0.2, (WIN[2] + WIN[3]) / 2))])
box("Skirting", (RX1 - RX0, 0.015, 0.08), (0, RY1 - 0.008, 0.04), M["white"])
box("InnerSill", (WIN[1] - WIN[0] + 0.15, 0.2, 0.04), ((WIN[0] + WIN[1]) / 2, 0.28, WIN[2] - 0.02), M["white"])
# curtains either side of the window (animated flutter later)
for side, x in (("L", WIN[0] - 0.22), ("R", WIN[1] + 0.22)):
    me = bpy.data.meshes.new("Curtain_" + side); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=12, y_segments=24, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.42, 0.03 * math.sin(v.co.x * 30), v.co.y * 2.3))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("Curtain_" + side, me); link(o, "Set"); o.location = (x, 0.3, 1.35); me.materials.append(M["curtain"])
    o.modifiers.new("sub", 'SUBSURF').levels = 1
box("CurtainRod", (2.0, 0.02, 0.02), ((WIN[0] + WIN[1]) / 2, 0.3, 2.5), M["metal"])

# desk
DESK_Z = 0.75
box("Desk_Top", (1.7, 0.78, 0.04), (0, 3.6, DESK_Z - 0.02), M["desk"], bevel=0.005)
for lx in (-0.8, 0.8):
    box("Desk_Leg", (0.06, 0.7, 0.04), (lx, 3.6, 0.02), M["metal"])
    box("Desk_Leg", (0.06, 0.05, DESK_Z - 0.04), (lx, 3.6, (DESK_Z - 0.04) / 2), M["metal"])
box("MousePad", (0.42, 0.34, 0.004), (0.42, 3.42, DESK_Z + 0.002), mat("PadCloth", (0.04, 0.04, 0.05), 0.9))
mon = import_glb(os.path.join(ASSETS, "glb", "monitor.glb"))
monitor = place_group(mon, "Monitor", 0.74, 0, Vector((0, 3.78, DESK_Z)), rot_z=0.0)
# screen: game-like moving landscape (the HDRI panned) + emission
scr = next(o for o in mon if o.type == 'MESH' and o.data.materials and o.data.materials[0].name.startswith("Display"))
sm = bpy.data.materials.new("Screen"); sm.use_nodes = True; nt = sm.node_tree; Nn, Ll = nt.nodes, nt.links
for n in list(Nn):
    if n.type != 'OUTPUT_MATERIAL': Nn.remove(n)
e_ = Nn.new("ShaderNodeEmission"); e_.name = "ScreenEmit"; e_.inputs["Strength"].default_value = 2.5
t_ = Nn.new("ShaderNodeTexEnvironment"); t_.image = env.image
tc2 = Nn.new("ShaderNodeTexCoord"); m2 = Nn.new("ShaderNodeMapping"); m2.name = "ScreenPan"
vec = Nn.new("ShaderNodeCombineXYZ")
sep = Nn.new("ShaderNodeSeparateXYZ"); Ll.new(tc2.outputs["Generated"], sep.inputs[0])
# map screen x,z -> direction (a 90-degree window of the panorama, slightly below the horizon)
mx_ = Nn.new("ShaderNodeMapRange"); mx_.inputs[3].default_value = -1.0; mx_.inputs[4].default_value = 1.0
Ll.new(sep.outputs[0], mx_.inputs[0])
mz_ = Nn.new("ShaderNodeMapRange"); mz_.inputs[3].default_value = -0.75; mz_.inputs[4].default_value = 0.55
Ll.new(sep.outputs[2], mz_.inputs[0])
Ll.new(mx_.outputs[0], vec.inputs[0]); vec.inputs[1].default_value = 1.0; Ll.new(mz_.outputs[0], vec.inputs[2])
Ll.new(vec.outputs[0], m2.inputs[0]); Ll.new(m2.outputs[0], t_.inputs[0])
tint_ = Nn.new("ShaderNodeMix"); tint_.data_type = 'RGBA'; tint_.blend_type = 'MULTIPLY'; tint_.inputs[0].default_value = 1.0
tint_.name = "ScreenTint"; tint_.inputs[7].default_value = (1.0, 0.9, 0.8, 1)
Ll.new(t_.outputs[0], tint_.inputs[6]); Ll.new(tint_.outputs[2], e_.inputs[0])
Ll.new(e_.outputs[0], Nn["Material Output"].inputs[0])
scr.data.materials[0] = sm
kb = import_glb(os.path.join(ASSETS, "glb", "keyboard.glb"))
kb_keys = [o for o in kb if o.name.startswith("Keyboard")]
ms_objs = [o for o in kb if o.name.startswith("Mouse")]
keyboard = place_group(kb_keys, "Keyboard", 0.44, 0, Vector((-0.08, 3.43, DESK_Z)), rot_z=R_(180))
mouse = place_group(ms_objs, "Mouse", 0.115, 1, Vector((0.42, 3.42, DESK_Z + 0.004)), rot_z=R_(180))
for o in kb:
    if o.parent is None and o.type == 'EMPTY' and not o.children: bpy.data.objects.remove(o)
ch = import_glb(os.path.join(ASSETS, "glb", "chair2.glb"))
chair = place_group(ch, "Chair", 1.3, 2, Vector((0, 2.62, 0)), rot_z=R_(180))
# PC tower with fan glow, LED strip, shelf, lamp, can, snack bowl, posters, bed, bookshelf, plant
tower = box("PC_Tower", (0.22, 0.46, 0.48), (1.05, 3.7, 0.24), mat("TowerBlack", (0.03, 0.03, 0.035), 0.35), bevel=0.01)
box("PC_Glass", (0.005, 0.4, 0.42), (0.938, 3.7, 0.25), mat("TowerGlass", (0.1, 0.1, 0.12), 0.05, metal=0.2, alpha=1.0))
for k, z in enumerate((0.13, 0.27, 0.40)):
    cyl("PC_Fan%d" % k, 0.07, 0.01, (0.932, 3.7, z), mat("FanRGB%d" % k, (0.1, 0.1, 0.1), 0.4, emit=(0.2, 0.5, 1.0), estr=6.0), rot=(0, R_(90), 0))
led = box("LED_Strip", (1.9, 0.01, 0.012), (0, RY1 - 0.01, 1.62), mat("LEDStrip", (0.1, 0.1, 0.1), 0.5, emit=(0.6, 0.1, 1.0), estr=12.0))
box("WallShelf", (1.3, 0.22, 0.03), (0, RY1 - 0.11, 1.6), M["trim"])
for k in range(6):
    box("ShelfItem%d" % k, (0.06, 0.12, random.uniform(0.12, 0.22)), (-0.5 + k * 0.2, RY1 - 0.12, 1.69),
        mat("ShelfItem%d" % k, (random.uniform(0.1, 0.8), random.uniform(0.1, 0.6), random.uniform(0.1, 0.7)), 0.5))
can = cyl("SodaCan", 0.033, 0.12, (0.7, 3.55, DESK_Z + 0.06), mat("CanPaint", (0.55, 0.08, 0.06), 0.25, metal=0.8))
cyl("SodaCanTop", 0.03, 0.004, (0.7, 3.55, DESK_Z + 0.122), mat("CanTop", (0.7, 0.7, 0.72), 0.2, metal=1.0))
bowl = cyl("SnackBowl", 0.09, 0.05, (-0.62, 3.48, DESK_Z + 0.025), mat("BowlWhite", (0.8, 0.8, 0.78), 0.3), r2=0.06)
for k in range(9):
    o = box("Chip%d" % k, (0.03, 0.025, 0.004), (-0.62 + random.uniform(-0.05, 0.05), 3.48 + random.uniform(-0.05, 0.05), DESK_Z + 0.05 + random.uniform(0, 0.01)),
            mat("Chip", (0.85, 0.62, 0.25), 0.6), rot=(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 3)))
lamp = append_objects(os.path.join(ASSETS, "desk_lamp_arm_01", "desk_lamp_arm_01_1k.blend"))
place_group(lamp, "DeskLamp", 0.5, 2, Vector((-0.72, 3.82, DESK_Z)), rot_z=R_(-30))
shelf = append_objects(os.path.join(ASSETS, "wooden_bookshelf_worn", "wooden_bookshelf_worn_1k.blend"))
place_group(shelf, "Bookshelf", 1.8, 2, Vector((RX0 + 0.22, 1.0, 0)), rot_z=R_(-90))
plant = append_objects(os.path.join(ASSETS, "potted_plant_01", "potted_plant_01_1k.blend"))
place_group(plant, "Plant", 0.9, 2, Vector((RX0 + 0.35, RY1 - 0.35, 0)))
# bed against the right wall
box("Bed_Frame", (1.0, 2.0, 0.32), (RX1 - 0.52, 1.35, 0.16), M["trim"])
box("Bed_Mattress", (0.95, 1.95, 0.2), (RX1 - 0.52, 1.35, 0.42), mat("Sheet", (0.75, 0.77, 0.8), 0.9), bevel=0.05)
box("Bed_Blanket", (0.98, 1.3, 0.06), (RX1 - 0.52, 1.05, 0.54), mat("Blanket", (0.15, 0.25, 0.42), 0.95), bevel=0.03)
box("Bed_Pillow", (0.6, 0.38, 0.12), (RX1 - 0.52, 2.08, 0.58), mat("Sheet", (0.75, 0.77, 0.8), 0.9), bevel=0.05)
# posters (abstract art, no text) on the right and left walls
def poster(name, loc, rot, size, seed, wall_n):
    wall_n = Vector(wall_n)
    me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], 0, v.co.y * size[1]))
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); link(o); o.location = loc; o.rotation_euler = rot
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; Nn, Ll = nt.nodes, nt.links
    b = Nn["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.6
    tcp = Nn.new("ShaderNodeTexCoord"); vo = Nn.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 3.0 + seed
    vo.voronoi_dimensions = '4D'; Ll.new(tcp.outputs["Generated"], vo.inputs[0]); vo.inputs["W"].default_value = seed
    ramp = Nn.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    random.seed(seed * 7)
    el[0].color = (random.random() * 0.3, random.random() * 0.2, random.random() * 0.5, 1); el[1].color = (0.9, random.random() * 0.6 + 0.2, 0.2, 1)
    Ll.new(vo.outputs["Distance"], ramp.inputs[0]); Ll.new(ramp.outputs[0], b.inputs["Base Color"])
    me.materials.append(m)
    o.location = Vector(loc) - wall_n * 0.004       # poster sits 4 mm proud of its frame
    box(name + "_Frame", (size[0] + 0.03, 0.006, size[1] + 0.03), Vector(loc) + wall_n * 0.003, mat("PosterFrame", (0.02, 0.02, 0.02), 0.4), rot=rot)
poster("Poster_A", (RX1 - 0.01, 1.4, 1.6), (0, 0, R_(90)), (0.6, 0.85), 3, (1, 0, 0))
poster("Poster_B", (RX0 + 0.01, 2.6, 1.65), (0, 0, R_(-90)), (0.5, 0.7), 5, (-1, 0, 0))
poster("Poster_C", (1.55, RY1 - 0.01, 1.35), (0, 0, 0), (0.45, 0.6), 8, (0, 1, 0))
# ceiling light fixture (off)
cyl("CeilingLamp", 0.22, 0.06, (0, 2.1, RZ1 - 0.04), mat("LampShade", (0.9, 0.9, 0.88), 0.4))
# rug
box("Rug", (1.6, 1.2, 0.01), (0, 2.6, 0.005), mat("Rug", (0.35, 0.12, 0.1), 0.95))

# interior lights: soft window fill, monitor glow, desk lamp warm, LED bounce
def area(name, size, loc, rot, energy, col, shape='RECTANGLE', sy=None):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.color = col; d.shape = shape; d.size = size
    if sy: d.size_y = sy
    o = bpy.data.objects.new(name, d); link(o, "Lights"); o.location = loc; o.rotation_euler = rot
    o.visible_camera = False; o.visible_glossy = False; return o
area("Win_Fill", 1.2, ((WIN[0] + WIN[1]) / 2, 0.35, 1.45), (R_(90), 0, 0), 90, (0.85, 0.92, 1.0), sy=1.1)
area("Monitor_Glow", 0.7, (0, 3.68, 1.08), (R_(-90), 0, 0), 40, (0.65, 0.78, 1.0), sy=0.4)
area("Room_Bounce", 2.5, (0.5, 2.0, RZ1 - 0.1), (0, 0, 0), 18, (1.0, 0.95, 0.9))
pl = bpy.data.lights.new("DeskLamp_Light", 'POINT'); pl.energy = 15; pl.color = (1.0, 0.8, 0.55); pl.shadow_soft_size = 0.05
plo = bpy.data.objects.new("DeskLamp_Light", pl); link(plo, "Lights"); plo.location = (-0.55, 3.62, 1.12)

# ------------------------------------------------------------------ the teen
with bpy.data.libraries.load(TEEN, link=False) as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects: link(o, "Teen")
shirt = bpy.data.objects["Teen.male_casualsuit04"]
tee = img(os.path.join(ASSETS, "tex", "tee_plain_diffuse.png"))
for m in shirt.data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and "diffuse" in n.image.name.lower():
            n.image = tee                                    # print/logo and trims removed by 00_plain_shirt.py
# eyes: the refractive outer layer renders black without caustics -> thin non-refractive coat
for m in bpy.data.objects["Teen.high-poly"].data.materials:
    for n in m.node_tree.nodes:
        if n.type == 'GROUP' and "OuterLayerTransmission" in n.inputs:
            n.inputs["OuterLayerTransmission"].default_value = 0.0
            n.inputs["OuterLayerAlpha"].default_value = 0.08
# books on the (empty) bookshelf
bs = bpy.data.objects["Bookshelf"]; mn_, mx_ = bounds([o for o in bpy.data.objects if o.parent == bs or (o.parent and o.parent.parent == bs)])
print("SHELF", tuple(mn_), tuple(mx_))
random.seed(9)
for lvl in range(5):
    z = mn_.z + 0.08 + lvl * (mx_.z - mn_.z - 0.1) / 5
    y = mn_.y + 0.05
    while y < mx_.y - 0.08:
        w_ = random.uniform(0.02, 0.05); h_ = random.uniform(0.18, 0.27)
        if random.random() < 0.12: y += 0.06; continue
        box("Book", (0.18, w_, h_), (mn_.x + 0.12, y + w_ / 2, z + h_ / 2), mat("Book%d" % random.randint(0, 7), (random.uniform(0.1, 0.7), random.uniform(0.05, 0.5), random.uniform(0.05, 0.5)), 0.6), c="Props")
        y += w_ + 0.003
print("OBJECTS", len(bpy.data.objects))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
