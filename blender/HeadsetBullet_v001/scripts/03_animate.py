"""Teen acting: seated gaming, impact jolt, headset removal, stunned look at the hole.
blender -b scene.blend --python 03_animate.py -- <out.blend> [posetest]"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "pipeline", "anim_lib.py")).read())
from mathutils import Quaternion
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; POSETEST = "posetest" in args

def fps(t): return 1 + round(t * 60)
BEAT = {1: 0.0, 2: 2.2, 3: 4.0, 4: 5.9, 5: 9.5, 6: 11.6, 7: 13.9, 8: 15.8, 9: 19.4, 10: 21.9}
BF = {k: fps(v) for k, v in BEAT.items()}
F_IMPACT = 700          # bullet touches the ear cup
F_GRAB = 1222           # hands closed on the cups; headset leaves the head-bone constraint
sc["F_IMPACT"] = F_IMPACT; sc["F_GRAB"] = F_GRAB

A = bpy.data.objects["Teen"]
bpy.context.view_layer.objects.active = A
FR = make_human_ctrl(A)
H = Human(FR)
ROOT_HEAD = FR.BN["root"].head_local.copy()
SH = {s: FR.BN["upperarm01." + s].head_local.copy() for s in "LR"}
DESK_Z = 0.75
CHAIR_Y = 2.93
CHAIR = bpy.data.objects["Chair"]; CHAIR.location.y = CHAIR_Y - 0.02

# ------------------------------------------------------------------ hands
def hand_basis(s, d, n):
    d = d.normalized(); n = (n - d * n.dot(d)).normalized()
    a = d.cross(n) if s == "R" else n.cross(d)
    return Matrix((d, a, n)).transposed()
REST_HAND = {}
for s in "LR":
    wv = FR.BN["wrist." + s].head_local
    d = FR.BN["finger3-1." + s].head_local - wv
    a = FR.BN["finger2-1." + s].head_local - FR.BN["finger5-1." + s].head_local
    n = d.cross(a) if s == "L" else a.cross(d)
    REST_HAND[s] = hand_basis(s, d, n)
def hand_matrix(s, W, d, n):
    Rm = hand_basis(s, d, n) @ REST_HAND[s].transposed()
    wr = FR.BN["wrist." + s].head_local
    return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ FR.rest("IK_hand." + s)
def key_hand(s, f, W, d, n, pole):
    FR.key_world("IK_hand." + s, f, hand_matrix(s, W, d, n))
    pb = FR.PB["Pole_elbow." + s]; nm = "Pole_elbow." + s
    pb.location = FR.rest(nm).to_3x3().inverted() @ (pole - FR.BN[nm].head_local)
    pb.keyframe_insert("location", frame=f, group=nm)
JW = (0.8, 1.1, 0.8)
def key_fingers(s, f, curl, thumb=18, spread=0.0):
    d, a_, n = (REST_HAND[s].col[i].copy() for i in range(3)); sign = 1 if s == "R" else -1
    for k in range(2, 6):
        c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
        for j in range(1, 4):
            b = "finger%d-%d.%s" % (k, j, s)
            sp = Matrix.Rotation(R_(spread * (k - 3.5) * sign * (1 if j == 1 else 0)), 3, n)
            FR.key_q(b, f, FR.local_q(b, sp @ Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a_)))
    for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
        b = "finger1-%d.%s" % (j, s)
        FR.key_q(b, f, FR.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a_) @ Matrix.Rotation(R_(22 * sign), 3, d)))

# ------------------------------------------------------------------ body (FK spine/head, IK feet)
SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
YAW0 = 180.0     # faces +Y (MPFB rest faces -Y)
def key_body(f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), jaw=0.0):
    Rw = Matrix.Rotation(R_(YAW0 + yaw), 3, 'Z') @ Matrix.Rotation(R_(pitch), 3, 'X') @ Matrix.Rotation(R_(roll), 3, 'Y')
    M = Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-ROOT_HEAD) @ FR.rest("root")
    FR.key_world("root", f, M)
    fl, sd, tw = spine
    for n_, w in SPINE_W.items():
        FR.key_rot(n_, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
    hp, ht, hr = head
    for n_, w in HEAD_W.items():
        FR.key_rot(n_, f, [("X", hp * w), ("Y", hr * w), ("Z", ht * w)])
    FR.key_rot("jaw", f, [("X", jaw)])
def key_feet(f, dy=0.0, lift=(0.0, 0.0), heel=(0.0, 0.0)):
    for i, s in enumerate("LR"):
        sx = -1 if s == "L" else 1          # facing +Y: his left is -X
        xy = Vector((sx * 0.13, CHAIR_Y + 0.42 + dy + (0.03 if s == "R" else -0.02)))
        H.key_foot(s, f, xy, YAW0 + sx * 8, lift=lift[i] + 0.016, pitch=heel[i])
        # knee pole in front of the knee
        pole = Vector((xy.x + sx * 0.05, xy.y + 0.7, 0.6))
        pb = FR.PB["Pole_knee." + s]; n_ = "Pole_knee." + s
        pb.location = FR.rest(n_).to_3x3().inverted() @ (pole - FR.BN[n_].head_local)
        pb.keyframe_insert("location", frame=f, group=n_)

SEAT_Z = ROOT_HEAD.z * 0.0 + 0.62
BASE = Vector((0.0, CHAIR_Y, SEAT_Z))
KB = Vector((-0.08, 3.43, DESK_Z)); MOUSE0 = Vector((0.42, 3.42, DESK_Z))
def kb_hand(f, dx=0.0, dy=0.0, lift=0.0):
    W = Vector((-0.16 + dx, 3.29 + dy, DESK_Z + 0.100 + lift))
    key_hand("L", f, W, Vector((0.25, 1.0, -0.18)), Vector((0.0, 0.0, -1.0)), W + Vector((-0.45, -0.25, -0.15)))
def mouse_hand(f, p, lift=0.0):
    W = Vector((p.x - 0.01, p.y - 0.09, DESK_Z + 0.086 + lift))
    key_hand("R", f, W, Vector((-0.05, 1.0, -0.12)), Vector((0.0, 0.0, -1.0)), W + Vector((0.45, -0.25, -0.15)))

if POSETEST:
    key_body(1, BASE, pitch=14, spine=(10, 0, 0), head=(-10, 0, 0))
    key_feet(1)
    kb_hand(1); mouse_hand(1, MOUSE0)
    key_fingers("L", 1, (28, 24, 22, 26), 14); key_fingers("R", 1, (18, 20, 30, 34), 10)
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ------------------------------------------------------------------ body tracks (frame: values), keyed every 3 frames
def track(keys, interp=pchip):
    if isinstance(keys[0][1], (tuple, list)):
        n = len(keys[0][1]); fs_ = [interp([(f, v[i]) for f, v in keys]) for i in range(n)]
        return lambda x: tuple(fn(x) for fn in fs_)
    return interp(keys)
T_ROOT = track([(1, (0, 0, 0, 14, 0)), (240, (0, 0.01, 0, 16, 0)), (355, (0.01, 0.02, -0.005, 18, 1)), (460, (-0.01, 0.0, 0, 15, -1)),
                (571, (0, 0.02, -0.005, 17, 0)), (700, (0, 0.02, -0.005, 17, 0)), (706, (0.025, 0.02, 0.0, 15, 4)), (722, (0.01, 0.0, 0.0, 11, 1)),
                (760, (0.0, -0.03, 0.012, 5, 0)), (900, (-0.01, -0.035, 0.012, 4, 2)), (1060, (-0.015, -0.03, 0.01, 3, 2)), (1085, (-0.02, -0.04, 0.012, 1, 3)),
                (1165, (-0.01, -0.03, 0.01, 4, 1)), (1222, (0, -0.02, 0.005, 6, 0)), (1262, (0, -0.09, 0.0, -2, 0)), (1315, (0, -0.085, 0.0, 9, 0)),
                (1400, (0, -0.085, 0.0, 5, 0)), (1460, (-0.01, -0.085, 0.0, 4, 2)), (1500, (-0.01, -0.085, 0.0, 4, 2))])
T_SPINE = track([(1, (10, 0, 0)), (300, (12, 0, -3)), (420, (8, 2, 4)), (571, (12, 0, 0)), (700, (12, 0, 0)), (708, (6, -8, 6)), (730, (2, -3, 2)),
                 (760, (-4, 0, -6)), (900, (-2, 2, -10)), (1060, (-3, 0, -8)), (1090, (-2, 3, 12)), (1165, (-3, 0, 6)), (1222, (0, 0, 0)),
                 (1262, (-6, 0, 0)), (1315, (8, 0, 0)), (1400, (4, 0, 6)), (1460, (3, 2, 18)), (1500, (3, 2, 19))])
T_HEAD = track([(1, (-8, 0, 0)), (120, (-6, 4, 0)), (240, (-10, -2, 0)), (300, (-8, 3, 2)), (360, (-9, -2, 0)), (420, (-7, 5, -2)), (480, (-10, 0, 0)),
                (571, (-9, -3, 0)), (650, (-9, -2, 0)), (700, (-9, -2, 0)), (704, (-6, -12, -12)), (716, (-4, -7, -6)), (740, (-2, 4, 0)),
                (770, (-4, 18, 3)), (840, (0, 25, 0)), (950, (2, 30, 4)), (1060, (0, 33, 0)), (1085, (0, 48, 2)), (1165, (-4, 18, 0)),
                (1205, (2, 2, 0)), (1222, (6, 0, 0)), (1245, (12, 0, 0)), (1272, (24, 0, 0)), (1315, (18, -6, 3)), (1360, (6, 0, 0)),
                (1400, (2, 18, 0)), (1450, (0, 50, 2)), (1500, (0, 52, 0))])
T_JAW = track([(1, 0), (700, 0), (708, 8), (760, 6), (900, 4), (1085, 10), (1165, 5), (1290, 9), (1330, 15), (1388, 14), (1394, 3), (1402, 3), (1412, 12), (1450, 12), (1500, 11)])
def breathe(f, amp=1.0, per=150):
    return amp * math.sin(2 * math.pi * f / per)
FRAMES = list(range(1, 1501, 3)) + [1500]
for f in FRAMES:
    dx, dy, dz, pt, rl = T_ROOT(f)
    sp = T_SPINE(f); hd = T_HEAD(f)
    br = breathe(f, 1.2 if f > 760 else 0.6, 110 if f > 760 else 160)
    key_body(f, BASE + Vector((dx, dy, dz)), pitch=pt, roll=rl, spine=(sp[0] + br, sp[1], sp[2]), head=hd, jaw=T_JAW(f))
# ------------------------------------------------------------------ face: shock (lids wide, brows up, jaw), blinks, eye darts, swallow
def key_loc_local(n, f, d_world_rest):
    pb = FR.PB[n]; pb.location = FR.rest(n).to_3x3().inverted() @ d_world_rest
    pb.keyframe_insert("location", frame=f, group=n)
T_SHOCK = track([(1, 0.0), (700, 0.0), (708, 0.8), (760, 0.85), (1000, 0.6), (1080, 0.6), (1088, 1.0), (1165, 0.75),
                 (1240, 0.8), (1300, 0.85), (1330, 1.0), (1440, 1.0), (1500, 0.9)])
BLINKS = [(400, 8), (590, 8), (1120, 7), (1362, 14), (1470, 9)]
def blink(f):
    v = 0.0
    for b0, ln in BLINKS:
        if b0 <= f <= b0 + ln: v = max(v, math.sin(math.pi * (f - b0) / ln))
    return v
T_EYE = track([(1, (0, 0)), (300, (4, -2)), (420, (-5, -3)), (571, (3, -2)), (700, (0, -2)), (712, (-8, 4)), (780, (14, 0)),
               (1085, (24, 2)), (1140, (8, 0)), (1240, (0, -14)), (1320, (0, -10)), (1400, (22, 2)), (1450, (12, 2)), (1500, (6, 2))])
for f in FRAMES:
    sh = T_SHOCK(f); bl = blink(f); ey, ep = T_EYE(f)
    for s in "LR":
        FR.key_rot("orbicularis03." + s, f, [("X", -16 * sh * (1 - bl) + 34 * bl)])
        FR.key_rot("orbicularis04." + s, f, [("X", 8 * sh * (1 - bl) - 6 * bl)])
        FR.key_rot("eye." + s, f, [("X", -ep), ("Z", ey)])
        key_loc_local("oculi01." + s, f, Vector((0, 0, 0.007 * sh)))
        key_loc_local("oculi02." + s, f, Vector((0, 0, 0.005 * sh)))
        FR.key_rot("risorius02." + s, f, [("X", 6 * sh)])      # mouth corners pulled down a touch
# chair follows the root (rolls back when he rips the headset off), swivels a touch
for f in FRAMES:
    dx, dy, dz, pt, rl = T_ROOT(f)
    CHAIR.location = (dx * 0.8, CHAIR_Y - 0.02 + dy, 0); CHAIR.rotation_euler = (0, 0, R_(180 + rl * 0.6))
    CHAIR.keyframe_insert("location", frame=f); CHAIR.keyframe_insert("rotation_euler", frame=f)
# feet planted (one heel-lift fidget early on, a flinch at impact, push back at the rip)
FOOT_F = [1, 200, 230, 260, 700, 712, 740, 1222, 1240, 1262, 1500]
for f in FOOT_F:
    lift = (0.03, 0.0) if f == 230 else ((0.0, 0.025) if f == 712 else (0.0, 0.0))
    key_feet(f, dy=0.0, lift=lift)

# ------------------------------------------------------------------ gaming hands (left: WASD, right: mouse)
random.seed(4)
MOUSE = bpy.data.objects["Mouse"]
mk = [(1, Vector((0, 0, 0)))]
f = 1
while f < 690:
    f += random.choice((18, 24, 30, 36))
    mk.append((min(f, 690), Vector((random.uniform(-0.035, 0.035), random.uniform(-0.02, 0.02), 0))))
mk.append((700, mk[-1][1])); mk.append((1500, mk[-1][1]))
M_PATH = catmull(mk)
LK = [(1, (0, 0, 0))]
f = 1
while f < 690:
    f += random.choice((24, 30, 40)); LK.append((min(f, 690), (random.uniform(-0.018, 0.018), random.uniform(-0.01, 0.01), 0)))
L_PATH = track(LK, catmull)
def tap(f, period, phase, width=5):
    x = (f + phase) % period
    return math.exp(-((x - period / 2) / width) ** 2)
F_STARTLE0, F_STARTLE1 = 701, 745
for f in range(1, F_STARTLE0 + 1, 2):
    dx, dy, _ = L_PATH(f); kb_hand(f, dx, dy, lift=0.006 * tap(f, 14, 0, 3))
    mp = MOUSE0 + M_PATH(f); mouse_hand(f, mp)
    MOUSE.location = Vector((mp.x, mp.y, DESK_Z + 0.004)); MOUSE.rotation_euler = (0, 0, R_(180 + 300 * M_PATH(f).x))
    MOUSE.keyframe_insert("location", frame=f); MOUSE.keyframe_insert("rotation_euler", frame=f)
    cL = [28 + 16 * tap(f, 22, 0), 24 + 16 * tap(f, 17, 6), 22 + 14 * tap(f, 26, 11), 26 + 6 * tap(f, 40, 3)]
    key_fingers("L", f, cL, 14)
    clk = 12 * tap(f, 33, 9, 3)
    key_fingers("R", f, [12 + clk, 14 + 4 * tap(f, 70, 20, 4), 24, 28], 10)
# startle: both hands jerk up and back off the desk, then hover, trembling, until he reaches for the headset
def hover(s, f, k):
    tr = Vector((0.003 * math.sin(f * 0.9 + k), 0.002 * math.sin(f * 1.3 + 2 * k), 0.003 * math.sin(f * 1.1 + 3 * k)))
    return tr
L_UP = Vector((-0.20, 3.20, DESK_Z + 0.13)); R_UP = Vector((0.30, 3.20, DESK_Z + 0.12))
for f in range(F_STARTLE0 + 2, 1166, 3):
    u = smooth((f - F_STARTLE0) / (F_STARTLE1 - F_STARTLE0))
    l0 = Vector((-0.16, 3.29, DESK_Z + 0.100)); r0 = MOUSE0 + M_PATH(700) + Vector((-0.01, -0.09, 0.086))
    WL = l0.lerp(L_UP, u) + hover("L", f, 0) * u + Vector((0, 0, 0.02 * math.sin(math.pi * u)))
    WR = r0.lerp(R_UP, u) + hover("R", f, 1) * u + Vector((0, 0, 0.02 * math.sin(math.pi * u)))
    if f > 1080:   # flinch at the wall thud
        k = smooth((f - 1080) / 12) * (1 - smooth((f - 1100) / 40)); WL += Vector((0, -0.03, 0.03)) * k; WR += Vector((0, -0.03, 0.03)) * k
    dL = Vector((0.25, 1.0, -0.25)).lerp(Vector((0.3, 0.8, 0.4)), u); dR = Vector((-0.05, 1.0, -0.3)).lerp(Vector((-0.3, 0.8, 0.4)), u)
    key_hand("L", f, WL, dL, Vector((0, 0, -1)).lerp(Vector((0.5, 0.3, -0.6)), u), WL + Vector((-0.45, -0.25, -0.2)))
    key_hand("R", f, WR, dR, Vector((0, 0, -1)).lerp(Vector((-0.5, 0.3, -0.6)), u), WR + Vector((0.45, -0.25, -0.2)))
    sp = 10 * u
    key_fingers("L", f, [28 - 18 * u] * 4, 14, spread=sp); key_fingers("R", f, [24 - 14 * u] * 4, 12, spread=sp)
MOUSE.keyframe_insert("location", frame=701); MOUSE.keyframe_insert("rotation_euler", frame=701)

# ------------------------------------------------------------------ headset (built to the head, Child Of head bone)
exec(open(os.path.join(HERE, "03a_headset.py")).read())
HEAD_REST_W = (A.matrix_world @ FR.BN["head"].matrix_local)
def head_delta(f):
    ev(f); return (A.matrix_world @ FR.PB["head"].matrix) @ HEAD_REST_W.inverted()
# grip points (rest coords): palm centre on each cup's outer face, fingers up toward the band
CUP_FACE = {"L": Vector((XC1, 0, 0)) + HEAD_C_REST, "R": Vector((-XC1, 0, 0)) + HEAD_C_REST}
OUTV = {"L": Vector((1, 0, 0)), "R": Vector((-1, 0, 0))}
def grip_world(s, D, close=1.0):
    """wrist target, finger dir, palm normal for hand s holding its cup, given a headset world transform D (rest->world)"""
    R3 = D.to_3x3().normalized()
    face = D @ CUP_FACE[s]; out = (R3 @ OUTV[s]).normalized()
    up = (R3 @ Vector((0, 0.25, 1))).normalized()
    W = face + out * (0.043 + 0.015 * (1 - close)) - up * 0.062
    return W, up, -out
# his LEFT is rest +X: the L hand holds the left (hit) cup
F_REACH0 = 1168
Wst = {}
for f in range(F_REACH0, F_GRAB + 1, 2):
    D = head_delta(f); u = smooth((f - F_REACH0) / (F_GRAB - 10 - F_REACH0)); cl = smooth((f - (F_GRAB - 14)) / 14)
    for s, up0, sx in (("L", L_UP, -1), ("R", R_UP, 1)):
        Wg, dg_, ng = grip_world(s, D, cl)
        if s not in Wst: Wst[s] = (up0, Vector((0.3 * sx * -1, 0.8, 0.4)), Vector((0.5 * -sx, 0.3, -0.6)))
        W0, d0, n0 = Wst[s]
        arc = Vector((0, -0.04, 0.05)) * math.sin(math.pi * u)
        W = W0.lerp(Wg, u) + arc; d = d0.lerp(dg_, u); n = n0.lerp(ng, u)
        key_hand(s, f, W, d, n, W + Vector((sx * 0.45, -0.1, -0.35)))
        key_fingers(s, f, [10 + 38 * cl] * 4, 12 + 30 * cl, spread=8 * (1 - cl))
# carrier: starts exactly on the head transform at F_GRAB, then lifts, comes down in front of him and turns in his hands
D0 = head_delta(F_GRAB)
C0 = D0 @ HEAD_C_REST
CP = track([(F_GRAB, tuple(C0)), (F_GRAB + 22, tuple(C0 + Vector((0, 0.07, 0.13)))), (F_GRAB + 50, (0.0, 3.36, 1.02)),
            (1300, (0.02, 3.38, 0.93)), (1340, (0.01, 3.37, 0.90)), (1400, (0.0, 3.33, 0.90)), (1450, (-0.02, 3.29, 0.90)), (1500, (-0.02, 3.28, 0.90))], catmull)
CR = track([(F_GRAB, (0, 0, 0)), (F_GRAB + 22, (-18, 0, 0)), (F_GRAB + 50, (30, 0, 8)), (1300, (45, 0, 20)), (1340, (58, 0, -12)),
            (1400, (40, 0, 12)), (1450, (40, 0, 8)), (1500, (38, 0, 8))], catmull)
def carrier_M(f):
    rx, ry, rz = CR(f); c = Vector(CP(f))
    Rw = Matrix.Rotation(R_(rz), 4, 'Z') @ Matrix.Rotation(R_(rx), 4, 'X') @ Matrix.Rotation(R_(ry), 4, 'Y')
    return Matrix.Translation(c) @ Rw @ Matrix.Translation(-C0) @ D0
CARRIER.rotation_mode = 'QUATERNION'; _q_prev = None
def key_carrier(f, M):
    global _q_prev
    loc, q, _ = M.decompose()
    if _q_prev is not None and q.dot(_q_prev) < 0: q = -q
    _q_prev = q; CARRIER.location = loc; CARRIER.rotation_quaternion = q
    CARRIER.keyframe_insert("location", frame=f); CARRIER.keyframe_insert("rotation_quaternion", frame=f)
key_carrier(F_GRAB - 1, carrier_M(F_GRAB))
for f in list(range(F_GRAB, 1501, 2)) + [1500]:
    key_carrier(f, carrier_M(f))
    # carrier world basis is (rest->world) for the headset: hands hold the cups
    D = carrier_M(f)
    w = smooth((f - (F_GRAB + 34)) / 26)          # outer-face grip while ripping it off -> cradle under the cups
    for s, sx in (("L", -1), ("R", 1)):
        W, d, n = grip_world(s, D, 1.0)
        cc = D @ (CUP_FACE[s] - OUTV[s] * 0.02)
        Wc = cc - Vector((0, 0, 1)) * (R_OUT + 0.045) + Vector((sx * 0.012, -0.07, 0))
        dc = Vector((-sx * 0.25, 1.0, 0.15)); nc = Vector((0, 0, 1))
        W = W.lerp(Wc, w); d = d.lerp(dc, w); n = n.lerp(nc, w)
        key_hand(s, f, W, d, n, W + Vector((sx * 0.45, -0.25 - 0.1 * w, -0.30)))
        key_fingers(s, f, [48 - 34 * w + 3 * math.sin(f * 0.2)] * 4, 42 - 30 * w)
# band bends visibly once off the head (shape key), and the cup crack stays
for o in (HS_BAND_PAD, HS_BAND_STEEL, HS_BAND_TOP):
    kbent = o.data.shape_keys.key_blocks["bent"]
    for f, v in ((1, 0.0), (F_IMPACT, 0.0), (F_IMPACT + 8, 0.7), (F_IMPACT + 20, 0.55)):
        kbent.value = v; kbent.keyframe_insert("value", frame=f)
sc["HEAD_C_REST"] = tuple(HEAD_C_REST); sc["XC1"] = XC1; sc["R_OUT"] = R_OUT

exec(open(os.path.join(HERE, "03b_effects.py")).read())
exec(open(os.path.join(HERE, "03c_camera.py")).read())
import json
json.dump([{"beat": k, "frame": BF[k], "first_words": w} for k, w in zip(range(1, 11), [
    "A bullet was fired toward the house", "smashed through the window", "headed straight for his head",
    "But he was gaming at his desk, wearing a headset", "And instead of piercing his skull", "the bullet hit the headset first",
    "The thick padding and the metal frame inside", "deflected the bullet, sending it safely away",
    "Shocked, he pulled off the broken headset", "and realized it had just saved his life"])],
    open(os.path.join(ROOT, "beats.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
