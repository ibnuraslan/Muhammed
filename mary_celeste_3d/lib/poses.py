"""Natural standing poses for lib/human.py rigs (rest pose faces -Y, character's left is +X, feet on z = 0).
All targets are in the rig's own frame, before the man is placed in the set."""
import math
from mathutils import Vector
import human as H


def stand(h, lean=0.0, hip_shift=0.0, weight="L", twist=0.0):
    """Relaxed stance: weight on one leg, the other knee soft, a little S through the spine."""
    sg = 1 if weight == "L" else -1
    free = "R" if weight == "L" else "L"
    h.rot(f"upperleg01.{free}", (1, 0, 0), -4)          # free leg a touch forward
    h.rot(f"lowerleg01.{free}", (1, 0, 0), 7)           # soft knee
    h.rot(f"foot.{free}", (1, 0, 0), -3)
    h.rot("spine05", (0, 1, 0), sg * 2.0)               # pelvis tilt toward the free side
    h.rot("spine03", (0, 1, 0), -sg * 2.5)
    for b, k in (("spine04", 0.3), ("spine03", 0.35), ("spine02", 0.35)):
        h.rot(b, (1, 0, 0), lean * k)                  # lean forward (toward -Y)
        h.rot(b, (0, 0, 1), twist * k)


def head(h, pitch=0.0, yaw=0.0, tilt=0.0):
    """pitch > 0 looks down; yaw > 0 turns to his left."""
    for b, k in (("neck01", 0.3), ("neck02", 0.3), ("head", 0.4)):
        h.rot(b, (1, 0, 0), pitch * k)
        h.rot(b, (0, 0, 1), yaw * k)
        h.rot(b, (0, 1, 0), tilt * k)


def arm_down(h, side, out=0.12, fwd=0.04, bend=12):
    sg = H.SIDE[side]
    h.aim(f"upperarm01.{side}", (out * sg, -fwd, -1)); h.aim(f"upperarm02.{side}", (out * sg, -fwd, -1))
    d = Vector((0.06 * sg, -math.sin(math.radians(bend)), -math.cos(math.radians(bend))))
    h.aim(f"lowerarm01.{side}", d); h.aim(f"lowerarm02.{side}", d)
    h.aim(f"wrist.{side}", d + Vector((0.02 * sg, -0.05, 0)))


def hand_reach(h, side, target, elbow=(0, 0.3, -1), hand_dir=None):
    H.reach(h, side, target, elbow, hand_dir)


def grip(h, side, amount=1.0):
    """Close the fingers round a handle (a fist with the thumb over)."""
    sg = H.SIDE[side]
    for f in range(2, 6):
        for k in (1, 2, 3):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), (62 if k == 1 else 70) * amount)
    for k in (1, 2, 3):
        h.rot(f"finger1-{k}.{side}", (0, 0, sg), 22 * amount)


def rest_hand(h, side, curl=22):
    sg = H.SIDE[side]
    for f in range(2, 6):
        for k in (1, 2, 3):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), curl * (0.6 + 0.15 * f) * (0.8 if k == 1 else 1.0))
    h.rot(f"finger1-2.{side}", (0, 0, sg), 10)


def palm_point(h, side, depth=0.085):
    """World point in the palm (for placing a handle)."""
    w = h.bone_head(f"wrist.{side}"); t = h.bone_tail(f"wrist.{side}")
    m = h.bone_tail(f"metacarpal3.{side}") if f"metacarpal3.{side}" in h.arm.pose.bones else t
    return w.lerp(m, 0.75)


def cabin(dv, M, board_w, lantern_w, lantern_side="L"):
    """(b) Leaning in over the berth: one hand on the berth board, the other fist holding the lantern up over
    the bedding, head bowed to look at the hollow. M places the rig in the set; targets are world points."""
    h = dv.h; Mi = M.inverted()
    ls = lantern_side; bs = "R" if ls == "L" else "L"; sl = H.SIDE[ls]; sb = H.SIDE[bs]
    stand(h, lean=14, weight=bs, twist=4 * sl)
    head(h, pitch=24, yaw=8 * sl, tilt=2 * sl)
    dv.lids(1.0); dv.brow_knit(1.0)
    bl = Mi @ Vector(board_w)
    hand_reach(h, bs, bl + Vector((0, 0, 0.035)), elbow=(0.7 * sb, 0.5, -0.4))
    h.aim(f"wrist.{bs}", Vector((0.15 * sb, -0.8, -0.6)))
    rest_hand(h, bs, curl=28)
    ln = Mi @ Vector(lantern_w)
    hand_reach(h, ls, ln, elbow=(0.45 * sl, 0.15, -1.0))          # elbow drops under the lantern's weight
    fa = (h.bone_tail(f"lowerarm02.{ls}") - h.bone_head(f"lowerarm01.{ls}")).normalized()
    h.aim(f"wrist.{ls}", (fa + Vector((0, 0, -0.15))).normalized())
    grip(h, ls, 1.0)
