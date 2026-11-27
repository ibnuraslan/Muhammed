"""CaveRescue v011 stage B: acting, props, the ONE camera (no cuts), visibility, water/flood, VO.
blender -b build.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (CaveRescue v010 timing): beats 1/341/571/687/891/1065/1160/1321/1463/1591/1761/1885/2105/2249,
frames 1-2436. Every limb target is computed in the character's body frame (rest space) and keyed as an IK target;
feet stand on the real floor (ray cast on the carved rock)."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(23)
END = 2436
O = bpy.data.objects
sc.frame_start, sc.frame_end = 1, END
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
T = Matrix.Translation
def Rz(d): return Matrix.Rotation(math.radians(d), 3, 'Z')
def Rx(d): return Matrix.Rotation(math.radians(d), 3, 'X')
def Ry(d): return Matrix.Rotation(math.radians(d), 3, 'Y')
def V(*a): return Vector(a)
def lerp(a_, b_, t): return a_ + (b_ - a_) * t
def ss(a_, b_, x): return smooth((x - a_) / (b_ - a_)) if b_ != a_ else float(x >= b_)

# ================================================================== floor (ray cast on the carved rock, front closed)
FRONT = O["FRONT_CTL"]
_BV = []
def _build_bvh():
    for n in ("ROCK_Back", "ROCK_Front"):
        o = O[n]; upd(); dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh(); Mw = o.matrix_world
        _BV.append(BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons])); e.to_mesh_clear()
ROUTE = [(-12, 0.0), (0, 0.0), (20, -0.3), (45, 0.2), (75, 1.0), (98, -0.6), (112, -8.0), (135, -8.0), (150, 0.4),
         (185, 3.0), (215, 3.5), (232, -2.5), (245, -6.0), (270, -6.0), (284, -3.2), (293, -1.6), (300, -1.2)]
def floor_route(x):
    for (x0, z0), (x1, z1) in zip(ROUTE, ROUTE[1:]):
        if x <= x1: t = (x - x0) / (x1 - x0); t = t * t * (3 - 2 * t); return z0 + (z1 - z0) * t
    return ROUTE[-1][1]
def ground_z(x, y):
    if not _BV: _build_bvh()
    z0 = 6.0 if x < -3 else (4.5 if x > 289 else floor_route(x) + 1.6)
    best = None
    for b in _BV:
        h = b.ray_cast(Vector((x, y, z0)), Vector((0, 0, -1)), 30.0)
        if h[0] is not None and (best is None or h[0].z > best): best = h[0].z
    return best if best is not None else 0.0

# ================================================================== actors
class Actor:
    def __init__(s, name):
        s.n = name; s.o = O[name]; s.CT = make_human_ctrl(s.o); add_hand_limits(s.o)
        # v012 natural limb limits: the elbow and knee are HINGES (no twist, no sideways bend), never past straight,
        # at most ~148 deg (elbow) / ~150 deg (knee) of total flexion. Limits are relative to each rig's rest bend.
        Bn = s.o.data.bones
        for sd in "LR":
            for up_, lo_, mx_ in (("upperarm02.", "lowerarm01.", 148.0), ("upperleg02.", "lowerleg01.", 150.0)):
                rest = math.degrees(Bn[up_ + sd].y_axis.angle(Bn[lo_ + sd].y_axis))
                lo = s.o.pose.bones[lo_ + sd]; lo.lock_ik_y = lo.lock_ik_z = True
                lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-(rest - 4.0)); lo.ik_max_x = math.radians(mx_ - rest)
                lo.ik_stiffness_x = 0.0
        for pb in s.o.pose.bones: pb.rotation_mode = 'QUATERNION'
        s.H = Human(s.CT); B = s.o.data.bones
        s.rh = B["root"].head_local.copy()
        g = lambda n: B[n].head_local.copy()
        s.sh = {d: g("upperarm01." + d) for d in "LR"}; s.hip = {d: g("upperleg01." + d) for d in "LR"}
        s.ank = {d: g("foot." + d) for d in "LR"}; s.wr = {d: g("wrist." + d) for d in "LR"}
        s.Lu = (g("upperarm01.L") - g("lowerarm01.L")).length; s.Lf = (g("lowerarm01.L") - g("wrist.L")).length
        s.Lt = (g("upperleg01.L") - g("lowerleg01.L")).length; s.Ls = (g("lowerleg01.L") - g("foot.L")).length
        s.head = g("head"); s.M = Matrix.Identity(4); s.R = Matrix.Identity(3); s._hs = None
        s.floor_local = s.ank["L"].z
        log("actor", name, "arm", round(s.Lu + s.Lf, 3), "leg", round(s.Lt + s.Ls, 3), "root", tuple(round(c, 3) for c in s.rh))
    # body frame: rest-space point -> world
    def setM(s, pos, yaw, flex=0.0, side=0.0):
        s.R = Rz(yaw) @ Rx(flex) @ Ry(side); s.M = T(pos) @ s.R.to_4x4() @ T(-s.rh)
    def W(s, p): return s.M @ Vector(p)
    def head_signs(s):
        if s._hs: return s._hs
        pb = s.o.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd(); e0 = Wh(s.o, "eye.L"); out = {}
        for ax, i in (("X", 0), ("Z", 2)):
            pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
            out[ax] = Wh(s.o, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
        s._hs = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1); return s._hs
    def body(s, f, pos, yaw, flex=0.0, side=0.0, sp=(0.0, 0.0, 0.0), head=(0.0, 0.0, 0.0)):
        """root + spine + head. yaw: 0 faces -Y, +90 faces +X. flex +: pitch forward (90 = prone). head=(yaw +left, pitch +down, roll)"""
        s.setM(pos, yaw, flex, side)
        s.H.key_root(f, Vector(pos), yaw=yaw, flex=flex, side=side)
        for n, w in Human.SPINE_W.items():
            s.CT.key_rot(n, f, [("X", sp[0] * w), ("Y", sp[2] * w), ("Z", sp[1] * w)])
        sx, sz = s.head_signs()
        for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
            s.CT.key_rot(n, f, [("X", sx * head[1] * w), ("Y", head[2] * w), ("Z", sz * head[0] * w)])
    def pole(s, d, f, target, kind):
        n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + d; pb = s.CT.PB[n]
        pb.location = s.CT.rest(n).to_3x3().inverted() @ (Vector(target) - s.CT.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def foot(s, d, f, a_local, rot_local=None, knee_local=None):
        """ankle at rest-space point a_local, foot rotated by rot_local (rest space), knee pole in rest space"""
        A = s.W(a_local); Rw = s.R @ (rot_local or Matrix.Identity(3))
        M = T(A) @ Rw.to_4x4() @ T(-s.ank[d]) @ s.CT.rest("IK_foot." + d)
        s.CT.key_world("IK_foot." + d, f, M)
        kl = knee_local or (Vector(a_local) + V(0, -0.7, 0.45))
        s.pole(d, f, s.W(kl), "knee")
    def foot_world(s, d, f, A, yaw, pitch=0.0, pole=None):
        M = T(Vector(A)) @ (Rz(yaw) @ Rx(pitch)).to_4x4() @ T(-s.ank[d]) @ s.CT.rest("IK_foot." + d)
        s.CT.key_world("IK_foot." + d, f, M)
        s.pole(d, f, pole if pole is not None else Vector(A) + Rz(yaw) @ V(0, -0.7, 0.45), "knee")
    def hand(s, d, f, palm_local, n_local, f_local, elbow_local=None, world=False):
        if world: P, N, F = Vector(palm_local), Vector(n_local), Vector(f_local)
        else: P, N, F = s.W(palm_local), s.R @ Vector(n_local), s.R @ Vector(f_local)
        place_hand(s.o, d, f, P, N, F)
        sx = 1 if d == "L" else -1
        el = elbow_local if elbow_local is not None else s.sh[d] + V(sx * 0.35, 0.45, -0.25)
        s.pole(d, f, el if world and elbow_local is not None else s.W(el), "elbow")
    def hand_M(s, d, f, Mw, elbow_world):
        """key IK_hand to a world matrix (for props owned by the hand: the prop follows the wrist exactly)"""
        s.CT.key_world("IK_hand." + d, f, Mw)
        s.pole(d, f, elbow_world, "elbow")
    def arm_hang(s, d, f, swing=0.0, out=0.06, bend=0.965):
        """a relaxed hanging arm, palm toward the thigh, elbow bent ~30 deg; swing (m) forward(+)/back"""
        sx = 1 if d == "L" else -1; L = (s.Lu + s.Lf) * bend
        p = s.sh[d] + V(sx * out, -swing, -math.sqrt(max(0.01, L * L - swing * swing - out * out)))
        s.hand(d, f, p + V(0, -0.02, -0.05), V(-sx, 0.15, 0), V(0, -0.15, -1))
CAST = {n: Actor(n) for n in ("Boy1", "Boy2", "Boy3", "Boy4", "Coach", "Diver1", "Diver2", "Diver3", "Medic")}
for a_ in CAST.values():
    for d in "LR": apply_pose(a_.o, d, "relaxed", 1)

# ================================================================== visibility helpers
def desc(o):
    out = [o]
    for c in o.children: out += desc(c)
    return out
def show_ranges(objs, ranges):
    """visible only inside the [a, b) ranges"""
    for o in objs:
        o.hide_render = True; o.hide_viewport = True
        o.keyframe_insert("hide_render", frame=0); o.keyframe_insert("hide_viewport", frame=0)
        for a_, b_ in ranges:
            for fr, h in ((a_, False), (b_, True)):
                o.hide_render = h; o.hide_viewport = h
                o.keyframe_insert("hide_render", frame=fr); o.keyframe_insert("hide_viewport", frame=fr)
        set_interp(o, 'CONSTANT', "hide")
def char_objs(name):
    r = O[name]; g = set(r.get("gear", "").split(",")) if r.get("gear") else set()
    return [r] + [c for c in r.children if c.name not in g and not c.name.startswith("FullMask")]

# ================================================================== GROUP A: the walk in, the flood, the run (1-700)
GROUP = {"Coach": (-5.4, -0.9), "Boy1": (-6.3, 0.55), "Boy2": (-7.3, -0.25), "Boy3": (-7.9, 1.25), "Boy4": (-8.6, -1.15)}
TORCH_OF = {"Coach": ("Torch_Coach", "R"), "Boy1": ("Torch_Boy1", "R"), "Boy3": ("Torch_Boy3", "L")}
W_SPD, R_SPD = 1.45, 3.0
F_STOP, F_RUN, F_FREEZE = 392, 452, 640
def gx(name, f):
    x0, y0 = GROUP[name]; ph = (hash(name) % 7) * 2
    if f <= F_STOP: x = x0 + W_SPD * (f - 1) / 60.0
    elif f <= F_RUN: x = x0 + W_SPD * (F_STOP - 1) / 60.0 + 0.25 * ss(F_STOP, F_STOP + 30, f)
    else: x = x0 + W_SPD * (F_STOP - 1) / 60.0 + 0.25 + R_SPD * ((min(f, F_FREEZE) - F_RUN) / 60.0) * ss(F_RUN, F_RUN + 25, min(f, F_FREEZE)) ** 0.5
    y = y0 + 0.08 * math.sin(f * 0.02 + ph)
    return Vector((x, y, 0))

def gait(A, f0, f1, path, yaw_fn, stride, duty, lift, bob, lean, run=False, carry=None, step=2):
    """feet + root (walk/run), and the arms: carry(d) -> None for a free swinging arm, or a callable keying that hand"""
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]): dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    H = A.H
    for d, ph in (("L", 0.0), ("R", 0.5)):
        cyc = [x / stride + ph for x in dist]; per = {}
        for i, c in enumerate(cyc): per.setdefault(int(math.floor(c)), []).append(i)
        plant = {}
        for pid, idx in per.items():
            st = [i for i in idx if (cyc[i] % 1.0) < duty]
            if st:
                im = min(st, key=lambda i: abs((cyc[i] % 1.0) - duty / 2))
                plant[pid] = (H.foot_xy(d, path(frames[im]), yaw_fn(frames[im])), yaw_fn(frames[im]))
        first = (H.foot_xy(d, path(f0), yaw_fn(f0)), yaw_fn(f0)); last = (H.foot_xy(d, path(f1), yaw_fn(f1)), yaw_fn(f1))
        for i, f in enumerate(frames):
            if (i % step) and i != len(frames) - 1: continue
            pid = int(math.floor(cyc[i])); fr = cyc[i] % 1.0
            if dist[-1] < 0.05: xy, yw, lf, pt = first[0], first[1], 0.0, 0.0
            elif fr < duty:
                xy, yw = plant.get(pid, first if i < len(frames) / 2 else last); lf = 0.0; pt = 0.0
            else:
                a_ = plant.get(pid, first); b_ = plant.get(pid + 1, last); u = (fr - duty) / (1 - duty)
                xy = a_[0].lerp(b_[0], smooth(u)); yw = a_[1] + (b_[1] - a_[1]) * smooth(u)
                lf = lift * math.sin(math.pi * u); pt = (35 if run else 25) * math.sin(math.pi * u) - 10
            H.key_foot(d, f, xy, yw, lf, pt)
    out = {}
    for i, f in enumerate(frames):
        if (i % step) and i != len(frames) - 1: continue
        p = path(f); cyc = (dist[i] / stride) % 1.0 if dist[-1] > 0.05 else 0.0
        gz_ = 0.5 * (ground_z(p.x, p.y) + ground_z(p.x + 0.15, p.y))
        crouch = 0.06 if run else 0.025
        z = gz_ + A.rh.z - crouch - bob * (0.5 + 0.5 * math.cos(4 * math.pi * cyc))
        yw = yaw_fn(f)
        out[f] = (Vector((p.x, p.y, z)), yw, lean * 0.5, 3 * math.sin(2 * math.pi * cyc), cyc)
    return out

def group_a(name):
    A = CAST[name]; tor = TORCH_OF.get(name)
    yaw = lambda f: 90.0
    walk = gait(A, 1, F_STOP, lambda f: gx(name, f), yaw, 0.62 if "Boy" in name else 0.72, 0.62, 0.07, 0.02, 5.0)
    stop = gait(A, F_STOP, F_RUN, lambda f: gx(name, f), yaw, 0.6, 0.62, 0.05, 0.0, 2.0)
    run = gait(A, F_RUN, F_FREEZE, lambda f: gx(name, f), yaw, 1.15 if "Boy" in name else 1.3, 0.42, 0.13, 0.04, 12.0, run=True)
    allk = {}; allk.update(walk); allk.update(stop); allk.update(run)
    look_side = 1 if GROUP[name][1] > 0 else -1          # which shoulder they look back over
    rnd = random.Random(hash(name) % 1000)
    for f in sorted(allk):
        pos, yw, fl, sd, cyc = allk[f]
        lookb = ss(F_STOP + 5, F_STOP + 30, f) * (1 - ss(F_RUN - 12, F_RUN + 8, f))
        tw = look_side * 55 * lookb
        hy = look_side * 75 * lookb + 6 * math.sin(f * 0.031 + rnd.random() * 6) * (1 - lookb)
        run_amt = ss(F_RUN, F_RUN + 20, f)
        A.body(f, pos, yw, flex=fl, side=sd, sp=(5 + 8 * run_amt, tw - 6 * math.sin(2 * math.pi * cyc), 0), head=(hy, -3 - 4 * run_amt, 0))
        sw = math.sin(2 * math.pi * cyc)
        for d in "LR":
            sx = 1 if d == "L" else -1; sg = sw if d == "R" else -sw
            if tor and tor[1] == d:
                # the lantern carried forward at hip height, its beam ahead (palm down on the top handle)
                p = A.sh[d] + V(sx * 0.02, -0.26 - 0.03 * sg, -(A.Lu + A.Lf) * 0.70)
                A.hand(d, f, p, V(0, 0, -1), V(-sx, 0, 0), elbow_local=A.sh[d] + V(sx * 0.35, 0.35, -0.3))
            elif run_amt > 0.5 and f > F_RUN:
                L = (A.Lu + A.Lf) * 0.80
                p = A.sh[d] + V(sx * 0.10, -0.22 * sg - 0.08, -L * 0.72 + 0.10 * max(0, sg))
                A.hand(d, f, p, V(-sx, 0.2, 0), V(0, -0.4, -1), elbow_local=A.sh[d] + V(sx * 0.25, 0.55, -0.2))
            else:
                A.arm_hang(d, f, swing=0.13 * sg if f < F_STOP else 0.02 * sg, out=0.11)
    # faces: calm walk, alarm when they look back, effort while running
    rig = A.o
    key_face(rig, 1, smile=0.15 if "Boy" in name else 0.05); key_face(rig, F_STOP, smile=0.1)
    key_face(rig, F_STOP + 25, brow=0.9, jaw=0.35); key_face(rig, F_RUN + 20, brow=0.6, jaw=0.45, squint=0.2)
    key_face(rig, F_FREEZE, brow=0.6, jaw=0.4)
    blinks(rig, [40 + (hash(name) % 50), 170 + (hash(name) % 40), 300, 520])
    for d in "LR":
        if not (tor and tor[1] == d): apply_pose(rig, d, "relaxed", 1)
    return A
for nm in GROUP: group_a(nm)

# ---- the lanterns: gripped on the top handle (grip solved at a setup frame), owned by the wrist for the whole walk
def handle_point(t):
    vs = [t.matrix_world @ v.co for v in t.data.vertices]; zmax = max(v.z for v in vs)
    top = [v for v in vs if v.z > zmax - 0.012]
    return sum(top, Vector()) / len(top), zmax
for nm, (tn, d) in TORCH_OF.items():
    A = CAST[nm]; t = O[tn]; FS = -60
    fs(1); upd()
    wr = Wh(A.o, "wrist." + d); pal = wr + (Wt(A.o, "wrist." + d) - wr) * 1.6
    # put the lantern under the palm, beam forward (+X walking direction -> the lantern front -Y rotated to +X)
    t.rotation_mode = 'XYZ'; t.rotation_euler = (0, 0, math.radians(90)); t.location = (0, 0, 0); upd()
    hp, zmax = handle_point(t)
    t.location = pal - hp - V(0, 0, 0.012); upd()
    hp, zmax = handle_point(t)
    for k in ("location", "rotation_euler"): t.keyframe_insert(k, frame=FS)
    # hold the hand (frame FS) exactly where it is at frame 1, then let the grip solver close the fingers on the handle
    try:
        rep = grip_object(A.o, d, FS + 1, t, hp, (0, 0, -1), finger_dir=(0, -1 if d == "L" else 1, 0))
        fs(FS + 1); pb_ = A.o.pose.bones["IK_hand." + d]
        pb_.keyframe_insert("location", frame=FS + 2); pb_.keyframe_insert("rotation_quaternion", frame=FS + 2)
        log("grip", nm, rep)
    except Exception as e:
        log("grip_fail", nm, e); apply_pose(A.o, d, "wrap_grip", FS + 1)
    # the grip_object placed IK_hand at FS+1: re-key frame 1 hand pose unchanged (the walk keys start at 1)
    t.rotation_mode = 'QUATERNION'
    owner_switch(t, FS + 3, A.o, "wrist." + d, log=log)
    for c_ in t.constraints:
        if c_.type == 'CHILD_OF':
            try: c_.keyframe_delete("influence", frame=0)
            except Exception: pass
    beam = O[tn + "_Beam"]; beam.location = (0, 0, 0)
    # spot along the lantern front (local -Y), from its front face
    vs = [v.co for v in t.data.vertices]; ymin = min(v.y for v in vs)
    beam.location = (0, ymin - 0.01, (max(v.z for v in vs) + min(v.z for v in vs)) * 0.45); beam.rotation_euler = (math.radians(-90 + 8), 0, 0)
# re-solve: grip_object keyed IK_hand at FS+1, which is fine (before the walk); the finger keys are constant after it

# ================================================================== GROUP B: the chamber (890-1884)
SIT = {"Boy1": (304.55, 2.25, -100), "Boy2": (305.7, 3.55, -110), "Boy3": (307.0, 2.15, -95), "Boy4": (308.0, 3.85, -120), "Coach": (309.3, 2.6, -105)}
def sit(A, f, x, y, yaw, hunch=12.0, head=(0, 0, 0), hands="knees", breathe=0.0, lean_back=0.0):
    """sitting on the mud shelf, knees up, feet flat in front, hands resting on the knees"""
    gz_ = ground_z(x, y)
    hipz = A.hip["L"].z
    pos = Vector((x, y, gz_ + (A.rh.z - hipz) + 0.10 + 0.004 * breathe))
    A.body(f, pos, yaw, flex=-lean_back, sp=(hunch + 2 * breathe, 0, 0), head=head)
    Lleg = A.Lt + A.Ls; fwd = 0.70 * Lleg
    for d in "LR":
        sx = 1 if d == "L" else -1
        a_loc = V(A.hip[d].x * 1.25, A.hip[d].y - fwd, A.hip[d].z - 0.085 + 0.075)
        # knee up: from the triangle hip-knee-ankle (in the sagittal plane)
        H_ = A.hip[d]; D = (a_loc - H_); dl = D.length
        cosa = max(-1, min(1, (A.Lt ** 2 + dl ** 2 - A.Ls ** 2) / (2 * A.Lt * dl))); ang = math.acos(cosa)
        dn = D.normalized(); up = V(0, 0, 1); up = (up - dn * up.dot(dn)).normalized()
        K = H_ + (dn * math.cos(ang) + up * math.sin(ang)) * A.Lt
        A.foot(d, f, a_loc, None, knee_local=K + V(sx * 0.05, -0.3, 0.25))
        if hands == "knees":
            A.hand(d, f, K + V(sx * 0.01, 0.02, 0.075), V(0, 0, -1), V(0, -0.85, -0.5), elbow_local=A.sh[d] + V(sx * 0.4, 0.15, -0.35))
    return K
def chamber_group(name, f0, f1, events=None):
    A = CAST[name]; x, y, yaw = SIT[name]; rnd = random.Random(hash(name) % 997)
    for f in range(f0, f1 + 1, 12):
        br = math.sin(2 * math.pi * f / 230 + rnd.random() * 6)
        hy, hp = 8 * math.sin(f / 97.0 + rnd.random()), 6 + 4 * math.sin(f / 61.0)
        if 975 <= f <= 1070: hy, hp = -25, -4                              # squint into the diver's lamp (pool side)
        if 1330 <= f <= 1460: hy, hp = -30, -4                             # stare at the dark water
        if 1470 <= f <= 1880: hy, hp = 28 if name != "Coach" else 35, 8      # watch the rescuers at Boy1
        if events: hy, hp = events(f, hy, hp)
        sit(A, f, x, y, yaw, head=(hy, hp, 0), breathe=br)
    sit(A, f1, x, y, yaw, head=(hy, hp, 0))
    rig = A.o
    key_face(rig, f0, brow=0.3); key_face(rig, 960, brow=0.2)
    key_face(rig, 990, squint=0.9, brow=-0.3, smile=0.0); key_face(rig, 1060, squint=0.5, smile=0.25)
    key_face(rig, 1120, squint=0.0, smile=0.1); key_face(rig, 1330, brow=0.9, jaw=0.25); key_face(rig, 1460, brow=0.6, jaw=0.1)
    key_face(rig, 1600, brow=0.3)
    blinks(rig, [930 + (hash(name) % 40), 1130, 1250 + (hash(name) % 30), 1420, 1560, 1700 + (hash(name) % 40), 1840])
    for d in "LR": apply_pose(rig, d, "relaxed", f0)
for nm in ("Boy2", "Boy3", "Boy4", "Coach"): chamber_group(nm, 890, 1884)
B1 = CAST["Boy1"]
def b1_events(f, hy, hp):
    if 1591 <= f <= 1700: return (-20, 10)        # watches the needle
    if f > 1700: return (0, 8 + 4 * ss(1700, 1760, f))   # drifting off: head drops a little, forward
    return (hy, hp)
chamber_group("Boy1", 890, 1888, b1_events)
for f in range(1682, 1889, 12):
    sit(B1, f, *SIT["Boy1"], hunch=-4.0 * ss(1682, 1730, f), lean_back=14.0 * ss(1682, 1730, f), head=(0, 4, 0))
key_face(B1.o, 1700, brow=0.1); eyes_closed(B1.o, 1725, 2436, ramp=30)

# ---- the lanterns rest on the shelf beside the boys (lit) while they sit; gone after the rescue
for nm, (tn, d) in TORCH_OF.items():
    t = O[tn]; x, y, yaw = SIT[nm]
    owner_switch(t, 700, None, log=log)
    p = Vector((x + 0.45, y + 0.45, 0)); p.z = ground_z(p.x, p.y)
    vs = [t.matrix_world @ v.co for v in t.data.vertices]
    key_basis(t, 701, T(p + V(0, 0, 0.002)) @ Matrix.Rotation(math.radians(yaw + 40), 4, 'Z') @ T(V(0, 0, -min((v.co.z for v in t.data.vertices)))))
    key_basis(t, 2436, T(p + V(0, 0, 0.002)) @ Matrix.Rotation(math.radians(yaw + 40), 4, 'Z') @ T(V(0, 0, -min((v.co.z for v in t.data.vertices)))))

# ================================================================== divers
D1, D2, D3 = CAST["Diver1"], CAST["Diver2"], CAST["Diver3"]
def swim(A, f, head_pos, heading_yaw, kick_phase, pitch=0.0, arms="forward", hand_fn=None, look=-35):
    """prone swimmer: body horizontal (flex 90+pitch), head toward heading; flutter kick; arms ahead on the line"""
    flex = 90.0 + pitch
    # put the root so the head lands at head_pos
    A.setM(V(0, 0, 0), heading_yaw, flex); hoff = A.W(A.head) - A.W(A.rh)
    pos = Vector(head_pos) - hoff
    A.body(f, pos, heading_yaw, flex=flex, sp=(-8, 3 * math.sin(kick_phase), 0), head=(0, look, 0))
    for d in "LR":
        sx = 1 if d == "L" else -1; k = math.sin(kick_phase + (0 if d == "L" else math.pi))
        a_loc = V(A.ank[d].x * 0.9, A.ank[d].y - 0.10 * k - 0.04, A.ank[d].z + 0.03)
        A.foot(d, f, a_loc, Rx(65 + 10 * k), knee_local=V(A.hip[d].x, A.hip[d].y - 0.8, A.hip[d].z - 0.35))
        if hand_fn and hand_fn(A, d, f): continue
        if arms == "forward":
            p = A.sh[d] + V(-sx * 0.04, -0.20, 0.42 + 0.03 * math.sin(kick_phase * 0.5 + sx))
            A.hand(d, f, p, V(0, -1, 0.2), V(0, -0.3, 1), elbow_local=A.sh[d] + V(sx * 0.35, 0.05, 0.3))
        elif arms == "side":
            p = A.sh[d] + V(sx * 0.10, -0.05, -(A.Lu + A.Lf) * 0.85)
            A.hand(d, f, p, V(-sx, 0.2, 0), V(0, 0, -1))
        elif arms == "scull":
            p = A.sh[d] + V(sx * 0.35, -0.18 + 0.08 * math.sin(kick_phase), -0.22)
            A.hand(d, f, p, V(0, 0.3 * math.sin(kick_phase), -1), V(sx, -0.5, 0), elbow_local=A.sh[d] + V(sx * 0.45, 0.25, -0.3))
def tread(A, f, head_pos, yaw, ph, look=(0, 0, 0)):
    """vertical in the water, head out, sculling arms just under the surface, slow kick"""
    A.setM(V(0, 0, 0), yaw, 8.0); hoff = A.W(A.head) - A.W(A.rh)
    pos = Vector(head_pos) - hoff
    A.body(f, pos, yaw, flex=8.0, sp=(4, 0, 0), head=look)
    for d in "LR":
        sx = 1 if d == "L" else -1; k = math.sin(ph + (0 if d == "L" else math.pi))
        A.foot(d, f, V(A.ank[d].x * 1.1, A.ank[d].y - 0.15 * k, A.ank[d].z + 0.08), Rx(55), knee_local=V(A.hip[d].x, A.hip[d].y - 0.8, A.hip[d].z - 0.3))
        p = A.sh[d] + V(sx * 0.36, -0.22 + 0.07 * math.sin(ph * 1.3), -0.30)
        A.hand(d, f, p, V(0, 0, -1), V(sx * 0.6, -0.8, 0), elbow_local=A.sh[d] + V(sx * 0.5, 0.3, -0.25))
def path_pts(keys):
    f_ = catmull([(k[0], Vector(k[1])) for k in keys]); return f_
# Diver 1: rises in the pool (900-1000), lamp on the boys, dives back (1060-1200) leading the camera down to the
# restriction, hovers there (1200-1290) watching the lone diver go on, then swims back up and surfaces (1290-1346).
# v012: a lit diver or a lamp is in frame on every underwater frame.
D1_P = path_pts([(890, (288.5, 0.3, -1.2)), (935, (291.5, 0.4, 0.5)), (965, (295.5, 1.0, 0.65)), (1000, (297.4, 1.2, 1.38)), (1060, (297.6, 1.25, 1.38)),
                 (1090, (294.5, 0.8, 0.6)), (1105, (291.0, 0.3, 0.5)), (1125, (288.6, 0.45, -1.2)), (1160, (286.0, 0.35, -2.2)), (1200, (284.2, 0.25, -2.55))])
D1_R = path_pts([(1290, (284.2, 0.25, -2.55)), (1315, (287.0, 0.3, -1.8)), (1335, (289.6, 0.4, -0.4)), (1350, (290.7, 0.45, 0.72))])
# v012 fix: head-first swimming (v011's heading formula swam feet-first) and smooth turns (<= 8 deg per frame)
_yaw = [None]
def turn_to(target, rate=24.0):
    if _yaw[0] is None: _yaw[0] = target; return target
    d = (target - _yaw[0] + 180.0) % 360.0 - 180.0
    _yaw[0] += max(-rate, min(rate, d)); return _yaw[0]
for f in range(890, 1350, 3):
    if 990 <= f <= 1066:
        swim(D1, f, D1_P(f) + V(0, 0, 0.03 * math.sin(f * 0.1)), turn_to(90 + 6 * math.sin(f * 0.03)), f * 0.12, pitch=-28, arms="scull", look=-30)
    elif 1200 <= f <= 1290:          # hovering at the restriction, sculling gently, looking ahead
        swim(D1, f, D1_P(1200) + V(0.04 * math.sin(f * 0.05), 0.03 * math.sin(f * 0.07), 0.04 * math.sin(f * 0.06)), turn_to(-90 + 5 * math.sin(f * 0.02)),
             f * 0.09, pitch=-6, arms="scull", look=-38)
    else:
        P_ = D1_R if f > 1290 else D1_P
        v = P_(f + 2) - P_(f - 2); yw = math.degrees(math.atan2(v.x, -v.y)) if v.to_2d().length > 1e-3 else (_yaw[0] or -90)
        pitch = -math.degrees(math.atan2(v.z, max(1e-4, v.to_2d().length))) * 0.8
        swim(D1, f, P_(f), turn_to(yw), f * 0.22, pitch=max(-40, min(40, pitch)))
# Diver 3: the lone diver ahead swims on through the restriction into the dark passage; his lamp dims to a small
# glow far away (1215-1300). Never shown up close.
D3_P = path_pts([(1100, (283.0, 0.05, -2.75)), (1170, (279.0, 0.05, -3.35)), (1250, (272.5, 0.05, -4.6)), (1340, (264.5, 0.0, -5.35))])
for f in range(1100, 1342, 3):
    swim(D3, f, D3_P(f), -90, f * 0.2, pitch=-8)
for n_ in ("Diver1_Beam", "Diver2_Beam"): O[n_].data.energy = 150.0
beam3 = O["Diver3_Beam"]
for fr, e in ((1100, 150.0), (1215, 140.0), (1300, 12.0)):
    beam3.data.energy = e; beam3.data.keyframe_insert("energy", frame=fr)
lm3 = O["Diver3_TorchLens"].data.materials[0].copy(); lm3.name = "M_TorchLens3"; O["Diver3_TorchLens"].data.materials[0] = lm3
em = lm3.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for fr, e in ((1100, 30.0), (1215, 30.0), (1300, 9.0)):
    em.default_value = e; em.keyframe_insert("default_value", frame=fr)

# ---- B9-B11 (1463-1884): Diver 1 and Diver 2 kneel on the shelf beside Boy1 (fins off)
def half_kneel(A, f, x, y, yaw, torso=(10, 0, 0), head=(0, 10, 0), hands=None, dz=0.0, both=None):
    both = (A is D2) if both is None else both
    """right knee up (foot planted ahead), left knee down with the toes tucked"""
    gz_ = ground_z(x, y)
    hipz = A.hip["L"].z
    pos = Vector((x, y, gz_ + (A.rh.z - hipz) + A.Lt * 0.97 + 0.05 + dz))
    A.body(f, pos, yaw, flex=4.0, sp=torso, head=head)
    fl = A.hip["L"].z - A.Lt * 0.97 - 0.05                        # floor level in rest space
    # down (left) leg: knee under the hip, shin back, toes tucked
    kn = V(A.hip["L"].x * 1.1, A.hip["L"].y - 0.04, fl + 0.05)
    A.foot("L", f, kn + V(0, A.Ls * 0.97, 0.09), Rx(78), knee_local=kn + V(0.05, -0.4, 0.0))
    # up (right) leg: foot flat ahead, shin vertical
    if both:
        kr = V(A.hip["R"].x * 1.1, A.hip["R"].y - 0.04, fl + 0.05)
        A.foot("R", f, kr + V(0, A.Ls * 0.97, 0.09), Rx(78), knee_local=kr + V(-0.05, -0.4, 0.0))
    else:
        A.foot("R", f, V(A.hip["R"].x * 1.3, A.hip["R"].y - A.Lt * 0.92, fl + 0.075), None,
               knee_local=V(A.hip["R"].x * 1.3, A.hip["R"].y - A.Lt - 0.5, fl + A.Ls + 0.3))
    if hands: hands(A, f)
B1x, B1y, B1yaw = SIT["Boy1"]
fs(1600); upd()
def b1_world(bone, f, tail=False):
    fs(f); upd(); return (Wt if tail else Wh)(B1.o, bone)
# Diver 1 kneels at Boy1's left (the -Y side as Boy1 faces the pool), facing +Y toward the boy's left arm
D1K = (B1x + 0.02, B1y - 0.53, 0.0)
SYR = O["Syringe"]
def d1_hands_idle(A, f):
    for d in "LR":
        sx = 1 if d == "L" else -1
        A.hand(d, f, A.sh[d] + V(sx * 0.12, -0.32, -0.42), V(0, 0, -1), V(-sx * 0.3, -1, 0), elbow_local=A.sh[d] + V(sx * 0.4, 0.3, -0.3))
for f in range(1352, 1592, 15):
    half_kneel(D1, f, D1K[0], D1K[1], 0.0 + 180.0, head=(5 * math.sin(f / 50.0), 18, 0), hands=d1_hands_idle)
# ---- the syringe: pinched at the barrel in his right hand from 1460; the injection 1600-1700 into the left deltoid
FSET = 1455
fs(FSET); upd()
wrR = Wh(D1.o, "wrist.R"); pal = wrR + (Wt(D1.o, "wrist.R") - wrR) * 1.7
SYR.rotation_mode = 'QUATERNION'
key_basis(SYR, FSET - 1, T(pal + V(0, 0.03, -0.03)) @ Euler((0, 0, math.radians(90)), 'XYZ').to_matrix().to_4x4())
fs(FSET)
try:
    rep = grip_object(D1.o, "R", FSET, SYR, pal + V(0, 0.03, -0.03), (0, 0, -1), grip="pinch"); log("syringe grip", rep)
except Exception as e:
    log("syringe grip fail", e); apply_pose(D1.o, "R", "tripod", FSET)
owner_switch(SYR, FSET + 1, D1.o, "wrist.R", log=log)
fs(FSET + 1); upd()
REL = (D1.o.matrix_world @ D1.o.pose.bones["IK_hand.R"].matrix).inverted() @ SYR.matrix_world   # syringe in the IK_hand frame
def key_syringe_world(f, S, elbow):
    """move D1's right hand so the syringe sits at world matrix S"""
    D1.hand_M("R", f, D1.o.matrix_world.inverted() @ S @ REL.inverted(), elbow)
