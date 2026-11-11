# Shared helpers for PrisonKeyCake animation (exec'd by 03_animate.py after pipeline/anim_lib.py).
import math, bpy
from mathutils import Vector, Matrix, Quaternion
V = lambda *a: Vector(a)

def lerp(a, b, t): return a + (b - a) * t
def ss(f, f0, f1): return smooth((f - f0) / max(1e-6, f1 - f0))

def key_hide(o, pairs):
    """pairs: [(frame, hidden)] keyed constant, applied to object + mesh children"""
    for ob in [o] + [c for c in o.children_recursive]:
        for f, h in pairs:
            ob.hide_render = h; ob.hide_viewport = h
            ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
        set_constant(ob)

def set_constant(ob, path_prefix=None):
    ad = ob.animation_data
    if not ad or not ad.action: return
    for fc in fcurves(ad.action):
        if path_prefix is None and fc.data_path in ("hide_render", "hide_viewport") or (path_prefix and fc.data_path.startswith(path_prefix)):
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

def fcurves(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []):
                out.extend(cb.fcurves)
    return out

def mat_from(loc, x, z):
    x = x.normalized(); y = z.cross(x).normalized(); z = x.cross(y).normalized()
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = loc; return M

def mlerp(A, B, t):
    la, qa, _ = A.decompose(); lb, qb, _ = B.decompose()
    M = qa.slerp(qb, t).to_matrix().to_4x4(); M.translation = la.lerp(lb, t); return M

def key_mat(o, f, M):
    o.matrix_world = M
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

def bake_obj(o, f0, f1, fn, step=2):
    """fn(f) -> world Matrix; keys every `step` frames (euler-compatible)"""
    prev = None
    for f in list(range(f0, f1 + 1, step)) + ([f1] if (f1 - f0) % step else []):
        M = fn(f)
        loc, q, sc_ = M.decompose()
        e = q.to_euler('XYZ', prev) if prev is not None else q.to_euler('XYZ')
        o.location = loc; o.rotation_euler = e; prev = e
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

def track(keys):
    """keys [(f, value)], value float or Vector -> pchip function"""
    if isinstance(keys[0][1], (int, float)):
        return pchip([(f, float(v)) for f, v in keys])
    fs = [pchip([(f, v[i]) for f, v in keys]) for i in range(len(keys[0][1]))]
    return lambda x: Vector([g(x) for g in fs])

# ------------------------------------------------------------------ fingers
def curl(rig, s, f, amt, thumb=None, spread=0.0):
    amt = max(amt, 22.0)                                  # relaxed default: never flat-splayed
    thumb = max(14.0, amt * 0.6 if thumb is None else thumb)
    for k in range(1, 6):
        for j in range(1, 4):
            n = "finger%d-%d.%s" % (k, j, s)
            if n not in rig.PB: continue
            a = (thumb if k == 1 else amt) * (0.8 if j == 1 else 1.0)
            q = Quaternion((1, 0, 0), R_(a))
            if j == 1 and k > 1 and spread:
                q = Quaternion((0, 0, 1), R_(spread * (k - 3) * (1 if s == "L" else -1))) @ q
            rig.key_q(n, f, q)

# ------------------------------------------------------------------ actor with pose keys, foot plan, hand channels
GRIP_D, GRIP_N = 0.075, 0.03
CH_S = ("flex", "side", "sp_flex", "sp_twist", "sp_side", "h_pitch", "h_yaw", "cL", "cR", "yaw")

