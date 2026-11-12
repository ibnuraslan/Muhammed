# People on the beach (exec'd by 03_anim.py after lib + anim_lib).  All of them leave frame inland before impact.
import math
from mathutils import Vector, Matrix
G = globals()
from mathutils.bvhtree import BVHTree as _BVH
_TT = _BVH.FromObject(bpy.data.objects["Terrain"], bpy.context.evaluated_depsgraph_get())
def ground_z(x, y):
    hit = _TT.ray_cast(Vector((x, y, 50.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else terrain_h(x, y)
G["ground_z"] = ground_z           # anim_lib's Human uses this module-level name

def yaw_of(d): return math.degrees(math.atan2(d.x, -d.y))
def fwv(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector((0, -1, 0))
def lftv(yaw): return Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector((1, 0, 0))

class Person:
    def __init__(self, name):
        self.o = bpy.data.objects[name]; self.H = Human(make_human_ctrl(self.o)); self.name = name
        B = self.H.r.BN
        self.sh = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.L = (B["wrist.L"].head_local - B["upperarm01.L"].head_local).length
        self.st = {}      # frame -> (pos3 root ground point, yaw, mode, phase)
        self.hand_limits()
        self.arm = {}     # frame -> dict(side -> mode)
    # ---------------------------------------------------------------- body
    def stand(self, f0, f1, pos, yaw, step=6, crouch=0.0, flex=4.0, head=(0, 0), sway=1.0):
        pos = Vector((pos[0], pos[1], 0)); H = self.H
        fr = list(range(f0, f1 + 1, step)) + ([f1] if (f1 - f0) % step else [])
        for f in fr:
            ph = (f - f0) / 60.0
            for s in "LR":
                H.key_foot(s, f, H.foot_xy(s, pos, yaw), yaw)
            gz = ground_z(pos.x, pos.y)
            hd = head(f) if callable(head) else head
            sd = (sum(map(ord, self.name)) % 97) / 97.0 * 6.28
            hd = (hd[0] + 3.0 * math.sin(ph * 1.1 + sd), hd[1] + 14.0 * math.sin(ph * 0.7 + sd) + 6.0 * math.sin(ph * 1.9 + 2 * sd))
            fl = flex(f) if callable(flex) else flex
            cr = crouch(f) if callable(crouch) else crouch
            sh_ = 0.025 * math.sin(ph * 0.9 + (sum(map(ord, self.name)) % 13))
            lat = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector((sh_, 0, 0))
            H.key_root(f, Vector((pos.x + lat.x, pos.y + lat.y, gz + H.root_head.z - 0.02 - cr - 0.008 * math.sin(ph * 2.6))), yaw=yaw,
                       flex=fl * 0.4, side=sway * 2.5 * math.sin(ph * 0.9 + (sum(map(ord, self.name)) % 13)))
            H.key_spine(f, flex=fl, twist=sway * 3 * math.sin(ph * 0.9), head=hd)
            self.st[f] = (pos.copy(), yaw, "stand", 0.0)
        return pos
    def go(self, pts, f0, f1, run=False, step=2, yaw_fn=None, head=(0, 0), kid=False):
        pts = [Vector((p[0], p[1], 0)) for p in pts]
        if yaw_fn is None and f0 in self.st and self.st[f0][2] == "stand":
            y_st = self.st[f0][1]; y_go = yaw_of(pts[1] - pts[0])
            dy_ = (y_go - y_st + 180) % 360 - 180
            yaw_fn_auto = None
            self._turn = (f0, y_st, y_st + dy_)
        else:
            self._turn = None
        seg = [(b - a).length for a, b in zip(pts, pts[1:])]; tot = sum(seg)
        def path(f):
            u = min(1, max(0, (f - f0) / (f1 - f0)))
            d = tot * (u * u * (3 - 2 * u) * 0.25 + u * 0.75)       # ease in/out a little
            for a, b, l in zip(pts, pts[1:], seg):
                if d <= l or b is pts[-1]:
                    return a.lerp(b, min(1, d / l if l else 1))
                d -= l
            return pts[-1]
        def yaw_auto(f):
            a, b = path(max(f0, f - 6)), path(min(f1, f + 6))
            dv = b - a
            if dv.length < 1e-3: dv = pts[-1] - pts[0]
            return yaw_of(dv)
        yf = yaw_fn or yaw_auto
        if self._turn and yaw_fn is None:
            ft0, ya, yb = self._turn
            nt_ = max(14.0, abs(yb - ya) / 5.0)
            yf = lambda f, ya=ya, yb=yb, ft0=ft0, nt_=nt_: (ya + (yb - ya) * sstep((f - ft0) / nt_)) if f < ft0 + nt_ else yaw_auto(f) + 0 * yb
        sc_ = 0.75 if kid else 1.0
        if run:
            self.H.walk(path, yf, f0, f1, stride=1.75 * sc_, duty=0.4, lift=0.16 * sc_, bob=0.045, crouch=0.07, lean=12, step=step)
        else:
            self.H.walk(path, yf, f0, f1, stride=0.72 * sc_, duty=0.62, lift=0.07, bob=0.02, crouch=0.03, lean=4, step=step)
        dist = 0.0; prev = path(f0)
        for f in range(f0, f1 + 1):
            p = path(f); dist += (p - prev).length; prev = p
            self.st[f] = (p.copy(), yf(f), "run" if run else "walk", dist / ((1.75 if run else 0.72) * sc_))
        if head != (0, 0):
            for f in range(f0, f1 + 1, 6):
                self.H.key_spine(f, flex=12 if run else 4, head=head(f) if callable(head) else head)
        return path(f1)
    # ---------------------------------------------------------------- arms
    def key_arms(self, f0, f1, mode, step=3):
        """mode(f) -> dict side -> name ; names: hang swing run point shade wave reach hold"""
        H = self.H; L = self.L
        frames = [f for f in range(f0, f1 + 1, step)] + [f1]
        for f in frames:
            ks = sorted(self.st)
            fk = min(ks, key=lambda k: abs(k - f))
            pos, yaw, md, ph = self.st[fk]
            fw = fwv(yaw); lf = lftv(yaw); up = Vector((0, 0, 1))
            gz = ground_z(pos.x, pos.y)
            Mroot = Matrix.Translation(Vector((pos.x, pos.y, gz))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
            m = mode(f)
            for s in "LR":
                sx = 1 if s == "L" else -1
                side = lf * sx
                shw = Mroot @ Vector((self.sh[s].x, self.sh[s].y, self.sh[s].z - 0.03))
                nm = m.get(s, "hang") if isinstance(m, dict) else m
                sw = math.sin(2 * math.pi * ph + (0 if s == "L" else math.pi))
                if md == "stand" and nm in ("swing", "run"): nm = "hang"
                if nm == "hang":
                    W = shw + side * 0.26 + fw * 0.05 + up * (-0.83 * L); d = (-up + fw * 0.1).normalized(); n = (-side - fw * 0.8).normalized()
                    pole = shw + side * 0.25 - fw * 0.45 - up * 0.2
                elif nm == "swing":
                    W = shw + side * 0.26 + fw * (0.28 * L * sw) + up * (-0.82 * L); d = (-up + fw * 0.2).normalized(); n = (-side - fw * 0.8).normalized()
                    pole = shw + side * 0.25 - fw * 0.45 - up * 0.2
                elif nm == "run":
                    W = shw + side * 0.23 + fw * (0.25 * L + 0.42 * L * sw) + up * (-0.55 * L + 0.1 * L * sw); d = (fw + up * 0.3).normalized(); n = -side
                    pole = shw + side * 0.2 - fw * 0.5 - up * 0.35
                elif nm == "point":
                    W = shw + fw * 0.93 * L + up * (0.2 + 0.05 * math.sin(f * 0.13)) * L + side * (0.05 + 0.04 * math.sin(f * 0.07)); d = (fw + up * 0.2).normalized(); n = -up
                    pole = shw + side * 0.4 - up * 0.3
                elif nm == "shade":
                    W = shw + fw * 0.5 * L + up * 0.55 * L - side * 0.06; d = (-side + up * 0.2).normalized(); n = -up
                    pole = shw + side * 0.5 + up * 0.1
                elif nm == "wave":
                    k = math.sin(f * 0.35)
                    W = shw + up * 0.9 * L + side * (0.25 + 0.15 * k) * L + fw * 0.15 * L; d = (up + side * 0.3 * k).normalized(); n = fw
                    pole = shw + side * 0.5 - fw * 0.2
                elif nm.startswith("reach"):
                    tgt = self.reach_target
                    W = tgt + up * 0.06; d = (fw * 0.3 - up).normalized(); n = -fw
                    pole = shw + side * 0.4 + up * 0.1
                elif nm == "hold":
                    W = shw + fw * 0.72 * L + up * (-0.32 * L) - side * 0.02; d = (fw - side * 0.6).normalized(); n = up
                    pole = shw + side * 0.4 - fw * 0.1 - up * 0.4
                H.key_hand(s, f, W, d, n, pole=pole)

    def hand_limits(self):
        """client hands rule: no backward bends; relaxed curled default"""
        R_ = math.radians
        for pb in self.o.pose.bones:
            n = pb.name
            if n.startswith("finger"):
                pb.rotation_mode = 'XYZ'
                thumb = n.startswith("finger1")
                c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                if thumb:
                    c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-15), R_(60), R_(-25), R_(25), R_(-30), R_(30)
                else:
                    c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = 0.0, R_(90), 0.0, 0.0, R_(-10), R_(10)
                pb.rotation_euler = (R_(10 if thumb else 18), 0, 0)
                pb.keyframe_insert("rotation_euler", frame=1)
            elif n.startswith("wrist."):
                c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                c.min_x, c.max_x, c.min_y, c.max_y, c.min_z, c.max_z = R_(-60), R_(60), R_(-40), R_(40), R_(-25), R_(25)
    def hide_after(self, f):
        for ob in [self.o] + list(self.o.children):
            key_hide(ob, [(1, False), (f, True)])

T = lambda t: F(t)
P = {n: Person(n) for n in ("Fisher", "LocalW", "TouristM", "TouristW", "KidA", "KidB", "OldM", "LocalM")}
for p in P.values():
    p.o.location = (0, 0, 0)

# ---------------------------------------------------------------- beat 1–4 on the beach (0 – 11 s)
# kids: chase the receding water, then run around on the exposed sand
k = P["KidA"]
k.go([(3.5, 10), (4.5, 30), (5.0, 48)], T(0), T(3.4), run=True, kid=True)
k.go([(5.0, 48), (8, 56), (4, 64), (-1, 57), (2, 50)], T(3.4), T(7.6), run=True, kid=True)
k.stand(T(7.6), T(8.6), (2, 50), 180, head=(-8, 0))
k.go([(2, 50), (0, 47.5), (-3.5, 44.8)], T(8.6), T(10.4), kid=True)
k.stand(T(10.4), T(12.4), (-3.5, 44.8), 180, head=(-10, 0))
k.go([(-3.5, 44.8), (-3.7, 42.3)], T(12.4), T(12.95), run=True, kid=True)
P["KidA"].key_arms(T(0), T(12.8), lambda f: {"R": "point"} if T(10.9) <= f <= T(12.2) else ("swing" if T(8.6) <= f <= T(10.4) else "run"))
k = P["KidB"]
k.go([(6.0, 8), (6.5, 28), (7.5, 44)], T(0.1), T(3.6), run=True, kid=True)
k.go([(7.5, 44), (11, 52), (8, 60), (4, 54)], T(3.6), T(7.4), run=True, kid=True)
k.stand(T(7.4), T(8.8), (4, 54), 190, head=(-10, 0))
k.go([(4, 54), (6, 50), (8.5, 47)], T(8.8), T(10.6), kid=True)
k.stand(T(10.6), T(12.4), (8.5, 47), 185, head=(-10, 0))
k.go([(8.5, 47), (8.6, 44.5)], T(12.4), T(12.95), run=True, kid=True)
k.key_arms(T(0), T(12.8), lambda f: {"L": "point"} if T(11.2) <= f <= T(12.3) else ("swing" if T(8.8) <= f <= T(10.6) else "run"))
# adults walk out onto the wet sand, point, pick up a fish, look; one man shouts
q = P["TouristW"]
q.stand(T(0), T(4.6), (-4, 3), 175, head=lambda f: (-5, 15 * math.sin(f / 50)))
q.go([(-4, 3), (-4.5, 22), (-5.5, 39)], T(4.6), T(8.2))
q.stand(T(8.2), T(12.4), (-5.5, 39), 180, head=(-8, 0))
q.go([(-5.5, 39), (-5.7, 36.5)], T(12.4), T(12.95), run=True)
q.key_arms(T(0), T(12.8), lambda f: {"R": "point"} if T(6.0) <= f <= T(7.4) else ({"L": "shade"} if T(8.4) <= f <= T(10.0) else {"R": "point"} if T(10.6) <= f <= T(12.3) else {"L": "swing", "R": "swing"}) if f < T(12.4) else "run")
q = P["TouristM"]
q.stand(T(0), T(5.0), (-1.5, 1), 180)
q.go([(-1.5, 1), (-2, 20), (-1.5, 42)], T(5.0), T(8.6))
q.stand(T(8.6), T(12.4), (-1.5, 42), 182, head=(-6, 0))
q.go([(-1.5, 42), (-1.7, 39.5)], T(12.4), T(12.95), run=True)
q.key_arms(T(0), T(12.8), lambda f: {"L": "shade"} if T(8.0) <= f <= T(10.2) else {"R": "point"} if T(10.8) <= f <= T(12.3) else ("run" if f > T(12.4) else "swing"))
q = P["LocalW"]
q.stand(T(0), T(5.4), (9, 6), 190)
q.go([(9, 6), (10, 25), (10.5, 46)], T(5.4), T(8.8))
q.stand(T(8.8), T(12.4), (10.5, 46), 185, head=(-5, 5))
q.go([(10.5, 46), (10.3, 43.5)], T(12.4), T(12.95), run=True)
q.key_arms(T(0), T(12.8), lambda f: {"R": "point"} if T(7.6) <= f <= T(9.6) or T(11.2) <= f <= T(12.3) else ("run" if f > T(12.4) else "swing"))
q = P["LocalM"]
q.stand(T(0), T(5.2), (16, 10), 185)
q.go([(16, 10), (17, 28), (17.5, 44)], T(5.2), T(8.6))
q.stand(T(8.6), T(12.4), (17.5, 44), 175)
q.go([(17.5, 44), (17.3, 41.5)], T(12.4), T(12.95), run=True)
q.key_arms(T(0), T(12.8), lambda f: {"L": "point"} if T(9.0) <= f <= T(10.0) or T(10.9) <= f <= T(12.3) else ("run" if f > T(12.4) else "swing"))
q = P["OldM"]
q.stand(T(0), T(10.6), (-11, -3), 170, head=lambda f: (-6, 0))
q.go([(-11, -3), (-12, -18)], T(10.6), T(12.8), run=False)
q.key_arms(T(0), T(12.8), lambda f: {"R": "shade"} if T(6.5) <= f <= T(10.4) else "swing")
# Fisher: walks to a stranded fish, bends and picks it up, holds it, sees the wave, drops it, turns and shouts
q = P["Fisher"]
FP = Vector((4.5, 54.5)); FISHPICK = Vector((4.6, 55.35, 0))
q.stand(T(0), T(4.0), (13, 18), 200)
q.go([(13, 18), (8, 36), (FP.x, FP.y)], T(4.0), T(6.0))
q.stand(T(6.0), T(9.1), FP, 180, crouch=lambda f: 0.32 * sstep((f - T(6.1)) / 25) * (1 - sstep((f - T(6.9)) / 25)),
        flex=lambda f: 4 + 58 * sstep((f - T(6.1)) / 25) * (1 - sstep((f - T(6.9)) / 25)),
        head=lambda f: (25 * sstep((f - T(6.0)) / 20) * (1 - sstep((f - T(6.9)) / 20)) - 10 * sstep((f - T(7.6)) / 30), 0), step=3)
P1 = Vector((FP.x + 0.1, FP.y - 0.7, 0))
H_ = q.H; p0 = Vector((FP.x, FP.y, 0))
for s_, (fa, fm_, fb) in (("L", (T(9.1), T(9.22), T(9.34))), ("R", (T(9.3), T(9.42), T(9.55)))):
    A_ = H_.foot_xy(s_, p0, 180); B_ = H_.foot_xy(s_, P1, 8)
    H_.key_foot(s_, fa, A_, 180); H_.key_foot(s_, fm_, A_.lerp(B_, 0.5), 94, lift=0.12); H_.key_foot(s_, fb, B_, 8)
for f_, u_ in ((T(9.1), 0.0), (T(9.33), 0.55), (T(9.55), 1.0)):
    pp = p0.lerp(P1, u_); yw = 180 + (8 - 180) * u_
    H_.key_root(f_, Vector((pp.x, pp.y, ground_z(pp.x, pp.y) + H_.root_head.z - 0.04)), yaw=yw, flex=3)
    q.st[f_] = (pp.copy(), yw, "stand", 0.0)
q.stand(T(9.6), T(12.4), (FP.x + 0.1, FP.y - 0.7), 8, head=(-12, 0), flex=8)
q.go([(FP.x + 0.1, FP.y - 0.7), (4.8, 51.3)], T(12.4), T(12.95), run=True)
fish_pick = bpy.data.objects["Fish_00"]
fish_pick.scale = (1.15,) * 3
fish_pick.location = (FISHPICK.x, FISHPICK.y, ground_z(FISHPICK.x, FISHPICK.y) + 0.07); fish_pick.rotation_euler = (0, math.radians(90), math.radians(80))
q.reach_target = Vector((FISHPICK.x - 0.1, FISHPICK.y - 0.08, ground_z(FISHPICK.x, FISHPICK.y) + 0.05))
q.key_arms(T(0), T(12.8), lambda f: ({"R": "reach"} if T(6.45) <= f <= T(6.95) else {"R": "hold", "L": "hang"} if T(6.95) < f <= T(9.0)
                                       else {"L": "wave"} if T(9.5) <= f <= T(11.5) else ("run" if f > T(12.4) else "swing")), step=2)
# jaw open for the shout
jaw = q.H.r
for f, a in ((T(9.4), 0), (T(9.55), 18), (T(9.9), 14), (T(10.1), 20), (T(10.35), 0)):
    jaw.key_rot("jaw", f, [("X", a)])

# ---------------------------------------------------------------- offscreen reset (13 s) and the flight inland past the camera (17.4 – 21.2 s)
RUN = {"Fisher": [(6, 8), (5, -10), (8, -26)], "LocalW": [(2, 6), (1, -12), (-2, -27)], "TouristM": [(-4, 9), (-5, -9), (-9, -27)],
       "TouristW": [(9, 7), (10, -10), (14, -26)], "KidA": [(0.5, 2), (0, -10), (-1, -23)], "KidB": [(4.5, 1.5), (4.5, -10), (5, -23)],
       "OldM": [(-9, 2), (-10, -11), (-13, -24)], "LocalM": [(12, 10), (13, -9), (18, -26)]}
START = {"Fisher": 17.5, "LocalW": 17.6, "TouristM": 17.4, "TouristW": 17.7, "KidA": 17.9, "KidB": 18.0, "OldM": 17.2, "LocalM": 17.6}
for n, pts in RUN.items():
    q = P[n]; kid = n.startswith("Kid")
    q.stand(T(13.0), T(START[n]), pts[0], 0 + (8 if n == "OldM" else 0), head=(-10, 180 if False else 0))
    q.go(pts, T(START[n]), T(21.1), run=True, kid=kid)
    q.key_arms(T(12.85), T(21.1), lambda f, s=START[n]: "run" if f > T(s) else "hang")
    q.hide_after(T(21.15))
# Fisher fish: rests on the sand, follows the right hand from the grasp until he drops it
q = P["Fisher"]
for f in range(T(6.9), T(9.05), 2):
    sc.frame_set(f)
    pbw = q.H.r.PB["finger3-1.R"]; Mw = q.o.matrix_world @ pbw.matrix
    palm = Mw.translation; nrm = (q.o.matrix_world.to_3x3() @ q.H.r.PB["wrist.R"].matrix.to_3x3()) @ Vector((0, 0, 1))
    # held by the tail: fish hangs below the fist, tail fin inside the curled fingers
    yawp = math.radians(q.st[min(q.st, key=lambda k: abs(k - f))][1])
    fish_pick.rotation_euler = (math.radians(90), 0, yawp); fish_pick.keyframe_insert("rotation_euler", frame=f)
    fish_pick.location = palm + Vector((0, 0, -0.27)); fish_pick.keyframe_insert("location", frame=f)
for f, z in ((T(6.88), 0.06), (T(9.25), 0.05)):
    fish_pick.location = (FISHPICK.x if f < T(7) else fish_pick.location.x, FISHPICK.y if f < T(7) else fish_pick.location.y, ground_z(FISHPICK.x, FISHPICK.y) + z)
    fish_pick.rotation_euler = (0, math.radians(90), math.radians(80)); fish_pick.keyframe_insert("location", frame=f); fish_pick.keyframe_insert("rotation_euler", frame=f)
print("PEOPLE_DONE")
