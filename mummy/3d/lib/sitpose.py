"""Seated poses for lib/human.py rigs, and the placement that puts the pelvis on a real seat.

All pose targets are given in WORLD space; `Seat` works out the rig placement matrix M first (so the
pelvis rests on the seat top and the rig faces `facing`), then poses with M.inverted() targets, exactly like
the shared scenes do (`P.hand_reach(h, side, Mi @ world_point)`).
"""
import math
from mathutils import Vector, Matrix
import human as H
import poses as P

FLESH = 0.095          # hip joint height above the seat surface (buttock thickness)


def hip_mid(h):
    return (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2


class Seat:
    def __init__(self, person, seat_world, facing_deg, frame=Matrix.Identity(4)):
        """seat_world: point on the seat surface under the pelvis; facing_deg: heading (deg, about world Z, in
        `frame`) the person looks along; frame: the boat/room matrix the heading is measured in."""
        self.p = person; h = person.h
        self.seat_world = Vector(seat_world)
        person.seated = True
        H.reset_pose(h)
        hip = hip_mid(h)
        Rz = Matrix.Rotation(math.radians(facing_deg + 90.0), 4, 'Z')     # rig faces -Y; heading 0 = +X
        R = frame.to_3x3().to_4x4() @ Rz
        target = Vector(seat_world) + frame.to_3x3() @ Vector((0, 0, FLESH))
        self.M = Matrix.Translation(target - (R.to_3x3() @ hip)) @ R
        self.Mi = self.M.inverted()

    def local(self, w):
        return self.Mi @ Vector(w)

    def legs(self, feet_world, knees_out=0.1):
        """Thigh-shin IK so each ankle lands at feet_world[side] (world points on the floor + ankle height)."""
        h = self.p.h
        for sd in ("L", "R"):
            sg = H.SIDE[sd]
            b = h.arm.data.bones
            a = b[f"upperleg01.{sd}"].length + b[f"upperleg02.{sd}"].length
            c = b[f"lowerleg01.{sd}"].length + b[f"lowerleg02.{sd}"].length
            S = h.bone_head(f"upperleg01.{sd}"); T = self.local(feet_world[sd])
            dv = T - S; d = min(max(dv.length, abs(a - c) + 1e-3), (a + c) * 0.995); u = dv.normalized()
            cosA = (a * a + d * d - c * c) / (2 * a * d); sinA = math.sqrt(max(0.0, 1 - cosA * cosA))
            pole = Vector((knees_out * sg, -1.0, 0.9)); pole = (pole - u * pole.dot(u)).normalized()
            E = S + u * (a * cosA) + pole * (a * sinA)
            h.aim(f"upperleg01.{sd}", E - S); h.aim(f"upperleg02.{sd}", E - S)
            T2 = S + u * d
            h.aim(f"lowerleg01.{sd}", T2 - E); h.aim(f"lowerleg02.{sd}", T2 - E)
            h.aim(f"foot.{sd}", Vector((0.08 * sg, -1.0, -0.25)))

    def lean(self, fwd=8.0, twist=0.0, side=0.0):
        h = self.p.h
        for b, k in (("spine05", 0.15), ("spine04", 0.25), ("spine03", 0.3), ("spine02", 0.3)):
            h.rot(b, (1, 0, 0), fwd * k)
            if twist:
                h.rot(b, (0, 0, 1), twist * k)
            if side:
                h.rot(b, (0, 1, 0), side * k)

    def hand(self, side, world, elbow=(0.6, 0.3, -0.7), grip=1.0, hand_dir=None):
        h = self.p.h; sg = H.SIDE[side]
        el = Vector((elbow[0] * sg, elbow[1], elbow[2]))
        P.hand_reach(h, side, self.local(world), elbow=el, hand_dir=hand_dir)
        if grip:
            P.grip(h, side, grip)
        else:
            P.rest_hand(h, side, 26)

    def hand_on_thigh(self, side, fwd=0.2):
        h = self.p.h; sg = H.SIDE[side]
        knee = h.bone_tail(f"upperleg02.{side}"); hip = h.bone_head(f"upperleg01.{side}")
        p = hip.lerp(knee, 0.55 + fwd) + Vector((0.02 * sg, 0, 0.075))
        P.hand_reach(h, side, p, elbow=(0.5 * sg, 0.4, -0.6))
        h.aim(f"wrist.{side}", (knee - hip).normalized() + Vector((0, 0, -0.6)))
        P.rest_hand(h, side, 30)

    def head(self, look_world, tilt=0.0, share=0.75):
        """Turn the head (and a little of the neck) toward a world point."""
        h = self.p.h
        hd = h.bone_head("head"); t = self.local(look_world)
        d = (t - hd)
        yaw = math.degrees(math.atan2(d.x, -d.y))          # rig faces -Y; P.head +yaw turns toward +X (fix from P5)
        pitch = -math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        P.head(h, pitch=pitch * share, yaw=yaw * share, tilt=tilt)
        return pitch, yaw

    def place_finish(self, look_world, density=1.0, hair=True):
        self.p.finish(look_at=look_world, place=self.M, density=density, hair=hair)


    def grip_bar(self, side, center, bar_dir, radius=0.024, over=(0, 0, 1), elbow=(0.7, 0.4, -0.6), iters=3):
        """Close a hand round a bar (oar loom, tiller): the palm sits on the bar at `center` (world), the hand lies
        across the bar (fingers pointing perpendicular to it, wrapping over from the `over` side and under), then the
        fingers close round it. The wrist target is corrected until the palm point is on the bar surface."""
        h = self.p.h; sg = H.SIDE[side]
        bar = Vector(bar_dir).normalized(); up = Vector(over).normalized()
        up = (up - bar * up.dot(bar)).normalized()
        palm_goal = Vector(center) + up * (radius + 0.012)          # palm resting on top of the loom
        # fingers point across the bar, away from the body and down over it
        body = self.M @ hip_mid(h)
        away = (Vector(center) - body); away = (away - bar * away.dot(bar) - up * away.dot(up))
        if away.length < 1e-4:
            away = bar.cross(up)
        away.normalize()
        fdir = (away * 0.8 - up * 0.6).normalized()
        el = Vector((elbow[0] * sg, elbow[1], elbow[2]))
        target = palm_goal - fdir * 0.06
        for _ in range(iters):
            P.hand_reach(h, side, self.local(target), elbow=el)
            h.aim(f"wrist.{side}", (self.Mi.to_3x3() @ fdir).normalized())
            palm = self.M @ P.palm_point(h, side)
            target = target + (palm_goal - palm)
        P.hand_reach(h, side, self.local(target), elbow=el)
        h.aim(f"wrist.{side}", (self.Mi.to_3x3() @ fdir).normalized())
        self.wrap_fingers(side, Vector(center), bar, radius)
        return (self.M @ P.palm_point(h, side) - palm_goal).length

    def wrap_fingers(self, side, center, bar, radius):
        """Wrap each finger round the bar by construction: every segment is aimed at the next point of a circle
        about the bar's axis (radius = bar + finger thickness), going over the bar the way the finger already
        points; the thumb wraps from the other side. Works for any hand orientation (rig space throughout)."""
        import math as _m
        h = self.p.h
        c = self.Mi @ Vector(center); ax = (self.Mi.to_3x3() @ Vector(bar)).normalized()
        R = radius + 0.010
        def frame(p):
            v = p - c; along = v.dot(ax); perp = v - ax * along
            return along, perp
        for f in range(1, 6):
            chain = [f"finger{f}-{k}.{side}" for k in (1, 2, 3)]
            if not all(b in h.arm.pose.bones for b in chain):
                continue
            K = h.bone_head(chain[0]); along, perp = frame(K)
            if perp.length < 1e-5:
                continue
            u = perp.normalized(); w = ax.cross(u)                     # circle basis at the knuckle
            d0 = h.bone_tail(chain[0]) - K
            sense = 1.0 if d0.dot(w) >= 0 else -1.0                   # wrap the way the finger points
            if f == 1:
                sense = -sense                                         # the thumb closes from the other side
            ang = 0.0; pcur = K; rr = perp.length
            limit = _m.radians(120 if f == 1 else 250)
            for bn in chain:
                L = h.arm.data.bones[bn].length
                # next point: on the circle (radius R, shrinking from the knuckle's radius), advanced along the arc
                rr_next = max(R, rr - L * 0.7)
                dang = min(L / max(rr_next, 1e-3), limit - ang)
                if dang <= 1e-3:
                    break
                ang += dang
                t = c + ax * along + (u * _m.cos(ang) + w * sense * _m.sin(ang)) * rr_next
                h.aim(bn, t - pcur)
                pcur = h.bone_tail(bn); rr = rr_next