# needle direction: along the syringe local +X; aim at Boy1's left deltoid from the side (-Y)
def delt(f):
    s_ = b1_world("upperarm01.L", f); e_ = b1_world("lowerarm01.L", f)
    out = (s_ - b1_world("upperarm01.R", f)); out.z = 0; out.normalize()
    return s_ + (e_ - s_) * 0.28 + out * 0.045, out
for f in range(1592, 1736, 4):
    half_kneel(D1, f, D1K[0], D1K[1], 180.0, head=(0, 22, 0), torso=(30, -8, 0))
    P, out = delt(f)
    t_in = ss(1610, 1650, f) - ss(1690, 1720, f)                 # approach, hold (press plunger), withdraw
    tip_gap = 0.10 * (1 - t_in) + 0.006
    dirn = -out                                                  # needle points into the arm
    Rm = Matrix((dirn, Vector((0, 0, 1)).cross(dirn).normalized(), dirn.cross(Vector((0, 0, 1)).cross(dirn).normalized()))).transposed()
    tip_local = V(0.0705, 0, 0)
    S = T(P - dirn * tip_gap - Rm @ tip_local) @ Rm.to_4x4()
    key_syringe_world(f, S, Wh(D1.o, "upperarm01.R") + V(0.15, -0.35, -0.35))
    # left hand steadies the boy's upper arm from below the injection point (palm on the arm, fingers forward)
    fs(f); upd()
    arm_pt = b1_world("upperarm01.L", f).lerp(b1_world("lowerarm01.L", f), 0.62)
    D1.hand("L", f, arm_pt + out * 0.075, -out, V(0, 0, -1),
            elbow_local=arm_pt + out * 0.4 + V(0.25, 0, -0.25), world=True)
