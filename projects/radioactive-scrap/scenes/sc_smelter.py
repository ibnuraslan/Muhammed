"""The smelting works about 90 km east of Istanbul: a dim steel-framed shed, a furnace whose door opens on the
glow (the film's one warm accent), workers feeding scrap, a ladle pouring into ingot moulds, sparks.
Ch4 (cold): a specialist walks the hall with a detector; the needle rests near zero by stacked ingots."""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from rs_env import sky
from human import reset_pose, pose_walk, reach, fingers_curl
from durs import dur

EXPOSURE = 0.0
BOUNCES = 6
FUR = Vector((0.0, 8.0, 0))          # furnace centre
MOULDS = Vector((7.0, 2.0, 0))       # first mould of the row


def molten(name, strength=18.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs['Scale'].default_value = 6; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (1.0, 0.35, 0.05, 1); cr.color_ramp.elements[1].color = (1.0, 0.75, 0.3, 1)
    L.new(nz.outputs['Fac'], cr.inputs['Fac'])
    p.inputs['Base Color'].default_value = (0.1, 0.05, 0.02, 1); L.new(cr.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = strength
    return m


def build(variant=None):
    c = {}
    v = variant or "hot"
    rng = np.random.default_rng(8)
    sky("overcast")
    bpy.context.scene.view_settings.exposure = 0.4 if v == "hot" else 0.3
    floor = ph_mat("concrete_floor_damaged_01", 0.3, (0.25, 0.24, 0.22), name="SmeltFloor", tint=(0.45, 0.42, 0.4))
    box("Floor", (0, 0, -0.05), (60, 60, 0.1), floor)
    iron = ph_mat("rusty_corrugated_iron", 0.4, (0.3, 0.25, 0.2), name="ShedWall", tint=(0.55, 0.55, 0.58))
    W, D, H = 36, 30, 14
    for a, b in (((-W / 2, -D / 2), (W / 2, -D / 2)), ((W / 2, -D / 2), (W / 2, D / 2)), ((W / 2, D / 2), (-W / 2, D / 2)), ((-W / 2, D / 2), (-W / 2, -D / 2))):
        wall("ShedWall", a, b, H, 0.1, iron)
    box("Roof", (0, 0, H + 0.05), (W, D, 0.1), iron)
    col_m = painted_steel("ShedSteel", (0.18, 0.2, 0.22), 0.5, 0.6)
    for x in np.arange(-W / 2 + 3, W / 2, 6):
        for y in (-D / 2 + 0.4, D / 2 - 0.4):
            box("Column", (x, y, H / 2), (0.4, 0.4, H), col_m)
        box("Truss", (x, 0, H - 0.6), (0.3, D, 0.6), col_m)
    for k in range(5):                                    # roof lights: grey daylight through dirty panels
        box("Rooflight", (-12 + k * 6, 0, H - 0.01), (2.0, 10, 0.02), glass("Rooflight", (0.8, 0.82, 0.8), 0.4))
        l = bpy.data.lights.new("RoofDay", 'AREA'); l.size = 2.0; l.size_y = 10; l.energy = 600 if v == "hot" else 900; l.color = (0.85, 0.9, 1.0)
        o = bpy.data.objects.new("RoofDay", l); bpy.context.collection.objects.link(o); o.location = (-12 + k * 6, 0, H - 0.3)
    haze((0, 0, 6), (W - 1, D - 1, 12), density=0.004 if v == "hot" else 0.003, color=(0.8, 0.78, 0.75), anis=0.4)
    # the furnace: refractory drum with a door that lifts on the glow
    refr = ph_mat("rough_concrete", 0.6, (0.25, 0.22, 0.2), name="Refractory")
    shell = painted_steel("FurShell", (0.12, 0.12, 0.13), 0.5, 0.7)
    cyl("Furnace", FUR + Vector((0, 0, 2.0)), 2.4, 4.0, shell, verts=40)
    cyl("FurnaceRim", FUR + Vector((0, 0, 4.05)), 2.5, 0.2, refr, verts=40)
    box("FurHood", FUR + Vector((0, 0, 6.5)), (3.0, 3.0, 2.5), shell)
    cyl("FurStack", FUR + Vector((0, 0, 10.5)), 0.7, 6.0, shell, verts=20)
    box("MouthFrame", FUR + Vector((0, -2.35, 1.5)), (1.8, 0.4, 1.6), painted_steel("Soot", (0.06, 0.055, 0.05), 0.8, 0.6))
    glow_m = molten("FurnaceGlow", 5.0)
    box("Mouth", FUR + Vector((0, -2.56, 1.45)), (1.25, 0.02, 1.05), glow_m)
    door = box("FurDoor", (0, 0, 0), (1.5, 0.15, 1.3), painted_steel("FurDoorM", (0.2, 0.18, 0.16), 0.6, 0.5), bevel=0.02)
    c["door"] = door; c["door_closed"] = FUR + Vector((0, -2.7, 1.45))
    fl = bpy.data.lights.new("FurnaceLight", 'SPOT'); fl.spot_size = math.radians(120); fl.spot_blend = 0.8; fl.shadow_soft_size = 0.5; fl.color = (1.0, 0.45, 0.12)
    d = fl.driver_add("energy").driver; d.type = 'SCRIPTED'; d.expression = "%d * (0.85 + 0.15 * sin(frame * 0.9) * sin(frame * 0.31))" % (1600 if v == "hot" else 0)
    fo = bpy.data.objects.new("FurnaceLight", fl); bpy.context.collection.objects.link(fo); fo.location = FUR + Vector((0, -3.3, 1.45)); fo.rotation_euler = (math.radians(90), 0, 0)
    fo.visible_camera = False; fo.visible_glossy = False
    c["fur_light"] = fo
    if v != "hot":
        glow_m.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = 1.5
    # ladle on a crane hook and the mould row
    lad = join([cyl("Ladle", (0, 0, 0.6), 0.7, 1.2, shell, verts=28), cyl("LadleLip", (0.72, 0, 1.15), 0.15, 0.12, shell, verts=10, rot=(0, math.radians(90), 0)),
                cyl("LadleMelt", (0, 0, 1.12), 0.62, 0.05, molten("LadleMelt", 20.0 if v == "hot" else 0.5), verts=28)], "Ladle")
    piv = bpy.data.objects.new("LadlePivot", None); bpy.context.collection.objects.link(piv); piv.location = MOULDS + Vector((-1.4, 0, 2.4))
    lad.parent = piv; lad.location = (0, 0, -0.6); c["ladle"] = piv
    for sy in (-1, 1):
        cyl("Bail", MOULDS + Vector((-1.4, sy * 0.72, 3.4)), 0.03, 2.2, shell, verts=8)
    cyl("CraneRope", MOULDS + Vector((-1.4, 0, 9.0)), 0.03, 9.0, pbr("Rope", (0.05, 0.05, 0.05), 0.6), verts=6)
    box("CraneBeam", (0, MOULDS.y, H - 1.4), (W - 1, 0.6, 0.8), painted_steel("CraneBeam", (0.6, 0.45, 0.08), 0.5, 0.5))
    stream = cyl("PourStream", (0, 0, 0), 0.05, 1.0, molten("Stream", 30.0), verts=12)
    c["stream"] = stream
    mould_m = painted_steel("Mould", (0.1, 0.1, 0.1), 0.6, 0.8)
    c["moulds"] = []
    for k in range(8):
        p = MOULDS + Vector((k * 0.9, 0, 0))
        box("MouldBox", p + Vector((0, 0, 0.18)), (0.7, 0.45, 0.36), mould_m, bevel=0.02)
        fillm = box("MouldFill", p + Vector((0, 0, 0.33)), (0.6, 0.35, 0.02), molten(f"Ingot{k}", 12.0 if (v == "hot" and k < 3) else 0.0))
        c["moulds"].append(p)
    # stacked cold ingots (Ch4)
    ing = painted_steel("Ingot", (0.12, 0.12, 0.13), 0.45, 0.9)
    pr = box("IngotP", (0, 0, -40), (0.6, 0.18, 0.12), ing, bevel=0.02)
    for row in range(6):
        for k in range(6):
            instance(pr, (-9.0 + k * 0.62 * (1 if row % 2 else 1), -4.0 + (0.2 * (row % 2)), 0.06 + row * 0.12), rot=(0, 0, (row % 2) * math.pi / 2))
    # scrap waiting to be charged, a skip, a shovel
    kit_ = scrap_kit(rng)
    hf = lambda x, y: max(0.0, 1.4 * (1 - math.hypot((x + 4.5) / 3.2, (y - 6.0) / 2.4)))
    L_, R_, S_, I_ = scrap_points(kit_, hf, -4.5, 6.0, 3.0, 220, rng, scl=(0.4, 0.8), exclude=("CarShell", "Fridge", "WashingMachine"))
    gn_instances("ChargeScrap", [p for p, w in kit_], L_, R_, S_, I_)
    c["sparks"] = sparks("Spark", 80, color=(1.0, 0.55, 0.15))
    sp_root, _ = ph_model("rusted_spade_01"); c["spade"] = sp_root
    c["charge"] = join([box("ChPlate", (0, 0, 0), (0.6, 0.4, 0.02), rust_mat("ChRust")), cyl("ChPipe", (0.1, 0, 0.05), 0.04, 0.6, rust_mat("ChRust2"), verts=8, rot=(0, 1.4, 0.3))], "Charge")
    P = {}
    P["w1"] = person("Smelter1", 1.0, 40, "charcoal", "short03", hat="flat", hat_col=(0.15, 0.13, 0.11), moustache=True)
    P["w2"] = person("Smelter2", 1.0, 31, "wool_brown", "short02", hat="knit", hat_col=(0.1, 0.1, 0.12))
    if v == "cold":
        P["spec"] = person("SmeltSpec", 1.0, 44, "overall_white", "short03", dosimeter=True, moustache=True)
        P["guide"] = person("SmeltGuide", 1.0, 55, "suit_brown", "short02", hv=0.6, moustache=True)
    c["people"] = P
    for h in P.values():
        place(h, (0, -100, 0), 0)
    if v == "cold":
        c["det"] = __import__("sc_scrapyard").detector("SmeltDet")
    return c


def walk_to(h, a, b, sec, speed=1.0, stride=1.25):
    a = Vector(a); b = Vector(b); d = b - a; L_ = d.length; s = min(L_, max(0.0, speed * sec))
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h)
    moving = 0 < s < L_; ph_ = (s / stride) % 1.0 if moving else 0.0
    pose_walk(h, ph_, stride=24 if moving else 0, arm_swing=0); arms_relaxed(h, ph_, 14 if moving else 0)
    p = a + d.normalized() * s; place(h, (p.x, p.y, 0), face_angle(a, b)); return p


def door_open(c, k):
    c["door"].location = c["door_closed"] + Vector((0, 0, 1.25 * k))


def C(p0, p1, tgt, lens):
    return lambda c, t: (Vector(p0).lerp(Vector(p1), ease(t)), Vector(tgt), lens)


def c1_14a(c, t):          # the furnace door opens; the glow lights two workers feeding scrap
    sec = t * dur("ch1_14a")
    k = ease(min(1.0, sec / 1.2)); door_open(c, k)
    for j, (nm, off, ph_) in enumerate((("w1", (-1.3, -4.2), 0.0), ("w2", (1.2, -4.0), 1.3))):
        h = c["people"][nm]; st = FUR + Vector((*off, 0)); stand_pose(h); place(h, st, face_angle(st, FUR + Vector((0, -2.2, 0))))
        cyc = (sec / 1.7 + ph_) % 1.0; q = 0.5 - 0.5 * math.cos(2 * math.pi * cyc)
        f = forward(h); sd = f.cross(Vector((0, 0, 1)))
        blade = (st + f * 0.8 + Vector((0, 0, 0.1))).lerp(FUR + Vector((0, -2.4, 1.2)), q)
        handle = blade + (st + Vector((0, 0, 1.0)) - blade).normalized() * 0.95
        h.rot("spine03", sd, -(10 + 18 * (1 - q)))
        reach(h, "R", handle, Vector((sd.x, sd.y, -0.6)), blade - handle); reach(h, "L", handle.lerp(blade, 0.45), Vector((-sd.x, -sd.y, -0.6)), blade - handle)
        fingers_curl(h, 70, thumb=40)
        if j == 0 and c["spade"] is not None:
            sp = c["spade"]; sp.location = blade + (handle - blade).normalized() * 0.5; sp.rotation_mode = 'QUATERNION'; sp.rotation_quaternion = (blade - handle).to_track_quat('Z', 'Y')
            c["charge"].location = blade + Vector((0, 0, 0.05))
    pose_sparks(c["sparks"], FUR + Vector((0, -2.5, 1.2)), sec, direction=Vector((0, -1, 0.6)), spread=1.2)
    c["stream"].location = (0, -100, 0)


def c1_14b(c, t):          # the ladle tips and pours into the moulds in a sheet of sparks
    sec = t * dur("ch1_14b")
    door_open(c, 1)
    k = ease(min(1.0, sec / 1.4))
    piv = c["ladle"]; piv.location = MOULDS + Vector((-1.4 + 0.25 * sec, 0, 2.4)); piv.rotation_euler = (0, math.radians(-55 * k), 0)
    bpy.context.view_layer.update()
    lip = piv.matrix_world @ Vector((0.85, 0, 0.55))
    target = Vector((lip.x + 0.15, MOULDS.y, 0.36))
    st = c["stream"]
    if k > 0.6:
        st.location = (lip + target) / 2; st.scale = (1, 1, (lip - target).length); st.rotation_mode = 'QUATERNION'; st.rotation_quaternion = (lip - target).to_track_quat('Z', 'Y')
    else:
        st.location = (0, -100, 0)
    pose_sparks(c["sparks"], target, sec, direction=Vector((0.3, -0.6, 0.8)), spread=1.6, on=k > 0.6)
    h = c["people"]["w1"]; stand_pose(h, crossed=True); place(h, MOULDS + Vector((2.5, -2.6, 0)), face_angle(MOULDS + Vector((2.5, -2.6, 0)), target))


def c4_6a(c, t):           # cold hall: a specialist walks past the furnaces with a detector
    sec = t * dur("ch4_6a")
    door_open(c, 0)
    h = c["people"]["spec"]
    walk_to(h, FUR + Vector((-6.0, -5.5, 0)), FUR + Vector((4.0, -5.5, 0)), sec, speed=0.6, stride=1.0)
    from sc_scrapyard import hold_detector
    hold_detector(c, h, sec, sweep=sec * 1.3, level=0.08)
    walk_to(c["people"]["guide"], FUR + Vector((-7.0, -6.6, 0)), FUR + Vector((3.0, -6.6, 0)), sec - 0.3, speed=0.6)
    c["stream"].location = (0, -100, 0); pose_sparks(c["sparks"], (0, 0, -50), 0, on=False)


def c4_6b(c, t):           # his needle rests near zero beside a stack of fresh ingots
    sec = t * dur("ch4_6b")
    door_open(c, 0)
    h = c["people"]["spec"]; st = Vector((-7.6, -2.6, 0)); stand_pose(h); place(h, st, face_angle(st, Vector((-7.6, -4.0, 0))))
    from sc_scrapyard import hold_detector
    hold_detector(c, h, sec, sweep=0.4 * math.sin(sec), level=0.06)
    c["stream"].location = (0, -100, 0); pose_sparks(c["sparks"], (0, 0, -50), 0, on=False)


SHOTS = {
    "ch1_14a": ("hot", c1_14a, C(FUR + Vector((3.2, -9.5, 1.3)), FUR + Vector((2.6, -8.8, 1.4)), FUR + Vector((0, -3.0, 1.4)), 30), None),
    "ch1_14b": ("hot", c1_14b, C(MOULDS + Vector((4.5, -5.0, 1.0)), MOULDS + Vector((3.8, -4.4, 1.1)), MOULDS + Vector((0.5, 0, 0.9)), 32), None),
    "ch4_6a": ("cold", c4_6a, C(FUR + Vector((5.0, -12.0, 1.5)), FUR + Vector((4.0, -11.5, 1.5)), FUR + Vector((-1.0, -5.5, 1.3)), 30), None),
    "ch4_6b": ("cold", c4_6b, C(Vector((-5.8, -5.6, 1.4)), Vector((-6.1, -5.3, 1.4)), Vector((-7.6, -3.0, 1.0)), 35), 2.8),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}
MOVES = {k: dict(kind="anim", far=100.0, anim=v[1], cam=v[2], dof=v[3]) for k, v in SHOTS.items()}
