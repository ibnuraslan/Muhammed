"""Shared hand-pose library for the MPFB "default" rig (finger1-1..finger5-3, wrist, .L/.R, plus IK_hand.L/R from anim_lib.make_human_ctrl).

    exec(open(".../pipeline/hand_poses.py").read())        # or importlib; needs only bpy + mathutils
    add_hand_limits(rig)                                   # STYLE_ANIMATED limits as LIMIT_ROTATION constraints (once per rig)
    apply_pose(rig, "L", "wrap_grip", frame, amount=1.0, spread=None)
    grip_object(rig, "R", frame, target_obj, contact_point, approach_dir)   # places IK_hand, closes fingers onto the surface
    place_hand(rig, "R", frame, palm_point, palm_normal, finger_dir)       # IK_hand only

Poses: relaxed, wrap_grip, power_fist, pinch, tripod, flat_palm, point, cup_hold, open_alarm, shield, hold_flat_object.
Design rules (client hands rule, STYLE_ANIMATED.md):
  * finger joints only flex forward (0..90 deg), spread/twist within +-10 deg; the thumb stays in a natural cone
  * fingers are kept together (each finger's base aligned with the middle finger) unless `spread` (deg) is given
  * the thumb is solved numerically per pose (it is aimed at a target such as the index tip), so it opposes on any MPFB body
Everything is derived from the rig's own bone geometry (flex direction, palm normal), so .L and .R and every MPFB body work."""
import math
import bpy
from mathutils import Matrix, Quaternion, Vector, Euler

_R = math.radians
FING = (2, 3, 4, 5)

# ------------------------------------------------------------------ pose table
# curl: per finger (MCP, PIP, DIP) degrees of forward flex; spread: deg between neighbouring fingers (0 = together)
# thumb: (target, gap_m) -> the thumb tip is solved to sit `gap_m` from the target point (see _thumb_target)
POSES = {
    "relaxed":          dict(curl={2: (14, 22, 12), 3: (16, 26, 14), 4: (19, 30, 16), 5: (22, 34, 18)}, spread=2.0, thumb=("beside_index", 0.012)),
    "wrap_grip":        dict(curl={2: (55, 75, 45), 3: (58, 78, 48), 4: (60, 80, 50), 5: (62, 82, 50)}, spread=0.0, thumb=("over_middle2", 0.020)),
    "power_fist":       dict(curl={2: (82, 90, 60), 3: (85, 90, 62), 4: (86, 90, 64), 5: (88, 90, 66)}, spread=0.0, thumb=("over_index2", 0.012)),
    "pinch":            dict(curl={2: (40, 45, 25), 3: (30, 45, 25), 4: (40, 60, 35), 5: (48, 68, 40)}, spread=0.0, thumb=("index_tip", 0.004)),
    "tripod":           dict(curl={2: (38, 40, 20), 3: (36, 42, 22), 4: (55, 70, 40), 5: (60, 75, 45)}, spread=0.0, thumb=("index_middle_tips", 0.008)),
    "flat_palm":        dict(curl={2: (2, 2, 1), 3: (2, 2, 1), 4: (2, 2, 1), 5: (3, 2, 1)}, spread=1.0, thumb=("flat_out", 0.0)),
    "point":            dict(curl={2: (0, 2, 2), 3: (78, 90, 55), 4: (82, 90, 58), 5: (85, 90, 60)}, spread=0.0, thumb=("over_middle2", 0.010)),
    "cup_hold":         dict(curl={2: (18, 20, 10), 3: (20, 22, 12), 4: (22, 24, 12), 5: (25, 26, 14)}, spread=0.0, thumb=("beside_index", 0.020)),
    "open_alarm":       dict(curl={2: (8, 12, 6), 3: (9, 14, 7), 4: (10, 16, 8), 5: (12, 18, 9)}, spread=6.0, thumb=("open", 0.0)),
    "shield":           dict(curl={2: (2, 3, 2), 3: (2, 3, 2), 4: (3, 3, 2), 5: (3, 4, 2)}, spread=0.0, thumb=("beside_index", 0.006)),
    "hold_flat_object": dict(curl={2: (30, 12, 6), 3: (30, 12, 6), 4: (32, 14, 8), 5: (34, 16, 8)}, spread=0.0, thumb=("on_top", 0.022)),
}
LIMITS = dict(finger=((0, 90), (-10, 10), (-10, 10)), thumb=((-30, 45), (-30, 30), (-40, 40)), wrist=((-60, 60), (-30, 30), (-25, 25)))