apply_pose(D1.o, "L", "cup_hold", 1592)
for f in range(1740, 1890, 15):
    half_kneel(D1, f, D1K[0], D1K[1], 180.0, head=(10, 15, 0), hands=d1_hands_idle)
# the plunger travel is not modelled separately (one rigid syringe); after the injection he puts it down on the bag
owner_switch(SYR, 1738, None, log=log)
show_ranges([SYR], [(1455, 1745)])

# Diver 2: kneels facing Boy1 (in front of him, between him and the pool), mask fitting 1761-1845
D2K = (B1x - 0.55, B1y + 0.62, 0.0)
D2Y = 40.5
FFM, STR = O["FullMask"], O["FullMaskStraps"]
def d2_idle(A, f):
    for d in "LR":
        sx = 1 if d == "L" else -1
        A.hand(d, f, A.sh[d] + V(sx * 0.14, -0.30, -0.45), V(0, 0, -1), V(-sx * 0.3, -1, 0), elbow_local=A.sh[d] + V(sx * 0.4, 0.3, -0.3))
for f in range(1352, 1700, 15):
    half_kneel(D2, f, D2K[0], D2K[1], D2Y, head=(10 * math.sin(f / 40.0), 15, 0), hands=d2_idle)
# fitted mask pose = its build pose relative to Boy1's head bone at rest
head_rest = B1.o.data.bones["head"].matrix_local.copy()
FFM_REST = FFM.matrix_world.copy()
def head_world(f):
    fs(f); upd(); return B1.o.matrix_world @ B1.o.pose.bones["head"].matrix
