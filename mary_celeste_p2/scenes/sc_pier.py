"""New York pier shots. blender -b --python scenes/sc_pier.py -- SHOT=01"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import stage as S, pier, cast, acts as A, poses as P
import ship

SHOT = S.shot_arg() or "01"
HAIR = float(os.environ.get("HAIR", "1.0"))
sc = S.setup(samples=128)
cine = {"sat": 1.08, "exposure": -0.05}

SET = pier.build("morning")
SM = SET["ship_M"]
PY = pier.PIER_W / 2


def stevedore(name, pos, yaw, pose="guide", target=None, years=30, jacket=(0.08, 0.06, 0.04), scarf=(0.4, 0.08, 0.04), hair=0.4):
    s = cast.Sailor(name=name, years=years, jacket=jacket, scarf=scarf)
    if target is not None and yaw is None:
        yaw = A.yaw_to(pos, target)
    Mw = A.stand_place(pos, yaw, z=pier.DECK)
    Mi = Mw.inverted()
    if pose == "guide" and target is not None:
        P.stand(s.h, lean=8, weight="L")
        P.head(s.h, pitch=-18)
        for sd, dx in (("L", 0.16), ("R", -0.16)):
            P.hand_reach(s.h, sd, Mi @ (target + Vector((dx, -0.38, -0.05))), elbow=(0.9 * (1 if sd == "L" else -1), 0.3, -0.6))
            P.rest_hand(s.h, sd, curl=20)
    elif pose == "roll" and target is not None:
        P.stand(s.h, lean=34, weight="R")
        P.head(s.h, pitch=18)
        for sd, dx in (("L", 0.18), ("R", -0.18)):
            P.hand_reach(s.h, sd, Mi @ (target + Vector((dx, 0, 0.05))), elbow=(0.8 * (1 if sd == "L" else -1), 0.4, -0.6))
            P.rest_hand(s.h, sd, curl=24)
    else:
        P.stand(s.h, weight="R")
        P.arm_down(s.h, "L"); P.arm_down(s.h, "R"); P.rest_hand(s.h, "L"); P.rest_hand(s.h, "R")
    s.finish_live(place=Mw, density=hair)
    if target is not None:
        s.look(target)
    return s


def briggs_on_pier(pos, yaw, look, head=(0, 0)):
    yaw = A.yaw_to(pos, look) if yaw is None else yaw
    b = cast.Briggs()
    P.stand(b.h, weight="L", lean=-2)
    P.head(b.h, pitch=head[0], yaw=head[1])
    # hands clasped behind his back
    Mw = A.stand_place(pos, yaw, z=pier.DECK)
    back = b.h.bone_head("spine04") + Vector((0, 0.2, -0.28))
    P.hand_reach(b.h, "L", back + Vector((0.03, 0, 0)), elbow=(0.6, 0.6, -0.4)); P.rest_hand(b.h, "L", 30)
    P.hand_reach(b.h, "R", back + Vector((-0.03, 0.02, 0.02)), elbow=(-0.6, 0.6, -0.4)); P.rest_hand(b.h, "R", 30)
    b.finish_live(place=Mw, density=HAIR)
    b.look(look)
    _hat(b)
    return b


def _hat(person):
    """A dark wool felt hat with a low crown and a narrow brim (a master's shore-going hat)."""
    import cabin
    h = person.h
    bpy.context.view_layer.update()
    hb = h.arm.matrix_world @ h.arm.pose.bones["head"].matrix
    R = hb.to_3x3().normalized() @ h.arm.data.bones["head"].matrix_local.to_3x3().inverted()
    ec = sum((e.matrix_world.translation for e in h.eyes), Vector()) / 2
    c = ec + R @ Vector((0, 0.025, 0.075))
    felt = cabin.plain("felt", (0.02, 0.018, 0.016), rough=0.8)
    prof = [(0.0, 0.11), (0.095, 0.105), (0.1, 0.0), (0.16, 0.0), (0.165, -0.008), (0.0, -0.008)]
    o = cabin.lathe("hat", prof, felt, center=(0, 0, 0), n=40)
    o.location = c; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = R.to_quaternion(); o.scale = (1.0, 1.12, 1.0)
    cabin.attach(o, person, "head")
    return o


if SHOT == "01":   # EWS: the pier from over the river, the Mary Celeste alongside, South Street behind
    for k, (x, y, yaw) in enumerate(((-12, 2, 30), (-18, -2.5, 160), (-6, 4.2, -70))):
        stevedore(f"st{k}", (x, y), yaw, pose="stand", hair=0.2)
    S.cam(Vector((pier.SHIP_X + 30, pier.SHIP_Y + 16, 7.5)), Vector((pier.SHIP_X - 12, 2, 5.5)), lens=26)
    cine = {"sat": 1.1, "exposure": 0.0}

elif SHOT == "04":  # WS: Briggs on the pier looks along her waterline; hands behind his back; a small nod
    tgt = SM @ Vector((ship.L / 2 - 6, -ship.B / 2, 0.2))
    b = briggs_on_pier((pier.SHIP_X - 8, PY - 1.4), None, tgt, head=(14, 0))
    hd = b.h.bone_head("head")
    S.frame([hd + Vector((0, 0, 0.15)), hd - Vector((0, 0, 1.7)), hd + Vector((3.0, 2.5, -0.8))], Vector((-0.25, -1.0, 0.15)), lens=32, fill=0.9, fstop=5.6)

elif SHOT == "05":  # low on the water: her hull at the waterline, the reflection, piles beside
    a = SM @ Vector((ship.L / 2 - 2, -ship.B / 2 - 1.0, 0.25))
    S.cam(SM @ Vector((ship.L / 2 + 5, ship.B / 2 + 4.0, 0.55)), SM @ Vector((-2, ship.B / 2, 1.2)), lens=35, fstop=8)

elif SHOT == "06":  # MCU: Briggs looks up into the rigging, thoughtful
    b = briggs_on_pier((pier.SHIP_X - 3, PY - 1.2), None, SM @ Vector((-1.5, 0, 18)), head=(-30, 10))
    hd = b.h.bone_head("head")
    # MS low from behind: his silhouette against the rigging and sky
    S.frame([hd + Vector((0, 0, 0.15)), hd - Vector((0, 0, 0.9))], Vector((-0.35, -1.0, -0.45)), lens=50, fill=0.85, fstop=2.8,
            aim_offset=(0, 0, 0.5))

elif SHOT == "15":  # WS: a barrel swings aboard in its sling; two stevedores guide it, one rolls the next
    sl = SET["sling_barrel"]
    stevedore("g1", (sl.x - 0.7, sl.y - 0.95), None, pose="guide", target=sl - Vector((0, 0, 0.4)))
    stevedore("g2", (sl.x + 0.8, sl.y - 0.85), None, pose="guide", target=sl - Vector((0, 0, 0.4)), years=45, jacket=(0.12, 0.1, 0.08))
    bd, bh = SET["barrel_size"]
    rb = pier._inst(SET["barrel_proto"][0], Vector((sl.x - 4.2, PY - 2.0, pier.DECK + bh / 2 - 0.0)) - Vector((0, 0, bh / 2)), rz=1.57, lying=True)
    stevedore("r1", (sl.x - 4.9, PY - 2.0), None, pose="roll", target=Vector((sl.x - 4.2, PY - 2.0, pier.DECK + bd / 2 + 0.1)))
    S.cam(Vector((sl.x - 4.5, -1.5, pier.DECK + 1.5)), sl + Vector((-1.5, 0, -0.4)), lens=30, fstop=5.6)

elif SHOT == "20":  # 5 November: a steam tug tows her off the pier and out into the river
    import seaset as W
    mc = SET["ship"]
    mc["root"].location = (pier.SHIP_X + 26, pier.SHIP_Y + 14, 0); mc["root"].rotation_euler = (0, 0, math.radians(22))
    bpy.context.view_layer.update()
    SM = mc["root"].matrix_world.copy()
    t = W.tug("tug", SM @ Vector((ship.L / 2 + 38, 2, 0)), 22)
    ship.rope("hawser", [SM @ Vector((ship.L / 2 + 1, 0, 3.0)), SM @ Vector((ship.L / 2 + 18, 0, 0.6)), SM @ Vector((ship.L / 2 + 30, 0, 1.6))],
              0.05, mc["mats"]["rope"])
    S.cam(Vector((pier.SHIP_X - 4, pier.PIER_W / 2 - 1.5, pier.DECK + 1.7)), SM @ Vector((ship.L / 2 + 8, 0, 5)), lens=26)
    cine = {"sat": 1.1, "exposure": 0.0}

S.finish(S.out_path(SHOT), cine=cine)