def _b(k, j, s): return "finger%d-%d.%s" % (k, j, s)
def _chain(s): return [_b(k, j, s) for k in (1,) + FING for j in (1, 2, 3)]

# ------------------------------------------------------------------ fast FK on the hand (no depsgraph per trial)
class _Hand:
    def __init__(self, rig, s):
        self.rig, self.s, self.PB, self.BN = rig, s, rig.pose.bones, rig.data.bones
        self.base = {}                           # evaluated pose matrices of the non-finger parents (wrist, metacarpals)
        for n in _chain(s):
            p = self.BN[n].parent
            if p and not p.name.startswith("finger"): self.base[p.name] = self.PB[p.name].matrix.copy()
    def fk(self, rot):
        """rot: bone -> Quaternion (local basis). Returns bone -> (head, tail) in armature space."""
        M = {}
        def mat(n):
            if n in M: return M[n]
            b = self.BN[n]; par = b.parent
            P = mat(par.name) if par.name.startswith("finger") else self.base[par.name]
            m = P @ (par.matrix_local.inverted() @ b.matrix_local) @ rot.get(n, Quaternion()).to_matrix().to_4x4()
            M[n] = m; return m
        out = {}
        for n in _chain(self.s):
            m = mat(n); out[n] = (m.translation.copy(), m.translation + m.to_3x3() @ Vector((0, self.BN[n].length, 0)))
        return out
    def frame(self):
        """palm frame at the current wrist: d = toward middle-finger base, n = palm normal (palm side), a = across"""
        wr = self.PB["wrist." + self.s].matrix
        base = {n: (self.base[self.BN[n].parent.name] @ (self.BN[n].parent.matrix_local.inverted() @ self.BN[n].matrix_local)).translation
                for n in (_b(3, 1, self.s), _b(2, 1, self.s), _b(5, 1, self.s))}
        d = (base[_b(3, 1, self.s)] - wr.translation).normalized(); a = (base[_b(2, 1, self.s)] - base[_b(5, 1, self.s)]).normalized()
        n = d.cross(a) if self.s == "L" else a.cross(d)
        n = (n - d * n.dot(d)).normalized()
        # make sure n points to the palm side: flexing the middle finger must move its tip toward +n
        t0 = self.fk({})[_b(3, 3, self.s)][1]
        q = {_b(3, j, self.s): Quaternion((1, 0, 0), _R(40)) for j in (1, 2, 3)}
        t1 = self.fk(q)[_b(3, 3, self.s)][1]
        if (t1 - t0).dot(n) < 0: n = -n
        return wr.translation.copy(), d, n, n.cross(d).normalized() if self.s == "L" else d.cross(n).normalized()

def _flex_sign(H, n, bone):
    """+1 if a positive local-X rotation flexes this bone toward the palm normal n"""
    head, tail = H.fk({})[bone]; head2, tail2 = H.fk({bone: Quaternion((1, 0, 0), _R(20))})[bone]
    return 1.0 if (tail2 - tail).dot(n) >= 0 else -1.0