def fitted(f): return head_world(f) @ head_rest.inverted() @ FFM_REST
FS2 = 1700
fs(FS2); upd()
S0 = fitted(FS2); fwd = (S0.to_3x3() @ V(0, -1, 0)).normalized()
start = T(fwd * 0.30 + V(0, 0, -0.05)) @ S0
FFM.rotation_mode = 'QUATERNION'; key_basis(FFM, FS2 - 1, start)
half_kneel(D2, FS2, D2K[0], D2K[1], D2Y, head=(0, 20, 0), hands=d2_idle)
cp = start.translation + start.to_3x3() @ V(0.10, 0.02, -0.04)      # the right edge of the skirt (Diver 2's right hand)
apply_pose(D2.o, "R", "cup_hold", FS2)
for f in range(FS2 + 4, 1850, 4):
    half_kneel(D2, f, D2K[0], D2K[1], D2Y, head=(0, 22, 0), torso=(24, 0, 0))
    u = ss(1765, 1830, f)
    Sf = fitted(f); Sm = T(fwd * 0.30 * (1 - u) + V(0, 0, -0.05 * (1 - u))) @ Sf
    if f < 1832: key_basis(FFM, f, Sm)
    rp = Sm.translation + Sm.to_3x3() @ V(0.105, 0.02, -0.04); rn = (Sm.to_3x3() @ V(-1, 0, 0)).normalized()
    if f > 1830: rp = rp.lerp(head_world(f).translation + (Sm.to_3x3() @ V(0.11, 0.09, 0.0)), ss(1832, 1846, f))
    D2.hand("R", f, rp, rn, Sm.to_3x3() @ V(0, 0, 1), elbow_local=rp + V(-0.3, -0.3, -0.3), world=True)
    # left hand on the other side of the skirt
    lp = Sm.translation + Sm.to_3x3() @ V(-0.105, 0.02, -0.04); ln = (Sm.to_3x3() @ V(1, 0, 0)).normalized()
    if f > 1830:          # then both hands slide back to pull the straps snug behind his head
        hb = head_world(f).translation
        lp = lp.lerp(hb + (Sm.to_3x3() @ V(-0.11, 0.09, 0.0)), ss(1832, 1846, f))
    D2.hand("L", f, lp, ln, Sm.to_3x3() @ V(0, 0, 1), elbow_local=lp + V(0.25, -0.35, -0.3), world=True)
