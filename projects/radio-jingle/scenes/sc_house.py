"""HOUSE: the family house in Eching, 1981 (built once, reused with new angles in every chapter).

Layout (metres, ground floor z = 0, ceiling 2.6):
  hallway   x[-1.1, 1.1]  y[-3.5, 3.5]   front door (frosted glass) in the south wall; stairs up the east side from y = 0.2;
            phone table on the east wall at y = -1.35 (rotary phone; police recorder in the "police" variants),
            hall chair with the stuffed toys at y = -2.4, Black Forest wall clock above at y = -0.6
  piano room x[-6.6, -1.1] y[-3.5, 3.5]  upright piano on the north wall (players face +Y), windows west and south,
            doorway to the hall at y[-1.7, -0.6]
  kitchen   x[-2.6, 2.6]  y[3.5, 7.5]    table at (0, 5.5), window over the sink in the north wall with the radio on the sill,
            doorway from the hall at x[-0.95, -0.1]
Garden ground outside, a neighbour's house and trees beyond the windows.

Variants: "<light>" or "<light>+police" ; light = morning | afternoon | sunset | dusk | night
Chat B: import this module and add MOVES with new angles (build(variant) returns every object in ctx).
"""
import math, os
import numpy as np
import bpy
from mathutils import Vector, Matrix
from kit import pbr, box, cyl, join, glass, emissive, area_light, point_at, fabric
from common import ease
import ph
import rj
from rj import mat, wall_x, wall_y, window_unit, door_leaf, person, stand, seat, walk, work, forward, upright, reach, fingers_curl, SIDE

EXPOSURE = 0.0
BOUNCES = 6
CEIL = 2.6
T_EXT, T_INT = 0.3, 0.12
PHONE_T = Vector((0.82, -1.35, 0.0))         # phone table (against the east wall), top at z 0.78
PIANO = Vector((-3.8, 2.88, 0.0))
KTABLE = Vector((0.0, 5.45, 0.0))

DUR = {}


def _light(variant):
    return (variant or "morning").split("|")[0].split("+")[0].split("@")[0]


def build(variant=None):
    variant = variant or "morning"
    light = _light(variant); police = "+police" in variant.split("|")[0]
    c = dict(variant=variant, light=light, police=police)
    # ---------------------------------------------------------------- shell
    pl = mat("plaster"); hall_m = mat("paper_hall"); liv_m = mat("paper"); ext = mat("plaster_ext")
    box("FloorHall", (0, 0, -0.01), (2.2, 7.0, 0.02), mat("tiles"))
    box("FloorLiv", (-3.85, 0, -0.01), (5.5, 7.0, 0.02), mat("parquet"))
    box("FloorKit", (0, 5.5, -0.01), (5.2, 4.0, 0.02), mat("lino"))
    ceil = pbr("Ceiling", (0.62, 0.60, 0.55), 0.85)
    box("CeilLiv", (-3.85, 0, CEIL + 0.02), (5.5, 7.0, 0.04), ceil)
    box("CeilHall", (0, -1.7, CEIL + 0.02), (2.2, 3.6, 0.04), ceil)            # open over the stairs (stairwell)
    box("CeilHall2", (-0.5, 1.75, CEIL + 0.02), (1.2, 3.5, 0.04), ceil)
    box("CeilKit", (0, 5.5, CEIL + 0.02), (5.2, 4.0, 0.04), ceil)
    box("Upstairs", (0.6, 1.75, CEIL + 1.4), (1.2, 3.5, 0.04), ceil)
    # exterior walls with windows
    WL = [(-2.25, -0.85, 0.9, 2.15), (0.85, 2.25, 0.9, 2.15)]                 # west windows (along y)
    WS = [(-5.3, -3.6, 0.9, 2.15)]                                            # south window of the piano room
    c["walls"] = []
    c["walls"] += wall_y("WLivW", -3.5, 3.5, -6.6 - T_EXT / 2, 0, CEIL, T_EXT, liv_m, holes=WL)
    c["walls"] += wall_x("WLivS", -6.6 - T_EXT, -1.1, -3.5 - T_EXT / 2, 0, CEIL, T_EXT, liv_m, holes=WS)
    c["walls"] += wall_x("WLivN", -6.6 - T_EXT, -2.6, 3.5 + T_INT / 2, 0, CEIL, T_INT, liv_m)
    c["walls"] += wall_x("WLivN2", -2.6, -1.1, 3.5 + T_INT / 2, 0, CEIL, T_INT, liv_m)
    c["walls"] += wall_y("WHallW", -3.5, 3.5, -1.1 - T_INT / 2, 0, CEIL, T_INT, hall_m, holes=[(-1.7, -0.6, 0, 2.08)])
    c["walls"] += wall_y("WHallE", -3.5, 3.5, 1.1 + T_EXT / 2, 0, CEIL + 1.4, T_EXT, hall_m, holes=[(-3.1, -2.75, 1.0, 2.0)])
    c["walls"] += wall_x("WHallS", -1.1, 1.1 + T_EXT, -3.5 - T_EXT / 2, 0, CEIL, T_EXT, hall_m, holes=[(-0.48, 0.48, 0, 2.12), (0.62, 0.92, 0.9, 2.1)])
    c["walls"] += wall_x("WHallN", -1.1, 1.1, 3.5 + T_INT / 2, 0, CEIL, T_INT, hall_m, holes=[(-0.95, -0.12, 0, 2.08)])
    c["walls"] += wall_y("WKitW", 3.5, 7.5, -2.6 - T_EXT / 2, 0, CEIL, T_EXT, pl, holes=[(4.6, 5.9, 0.95, 2.1)])
    c["walls"] += wall_y("WKitE", 3.5, 7.5, 2.6 + T_EXT / 2, 0, CEIL, T_EXT, pl)
    c["walls"] += wall_x("WKitN", -2.6 - T_EXT, 2.6 + T_EXT, 7.5 + T_EXT / 2, 0, CEIL, T_EXT, pl, holes=[(-0.75, 0.75, 1.05, 2.15)])
    c["walls"] += wall_x("WKitS", 1.1, 2.6 + T_EXT, 3.5 + T_INT / 2, 0, CEIL, T_INT, pl)
    c["walls"] += wall_x("WStairN", 0.0, 1.1, 3.5 + T_INT / 2, CEIL, CEIL + 1.4, T_INT, hall_m)
    # skirting boards
    sk = mat("darkwood")
    for (x, y, sx, sy) in ((-6.59, 0, 0.02, 7.0), (-1.17, 0, 0.02, 7.0), (-1.03, 0, 0.02, 7.0), (1.09, 0, 0.02, 7.0)):
        box("Skirt", (x, y, 0.05), (sx, sy, 0.1), sk)
    # windows
    for (a, b, za, zb) in WL:
        window_unit('y', (a + b) / 2, b - a, -6.6 - T_EXT / 2, za, zb, inward=1)
    for (a, b, za, zb) in WS:
        window_unit('x', (a + b) / 2, b - a, -3.5 - T_EXT / 2, za, zb, inward=1)
    window_unit('x', 0.0, 1.5, 7.5 + T_EXT / 2, 1.05, 2.15, inward=-1)
    window_unit('y', 5.25, 1.3, -2.6 - T_EXT / 2, 0.95, 2.1, inward=1)
    window_unit('y', -2.925, 0.35, 1.1 + T_EXT / 2, 1.0, 2.0, inward=-1, curtains=False)
    # front door (frosted glass panel), the hall-to-room doorway frames
    c["front_door"] = door_leaf("FrontDoor", (-0.46, -3.5 - T_EXT / 2, 0.0), 0.92, 2.1, mat("oak"), axis='x', glass_panel=True)
    box("SideLight", (0.77, -3.5 - T_EXT / 2, 1.5), (0.3, 0.02, 1.2), mat("frosted"))
    for (x, y, sx, sy, h) in ((-1.1 - T_INT / 2, -1.7, T_INT + 0.04, 0.06, 2.12), (-1.1 - T_INT / 2, -0.6, T_INT + 0.04, 0.06, 2.12),
                              (-0.95, 3.5 + T_INT / 2, 0.06, T_INT + 0.04, 2.12), (-0.12, 3.5 + T_INT / 2, 0.06, T_INT + 0.04, 2.12)):
        box("DoorFrame", (x, y, h / 2), (sx, sy, h), mat("trim"))
    box("DoorHead", (-1.1 - T_INT / 2, -1.15, 2.1), (T_INT + 0.04, 1.16, 0.06), mat("trim"))
    box("DoorHead2", (-0.535, 3.5 + T_INT / 2, 2.1), (0.89, T_INT + 0.04, 0.06), mat("trim"))
    stairs(c)
    hall_props(c)
    piano_room(c)
    kitchen(c)
    exterior(c)
    lighting(c)
    cast(c)
    kitchen_extras(c)
    apply_look(c)
    if "+torches" in variant:
        c["out_torches"] = [rj.torch(f"OutTorch{k}", energy=80, cone=24) for k in range(3)]
    if c["police"] and "officer" in c["P"] and "hp" not in c:
        c["hp"] = rj.put_headphones(c["P"]["officer"], rj.headphones("Headphones"))
    rj.finish_scene()
    return c


