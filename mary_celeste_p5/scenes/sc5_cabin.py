"""Part 5 interiors aboard: the cabin table (myth and record) and the galley. SHOT = S09 S10 S12 S13 S14.

S09/S10  THE STORY (years later): a warm meal on the cabin table, lamp lit, steam off the mugs, a chair pushed back.
S13/S14  THE RECORD: the same cabin soaked, grey light down the skylight, water on the floor, on the table only the
         log slate with the last position (25 November, 8 a.m.) - already days old when they found it.
S12      the galley: the stove cold, pots shifted, water slopping across the floor.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector, Matrix
import ship, props5 as PR


def p1_interiors():
    """Part 1's interiors module, used as is (mary_celeste_p1/p1, same set as P1 S34-S36 and its slate), so the
    galley and the slate match Part 1 shot for shot."""
    p1 = os.path.abspath(os.path.join(p5.ROOT, "mary_celeste_p1", "p1"))
    if p1 not in sys.path:
        sys.path.append(p1)
    import interiors
    return interiors

SHOT = os.environ.get("SHOT", "S09")
OUT = os.environ.get("OUT", os.path.join(p5.OUTDIR, f"{SHOT}.png"))
sc = C.render_setup(samples=int(os.environ.get("SPP", "200")), noise=0.025, bounces=8)
MYTH = SHOT in ("S09", "S10")
WET = 0.0 if MYTH else 0.85
RX, RY, RZ = 1.9, 1.5, 2.05
TABLE = Vector((0.0, 0.0, 0.74))


def wood(aid, s, tint, name, wet=WET):
    return ship.wood(aid, s, wet=wet, tint=tint, name=name)


def room(rx, ry, rz, walls, floor, ceil, sky=(0.1, -0.4, 0.62, 0.5)):
    ship.box("floor", (0, 0, -0.03), (2 * rx, 2 * ry, 0.06), floor)
    for sg in (1, -1):
        ship.box(f"wy{sg}", (0, sg * (ry + 0.03), rz / 2), (2 * rx, 0.06, rz + 0.1), walls)
        ship.box(f"wx{sg}", (sg * (rx + 0.03), 0, rz / 2), (0.06, 2 * ry, rz + 0.1), walls)
    sx, sy, sw, sh = sky
    ship.box("ca", ((sx - sw / 2 - rx) / 2, 0, rz + 0.03), (sx - sw / 2 + rx, 2 * ry, 0.06), ceil)
    ship.box("cb", ((sx + sw / 2 + rx) / 2, 0, rz + 0.03), (rx - sx - sw / 2, 2 * ry, 0.06), ceil)
    ship.box("cc", (sx, (sy - sh / 2 - ry) / 2, rz + 0.03), (sw, sy - sh / 2 + ry, 0.06), ceil)
    ship.box("cd", (sx, (sy + sh / 2 + ry) / 2, rz + 0.03), (sw, ry - sy - sh / 2, 0.06), ceil)
    x = -rx + 0.25
    while x < rx:
        if abs(x - sx) > sw / 2 + 0.05:
            ship.box("beam", (x, 0, rz - 0.07), (0.11, 2 * ry, 0.14), ceil, bevel=0.01)
        x += 0.52
    # skylight glazing bars (glass left out: the frame reads, the light comes through clean)
    for k in range(1, 4):
        ship.box("bar", (sx - sw / 2 + k * sw / 4, sy, rz + 0.05), (0.025, sh, 0.04), ceil)
    return sky


walls = wood("dark_wooden_planks", 1.4, (0.95, 0.75, 0.55) if MYTH else (0.75, 0.62, 0.5), "walls", wet=0.15)
floor = wood("weathered_planks", 0.9, (0.9, 0.72, 0.55), "floor")
ceil = ship.paint("ceil", (0.42, 0.37, 0.28), rough=0.5, grime=0.6, chips=0.3, scale=6)
tabw = wood("brown_planks_05", 1.6, (0.85, 0.6, 0.42), "tablewood")

if SHOT != "S12":
    SKY = room(RX, RY, RZ, walls, floor, ceil)
    # the ship's table: a heavy top bolted to two pedestals, with fiddles (rails) round the edge
    ship.box("top", (TABLE.x, TABLE.y, TABLE.z - 0.025), (1.3, 0.82, 0.05), tabw, bevel=0.008)
    for sx in (-0.42, 0.42):
        ship.box("ped", (sx, 0, (TABLE.z - 0.05) / 2), (0.12, 0.5, TABLE.z - 0.05), tabw, bevel=0.01)
        ship.box("foot", (sx, 0, 0.03), (0.22, 0.7, 0.06), tabw, bevel=0.01)
    for sy in (-1, 1):
        ship.box("fid", (0, sy * 0.4, TABLE.z + 0.018), (1.3, 0.018, 0.035), tabw, bevel=0.004)
    for sx in (-1, 1):
        ship.box("fid", (sx * 0.64, 0, TABLE.z + 0.018), (0.018, 0.82, 0.035), tabw, bevel=0.004)
    # a settee along the after bulkhead, a chair at the side
    ship.box("settee", (0, RY - 0.3, 0.22), (2.6, 0.5, 0.44), tabw, bevel=0.01)
    ship.box("settee_back", (0, RY - 0.06, 0.62), (2.6, 0.08, 0.5), tabw, bevel=0.01)
    T = TABLE + Vector((0, 0, 0.0))
    if MYTH:
        chair, _ = PR.put("WoodenChair_01", (0.3, -0.85, 0), rot_z=math.radians(200), size=0.9)
        chair.rotation_euler.z += math.radians(18)          # pushed back and turned, as if someone got up
        PR.put("carved_wooden_plate", T + Vector((0.3, -0.18, 0)), size=0.24, axis=0)
        PR.put("carved_wooden_plate", T + Vector((-0.35, -0.16, 0)), size=0.24, axis=0)
        PR.put("carved_wooden_plate", T + Vector((-0.2, 0.2, 0)), size=0.24, axis=0)
        bowl, _ = PR.put("wooden_bowl_01", T + Vector((0.0, 0.02, 0)), size=0.22, axis=0)
        stew = ship.cyl("stew", T + Vector((0.0, 0.02, 0.045)), T + Vector((0.0, 0.02, 0.05)), 0.085, mat=ship.paint("stew", (0.16, 0.07, 0.025), rough=0.25, grime=0.3), verts=32)
        PR.steam("steam_bowl", T + Vector((0.0, 0.02, 0.06)), size=(0.16, 0.16, 0.32), density=4.0)
        for k, (x, y) in enumerate(((0.45, 0.12), (-0.48, 0.1), (0.1, -0.28))):
            mug = PR.mug(f"mug{k}", T + Vector((x, y, 0)))
            PR.steam(f"steam{k}", T + Vector((x, y, 0.09)), size=(0.08, 0.08, 0.22), density=3.5)
        PR.put("jug_01", T + Vector((-0.5, -0.25, 0)), size=0.2)
        PR.put("hamburger_buns", T + Vector((0.22, 0.22, 0)), size=0.24, axis=0)
        for k, x in enumerate((0.3, -0.35)):
            fk = ship.box(f"fork{k}", (0, 0, 0), (0.18, 0.012, 0.004), ship.iron(f"steel{k}"))
            fk.matrix_world = Matrix.Translation(T + Vector((x + 0.06, -0.2, 0.012))) @ Matrix.Rotation(0.5 + k, 4, 'Z')
        lamp, lm = PR.put("vintage_oil_lamp", T + Vector((-0.05, 0.28, 0)), size=0.46)
        lp = bpy.data.objects.new("flame", bpy.data.lights.new("flame", 'POINT')); sc.collection.objects.link(lp)
        lp.location = T + Vector((-0.05, 0.28, 0.2)); lp.data.energy = 40; lp.data.color = (1.0, 0.6, 0.28); lp.data.shadow_soft_size = 0.02
    else:
        p1_interiors().slate(T + Vector((0.12, -0.08, 0.0)), rot=math.radians(-8))     # P1/P2's dark slate, chalk hand
        # under our grey skylight P1's slate face read pale: deepen the slate (gamma), the chalk stays bright
        sm = bpy.data.materials.get("slateface")
        if sm:
            N = sm.node_tree.nodes; Lk = sm.node_tree.links; tex = next(n for n in N if n.type == 'TEX_IMAGE')
            g = N.new("ShaderNodeGamma"); g.inputs['Gamma'].default_value = 2.2
            Lk.new(tex.outputs['Color'], g.inputs['Color']); Lk.new(g.outputs['Color'], N["Principled BSDF"].inputs['Base Color'])
            N["Principled BSDF"].inputs['Roughness'].default_value = 0.85
        PR.water_floor("bilge", (0, 0, 0.0), (2 * RX - 0.1, 2 * RY - 0.1), depth=0.035)
        chair, _ = PR.put("WoodenChair_01", (-1.0, -0.7, 0), rot_z=math.radians(60), size=0.9)
        chair.rotation_euler = (math.radians(0), math.radians(90), math.radians(70))      # knocked over
        chair.location.z += 0.22
    # light
    if MYTH:
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.025, 0.035, 1)
        hang = bpy.data.objects.new("hanglamp", bpy.data.lights.new("hanglamp", 'POINT')); sc.collection.objects.link(hang)
        hang.location = (-0.9, 0.3, 1.7); hang.data.energy = 60; hang.data.color = (1.0, 0.62, 0.32); hang.data.shadow_soft_size = 0.05
        fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", 'AREA')); sc.collection.objects.link(fill)
        fill.location = (1.2, -1.2, 1.6); fill.data.energy = 18; fill.data.size = 1.2; fill.data.color = (1.0, 0.8, 0.6)
        fill.rotation_euler = (math.radians(60), 0, math.radians(45))
        cine = {"sat": 1.15, "exposure": 0.1}
    else:
        w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.035, 0.045, 1)
        sx, sy, sw, sh = SKY
        key = bpy.data.objects.new("skylight", bpy.data.lights.new("skylight", 'AREA')); sc.collection.objects.link(key)
        key.location = (sx, sy, RZ + 0.25); key.data.shape = 'RECTANGLE'; key.data.size = sw; key.data.size_y = sh
        key.data.energy = 260; key.data.color = (0.85, 0.9, 1.0)
        lan = bpy.data.objects.new("lantern", bpy.data.lights.new("lantern", 'POINT')); sc.collection.objects.link(lan)
        lan.location = (-1.6, -1.2, 1.2); lan.data.energy = 6; lan.data.color = (1.0, 0.65, 0.35)
        # drips from the skylight, falling
        cine = {"sat": 1.0, "exposure": 0.0}
    # cameras
    if SHOT == "S09":
        C.camera((1.75, -1.35, 1.45), (0.0, 0.05, 0.8), lens=28, fstop=4.0, focus=2.3)
    elif SHOT == "S10":
        C.camera((0.55, -0.95, 0.95), (0.05, 0.05, 0.78), lens=50, fstop=2.0, focus=0.9)
    elif SHOT == "S13":
        C.camera((1.75, -1.35, 1.45), (0.0, 0.05, 0.8), lens=28, fstop=4.0, focus=2.3)
    elif SHOT == "S14":
        C.camera((0.12, -0.42, 1.25), T + Vector((0.12, -0.06, 0.02)), lens=60, fstop=3.5, focus=0.62)
else:
    # ---- the galley: Part 1's set as is (sooty planking, the cast-iron "Star 6" stove knocked off its hearth,
    # sea water up to the door sill), lit by its hanging lamp and the daylight from the door, as P1 S34
    I = p1_interiors()
    a = I.galley()
    I.lantern((0.6, 0.9, 1.75), energy=95)
    ship.cyl("lamp_hook", (0.6, 0.9, 1.75), (0.6, 0.9, 1.95), 0.006, mat=ship.iron("hk"), verts=8)
    C.camera((1.55, 1.15, 1.4), (-0.9, -0.2, 0.45), lens=22, fstop=4.0)
    cine = {"sat": 1.05, "exposure": 0.5}

C.finish(OUT, cine=cine, bloom=0.4)
print("RENDERED", OUT)