owner_switch(FFM, 1832, B1.o, "head", log=log)
for f in range(1850, 1892, 14):
    half_kneel(D2, f, D2K[0], D2K[1], D2Y, head=(0, 15, 0), hands=d2_idle)
apply_pose(D2.o, "L", "cup_hold", FS2 + 4); apply_pose(D2.o, "R", "cup_hold", FS2 + 4)
show_ranges([FFM] + list(FFM.children), [(1700, 2030), (2058, 2436)])
show_ranges([STR], [(1836, 2436)])

# ================================================================== B12 the tow (1890-2010) and B13 the carry out (2110-2436)
SK = O["Sked"]; SK.rotation_mode = 'QUATERNION'
# over the ledge slab (top z 0.15 for x > 290) in the shallow pool, then down the step into the sump (x < 289.6)
TOW_P = path_pts([(1870, (294.5, 0.35, 0.47)), (1882, (294.2, 0.35, 0.45)), (1925, (291.3, 0.4, 0.42)), (1948, (289.7, 0.43, 0.22)),
                  (1975, (288.95, 0.45, -0.55)), (2008, (288.75, 0.45, -1.0)), (2050, (288.2, 0.42, -1.5)), (2060, (288.0, 0.4, -1.6))])
def sked_M(f):
    """the sked's world matrix: underwater tow (head end first, -X) then the carry out of the mouth"""
    if f < 2058:
        # v012: the tow starts in the chamber pool just under the surface and descends into the sump, so the
        # stretcher + towing diver lead the camera's dive (never an empty dark pool)
        p0 = TOW_P(f); v = TOW_P(f + 3) - TOW_P(f - 3)
        pitch = 0.6 * math.degrees(math.atan2(-v.z, max(1e-3, -v.x)))
        return (T(p0 + V(0, 0, 0.03 * math.sin(f * 0.05))) @ Matrix.Rotation(math.radians(180), 4, 'Z') @
                Matrix.Rotation(math.radians(pitch), 4, 'Y') @ Matrix.Rotation(math.radians(3 * math.sin(f * 0.04)), 4, 'X'))
    x = lerp(1.4, -3.6, ss(2125, 2320, f)); y = lerp(-0.2, -0.9, ss(2125, 2320, f))
    z = ground_z(x, y) + 0.74 + 0.012 * math.sin(f * 0.21)
    return T(V(x, y, z)) @ Matrix.Rotation(math.radians(180 - 8 * ss(2112, 2320, f)), 4, 'Z')
for f in list(range(1870, 2058, 4)) + [2057] + list(range(2058, 2437, 4)):
    key_basis(SK, f, sked_M(f))
show_ranges(desc(SK), [(1870, 2030), (2058, 2437)])
def lie_in_sked(A, f, M):
    """supine in the sked, head at the sked's +X end, arms by the sides, legs straight, relaxed (sedated)"""
    R3 = M.to_3x3(); hip = A.hip["L"].z
    pos = M @ V(0.06, 0, 0.022 + 0.10)
    yaw_s = math.degrees(math.atan2(R3.col[0].y, R3.col[0].x))
    A.body(f, pos, yaw_s - 90.0, flex=-88.0, sp=(-2, 0, 0), head=(0, -4, 0))
    for d in "LR":
        sx = 1 if d == "L" else -1
        A.foot(d, f, V(A.ank[d].x * 1.15, A.ank[d].y + 0.02, A.ank[d].z + 0.02), Rx(25), knee_local=V(A.hip[d].x, A.hip[d].y - 0.8, A.hip[d].z - 0.4))
        p = V(A.hip[d].x + sx * 0.13, A.hip[d].y - 0.08, A.hip[d].z + 0.02)
        A.hand(d, f, p, V(-sx, 0.3, 0), V(0, -0.3, -1), elbow_local=A.sh[d] + V(sx * 0.4, 0.3, -0.3))
for fc in iter_fcurves(B1.o.animation_data.action):          # hold the seated pose to 1885 (hidden at 1885)
    if fc.data_path.startswith("hide"): continue
    fc.keyframe_points.insert(1881, fc.evaluate(1874), options={'FAST'})
for f in [1882] + list(range(1888, 2054, 6)) + [2056] + list(range(2058, 2437, 6)):
    lie_in_sked(B1, f, sked_M(f))
for fc in iter_fcurves(B1.o.animation_data.action):          # drop the stray seated chamber keys inside the switch
    if fc.data_path.startswith("hide"): continue
    for kp in [k for k in fc.keyframe_points if 1882 < k.co.x < 1888]: fc.keyframe_points.remove(kp, fast=True)
    fc.update()
# Diver 1 tows: swims just above and beside the sked's head end, his left hand on the head-end loop
def loop_world(f, k):
    loc = [(-0.74, 0.295), (0.74, 0.295), (-0.74, -0.295), (0.74, -0.295)][k]
    return sked_M(f) @ V(loc[0], loc[1], O["Sked"]["H"] + 0.02)