def stairs(c):
    st = mat("oak"); n = 12; rise = (CEIL + 0.1) / n; run = 0.27
    for k in range(n):
        y0 = 0.25 + k * run
        box("Tread", (0.62, y0 + run / 2, rise * (k + 1) - 0.02), (0.96, run + 0.02, 0.04), st, bevel=0.004)
        box("Riser", (0.62, y0 + 0.01, rise * (k + 0.5)), (0.94, 0.02, rise), mat("trim"))
    # stringer wall side + banister on the open (west) side
    L_ = math.hypot(n * run, n * rise); ang = math.atan2(n * rise, n * run)
    box("Stringer", (0.13, 0.25 + n * run / 2, n * rise / 2 - 0.05), (0.05, L_, 0.25), st, rot=(ang, 0, 0))
    box("Rail", (0.13, 0.25 + n * run / 2, n * rise / 2 + 0.85), (0.06, L_, 0.05), mat("darkwood"), rot=(ang, 0, 0), bevel=0.01)
    for k in range(0, n, 1):
        y = 0.25 + (k + 0.5) * run
        box("Baluster", (0.13, y, rise * (k + 1) + 0.42), (0.025, 0.025, 0.84), mat("darkwood"))
    box("Newel", (0.13, 0.25, 0.55), (0.09, 0.09, 1.1), mat("darkwood"), bevel=0.01)
    c["stair_rise"] = rise; c["stair_run"] = run


def hall_props(c):
    # runner rug
    box("Runner", (-0.4, -1.2, 0.004), (0.8, 4.0, 0.008), fabric("Runner", (0.26, 0.10, 0.07), 0.95, 0.4, 300))
    # phone table: small dark-wood table with a shelf
    t = PHONE_T
    tw = mat("darkwood")
    parts = [box("PTop", (t.x, t.y, 0.76), (0.42, 1.0, 0.035), tw, bevel=0.005), box("PShelf", (t.x, t.y, 0.25), (0.38, 0.95, 0.02), tw)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box("PLeg", (t.x + sx * 0.17, t.y + sy * 0.45, 0.38), (0.035, 0.035, 0.76), tw))
    c["ptable"] = join(parts, "PhoneTable")
    ph_r, hs, dial = rj.rotary_phone("Phone")
    ph_r.location = (t.x + 0.02, t.y - 0.22, 0.778); ph_r.rotation_euler = (0, 0, -math.pi / 2 + 0.25)   # dial faces the hall (-X)
    c["phone"] = ph_r; c["handset"] = hs; c["dial"] = dial
    c["handset_rest"] = (hs.location.copy(), hs.rotation_euler.copy())
    # directory books, a notepad, a little brass lamp
    box("Book", (t.x + 0.05, t.y + 0.3, 0.27), (0.22, 0.3, 0.05), pbr("Directory", (0.55, 0.45, 0.2), 0.7))
    box("Notepad", (t.x - 0.02, t.y + 0.12, 0.783), (0.12, 0.17, 0.008), pbr("Pad", (0.82, 0.8, 0.72), 0.8))
    lamp_parts = [cyl("LBase", (0, 0, 0.012), 0.065, 0.024, pbr("BrassL", (0.6, 0.45, 0.2), 0.3, 1.0), 24),
                  cyl("LStem", (0, 0, 0.18), 0.009, 0.33, pbr("BrassL2", (0.6, 0.45, 0.2), 0.3, 1.0), 12)]
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.15, radius2=0.09, depth=0.17, location=(0, 0, 0.37))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("LampShade", (0.7, 0.55, 0.34), 0.7, 0.0, **{'Transmission Weight': 0.4,
                                                                    'Emission Color': (1.0, 0.65, 0.35, 1), 'Emission Strength': 0.0}))
    sol = sh.modifiers.new("s", 'SOLIDIFY'); sol.thickness = 0.003
    c["shade_mat"] = sh.data.materials[0]
    lamp_parts.append(sh)
    lamp = join(lamp_parts, "HallLamp"); lamp.location = (t.x + 0.06, t.y + 0.43, 0.778)
    c["hall_lamp"] = lamp
    # hall chair with the two stuffed toys
    ch_r, _ = rj.model_fit("WoodenChair_01", (0.72, -2.45, 0.0), rot_z=math.pi / 2, height=0.9)
    c["chair"] = ch_r
    bear = rj.teddy("Bear"); bear.location = (0.78, -2.5, 0.47); bear.rotation_euler = (0, 0, math.pi / 2 + 0.25)
    rab = rj.plush_rabbit("Rabbit"); rab.location = (0.76, -2.25, 0.47); rab.rotation_euler = (0, 0.12, math.pi / 2 - 0.3)
    c["toys"] = [bear, rab]
    # wall clock above the table, a mirror and coat hooks on the west wall
    ck, hands, pend = rj.wall_clock("HallClock")
    ck.location = (1.1 - 0.05, -0.55, 1.95); ck.rotation_euler = (0, 0, math.pi / 2)
    c["clock_hands"] = hands; c["pendulum"] = pend
    hands["h"].rotation_euler.y = math.radians(7.33 * 30); hands["m"].rotation_euler.y = math.radians(20 * 6)
    try:
        mr, _ = rj.model_fit("ornate_mirror_01", (-1.1 + 0.03, -2.4, 1.1), rot_z=-math.pi / 2, height=0.75)
    except Exception:
        pass
    box("CoatRail", (-1.09, -2.95, 1.75), (0.04, 0.7, 0.06), mat("darkwood"))
    coat = fabric("Coat", (0.12, 0.1, 0.08), 0.9, 0.3)
    for k, y in enumerate((-3.15, -2.85)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.17, depth=0.95, location=(-0.95, y, 1.25))
        co = bpy.context.active_object; co.scale = (0.55, 1.0, 1.0); co.data.materials.append(coat)
        bpy.ops.object.shade_smooth()
    # ceiling pendant over the hall
    pend_l = cyl("HallPendant", (0, -1.5, CEIL - 0.25), 0.14, 0.12, pbr("PendGlass", (0.8, 0.75, 0.65), 0.3, 0.0, **{'Transmission Weight': 0.6}), 24)
    cyl("Cord", (0, -1.5, CEIL - 0.1), 0.004, 0.2, mat("black"), 6)
    if c["police"]:
        police_gear(c)


