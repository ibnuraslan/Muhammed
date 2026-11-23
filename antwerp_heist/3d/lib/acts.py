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

    def grip(self, side, center, bar_dir, radius=0.012, over=None, elbow=(0.7, 0.4, -0.6)):
        """Close a hand round a bar (sitpose.Seat.grip_bar's solver, for a standing man). Returns the palm gap (m)."""
        fake = SP.Seat.__new__(SP.Seat); fake.p = self.m; fake.M = self.M; fake.Mi = self.Mi
        if over is None:
            hip = self.M @ H.hip_mid(self.m.h) if hasattr(H, "hip_mid") else self.M @ SP.hip_mid(self.m.h)
            o = hip - Vector(center); o.z = 0
            over = o.normalized() if o.length > 1e-4 else Vector((0, -1, 0))
        return fake.grip_bar(side, center, bar_dir, radius=radius, over=over, elbow=elbow)

    def palm(self, side):
        return self.M @ P.palm_point(self.m.h, side)

    def wrist(self, side):
        return self.M @ self.m.h.bone_tail(f"wrist.{side}")

    def arm_down(self, side, out=0.16, fwd=0.05, bend=14):
        P.arm_down(self.m.h, side, out=out, fwd=fwd, bend=bend); P.rest_hand(self.m.h, side, 28)

    def finish(self, look=None, density=0.6, hair=True, floor_z=0.0, floor_fn=None):
        self.m.finish(look_at=look, place=self.M, density=density, hair=hair)
        jk = getattr(self.m, "jacket", None)                 # layering after posing: no trousers/shirt through the coat
        if jk is not None and hasattr(self.m, "_cover"):
            self.m._cover(jk, [getattr(self.m, "shirt", None), getattr(self.m, "trousers", None)], trust_normals=True)
        # feet on the floor: lift him so the lowest sole/heel sits 1.5 mm above floor_z (no sinking into the floor)
        import numpy as np
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        low = None
        for o in self.m.objects:
            if o.type != 'MESH' or not any(k in o.name for k in (("_body", "sole", "heel", "boot", "shoe", "trousers") if getattr(self, "ground_all", False) else ("sole", "heel", "boot", "shoe"))):
                continue
            oe = o.evaluated_get(dg); me = oe.to_mesh()
            if len(me.vertices) and len(me.polygons):
                co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co)
                co = co.reshape(-1, 3); M = np.array(oe.matrix_world)
                me.calc_loop_triangles(); tv = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tv)
                co = co[np.unique(tv)]                                    # surface vertices only (no loose helpers)
                W_ = co @ M[:3, :3].T + M[:3, 3]
                if floor_fn is not None:          # sloped floor: height above the local surface
                    z = float((W_[:, 2] - np.array([floor_fn(y) for y in W_[:, 1]]) + floor_z).min())
                else:
                    z = W_[:, 2].min()
                low = z if low is None else min(low, z)
            oe.to_mesh_clear()
        if low is not None and low < floor_z + 0.0015 and low > floor_z - 0.3:
            dz = floor_z + 0.0015 - low
            for o in self.m.objects:
                if o.parent is None:
                    o.location.z += dz
            for k, v in list(self.attached):
                k.location.z += dz
            self.M = Matrix.Translation((0, 0, dz)) @ self.M
        if getattr(self, "seat_top", None) is not None:
            self._rest_on_seat()
        if getattr(self, "ground_all", False):          # coat skirts and jacket hems lie on the floor, never through it
            bpy.context.view_layer.update()
            hip = self.M @ H_hip(self.m.h)
            self.seat_top = floor_z - 0.004; self.seat_xy = (hip.x, hip.y)
            self._rest_on_seat(margin=0.012, r=1.2, depth=0.6)
            self.seat_top = None
        for prop, local in self.attached_pending:
            prop.matrix_world = self.M @ local
        bpy.context.view_layer.update()
        for prop, axis in getattr(self, "fit_pending", []):
            fit_clear(prop, [o for o in self.m.objects if o.type == 'MESH'], (self.M.to_3x3() @ Vector(axis)).normalized())
        return self.m

    attached = ()
    attached_pending = ()

    def _rest_on_seat(self, margin=0.016, r=0.36, depth=0.25):
        """Seated: cloth that hangs below the seat top over the seat footprint (jacket skirts, trouser seat) is lifted
        to lie on it, like real cloth resting on a chair."""
        import numpy as np
        c = self.seat_xy; z0 = self.seat_top + margin
        for o in self.m.objects:
            if o.type != 'MESH' or not any(k in o.name for k in ("jacket", "trousers", "shirt", "tie")):
                continue
            me = o.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
            M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
            sel = (np.hypot(w[:, 0] - c[0], w[:, 1] - c[1]) < r) & (w[:, 2] < z0) & (w[:, 2] > z0 - depth)
            if not sel.any():
                continue
            w[sel, 2] = z0
            Mi = np.linalg.inv(M); co = w @ Mi[:3, :3].T + Mi[:3, 3]
            me.vertices.foreach_set("co", co.astype(np.float32).ravel()); me.update()

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
    def __init__(self, m, seat, heading, feet=None, lean=8.0, twist=0.0, knees_out=0.12, floor=0.0):
        self.m = m
        self.seat_top = seat[2] - 0.01; self.seat_xy = (seat[0], seat[1])
        seat = (seat[0], seat[1], seat[2] + 0.015)
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
            feet = {"L": s + f * 0.42 + sd * 0.14 + Vector((0, 0, -s.z + floor + 0.08)),
                    "R": s + f * 0.42 - sd * 0.14 + Vector((0, 0, -s.z + floor + 0.08))}
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


