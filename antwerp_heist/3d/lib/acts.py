"""Posing people in WORLD terms for the Antwerp shots (wraps lib/poses.py, lib/sitpose.py, lib/human.py).

    m = modern.Leonardo()
    st = Stand(m, feet=(x, y), heading=90)        # heading: direction he faces, degrees about Z (0 = +x)
    st.pose(look=(x, y, z)); st.hand('R', world_pt, grip=1.0)
    st.finish(look=(x, y, z))

    se = Seated(m, seat=(x, y, z), heading=-90, feet={...})   # sitpose.Seat underneath
Every helper keeps arms in front of / beside the body (no arms bent behind the back) and hands on something real.
"""
import math
import bpy
from mathutils import Vector, Matrix
import human as H
import poses as P
import sitpose as SP


def place_matrix(feet, heading):
    return Matrix.Translation(Vector((feet[0], feet[1], feet[2] if len(feet) > 2 else 0.0))) @ \
        Matrix.Rotation(math.radians(heading + 90.0), 4, 'Z')


class _Base:
    def local(self, w):
        return self.Mi @ Vector(w)

    def head_to(self, world, share=0.8, tilt=0.0):
        h = self.m.h
        hd = h.bone_head("head"); d = self.local(world) - hd
        yaw = math.degrees(math.atan2(d.x, -d.y))
        pitch = -math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        P.head(h, pitch=max(-35, min(45, pitch * share)), yaw=max(-60, min(60, yaw * share)), tilt=tilt)

    def hand(self, side, world, elbow=(0.6, 0.2, -0.8), grip=0.0, hand_dir=None, curl=26):
        """Wrist to a world point; elbow pole in the rig frame (x toward his own side), hand_dir a world direction."""
        h = self.m.h; sg = H.SIDE[side]
        el = Vector((elbow[0] * sg, elbow[1], elbow[2]))
        hd = (self.Mi.to_3x3() @ Vector(hand_dir)).normalized() if hand_dir is not None else None
        P.hand_reach(h, side, self.local(world), elbow=el, hand_dir=hd)
        if grip:
            P.grip(h, side, grip)
        else:
            P.rest_hand(h, side, curl)

    def palm(self, side):
        return self.M @ P.palm_point(self.m.h, side)

    def wrist(self, side):
        return self.M @ self.m.h.bone_tail(f"wrist.{side}")

    def arm_down(self, side, out=0.16, fwd=0.05, bend=14):
        P.arm_down(self.m.h, side, out=out, fwd=fwd, bend=bend); P.rest_hand(self.m.h, side, 28)

    def finish(self, look=None, density=0.6, hair=True, floor_z=0.0):
        self.m.finish(look_at=look, place=self.M, density=density, hair=hair)
        # feet on the floor: lift him so the lowest sole/heel sits 1.5 mm above floor_z (no sinking into the floor)
        import numpy as np
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        low = None
        for o in self.m.objects:
            if o.type != 'MESH' or not any(k in o.name for k in ("sole", "heel", "boot", "shoe")):
                continue
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            if len(me.vertices):
                co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3); M = np.array(oe.matrix_world)
                z = (co @ M[:3, :3].T + M[:3, 3])[:, 2].min()
                low = z if low is None else min(low, z)
            oe.to_mesh_clear()
        if low is not None and low < floor_z + 0.0015 and low > floor_z - 0.08:
            dz = floor_z + 0.0015 - low
            for o in self.m.objects:
                if o.parent is None:
                    o.location.z += dz
            for k, v in list(self.attached):
                k.location.z += dz
            self.M = Matrix.Translation((0, 0, dz)) @ self.M
        for prop, local in self.attached_pending:
            prop.matrix_world = self.M @ local
        bpy.context.view_layer.update()
        for prop, axis in getattr(self, "fit_pending", []):
            fit_clear(prop, [o for o in self.m.objects if o.type == 'MESH'], (self.M.to_3x3() @ Vector(axis)).normalized())
        return self.m

    attached = ()
    attached_pending = ()

    def attach(self, prop, local_matrix):
        """Place a prop given in the rig frame (e.g. a phone at the ear) once the man is placed."""
        self.attached_pending = list(self.attached_pending) + [(prop, local_matrix)]


