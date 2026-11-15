"""Killer thumbnail plate: looking straight up inside a narrow 1940s closet at the small opening in its ceiling
(about 8 x 15 inches), police chalk measurements beside it, a faint warm glow coming down from the crawl space.
A cold torch beam from below (the detectives). Coats hang at the frame edge.
  python sc_closet_hatch.py [--pct 25] [--samples 64] [--out plates/killer.png]"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
import bpy
from mathutils import Vector
from common import reset, camera, point_at, area_light
from kit import pbr, box, cyl, emissive, fabric, haze
import ph

arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
s = reset(res=(1920, 1080), samples=arg("--samples", 160), exposure=0.0)
s.render.resolution_percentage = arg("--pct", 100)
s.cycles.max_bounces = 8
w = bpy.data.worlds.new("W"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs['Color'].default_value = (0, 0, 0, 1)

IN = 0.0254
CW, CD, CH = 0.92, 0.66, 2.44          # closet inside: width (x), depth (y), height
HX, HY = 0.05, 0.03                     # hatch centre on the ceiling
HL, HWD = 15 * IN, 8 * IN               # 15 in along x, 8 in along y
T = 0.035                               # ceiling thickness

paper = ph.texture("decrepit_wallpaper", scale=1.4, tint=(0.95, 0.85, 0.68), name="Wallpaper")
plaster = ph.texture("white_plaster_rough_01", scale=1.6, tint=(0.82, 0.76, 0.64), name="Ceiling")
wood = ph.texture("old_planks_02", scale=2.0, tint=(0.7, 0.55, 0.42), name="Trim")
raft = ph.texture("weathered_brown_planks", scale=1.5, tint=(0.06, 0.045, 0.035), name="Rafters")

# walls (inside faces)
box("WallL", (-CW / 2 - 0.02, 0, CH / 2), (0.04, CD, CH), paper)
box("WallR", (CW / 2 + 0.02, 0, CH / 2), (0.04, CD, CH), paper)
box("WallB", (0, CD / 2 + 0.02, CH / 2), (CW + 0.08, 0.04, CH), paper)
# front wall above the door opening (the door is behind and below the camera)
box("Header", (0, -CD / 2 - 0.02, CH - 0.2), (CW + 0.08, 0.04, 0.4), paper)
box("FrontL", (-CW / 2 + 0.06, -CD / 2 - 0.02, CH / 2), (0.12, 0.04, CH), paper)
box("FrontR", (CW / 2 - 0.06, -CD / 2 - 0.02, CH / 2), (0.12, 0.04, CH), paper)
box("RoomCeil", (0, -2.5, CH + T / 2), (6, 4.2, T), plaster)
box("RoomFloor", (0, -1.5, -0.01), (6, 6, 0.02), wood)
# ceiling with the opening: four plates round the hole
x0, x1, y0, y1 = HX - HL / 2, HX + HL / 2, HY - HWD / 2, HY + HWD / 2
zc = CH + T / 2
box("CeilL", ((-CW / 2 + x0) / 2, 0, zc), (x0 + CW / 2, CD, T), plaster)
box("CeilR", ((CW / 2 + x1) / 2, 0, zc), (CW / 2 - x1, CD, T), plaster)
box("CeilF", (HX, (-CD / 2 + y0) / 2, zc), (HL, y0 + CD / 2, T), plaster)
box("CeilB", (HX, (CD / 2 + y1) / 2, zc), (HL, CD / 2 - y1, T), plaster)
# a thin wooden trim round the hole and the crown moulding
tw = 0.018
box("TrimF", (HX, y0 - tw / 2, CH - 0.006), (HL + 2 * tw, tw, 0.012), wood)
box("TrimB", (HX, y1 + tw / 2, CH - 0.006), (HL + 2 * tw, tw, 0.012), wood)
box("TrimL", (x0 - tw / 2, HY, CH - 0.006), (tw, HWD, 0.012), wood)
box("TrimR", (x1 + tw / 2, HY, CH - 0.006), (tw, HWD, 0.012), wood)
for nm, loc, size in (("CrL", (-CW / 2 + 0.02, 0, CH - 0.03), (0.04, CD, 0.06)), ("CrR", (CW / 2 - 0.02, 0, CH - 0.03), (0.04, CD, 0.06)),
                      ("CrB", (0, CD / 2 - 0.02, CH - 0.03), (CW, 0.04, 0.06))):
    box(nm, loc, size, wood)

# the crawl space above: joists, sloping roof boards, very dark; a hot plate's glow off to one side
box("AtticFloor", (0, 0, CH + T + 0.01), (3, 3, 0.02), raft).hide_render = True
for k in range(-3, 3):
    box(f"Joist{k}", (0.31 + k * 0.5, 0, CH + T + 0.07), (0.05, 3.0, 0.14), raft)
for sgn in (-1, 1):
    r = box(f"Roof{sgn}", (0, sgn * 0.7, CH + 0.55), (3.0, 1.6, 0.03), raft, rot=(math.radians(-sgn * 32), 0, 0))
bpy.ops.object.light_add(type='POINT', location=(0.6, 0.12, CH + T + 0.04)); hp = bpy.context.active_object
hp.data.energy = 22; hp.data.color = (1.0, 0.42, 0.12); hp.data.shadow_soft_size = 0.05
bpy.ops.object.light_add(type='POINT', location=(0.35, -0.1, CH + T + 0.2)); hp2 = bpy.context.active_object
hp2.data.energy = 0.0; hp2.data.color = (1.0, 0.55, 0.25); hp2.data.shadow_soft_size = 0.2

box("Brace", (0.02, 0.0, CH + 0.36), (0.05, 1.6, 0.07), raft, rot=(0.0, 0.0, math.radians(18)))
haze((0.3, 0.05, CH + T + 0.25), (1.4, 1.0, 0.42), density=1.1, color=(1.0, 0.8, 0.6), anis=0.2)
# chalk: dimension lines and the two numbers, as the police marked them
chalk = pbr("Chalk", (0.85, 0.85, 0.82), 0.95)
zc0 = CH - 0.0015
box("DimX", (HX, y0 - 0.07, zc0), (HL, 0.005, 0.002), chalk)
for x in (x0, x1):
    box("TickX", (x, y0 - 0.07, zc0), (0.005, 0.04, 0.002), chalk)
box("DimY", (x1 + 0.07, HY, zc0), (0.005, HWD, 0.002), chalk)
for y in (y0, y1):
    box("TickY", (x1 + 0.07, y, zc0), (0.04, 0.005, 0.002), chalk)
FONT = os.path.join(HERE, "..", "..", "assets", "fonts", "CaveatBrush-Regular.ttf")


def chalk_text(s_, loc, rotz, size):
    bpy.ops.object.text_add(location=loc); t = bpy.context.active_object
    t.data.body = s_; t.data.size = size; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    try:
        t.data.font = bpy.data.fonts.load(FONT)
    except Exception as e:
        print("font", e)
    t.data.extrude = 0.0006; t.rotation_euler = (math.pi, 0, rotz)        # facing down, readable from below
    t.data.materials.append(chalk)
    return t


chalk_text("15 in", (HX, y0 - 0.115, zc0), 0.0, 0.06)
chalk_text("8 in", (x1 + 0.125, HY, zc0), math.radians(-90), 0.06)

# the detectives' torch from below, cold white; plus a weak fill so the paper reads
bpy.ops.object.light_add(type='SPOT', location=(-0.3, -0.45, 1.05)); sp = bpy.context.active_object
sp.data.energy = 40; sp.data.spot_size = math.radians(30); sp.data.spot_blend = 0.8; sp.data.shadow_soft_size = 0.02
sp.data.color = (0.82, 0.88, 1.0); point_at(sp, (HX - 0.12, HY - 0.1, CH))
f = area_light((0.0, -0.9, 1.2), (0, 0, 0), 0.8, 2.0, (0.6, 0.7, 0.95)); point_at(f, (0, 0, 2.2))
f2 = area_light((0.0, -0.75, 0.25), (0, 0, 0), 0.6, 9.0, (1.0, 0.85, 0.65)); point_at(f2, (0, 0.2, 1.6))

att = bpy.data.collections.new("Attic"); s.collection.children.link(att)
for o in list(bpy.data.objects):
    if o.name.startswith(("Joist", "Roof")):
        for c_ in o.users_collection: c_.objects.unlink(o)
        att.objects.link(o)
try:
    sp.light_linking.receiver_collection = bpy.data.collections.new("TorchRecv")
    for o in bpy.data.objects:
        if o.type in ('MESH', 'FONT') and o.name not in att.objects:
            sp.light_linking.receiver_collection.objects.link(o)
except Exception as e:
    print("linking", e)
CL = (-0.02, -0.06, 1.05)
cam = camera(CL, (-0.03, -0.0, CH), lens=17)
cam.rotation_euler.rotate_axis('Z', math.radians(0))
out = arg("--out", os.path.join(HERE, "plates", "killer.png"))
s.render.filepath = out; s.render.image_settings.color_depth = '8'
bpy.ops.render.render(write_still=True)
print("[plate]", out)