def _pose_rots(rig, s, name, spread=None):
    P = POSES[name]; H = _Hand(rig, s); wr, d, n, a = H.frame()
    sp = P["spread"] if spread is None else spread
    rot = {}
    for k in FING:
        for j, c in zip((1, 2, 3), P["curl"][k]):
            b = _b(k, j, s); rot[b] = Quaternion((1, 0, 0), _flex_sign(H, n, b) * _R(c))
    # together/spread: align each finger's first phalanx with the middle finger in the palm plane, then fan by `sp`
    ref = H.fk(rot)
    mid = (ref[_b(3, 1, s)][1] - ref[_b(3, 1, s)][0]); mid = (mid - n * mid.dot(n)).normalized()
    for k in (2, 4, 5):
        b = _b(k, 1, s); fan = _R(sp) * (3 - k)            # index fans toward the thumb side, ring/little away
        want = Quaternion(n, fan if s == "L" else -fan) @ mid
        best = (9, 0.0)
        for zd10 in range(-100, 101, 5):
            q = rot[b] @ Quaternion((0, 0, 1), _R(zd10 / 10))
            h, t = H.fk({**rot, b: q})[b]; v = t - h; v = (v - n * v.dot(n)).normalized()
            e = v.angle(want, 9)
            if e < best[0]: best = (e, zd10 / 10)
        rot[b] = rot[b] @ Quaternion((0, 0, 1), _R(best[1]))
    rot.update(_solve_thumb(H, rot, P["thumb"], wr, d, n, a))
    return rot

def _thumb_target(kind, F, wr, d, n, a, s):
    tip = lambda k: F[_b(k, 3, s)][1]; mid2 = lambda k: (F[_b(k, 2, s)][0] + F[_b(k, 2, s)][1]) / 2
    side = (F[_b(2, 1, s)][0] - F[_b(3, 1, s)][0]).normalized()          # toward the thumb side of the hand
    return {"index_tip": tip(2), "index_middle_tips": (tip(2) + tip(3)) / 2,
            "over_middle2": mid2(3) + n * 0.004, "over_index2": mid2(2) - d * 0.004,
            "beside_index": F[_b(2, 2, s)][0] + side * 0.018 + n * 0.006,
            "on_top": F[_b(2, 1, s)][0] - n * 0.026 + d * 0.012,
            "flat_out": F[_b(2, 1, s)][0] + side * 0.035 - d * 0.005,
            "open": F[_b(2, 1, s)][0] + side * 0.045 + n * 0.012 - d * 0.004}[kind]

def _solve_thumb(H, rot, spec, wr, d, n, a, target=None, obj=None, radius=0.008):
    s = H.s; kind, gap = spec
    F = H.fk(rot); target = target if target is not None else _thumb_target(kind, F, wr, d, n, a, s)
    Mw = H.rig.matrix_world
    b1, b2, b3 = _b(1, 1, s), _b(1, 2, s), _b(1, 3, s)
    sg2, sg3 = _flex_sign(H, n, b2), _flex_sign(H, n, b3)
    (xl, xh), (yl, yh), (zl, zh) = LIMITS["thumb"]
    def q_of(x1, z1, f2, f3):
        return {b1: Quaternion(Euler((_R(x1), 0, _R(z1)), 'XYZ')), b2: Quaternion((1, 0, 0), sg2 * _R(f2)), b3: Quaternion((1, 0, 0), sg3 * _R(f3))}
    def cost(x):
        Q = q_of(*x); tip = H.fk({**rot, **Q})[b3][1]
        c = abs((tip - target).length - gap)
        # keep the thumb out of the fingers: penalise its tip inside 9 mm of any finger bone (except the pinch targets)
        if kind not in ("index_tip", "index_middle_tips"):
            for k in FING:
                for j in (1, 2, 3):
                    h, t = F[_b(k, j, s)]
                    u = max(0, min(1, (tip - h).dot(t - h) / max(1e-9, (t - h).length_squared)))
                    dd = (tip - (h + (t - h) * u)).length
                    if dd < 0.009: c += (0.009 - dd) * 4
        if obj is not None:                                    # never inside the gripped object
            F2 = H.fk({**rot, **Q})
            for bn in (b2, b3):
                h, t = F2[bn]
                for u in (0.5, 1.0):
                    dd = _dist_to(obj, Mw @ h.lerp(t, u))
                    if dd < radius: c += (radius - dd) * 6
        return c + 0.00002 * (x[2] + x[3])                     # tiny preference for less flexion
    best = None
    for x1 in range(xl, xh + 1, 15):
        for z1 in range(zl, zh + 1, 10):
            for f2 in (0, 25, 50):
                for f3 in (0, 30, 60):
                    c = cost((x1, z1, f2, f3))
                    if best is None or c < best[0]: best = (c, [x1, z1, f2, f3])
    x = best[1]; step = [6, 6, 8, 8]; lo = [xl, zl, 0, 0]; hi = [xh, zh, 55, 70]
    for _ in range(4):
        improved = True
        while improved:
            improved = False
            for i in range(4):
                for sgn in (-1, 1):
                    y = list(x); y[i] = max(lo[i], min(hi[i], y[i] + sgn * step[i]))
                    c = cost(y)
                    if c < best[0] - 1e-7: best = (c, y); x = y; improved = True
        step = [v / 2 for v in step]
    return q_of(*x)