class Stand(_Base):
    def __init__(self, m, feet, heading, weight="L", lean=1.5, twist=0.0):
        self.m = m; self.M = place_matrix(feet, heading); self.Mi = self.M.inverted()
        H.reset_pose(m.h)
        P.stand(m.h, lean=lean, weight=weight, twist=twist)
        for sd in ("L", "R"):
            self.arm_down(sd)
        m.lids(0.15)

    def walk(self, phase=0.25, stride=24):
        """A step caught mid-stride (static: used only from behind / through foreground, as the house rules say)."""
        H.pose_walk(self.m.h, phase, stride=stride, arm_swing=14)

    def phone(self, side="R", prop=None):
        """A mobile phone held to the ear: the phone lies against the ear (found on the posed body surface), the hand
        holds it from outside, elbow down and forward. prop: the phone object (placed in finish)."""
        from mathutils.bvhtree import BVHTree
        h = self.m.h; sg = H.SIDE[side]
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        bvh = BVHTree.FromObject(h.body, dg)
        hc = h.bone_head("head") + Vector((0, -0.01, 0.045))
        lat = Vector((sg, 0, 0))
        hit, nrm, _, _ = bvh.ray_cast(hc + lat * 0.25, -lat, 0.3)
        ear = hit if hit is not None else hc + lat * 0.075
        pc = ear + lat * 0.016 + Vector((0, 0.0, -0.02))
        R = Matrix.Rotation(math.radians(-12), 3, 'X')
        for _ in range(30):                     # push the phone out until its inner face clears the skin by 2 mm
            bad = False
            for u in (-0.021, 0.0, 0.021):
                for w in (-0.05, -0.025, 0.0, 0.025, 0.05):
                    q = pc + R @ Vector((-sg * 0.009, u, w))
                    loc, nrm, _, d = bvh.find_nearest(q)
                    if loc is not None and ((q - loc).dot(nrm) < 0.002 or (q - loc).dot(lat) < 0.0):
                        bad = True; break
                if bad:
                    break
            if not bad:
                break
            pc = pc + lat * 0.003
        # hand flat on the phone's outer face: wrist below it, fingers straight up along it (no curl into the head)
        P.hand_reach(h, side, pc + lat * 0.03 + Vector((0, 0.012, -0.1)), elbow=Vector((0.55 * sg, -0.45, -1.0)))
        h.aim(f"wrist.{side}", Vector((0.06 * sg, -0.1, 1.0)))
        P.rest_hand(h, side, 6)
        if prop is not None:
            R = Matrix.Rotation(math.radians(-12), 4, 'X')
            self.attach(prop, Matrix.Translation(pc) @ R)
            self.fit_pending = [(prop, lat)]
        return pc

    def phone_dial(self, side="R", prop=None):
        """Phone held in front of the chest, screen up, thumb on the keys; head bowed to it."""
        h = self.m.h; sg = H.SIDE[side]
        ch = h.bone_head("spine01") if "spine01" in h.arm.pose.bones else h.bone_head("neck01") - Vector((0, 0, 0.3))
        tgt = h.bone_head("neck01") + Vector((-0.06 * sg, -0.3, -0.33))
        P.hand_reach(h, side, tgt, elbow=Vector((0.8 * sg, 0.3, -0.6)))
        h.aim(f"wrist.{side}", Vector((-0.45 * sg, -0.85, 0.35)))
        P.rest_hand(h, side, 40)
        P.head(h, pitch=30, yaw=-8 * sg)
        if prop is not None:
            bpy.context.view_layer.update()
            palm = P.palm_point(h, side)
            n = Vector((0, 0, 1))
            R = Vector((-0.45 * sg, -0.85, 0.35)).normalized().to_track_quat('Z', 'X').to_matrix().to_4x4()
            self.attach(prop, Matrix.Translation(palm + n * 0.02) @ R @ Matrix.Rotation(math.radians(90), 4, 'Y'))
            self.fit_pending = [(prop, n)]
        return tgt

    def hands_front(self, at=None):
        """Hands loosely together in front, below the belt (waiting, listening)."""
        h = self.m.h
        hip = h.bone_head("upperleg01.L").lerp(h.bone_head("upperleg01.R"), 0.5)
        for sd, sg in (("L", 1), ("R", -1)):
            P.hand_reach(h, sd, hip + Vector((0.035 * sg, -0.16, 0.0)), elbow=Vector((sg * 1.0, 0.25, -0.5)))
            h.aim(f"wrist.{sd}", Vector((-sg * 0.8, -0.35, -0.3)))
            P.rest_hand(h, sd, 34)