class Actor:
    def __init__(self, name):
        self.o = bpy.data.objects[name]; self.r = make_human_ctrl(self.o); self.h = Human(self.r)
        self.keys = []; self.walks = []; self.feet = {"L": [], "R": []}; self.hand_fn = {"L": [], "R": []}
        self.breath = 1.0; self.name = name
        self.dz = (self.h.root_head.z - 0.035) - 0.99      # root z 0.99 in the keys means 'standing' for every actor
        sh = [c for c in self.o.children if "shoes" in c.name]
        if sh:
            for s_ in "LR":
                a = self.h.ankle[s_]
                lo = min((v.co.z for v in sh[0].data.vertices if (v.co.xy - a.xy).length < 0.15), default=0.0)
                self.sole = max(getattr(self, "sole", 0.0), max(0.0, -lo) + 0.003)
            _kf = self.h.key_foot
            self.h.key_foot = lambda s_, f_, xy_, yaw_, lift_=0.0, pitch_=0.0: _kf(s_, f_, xy_, yaw_, lift_ + self.sole, pitch_)
    def k(self, f, **kw):
        self.keys.append((f, kw)); return self
    def walk(self, f0, f1, pts, stride=0.8, speed_curve=None, lean=6.0, yaw_override=None):
        """path through pts (xy or xyz), constant speed between f0..f1"""
        pts = [Vector((p[0], p[1], 0.0)) for p in pts]
        seg = [(b - a).length for a, b in zip(pts, pts[1:])]; L = sum(seg)
        cr = catmull([(sum(seg[:i]) / L, p) for i, p in enumerate(pts)])
        def path(f):
            u = (f - f0) / (f1 - f0)
            u = max(0.0, min(1.0, u if speed_curve is None else speed_curve(u)))
            return cr(u)
        def yaw_fn(f):
            if yaw_override: return yaw_override(f)
            a, b = path(max(f0, f - 6)), path(min(f1, f + 6)); d = (b - a)
            if d.length < 1e-4: d = pts[-1] - pts[-2]
            return math.degrees(math.atan2(d.x, -d.y))
        # unwrap yaw relative to previous key
        self.walks.append((f0, f1, path, yaw_fn, dict(stride=stride, lean=lean)))
        return path, yaw_fn
    def plant(self, s, f_lift, f_land, xy, yaw, lift=0.07):
        self.feet[s].append((f_lift, f_land, Vector(xy[:2]), yaw, lift))
    def stand(self, f, pos, yaw):
        """plant both feet under a standing pose at pos (instant if first, else stepping over the previous 24 frames)"""
        for i, s in enumerate("LR"):
            xy = self.h.foot_xy(s, Vector((pos[0], pos[1], 0)), yaw)
            if not self.feet[s]: self.feet[s].append((f - 1, f, xy, yaw, 0.0))
            else:
                fl = f - 24 + i * 9
                self.feet[s].append((fl, fl + 15, xy, yaw, 0.07))
    def in_walk(self, f):
        for w in self.walks:
            if w[0] <= f <= w[1]: return w
        return None
    def root_at(self, f):
        w = self.in_walk(f)
        if w:
            p = w[2](f); return Vector((p.x, p.y, self.h.root_head.z - 0.03)), w[3](f)
        return self.T["root"](f), self.T["yaw"](f)
    def compile(self):
        self.keys.sort(key=lambda x: x[0])
        for s_ in "LR": self.feet[s_].sort(key=lambda x: x[1])
        full = []; cur = dict(root=V(0, 0, 1.0), yaw=0.0, flex=0.0, side=0.0, sp_flex=0.0, sp_twist=0.0, sp_side=0.0, h_pitch=0.0, h_yaw=0.0, cL=10.0, cR=10.0,
                              hL=None, hR=None)
        merged = {}
        for f, kw in self.keys: merged.setdefault(f, {}).update(kw)
        for f in sorted(merged):
            cur = dict(cur); cur.update(merged[f]); full.append((f, cur))
        self.full = full
        self.T = {}
        for ch in ("root",) + CH_S:
            ks = [(f, (d[ch] + Vector((0, 0, self.dz))) if ch == "root" else d[ch]) for f, d in full]
            self.T[ch] = track(ks)
        # hands: (W, d, n) in world or ('B', W, d, n) body-relative; convert at key frames
        for s in "LR":
            ks = []
            for f, d in full:
                hv = d["h" + s]
                if hv is None: continue
                if hv[0] == 'B':
                    p, yw = self.root_at(f); Rz = Matrix.Rotation(R_(yw), 3, 'Z')
                    W = p + Rz @ hv[1]; dd = Rz @ hv[2]; nn = Rz @ hv[3]
                else:
                    W, dd, nn = hv
                ks.append((f, (W, dd.normalized(), nn.normalized())))
            # dedupe frames
            dd_ = {}
            for f, v in ks: dd_[f] = v
            ks = sorted(dd_.items())
            if ks:
                tW = track([(f, v[0]) for f, v in ks]); td = track([(f, v[1]) for f, v in ks]); tn = track([(f, v[2]) for f, v in ks])
                self.T["H" + s] = (tW, td, tn)
    def foot_at(self, s, f):
        pl = self.feet[s]
        cur = pl[0]
        for i, st in enumerate(pl):
            if f >= st[1]: cur = st; continue
            if st[0] < f < st[1]:
                prev = pl[i - 1] if i else st
                u = (f - st[0]) / (st[1] - st[0])
                xy = prev[2].lerp(st[2], smooth(u)); yw = prev[3] + (st[3] - prev[3]) * smooth(u)
                return xy, yw, st[4] * math.sin(math.pi * u), 20 * math.sin(math.pi * u) - 5 * u
            break
        return cur[2], cur[3], 0.0, 0.0
    def bake(self, f0=1, f1=1890, step=2):
        self.compile()
        for w in self.walks:
            self.h.walk(w[2], w[3], w[0], w[1], stride=w[4]["stride"], lean=w[4]["lean"], step=step)
        ph = hash(self.name) % 100
        for f in list(range(f0, f1 + 1, step)):
            wk = self.in_walk(f)
            br = self.breath * math.sin(2 * math.pi * (f + ph) / 230.0)
            if not wk:
                self.h.key_root(f, self.T["root"](f) + V(0, 0, 0.004 * br), yaw=self.T["yaw"](f), flex=self.T["flex"](f), side=self.T["side"](f))
                self.h.key_spine(f, flex=self.T["sp_flex"](f) + 1.5 * br, twist=self.T["sp_twist"](f), side=self.T["sp_side"](f),
                                 head=(self.T["h_pitch"](f) - 1.0 * br + 1.2 * math.sin(f / 37.0 + ph), self.T["h_yaw"](f) + 1.5 * math.sin(f / 53.0 + ph)))
                for s in "LR":
                    xy, yw, lf, pt = self.foot_at(s, f)
                    self.h.key_foot(s, f, xy, yw, lf, pt)
            else:
                # head on top of the walk's spine keys
                for n_, w_ in self.h.HEAD_W.items():
                    self.r.key_rot(n_, f, [("X", (self.T["h_pitch"](f)) * w_), ("Z", self.T["h_yaw"](f) * w_)])
            for s in "LR":
                fn = next((g for (a, b, g) in self.hand_fn[s] if a <= f <= b), None)
                if fn: W, dd, nn = fn(f)
                elif ("H" + s) in self.T:
                    tW, td, tn = self.T["H" + s]; W, dd, nn = tW(f), td(f), tn(f)
                else: continue
                p, yw = self.root_at(f)
                pole = p + Matrix.Rotation(R_(yw), 3, 'Z') @ V(0.45 if s == "L" else -0.45, 0.5, -0.25)
                self.h.key_hand(s, f, W, dd, nn, pole=pole)
            if f % 4 == 1 or step > 2:
                curl(self.r, "L", f, self.T["cL"](f)); curl(self.r, "R", f, self.T["cR"](f))