def police_gear(c):
    """Recorder on the phone table, a cable to the phone, headphones, a folding chair and a notebook for the officer."""
    t = PHONE_T
    deck = rj.reel_deck("Deck")
    deck["root"].location = (t.x - 0.02, t.y + 0.13, 0.778); deck["root"].rotation_euler = (0, 0, -math.pi / 2)   # keys toward the hall
    c["deck"] = deck
    # cable from the deck to the phone (lying on the table)
    pts = [Vector((t.x + 0.12, t.y + 0.0, 0.79)), Vector((t.x + 0.15, t.y - 0.1, 0.785)), Vector((t.x + 0.1, t.y - 0.2, 0.785))]
    cu = bpy.data.curves.new("TapCable", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.003
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (*q, 1)
    sp.use_endpoint_u = True
    co = bpy.data.objects.new("TapCable", cu); bpy.context.collection.objects.link(co); co.data.materials.append(mat("black"))
    # officer's chair (folding) beside the table, on the hall side, a little north
    ch, _ = rj.model_fit("SchoolChair_01", (0.25, -0.62, 0.0), rot_z=math.pi * 0.62, height=0.85)
    c["off_chair"] = ch
    box("OffNotebook", (t.x - 0.04, t.y + 0.42, 0.785), (0.15, 0.21, 0.012), pbr("OffPad", (0.12, 0.2, 0.32), 0.6))


def piano_room(c):
    pn = rj.upright_piano("Piano")
    pn["root"].location = PIANO
    c["piano"] = pn
    # piano lamp (a small brass lamp on the piano top), metronome, a framed photo with no face (back to camera)
    lamp_parts = [cyl("PLBase", (0, 0, 0.01), 0.06, 0.02, pbr("BrassP", (0.55, 0.42, 0.2), 0.3, 1.0), 24),
                  cyl("PLStem", (0, 0, 0.17), 0.008, 0.32, pbr("BrassP2", (0.55, 0.42, 0.2), 0.3, 1.0), 12)]
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.13, radius2=0.08, depth=0.15, location=(0, 0, 0.36))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("PShade", (0.72, 0.6, 0.4), 0.7, 0.0, **{'Transmission Weight': 0.4,
                                                                 'Emission Color': (1.0, 0.68, 0.38, 1), 'Emission Strength': 0.0}))
    c["pshade_mat"] = sh.data.materials[0]
    lamp_parts.append(sh)
    pl = join(lamp_parts, "PianoLamp"); pl.location = PIANO + Vector((0.5, 0.28, 1.262))
    c["piano_lamp"] = pl
    met = join([cyl("Met", (0, 0, 0.1), 0.05, 0.2, mat("darkwood"), 4, rot=(0, 0, math.pi / 4))], "Metronome")
    met.location = PIANO + Vector((-0.45, 0.3, 1.262)); met.scale = (0.9, 0.7, 1.0)
    for k, (dx, h_) in enumerate(((-0.2, 0.22), (-0.05, 0.18))):
        box("Frame", (PIANO.x + dx, PIANO.y + 0.45, 1.262 + h_ / 2), (0.14, 0.015, h_), pbr("FrameW", (0.25, 0.18, 0.1), 0.4), rot=(math.radians(-8), 0, 0))
    # sofa, armchair, coffee table, rug, bookshelf, a standing lamp, a sideboard with a television (off)
    rj.model_fit("sofa_02", (-3.9, -2.6, 0), rot_z=0.0, width=2.0)
    rj.model_fit("ArmChair_01", (-5.7, -1.0, 0), rot_z=-math.pi / 2 + 0.3, height=0.95)
    rj.model_fit("CoffeeTable_01", (-3.9, -1.1, 0), rot_z=0.0, width=1.1)
    box("RugLiv", (-3.9, -1.0, 0.004), (2.8, 2.0, 0.008), mat("rug"))
    try:
        rj.model_fit("painted_wooden_cabinet", (-1.5, 1.7, 0), rot_z=-math.pi / 2, height=1.25)
    except Exception:
        pass
    try:
        rj.model_fit("decorative_book_set_01", (-3.6, -1.1, 0.42), rot_z=0.3, width=0.3)
    except Exception:
        pass
    try:
        tv, _ = rj.model_fit("Television_01", (-6.25, 2.9, 0.62), rot_z=math.radians(-140), height=0.5)
        box("TVCab", (-6.25, 2.9, 0.31), (0.8, 0.5, 0.62), mat("oak"), bevel=0.01, rot=(0, 0, math.radians(-50)))
    except Exception:
        pass
    try:
        rj.model_fit("potted_plant_04", (-6.3, -3.1, 0), height=1.0)
    except Exception:
        pass
    for k, (x, z) in enumerate(((-2.3, 1.75), (-5.2, 1.6))):
        box("Picture", (x, 3.5 - 0.01, z), (0.5, 0.02, 0.38), pbr("PicFrame", (0.2, 0.14, 0.08), 0.4))
        box("PictureCanvas", (x, 3.5 - 0.022, z), (0.42, 0.005, 0.3), pbr("PicCanvas", (0.25 + 0.1 * k, 0.28, 0.22), 0.8))


def kitchen(c):
    k = KTABLE
    tr, _ = rj.model_fit("dining_table", (k.x, k.y, 0), rot_z=0.0, height=0.76)
    c["ktable"] = tr
    lo, hi = ph.bounds([o for o in tr.children_recursive if o.type == 'MESH'])
    c["ktable_top"] = hi.z
    c["ktable_bounds"] = (lo, hi)
    for (dx, dy, rz) in ((0, -0.7, 0.0), (0, 0.7, math.pi), (-0.95, 0, -math.pi / 2), (0.95, 0, math.pi / 2)):
        rj.model_fit("dining_chair_02", (k.x + dx, k.y + dy, 0), rot_z=rz + math.pi, height=0.95)
    wd = mat("oak"); top = pbr("Worktop", (0.55, 0.52, 0.45), 0.4)
    box("CounterE", (2.3, 5.5, 0.44), (0.6, 3.6, 0.88), wd); box("CounterETop", (2.3, 5.5, 0.9), (0.64, 3.64, 0.04), top)
    box("CounterN", (0, 7.2, 0.44), (4.0, 0.6, 0.88), wd); box("CounterNTop", (0, 7.2, 0.9), (4.04, 0.64, 0.04), top)
    box("Sink", (0, 7.2, 0.89), (0.7, 0.45, 0.04), pbr("SinkSteel", (0.6, 0.6, 0.62), 0.25, 1.0))
    box("UpperE", (2.42, 5.5, 1.9), (0.35, 3.0, 0.7), wd)
    try:
        ph.model("vintage_electric_kettle", loc=(2.25, 4.5, 0.92), rot_z=-math.pi / 2)
    except Exception:
        pass
    try:
        ph.model("wooden_cutting_board", loc=(2.25, 6.1, 0.92), rot_z=1.6)
    except Exception:
        pass
    # the radio on the windowsill (inside sill at y ~ 7.36)
    rad, scale_m = rj.kitchen_radio("KRadio")
    rad.location = (-0.45, 7.47 - 0.17, 1.055 - 0.13 + 0.17); rad.rotation_euler = (0, 0, 0)
    rad.location = (-0.42, 7.16, 0.92)
    c["kradio"] = rad; c["kradio_scale"] = scale_m
    mug = pbr("Mug", (0.75, 0.72, 0.65), 0.25)
    c["cups"] = [cyl("Cup", (k.x + 0.25, k.y - 0.2, c["ktable_top"] + 0.045), 0.04, 0.09, mug, 24),
                 cyl("Cup2", (k.x - 0.3, k.y + 0.15, c["ktable_top"] + 0.045), 0.04, 0.09, mug, 24)]
    # kitchen pendant
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.24, radius2=0.05, depth=0.16, location=(k.x, k.y, 1.85))
    sh = bpy.context.active_object; sh.data.materials.append(pbr("KShade", (0.45, 0.3, 0.15), 0.5, 0.0, **{'Emission Color': (1, 0.7, 0.4, 1), 'Emission Strength': 0.0}))
    c["kshade_mat"] = sh.data.materials[0]
    cyl("KCord", (k.x, k.y, 2.25), 0.004, 0.7, mat("black"), 6)


def exterior(c):
    box("Garden", (0, 0, -0.05), (120, 120, 0.06), mat("grass"))
    box("Path", (0, -7, -0.015), (1.4, 7, 0.03), mat("gravel"))
    # neighbour house to the west and south (plaster block, tiled roof, balconies)
    import sc_village
    try:
        sc_village.house_block((-34, 8, 0), rot_z=math.pi / 2, seed=3)
        sc_village.house_block((-2, -20, 0), rot_z=0.0, seed=5)
        sc_village.house_block((3, 18, 0), rot_z=math.pi, seed=7)
    except Exception as e:
        print("[house] neighbours skipped", e)
    # trees and a hedge outside
    trees = []
    for (x, y, s) in ((-16, 9, 1.0), (-15, -8, 0.8), (-6, -11, 0.9), (6, -9, 1.1), (7, 10, 1.0), (-8, 12, 0.9)):
        trees.append((Vector((x, y, 0)), (x * 7.1) % 6.28, s))
    c["trees"] = rj.low_instances("birch", trees)
    hedge = rj.ph_instances("shrub_02", [((-9.5, y, 0), y, 1.0) for y in (-7.5, 6.5)] + [((x, -6.5, 0), x, 1.1) for x in (-5, 3)])
    c["trees"] += hedge