class Seated(_Base):
    def __init__(self, m, seat, heading, feet=None, lean=8.0, twist=0.0, knees_out=0.12):
        self.m = m
        self.s = SP.Seat(m, seat, heading)
        self.M = self.s.M; self.Mi = self.s.Mi
        h = m.h
        if feet is None:
            f = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0))
            sd = Vector((-f.y, f.x, 0))
            s = Vector(seat)
            feet = {"L": s + f * 0.42 + sd * 0.13 * -1 + Vector((0, 0, -s.z + 0.08)),
                    "R": s + f * 0.42 + sd * 0.13 + Vector((0, 0, -s.z + 0.08))}
            # left foot is on the character's left: sd points to his left when he faces f
            feet = {"L": s + f * 0.42 + sd * 0.14 + Vector((0, 0, -s.z + 0.08)),
                    "R": s + f * 0.42 - sd * 0.14 + Vector((0, 0, -s.z + 0.08))}
        self.s.legs(feet, knees_out=knees_out)
        self.s.lean(fwd=lean, twist=twist)
        for sd in ("L", "R"):
            self.s.hand_on_thigh(sd)
        m.lids(0.15)

    def hand_on_thigh(self, side, fwd=0.2):
        self.s.hand_on_thigh(side, fwd)


class Lean(_Base):
    """Standing at a table, leaning over it on both hands (studying plans)."""
    def __init__(self, m, feet, heading, palms, lean=28.0):
        self.m = m; self.M = place_matrix(feet, heading); self.Mi = self.M.inverted()
        h = m.h
        H.reset_pose(h)
        P.stand(h, lean=lean, weight="L")
        for sd, sg in (("L", 1), ("R", -1)):
            w = Vector(palms[sd]) + Vector((0, 0, 0.035))
            self.hand(sd, w, elbow=(0.7, 0.4, -0.5), curl=18)
            fdir = (self.Mi.to_3x3() @ Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), -0.15))).normalized()
            h.aim(f"wrist.{sd}", fdir + Vector((-0.12 * sg, 0, 0)))
        P.head(h, pitch=30, yaw=0)
        m.lids(0.6)


def _tris_world(o, dg):
    import numpy as np
    from mathutils.bvhtree import BVHTree
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    if not len(me.vertices):
        oe.to_mesh_clear(); return None
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(oe.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles(); tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
    oe.to_mesh_clear()
    return BVHTree.FromPolygons(w.tolist(), tri.reshape(-1, 3).tolist(), all_triangles=True)


def fit_clear(prop, others, axis, lo=-0.03, hi=0.04, step=0.0015):
    """Slide a hand-held prop (and its children) along `axis` to the offset nearest its placed position where none of its
    meshes overlaps any of `others` (the holder's body, hand and clothes). Prints the result."""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    trees = [t for t in (_tris_world(o, dg) for o in others) if t is not None]
    parts = [c for c in prop.children_recursive if c.type == 'MESH']
    base = prop.location.copy()
    offs = sorted([lo + i * step for i in range(int((hi - lo) / step) + 1)], key=abs)
    best = None
    for d in offs:
        prop.location = base + axis * d
        bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
        n = 0
        for c in parts:
            tc = _tris_world(c, dg)
            if tc is None:
                continue
            for t in trees:
                n += len(tc.overlap(t))
            if n:
                break
        if best is None or n < best[1]:
            best = (d, n)
        if n == 0:
            break
    prop.location = base + axis * best[0]
    bpy.context.view_layer.update()
    print(f"FIT {prop.name}: offset {best[0] * 1000:.1f} mm, overlaps {best[1]}")
    return best
