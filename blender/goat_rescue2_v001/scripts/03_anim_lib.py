# Shared animation helpers for the goat rescue film (exec'd by 03_animate.py).
import math
import bpy
from mathutils import Vector, Matrix, Quaternion

R_ = math.radians
sc = bpy.context.scene

def ev(f=None):
    if f is not None:
        sc.frame_set(int(f))
    else:
        bpy.context.view_layer.update()

def rotw(seq):
    M = Matrix.Identity(3)
    for ax, d in seq:
        M = Matrix.Rotation(R_(d), 3, ax) @ M
    return M

class Rig:
    def __init__(self, obj):
        self.o = obj; self.A = obj.data; self.PB = obj.pose.bones; self.BN = obj.data.bones
    def rest(self, n):
        return self.BN[n].matrix_local.copy()
    def local_q(self, n, Rw):
        R = self.rest(n).to_3x3().normalized()
        return (R.inverted() @ Rw @ R).to_quaternion()
    def key_q(self, n, f, q):
        pb = self.PB[n]
        if pb.rotation_quaternion.dot(q) < 0:
            q = -q
        pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    def key_rot(self, n, f, seq):
        self.key_q(n, f, self.local_q(n, rotw(seq)))
    def key_world(self, n, f, M, rot=True):
        """armature-space target for a bone whose parent chain is at rest"""
        pb = self.PB[n]
        basis = self.rest(n).inverted() @ M
        loc, q, _ = basis.decompose()
        if pb.rotation_quaternion.dot(q) < 0:
            q = -q
        pb.location = loc
        pb.keyframe_insert("location", frame=f, group=n)
        if rot:
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
    def delta(self, n):
        return self.PB[n].matrix @ self.rest(n).inverted()

def catmull(keys):
    """Catmull-Rom through (frame, value or Vector); continuous velocity, no stops at keys"""
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(len(xs) - 1) if xs[j] <= x)
        x0, x1 = xs[i], xs[i + 1]
        p0 = ys[i - 1] if i > 0 else ys[i] - (ys[i + 1] - ys[i])
        p3 = ys[i + 2] if i + 2 < len(ys) else ys[i + 1] + (ys[i + 1] - ys[i])
        t0 = xs[i - 1] if i > 0 else x0 - (x1 - x0)
        t3 = xs[i + 2] if i + 2 < len(xs) else x1 + (x1 - x0)
        p1, p2 = ys[i], ys[i + 1]
        m1 = (p2 - p0) * ((x1 - x0) / (x1 - t0))
        m2 = (p3 - p1) * ((x1 - x0) / (t3 - x0))
        t = (x - x0) / (x1 - x0)
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t
        h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
        return p1 * h00 + m1 * h10 + p2 * h01 + m2 * h11
    return f

def pchip(keys):
    xs = [k[0] for k in keys]; ys = [k[1] for k in keys]; n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        return ((1 + 2 * t) * (1 - t) ** 2 * ys[i] + t * (1 - t) ** 2 * h[i] * m[i]
                + t * t * (3 - 2 * t) * ys[i + 1] + t * t * (t - 1) * h[i] * m[i + 1])
    return f

