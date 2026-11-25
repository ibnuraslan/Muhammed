"""DonationBin v010 animation helpers (exec'd by 02_animate.py after anim_lib.py + hand_poses.py).
A KEYPOSE BAKER: every character is a list of keyposes (root position + orientation, spine, head, hands, feet, face);
the baker interpolates them (Catmull-Rom positions, eased slerp rotations, blended hand/foot targets resolved at the
frame being baked, so a hand that is 'local' to the body follows it and a hand 'on' a surface stays on it) and keys the
MPFB IK rig every 2 frames."""
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion
O = bpy.data.objects
def upd(): bpy.context.view_layer.update()
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail
def fs(f): sc.frame_set(int(f))

def Rb(up, front):
    """root orientation from world 'up' (head direction) and 'front' (where the chest faces)"""
    u = Vector(up).normalized(); fr = Vector(front); fr = (fr - u * fr.dot(u)).normalized()
    left = (-fr).cross(u)
    return Matrix((left, -fr, u)).transposed().to_quaternion()

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

class Actor:
    def __init__(self, rig):
        self.o = rig; self.c = make_human_ctrl(rig); self.H = Human(self.c)
        add_hand_limits(rig)
        for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
        for s in "LR":
            lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
        B = rig.data.bones
        self.root_head = B["root"].head_local.copy()
        self.K = []           # keyposes: (frame, dict)
        self.walks = []       # (f0, f1, path(f)->Vector, yaw(f)->deg)
        self.name = rig.name
    def key(self, f, **kw):
        self.K.append((f, kw)); self.K.sort(key=lambda k: k[0])
    # ---------------------------------------------------------------- interpolation of one field
    def _seg(self, field, f):
        ks = [(fr, d[field]) for fr, d in self.K if field in d]
        if not ks: return None, None, 0.0
        if f <= ks[0][0]: return ks[0][1], ks[0][1], 0.0
        if f >= ks[-1][0]: return ks[-1][1], ks[-1][1], 0.0
        for i in range(len(ks) - 1):
            if ks[i][0] <= f <= ks[i + 1][0]:
                return ks[i][1], ks[i + 1][1], (f - ks[i][0]) / max(1e-6, ks[i + 1][0] - ks[i][0])
    def pos(self, f):
        ks = [(fr, Vector(d["pos"])) for fr, d in self.K if "pos" in d]
        # keys one frame apart are a CUT (teleport while unseen): interpolate each side separately, no overshoot across it
        segs = [[ks[0]]]
        for k in ks[1:]:
            if k[0] - segs[-1][-1][0] <= 1: segs.append([k])
            else: segs[-1].append(k)
        for sg in segs:
            if f <= sg[-1][0] or sg is segs[-1]:
                return catmull(sg)(f) if len(sg) > 1 else sg[0][1]
    def rot(self, f):
        a, b, t = self._seg("rot", f)
        return a.slerp(b, ease(t)) if a is not None else Quaternion()
    def scal(self, field, f, default=0.0):
        ks = [(fr, d[field]) for fr, d in self.K if field in d]
        if not ks: return default
        if isinstance(ks[0][1], (int, float)): return catmull(ks)(f) if len(ks) > 1 else ks[0][1]
        return tuple(catmull([(fr, v[i]) for fr, v in ks])(f) if len(ks) > 1 else ks[0][1][i] for i in range(len(ks[0][1])))
    # ---------------------------------------------------------------- body frame
    def body_M(self, f):
        return Matrix.Translation(self.pos(f)) @ self.rot(f).to_matrix().to_4x4()
    def resolve(self, spec, f):
        """a hand/foot spec -> (point, normal, fdir) in world. spec: ('L', p, n, d) body-local | ('W', p, n, d) world | callable(f)"""
        if callable(spec): spec = spec(f)
        kind, p, n, d = spec[:4]
        if kind == 'W': return Vector(p), Vector(n), Vector(d)
        M = self.body_M(f); R = M.to_3x3()
        return M @ Vector(p), R @ Vector(n), R @ Vector(d)
    def blend_spec(self, field, f):
        a, b, t = self._seg(field, f)
        if a is None: return None
        pa, na, da = self.resolve(a, f)
        if a is b or t == 0.0: return pa, na, da, a
        pb, nb, db = self.resolve(b, f)
        w = ease(t)
        return pa.lerp(pb, w), na.lerp(nb, w).normalized(), da.lerp(db, w).normalized(), (a if w < 0.5 else b)
    # ---------------------------------------------------------------- baking
    def bake(self, f0, f1, step=2, skip_root=None):
        rig = self.o; c = self.c
        frames = list(range(f0, f1 + 1, step))
        if frames[-1] != f1: frames.append(f1)
        for f in frames:
            fs(f)
            walking = any(w[0] <= f <= w[1] for w in self.walks)
            if not walking:
                M = self.body_M(f)
                Mr = M @ Matrix.Translation(-self.root_head) @ c.rest("root")
                c.key_world("root", f, Mr)
                fl, tw, sd = self.scal("spine", f, (0.0, 0.0, 0.0))
                for n, w in Human.SPINE_W.items():
                    c.key_rot(n, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
            pi, yw, rl = self.scal("head", f, (0.0, 0.0, 0.0))
            for n, w in Human.HEAD_W.items():
                c.key_rot(n, f, [("X", pi * w), ("Y", rl * w), ("Z", yw * w)])
            fs(f)
            for s in "LR":
                sx = 1 if s == "L" else -1
                if not walking:
                    fb = self.blend_spec("foot_" + s, f)
                    if fb is not None:
                        P, n_, d_, _ = fb          # P = ankle world, n_ = foot up, d_ = toe direction
                        a = c.BN["foot." + s].head_local
                        up = n_.normalized(); fw = (d_ - up * d_.dot(up)).normalized()
                        Rf = Matrix(((-fw).cross(up), -fw, up)).transposed()   # foot frame like the body frame (front = toes)
                        Mf = Matrix.Translation(P) @ Rf.to_4x4() @ Matrix.Translation(-a) @ c.rest("IK_foot." + s)
                        c.key_world("IK_foot." + s, f, Mf)
                        kp = self.resolve(('L', (sx * 0.16, -0.75, -0.25), (0, 0, 1), (0, -1, 0)), f)[0] if True else None
                        kspec = self.blend_spec("knee_" + s, f)
                        if kspec is not None: kp = kspec[0]
                        n = "Pole_knee." + s; pb = c.PB[n]
                        pb.location = c.rest(n).to_3x3().inverted() @ (kp - c.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
                hb = self.blend_spec("hand_" + s, f)
                if hb is not None:
                    P, n_, d_, spec = hb
                    place_hand(rig, s, f, P, n_, d_, skin=0.012)
                    es = self.blend_spec("elbow_" + s, f)
                    ep = es[0] if es is not None else self.resolve(('L', (sx * 0.45, 0.35, 0.15), (0, 0, 1), (0, 0, 1)), f)[0]
                    n = "Pole_elbow." + s; pb = c.PB[n]
                    pb.location = c.rest(n).to_3x3().inverted() @ (ep - c.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
        # faces at their keys (smile, jaw, brow, squint)
        for fr, d in self.K:
            if "face" in d and f0 <= fr <= f1: key_face(rig, fr, *d["face"])
        # finger poses at the hand keys
        for fr, d in self.K:
            for s in "LR":
                if "grip_" + s in d and f0 <= fr <= f1: apply_pose(rig, s, d["grip_" + s], fr)
        log("baked", self.name, f0, f1, len(frames), "frames")

# ------------------------------------------------------------------ simple procedural walk (feet planted, arm swing via hand keys)
def walk_feet(actor, path, yawf, f0, f1, stride=0.62, lift=0.07):
    """returns foot specs as callables for the baker: feet planted on the ground, swinging between plants"""
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    def mk(s, ph):
        sx = 1 if s == "L" else -1
        ank = actor.o.data.bones["foot." + s].head_local
        def foot_at(f):
            i = max(0, min(len(frames) - 1, int(f) - f0)); cyc = dist[i] / stride + ph
            k = math.floor(cyc); u = cyc - k
            def plant(kk):
                dd = (kk - ph + 0.25) * stride; dd = max(0.0, min(dist[-1], dd))
                j = min(range(len(dist)), key=lambda j: abs(dist[j] - dd)); fr = frames[j]
                yw = math.radians(yawf(fr)); fwd = Vector((-math.sin(yw), math.cos(yw), 0)) * -1
                left = Vector((math.cos(yw), math.sin(yw), 0))
                return path(fr) + left * sx * abs(ank.x) * 0.9, yw
            if u < 0.5:
                p, yw = plant(k)
                lf = 0.0
            else:
                pa, ya = plant(k); pb, yb = plant(k + 1); w = ease((u - 0.5) / 0.5)
                p = pa.lerp(pb, w); yw = ya + (yb - ya) * w; lf = lift * math.sin(math.pi * w)
            fwd = Vector((math.sin(yw), -math.cos(yw), 0))      # rest front is -Y rotated by yaw
            return ('W', Vector((p.x, p.y, ank.z + lf)), (0, 0, 1), fwd)
        return foot_at
    return mk("L", 0.0), mk("R", 0.5)


_NUDGE = {}
def nudge_q(rig, bone, want, deg):
    key = (rig.name, bone, tuple(round(x, 2) for x in want))
    if key not in _NUDGE:
        pb = rig.pose.bones[bone]; q0 = pb.rotation_quaternion.copy(); upd()
        base = Wt(rig, bone); best = None
        for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
            for sg in (1, -1):
                pb.rotation_quaternion = Quaternion(ax, math.radians(10 * sg)); upd()
                d = (Wt(rig, bone) - base).dot(Vector(want).normalized())
                if best is None or d > best[0]: best = (d, ax, sg)
        pb.rotation_quaternion = q0; upd()
        _NUDGE[key] = best
    d, ax, sg = _NUDGE[key]
    return Quaternion(ax, math.radians(deg * sg))

def face_dirs(rig):
    """world directions of the face at rest-orientation of the root (rig faces -Y at rest)"""
    return Vector((0, -1, 0)), Vector((0, 0, 1))

def key_face(rig, f, smile=0.0, jaw=0.0, brow=0.0, squint=0.0, pucker=0.0):
    """expressions as bone nudges (rest-relative). smile 0..1, jaw 0..1 open, brow -1(frown)..1(raised), squint 0..1"""
    up = Vector((0, 0, 1))
    for s, sx in (("L", 1), ("R", -1)):
        out = Vector((sx, 0, 0))
        for b, amt in (("risorius03." + s, 14), ("levator05." + s, 10), ("oris04." + s, 8)):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up + out * 0.7, amt) if smile >= 0 else nudge_q(rig, b, -up + out * 0.2, amt)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(smile)); pb.keyframe_insert("rotation_quaternion", frame=f)
        for b in ("oculi01." + s, "oculi02." + s):
            if b in rig.pose.bones:
                q = nudge_q(rig, b, up, 10) if brow >= 0 else nudge_q(rig, b, -up - out * 0.5, 10)
                pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, abs(brow)); pb.keyframe_insert("rotation_quaternion", frame=f)
        b = "orbicularis04." + s     # lower lid up for squint
        if b in rig.pose.bones:
            q = nudge_q(rig, b, up, 12); pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, squint); pb.keyframe_insert("rotation_quaternion", frame=f)
    q = nudge_q(rig, "jaw", -up, 14); pb = rig.pose.bones["jaw"]; pb.rotation_quaternion = Quaternion().slerp(q, jaw); pb.keyframe_insert("rotation_quaternion", frame=f)

def blinks(rig, frames, close_deg=26):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]
        q = nudge_q(rig, b, Vector((0, 0, -1)), close_deg)
        pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=1)
        for bf in frames:
            for df, u in ((0, 0), (3, 1), (6, 1), (11, 0)):
                pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=bf + df)

def eyes_closed(rig, f0, f1, ramp=8):
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]; q = nudge_q(rig, b, Vector((0, 0, -1)), 26)
        for f, u in ((f0, 0), (f0 + ramp, 1), (f1 - ramp, 1), (f1, 0)):
            pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=f)

def saccades(ctrl, f0, f1, every=40, amp=(3, 5), seed=1):
    rnd = random.Random(seed)
    for f in range(f0, f1, every):
        for s in "LR":
            ctrl.key_rot("eye." + s, f, [("X", rnd.uniform(-amp[0], amp[0])), ("Z", rnd.uniform(-amp[1], amp[1]))])

def breathe(ctrl, f0, f1, base_flex, per=200, amp=1.2, twist=0.0):
    for f in range(f0, f1 + 1, 20):
        key_spine(ctrl, f, flex=base_flex(f) + amp * math.sin(2 * math.pi * f / per), twist=twist)

