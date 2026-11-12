"""Paper and storage: the company's Ankara office (a clerk stamping a document), its dusty storeroom (grey
packages on pallets; later empty), and the investigators' records room (two ledgers compared side by side).
No readable text: ledgers carry generic ruled columns only."""
import math
import numpy as np
import bpy
from mathutils import Vector, Euler
from kit import *
from rs_kit import *
from rs_env import sky
from human import reset_pose, pose_walk, reach, fingers_curl, pose_sit
from durs import dur

EXPOSURE = 0.0
BOUNCES = 8
OFF = Vector((0, 0, 0))           # Ankara office
STO = Vector((20, 0, 0))          # storeroom
REC = Vector((-20, 0, 0))         # records room


def ledger_material(name, seed=0.0):
    """Ruled ledger page: faint blue rules, a red margin line, and blocks of dark 'ink' in columns (no glyphs)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs['UV'], sep.inputs[0])
    rows = N.new("ShaderNodeMath"); rows.operation = 'MULTIPLY'; rows.inputs[1].default_value = 34; L.new(sep.outputs['Y'], rows.inputs[0])
    fr = N.new("ShaderNodeMath"); fr.operation = 'FRACT'; L.new(rows.outputs[0], fr.inputs[0])
    rule = N.new("ShaderNodeMath"); rule.operation = 'LESS_THAN'; rule.inputs[1].default_value = 0.06; L.new(fr.outputs[0], rule.inputs[0])
    flo = N.new("ShaderNodeMath"); flo.operation = 'FLOOR'; L.new(rows.outputs[0], flo.inputs[0])
    cols = N.new("ShaderNodeMath"); cols.operation = 'MULTIPLY'; cols.inputs[1].default_value = 5; L.new(sep.outputs['X'], cols.inputs[0])
    cfl = N.new("ShaderNodeMath"); cfl.operation = 'FLOOR'; L.new(cols.outputs[0], cfl.inputs[0])
    cfr = N.new("ShaderNodeMath"); cfr.operation = 'FRACT'; L.new(cols.outputs[0], cfr.inputs[0])
    cxy = N.new("ShaderNodeCombineXYZ"); L.new(cfl.outputs[0], cxy.inputs[0]); L.new(flo.outputs[0], cxy.inputs[1]); cxy.inputs[2].default_value = seed
    wn = N.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'; L.new(cxy.outputs[0], wn.inputs['Vector'])
    lenv = N.new("ShaderNodeMath"); lenv.operation = 'MULTIPLY_ADD'; lenv.inputs[1].default_value = 0.6; lenv.inputs[2].default_value = 0.2
    L.new(wn.outputs['Value'], lenv.inputs[0])
    ink = N.new("ShaderNodeMath"); ink.operation = 'LESS_THAN'; L.new(cfr.outputs[0], ink.inputs[0]); L.new(lenv.outputs[0], ink.inputs[1])
    band = N.new("ShaderNodeMath"); band.operation = 'GREATER_THAN'; band.inputs[1].default_value = 0.3; L.new(fr.outputs[0], band.inputs[0])
    band2 = N.new("ShaderNodeMath"); band2.operation = 'LESS_THAN'; band2.inputs[1].default_value = 0.7; L.new(fr.outputs[0], band2.inputs[0])
    i1 = N.new("ShaderNodeMath"); i1.operation = 'MULTIPLY'; L.new(ink.outputs[0], i1.inputs[0]); L.new(band.outputs[0], i1.inputs[1])
    i2 = N.new("ShaderNodeMath"); i2.operation = 'MULTIPLY'; L.new(i1.outputs[0], i2.inputs[0]); L.new(band2.outputs[0], i2.inputs[1])
    paper = N.new("ShaderNodeMix"); paper.data_type = 'RGBA'; L.new(rule.outputs[0], paper.inputs['Factor'])
    paper.inputs[6].default_value = (0.86, 0.83, 0.74, 1); paper.inputs[7].default_value = (0.55, 0.62, 0.75, 1)
    out = N.new("ShaderNodeMix"); out.data_type = 'RGBA'; L.new(i2.outputs[0], out.inputs['Factor'])
    L.new(paper.outputs[2], out.inputs[6]); out.inputs[7].default_value = (0.08, 0.08, 0.12, 1)
    L.new(out.outputs[2], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.85
    return m


def ledger(name, loc, rot_z):
    """Open ledger: two page planes on a cloth spine; a loose page hinged at the spine that can lift."""
    cover = pbr(name + "Cover", (0.25, 0.12, 0.08), 0.6)
    base = join([box("CoverL", (-0.21, 0, 0.005), (0.42, 0.32, 0.01), cover), box("CoverR", (0.21, 0, 0.005), (0.42, 0.32, 0.01), cover)], name)
    base.location = loc; base.rotation_euler = (0, 0, rot_z)
    for side in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        pg = bpy.context.active_object; pg.scale = (0.4, 0.3, 1); pg.data.materials.append(ledger_material(name + f"Page{side}", seed=hash(name) % 97 + side))
        pg.parent = base; pg.location = (side * 0.205, 0, 0.022)
    hinge = bpy.data.objects.new(name + "Leaf", None); bpy.context.collection.objects.link(hinge); hinge.parent = base; hinge.location = (0, 0, 0.024)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    lf = bpy.context.active_object; lf.scale = (0.4, 0.3, 1); lf.data.materials.append(ledger_material(name + "Leaf", seed=7)); lf.parent = hinge; lf.location = (0.2, 0, 0)
    return base, hinge


def build(variant=None):
    c = {}
    v = variant or "office"
    sky("overcast")
    parq = ph_mat("herringbone_parquet", 0.8, (0.4, 0.28, 0.18), name="Parquet")
    conc = ph_mat("concrete_floor_worn_001", 0.08, (0.4, 0.4, 0.38), name="StoreFloor")
    # ---------------- Ankara office
    room("Office", OFF, 5.5, 4.5, 3.0, parq, two_tone("OffWall", (0.5, 0.45, 0.36), (0.8, 0.76, 0.66)), windows=[("N", 0.8, 1.0, 1.6, 1.5)])
    daylight_window(OFF + Vector((0.8, 2.35, 1.75)), "N", (1.6, 1.5), energy=650)
    ph_model("metal_office_desk", loc=OFF + Vector((0, 0.4, 0)), rot_z=math.pi)
    lamp_root, _ = ph_model("desk_lamp_arm_01", loc=OFF + Vector((-0.45, 0.55, 0.76)), rot_z=math.radians(150))
    l = bpy.data.lights.new("DeskLamp", 'SPOT'); l.energy = 60; l.color = (1.0, 0.82, 0.6); l.spot_size = math.radians(70); l.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("DeskLamp", l); bpy.context.collection.objects.link(lo); lo.location = OFF + Vector((-0.2, 0.4, 1.25))
    paper = pbr("Paper", (0.85, 0.83, 0.76), 0.85)
    c["doc"] = box("Document", OFF + Vector((0.05, 0.35, 0.775)), (0.21, 0.3, 0.002), ledger_material("DocPage", 3))
    for k in range(4):
        box("PaperStack", OFF + Vector((0.45 + 0.01 * k, 0.5, 0.775 + 0.004 * k)), (0.21, 0.3, 0.003), paper, rot=(0, 0, 0.05 * k))
    c["stamp"] = join([cyl("StampBase", (0, 0, 0.02), 0.025, 0.03, pbr("StampRubber", (0.1, 0.05, 0.03), 0.6), verts=16),
                       cyl("StampHandle", (0, 0, 0.08), 0.015, 0.09, wood("StampWood", (0.15, 0.08, 0.04), (0.35, 0.2, 0.1)), verts=12)], "Stamp")
    c["stamp_rest"] = OFF + Vector((0.3, 0.25, 0.775))
    box("InkPad", OFF + Vector((0.32, 0.12, 0.785)), (0.1, 0.07, 0.015), pbr("InkPad", (0.1, 0.1, 0.25), 0.4))
    filing_cabinet(OFF + Vector((2.4, -1.4, 0)), math.pi / 2, (0.5, 0.48, 0.42), name="OffFCside")
    for k in range(3):                                   # a row of steel filing cabinets on the back wall
        filing_cabinet(OFF + Vector((-2.2 + 0.5 * k, -1.88, 0)), 0.0, (0.42, 0.45, 0.42) if k != 1 else (0.5, 0.48, 0.42), name=f"OffFC{k}")
    for k in range(3):
        box("Binder", OFF + Vector((-2.35 + 0.08 * k, -1.85, 1.44)), (0.06, 0.28, 0.3), pbr(f"BinderM{k}", [(0.15, 0.2, 0.4), (0.4, 0.1, 0.08), (0.2, 0.3, 0.2)][k], 0.6))
    # a framed portrait shape on the wall (no face: a soft sepia blur), a wall clock, a coat stand
    box("PortraitFrame", OFF + Vector((0.6, -2.22, 2.0)), (0.5, 0.04, 0.62), wood("FrameWood", (0.2, 0.12, 0.06), (0.35, 0.22, 0.1)))
    box("PortraitPanel", OFF + Vector((0.6, -2.2, 2.0)), (0.4, 0.02, 0.52), noisy("PortraitSepia", (0.45, 0.38, 0.28), 0.8, dirt=0.6, scale=1.5, dark=0.6))
    cyl("WallClock", OFF + Vector((-1.0, -2.22, 2.2)), 0.16, 0.04, pbr("ClockFace", (0.9, 0.88, 0.82), 0.4), verts=32, rot=(math.radians(90), 0, 0))
    cyl("CoatStand", OFF + Vector((2.2, 1.6, 0.9)), 0.02, 1.8, wood("CoatWood", (0.2, 0.12, 0.06), (0.35, 0.22, 0.1)), verts=8)
    box("Coat", OFF + Vector((2.2, 1.55, 1.3)), (0.4, 0.2, 0.8), fabric("CoatF", (0.18, 0.16, 0.15), 0.95, 0.4, 300), bevel=0.08)
    ph_model("SchoolChair_01", loc=OFF + Vector((0.0, -0.25, 0)), rot_z=0.0)
    tube_light(OFF + Vector((0, 0, 2.95)), energy=80)
    # ---------------- storeroom (dusty): steel shelving, boxes, pallets with grey packages, a swinging lamp
    room("Store", STO, 6, 14, 3.4, conc, two_tone("StoreWall", (0.45, 0.45, 0.42), (0.62, 0.6, 0.55), split=1.0), windows=[("E", 3.5, 2.2, 1.2, 0.6)])
    daylight_window(STO + Vector((3.1, 3.5, 2.5)), "E", (1.2, 0.6), energy=1500)
    tube_light(STO + Vector((0, -3.5, 3.35)), energy=160)
    tube_light(STO + Vector((0, 1.5, 3.35)), energy=200)
    for k in range(4):
        ph_model("steel_frame_shelves_01", loc=STO + Vector((-2.4, -5.0 + k * 2.6, 0)), rot_z=math.radians(90))
    for k in range(10):
        ph_model("cardboard_box_01", loc=STO + Vector((-2.4 + 0.2 * (k % 2), -5.4 + k * 1.1, 0.05 + 0.9 * (k % 3))), rot_z=0.3 * k)
    pal_m = noisy("PalletWood", (0.42, 0.32, 0.2), 0.85, dirt=0.6, scale=5)
    c["packages"] = []
    for k in range(2):
        pp = STO + Vector((1.0, 4.0 + k * 1.6, 0))
        box("Pallet", pp + Vector((0, 0, 0.07)), (1.2, 1.2, 0.14), pal_m)
        if v == "full":
            o, kk = container(f"Pkg{k}"); o.location = pp + Vector((0, 0, 0.14)); kk["trefoil"].hide_render = True
            crate(f"PkgCrate{k}", loc=pp + Vector((0, 0, 0.14)))
            c["packages"].append(o)
    box("Pallet", STO + Vector((1.0, -1.0, 0.07)), (1.2, 1.2, 0.14), pal_m)
    swing = bpy.data.objects.new("LampSwing", None); bpy.context.collection.objects.link(swing); swing.location = STO + Vector((1.0, 3.5, 3.4))
    cord = cyl("LampCord", (0, 0, 0), 0.005, 1.1, pbr("CordM", (0.02, 0.02, 0.02), 0.6), verts=6); cord.parent = swing; cord.location = (0, 0, -0.55)
    shade = join([cyl("Shade", (0, 0, 0), 0.18, 0.12, painted_steel("ShadeM", (0.25, 0.3, 0.28), 0.4, 0.5), verts=20)], "LampShade"); shade.parent = swing; shade.location = (0, 0, -1.15)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.04, location=(0, 0, 0))
    bulb = bpy.context.active_object; bulb.data.materials.append(pbr("SBulb", (1, 1, 1), 0.2, 0.0, **{'Emission Color': (1.0, 0.78, 0.5, 1), 'Emission Strength': 18.0})); bulb.parent = swing; bulb.location = (0, 0, -1.22)
    sl = bpy.data.lights.new("StoreBulb", 'SPOT'); sl.energy = 1400; sl.color = (1.0, 0.78, 0.5); sl.spot_size = math.radians(110); sl.spot_blend = 0.7
    so = bpy.data.objects.new("StoreBulb", sl); bpy.context.collection.objects.link(so); so.parent = swing; so.location = (0, 0, -1.25)
    c["swing"] = swing
    haze(STO + Vector((0, 0, 1.7)), (5.8, 13.8, 3.3), density=0.004, color=(0.85, 0.8, 0.72), anis=0.5)
    # ---------------- records room: two ledgers side by side under a lamp, a window draught
    room("Records", REC, 5.0, 4.5, 3.0, parq, two_tone("RecWall", (0.35, 0.42, 0.45), (0.78, 0.76, 0.7)), windows=[("W", 0.0, 1.0, 1.4, 1.5)])
    daylight_window(REC + Vector((-2.6, 0, 1.75)), "W", (1.4, 1.5), energy=1800)
    tube_light(REC + Vector((0.8, 1.2, 2.95)), energy=90)
    tab = wood("RecTable", (0.1, 0.06, 0.035), (0.28, 0.16, 0.09), rough=0.5, coat=0.3)
    box("RecTableTop", REC + Vector((0, 0, 0.76)), (1.8, 1.0, 0.04), tab)
    for dx in (-0.85, 0.85):
        for dy in (-0.45, 0.45):
            box("RecLeg", REC + Vector((dx, dy, 0.38)), (0.05, 0.05, 0.76), tab)
    c["ledA"], c["leafA"] = ledger("LedgerA", REC + Vector((-0.45, 0.0, 0.78)), 0.03)
    c["ledB"], c["leafB"] = ledger("LedgerB", REC + Vector((0.45, 0.02, 0.78)), -0.02)
    for k in range(2):
        ph_model("SchoolChair_01", loc=REC + Vector((-0.5 + k * 1.0, -0.95, 0)), rot_z=0.0)
    pend = bpy.data.lights.new("RecLamp", 'SPOT'); pend.energy = 380; pend.color = (1.0, 0.85, 0.65); pend.spot_size = math.radians(80); pend.spot_blend = 0.6
    po = bpy.data.objects.new("RecLamp", pend); bpy.context.collection.objects.link(po); po.location = REC + Vector((0, 0, 2.2))
    cone = bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.25, radius2=0.04, depth=0.2, location=REC + Vector((0, 0, 2.3)))
    bpy.context.active_object.data.materials.append(painted_steel("RecShade", (0.2, 0.28, 0.25), 0.4, 0.5))
    cyl("RecCord", REC + Vector((0, 0, 2.65)), 0.005, 0.7, pbr("CordM2", (0.02, 0.02, 0.02), 0.6), verts=6)
    ph_model("wooden_bookshelf_worn", loc=REC + Vector((1.6, 2.0, 0)), rot_z=math.pi)
    P = {}
    P["clerk"] = person("Clerk", 1.0, 52, "suit_brown", "short03", hv=0.55, moustache=True)
    P["inv"] = person("InvA", 1.0, 48, "camel", "short03", moustache=True)
    P["inv2"] = person("InvB", 0.0, 41, "woman_coat", "bob02", hv=0.2)
    c["people"] = P
    for h in P.values():
        place(h, (0, -150, 0), 0)
    import rs_env as _rs_env
    _rs_env.cinematic(c, __name__)        # house cinematic look (look.py)
    return c


def C(p0, p1, tgt, lens):
    return lambda c, t: (Vector(p0).lerp(Vector(p1), ease(t)), Vector(tgt), lens)


def sit_at(h, loc, look, lean=10):
    h.arm.rotation_euler = (0, 0, 0); h.arm.location = (0, 0, 0); reset_pose(h); pose_sit(h, lean=lean)
    place(h, Vector((loc[0], loc[1], 0.0)), face_angle(loc, look))


def c2_12a(c, t):          # the clerk stamps a document under the desk lamp (medium, person in frame)
    sec = t * dur("ch2_12a"); h = c["people"]["clerk"]
    sit_at(h, OFF + Vector((0.0, -0.2, 0.45)), OFF + Vector((0, 1, 0)), lean=20)
    sd = forward(h).cross(Vector((0, 0, 1)))
    cyc = (sec / 1.3) % 1.0; k = math.sin(math.pi * min(1.0, cyc * 1.6)) if cyc < 0.62 else 0.0
    sp = c["doc"].location + Vector((0.02, 0.0, 0.002 + 0.16 * (1 - k)))
    c["stamp"].location = sp
    reach(h, "R", sp + Vector((0, 0, 0.14)), Vector((sd.x, sd.y, -0.7)), Vector((0, 0, -1)))
    reach(h, "L", c["doc"].location + Vector((-0.16, -0.12, 0.03)), Vector((-sd.x, -sd.y, -1.0)), forward(h))
    fingers_curl(h, 40, thumb=30)
    h.rot("head", sd, -12)


def c2_12b(c, t):
    pass


def c4_9a(c, t):           # an investigator stands in the empty storeroom
    sec = t * dur("ch4_9a"); h = c["people"]["inv"]
    stand_pose(h, hands_pockets=True); place(h, STO + Vector((0.2, 2.0, 0)), face_angle(STO + Vector((0.2, 2.0, 0)), STO + Vector((1.0, 4.8, 0))))
    h.rot("head", (0, 0, 1), 6 * math.sin(sec * 0.5))
    c["swing"].rotation_euler = (math.radians(3 * math.sin(sec * 1.6)), 0, 0)


def c4_9b(c, t):           # the light over the empty pallets swings in the draught
    sec = t * dur("ch4_9b")
    c["swing"].rotation_euler = (math.radians(9 * math.sin(sec * 1.7)), math.radians(3 * math.sin(sec * 1.1)), 0)


def lap_hands(h, sides=("L", "R")):
    """Seated, hands resting on the thighs."""
    f = forward(h); sd = f.cross(Vector((0, 0, 1))).normalized()
    for S_ in sides:
        hip = h.bone_head(f"upperleg01.{S_}"); knee = h.bone_head(f"lowerleg01.{S_}")
        p = hip.lerp(knee, 0.3) + Vector((0, 0, 0.13)) - sd * (0.06 if S_ == "R" else -0.06)
        sg = 1 if S_ == "R" else -1
        reach(h, S_, p, Vector((sd.x * sg, sd.y * sg, -0.6)) + f * -0.4, f + Vector((0, 0, -0.3)))
    fingers_curl(h, 25, thumb=15)


def investigators(c, sec, lean_back=0.0):
    a = c["people"]["inv"]; b = c["people"]["inv2"]
    sit_at(a, REC + Vector((-0.5, -0.95, 0.45)), REC + Vector((-0.5, 0, 0)), lean=18 - 30 * lean_back)
    sit_at(b, REC + Vector((0.5, -0.95, 0.45)), REC + Vector((0.5, 0, 0)), lean=20)
    arms_crossed(a); arms_crossed(b)
    return a, b


def c4_7a(c, t):           # two investigators lay the two ledgers side by side (medium): one squares a ledger, one waits
    sec = t * dur("ch4_7a"); a, b = investigators(c, sec)
    k = ease(min(1.0, sec / 1.8))
    c["ledB"].location = REC + Vector((0.45 + 0.5 * (1 - k), 0.02 + 0.3 * (1 - k), 0.78))
    sd = forward(b).cross(Vector((0, 0, 1)))
    edge = c["ledB"].location + Vector((0, -0.2, 0.04))
    reach(b, "R", edge + sd * 0.12, Vector((sd.x, sd.y, -1.0)), forward(b)); reach(b, "L", edge - sd * 0.12, Vector((-sd.x, -sd.y, -1.0)), forward(b))
    fingers_curl(b, 30, thumb=20)
    arms_crossed(a)
    a.rot("head", forward(a).cross(Vector((0, 0, 1))), -16); b.rot("head", sd, -14)


def c4_7b(c, t):           # the ledger pages lift in a draught from the window
    sec = t * dur("ch4_7b"); investigators(c, sec)
    for k, lf in enumerate((c["leafA"], c["leafB"])):
        lf.rotation_euler = (0, -math.radians(max(0.0, 35 * math.sin(sec * 1.2 + k * 1.3) ** 2)), 0)


def c4_8a(c, t):           # one investigator leans back and shakes his head; the other keeps his hands in his lap
    sec = t * dur("ch4_8a"); a, b = investigators(c, sec, lean_back=ease(min(1.0, sec / 1.2)))
    arms_crossed(a)
    if sec > 1.2:
        a.rot("head", (0, 0, 1), 14 * math.sin((sec - 1.2) * 5.0) * max(0.0, 1 - (sec - 1.2) / 2.0))
    lap_hands(b)


def c4_8b(c, t):
    sec = t * dur("ch4_8b"); investigators(c, sec)


SHOTS = {
    "ch2_12a": ("office", c2_12a, C(OFF + Vector((2.3, 1.9, 1.65)), OFF + Vector((2.1, 1.75, 1.65)), OFF + Vector((-0.2, -0.6, 1.1)), 26), 2.8),
    "ch2_12b": ("full", c2_12b, C(STO + Vector((0.6, -6.2, 1.6)), STO + Vector((0.8, 0.0, 1.4)), STO + Vector((1.0, 4.8, 0.7)), 30), 4.0),
    "ch4_9a": ("empty", c4_9a, C(STO + Vector((2.0, -3.2, 1.5)), STO + Vector((1.9, -2.6, 1.5)), STO + Vector((0.4, 2.4, 1.3)), 32), 4.0),
    "ch4_9b": ("empty", c4_9b, C(STO + Vector((2.3, 0.6, 0.9)), STO + Vector((2.2, 1.0, 0.95)), STO + Vector((1.0, 4.0, 1.8)), 28), None),
    "ch4_7a": ("office", c4_7a, C(REC + Vector((1.6, 1.6, 1.7)), REC + Vector((1.4, 1.4, 1.7)), REC + Vector((0.0, -0.3, 0.95)), 32), 2.8),
    "ch4_7b": ("office", c4_7b, C(REC + Vector((0.9, 0.9, 1.25)), REC + Vector((0.7, 0.75, 1.2)), REC + Vector((0.0, 0.0, 0.8)), 40), 2.0),
    "ch4_8a": ("office", c4_8a, C(REC + Vector((-1.4, 1.5, 1.5)), REC + Vector((-1.25, 1.35, 1.5)), REC + Vector((-0.5, -0.9, 1.15)), 35), 2.8),
    "ch4_8b": ("office", c4_8b, C(REC + Vector((0.0, -0.6, 1.5)), REC + Vector((0.0, -0.25, 1.15)), REC + Vector((0.0, 0.0, 0.79)), 40), 2.0),
}
VARIANT_FOR = {k: v[0] for k, v in SHOTS.items()}
DUR = {k: dur(k) for k in SHOTS}
MOVES = {k: dict(kind="anim", far=60.0, anim=v[1], cam=v[2], dof=v[3]) for k, v in SHOTS.items()}