def lighting(c):
    L = c["light"]
    st = c["shade_mat"].node_tree.nodes["Principled BSDF"]; ps = c["pshade_mat"].node_tree.nodes["Principled BSDF"]
    ks = c["kshade_mat"].node_tree.nodes["Principled BSDF"]
    lamps_on = L in ("night", "dusk")
    from common import sun
    def _sky(kind):
        w, sn = rj.sky(kind)
        if sn is not None:
            bpy.data.objects.remove(sn, do_unlink=True)
        return w
    if L == "morning":
        # grey morning: a soft, cool sun low through the west windows of the piano room is the one key
        _sky("grey")
        sun(9, -97, 4.0, (1.0, 0.86, 0.72), 2.0)            # low morning sun through the south window, behind the players
        sun(14, 180, 0.6, (0.75, 0.82, 1.0), 10)            # weak cool skylight through the west windows
    elif L == "afternoon":
        _sky("lowsun")
        sun(14, 200, 4.0, (1.0, 0.72, 0.45), 2)
    elif L == "sunset":
        # the low warm sun from the south-west comes through the frosted front door and the hall window
        _sky("sunset")
        sun(5, -62, 5.0, (1.0, 0.5, 0.22), 1.5)
    elif L == "dusk":
        rj.sky("dusk")
        b = area_light((0.0, -6.0, 1.6), (0, 0, 0), 1.6, 90, (0.45, 0.55, 0.95)); point_at(b, (0.4, -1.4, 1.2)); b.visible_camera = False
        b2 = area_light((-9, 0, 1.6), (0, 0, 0), 3.0, 120, (0.45, 0.55, 0.95)); point_at(b2, (-4, 1.5, 0.5)); b2.visible_camera = False
    else:                                            # night: practical lamps only, a little moonlight outside
        rj.sky("night")
        mo = area_light((-10, 4, 6), (0, 0, 0), 6.0, 60, (0.4, 0.5, 0.9)); point_at(mo, (-4, 0, 0)); mo.visible_camera = False
    if lamps_on or L == "night":
        st.inputs['Emission Strength'].default_value = 3.0
        hl = bpy.data.lights.new("HallLampL", 'POINT'); hl.energy = 38; hl.color = (1.0, 0.62, 0.32); hl.shadow_soft_size = 0.06
        ho = bpy.data.objects.new("HallLampL", hl); bpy.context.collection.objects.link(ho)
        ho.location = c["hall_lamp"].location + Vector((0, 0, 0.36))
        ps.inputs['Emission Strength'].default_value = 3.0
        pl = bpy.data.lights.new("PianoLampL", 'POINT'); pl.energy = 30; pl.color = (1.0, 0.62, 0.32); pl.shadow_soft_size = 0.05
        po = bpy.data.objects.new("PianoLampL", pl); bpy.context.collection.objects.link(po)
        po.location = c["piano_lamp"].location + Vector((0, 0, 0.35))
        c["hall_light"] = ho; c["piano_light"] = po
        # soft warm bounce off the ceiling around each practical (dark negative fill elsewhere)
        b1 = area_light(c["hall_lamp"].location + Vector((-0.5, 0, 1.6)), (0, 0, 0), 1.2, 22, (1.0, 0.66, 0.4)); b1.visible_camera = False
        b2 = area_light(c["piano_lamp"].location + Vector((0, -1.2, 1.1)), (0, 0, 0), 1.4, 18, (1.0, 0.66, 0.4)); b2.visible_camera = False
        # cool moonlight through the front door glass and the hall window, rim on the figures
        m1 = area_light((0.2, -5.2, 1.8), (0, 0, 0), 1.0, 60, (0.45, 0.55, 0.95)); point_at(m1, (0.3, -1.4, 1.2)); m1.visible_camera = False
        # the kitchen beyond: a faint warm spill through the doorway
        ks.inputs['Emission Strength'].default_value = 1.2
        kl = bpy.data.lights.new("KitL", 'POINT'); kl.energy = 25; kl.color = (1.0, 0.6, 0.3)
        ko = bpy.data.objects.new("KitL", kl); bpy.context.collection.objects.link(ko); ko.location = (KTABLE.x, KTABLE.y, 1.75)


ROOM_WINDOWS = {        # (window point outside, target inside) for look.interior_day: the one strong key per room
    "piano": ((-4.45, -4.6, 1.6), (-3.8, 2.0, 0.8)),
    "hall": ((0.0, -4.6, 1.5), (0.5, -1.4, 1.2)),
    "kitchen": ((0.0, 8.6, 1.7), (0.0, 5.4, 0.8)),
}


def apply_look(c):
    import look
    v = c["variant"]; L = c["light"]
    room = v.split("@")[1].split("|")[0].split("+")[0] if "@" in v else "piano"
    if L in ("night", "dusk"):
        look.night_interior()
    else:
        mood = {"morning": "low_sun" if room == "piano" else "overcast", "afternoon": "low_sun", "sunset": "low_sun"}[L]
        for o in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.data.type == 'SUN']:
            bpy.data.objects.remove(o)
        look.interior_day(window=ROOM_WINDOWS[room], mood=mood)


def cast(c):
    """The people this variant needs (variant "light+police|mother,officer"): built here, so the bake can restore
    their rest pose every frame."""
    c["P"] = {}
    roles = c["variant"].split("|")[1].split(",") if "|" in c["variant"] else []
    for role in roles:
        c["P"][role] = person(role, cap=False)                 # indoors: no caps


def need(c, role):
    return c["P"][role]


# ============================================================================ actions
def phone_to_ear(c, h, sec, side="L", talk=0.0):
    sgn = 1.0 if side == "L" else -1.0
    """Standing at the phone: the handset along the left cheek (earpiece at the ear, mouthpiece at the mouth),
    held at the grip, elbow down and forward."""
    from mathutils import Matrix
    hs = c["handset"]
    fwd = forward(h); left = -fwd.cross(Vector((0, 0, 1))).normalized() * sgn     # "left" = the holding side
    head = h.bone_head("head"); tail = h.bone_tail("head"); up = (tail - head).normalized()
    E = head + up * 0.06 + left * 0.075 + fwd * 0.0             # ear
    Mo = head - up * 0.035 + fwd * 0.085 + left * 0.035         # mouth corner
    X = (E - Mo).normalized(); Z = (left - X * left.dot(X)).normalized(); Y = Z.cross(X)
    C = (E + Mo) * 0.5 + Z * 0.04
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = C
    hs.matrix_world = M
    wrist_t = C + Z * 0.035 - X * 0.02 - up * 0.07
    reach(h, side, wrist_t, Vector((0, 0, -1.0)) + fwd * 0.55 + left * 0.35, X + Z * 0.3)
    fingers_curl(h, 82, side=(side,), thumb=45)            # a closed grip round the handset
    return E


def handset_rest(c):
    loc, rot = c["handset_rest"]
    c["handset"].matrix_parent_inverse.identity()
    c["handset"].location = loc; c["handset"].rotation_euler = rot


def breathe(h, sec, amt=1.0):
    side = forward(h).cross(Vector((0, 0, 1))).normalized()
    h.rot("spine03", side, amt * 1.2 * math.sin(sec * 1.6))
    h.rot("neck01", side, amt * 0.8 * math.sin(sec * 1.6 + 0.6))


def place_mother_phone(c, sec, yaw=0.0, talk=0.4, look=0.0, hand="L"):
    m = need(c, "mother")
    stand(m, (PHONE_T.x - 0.55, PHONE_T.y - 0.12, 0.0), math.pi / 2 + yaw)       # faces the table (+X)
    breathe(m, sec)
    side = forward(m).cross(Vector((0, 0, 1))).normalized()
    m.rot("head", side, -8 - 2 * math.sin(sec * 0.5)); m.rot("head", (0, 0, 1), look)
    phone_to_ear(c, m, sec, side=hand)
    # the free hand rests on the table edge
    free = "R" if hand == "L" else "L"
    reach(m, free, Vector((PHONE_T.x - 0.24, PHONE_T.y + (-0.33 if free == "R" else 0.05), 0.8)), Vector((0.2, -0.6 if free == "R" else 0.6, -1)),
          forward(m) + Vector((0, 0, -0.8)))
    fingers_curl(m, 20, side=(free,))
    return m


def place_officer(c, sec, press=0.0, write=0.0):
    """The officer on the folding chair by the recorder, headphones on, leaning toward the table."""
    o = need(c, "officer")
    rj.sit_on(o, (0.25, -0.62), math.radians(118), 0.45, lean=18, feet=0.4)
    if "hp" not in c:
        c["hp"] = rj.put_headphones(o, rj.headphones("Headphones"))
    fwd = forward(o); side = fwd.cross(Vector((0, 0, 1))).normalized()
    o.rot("head", side, -14 - 3 * math.sin(sec * 0.4))
    rj.wear_headphones(o, c["hp"])
    # left hand on the headphone cup (press = pulls it tighter), right hand on his knee or on the notebook
    left = -side
    cup = c["hp"].matrix_world @ Vector((-0.12, 0, -0.105))         # outside of the left ear cup
    lt = cup + left * 0.03 * (1 - press) + Vector((0, 0, -0.04))
    if press > 0.01:
        reach(o, "L", lt, left * 0.5 + Vector((0, 0, -1)) - fwd * 0.3, Vector((0, 0, 1)) - left * 0.35)
        fingers_curl(o, 25, side=("L",))
    knee = o.bone_tail("upperleg02.R") + Vector((0, 0, 0.1))
    reach(o, "R", knee.lerp(Vector((PHONE_T.x - 0.06, PHONE_T.y + 0.42, 0.8)), write), side * 0.4 + Vector((0, 0, -1)), fwd + Vector((0, 0, -0.8)))
    fingers_curl(o, 30)
    return o


# ============================================================================ shots
def _reels(c, sec, on=True):
    if "deck" in c:
        rj.spin_reels(c["deck"], sec, on=on)
        # needle: jittering with the line, kicks on clicks at fixed times
        kick = sum(math.exp(-((sec - tk) / 0.06) ** 2) for tk in (0.9, 2.1, 3.3, 4.4))
        c["deck"]["needle"].rotation_euler.z = math.radians(-35 + 12 * (0.5 + 0.5 * math.sin(sec * 9.0)) * 0.4 + 45 * kick) if on else math.radians(-40)


def _clock(c, sec):
    c["pendulum"].rotation_euler.y = math.radians(7) * math.sin(sec * math.pi)      # one swing per second


def _curtain_air(c, sec):
    pass