# ------------------------------------------------------------------ public API
def add_hand_limits(rig):
    """LIMIT_ROTATION (local space) on every finger, thumb and wrist bone, per STYLE_ANIMATED.md. Idempotent."""
    for s in "LR":
        for n in _chain(s) + ["wrist." + s]:
            pb = rig.pose.bones[n]
            if any(c.name == "HandLimit" for c in pb.constraints): continue
            lim = LIMITS["wrist"] if n.startswith("wrist") else LIMITS["thumb"] if n.startswith("finger1") else LIMITS["finger"]
            c = pb.constraints.new('LIMIT_ROTATION'); c.name = "HandLimit"; c.owner_space = 'LOCAL'
            for ax, (lo, hi) in zip("xyz", lim):
                setattr(c, "use_limit_" + ax, True); setattr(c, "min_" + ax, _R(lo)); setattr(c, "max_" + ax, _R(hi))
        # flex sign check: the rig must flex forward on +X (true for MPFB default); limits assume it
        lo = rig.pose.bones.get("lowerarm01." + s)
        if lo: lo.use_ik_limit_x = True; lo.ik_min_x = 0.0; lo.ik_max_x = _R(145)

def _key(rig, s, rot, frame, amount):
    for n, q in rot.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        q0 = pb.rotation_quaternion.copy()
        if amount < 1.0: q = q0.slerp(q, amount)
        if q0.dot(q) < 0: q = -q
        pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=frame, group=n)

def apply_pose(rig_obj, side, pose_name, frame, amount=1.0, spread=None):
    """Key fingers + thumb of `side` ("L"/"R") into `pose_name` at `frame`; amount<1 blends from the pose currently evaluated."""
    bpy.context.scene.frame_set(int(frame))
    _key(rig_obj, side, _pose_rots(rig_obj, side, pose_name, spread), frame, amount)

def _rest_hand(rig, s):
    BN = rig.data.bones; wr = BN["wrist." + s].head_local
    d = BN[_b(3, 1, s)].head_local - wr; a = BN[_b(2, 1, s)].head_local - BN[_b(5, 1, s)].head_local
    n = d.cross(a) if s == "L" else a.cross(d)
    def basis(d_, n_):
        d_ = d_.normalized(); n_ = (n_ - d_ * n_.dot(d_)).normalized()
        a_ = d_.cross(n_) if s == "R" else n_.cross(d_)
        return Matrix((d_, a_, n_)).transposed()
    palm = wr.lerp(BN[_b(3, 1, s)].head_local, 0.6)
    return wr, basis(d, n), basis, palm

def _rest_palm_sign(rig, s, n_rest):
    """+1 if the rest-pose cross-product normal points to the palm side (flexing the middle finger moves its tip along it)"""
    BN = rig.data.bones; b1, b3 = BN[_b(3, 1, s)], BN[_b(3, 3, s)]
    tip0 = b3.tail_local
    # rotate the middle finger chain 40 deg about finger3-1's local X at rest and see where the tip goes
    M1 = b1.matrix_local; R = M1 @ Quaternion((1, 0, 0), _R(40)).to_matrix().to_4x4() @ M1.inverted()
    return 1.0 if ((R @ tip0) - tip0).dot(n_rest) >= 0 else -1.0