for f in range(1882, 2054, 3):
    M = sked_M(f); head_end = M @ V(0.95, 0.0, 0.0)
    def tow_hand(A, d, f_, _M=M):
        if d != "L": return False
        lp = loop_world(f_, 1)
        A.hand("L", f_, lp + V(0, 0, 0.03), V(0, 0, -1), V(-1, 0, 0), elbow_local=lp + V(0.1, 0.35, 0.35), world=True); return True
    swim(D1, f, head_end + V(-0.30, 0.12, 0.64), -90, f * 0.2, pitch=-4, hand_fn=tow_hand, look=-30)
apply_pose(D1.o, "L", "wrap_grip", 1882, 0.8)
# B13: Diver 1 carries the front (walking -X ahead of the sked), Diver 2 the back; hands on the end loops
def carry(A, f0, f1, front):
    def path(f):
        M = sked_M(f); return (M @ V(1.12 if front else -1.12, 0, 0)).to_3d() * Vector((1, 1, 0))
    yaw = lambda f: 90.0 + math.degrees(math.atan2(*(sked_M(f).to_3x3().col[0].to_2d().yx))) * 0 + (-180 + 8 * ss(2112, 2320, f)) * 0 - 90.0 - 8 * ss(2112, 2320, f) * 0
    ks = gait(A, f0, f1, path, lambda f: -90.0 + 8 * ss(2112, 2320, f), 0.7, 0.62, 0.06, 0.015, 4.0)
    for f in sorted(ks):
        pos, yw, fl, sd, cyc = ks[f]
        A.body(f, pos, yw, flex=fl, side=sd, sp=(4, 0, 0), head=((-25 if front else 15) * ss(2240, 2290, f), -2, 0))
        for d in "LR":
            sx = 1 if d == "L" else -1
            # front carrier (facing -X): the loops are behind his hips; back carrier: in front of him
            k = (0 if d == "R" else 2) if front else (1 if d == "L" else 3)
            k = {("F", "L"): 1, ("F", "R"): 3, ("B", "L"): 0, ("B", "R"): 2}[("F" if front else "B", d)]
            lp = loop_world(f, k)
            A.hand(d, f, lp + V(0, 0, 0.035), V(0, 0, -1), (lp - Wh(A.o, "upperarm01." + d)).normalized() * 0 + V(0, -sx, 0) * 0 + V(1 if front else -1, 0, 0),
                   elbow_local=lp + V(0.25 if front else -0.25, sx * 0.25 * (1 if front else -1), 0.3), world=True)
    for d in "LR": apply_pose(A.o, d, "wrap_grip", f0, 0.85)
carry(D1, 2058, 2436, True)
carry(D2, 2058, 2436, False)
for A in (D1, D2):
    key_face(A.o, 2104, smile=0.0); key_face(A.o, 2260, smile=0.6, squint=0.2); blinks(A.o, [2150, 2300, 2400])
# B13 crowd: the coach, the other boys and the medic wait outside and cheer (each with his own timing and pose)
CROWD = {"Coach": (-5.2, -2.0, 150), "Boy2": (-6.2, -2.3, 140), "Boy3": (-5.6, 1.0, 35), "Boy4": (-6.8, 0.7, 25), "Medic": (-10.6, 2.6, 70)}
for nm, (x, y, yaw) in CROWD.items():
    A = CAST[nm]; rnd = random.Random(hash(nm) % 991); ph = rnd.random() * 6
    for f in range(2058, 2437, 6):
        cheer = ss(2250 + rnd.randint(0, 25), 2280 + rnd.randint(0, 25), f)
        gz_ = ground_z(x, y); pos = V(x, y, gz_ + A.rh.z - 0.02 - 0.03 * cheer * (0.5 + 0.5 * math.sin(f * 0.25 + ph)))
        A.body(f, pos, yaw + 4 * math.sin(f * 0.02 + ph), sp=(-3 * cheer, 0, 0), head=(-10 + 8 * math.sin(f * 0.03 + ph), -4 - 6 * cheer, 0))
        for d in "LR":
            sx = 1 if d == "L" else -1
            fxy = Vector((x, y, 0)) + Rz(yaw) @ V(sx * 0.11, 0, 0)
            A.foot_world(d, f, V(fxy.x, fxy.y, ground_z(fxy.x, fxy.y) + A.ank[d].z), yaw)
            up = cheer * (1.0 if (d == "R" or nm in ("Boy2", "Boy3")) else 0.55)
            wave = math.sin(f * 0.22 + ph + sx) * 0.06 * cheer
            if up > 0.05:
                p = A.sh[d] + V(sx * (0.20 + wave), -0.10, -0.35 + 0.80 * up)
                A.hand(d, f, p, V(0, -1, 0), V(sx * 0.2, 0, 1), elbow_local=A.sh[d] + V(sx * 0.5, 0.25, -0.1))
            else:
                A.arm_hang(d, f, swing=0.02 * math.sin(f * 0.03 + ph))
    key_face(A.o, 2058, smile=0.3); key_face(A.o, 2250, smile=0.4); key_face(A.o, 2290, smile=1.0, squint=0.3, jaw=0.25)
    blinks(A.o, [2130 + rnd.randint(0, 30), 2230, 2350 + rnd.randint(0, 30)])
    for d in "LR": apply_pose(A.o, d, "relaxed", 2100)

# D1 holds his kneel to 1877 (hidden at 1878) before the swim keys of the tow take over at 1882
for fc in iter_fcurves(D1.o.animation_data.action):
    if fc.data_path.startswith("hide"): continue
    v1874 = fc.evaluate(1874)
    for kp in [k for k in fc.keyframe_points if 1874 < k.co.x < 1882]: fc.keyframe_points.remove(kp, fast=True)
    fc.update(); fc.keyframe_points.insert(1877, v1874, options={'FAST'})
# D1 switches from the surfacing swimmer to the kneeling rescuer between 1349 and 1350, mid-whip (both off frame)
for fc in iter_fcurves(D1.o.animation_data.action):
    if fc.data_path.startswith("hide"): continue
    fc.keyframe_points.insert(1350, fc.evaluate(1352), options={'FAST'})
# ================================================================== who is visible when (teleports happen off camera)
show_ranges(char_objs("Coach"), [(1, 641), (890, 1885), (2058, 2437)])
show_ranges(char_objs("Boy2"), [(1, 641), (890, 1885), (2058, 2437)])
show_ranges(char_objs("Boy3"), [(1, 641), (890, 1885), (2058, 2437)])
show_ranges(char_objs("Boy4"), [(1, 641), (890, 1885), (2058, 2437)])
show_ranges(char_objs("Boy1"), [(1, 641), (890, 1881), (1882, 2030), (2058, 2437)])
show_ranges(char_objs("Diver1"), [(895, 1878), (1882, 2030), (2058, 2437)])
show_ranges(char_objs("Diver2"), [(1300, 1892), (2058, 2437)])
show_ranges(char_objs("Diver3"), [(1060, 1352)])
show_ranges(char_objs("Medic"), [(2058, 2437)])
def gear(n): return [O[x] for x in O[n]["gear"].split(",")]
for n, rngs in (("Diver1", [(895, 1878), (1882, 2030), (2058, 2437)]), ("Diver2", [(1300, 1892), (2058, 2437)]), ("Diver3", [(1060, 1352)])):
    fins = [o for o in gear(n) if "Fin" in o.name]
    show_ranges([o for o in gear(n) if o not in fins], rngs)
    show_ranges(fins, [r for r in ((895, 1350), (1060, 1342), (1882, 2056)) if any(a_ <= r[0] < b_ for a_, b_ in rngs)])
torches = [O[t] for t, _ in TORCH_OF.values()]
show_ranges(torches + [O[t.name + "_Beam"] for t in torches], [(1, 641), (890, 1885)])
show_ranges([O["GearBag"], O["SpareTank"]], [(1352, 1892)])
for o, loc, rz in ((O["GearBag"], (B1x + 1.05, B1y - 1.15), 25), (O["SpareTank"], (B1x + 1.45, B1y - 0.75), -10)):
    z = ground_z(*loc) + 0.2 if o.name == "GearBag" else ground_z(*loc) + 0.088
    o.location = (loc[0], loc[1], z); o.rotation_euler = (0, 0, math.radians(rz))

# ================================================================== the cutaway, flood, route, orbs, water, rain, silt, bubbles
FD2, FC2 = 2008, 2117
FRONT.location = (0, 0, 0)
# v012: the second cutaway opens at 2008 (camera low in the sump, seeing only back-half rock) and CLOSES INSTANTLY at
# 2117 while the camera is inside the passage near the mouth facing the back wall: no mountain ever rises into view.
for fr, z in ((559, 0.0), (560, -300.0), (955, -300.0), (995, 0.0), (FD2, 0.0), (FD2 + 1, -300.0), (FC2 - 1, -300.0), (FC2, 0.0)):
    FRONT.location.z = z; FRONT.keyframe_insert("location", index=2, frame=fr)
_amb = set(desc(O["Ambulance"]))
fronts = [o for o in desc(FRONT) if o is not FRONT and o not in _amb and not o.name.startswith("PoolSurf")]
show_ranges(fronts + [O["PoolSurf_Front"]], [(0, 560), (952, FD2 + 1), (FC2, 2437)])
XS_R = [(645, 938), (2034, 2100)]
RT = O["FX_Route"]; show_ranges([RT, O["FX_Beacon"], O["FX_BeaconRing"]], XS_R)
RT.data.bevel_factor_end = 0.0; RT.data.keyframe_insert("bevel_factor_end", frame=645)
RT.data.bevel_factor_end = 1.0; RT.data.keyframe_insert("bevel_factor_end", frame=700)
RT["flood"] = 0.0; RT.keyframe_insert('["flood"]', frame=720); RT["flood"] = 1.0; RT.keyframe_insert('["flood"]', frame=830)
for o in (O["FX_Beacon"], O["FX_BeaconRing"]):
    for f in range(596, 965, 30):
        s_ = 1.0 + 0.25 * (f % 60 == 0); o.scale = (s_,) * 3; o.keyframe_insert("scale", frame=f)
    for f in range(2012, 2115, 30):
        o.scale = (1.0 + 0.25 * (f % 60 == 0),) * 3; o.keyframe_insert("scale", frame=f)