# --- Cold Open set 1-3 (night, police gear): mother at the phone, officer listening, reels turning
def anim_co(c, t, shot, dur):
    sec = t * dur
    _reels(c, sec); _clock(c, sec)
    if shot in ("co_push", "co_profile", "co_officer", "co_meter", "co_tape", "co_top"):
        place_mother_phone(c, sec, talk=0.6, hand="R" if shot == "co_officer" else "L")
        place_officer(c, sec, press=ease(min(1, max(0, (sec - 0.6) / 1.5))) if shot == "co_officer" else 0.0)


def cam_co_push(c, t):
    e = ease(t)
    a = Vector((-0.55, -3.25, 1.55)); b = Vector((-0.35, -2.55, 1.5))
    return (a.lerp(b, e), Vector((0.55, -1.1, 1.25)), 32)


def cam_co_profile(c, t):
    e = ease(t)
    a = Vector((0.85, -3.3, 1.5)); b = Vector((0.78, -3.05, 1.48))           # from the right (by the front door)
    return (a.lerp(b, e), Vector((0.2, -1.35, 1.38)), 40)


def cam_co_officer(c, t):
    e = ease(t)
    o = c["P"]["officer"]; hd = o.bone_head("head")
    f = forward(o); left = Vector((-f.y, f.x, 0))
    a = hd - f * 1.25 + left * 0.6 + Vector((0, 0, 0.3)); b = hd - f * 1.1 + left * 0.55 + Vector((0, 0, 0.28))
    m = c["P"]["mother"].bone_head("head")
    return (a.lerp(b, e), hd.lerp(m, 0.55) + Vector((0, 0, -0.18)), 30)


def cam_co_tape(c, t):
    e = ease(t)
    d = c["deck"]["root"].matrix_world
    a = d @ Vector((-0.3, -0.44, 0.22)); b = d @ Vector((0.02, -0.44, 0.21))
    return (a.lerp(b, e), d @ Vector((0.0, -0.06, 0.12)), 45)


def cam_co_top(c, t):
    d = c["deck"]["root"].matrix_world
    ang = math.radians(-20 + 25 * ease(t))
    tgt = d @ Vector((0, 0.035, 0.12))
    off = Vector((0, 0, 0.5)) + d.to_3x3() @ Vector((0, -0.06, 0))
    up = d.to_3x3() @ Vector((math.sin(ang), math.cos(ang), 0))
    return (tgt + off, tgt, 38, tuple(up))


def cam_co_meter(c, t):
    e = ease(t)
    d = c["deck"]["root"].matrix_world
    a = d @ Vector((-0.24, -0.44, 0.25)); b = d @ Vector((-0.18, -0.32, 0.2))
    return (a.lerp(b, e), d @ Vector((-0.14, -0.105, 0.12)), 50)


# --- piano: the brother alone at night (Cold Open 4) ; brother and sister in the morning (Ch1 1)
def place_pianists(c, sec, both=True, playing=True, page=0.0):
    pn = c["piano"]; bench = pn["bench"].matrix_world.translation
    br = need(c, "brother")
    bx = 0.22 if both else 0.0
    rj.sit_on(br, (bench.x + bx, bench.y - 0.02), math.pi, 0.515, lean=8, feet=0.45)
    keys_y = PIANO.y - 0.15; kz = 0.76
    def play(h, sd, x0, ph0, amp):
        fwd = forward(h)
        x = x0 + 0.04 * math.sin(sec * 1.3 + ph0) * amp
        tap = 0.012 * max(0.0, math.sin(sec * 7.5 + ph0)) * amp
        reach(h, sd, Vector((x, keys_y - 0.04, kz + 0.06 - tap)), Vector((SIDE[sd] * -0.6, -0.3, -1)), fwd + Vector((0, 0, -0.5)))
    if playing and not both:
        play(br, "L", bench.x - 0.25, 0.0, 1.0); play(br, "R", bench.x + 0.2, 1.7, 1.0)
    breathe(br, sec, 0.6)
    side = forward(br).cross(Vector((0, 0, 1))).normalized()
    br.rot("head", side, -14)
    if both:
        si = need(c, "sister")
        rj.sit_on(si, (bench.x - 0.24, bench.y + 0.0), math.pi, 0.515, lean=6, feet=0.32)
        play(si, "L", bench.x - 0.42, 0.0, 1.0 if playing else 0.0); play(si, "R", bench.x - 0.1, 2.0, 1.0 if playing else 0.0)
        s2 = forward(si).cross(Vector((0, 0, 1))).normalized(); si.rot("head", s2, -10)
        # brother: one hand on his knee, the other reaches up to the score when turning the page
        sc = pn["score"].matrix_world.translation
        reach(br, "L", Vector((bench.x + 0.15, keys_y - 0.12, 0.62)), Vector((0.3, -0.3, -1)), forward(br) + Vector((0, 0, -0.8)))
        if page > 0.0:
            tgt = sc + Vector((0.2 - 0.25 * page, -0.06, 0.05))
            reach(br, "R", tgt, Vector((0.7, -0.2, -1)), Vector((0, 1, 0.3)))
        pn["turn"].rotation_euler.z = math.radians(-178 * ease(min(1.0, max(0.0, (page - 0.25) / 0.75)))) if page > 0 else 0.0
    return br


def anim_piano(c, t, shot, dur):
    sec = t * dur
    if shot in ("co_brother", "co_brother_side"):
        stop = shot == "co_brother_side" and sec > dur * 0.45
        place_pianists(c, sec, both=False, playing=not stop)
    else:
        page = ease(min(1.0, max(0.0, (sec - 1.2) / 1.6))) if shot == "p_page" else 0.0
        place_pianists(c, sec, both=True, playing=True, page=page)
    rj.sway(c["trees"], sec, 0.01, 0.25)


def cam_co_brother(c, t):
    e = ease(t)
    a = Vector((-3.55, -0.2, 1.35)); b = Vector((-3.65, 0.55, 1.3))
    return (a.lerp(b, e), PIANO + Vector((0.0, 0.0, 1.0)), 38)


def cam_co_brother_side(c, t):
    e = ease(t)
    a = Vector((-5.9, 0.4, 1.25)); b = Vector((-6.15, -0.1, 1.3))
    return (a.lerp(b, e), PIANO + Vector((0.2, -0.6, 0.85)), 30)


def cam_p_title(c, t):
    e = ease(t)
    a = Vector((-2.35, 0.05, 1.3)); b = Vector((-2.75, 0.2, 1.28))           # from the right, behind
    return (a.lerp(b, e), PIANO + Vector((-0.1, -0.5, 0.95)), 32)


def cam_p_page(c, t):
    e = ease(t)
    a = Vector((-5.65, 0.6, 1.45)); b = Vector((-5.45, 0.95, 1.42))          # from the left, wider
    return (a.lerp(b, e), PIANO + Vector((0.05, -0.55, 0.95)), 30)


def _mk(shot, dur, cam, anim_fn, focus=None, dof=None):
    DUR[shot] = dur
    spec = dict(kind="anim", cam=cam, anim=lambda c, t: anim_fn(c, t, shot, dur))
    if focus:
        spec["focus"] = focus; spec["dof"] = dof or 2.8
    return spec


def _f_mother(c, t):
    return c["P"]["mother"].bone_head("head")


def _f_officer(c, t):
    return c["P"]["officer"].bone_head("head")


def _f_deck(c, t):
    return c["deck"]["root"].matrix_world @ Vector((0, -0.08, 0.12))


def _f_meter(c, t):
    return c["deck"]["root"].matrix_world @ Vector((-0.14, -0.105, 0.12))


def _f_bench(c, t):
    return c["piano"]["bench"].matrix_world.translation + Vector((0, 0, 0.9))


def cam_debug(c, t):
    return (Vector((-0.9, -3.3, 2.4)), Vector((0.6, -0.6, 0.8)), 18)


def cam_debug_liv(c, t):
    return (Vector((-1.6, -3.2, 2.4)), Vector((-4.0, 2.0, 0.6)), 16)


# ============================================================================ Chapter One / Two house shots
def suitcase():
    """An open 1970s hard suitcase (brown vinyl, chrome latches): body + lid on a hinge empty. Local: hinge along +Y edge."""
    vin = pbr("SuitVinyl", (0.12, 0.07, 0.04), 0.45, 0.0, **{'Coat Weight': 0.3}); lin = rj.fabric("SuitLining", (0.25, 0.18, 0.12), 0.9, 0.3)
    W_, D_, H_ = 0.62, 0.42, 0.16
    body = join([box("SBody", (0, 0, H_ / 2), (W_, D_, H_), vin, bevel=0.012), box("SLining", (0, 0, H_ - 0.004), (W_ - 0.03, D_ - 0.03, 0.006), lin)], "Suitcase")
    hinge = bpy.data.objects.new("SuitHinge", None); bpy.context.collection.objects.link(hinge); hinge.parent = body; hinge.location = (0, D_ / 2, H_)
    lid = join([box("SLid", (0, -D_ / 2, 0.045), (W_, D_, 0.09), vin, bevel=0.012), box("SLidLin", (0, -D_ / 2, 0.002), (W_ - 0.03, D_ - 0.03, 0.004), lin)], "SuitLid")
    lid.parent = hinge
    for x in (-0.18, 0.18):
        box("Latch", (x, -D_ / 2 - 0.004, H_ - 0.01), (0.05, 0.012, 0.035), mat("chrome")).parent = body
    box("SHandle", (0, -D_ / 2 - 0.02, H_ - 0.02), (0.14, 0.02, 0.025), pbr("HandleBlk", (0.03, 0.02, 0.015), 0.4), bevel=0.008).parent = body
    return dict(root=body, hinge=hinge, W=W_, D=D_, H=H_)