class Kneel(_Base):
    ground_all = True
    """Kneeling on both knees (sorting things on the floor): knees on the floor in front of the hips, shins flat
    behind, toes tucked; torso leaning over the work. sit_back=True sits back toward the heels."""
    def __init__(self, m, knees, heading, lean=30.0, sit_back=False):
        self.m = m; h = m.h
        m.asset_boots = True          # keep the fitted shoe shell (the lofted street shoe assumes an upright leg)
        H.reset_pose(h)
        f = Vector((math.cos(math.radians(heading)), math.sin(math.radians(heading)), 0))
        # rig placement: put the hips over the knees (rig frame: faces -Y); compute after posing the legs
        self.M = place_matrix((0, 0, 0), heading); self.Mi = self.M.inverted()
        hip = H_hip(h)
        thigh = h.arm.data.bones["upperleg01.L"].length + h.arm.data.bones["upperleg02.L"].length
        shin = h.arm.data.bones["lowerleg01.L"].length + h.arm.data.bones["lowerleg02.L"].length
        back = 0.55 if sit_back else 0.12                 # how far the thigh leans back from vertical (rad-ish)
        for sd, sg in (("L", 1), ("R", -1)):
            th = Vector((0.06 * sg, -math.sin(back) * -1 * 0.0 - 0.12, -1)).normalized()
            th = Vector((0.07 * sg, -0.15 + (0.35 if sit_back else 0.0), -1)).normalized()
            h.aim(f"upperleg01.{sd}", th); h.aim(f"upperleg02.{sd}", th)
            sh = Vector((0.0, 1.0, 0.04)).normalized()            # shin runs back along the floor (+Y in rig)
            h.aim(f"lowerleg01.{sd}", sh); h.aim(f"lowerleg02.{sd}", sh)
            h.aim(f"foot.{sd}", Vector((0.0, 0.25, -1.0)))
        for b, k in (("spine05", 0.15), ("spine04", 0.25), ("spine03", 0.3), ("spine02", 0.3)):
            h.rot(b, (1, 0, 0), lean * k)
        bpy.context.view_layer.update()
        # knee height: knee joint sits ~5 cm above the floor (kneecap + cloth); place the rig so that is true
        kL = h.bone_head("lowerleg01.L"); kR = h.bone_head("lowerleg01.R"); kc = (kL + kR) / 2
        target = Vector((knees[0], knees[1], 0.055))
        R = Matrix.Rotation(math.radians(heading + 90.0), 4, 'Z')
        self.M = Matrix.Translation(target - R.to_3x3() @ kc) @ R; self.Mi = self.M.inverted()
        for sd in ("L", "R"):
            self.arm_down(sd)
        m.lids(0.4)


class SitFloor(_Base):
    ground_all = True
    """Sitting on the floor (collapsed, fainted): legs out in front, knees soft, back against a wall or another
    person's support, head dropped. back_lean in degrees (0 = upright)."""
    def __init__(self, m, hips, heading, back_lean=-18.0, head_drop=25.0):
        self.m = m; h = m.h
        m.asset_boots = True
        H.reset_pose(h)
        for sd, sg in (("L", 1), ("R", -1)):
            th = Vector((0.12 * sg, -1.0, -0.12)).normalized()
            h.aim(f"upperleg01.{sd}", th); h.aim(f"upperleg02.{sd}", th)
            sh = Vector((0.08 * sg, -1.0, -0.35)).normalized()
            h.aim(f"lowerleg01.{sd}", sh); h.aim(f"lowerleg02.{sd}", sh)
            h.aim(f"foot.{sd}", Vector((0.15 * sg, -0.4, 1.0)))
        for b, k in (("spine05", 0.2), ("spine04", 0.25), ("spine03", 0.3), ("spine02", 0.25)):
            h.rot(b, (1, 0, 0), back_lean * k)
        P.head(h, pitch=head_drop, yaw=8, tilt=10)
        bpy.context.view_layer.update()
        hip = H_hip(h)
        R = Matrix.Rotation(math.radians(heading + 90.0), 4, 'Z')
        self.M = Matrix.Translation(Vector((hips[0], hips[1], 0.1)) - R.to_3x3() @ hip) @ R; self.Mi = self.M.inverted()
        for sd in ("L", "R"):
            self.arm_down(sd, out=0.25, fwd=0.2, bend=30)
        m.lids(1.0)


def H_hip(h):
    return (h.bone_head("upperleg01.L") + h.bone_head("upperleg01.R")) / 2


def hands_to_face(st, side="both"):
    """Grief: hands up over the face, elbows in, head bowed (always shot from behind or in silhouette)."""
    h = st.m.h
    P.head(h, pitch=28, yaw=0)
    bpy.context.view_layer.update()
    hc = h.bone_head("head") + Vector((0, -0.11, 0.02))
    for sd, sg in (("L", 1), ("R", -1)):
        if side != "both" and sd != side:
            continue
        P.hand_reach(h, sd, hc + Vector((0.035 * sg, -0.02, -0.06)), elbow=Vector((0.25 * sg, -0.5, -1.0)))
        h.aim(f"wrist.{sd}", Vector((-0.25 * sg, -0.25, 1.0)))
        P.rest_hand(h, sd, 25)