def place_hand(rig_obj, side, frame, palm_point, palm_normal, finger_dir, skin=0.012):
    """Key IK_hand.<side> so the palm centre sits `skin` off `palm_point` (world), the palm facing `palm_normal`
    (= direction from the hand toward what it touches), fingers pointing along `finger_dir`."""
    s = side; rig = rig_obj; inv = rig.matrix_world.inverted(); R3 = inv.to_3x3()
    P = inv @ Vector(palm_point); nW = (R3 @ Vector(palm_normal)).normalized(); fW = (R3 @ Vector(finger_dir)).normalized()
    wr, B0, basis, palm = _rest_hand(rig, s)
    sign = _rest_palm_sign(rig, s, B0.col[2])
    Rm = basis(fW, nW * sign) @ B0.transposed()
    W = P - nW * skin - Rm @ (palm - wr)
    M = Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ rig.data.bones["IK_hand." + s].matrix_local
    pb = rig.pose.bones["IK_hand." + s]; loc, q, _ = (rig.data.bones["IK_hand." + s].matrix_local.inverted() @ M).decompose()
    pb.rotation_mode = 'QUATERNION'
    if pb.rotation_quaternion.dot(q) < 0: q = -q
    pb.location = loc; pb.rotation_quaternion = q
    pb.keyframe_insert("location", frame=frame, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)

def _dist_to(obj, p_world):
    """signed distance (m) from a world point to obj's surface (negative = inside)"""
    inv = obj.matrix_world.inverted(); ok, loc, nrm, idx = obj.closest_point_on_mesh(inv @ p_world)
    if not ok: return 9.0
    w = obj.matrix_world @ loc; nw = (obj.matrix_world.to_3x3().inverted().transposed() @ nrm).normalized()
    dvec = p_world - w; return dvec.length if dvec.dot(nw) >= 0 else -dvec.length

