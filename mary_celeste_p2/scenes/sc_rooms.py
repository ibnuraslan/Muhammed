"""Marion parlour (09), schoolroom (10), the hold (16, 18), the white ship maquette (41).
blender -b --python scenes/sc_rooms.py -- SHOT=09"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import stage as S, rooms, cast, acts as A, poses as P, cabin
import ship

SHOT = S.shot_arg() or "09"
HAIR = float(os.environ.get("HAIR", "1.0"))
sc = S.setup(samples=128)
cine = {"sat": 1.05, "exposure": 0.0}

if SHOT == "09":    # Arthur, 7, at the window of his grandmother's house in Marion
    R = rooms.parlour()
    k = cast.Boy()
    P.stand(k.h, weight="L", lean=4)
    P.head(k.h, pitch=-4, yaw=-10)
    sill = R["sill"]
    Mk = A.stand_place((sill.x - 0.48, sill.y - 0.12), 90)
    Mi = Mk.inverted()
    P.hand_reach(k.h, "L", Mi @ (sill + Vector((0.0, 0.12, 0.03))), elbow=(0.7, 0.3, -0.6)); P.rest_hand(k.h, "L", 18)
    P.hand_reach(k.h, "R", Mi @ (sill + Vector((0.0, -0.18, 0.03))), elbow=(-0.7, 0.3, -0.6)); P.rest_hand(k.h, "R", 18)
    k.finish_live(place=Mk, density=HAIR)
    k.look(Vector((8, 0, 1.4)))
    hd = k.h.bone_head("head")
    S.frame([hd, hd - Vector((0, 0, 0.75)), sill + Vector((0, 0.5, 0.9))], Vector((-1.0, -0.75, 0.1)), lens=32, fill=0.9,
            bounds=R["bounds"], fstop=4.0)
    cine = {"sat": 1.05, "exposure": 0.25}

elif SHOT == "10":  # Arthur at a school desk writes on his own slate
    R = rooms.schoolroom()
    k = cast.Boy(seated=True)
    d = R["desk"]; top = R["desk_top"]
    A.sit_chair(k.h, lean=10)
    seat_z = top - 0.3
    Mk = A.sit_place(k.h, (d.x - 0.5, d.y), 90, seat_z)
    A.feet_to_floor(k.h, Mk, 0.003)
    hip = Mk @ ((k.h.bone_head("upperleg01.L") + k.h.bone_head("upperleg01.R")) / 2)
    bench = ship.wood("brown_planks_05", 2.0, tint=(0.6, 0.42, 0.28), name="bench")
    ship.box("bench_top", (hip.x - 0.02, d.y, seat_z - 0.02), (0.3, 0.9, 0.035), bench, bevel=0.005)
    for sy in (-0.38, 0.38):
        ship.box("bench_leg", (hip.x - 0.02, d.y + sy, (seat_z - 0.04) / 2), (0.26, 0.04, seat_z - 0.04), bench)
    Mi = Mk.inverted()
    sl = cabin._slate(Vector((d.x - 0.12, d.y, top)), cabin.M("brown_planks_05", 5.0, tint=(0.7, 0.5, 0.3), name="slframe"))
    A.write(k.h, Mi, sl + Vector((0, -0.03, 0)), side="R", other_on_table=sl + Vector((0.05, 0.2, 0)), lean=16, head_pitch=30)
    k.finish_live(place=Mk, density=HAIR)
    k.look(sl)
    hd = k.h.bone_head("head")
    S.frame([hd, sl, hd - Vector((0, 0, 0.5))], Vector((0.5, -1.0, 0.25)), lens=40, fill=0.8, fstop=2.8)
    cine = {"sat": 1.02, "exposure": 0.2}

elif SHOT in ("16", "18"):   # the hold: men stow barrels in tiers by lantern light; a mallet drives a bung
    R = rooms.hold()
    bd = R["bd"]
    s1 = cast.Sailor(name="Stev1", years=34, jacket=(0.1, 0.07, 0.05), scarf=(0.5, 0.35, 0.1))
    tgt = R["barrels"][35] + Vector((R["bl"] + 0.06, 0, 0))
    P.stand(s1.h, lean=32, weight="L"); P.head(s1.h, pitch=24)
    M1 = A.stand_place((tgt.x + 0.95, tgt.y - 0.3), -90, z=0.55)
    Mi = M1.inverted()
    if SHOT == "16":
        P.hand_reach(s1.h, "R", Mi @ (tgt + Vector((0.42, -0.22, -0.05))), elbow=(-0.8, 0.3, -0.6)); P.rest_hand(s1.h, "R", 28)
        P.hand_reach(s1.h, "L", Mi @ (tgt + Vector((0.42, 0.22, 0.0))), elbow=(0.8, 0.3, -0.6)); P.rest_hand(s1.h, "L", 28)
    else:
        bung = tgt + Vector((0.0, 0, bd / 2 + 0.01))
        P.hand_reach(s1.h, "R", Mi @ (bung + Vector((0.12, -0.08, 0.32))), elbow=(-0.8, 0.0, -0.8)); P.grip(s1.h, "R")
        P.hand_reach(s1.h, "L", Mi @ (bung + Vector((-0.1, 0.12, 0.02))), elbow=(0.8, 0.3, -0.6)); P.rest_hand(s1.h, "L", 30)
    s1.finish_live(place=M1, density=HAIR)
    s1.look(tgt)
    # the barrel being placed
    import pier
    b = pier._inst(bpy.data.objects["wine_barrel_01"], tgt, rz=0); b.rotation_euler = (0, math.pi / 2, 0)
    if SHOT == "18":
        w = s1.h.bone_tail("wrist.R")
        m = ship.cyl("mallet_handle", w + Vector((0, 0, 0.06)), w + Vector((0.0, 0.0, -0.26)), 0.012, mat=cabin.plain("ash", (0.35, 0.22, 0.12), rough=0.6), verts=10)
        hd_ = w + Vector((0, 0, -0.3))
        ship.cyl("mallet_head", hd_ + Vector((0, -0.07, 0)), hd_ + Vector((0, 0.07, 0)), 0.04, mat=cabin.plain("beech", (0.4, 0.26, 0.14), rough=0.6), verts=16)
        cabin.attach(m, s1, "wrist.R"); cabin.attach(bpy.data.objects["mallet_head"], s1, "wrist.R")
        ship.cyl("bung", bung - Vector((0, 0, 0.015)), bung + Vector((0, 0, 0.008)), 0.022, mat=cabin.plain("bungwood", (0.3, 0.2, 0.1), rough=0.7), verts=14)
        hd = s1.h.bone_head("head")
        S.frame([hd, bung, hd - Vector((0, 0, 0.9))], Vector((0.6, -1.0, 0.2)), lens=35, fill=0.9, fstop=2.8)
    else:
        # two more men steady the next barrel as it comes down on the whip from a block on the deck beam
        nb = Vector((2.75, 1.0, 1.35))
        b2 = pier._inst(bpy.data.objects["wine_barrel_01"], nb, rz=0); b2.rotation_euler = (0, math.pi / 2, 0)
        rope = ship.tarred_rope("whip")
        blk = Vector((2.75, 1.0, 2.48))
        ship.box("block", tuple(blk + Vector((0, 0, 0.05))), (0.08, 0.06, 0.14), cabin.plain("blockwood", (0.25, 0.16, 0.08), rough=0.6))
        for dy in (-0.22, 0.22):
            ship.rope("sling", [nb + Vector((-0.28, dy, -0.25)), blk - Vector((0, 0, 0.05))], 0.01, rope)
            ship.rope("sling", [nb + Vector((0.28, dy, -0.25)), blk - Vector((0, 0, 0.05))], 0.01, rope)
        for nm, pos, yrs, jk in (("Stev2", (2.75, 0.05), 26, (0.05, 0.05, 0.06)), ("Stev3", (3.55, 1.05), 41, (0.14, 0.1, 0.07))):
            st = cast.Sailor(name=nm, years=yrs, jacket=jk, cap=(nm == "Stev2"))
            yaw = A.yaw_to(pos, nb)
            Mx = A.stand_place(pos, yaw, z=0.55); Mxi = Mx.inverted()
            P.stand(st.h, lean=10, weight="R"); P.head(st.h, pitch=-8)
            d = (nb - Vector((pos[0], pos[1], nb.z))).normalized()
            side = Vector((-d.y, d.x, 0))
            for sd, sg in (("L", 1), ("R", -1)):
                P.hand_reach(st.h, sd, Mxi @ (nb - d * 0.42 + side * (0.17 * sg) + Vector((0, 0, 0.02))), elbow=(0.9 * sg, 0.3, -0.6))
                P.rest_hand(st.h, sd, curl=22)
            st.finish_live(place=Mx, density=HAIR)
            st.look(nb)
        S.cam(Vector((3.3, -2.0, 2.3)), Vector((1.6, 0.6, 1.15)), lens=24, fstop=5.6)
    cine = {"sat": 1.08, "exposure": 0.15}

elif SHOT == "41":  # a carved model of the ship on the cabin table: the empty chocks, the instrument boxes, the papers
    SET = cabin.build("night", letters=False, chrono="empty")
    T = cabin.TABLE
    chart = cabin.sheet("chart", T + Vector((0.0, 0.0, 0.002)), 0.9, 0.6, cabin.paper_material("chart", ink=True, lines=40), rot=0.05)
    mc = ship.build("MCmodel", sails="found", rail_gap=(-2.7, -0.6, "S"), wet=0.0, detail=True, hatches_off=False, boat_chocks=True)
    for o in mc["coll"].objects:
        if o.type == 'MESH' and any(k in o.name for k in ("_sail_", "_shred", "_jib", "_fstay")):
            o.hide_render = True
    k = 0.024
    mc["root"].scale = (k, k, k); mc["root"].location = T + Vector((-0.06, 0.03, 0.002 + ship.DRAFT * k + 0.004))
    mc["root"].rotation_euler = (0, 0, math.radians(-12))
    bpy.context.view_layer.update()
    # the model's cradle: two carved chocks under the hull
    wd = cabin.M("brown_planks_05", 5.0, tint=(0.75, 0.42, 0.26), name="cradle")
    for dx in (-0.2, 0.2):
        c = mc["root"].matrix_world @ Vector((dx / k, 0, -ship.DRAFT))
        ship.box("cradle", (c.x, c.y, T.z + 0.03), (0.05, 0.2, 0.06), wd, bevel=0.005).rotation_euler = (0, 0, math.radians(-12))
    cabin.sextant_case(T + Vector((0.42, -0.22, 0.0)), wd)
    cabin._chronometer_box(T + Vector((0.42, 0.12, 0.0)), wd, cabin.brass(), state="empty")
    chocks = mc["root"].matrix_world @ Vector((ship.MAIN_HATCH_X, 0, ship.zdeck(ship.MAIN_HATCH_X) + 0.6))
    S.spot("pool_chocks", chocks + Vector((0, 0, 0.9)), chocks, 18, angle=10, blend=0.6, color=(1.0, 0.75, 0.45), radius=0.02)
    S.cam(T + Vector((0.9, -1.0, 0.75)), T + Vector((0.05, 0.0, 0.12)), lens=35, fstop=4.0)
    cine = {"sat": 1.08, "exposure": 0.2}

S.finish(S.out_path(SHOT), cine=cine)