def note_bundle(name):
    """A bundle of used, plain banknotes (no design, nothing readable): a slightly worn stack with a paper band."""
    m = pbr("NotePaper", (0.42, 0.36, 0.30), 0.85)
    band = pbr("NoteBand", (0.75, 0.72, 0.62), 0.8)
    return join([box(name, (0, 0, 0.018), (0.16, 0.085, 0.036), m, bevel=0.002), box(name + "B", (0, 0, 0.018), (0.03, 0.087, 0.038), band)], name)


def kitchen_extras(c):
    v = c["variant"]
    top = c["ktable_top"]
    if "+letter" in v:
        img = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "nvidia_doc", "assets", "generated", "rj_letter.png")
        if not os.path.exists(img):
            import letter; letter.make()
        m = bpy.data.materials.new("Letter"); m.use_nodes = True
        N = m.node_tree.nodes; L = m.node_tree.links; p = N["Principled BSDF"]
        tx = N.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.abspath(img)); L.new(tx.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.85
        bpy.ops.mesh.primitive_plane_add(size=1, location=(KTABLE.x + 0.05, KTABLE.y - 0.05, top + 0.002))
        lt = bpy.context.active_object; lt.scale = (0.21, 0.297, 1); lt.rotation_euler.z = 0.12; lt.data.materials.append(m)
        c["letter"] = lt
        env = box("EnvelopeK", (KTABLE.x - 0.32, KTABLE.y + 0.12, top + 0.004), (0.23, 0.12, 0.006), pbr("Env", (0.78, 0.74, 0.62), 0.8), rot=(0, 0, -0.3))
    if "+suitcase" in v:
        sc = suitcase(); sc["root"].location = (KTABLE.x - 0.05, KTABLE.y + 0.05, top); c["suit"] = sc
        c["bundles"] = []
        for k in range(14):
            b = note_bundle(f"Bundle{k}")
            r, q = divmod(k, 3)
            b.location = (KTABLE.x - 0.05 - 0.17 + q * 0.17, KTABLE.y + 0.05 - 0.13 + (r % 3) * 0.09, top + 0.025 + (r // 3) * 0.037)
            c["bundles"].append(b)
        c["stack"] = [note_bundle(f"Stack{k}") for k in range(6)]
        for k, b in enumerate(c["stack"]):
            b.location = (KTABLE.x + 0.55, KTABLE.y - 0.15 + 0.0, top + k * 0.037)


def stand_at(h, pos, face_z):
    stand(h, Vector((pos[0], pos[1], 0)), face_z)


# --- 4A/4B: sunset, the mother calls the cousin's house
def anim_dial(c, t, shot, dur):
    sec = t * dur
    _clock(c, sec)
    m = c["P"]["mother"]
    if shot == "dial":
        stand_at(m, (PHONE_T.x - 0.55, PHONE_T.y - 0.12), math.pi / 2)
        breathe(m, sec)
        side = forward(m).cross(Vector((0, 0, 1))).normalized(); m.rot("head", side, -16)
        phone_to_ear(c, m, sec)
        d = c["dial"].matrix_world
        k = (sec * 0.8) % 1.0
        c["dial"].rotation_euler.z = math.radians(-120 * math.sin(math.pi * k))
        reach(m, "R", d @ Vector((0.03, 0.0, 0.05)), Vector((0, -0.4, -1)), forward(m) + Vector((0, 0, -1)))
    else:
        put = ease(min(1.0, sec / 1.2))
        stand_at(m, (PHONE_T.x - 0.55, PHONE_T.y - 0.12), math.pi / 2 + math.radians(28) * ease(max(0.0, (sec - 1.4) / 1.2)))
        side = forward(m).cross(Vector((0, 0, 1))).normalized(); m.rot("head", side, 8 * ease(max(0.0, (sec - 1.4) / 1.2)))
        if put < 1.0:
            ear = phone_to_ear(c, m, sec)
            hs = c["handset"]; rest = c["phone"].matrix_world @ Vector(c["handset_rest"][0])
            M = hs.matrix_world.copy(); M.translation = M.translation.lerp(rest, put); hs.matrix_world = M
            reach(m, "L", hs.matrix_world.translation + Vector((0, 0, 0.03)), Vector((0, -0.5, -1)), forward(m))
        else:
            handset_rest(c)


def cam_dial(c, t):
    e = ease(t)
    a = Vector((0.75, -3.0, 1.45)); b = Vector((0.7, -2.75, 1.42))
    return (a.lerp(b, e), Vector((0.25, -1.4, 1.25)), 45)


def cam_hangup(c, t):
    e = ease(t)
    a = Vector((-0.85, -1.9, 1.5)); b = Vector((-0.75, -1.65, 1.5))
    return (a.lerp(b, e), Vector((0.95, -0.85, 1.55)), 32)


# --- 12A/B: night, the empty piano bench ; torches flicker outside past the piano
def anim_empty_piano(c, t, shot, dur):
    sec = t * dur
    for k, tr in enumerate(c.get("out_torches", [])):
        tr.location = (-12.5 + 3 * math.sin(sec * 0.3 + k), 2.0 + k * 3.0 - 0.6 * sec, 1.1 + 0.05 * math.sin(sec * 4 + k))
        aim = Vector((math.sin(sec * 0.9 + k * 2), -0.5, -0.35)).normalized()
        tr.rotation_euler = aim.to_track_quat('-Y', 'Z').to_euler()
    rj.sway(c["trees"], sec, 0.01, 0.25)


def cam_bench(c, t):
    e = ease(t)
    a = Vector((-3.75, 0.2, 1.05)); b = Vector((-3.78, 1.0, 0.95))
    return (a.lerp(b, e), PIANO + Vector((0.0, -0.75, 0.7)), 40)


def cam_pwin(c, t):
    e = ease(t)
    a = Vector((-2.6, 1.6, 1.4)); b = Vector((-2.9, 1.3, 1.35))
    return (a.lerp(b, e), Vector((-6.6, 1.55, 1.4)), 30)


# --- 14A/B: kitchen, grey morning, the radio
def anim_kitchen(c, t, shot, dur):
    sec = t * dur
    P_ = c["P"]
    if "mother" in P_:
        rj.sit_on(P_["mother"], (KTABLE.x - 0.0, KTABLE.y - 0.62), 0.0 + math.pi, 0.46, lean=14, feet=0.35)
        P_["mother"].arm.rotation_euler.z = math.pi
        rj.sit_on(P_["mother"], (KTABLE.x, KTABLE.y - 0.66), math.pi, 0.46, lean=14, feet=0.32)
        side = forward(P_["mother"]).cross(Vector((0, 0, 1))).normalized(); P_["mother"].rot("head", side, -14)
    if "father" in P_ and shot == "k_radio":
        rj.sit_on(P_["father"], (KTABLE.x - 0.88, KTABLE.y), -math.pi / 2, 0.46, lean=10, feet=0.35)
        side = forward(P_["father"]).cross(Vector((0, 0, 1))).normalized(); P_["father"].rot("head", (0, 0, 1), 35)
    if "father" in P_ and shot == "k_window":
        f = P_["father"]; stand_at(f, (0.55, 6.75), math.pi + 0.15)
        breathe(f, sec)
        cup = c["cups"][0]
        fwd = forward(f); right = fwd.cross(Vector((0, 0, 1))).normalized()
        hand = rj.rjp.chest_point(f, 0.3, 0.32 - 0.03 * math.sin(sec * 0.6))
        reach(f, "R", hand, Vector((0, 0, -1)) + right * 0.4, fwd)
        cup.location = f.bone_tail("wrist.R") + fwd * 0.05 + Vector((0, 0, 0.05))
        side = right; f.rot("head", side, -6)
    # the radio's tuning pointer drifts a hair, the scale glows
    rj.sway(c["trees"], sec, 0.01, 0.25)


def cam_kradio(c, t):
    e = ease(t)
    r = c["kradio"].location
    a = r + Vector((0.55, -1.1, 0.35)); b = r + Vector((0.35, -0.7, 0.3))
    return (a.lerp(b, e), r + Vector((0.0, 0.0, 0.1)), 50)


def cam_kwin(c, t):
    e = ease(t)
    a = Vector((-1.6, 4.6, 1.5)); b = Vector((-1.3, 4.9, 1.5))
    return (a.lerp(b, e), Vector((0.5, 6.9, 1.45)), 38)


# --- 15A/B: the first call (grey morning): the phone rings, the mother hurries in ; she listens, lowers the receiver
def anim_ring(c, t, shot, dur):
    sec = t * dur
    m = c["P"]["mother"]
    ring = (sec % 2.0) < 1.0
    c["phone"].rotation_euler.x = math.radians(0.6) * math.sin(sec * 120) if ring and shot == "ring" else 0.0
    c["handset"].rotation_euler.y = (math.radians(0.8) * math.sin(sec * 140) if ring and shot == "ring" else 0.0)
    if shot == "ring":
        walk(m, (-0.45, 3.2), (PHONE_T.x - 0.55, PHONE_T.y + 0.1), sec + 0.0, speed=1.5, stride=30)
    else:
        lower = ease(max(0.0, (sec - dur * 0.6) / (dur * 0.35)))
        stand_at(m, (PHONE_T.x - 0.55, PHONE_T.y - 0.12), math.pi / 2)
        breathe(m, sec)
        ear = phone_to_ear(c, m, sec)
        if lower > 0:
            hs = c["handset"]; M = hs.matrix_world.copy()
            M.translation = M.translation + Vector((0.12, 0.05, -0.35)) * lower; hs.matrix_world = M
            reach(m, "L", M.translation + Vector((0, 0, -0.06)), Vector((0, -0.4, -1)), forward(m))
        side = forward(m).cross(Vector((0, 0, 1))).normalized(); m.rot("head", side, -6 - 12 * lower)


def cam_ring(c, t):
    e = ease(t)
    a = Vector((-0.55, -2.9, 1.35)); b = Vector((-0.45, -2.6, 1.3))
    return (a.lerp(b, e), Vector((0.3, -0.4, 1.0)), 28)


def cam_listen(c, t):
    e = ease(t)
    a = Vector((-0.3, 0.3, 1.5)); b = Vector((-0.2, 0.05, 1.48))        # from the left (north), profile
    return (a.lerp(b, e), Vector((0.3, -1.45, 1.35)), 42)


# --- 17A/B: the cut-out letter on the kitchen table
def anim_letter(c, t, shot, dur):
    sec = t * dur
    P_ = c["P"]
    if "father" in P_:
        f = P_["father"]; stand_at(f, (KTABLE.x - 0.1, KTABLE.y - 0.78), math.pi + 0.05)
        side = forward(f).cross(Vector((0, 0, 1))).normalized(); f.rot("spine03", side, -14); f.rot("head", side, -24)
        breathe(f, sec)
        reach(f, "R", Vector((KTABLE.x + 0.12, KTABLE.y - 0.45, c["ktable_top"] + 0.03)), Vector((0.3, 0, -1)), Vector((0, 1, -0.8)))
    if "detective" in P_:
        d = P_["detective"]; stand_at(d, (KTABLE.x + 0.72, KTABLE.y - 0.45), math.radians(125))
        side = forward(d).cross(Vector((0, 0, 1))).normalized(); d.rot("spine03", side, -10); d.rot("head", side, -26)
        breathe(d, sec + 1)


def cam_letter(c, t):
    e = ease(t)
    lt = c["letter"].location
    a = lt + Vector((0.02, -0.18, 0.95)); b = lt + Vector((0.01, -0.08, 0.6))
    return (a.lerp(b, e), lt + Vector((0, 0.03, 0)), 40, (0.0, 1.0, 0.0))


def cam_read(c, t):
    e = ease(t)
    a = Vector((KTABLE.x - 1.5, KTABLE.y + 0.9, 0.95)); b = Vector((KTABLE.x - 1.35, KTABLE.y + 0.7, 0.95))
    return (a.lerp(b, e), Vector((KTABLE.x + 0.2, KTABLE.y - 0.5, 1.2)), 32)


# --- 18A/B: the police arrive: a technician threads the recorder ; the officer pulls on his headphones
def anim_police_day(c, t, shot, dur):
    sec = t * dur
    _reels(c, sec, on=(shot == "door"))
    if shot == "thread" and "tech" in c["P"]:
        h = c["P"]["tech"]
        stand_at(h, (PHONE_T.x - 0.6, PHONE_T.y + 0.15), math.pi / 2)
        rj.rjp.bend_to(h, PHONE_T + Vector((0, 0.13, 0.9)), frac=0.8, max_deg=20)
        d = c["deck"]["root"].matrix_world
        k = 0.5 + 0.5 * math.sin(sec * 1.4)
        reach(h, "L", d @ Vector((-0.1, -0.03, 0.17)), Vector((0, 0, -1)) + Vector((0, 0.6, 0)), Vector((1, 0, -0.8)))
        reach(h, "R", d @ Vector((-0.04 + 0.08 * k, -0.1, 0.16)), Vector((0, 0, -1)) + Vector((0, -0.6, 0)), Vector((1, 0, -0.8)))
        fingers_curl(h, 30)
        side = forward(h).cross(Vector((0, 0, 1))).normalized(); h.rot("head", side, -20)
    if shot == "door" and "officer" in c["P"]:
        o = c["P"]["officer"]
        rj.sit_on(o, (0.25, -0.62), math.radians(118), 0.45, lean=12, feet=0.4)
        k = ease(min(1.0, sec / 2.0))
        hp = c["hp"]
        rj.wear_headphones(o, hp)
        M = hp.matrix_world.copy(); M.translation = M.translation + (Vector((0, 0, 0.3)) + forward(o) * 0.25) * (1 - k); hp.matrix_world = M
        side = forward(o).cross(Vector((0, 0, 1))).normalized()
        for sd, sg in SIDE.items():
            cup = hp.matrix_world @ Vector((0.088 if sd == "R" else -0.088, 0, -0.105))
            reach(o, sd, cup + Vector((0, 0, -0.04)), Vector((0, 0, -1)) + side * (0.7 if sd == "R" else -0.7), Vector((0, 0, 1)))


def cam_thread(c, t):
    e = ease(t)
    a = Vector((-0.75, -2.35, 1.6)); b = Vector((-0.65, -2.1, 1.55))
    return (a.lerp(b, e), PHONE_T + Vector((-0.1, 0.1, 0.95)), 38)


def cam_door(c, t):
    e = ease(t)
    a = Vector((0.2, -3.3, 1.65)); b = Vector((0.15, -3.05, 1.62))
    return (a.lerp(b, e), Vector((0.45, -0.75, 1.15)), 36)


# --- 19A/B (night, police): the mother says they'll pay ; the stuffed toys ; Ch2 11A/B the same hall, later
def anim_call(c, t, shot, dur):
    sec = t * dur
    _reels(c, sec, on=shot not in ("silent", "stairs"))
    _clock(c, sec)
    if shot in ("call_left", "toys", "co2_back", "co2_toy"):
        place_mother_phone(c, sec, talk=0.6)
        if "officer" in c["P"]:
            place_officer(c, sec)
    if shot == "stairs":
        m = c["P"]["mother"]
        rj.sit_on(m, (0.6, 0.25 + c["stair_run"] * 1.5), math.pi * 0.0 + math.radians(170), c["stair_rise"] * 2 + 0.0, lean=18, feet=0.32)
        breathe(m, sec)
        side = forward(m).cross(Vector((0, 0, 1))).normalized(); m.rot("head", side, -18); m.rot("head", (0, 0, 1), -25)
        handset_rest(c)


def cam_call_left(c, t):
    e = ease(t)
    a = Vector((-0.55, 0.15, 1.45)); b = Vector((-0.45, -0.1, 1.45))
    return (a.lerp(b, e), Vector((0.3, -1.5, 1.32)), 40)


def cam_toys(c, t):
    e = ease(t)
    a = Vector((-0.2, -3.0, 0.75)); b = Vector((0.15, -2.85, 0.7))
    return (a.lerp(b, e), Vector((0.77, -2.38, 0.6)), 50)


def cam_silent(c, t):
    e = ease(t)
    a = Vector((-0.4, -2.2, 1.25)); b = Vector((0.1, -1.75, 1.05))
    return (a.lerp(b, e), PHONE_T + Vector((0, -0.05, 0.85)), 40)


def cam_stairs(c, t):
    e = ease(t)
    a = Vector((-0.2, -1.4, 1.3)); b = Vector((-0.45, -3.1, 1.5))
    return (a.lerp(b, e), Vector((0.55, 0.7, 0.85)), 32)


def cam_co2_back(c, t):
    e = ease(t)
    a = Vector((-0.75, -1.05, 1.5)); b = Vector((-0.95, 0.4, 1.6))
    return (a.lerp(b, e), Vector((0.45, -1.4, 1.3)), 35)


def cam_co2_toy(c, t):
    e = ease(t)
    a = Vector((1.0 - 0.35, -3.05, 0.85)); b = Vector((0.4, -2.95, 0.8))
    return (a.lerp(b, e), Vector((0.8, -2.5, 0.62)), 45)


# --- 20A/B: the suitcase on the kitchen table
def anim_suit(c, t, shot, dur):
    sec = t * dur
    sc = c["suit"]; top = c["ktable_top"]
    if shot == "suitcase":
        sc["hinge"].rotation_euler.x = math.radians(100)
        o = c["P"]["detective"]; stand_at(o, (KTABLE.x + 0.75, KTABLE.y - 0.35), math.radians(125))
        k = (sec / 1.6) % 1.0; n = int(sec / 1.6)
        b = c["stack"][min(n, len(c["stack"]) - 1)]
        src = Vector((KTABLE.x + 0.55, KTABLE.y - 0.15, top + 0.2)); dst = Vector((KTABLE.x + 0.1 - 0.12 * (n % 2), KTABLE.y + 0.05, top + 0.12))
        for j, bb in enumerate(c["stack"]):
            if j < n:
                bb.location = (KTABLE.x + 0.1 - 0.12 * (j % 2), KTABLE.y + 0.05 - 0.1 + 0.09 * (j // 2 % 3), top + 0.13)
        b.location = src.lerp(dst, ease(k)) + Vector((0, 0, 0.1 * math.sin(math.pi * k)))
        rj.rjp.bend_to(o, b.location, frac=0.8, max_deg=20)
        fwd = forward(o); right = fwd.cross(Vector((0, 0, 1))).normalized()
        reach(o, "R", b.location + Vector((0, 0, 0.04)), Vector((0, 0, -1)) + right * 0.6, fwd + Vector((0, 0, -1)))
        side = right; o.rot("head", side, -22)
        if "father" in c["P"]:
            f = c["P"]["father"]; stand_at(f, (KTABLE.x - 0.45, KTABLE.y - 0.85), math.pi + 0.2)
            f.rot("head", forward(f).cross(Vector((0, 0, 1))).normalized(), -18)
    else:
        k = ease(min(1.0, sec / 1.6))
        sc["hinge"].rotation_euler.x = math.radians(100) * (1 - k)
        for bb in c["stack"]:
            bb.location.z = -5
        f = c["P"]["father"]; stand_at(f, (KTABLE.x - 0.05, KTABLE.y - 0.62), math.pi)
        lidp = sc["hinge"].matrix_world @ Vector((0, -sc["D"], 0.08))
        rj.rjp.bend_to(f, lidp, frac=0.8, max_deg=22)
        fwd = forward(f); right = fwd.cross(Vector((0, 0, 1))).normalized()
        latch = lambda x: sc["root"].matrix_world @ Vector((x, -sc["D"] / 2 - 0.01, sc["H"]))
        if k < 1.0:
            reach(f, "R", lidp + right * 0.15 + Vector((0, 0, 0.03)), Vector((0, 0, -1)) + right * 0.5, fwd)
            reach(f, "L", lidp - right * 0.15 + Vector((0, 0, 0.03)), Vector((0, 0, -1)) - right * 0.5, fwd)
        else:
            reach(f, "R", latch(0.18) + Vector((0, -0.03, 0.02)), Vector((0, 0, -1)) + right * 0.5, fwd + Vector((0, 0, -1)))
            reach(f, "L", latch(-0.18) + Vector((0, -0.03, 0.02)), Vector((0, 0, -1)) - right * 0.5, fwd + Vector((0, 0, -1)))
        f.rot("head", right, -20)


def cam_suitcase(c, t):
    e = ease(t)
    a = Vector((KTABLE.x - 1.1, KTABLE.y - 0.9, 1.55)); b = Vector((KTABLE.x - 0.9, KTABLE.y - 0.75, 1.45))
    return (a.lerp(b, e), Vector((KTABLE.x + 0.15, KTABLE.y, c["ktable_top"] + 0.1)), 40)


def cam_latch(c, t):
    e = ease(t)
    a = Vector((KTABLE.x + 1.45, KTABLE.y - 0.2, 1.15)); b = Vector((KTABLE.x + 1.25, KTABLE.y - 0.3, 1.1))
    return (a.lerp(b, e), Vector((KTABLE.x - 0.05, KTABLE.y - 0.1, c["ktable_top"] + 0.15)), 40)


MOVES = {
    "debug": dict(kind="anim", cam=cam_debug, anim=lambda c, t: anim_co(c, t, "co_push", 4.0)),
    "debug_liv": dict(kind="anim", cam=cam_debug_liv, anim=lambda c, t: anim_piano(c, t, "p_title", 4.0)),
    "co_push": _mk("co_push", 6.0, cam_co_push, anim_co, _f_mother, 4.0),
    "co_profile": _mk("co_profile", 5.0, cam_co_profile, anim_co, _f_mother, 2.8),
    "co_officer": _mk("co_officer", 4.5, cam_co_officer, anim_co, _f_mother, 2.4),
    "co_tape": _mk("co_tape", 3.5, cam_co_tape, anim_co, _f_deck, 5.6),
    "co_top": _mk("co_top", 4.0, cam_co_top, anim_co, _f_deck, 4.0),
    "co_meter": _mk("co_meter", 4.0, cam_co_meter, anim_co, _f_meter, 1.8),
    "co_brother": _mk("co_brother", 5.0, cam_co_brother, anim_piano, _f_bench, 2.8),
    "co_brother_side": _mk("co_brother_side", 4.5, cam_co_brother_side, anim_piano, _f_bench, 4.0),
    "p_title": dict(_mk("p_title", 8.5, cam_p_title, anim_piano), title=("CHAPTER 1", "TEN MINUTES HOME", 18, 120)),
    "p_page": _mk("p_page", 5.0, cam_p_page, anim_piano, _f_bench, 4.0),
    "dial": _mk("dial", 5.0, cam_dial, anim_dial, _f_mother, 2.8),
    "hangup": _mk("hangup", 4.5, cam_hangup, anim_dial, lambda c, t: Vector((1.0, -0.6, 1.7)), 4.0),
    "bench": _mk("bench", 5.0, cam_bench, anim_empty_piano, _f_bench, 2.8),
    "pwin": _mk("pwin", 4.5, cam_pwin, anim_empty_piano),
    "k_radio": _mk("k_radio", 5.5, cam_kradio, anim_kitchen, lambda c, t: c["kradio"].location + Vector((0, 0, 0.1)), 2.0),
    "k_window": _mk("k_window", 5.0, cam_kwin, anim_kitchen, lambda c, t: c["P"]["father"].bone_head("head"), 2.8),
    "ring": _mk("ring", 4.0, cam_ring, anim_ring),
    "listen": _mk("listen", 5.0, cam_listen, anim_ring, _f_mother, 2.8),
    "letter": _mk("letter", 5.5, cam_letter, anim_letter, lambda c, t: c["letter"].location, 2.8),
    "read": _mk("read", 5.0, cam_read, anim_letter),
    "thread": _mk("thread", 5.0, cam_thread, anim_police_day, _f_deck, 2.8),
    "door": _mk("door", 5.0, cam_door, anim_police_day, _f_officer, 2.8),
    "call_left": _mk("call_left", 5.0, cam_call_left, anim_call, _f_mother, 2.8),
    "toys": _mk("toys", 4.5, cam_toys, anim_call, lambda c, t: Vector((0.77, -2.38, 0.6)), 2.0),
    "silent": _mk("silent", 5.0, cam_silent, anim_call, _f_deck, 2.8),
    "stairs": _mk("stairs", 5.0, cam_stairs, anim_call, _f_mother, 4.0),
    "co2_back": _mk("co2_back", 5.0, cam_co2_back, anim_call, _f_mother, 4.0),
    "co2_toy": _mk("co2_toy", 4.5, cam_co2_toy, anim_call, lambda c, t: Vector((0.78, -2.5, 0.6)), 1.8),
    "suitcase": _mk("suitcase", 5.0, cam_suitcase, anim_suit),
    "latch": _mk("latch", 4.5, cam_latch, anim_suit),
}
NP = "night+police|mother,officer"
VARIANT_FOR = {"debug": "morning@hall+police|mother,officer", "debug_liv": "morning|brother,sister", "co_push": NP, "co_profile": NP, "co_officer": NP, "co_tape": NP, "co_top": NP, "co_meter": NP,
               "co_brother": "night|brother", "co_brother_side": "night|brother",
               "p_title": "morning@piano|brother,sister", "p_page": "morning@piano|brother,sister",
               "dial": "sunset@hall|mother", "hangup": "sunset@hall|mother", "bench": "night", "pwin": "night+torches",
               "k_radio": "morning@kitchen|mother,father", "k_window": "morning@kitchen|mother,father", "ring": "morning@hall|mother", "listen": "morning@hall|mother",
               "letter": "morning@kitchen+letter|father,detective", "read": "morning@kitchen+letter|father,detective",
               "thread": "morning@hall+police|tech", "door": "morning@hall+police|officer", "call_left": NP, "toys": NP,
               "silent": "night+police", "stairs": "night+police|mother", "co2_back": NP, "co2_toy": NP,
               "suitcase": "morning@kitchen+suitcase|father,detective", "latch": "morning@kitchen+suitcase|father"}
