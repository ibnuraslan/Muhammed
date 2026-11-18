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
    Mk = A.stand_place((sill.x - 0.38, sill.y - 0.12), 90)
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
    k = cast.Boy()
    d = R["desk"]; top = R["desk_top"]
    A.sit_chair(k.h, lean=10)
    seat_z = top - 0.3
    Mk = A.sit_place(k.h, (d.x - 0.5, d.y), 90, seat_z)
    try:
        S.place_model("SchoolChair_01", (d.x - 0.52, d.y, 0), size=0.8, rot_z=math.radians(-90))
    except Exception:
        ship.box("stool", (d.x - 0.52, d.y, seat_z / 2), (0.36, 0.36, seat_z), cabin.plain("stoolwood", (0.3, 0.2, 0.12)))
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
    tgt = R["barrels"][-1] + Vector((0.6, 0, 0))
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
        S.frame([hd, bung], Vector((0.3, -1.0, 0.7)), lens=35, fill=0.9, fstop=2.8)
    else:
        s2 = cast.Sailor(name="Stev2", years=26, jacket=(0.05, 0.05, 0.06), cap=True)
        P.stand(s2.h, lean=10, weight="R"); P.head(s2.h, pitch=-30)
        M2 = A.stand_place((0.9, 0.6), 160, z=0.55)
        P.hand_reach(s2.h, "L", s2.h.bone_head("upperarm01.L") + Vector((0.1, -0.1, 0.55)), elbow=(0.8, 0.3, -0.4)); P.grip(s2.h, "L")
        P.hand_reach(s2.h, "R", s2.h.bone_head("upperarm01.R") + Vector((-0.1, -0.1, 0.5)), elbow=(-0.8, 0.3, -0.4)); P.grip(s2.h, "R")
        s2.finish_live(place=M2, density=HAIR)
        S.cam(Vector((3.3, 2.2, 2.35)), Vector((-0.6, -0.2, 1.1)), lens=24, fstop=5.6)
    cine = {"sat": 1.08, "exposure": 0.15}

elif SHOT == "41":  # white maquette of the ship from above; warm pools where things are missing
    mc = ship.build("MC", sails="found", rail_gap=(-2.7, -0.6, "S"), wet=0.0, detail=False)
    clay = cabin.plain("clay", (0.62, 0.58, 0.52), rough=0.6)
    for o in mc["coll"].objects:
        if o.type == 'MESH':
            if any(k in o.name for k in ("_sail", "_furl", "_shred", "_jib", "_fstay", "_main_furl", "_gaff_furl")):
                o.hide_render = True
            o.data.materials.clear(); o.data.materials.append(clay)
        elif o.type == 'CURVE':
            o.hide_render = True
    ship.box("table", (0, 0, -3.2), (60, 30, 0.2), cabin.plain("maqtable", (0.08, 0.05, 0.035), rough=0.5))
    bpy.context.view_layer.update()
    for o in mc["coll"].objects:
        if o.type == 'MESH':
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
            if min(v.z for v in bb) > 3.2 or max(v.z for v in bb) > 9:
                o.hide_render = True
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.025, 0.02, 1)
    S.area("MaqKey", Vector((-14, -18, 30)), Vector((0, 0, 0)), 9000, size=6, color=(1, 0.95, 0.88))
    for (x, y, z), lab in (((ship.MAIN_HATCH_X, 0, ship.zdeck(ship.MAIN_HATCH_X) + 0.8), "boat"),
                           ((-ship.L / 2 + 5.8, 0, ship.zdeck(-10) + 1.2), "cabin"),
                           ((-1.65, -ship.B / 2, ship.zdeck(-1.65) + 1.0), "gap")):
        S.spot(f"pool_{lab}", Vector((x, y, z + 9)), Vector((x, y, z)), 2600, angle=16, blend=0.5, color=(1.0, 0.62, 0.3), radius=0.2)
    S.cam(Vector((6, -34, 30)), Vector((-1.5, 0, 0.5)), lens=50)
    cine = {"sat": 1.0, "exposure": 0.0}

S.finish(S.out_path(SHOT), cine=cine)