def grip_object(rig_obj, side, frame, target_obj, contact_point, approach_dir, finger_dir=None, finger_radius=0.008, grip=None):
    """Place IK_hand so the palm meets `contact_point` (world) moving along `approach_dir` (hand -> object), then close every
    finger and the opposing thumb until it touches `target_obj` (closest-point test along every phalanx bone, 3 samples each).
    finger_dir: default = perpendicular to the object's longest axis (fingers wrap round it), pointing away from the shoulder.
    grip: None = auto ('pinch' for objects thinner than 12 mm: thumb and index close on both faces at the edge; else 'wrap').
    Returns {tip bone: closing fraction at first contact (None = no contact within the pose range); for a wrap the thumb entry is its tip-to-surface distance in m}."""
    sc = bpy.context.scene; s = side; rig = rig_obj; Mw = rig.matrix_world
    nW = Vector(approach_dir).normalized(); C = Vector(contact_point)
    sc.frame_set(int(frame))
    shoulder = Mw @ rig.pose.bones["upperarm01." + s].head
    dims = target_obj.dimensions; ax = max(range(3), key=lambda i: dims[i]); thin_ax = min(range(3), key=lambda i: dims[i])
    grip = grip or ("pinch" if dims[thin_ax] < 0.012 else "wrap")
    R3 = target_obj.matrix_world.to_3x3()
    if grip == "pinch":
        ns = (R3 @ Vector([1.0 if i == thin_ax else 0.0 for i in range(3)])).normalized()
        fW = (nW - ns * nW.dot(ns)).normalized()                     # fingers point along the approach, in the sheet plane
        palmN = ns if ns.dot(Vector((0, 0, -1))) >= 0 else -ns       # palm faces across the sheet (thumb on the far face)
        place_hand(rig, s, frame, C - fW * 0.08 - palmN * 0.02, palmN, fW)
        rot0 = _pose_rots(rig, s, "pinch")
        for _ in range(2):                                           # move the hand so the pinch point lands on the edge
            sc.frame_set(int(frame)); H = _Hand(rig, s); F = H.fk(rot0)
            pp = Mw @ ((F[_b(1, 3, s)][1] + F[_b(2, 3, s)][1]) / 2)
            pb = rig.pose.bones["IK_hand." + s]; delta = rig.matrix_world.inverted().to_3x3() @ (C - pp)
            pb.location = pb.location + rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ delta
            pb.keyframe_insert("location", frame=frame, group=pb.name)
        fingers = (2,); open_ = _pose_rots(rig, s, "open_alarm"); closed = rot0
    else:
        if finger_dir is None:
            L = (R3 @ Vector([1.0 if i == ax else 0.0 for i in range(3)])).normalized()
            fd = L.cross(nW)
            if fd.length < 1e-3: fd = Vector((0, 0, 1)).cross(nW)
            fd.normalize()
            if fd.dot(C - shoulder) < 0: fd = -fd
        else:
            fd = Vector(finger_dir)
        fW = (fd - nW * fd.dot(nW)).normalized()
        place_hand(rig, s, frame, C, nW, fW)
        fingers = FING; open_ = _pose_rots(rig, s, "shield"); closed = _pose_rots(rig, s, "power_fist")
    sc.frame_set(int(frame)); H = _Hand(rig, s)
    rot = dict(_pose_rots(rig, s, "relaxed")); rot.update({k: v for k, v in open_.items()}); report = {}
    def touching(bones, R):
        F = H.fk(R)
        for bn in bones:
            h, t = F[bn]
            for u in (0.35, 0.7, 1.0):
                if _dist_to(target_obj, Mw @ h.lerp(t, u)) < finger_radius: return bn
        return None
    if grip == "wrap":    # back the hand off along the approach until the open hand clears the surface (no start-inside)
        pb = rig.pose.bones["IK_hand." + s]; back = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ (Mw.inverted().to_3x3() @ (-nW * 0.003))
        for _ in range(25):
            F = H.fk(open_)
            worst = min(_dist_to(target_obj, Mw @ F[bn][0].lerp(F[bn][1], u)) for k in FING for bn in [_b(k, j, s) for j in (1, 2, 3)] for u in (0.5, 1.0))
            if worst >= finger_radius * 0.8: break
            pb.location = pb.location + back; pb.keyframe_insert("location", frame=frame, group=pb.name)
            sc.frame_set(int(frame)); H = _Hand(rig, s)
    if grip == "pinch":   # middle/ring/little curl away under the index (out of the sheet)
        for k in (3, 4, 5):
            for j in (1, 2, 3): rot[_b(k, j, s)] = closed[_b(k, j, s)]
    if grip == "wrap":    # thumb opposes: aimed at the surface point across the object from the fingers
        for k in FING:      # close the fingers first so the thumb solve sees them
            chain = [_b(k, j, s) for j in (1, 2, 3)]
            for i in range(0, 41):
                u = i / 40.0; trial = dict(rot)
                for bn in chain: trial[bn] = open_[bn].slerp(closed[bn], u)
                if touching(chain, trial): report[chain[-1]] = round(u, 3); break
                rot = trial
            else: report[chain[-1]] = None
        wr_, d_, n_, a_ = H.frame(); F = H.fk(rot)
        side_ = (F[_b(2, 1, s)][0] - F[_b(3, 1, s)][0]).normalized()
        guess = Mw @ (F[_b(2, 1, s)][0] + side_ * 0.02 + n_ * 0.035)
        inv = target_obj.matrix_world.inverted(); ok, loc, nrm, idx = target_obj.closest_point_on_mesh(inv @ guess)
        tgt = Mw.inverted() @ (target_obj.matrix_world @ loc)
        rot.update(_solve_thumb(H, rot, ("point", finger_radius + 0.002), wr_, d_, n_, a_, target=tgt, obj=target_obj, radius=finger_radius))
        F = H.fk(rot); report[_b(1, 3, s)] = round(_dist_to(target_obj, Mw @ F[_b(1, 3, s)][1]), 4)
        _key(rig, s, rot, frame, 1.0)
        return report
    for k in fingers + (1,):
        chain = [_b(k, j, s) for j in (1, 2, 3)]; hit = None
        probe = chain[1:] if k == 1 else chain          # the thumb's base bone sits in the palm: test only its two phalanges
        for i in range(0, 41):
            u = i / 40.0; trial = dict(rot)
            for bn in chain: trial[bn] = open_[bn].slerp(closed[bn], u)
            if touching(probe, trial): hit = u; break
            rot = trial
        report[chain[-1]] = round(hit, 3) if hit is not None else None
    _key(rig, s, rot, frame, 1.0)
    return report