def smooth(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ terrain
_HEAP = None
def ground_z(x, y):
    """height of the walkable surface (field at 0, manure heap via ray cast)"""
    global _HEAP
    if _HEAP is None:
        _HEAP = bpy.data.objects.get("ManureHeap")
    if _HEAP is None:
        return 0.0
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nrm, idx = _HEAP.evaluated_get(dg).ray_cast(Vector((x, y, 6.0)), Vector((0, 0, -1)))
    return max(0.0, loc.z) if hit else 0.0

def hoof_matrix(rig, n, xy, h, lift=0.0, toe_up=0.0):
    """IK_hoof target so that both the heel (fetlock xy) and the toe tip rest on the surface"""
    H0 = rig.BN[n].head_local; T0 = rig.BN[n].tail_local
    Rh = Matrix.Rotation(h, 3, 'Z')
    v = Rh @ (T0 - H0)
    tip_xy = Vector((xy.x + v.x, xy.y + v.y))
    g_tip = ground_z(tip_xy.x, tip_xy.y); g_heel = ground_z(xy.x, xy.y)
    a = math.atan2(g_tip - g_heel, max(1e-4, v.to_2d().length)) + toe_up
    Rp = Matrix.Rotation(-a, 3, Rh @ Vector((1, 0, 0)))
    v2 = Rp @ v
    head = Vector((xy.x, xy.y, max(g_tip + T0.z - v2.z, g_heel + 0.6 * (H0.z - T0.z)) + lift))
    return Matrix.Translation(head) @ (Rp @ Rh).to_4x4() @ Matrix.Translation(-H0) @ rig.rest(n)

# ------------------------------------------------------------------ quadruped locomotion
LEGS = ("FL", "FR", "HL", "HR")

def quad_move(rig, path, f0, f1, stride, gait="walk", lift=None, body_bob=0.01, step=2, heading_fn=None):
    """path(f) -> Vector (torso ground position xy); hooves planted with no slide.
    gait walk: lateral sequence HL,FL,HR,FR (phases 0,.25,.5,.75), duty .65
    gait trot: diagonal pairs FL+HR / FR+HL, duty .45"""
    BN = rig.BN
    torso_rest = rig.rest("torso")
    off = {k: BN["IK_hoof." + k].head_local - torso_rest.translation for k in LEGS}
    phase = {"walk": {"HL": 0.0, "FL": 0.25, "HR": 0.5, "FR": 0.75},
             "trot": {"FL": 0.0, "HR": 0.0, "FR": 0.5, "HL": 0.5}}[gait]
    duty = 0.65 if gait == "walk" else 0.45
    lift = lift if lift is not None else 0.06 * torso_rest.translation.z
    # distance travelled -> cycle position
    frames = list(range(f0, f1 + 1))
    dist = [0.0]
    for a, b in zip(frames, frames[1:]):
        dist.append(dist[-1] + (path(b) - path(a)).to_2d().length)
    def heading(f):
        if heading_fn:
            return heading_fn(f)
        a, b = path(max(f0, f - 2)), path(min(f1, f + 2))
        d = (b - a).to_2d()
        if d.length < 1e-5:
            d = (path(f1) - path(f0)).to_2d()
        return math.atan2(d.x, -d.y)          # facing -Y at heading 0
    def foot_world(k, f):
        p = path(f); h = heading(f)
        o = Matrix.Rotation(h, 3, 'Z') @ off[k]
        x, y = p.x + o.x, p.y + o.y
        return Vector((x, y, ground_z(x, y) + BN["IK_hoof." + k].head_local.z))
    for k in LEGS:
        n = "IK_hoof." + k
        cyc = [d / stride + phase[k] for d in dist]
        per = {}
        for i, c in enumerate(cyc):
            per.setdefault(int(math.floor(c)), []).append(i)
        plant = {}
        for pid, idxs in per.items():
            st = [i for i in idxs if (cyc[i] % 1.0) < duty]
            if not st:
                continue
            i_mid = min(st, key=lambda i: abs((cyc[i] % 1.0) - duty / 2))
            plant[pid] = (foot_world(k, frames[i_mid]), heading(frames[i_mid]))
        last = (foot_world(k, frames[-1]), heading(frames[-1]))
        first = (foot_world(k, frames[0]), heading(frames[0]))
        for i, f in enumerate(frames):
            if (i % step) and i != len(frames) - 1:
                continue
            pid = int(math.floor(cyc[i])); fr = cyc[i] % 1.0
            if fr < duty:
                pos, h = plant.get(pid, first if pid not in plant and i < len(frames) / 2 else last); z = 0.0
            else:
                a = plant.get(pid, first)
                b = plant.get(pid + 1, last)
                s_ = (fr - duty) / (1 - duty)
                pos = a[0].lerp(b[0], smooth(s_)); h = a[1] + (b[1] - a[1]) * smooth(s_)
                z = lift * math.sin(math.pi * s_)
            M = hoof_matrix(rig, n, pos.to_2d(), h, lift=z)
            rig.key_world(n, f, M)
    # body: follow path with bob
    for i, f in enumerate(frames):
        if i % step and i != len(frames) - 1:
            continue
        p = path(f); h = heading(f)
        cyc = (dist[i] / stride) % 1.0
        bob = body_bob * math.cos(4 * math.pi * cyc)
        gz = {k: ground_z(*foot_world(k, f).to_2d()) for k in LEGS}
        zf, zh = (gz["FL"] + gz["FR"]) / 2, (gz["HL"] + gz["HR"]) / 2
        span = (off["FL"] - off["HL"]).length
        pitch = math.atan2(zf - zh, span)          # nose up when the front is higher
        M = Matrix.Translation(Vector((p.x, p.y, torso_rest.translation.z + bob + (zf + zh) / 2))) @ \
            Matrix.Rotation(h, 4, 'Z') @ Matrix.Rotation(-pitch, 4, 'X') @ \
            Matrix.Translation(-torso_rest.translation) @ torso_rest
        rig.key_world("torso", f, M)
    return heading

def quad_hold(rig, f, pos, h, torso_dz=0.0, extra_rot=None):
    """key every hoof and the torso at a still pose (feet under body)"""
    BN = rig.BN; tr = rig.rest("torso")
    for k in LEGS:
        n = "IK_hoof." + k
        o = Matrix.Rotation(h, 3, 'Z') @ (BN[n].head_local - tr.translation)
        rig.key_world(n, f, hoof_matrix(rig, n, Vector((pos.x + o.x, pos.y + o.y)), h))
    fw = Matrix.Rotation(h, 3, 'Z') @ Vector((0, -1, 0))
    span = (BN["IK_hoof.FL"].head_local - BN["IK_hoof.HL"].head_local).length
    zf = ground_z(pos.x + fw.x * span / 2, pos.y + fw.y * span / 2); zh = ground_z(pos.x - fw.x * span / 2, pos.y - fw.y * span / 2)
    pitch = math.atan2(zf - zh, span)
    R = Matrix.Rotation(h, 4, 'Z') @ Matrix.Rotation(-pitch, 4, 'X') @ (extra_rot.to_4x4() if extra_rot else Matrix.Identity(4))
    rig.key_world("torso", f, Matrix.Translation(Vector((pos.x, pos.y, tr.translation.z + torso_dz + (zf + zh) / 2))) @ R @
                  Matrix.Translation(-tr.translation) @ tr)

# ------------------------------------------------------------------ human (MPFB default rig) control + walking
def make_human_ctrl(obj):
    """adds IK_foot/IK_hand controls with knee/elbow poles to an MPFB 'default' rig; returns Rig"""
    obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects: o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = obj.data.edit_bones
    for s in "LR":
        sx = 1 if s == "L" else -1
        for src, nm in (("foot." + s, "IK_foot." + s), ("wrist." + s, "IK_hand." + s)):
            b = eb.new(nm); b.head, b.tail, b.roll = eb[src].head.copy(), eb[src].tail.copy(), eb[src].roll
            b.use_deform = False; b.parent = None
        kn = eb["lowerleg01." + s].head.copy(); p = eb.new("Pole_knee." + s)
        p.head = kn + Vector((0, -0.6, 0)); p.tail = p.head + Vector((0, 0, 0.08)); p.use_deform = False
        el = eb["lowerarm01." + s].head.copy(); p = eb.new("Pole_elbow." + s)
        p.head = el + Vector((0.25 * sx, 0.55, -0.1)); p.tail = p.head + Vector((0, 0, 0.08)); p.use_deform = False
    bpy.ops.object.mode_set(mode='POSE')
    R = Rig(obj)
    for pb in obj.pose.bones: pb.rotation_mode = 'QUATERNION'
    cons = {}
    for s in "LR":
        for chain_end, tgt, pole, twist_bones, key in (("lowerleg02." + s, "IK_foot." + s, "Pole_knee." + s, ("upperleg02.", "lowerleg02."), "leg"),
                                                       ("lowerarm02." + s, "IK_hand." + s, "Pole_elbow." + s, ("upperarm02.", "lowerarm02."), "arm")):
            c = R.PB[chain_end].constraints.new('IK'); c.target, c.subtarget = obj, tgt
            c.pole_target, c.pole_subtarget = obj, pole; c.chain_count = 4; c.iterations = 300
            for tb in twist_bones:
                pb = R.PB[tb + s]; pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = True
            cons[key + s] = c
        R.PB["lowerleg01." + s].lock_ik_y = R.PB["lowerleg01." + s].lock_ik_z = True
        for bone, tgt in (("foot." + s, "IK_foot." + s), ("wrist." + s, "IK_hand." + s)):
            cr = R.PB[bone].constraints.new('COPY_ROTATION'); cr.target, cr.subtarget = obj, tgt
    for key, c in cons.items():
        mid = ("lowerleg01." if key.startswith("leg") else "lowerarm01.") + key[-1]
        ref = R.BN[mid].head_local.copy(); best = (0, 9)
        for d in range(-180, 180, 4):
            c.pole_angle = R_(d); ev(); e = (R.PB[mid].head - ref).length
            if e < best[1]: best = (d, e)
        for d10 in range((best[0] - 4) * 10, (best[0] + 4) * 10):
            c.pole_angle = R_(d10 / 10); ev(); e = (R.PB[mid].head - ref).length
            if e < best[1]: best = (d10 / 10, e)
        c.pole_angle = R_(best[0])
    bpy.ops.object.mode_set(mode='OBJECT')
    return R

class Human:
    SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
    HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
    def __init__(self, rig):
        self.r = rig; B = rig.BN
        self.root_head = B["root"].head_local.copy()
        self.ankle = {s: B["foot." + s].head_local.copy() for s in "LR"}
    def key_root(self, f, pos, yaw=0.0, flex=0.0, side=0.0):
        Rw = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(flex), 3, 'X') @ Matrix.Rotation(R_(side), 3, 'Y')
        M = Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-self.root_head) @ self.r.rest("root")
        self.r.key_world("root", f, M)
    def key_spine(self, f, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0)):
        for n, w in self.SPINE_W.items():
            self.r.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
        for n, w in self.HEAD_W.items():
            self.r.key_rot(n, f, [("X", head[0] * w), ("Z", head[1] * w)])
    def key_foot(self, s, f, xy, yaw, lift=0.0, pitch=0.0):
        a = self.ankle[s]
        z = ground_z(xy.x, xy.y) + a.z + lift
        M = Matrix.Translation(Vector((xy.x, xy.y, z))) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ \
            Matrix.Translation(-a) @ self.r.rest("IK_foot." + s)
        self.r.key_world("IK_foot." + s, f, M)
        pole = Vector((xy.x, xy.y, z + 0.45)) + Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((0, -0.7, 0))
        pb = self.r.PB["Pole_knee." + s]; n = "Pole_knee." + s
        pb.location = self.r.rest(n).to_3x3().inverted() @ (pole - self.r.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def foot_xy(self, s, pos, yaw):
        o = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((self.ankle[s].x * 0.75, self.ankle[s].y - self.root_head.y, 0))
        return Vector((pos.x + o.x, pos.y + o.y))
    def key_hand(self, s, f, W, d, n, pole=None):
        sx = 1 if s == "L" else -1
        wr = self.r.BN["wrist." + s].head_local
        dd = self.r.BN["finger3-1." + s].head_local - wr
        aa = self.r.BN["finger2-1." + s].head_local - self.r.BN["finger5-1." + s].head_local
        nn = dd.cross(aa) if s == "L" else aa.cross(dd)
        def basis(d_, n_):
            d_ = d_.normalized(); n_ = (n_ - d_ * n_.dot(d_)).normalized()
            a_ = d_.cross(n_) if s == "R" else n_.cross(d_)
            return Matrix((d_, a_, n_)).transposed()
        Rm = basis(d, n) @ basis(dd, nn).transposed()
        self.r.key_world("IK_hand." + s, f, Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.r.rest("IK_hand." + s))
        if pole is not None:
            pb = self.r.PB["Pole_elbow." + s]; nme = "Pole_elbow." + s
            pb.location = self.r.rest(nme).to_3x3().inverted() @ (pole - self.r.BN[nme].head_local)
            pb.keyframe_insert("location", frame=f, group=nme)
    def walk(self, path, yaw_fn, f0, f1, stride=0.75, duty=0.62, lift=0.08, bob=0.022, crouch=0.03, lean=6.0, step=2):
        frames = list(range(f0, f1 + 1)); dist = [0.0]
        for a_, b_ in zip(frames, frames[1:]):
            dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
        for s, ph in (("L", 0.0), ("R", 0.5)):
            cyc = [d / stride + ph for d in dist]; per = {}
            for i, c in enumerate(cyc): per.setdefault(int(math.floor(c)), []).append(i)
            plant = {}
            for pid, idx in per.items():
                st = [i for i in idx if (cyc[i] % 1.0) < duty]
                if st:
                    im = min(st, key=lambda i: abs((cyc[i] % 1.0) - duty / 2))
                    plant[pid] = (self.foot_xy(s, path(frames[im]), yaw_fn(frames[im])), yaw_fn(frames[im]))
            first = (self.foot_xy(s, path(f0), yaw_fn(f0)), yaw_fn(f0)); last = (self.foot_xy(s, path(f1), yaw_fn(f1)), yaw_fn(f1))
            for i, f in enumerate(frames):
                if (i % step) and i != len(frames) - 1: continue
                pid = int(math.floor(cyc[i])); fr = cyc[i] % 1.0
                if fr < duty:
                    xy, yw = plant.get(pid, first if i < len(frames) / 2 else last); lf = 0.0; pt = 0.0
                else:
                    a_ = plant.get(pid, first); b_ = plant.get(pid + 1, last); u = (fr - duty) / (1 - duty)
                    xy = a_[0].lerp(b_[0], smooth(u)); yw = a_[1] + (b_[1] - a_[1]) * smooth(u)
                    lf = lift * math.sin(math.pi * u); pt = 25 * math.sin(math.pi * u) - 10
                self.key_foot(s, f, xy, yw, lf, pt)
        for i, f in enumerate(frames):
            if (i % step) and i != len(frames) - 1: continue
            p = path(f); cyc = (dist[i] / stride) % 1.0
            gz_ = ground_z(p.x, p.y)
            z = gz_ + self.root_head.z - crouch - bob * (0.5 + 0.5 * math.cos(4 * math.pi * cyc))
            yw = yaw_fn(f)
            self.key_root(f, Vector((p.x, p.y, z)), yaw=yw, flex=lean * 0.5, side=3 * math.sin(2 * math.pi * cyc))
            self.key_spine(f, flex=lean, twist=-6 * math.sin(2 * math.pi * cyc))