# rescue orbs: one by one from the chamber along the route toward the mouth (B12, 2030-2105)
RPTS = [V(x, -0.6, floor_route(x) + 1.0) for x in range(0, 304, 2)]
def route_at(u):
    i = max(0, min(len(RPTS) - 2, int(u * (len(RPTS) - 1)))); t = u * (len(RPTS) - 1) - i; return RPTS[i].lerp(RPTS[i + 1], t)
orbs = [O["FX_Orb%d" % i] for i in range(5)]
show_ranges(orbs, [(2025, 2100)])
for i, o in enumerate(orbs):
    for f in range(2020, 2114, 3):
        u = 1.0 - max(0.0, min(1.0, (f - 2028 - i * 9) / 80.0)) * 0.97
        o.location = route_at(u); o.keyframe_insert("location", frame=f)
# water: the sumps and the chamber pool fill during B4; glow only in the cross-section
waters = [O[n] for n in ("Water1_Back", "Water1_Front", "Water2_Back", "Water2_Front", "Water3_Back", "Water3_Front")]
for o in waters:
    o.scale = (1, 1, 0.02); o.keyframe_insert("scale", index=2, frame=700)
    o.scale = (1, 1, 1.0); o.keyframe_insert("scale", index=2, frame=840)
# v012: the water bodies are clear; their cut faces glow as a teal section fill only in the cross-section views
WM = bpy.data.materials["M_WaterVol"]; sec = WM.node_tree.nodes["Section"].inputs["Fac"]
for fr, e in ((0, 1.0), (950, 1.0), (953, 0.0), (FD2 + 1, 0.0), (FD2 + 22, 1.0), (2110, 1.0), (2112, 0.0)):
    sec.default_value = e; sec.keyframe_insert("default_value", frame=fr)
show_ranges([O["PoolSurf_Back"]], [(953, FD2 + 1), (FC2, 2437)])
# the flood surge across the mouth floor and into the passage (B2)
SU = O["FX_Surge"]
for fr, sx_ in ((420, 0.18), (440, 0.25), (500, 0.40), (570, 0.52), (640, 0.62)):
    SU.scale = (sx_, 1, 1); SU.keyframe_insert("scale", index=0, frame=fr)