def grip_hand(G, d, n):
    """wrist target so that the palm centre is at G, fingers along d, palm facing n (n points from palm to object)"""
    d = d.normalized(); n = (n - d * n.dot(d)).normalized()
    return (G - d * GRIP_D - n * GRIP_N, d, n)

def B(W, d, n):
    return ('B', Vector(W), Vector(d), Vector(n))

HANG = {"L": B((0.24, 0.0, -0.04), (0.05, -0.1, -1), (-1, 0, 0)), "R": B((-0.24, 0.0, -0.04), (-0.05, -0.1, -1), (1, 0, 0))}

def arm_swing(actor, f0, f1, path, amp=0.11):
    """body-relative hand keys every 6 frames, opposite to the legs"""
    dist = 0.0; prev = path(f0); stride = 0.8
    for f in range(f0, f1 + 1, 6):
        p = path(f); dist += (p - prev).to_2d().length; prev = p
        c = math.sin(2 * math.pi * dist / (2 * stride) * 2)
        for s, sg in (("L", 1), ("R", -1)):
            x = 0.24 if s == "L" else -0.24
            actor.k(f, **{"h" + s: B((x, 0.0 - amp * sg * c, -0.05 + 0.03 * abs(c)), (0, -0.25 * sg * c, -1), (-1 if s == "L" else 1, 0, 0))})
