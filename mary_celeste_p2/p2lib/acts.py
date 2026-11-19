"""Poses for Part 2 (chairs, tables, writing, holding), on top of the shared poses.py.
Rig frame: the person faces -Y, their left is +X, feet on z = 0. Targets given in world space are brought into the
rig frame with Mi = place.inverted() before posing; finish_live() then moves the posed rig to `place`."""
import math
from mathutils import Vector, Matrix
import human as H
import poses as P


def chain(h, pairs):
    for b, d in pairs:
        h.aim(b, Vector(d))


def sit_chair(h, lean=6.0, knee_out=0.08, shin_fwd=0.05, feet=0.0):
    """Upright on a chair: thighs level and forward, shins down, a slight lean from the hips."""
    for sd, sg in H.SIDE.items():
        chain(h, [(f"upperleg01.{sd}", (knee_out * sg, -1, -0.04)), (f"upperleg02.{sd}", (knee_out * sg, -1, -0.04)),
                  (f"lowerleg01.{sd}", (0.02 * sg, -shin_fwd - feet * (0.3 if sd == "L" else -0.2), -1)),
                  (f"lowerleg02.{sd}", (0.02 * sg, -shin_fwd - feet * (0.3 if sd == "L" else -0.2), -1)),
                  (f"foot.{sd}", (0.08 * sg, -1, -0.25))])
    for b, k in (("spine05", 0.1), ("spine04", 0.3), ("spine03", 0.3), ("spine02", 0.2), ("spine01", 0.1)):
        h.rot(b, (1, 0, 0), lean * k)


def seat_offset(h, seat_z):
    """Translation (rig frame z) that puts the sitting bones on a seat at height seat_z."""
    hip = (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2
    return seat_z + 0.085 - hip.z, hip


def sit_place(h, seat_world, yaw_deg, seat_z):
    """World matrix for a seated rig: hips over seat_world (x, y), facing yaw (0 = facing -Y)."""
    dz, hip = seat_offset(h, seat_z)
    R = Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')
    hip_xy = Vector((hip.x, hip.y + 0.02, 0))
    return Matrix.Translation(Vector((seat_world[0], seat_world[1], dz))) @ R @ Matrix.Translation(-hip_xy)


def stand_place(pos, yaw_deg, z=0.0):
    return Matrix.Translation(Vector((pos[0], pos[1], z))) @ Matrix.Rotation(math.radians(yaw_deg), 4, 'Z')


def write(h, Mi, paper_w, side="R", other_on_table=None, lean=20.0, head_pitch=26.0):
    """Seated, writing: the pen hand on the paper (fingers in a pen grip), the other forearm resting on the table."""
    sg = H.SIDE[side]; os_ = "L" if side == "R" else "R"; so = H.SIDE[os_]
    for b, k in (("spine04", 0.35), ("spine03", 0.35), ("spine02", 0.3)):
        h.rot(b, (1, 0, 0), lean * k)
    P.head(h, pitch=head_pitch, yaw=-4 * sg)
    tgt = Mi @ Vector(paper_w)
    P.hand_reach(h, side, tgt + Vector((0.02 * sg, 0.06, 0.075)), elbow=(0.9 * sg, 0.4, 0.45))
    h.aim(f"wrist.{side}", Vector((-0.35 * sg, -0.8, -0.45)))
    pen_grip(h, side)
    if other_on_table is not None:
        P.hand_reach(h, os_, Mi @ Vector(other_on_table) + Vector((0, 0.03, 0.05)), elbow=(0.9 * so, 0.5, 0.45))
        h.aim(f"wrist.{os_}", Vector((0.25 * so, -0.95, -0.2)))      # palm down, hand flat on the page
        P.rest_hand(h, os_, curl=8)


def pen_grip(h, side):
    """Thumb, index and middle pinched round a pen; ring and little finger curled under."""
    sg = H.SIDE[side]
    for k, d in ((1, 30), (2, 35), (3, 25)):
        h.rot(f"finger2-{k}.{side}", (1, 0, 0), d)
        h.rot(f"finger3-{k}.{side}", (1, 0, 0), d + 8)
    for f in (4, 5):
        for k in (1, 2, 3):
            h.rot(f"finger{f}-{k}.{side}", (1, 0, 0), 62 if k == 1 else 70)
    h.rot(f"finger1-2.{side}", (0, 0, sg), 18); h.rot(f"finger1-3.{side}", (1, 0, 0), 15)


def hands_in_lap(h, Mi=None, lap_w=None):
    for sd, sg in H.SIDE.items():
        knee = (h.bone_head(f"upperleg01.{sd}") + h.bone_tail(f"upperleg02.{sd}")) / 2
        tgt = knee + Vector((-0.06 * sg, -0.05, 0.11))
        P.hand_reach(h, sd, tgt, elbow=(0.6 * sg, 0.6, -0.5))
        h.aim(f"wrist.{sd}", Vector((-0.6 * sg, -0.75, -0.2)))
        P.rest_hand(h, sd, curl=26)


def hold_up(h, side, tgt_rig, elbow=None):
    sg = H.SIDE[side]
    P.hand_reach(h, side, tgt_rig, elbow=elbow or (0.7 * sg, 0.3, -0.6))
    P.grip(h, side, 0.75)


def hand_to_temple(h, side="R"):
    """Fingertips pressed to the temple, elbow out on the table: weary."""
    sg = H.SIDE[side]
    eye = h.bone_head(f"eye.{side}") if f"eye.{side}" in h.arm.pose.bones else h.bone_head("head") + Vector((0.03 * sg, -0.08, 0.1))
    tgt = eye + Vector((0.06 * sg, 0.06, -0.06))
    P.hand_reach(h, side, tgt, elbow=(0.6 * sg, -0.5, -0.8))
    h.aim(f"wrist.{side}", Vector((-0.3 * sg, 0.2, 1.0)))
    P.rest_hand(h, side, curl=14)


def yaw_to(frm, to):
    """stand_place yaw (deg) that turns a rig (rest: facing -Y) at `frm` to face `to` (xy only)."""
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return math.degrees(math.atan2(dx, -dy))


def feet_to_floor(h, Mw, floor_z=0.0, tries=None):
    """Seated: swing the shins (about the knee) until the ankles sit at their standing height above the floor.
    Mw = the world matrix the rig will be placed with."""
    ank0 = h.joint("foot.L____head")[2]                 # rest ankle height above the sole
    for sd, sg in H.SIDE.items():
        best = None
        for fwd in [i * 0.05 for i in range(0, 30)]:
            d = Vector((0.02 * sg, -fwd, -1))
            h.aim(f"lowerleg01.{sd}", d); h.aim(f"lowerleg02.{sd}", d)
            h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25)))
            z = (Mw @ h.bone_head(f"foot.{sd}")).z - ank0 - floor_z
            if best is None or abs(z) < abs(best[1]):
                best = (fwd, z)
            if z > 0.004:
                break
        d = Vector((0.02 * sg, -best[0], -1))
        h.aim(f"lowerleg01.{sd}", d); h.aim(f"lowerleg02.{sd}", d)
        h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25)))
        if best[1] > 0.008:          # legs too short for the chair: point the toes down to the floor
            for k in range(1, 12):
                h.aim(f"foot.{sd}", Vector((0.08 * sg, -1, -0.25 - 0.18 * k)))
                toe = Mw @ h.bone_tail(f"foot.{sd}")
                if toe.z - floor_z < 0.03:
                    break