SU.location = (-14.0, 0, 0)
show_ranges([SU], [(420, 570)])
# the rain (B2): a looping fall of two stacked sheets
RC = O["RainCtl"]
RC.location.z = 0.0; RC.keyframe_insert("location", index=2, frame=341)
RC.location.z = -24.0; RC.keyframe_insert("location", index=2, frame=501)
for fc in iter_fcurves(RC.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    fc.modifiers.new('CYCLES')
show_ranges([O["FX_Rain"], O["FX_Rain2"]], [(341, 720)])
# silt stirred up in the restriction as the divers pass
for i, o in enumerate(O[n] for n in ("FX_Silt0", "FX_Silt1", "FX_Silt2")):
    s0 = o.scale.copy()
    o.scale = s0 * 0.3; o.keyframe_insert("scale", frame=1080 + i * 15)
    o.scale = s0 * 1.4; o.keyframe_insert("scale", frame=1160 + i * 15)
    o.scale = s0 * 1.6; o.keyframe_insert("scale", frame=1320)
show_ranges([O["FX_Silt0"], O["FX_Silt1"], O["FX_Silt2"]], [(1065, 1330), (1885, 2050)])
WV = O["WaveCtl"]; WV.location = (0, 0, 0); WV.keyframe_insert("location", frame=1)
WV.location = (6.0, 3.0, 2.0); WV.keyframe_insert("location", frame=END)
for fc in iter_fcurves(WV.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
# bubbles: small clusters rising from the regulators (divers) and the boy's mask during the tow
M_BUB = bpy.data.materials.new("M_Bubble"); M_BUB.use_nodes = True
_p = M_BUB.node_tree.nodes["Principled BSDF"]; _p.inputs["Roughness"].default_value = 0.05; _p.inputs["Base Color"].default_value = (0.9, 0.97, 1, 1)
_p.inputs["Emission Color"].default_value = (0.8, 0.95, 1, 1); _p.inputs["Emission Strength"].default_value = 0.6; _p.inputs["Alpha"].default_value = 0.6
def bubbles(tag, src, f0, f1, n=7, rise=0.7, period=48):
    bs = []; cache = {f: src(f) for f in range(f0, f1 + 1, 3)}
    for i in range(n):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012 + 0.006 * (i % 3), segments=12, ring_count=6)
        b = bpy.context.active_object; b.name = "FX_Bub_%s%d" % (tag, i); b.data.materials.append(M_BUB); bs.append(b)
        for f in range(f0, f1 + 1, 3):
            u = ((f - f0) / period + i / n) % 1.0
            b.location = cache[f] + V(0.02 * math.sin(i * 2 + f * 0.2), 0.02 * math.cos(i * 3 + f * 0.17), rise * u); b.keyframe_insert("location", frame=f)
            if u > 0.93 or (f - f0) < 3: pass
    show_ranges(bs, [(f0, f1)])
def regsrc(n): return lambda f: (fs(f), upd(), O[n + "_Regulator"].matrix_world.translation + V(0, 0, 0.05))[2]
bubbles("d1a", regsrc("Diver1"), 900, 995); bubbles("d1b", regsrc("Diver1"), 1100, 1340)
bubbles("d3", regsrc("Diver3"), 1100, 1336); bubbles("d1t", regsrc("Diver1"), 1898, 2028)
bubbles("b1", lambda f: (fs(f), upd(), FFM.matrix_world.translation + V(0, 0, 0.12))[2], 1890, 2028, n=5)
# lights: the sump glow only while we are underwater; the sun brightens at the end
SG = O["SU_Glow"].data
SGo = O["SU_Glow"]
for fr, x_ in ((1060, 291.0), (1160, 286.9), (1320, 285.0), (1885, 290.5), (2050, 288.6)):
    SGo.location = (x_, -0.2, floor_route(x_) + 0.9); SGo.keyframe_insert("location", frame=fr)
for fr, e in ((0, 0.0), (1060, 0.0), (1080, 22.0), (1330, 22.0), (1345, 0.0), (1885, 0.0), (1905, 30.0), (2050, 30.0), (2060, 0.0)):
    SG.energy = e; SG.keyframe_insert("energy", frame=fr)
SUN = O["Sun"].data
for fr, e in ((0, 3.0), (2280, 3.0), (2436, 5.0)):
    SUN.energy = e; SUN.keyframe_insert("energy", frame=fr)
show_ranges(desc(O["Ambulance"]), [(FC2, 2437)])

for n in ("JG_MouthFern0", "JG_MouthFern2"):
    if n in O: [bpy.data.objects.remove(o, do_unlink=True) for o in desc(O[n])]
# ================================================================== the ONE camera
cam = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36.0; cam.data.clip_start = 0.05; cam.data.clip_end = 2000
CK = [
    (1, (-3.0, -3.3, 1.55), (-6.6, 0.0, 1.2), 30), (120, (-1.2, -1.5, 1.6), (-4.8, -0.2, 1.3), 30),
    (230, (2.6, -1.35, 1.65), (-1.8, 0.1, 1.35), 30), (340, (5.6, -1.1, 1.6), (0.8, 0.1, 1.35), 30),
    (400, (7.1, -0.9, 1.55), (2.4, 0.2, 1.4), 30), (460, (8.6, -0.8, 1.5), (2.0, 0.0, 1.45), 28),
    (520, (11.6, -0.9, 1.5), (6.4, 0.2, 1.3), 28), (556, (13.2, -1.1, 1.6), (11.6, 2.0, 1.3), 28),
    (590, (13.0, -4.5, 2.6), (11.0, 0.5, 1.1), 28), (612, (13.5, -9.0, 3.8), (11.5, 0.5, 1.0), 28),
    (645, (40.0, -60.0, 15.0), (60.0, 0.0, 5.0), 30),
    (686, (150.0, -270.0, 10.0), (150.0, 0.0, 0.0), 30), (780, (190.0, -240.0, 6.0), (185.0, 0.0, -2.0), 32),
    (890, (240.0, -180.0, 4.0), (250.0, 0.0, -2.0), 32), (930, (296.0, -60.0, 10.0), (301.0, 0.0, 3.0), 30),
    (956, (302.8, -2.0, 3.2), (305.5, 3.0, 2.2), 24), (968, (303.4, 0.45, 3.0), (306.0, 3.4, 2.0), 24),
    (998, (303.3, 0.6, 2.95), (305.9, 3.3, 2.0), 25), (1032, (301.8, -0.7, 2.3), (298.0, 1.2, 1.5), 28),
    (1060, (301.6, -0.4, 2.2), (297.6, 1.0, 1.3), 28), (1080, (299.6, 0.1, 1.75), (296.0, 0.9, 0.7), 26),
    # v012 dive: the camera follows Diver 1 down (always 2-3 m behind him, his lamp + rim-lit back in frame)
    (1096, (297.6, 0.0, 1.0), (293.4, 0.6, 0.4), 24), (1112, (294.4, -0.1, 0.6), (290.2, 0.4, -0.5), 24),
    (1124, (291.0, -0.25, 0.75), (287.8, 0.4, -1.2), 24), (1138, (289.6, -0.3, 0.3), (286.6, 0.35, -1.9), 24),
    (1160, (288.5, -0.4, -1.35), (285.2, 0.3, -2.4), 24),
    (1200, (286.7, -0.45, -1.95), (279.0, 0.1, -3.4), 26),
    # the hover: Diver 1 in the foreground watches the lone diver's lamp go on and dim (the respectful pause)
    (1250, (286.4, -0.5, -2.0), (274.0, 0.05, -4.3), 30), (1290, (286.3, -0.5, -2.05), (271.0, 0.0, -4.8), 30),
    # back up with Diver 1 (the camera leads him, looking back at him) and out through the pool surface
    (1300, (287.6, -0.6, -1.65), (285.0, 0.3, -2.4), 28),
    (1312, (288.9, -0.7, -1.0), (286.6, 0.3, -1.85), 26), (1325, (289.7, -0.8, -0.1), (288.2, 0.35, -1.1), 26),
    (1336, (290.6, -0.85, 0.75), (289.6, 0.4, -0.35), 26),
    (1343, (292.4, -0.9, 1.55), (290.6, 0.45, 0.55), 26), (1350, (293.0, -0.8, 1.7), (293.2, 8.0, 1.6), 26),
    (1358, (294.6, -0.45, 1.65), (300.5, 1.7, 1.8), 26),
    (1368, (299.2, 0.6, 1.4), (304.5, 2.2, 2.3), 26), (1400, (302.6, 0.95, 2.45), (304.6, 2.25, 2.5), 35),
    (1460, (302.9, 0.75, 2.5), (304.6, 2.25, 2.45), 38), (1520, (302.5, -1.5, 3.2), (305.3, 2.3, 1.9), 26),
    (1590, (302.4, 0.2, 2.8), (304.6, 2.0, 2.2), 30), (1640, (302.6, 1.75, 2.35), (304.5, 1.85, 2.3), 40),
    (1700, (302.55, 1.7, 2.4), (304.5, 1.95, 2.35), 42), (1760, (302.4, 1.4, 2.7), (304.35, 2.3, 2.45), 45),
    (1830, (302.5, 1.45, 2.68), (304.35, 2.3, 2.47), 48), (1874, (302.6, 1.5, 2.65), (304.35, 2.3, 2.45), 46),
    # v012 tow: the turn from the mask close-up lands on the stretcher + towing diver just under the pool surface;
    # the camera dives with them (they stay 2+ m from the lens), ends low beside the stretcher facing the back wall,
    # the front drops unseen (2008) and the camera pulls straight back out of the cut into the cross-section.
    (1882, (302.3, 0.9, 2.55), (300.0, -2.0, 2.0), 30), (1890, (300.9, 0.3, 2.35), (294.0, 0.35, 0.8), 30),
    (1905, (296.4, -0.6, 1.65), (292.8, 0.35, 0.65), 28), (1922, (293.4, -0.9, 0.8), (291.4, 0.4, 0.5), 26),
    (1945, (291.4, -0.95, 0.55), (289.7, 0.43, 0.05), 26), (1960, (290.1, -1.0, 0.4), (289.2, 0.45, -0.3), 24),
    (1975, (289.6, -1.1, -0.25), (288.95, 0.45, -0.75), 22),
    (1995, (289.3, -1.15, -0.42), (288.8, 1.5, -1.1), 20), (2006, (288.9, -1.22, -0.42), (288.7, 2.0, -1.2), 20),
    (2016, (288.8, -5.0, -0.6), (288.6, 1.0, -1.0), 28), (2034, (276.0, -45.0, 8.0), (266.0, 0.0, -2.0), 28),
    (2080, (190.0, -240.0, 8.0), (160.0, 0.0, 0.0), 30), (2098, (60.0, -60.0, 12.0), (20.0, 0.0, 1.0), 30),
    # v012: into the open passage near the mouth, facing the back wall; the front closes unseen at 2117
    (2109, (19.0, -9.0, 2.6), (13.0, 2.0, 1.4), 28), (2116, (13.2, -1.3, 1.7), (9.6, 2.6, 1.4), 26),
    # turn to the mouth: the carriers walk the stretcher out into daylight; the crowd waits outside, facing us
    (2140, (11.8, -0.7, 1.75), (2.0, -0.4, 1.45), 28), (2200, (6.6, -0.5, 1.95), (-4.0, -0.5, 1.35), 28),
    (2249, (3.8, -0.5, 2.4), (-6.0, -0.6, 1.4), 28), (2300, (1.0, -0.6, 3.3), (-7.0, -1.2, 1.3), 28),
    # out over the carriers (1.5 m above the heads) and crane up: stretcher, cheering crowd, the ambulance + logo
    (2345, (-1.6, -0.8, 4.4), (-9.5, -1.8, 1.2), 28), (2395, (-3.2, -0.9, 5.9), (-11.0, -2.4, 1.3), 28),
    (2436, (-4.0, -0.9, 7.2), (-11.6, -2.4, 1.4), 28)]
cp_ = catmull([(k[0], Vector(k[1])) for k in CK]); ct_ = catmull([(k[0], Vector(k[2])) for k in CK]); cl_ = catmull([(k[0], float(k[3])) for k in CK])
_ext = [cp_(f) for f in list(range(1, 600, 5)) + list(range(2100, END + 1, 5))]
for o in [o for o in O if o.name.startswith("JG_") and o.parent is None or (o.name.startswith("JG_") and o.parent and o.parent.name == "FRONT_CTL")]:
    if any((o.matrix_world.translation.to_2d() - q.to_2d()).length < 3.2 + 1.5 * o.scale.x and q.z < 14 for q in _ext):
        for c_ in desc(o): bpy.data.objects.remove(c_, do_unlink=True)
D1HEAD = {}
for f in list(range(1084, 1204)) + list(range(1288, 1346)):
    if f % 2 == 1: fs(f); D1HEAD[f] = D1.o.matrix_world @ D1.o.pose.bones["head"].head
def d1w(f):
    for a_, b_ in ((1085, 1202), (1289, 1344)):
        if a_ <= f <= b_: return min(ss(a_, a_ + 10, f), 1.0 - ss(b_ - 6, b_, f)) * 0.85
    return 0.0
for f in range(1, END + 1, 2):
    p = cp_(f); t_ = ct_(f); cam.location = p
    if f in D1HEAD and d1w(f) > 0: t_ = t_.lerp(D1HEAD[f] + V(0, 0, 0.1), d1w(f))
    cam.rotation_mode = 'QUATERNION'; q = (t_ - p).to_track_quat('-Z', 'Y')
    if cam.rotation_quaternion.dot(q) < 0: q = -q
    cam.rotation_quaternion = q; cam.data.lens = cl_(f)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam.data.keyframe_insert("lens", frame=f)
cam.data.dof.use_dof = False

# ================================================================== v012 underwater look: fog, camera fill, diver rim/face lights
exec(open(HERE + "/lib_fog.py").read())
def cam_under(f):
    fs(f); p = cam.matrix_world.translation
    if abs(FRONT.matrix_world.translation.z) > 1.0: return False
    return (224.0 < p.x < 318.0 and p.z < POOL_Z_ - 0.02) or (96.0 < p.x < 154.0 and p.z < -2.22)
POOL_Z_ = 1.2
UNDER = {f for f in range(840, END + 1) if cam_under(f)}
log("camera under water frames", min(UNDER) if UNDER else None, max(UNDER) if UNDER else None, len(UNDER))
key_cam_under(UNDER, 0, END + 1)
log("fog spliced into materials:", apply_fog())
CF = bpy.data.lights.new("CAM_Fill", 'AREA'); CF.size = 0.6; CF.color = (0.78, 0.95, 1.0); CF.energy = 0.0
cfo = bpy.data.objects.new("CAM_Fill", CF); sc.collection.objects.link(cfo); cfo.visible_glossy = False; cfo.parent = cam; cfo.location = (0.0, 0.18, 0.05)
def key_steps(lightdata, on_value, frames_on, f0=0, f1=END + 1):
    prev = None
    for f in range(f0, f1 + 1):
        v = on_value if f in frames_on else 0.0
        if v != prev: lightdata.energy = v; lightdata.keyframe_insert("energy", frame=f); prev = v
    for fc in iter_fcurves(lightdata.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
key_steps(CF, 22.0, UNDER)
for n_ in ("Diver1", "Diver2", "Diver3"):
    key_steps(O[n_ + "_RimLight"].data, 22.0, UNDER)
    O[n_ + "_FaceLight"].data.energy = 6.0

# ================================================================== tidy + VO + save
for a_ in CAST.values(): quat_continuity(a_.o)
for o in O:
    if o.animation_data and o.animation_data.action: quat_continuity(o)
if not sc.sequence_editor: sc.sequence_editor_create()
snd = sc.sequence_editor.strips.new_sound("VO", VO, 1, 1) if hasattr(sc.sequence_editor, "strips") else sc.sequence_editor.sequences.new_sound("VO", VO, 1, 1)
bpy.ops.file.pack_all()
sc.render.filepath = "//render/CaveRescue_v012_####"
sc.render.image_settings.file_format = 'PNG'
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
