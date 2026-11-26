"""DrunkTrain v008 stage B: the man's acting, the worker, the ONE train, the bottle, the ONE camera (no cuts), the two
explainer flashes, the VO. blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (DrunkTrain v007 recording) from the start; beat frames = 1 + round(word start s x 60):
  1 'He was so drunk' / 81 'he passed out on the train tracks' / 199 'with his head right on the rail' / 343 'Seconds later,
  a cargo train came roaring toward him' / 537 'It hit him in the head' / 623 'spun him around' / 672 'and dragged him under
  the train' / 793 'When it screeched to a stop' / 889 'everyone was sure he was dead' / 1015 'But then, he stood up' /
  1136 'Being that drunk had left his whole body completely loose' / 1349 'So, instead of fighting the impact, he moved with it'
  / 1549 'He walked away with just a few cuts on his hand' (VO ends 28.1 s, END 1735).
Staging (contact-safe): he lies ACROSS the track outside the rails with only his head on the rail; the train's impact is
hidden behind the locomotive passing the camera; afterwards he lies LENGTHWISE between the rails, under the open part of the
first container wagon, log-rolls while being dragged, the train stops, he rolls out on the -X side, sits up and stands."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(16)
END = 1735
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
MR, MBD, MCL = O["Man"], O["Man.body"], O["Man.clothes"]
WR, WBD, WCL = O["Worker"], O["Worker.body"], O["Worker.clothes"]
TRAIN, BOT = O["Train"], O["Bottle"]
RX, RT, SLEEPER_TOP = 0.80, 0.22, 0.06
EX = Vector((400.0, 0.0, 0.0))
FL1, FL2 = 1186, 1513            # the flash frames (scene swaps): in to the explainer, back out
def V(*v): return Vector(v)

# ================================================================== rigs
def setup(R):
    C = make_human_ctrl(R); add_hand_limits(R)
    for pb in R.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = R.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    return C, Human(C)
CM, HM = setup(MR)
CW, HW = setup(WR)
RH_M = HM.root_head.copy(); RH_W = HW.root_head.copy()

def key_pole(C, s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = C.PB[n]
    pb.location = C.rest(n).to_3x3().inverted() @ (Vector(target) - C.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)
def Mbody(Hh, pos, R): return Matrix.Translation(pos) @ R.to_4x4() @ Matrix.Translation(-Hh.root_head)
def key_rootM(C, Hh, f, pos, R): C.key_world("root", f, Mbody(Hh, pos, R) @ C.rest("root"))
def key_spine(C, f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items(): C.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
_HS = {}
def head_signs(R):
    if R.name in _HS: return _HS[R.name]
    pb = R.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(R, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(R, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS[R.name] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS[R.name]
def key_head(R, C, f, yaw, pitch, roll=0.0):
    """yaw +: toward his own left; pitch +: chin down (at rest orientation)"""
    sx, sz = head_signs(R)
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        C.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])
def Rx(d): return Matrix.Rotation(math.radians(d), 3, 'X')
def Ry(d): return Matrix.Rotation(math.radians(d), 3, 'Y')
def Rz(d): return Matrix.Rotation(math.radians(d), 3, 'Z')

def key_limbs_rel(C, Hh, f, pos, R, legs_bend=0.03, arms="side", hand_z=None, rig=None, R_legs=None):
    """IK targets keyed relative to the body frame (pos, R): straight-ish legs, arms by the sides (palms down when lying)
    or resting on the thighs ('thighs')."""
    Mb = Mbody(Hh, pos, R); Ml = Mbody(Hh, pos, R_legs if R_legs is not None else R)
    for s, sx in (("L", 1), ("R", -1)):
        n = "IK_foot." + s
        C.key_world(n, f, Ml @ Matrix.Translation((0, -0.01, legs_bend)) @ C.rest(n))
        kn = C.BN["lowerleg01." + s].head_local
        key_pole(C, s, f, Ml @ (kn + V(0.03 * sx, -0.7, 0.05)), kind="knee")
        sh = C.BN["upperarm01." + s].head_local
        if arms == "side":
            wl = V(sx * 0.36, 0.05, Hh.root_head.z - 0.06); d = V(0, 0, -1); nn = V(0, 1, 0)
        else:   # palms resting on the front of the thighs
            wl = V(sx * 0.17, -0.17, Hh.root_head.z - 0.14); d = V(0, -0.15, -1); nn = V(0, 1, 0)
        W = Mb @ wl
        if hand_z is not None: W.z = hand_z
        Hh.key_hand(s, f, W, R @ d, R @ nn, pole=Mb @ (sh + V(sx * 0.35, 0.35, -0.30)))
        apply_pose(rig, s, "relaxed", f)

# ---- evaluated surfaces (what renders)
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
def body_pts(objs):
    pts = []
    for o in objs:
        for i, p, n in eval_points(o): pts.append(p)
    return pts

# ================================================================== the train (keyed every frame; ONE object tree)
V0 = 13.0 / 60.0                     # m per frame (47 km/h)
T_HIT, T_BRAKE, T_STOP = 537, 700, 860
def Tfront(f):
    if f <= T_BRAKE: return V0 * (f - T_HIT)
    t = min(f, T_STOP) - T_BRAKE; D = T_STOP - T_BRAKE
    return V0 * (T_BRAKE - T_HIT) + V0 * (t - t * t / (2 * D))
for f in range(1, END + 1):
    TRAIN.location = (0, Tfront(f), 0); TRAIN.keyframe_insert("location", frame=f)
set_interp(TRAIN, 'LINEAR')
log("train stop front y", round(Tfront(END), 2))
# wheel sparks while braking (scale flicker), off otherwise
SPK = [o for o in O if o.name.startswith("TN_SparkSet")]
rr = random.Random(3)
for g in SPK:
    g.scale = (0.001,) * 3; g.keyframe_insert("scale", frame=1); g.keyframe_insert("scale", frame=T_BRAKE)
    for f in range(T_BRAKE + 3, T_STOP - 4, 3):
        k = 0.6 + 0.7 * rr.random(); g.scale = (k, k * (0.7 + 0.6 * rr.random()), k); g.keyframe_insert("scale", frame=f)
    g.scale = (0.001,) * 3; g.keyframe_insert("scale", frame=T_STOP)

# ================================================================== where he is dragged (world y of his pelvis while lying between the rails)
D0, D1 = 640, 670
def y_drag(f):
    if f <= D0: return 0.0
    if f <= D1: return V0 * (f - D0) ** 2 / (2 * (D1 - D0))
    return V0 * (D1 - D0) / 2 + (Tfront(f) - Tfront(D1))
Y_S = y_drag(T_STOP)
log("he stops at y", round(Y_S, 2), "rel to train front", round(Y_S - Tfront(T_STOP), 2))

# ================================================================== MAN: 1) the drunk stagger with the bottle (f1-96)
def path_a(f):
    u = (f - 1) / 99.0
    return V(2.10 + 0.16 * math.sin(2 * math.pi * u * 1.3 + 0.4), 3.30 - 1.30 * u - 0.12 * math.sin(2 * math.pi * u * 0.9), 0)
def yaw_a(f):
    d = path_a(min(f + 2, 100)) - path_a(max(f - 2, 1))
    return math.degrees(math.atan2(d.x, -d.y)) + 6 * math.sin(f / 9.0)
HM.walk(path_a, yaw_a, 1, 100, stride=0.42, duty=0.66, lift=0.05, bob=0.016, crouch=0.04, lean=7.0, step=2)
# drunk sway on top: side lean + twist, a lolling head (overrides the walk's head keys)
for f in range(1, 101, 2):
    key_spine(CM, f, flex=7 + 3 * math.sin(f / 7.0), twist=5 * math.sin(f / 11.0), side=7 * math.sin(f / 13.0 + 0.5))
    key_head(MR, CM, f, yaw=8 * math.sin(f / 17.0) - 6, pitch=6 + 5 * math.sin(f / 10.0), roll=9 * math.sin(f / 12.0 + 1.0))
# arms: the left hand carries the bottle at the hip (body-relative), the right hand swings loose for balance
def hand_rel(C, Hh, Rm_, f, s, wl, d, nn, pole_rel):
    fs(f); Mr = Rm_.matrix_world @ Rm_.pose.bones["root"].matrix @ C.rest("root").inverted()   # = Mbody at f
    Hh.key_hand(s, f, Mr @ wl, Mr.to_3x3() @ d, Mr.to_3x3() @ nn, pole=Mr @ pole_rel)
SH_L = CM.BN["upperarm01.L"].head_local; SH_R = CM.BN["upperarm01.R"].head_local
for f in range(1, 101, 4):
    sw = math.sin(f / 8.0)
    hand_rel(CM, HM, MR, f, "L", V(0.26, -0.16 - 0.02 * sw, RH_M.z + 0.02), V(0.05, -0.35, -1.0), V(-1, 0.1, 0), SH_L + V(0.35, 0.35, -0.30))
    hand_rel(CM, HM, MR, f, "R", V(-0.30 - 0.04 * sw, -0.02 + 0.10 * sw, RH_M.z - 0.02 + 0.04 * abs(sw)), V(-0.15, -0.2 * sw, -1.0), V(1, 0, 0), SH_R + V(-0.35, 0.35, -0.30))
    apply_pose(MR, "R", "relaxed", f)
# the bottle: placed in the left palm at f1 (grip solved by the library), then owned by wrist.L (Child Of, no offset gap)
fs(1)
wr = Wh(MR, "wrist.L"); mid = Wh(MR, "finger3-1.L"); i1 = Wh(MR, "finger2-1.L"); p5 = Wh(MR, "finger5-1.L")
fd = (mid - wr).normalized(); ac = (i1 - p5).normalized(); pn = fd.cross(ac).normalized()
# palm normal: toward the body midline (palm faces the thigh)
if pn.dot(V(-1, 0, 0)) < 0: pn = -pn
cpt = wr.lerp(mid, 0.55) + pn * 0.045
axis = ac                                                     # bottle axis across the palm (index -> little finger)
if axis.z < 0: axis = -axis                                   # neck up/forward
BOT.rotation_mode = 'QUATERNION'
q = V(0, 0, 1).rotation_difference(axis)
BOT.matrix_world = Matrix.Translation(cpt - axis * 0.13) @ q.to_matrix().to_4x4()
key_basis(BOT, 1, BOT.matrix_world.copy())
rep = grip_object(MR, "L", 1, BOT, cpt - pn * 0.0, pn, finger_dir=None)
log("bottle grip", rep)
owner_switch(BOT, 2, MR, "wrist.L", log=log)
apply_pose(MR, "L", "wrap_grip", 1, amount=0.0)   # (fingers keyed by grip_object at f1)
# keep the solved grip fingers for the whole carry
fs(1); grip_rot = {pb.name: pb.rotation_quaternion.copy() for pb in MR.pose.bones if pb.name.startswith("finger") and pb.name.endswith(".L")}
for f in (40, 92):
    for n, qq in grip_rot.items():
        pb = MR.pose.bones[n]; pb.rotation_quaternion = qq; pb.keyframe_insert("rotation_quaternion", frame=f)
# ---- the bottle slips (f94): released, falls, tips over and lies on the ballast (lands exactly ON the surface)
REL = 94
owner_switch(BOT, REL, None, log=log)
fs(REL); P0 = BOT.matrix_world.translation.copy(); q0 = BOT.matrix_world.to_quaternion()
LAND = V(P0.x + 0.12, P0.y - 0.10, 0.0)
rad = 0.039
q_lie = V(0, 0, 1).rotation_difference(V(0.6, 0.8, 0).normalized())    # lying on its side
for f in range(REL + 1, REL + 24):
    u = (f - REL) / 22.0
    if u <= 1.0:
        z = P0.z + (rad - P0.z) * u * u
        pos = P0.lerp(LAND, u); pos.z = z
        qq = q0.slerp(q_lie, min(1.0, u * 1.15))
    else:
        pos = V(LAND.x, LAND.y, rad); qq = q_lie
    # the bottle's origin is its base centre: lying, the base centre sits at the radius height
    key_basis(BOT, f, Matrix.Translation(pos) @ qq.to_matrix().to_4x4())
key_basis(BOT, REL + 30, Matrix.Translation(V(LAND.x, LAND.y, rad)) @ q_lie.to_matrix().to_4x4())
set_interp(BOT, 'LINEAR')
BOT_REST = V(LAND.x, LAND.y, rad)
log("bottle lands", BOT_REST)
for n in grip_rot:
    pb = MR.pose.bones[n]; pb.rotation_quaternion = grip_rot[n]; pb.keyframe_insert("rotation_quaternion", frame=REL)
apply_pose(MR, "L", "open_alarm", REL + 6)
apply_pose(MR, "L", "relaxed", REL + 20)

# ================================================================== MAN: 2) lying ACROSS the track, head on the +X rail (f150-538)
R1 = Rz(90) @ Rx(-90)                  # supine, head toward -X (only the head is raised, onto the rail)
DB = dom_bones(MBD, MR)
HEADV = {i for i, b in DB.items() if b and (b == "head" or b.startswith(("jaw", "eye", "orbic", "oris", "levator", "risor", "temporal", "tongue")))}
NECKV = {i for i, b in DB.items() if b and b.startswith("neck")}
def parts_pts(f):
    fs(f); hp_, bp_ = [], []
    for i, p, n in eval_points(MBD):
        if i in HEADV: hp_.append(p)
        elif i not in NECKV and not (DB[i] or "").startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "clavicle", "shoulder")): bp_.append(p)
    return hp_, bp_
def head_low(f):
    hp_, _ = parts_pts(f); return min(hp_, key=lambda p: p.z)
def R1t(t): return Rz(90) @ Rx(-90 + t)
def settle_pose1(f):
    """pelvis x,z and torso tilt (pivot at the pelvis, legs stay flat) so the body rests ON the ballast and the back of
    the head rests ON the rail top"""
    px, pz, t = 1.60, 0.12, 10.0
    for it in range(16):
        key_rootM(CM, HM, f, V(px, 0.0, pz), R1t(t)); key_limbs_rel(CM, HM, f, V(px, 0, pz), R1t(t), hand_z=0.035, rig=MR, R_legs=R1)
        key_head(MR, CM, f, yaw=22, pitch=18, roll=0)
        hp_, bp_ = parts_pts(f)
        hl = min(hp_, key=lambda p: p.z); bl_ = min(p.z for p in bp_)
        log("settle1", it, round(px, 3), round(pz, 3), round(t, 1), "head low", [round(c, 3) for c in hl], "body low", round(bl_, 3))
        px += (RX - hl.x)
        pz += (0.006 - bl_) * 0.6
        t += (RT + 0.004 - hl.z) * 45.0
        t = max(0.0, min(30.0, t))
    return px, pz, t
key_spine(CM, 150, flex=0, twist=0, side=0)
P1X, P1Z, T1 = settle_pose1(150)
log("head on rail", [round(c, 3) for c in head_low(150)])
POSE1 = (V(P1X, 0, P1Z), R1t(T1))
# the head turns a little toward his left (+Y, the camera side) while asleep; snoring breath
def lie1(f, breath_amp=1.2, head_yaw=22, jaw=0.25):
    key_rootM(CM, HM, f, POSE1[0], POSE1[1]); key_limbs_rel(CM, HM, f, POSE1[0], POSE1[1], hand_z=0.035, rig=MR, R_legs=R1)
for f in range(150, 539, 6):
    lie1(f)
    b = math.sin(2 * math.pi * (f - 150) / 150.0)
    key_spine(CM, f, flex=-3.0 * b, twist=1.5 * b, side=0)
def solve_pitch(f, yaw):
    lo, hi = 0.0, 40.0
    for _ in range(8):
        m = (lo + hi) / 2; key_head(MR, CM, f, yaw=yaw, pitch=m, roll=0)
        if head_low(f).z < RT + 0.003: lo = m
        else: hi = m
    return (lo + hi) / 2
PIT1 = 18.0
log("lying head pitch", round(PIT1, 1))
for f in range(150, 539, 6):
    hy = 22 if f < 470 else 22 - (f - 470) * 0.2
    key_head(MR, CM, f, yaw=hy, pitch=PIT1, roll=0)
# the collapse (f96-150) happens while the camera looks down at the falling bottle: intermediate keys
fs(100)
key_rootM(CM, HM, 112, V(2.05, 1.45, 0.75), Rz(18) @ Rx(35))
key_rootM(CM, HM, 128, V(1.95, 0.70, 0.35), Rz(60) @ Rx(-30))
key_rootM(CM, HM, 140, V(P1X, 0.05, P1Z + 0.05), POSE1[1])
for f, pos_, Rm_ in ((112, V(2.05, 1.45, 0.75), Rz(18) @ Rx(35)), (128, V(1.95, 0.70, 0.35), Rz(60) @ Rx(-30)), (140, V(P1X, 0.05, P1Z + 0.05), POSE1[1])):
    key_limbs_rel(CM, HM, f, pos_, Rm_, hand_z=None if f < 140 else 0.04, rig=MR)
eyes_closed(MR, 112, 560, ramp=10)
for f, jw in ((150, 0.15), (190, 0.30), (230, 0.12), (270, 0.32), (310, 0.12), (350, 0.30), (400, 0.12), (450, 0.28), (500, 0.15), (538, 0.2)):
    key_face(MR, f, smile=0.0, jaw=jw, brow=-0.1, squint=0.0)

# ================================================================== MAN: 3) after the hit: lying LENGTHWISE between the rails, head +Y (f540-1015)
R2 = Rx(-90)
def settle_pose2(f, y):
    pz = 0.14
    for it in range(3):
        key_rootM(CM, HM, f, V(0, y, pz), R2); key_limbs_rel(CM, HM, f, V(0, y, pz), R2, arms="thighs", rig=MR)
        fs(f); lo = min(p.z for p in body_pts([MBD, MCL]))
        pz += (SLEEPER_TOP + 0.006 - lo)
    return pz
key_spine(CM, 539, 0, 0, 0); key_head(MR, CM, 539, 0, 6, 0)
P2Z = settle_pose2(539, 0.0)
# side-lying clearance (90 deg roll) for the roll height profile
key_rootM(CM, HM, 539, V(0, 0, P2Z), R2 @ Rz(90)); key_limbs_rel(CM, HM, 539, V(0, 0, P2Z), R2 @ Rz(90), arms="thighs", rig=MR)
fs(539); lo90 = min(p.z for p in body_pts([MBD, MCL])); EXTRA90 = SLEEPER_TOP + 0.006 - lo90
log("pose2 pelvis z", round(P2Z, 3), "extra at 90 roll", round(EXTRA90, 3))
def roll_deg(f):
    if f < 626: return 0.0
    if f <= 840:
        u = (f - 626) / (840 - 626); return -1080.0 * (1 - (1 - u) ** 2)    # three log rolls, slowing (rolling toward -X side then back is fine)
    return -1080.0
def pose2(f, x=0.0, roll=None, ground=SLEEPER_TOP):
    r = roll_deg(f) if roll is None else roll
    s_ = abs(math.sin(math.radians(r)))
    z = P2Z + (ground - SLEEPER_TOP) + EXTRA90 * s_
    return V(x, y_drag(f), z), R2 @ Rz(r)
for f in list(range(539, 1010, 2)):
    pos_, Rm_ = pose2(f)
    key_rootM(CM, HM, f, pos_, Rm_); key_limbs_rel(CM, HM, f, pos_, Rm_, arms="thighs", rig=MR)
    key_spine(CM, f, flex=0, twist=0, side=0)
    key_head(MR, CM, f, yaw=0, pitch=6, roll=0)
eyes_closed(MR, 560, 1010, ramp=8)
for o_ in [MR] + list(MR.children):
    vis(o_, 1, True); vis(o_, 541, False); vis(o_, 647, True)
for f, jw, br in ((560, 0.1, -0.5), (650, 0.25, -0.7), (760, 0.15, -0.5), (900, 0.05, -0.2), (1010, 0.05, 0.0)):
    key_face(MR, f, smile=-0.2, jaw=jw, brow=br)

# ================================================================== MAN: 4) he rolls out on the -X side, sits up, stands (f1015-1118)
XO = -2.10
def roll_out(f):
    u = smoothstep((f - 1010) / (1056 - 1010)); x = XO * u
    r = -1080.0 + 720.0 * u               # two rolls toward -X (top of the body moves toward -X)
    over_rail = max(0.0, 1 - abs(x + RX) / 0.42) * 0.22      # lifts over the near rail
    ground = SLEEPER_TOP if x > -1.3 else 0.0
    p_, Rm_ = pose2(1015, x=x, roll=r, ground=ground)
    p_.z += over_rail
    return p_, Rm_
for f in range(1010, 1057, 1):
    pos_, Rm_ = roll_out(f)
    key_rootM(CM, HM, f, pos_, Rm_); key_limbs_rel(CM, HM, f, pos_, Rm_, arms="thighs", rig=MR)
    key_head(MR, CM, f, yaw=0, pitch=4, roll=0)
def ground_at(x):
    if abs(abs(x) - RX) < 0.09: return RT
    return SLEEPER_TOP if abs(x) < 1.3 else 0.0
def settle_frames(frames, posR):
    for f in frames:
        pos_, Rm_ = posR(f)
        key_rootM(CM, HM, f, pos_, Rm_); key_limbs_rel(CM, HM, f, pos_, Rm_, arms="thighs", rig=MR)
        fs(f); pts = [p for p in body_pts([MBD, MCL])]
        d = max(ground_at(p.x) + 0.004 - p.z for p in pts)        # deepest penetration below the local surface
        pos_ = pos_ + V(0, 0, d)
        key_rootM(CM, HM, f, pos_, Rm_); key_limbs_rel(CM, HM, f, pos_, Rm_, arms="thighs", rig=MR)
settle_frames(range(1010, 1057), roll_out)
settle_frames(range(626, 842, 2), pose2)
PS = roll_out(1056)[0]                    # supine on the ballast, head +Y, feet -Y
log("rolled out to", PS)
# sit up: pelvis pivots, legs stay on the ground (feet IK on the ballast), hands plant behind the hips
def feet_on_ground(f, x, yf, R_feet, spread=0.12):
    for s, sx in (("L", 1), ("R", -1)):
        a_ = CM.BN["foot." + s].head_local
        tgt = V(x + sx * spread, yf, 0.075)
        CM.key_world("IK_foot." + s, f, Matrix.Translation(tgt) @ R_feet.to_4x4() @ Matrix.Translation(-a_) @ CM.rest("IK_foot." + s))
key_rootM(CM, HM, 1059, PS + V(0, 0, 0.0), Rx(-90)); key_limbs_rel(CM, HM, 1059, PS, Rx(-90), arms="side", hand_z=0.035, rig=MR)
for f, flex, dz, hy, kneey in ((1067, -60, 0.00, 0.10, 0.0), (1076, -20, 0.00, 0.20, 0.0), (1082, -12, 0.0, 0.25, 0.0)):
    key_rootM(CM, HM, f, PS + V(0, 0, dz), Rx(flex))
    feet_on_ground(f, PS.x, PS.y - 0.92 + kneey, Rx(-90))
    for s, sx in (("L", 1), ("R", -1)):
        kn = CM.BN["lowerleg01." + s].head_local
        key_pole(CM, s, f, PS + V(sx * 0.15, -0.5, 0.8), kind="knee")
        W = PS + V(sx * 0.30, hy, 0.04)
        HM.key_hand(s, f, W, V(0, -0.1, -1), V(0, 0, -1), pole=PS + V(sx * 0.6, 0.4, 0.4))
        apply_pose(MR, s, "flat_palm", f)
    key_spine(CM, f, flex=10 if f > 1067 else 0)
    key_head(MR, CM, f, yaw=0, pitch=8, roll=0)
# knees up, lean forward over the feet, push up, stand (feet flat from 1088)
for f, py, pz, flex, fy, rot_f in ((1090, -0.18, 0.20, 30, -0.45, 0), (1100, -0.30, 0.55, 38, -0.40, 0), (1110, -0.36, 0.92, 15, -0.40, 0),
                                   (1118, -0.38, RH_M.z - 0.02, 4, -0.40, 0)):
    key_rootM(CM, HM, f, V(PS.x, PS.y + py, pz), Rx(flex))
    feet_on_ground(f, PS.x, PS.y + fy, Matrix.Identity(3), spread=0.13)
    for s, sx in (("L", 1), ("R", -1)):
        key_pole(CM, s, f, V(PS.x + sx * 0.1, PS.y + fy - 0.7, 0.6), kind="knee")
    key_spine(CM, f, flex=12 if f < 1110 else 4)
for s, sx in (("L", 1), ("R", -1)):
    HM.key_hand(s, 1090, PS + V(sx * 0.32, -0.05, 0.04), V(0, -0.2, -1), V(0, 0, -1), pole=PS + V(sx * 0.6, 0.4, 0.5))
    apply_pose(MR, s, "flat_palm", 1090)
# feet planted flat at standing; IK feet need the rest orientation (Identity), with ankle height
for f in (1090, 1100, 1110, 1118):
    for s, sx in (("L", 1), ("R", -1)):
        a_ = CM.BN["foot." + s].head_local
        CM.key_world("IK_foot." + s, f, Matrix.Translation(V(PS.x + sx * 0.13, PS.y - 0.40, a_.z)) @ Matrix.Translation(-a_) @ CM.rest("IK_foot." + s))
STAND = V(PS.x, PS.y - 0.38, RH_M.z - 0.02)
# ---- standing, dazed and loose (f1118-1500): sway, arms hanging loose, head lolling, blinks
def stand_man(f, pos, yaw=0.0, flex=3.0, side=0.0):
    key_rootM(CM, HM, f, pos, Rz(yaw) @ Rx(flex) @ Ry(side))
def hang_rel(f, sw=0.0):
    for s, sx in (("L", 1), ("R", -1)):
        hand_rel(CM, HM, MR, f, s, V(sx * (0.28 + 0.05 * sw), -0.06 + 0.14 * sx * sw, RH_M.z - 0.07 + 0.03 * sw), V(sx * 0.2, -0.3 * sx * sw, -1.0), V(-sx, 0, 0),
                 CM.BN["upperarm01." + s].head_local + V(sx * 0.35, 0.35, -0.30))
        apply_pose(MR, s, "relaxed", f)
for f in range(1100, 1501, 6):
    if f >= 1118:
        sw = math.sin((f - 1118) / 14.0)
        stand_man(f, STAND + V(0.03 * sw, 0, -0.005 * abs(sw)), yaw=4 * sw, flex=3 + 2 * math.sin(f / 23.0), side=4 * sw)
        key_spine(CM, f, flex=4, twist=-3 * sw, side=-3 * sw)
    if f >= 1112: hang_rel(f, math.sin((f - 1118) / 14.0 + 0.6) if f >= 1118 else 0)
for f in range(1100, 1501, 6):
    key_head(MR, CM, f, yaw=10 * math.sin(f / 31.0) - 4, pitch=-2 + 4 * math.sin(f / 19.0), roll=6 * math.sin(f / 15.0))
for f, sm, br, jw, sq in ((1048, -0.1, 0.2, 0.05, 0.0), (1080, -0.2, 0.6, 0.15, 0.2), (1118, 0.0, 0.5, 0.12, 0.3), (1180, 0.1, 0.4, 0.10, 0.35),
                          (1500, 0.1, 0.4, 0.10, 0.35)):
    key_face(MR, f, smile=sm, brow=br, jaw=jw, squint=sq)

# ================================================================== MAN: 5) walks away along the train (f1500-1735), looks at his palm, grins
def path_e(f):
    u = (f - 1500) / (END - 1500)
    return V(STAND.x - 0.55 * smoothstep(u * 1.6) + 0.06 * math.sin(u * 9.0), STAND.y - 3.6 * u, 0)
def yaw_e(f):
    d = path_e(min(f + 3, END)) - path_e(max(f - 3, 1500))
    return math.degrees(math.atan2(d.x, -d.y)) + 4 * math.sin(f / 13.0)
HM.walk(path_e, yaw_e, 1500, END, stride=0.40, duty=0.66, lift=0.05, bob=0.014, crouch=0.035, lean=5.0, step=2)
for f in range(1500, END + 1, 2):
    key_spine(CM, f, flex=5, twist=3 * math.sin(f / 11.0), side=4 * math.sin(f / 15.0))
PALM_UP0, PALM_UP1 = 1592, 1712
for f in range(1500, END + 1, 4):
    sw = math.sin(f / 9.0)
    # left hand hangs loose
    hand_rel(CM, HM, MR, f, "L", V(0.27, -0.04 + 0.05 * sw, RH_M.z - 0.10), V(0.1, -0.2, -1.0), V(-1, 0, 0), SH_L + V(0.35, 0.35, -0.30))
    apply_pose(MR, "L", "relaxed", f)
    # right hand: hangs, then rises palm up in front of the chest (he looks at the cuts), then lowers
    u = smoothstep((f - PALM_UP0) / 24.0) * (1 - smoothstep((f - (PALM_UP1 - 18)) / 18.0))
    hang = V(-0.27, -0.04 - 0.05 * sw, RH_M.z - 0.10)
    look = V(-0.12, -0.46, RH_M.z + 0.30)
    W = hang.lerp(look, u)
    d = V(-0.1, -0.2, -1.0).lerp(V(0.35, -0.75, 0.1), u)
    nn = V(1, 0, 0).lerp(V(0.10, 0.35, 1.0), u)                 # the palm turns up toward his face (and the camera above)
    hand_rel(CM, HM, MR, f, "R", W, d, nn, SH_R + V(-0.35, 0.30, -0.35))
    apply_pose(MR, "R", "relaxed" if u < 0.5 else "cup_hold", f)
for f in range(1500, END + 1, 4):
    u = smoothstep((f - PALM_UP0) / 24.0) * (1 - smoothstep((f - (PALM_UP1 - 18)) / 18.0))
    key_head(MR, CM, f, yaw=-14 * u + 5 * math.sin(f / 23.0), pitch=-2 + 26 * u, roll=4 * math.sin(f / 17.0))
for f, sm, br, jw, sq in ((1500, 0.1, 0.4, 0.08, 0.3), (1600, 0.0, 0.7, 0.10, 0.1), (1660, 0.1, 0.5, 0.05, 0.1), (1680, 0.9, 0.35, 0.08, 0.25),
                          (END, 1.0, 0.35, 0.08, 0.25)):
    key_face(MR, f, smile=sm, brow=br, jaw=jw, squint=sq)
blinks(MR, [20, 70, 1128, 1175, 1236, 1300, 1380, 1460, 1530, 1585, 1650, 1718])
saccades(CM, 1, 100, every=30, amp=(2, 3), seed=4)
saccades(CM, 1120, END, every=34, amp=(1.5, 2.5), seed=5)

# ================================================================== WORKER: runs in along the path, shocked, steps back, watches
WK_STOP = V(-2.65, Y_S + 1.50, 0)          # ahead of the man (+Y side), facing him: his face toward the camera
def path_w(f):
    u = min(1.0, max(0.0, (f - 790) / (925 - 790)))
    u2 = 1 - (1 - u) ** 2                  # decelerates into the stop
    return V(-3.85 + 1.20 * u2, Y_S + 17.0 - (17.0 - 1.50) * u2, 0)
def yaw_w(f):
    if f < 905: return 0.0                 # running toward -Y
    return 62.0 * smoothstep((f - 905) / 25.0)
HW.walk(path_w, yaw_w, 790, 930, stride=1.25, duty=0.42, lift=0.12, bob=0.035, crouch=0.06, lean=12.0, step=2)
def stand_w(f, pos, yaw, flex=2.0, side=0.0):
    key_rootM(CW, HW, f, V(pos.x, pos.y, RH_W.z - 0.012), Rz(yaw) @ Rx(flex) @ Ry(side))
    for s, sx in (("L", 1), ("R", -1)):
        a_ = CW.BN["foot." + s].head_local
        tgt = pos + Rz(yaw) @ V(sx * 0.13, 0, 0); tgt.z = a_.z
        CW.key_world("IK_foot." + s, f, Matrix.Translation(tgt) @ Rz(yaw).to_4x4() @ Matrix.Translation(-a_) @ CW.rest("IK_foot." + s))
        key_pole(CW, s, f, tgt + Rz(yaw) @ V(sx * 0.05, -0.8, 0.45), kind="knee")
for f in (1, 400, 789):
    stand_w(f, path_w(790), 0.0)
WK2 = V(-3.25, Y_S + 2.30, 0)               # one step back when the man stands up
for f, pos, yaw, fl_ in ((932, WK_STOP, 62, 8), (960, WK_STOP, 64, 18), (990, WK_STOP, 60, 14), (1020, WK_STOP, 62, 16), (1050, WK_STOP, 58, 8),
                         (1072, WK_STOP.lerp(WK2, 0.6), 50, -4), (1085, WK2, 45, -2), (1180, WK2, 40, 0), (1500, WK2, 25, 0), (END, WK2, 15, 0)):
    stand_w(f, pos, yaw, flex=fl_)
for o_ in [WR] + list(WR.children):
    vis(o_, 1, False); vis(o_, 780, True)
SH_WL = CW.BN["upperarm01.L"].head_local; SH_WR = CW.BN["upperarm01.R"].head_local
# arms: run swing (elbows bent), then hands raised open in shock in front of his chest (never touching the face)
for f in range(790, 931, 4):
    ph = math.sin(2 * math.pi * (f - 790) / 26.0)
    for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
        hand_rel(CW, HW, WR, f, s, V(sx * 0.24, -0.18 * sg * ph, RH_W.z + 0.12), V(0, -0.6, 0.6), V(-sx, 0, 0),
                 CW.BN["upperarm01." + s].head_local + V(sx * 0.3, 0.45, -0.3))
        apply_pose(WR, s, "relaxed", f)
# shock: both hands up and open at shoulder height, palms toward the man, a small tremble (never touching the face)
for f in list(range(935, 1110, 8)) + [1118, 1185]:
    lift_ = 0.0 if f >= 1185 else (0.7 if 1040 <= f < 1062 else 1.0)
    tr = 0.02 * math.sin(f * 1.3)
    for s, sx in (("L", 1), ("R", -1)):
        up = V(sx * (0.40 + tr), -0.24, RH_W.z + 0.42 + tr)
        dn = V(sx * 0.27, -0.05, RH_W.z - 0.10)
        W_ = dn.lerp(up, lift_)
        dirn = V(sx * 0.35, -0.15, 1).lerp(V(sx * 0.1, -0.2, -1), 1 - lift_)
        nrm = V(0, -1, 0).lerp(V(-sx, 0, 0), 1 - lift_)
        hand_rel(CW, HW, WR, f, s, W_, dirn, nrm, CW.BN["upperarm01." + s].head_local + V(sx * 0.45, 0.25, -0.35))
        apply_pose(WR, s, "open_alarm" if lift_ > 0 else "relaxed", f)
for f in range(1200, END + 1, 8):
    for s, sx in (("L", 1), ("R", -1)):
        hand_rel(CW, HW, WR, f, s, V(sx * 0.27, -0.05 + 0.02 * math.sin(f / 20.0), RH_W.z - 0.10), V(sx * 0.1, -0.2, -1), V(-sx, 0, 0),
                 CW.BN["upperarm01." + s].head_local + V(sx * 0.35, 0.35, -0.30))
        apply_pose(WR, s, "relaxed", f)
for f in range(790, END + 1, 6):
    if f < 935: key_head(WR, CW, f, yaw=0, pitch=-4, roll=0)
    elif f < 1050: key_head(WR, CW, f, yaw=4 * math.sin(f / 9.0), pitch=24, roll=3 * math.sin(f / 7.0))
    elif f < 1190: key_head(WR, CW, f, yaw=-6, pitch=8, roll=0)
    else: key_head(WR, CW, f, yaw=6 * math.sin(f / 37.0), pitch=6, roll=0)
    key_spine(CW, f, flex=6 if 935 <= f < 1050 else 2, twist=0, side=0)
for f, sm, br, jw in ((790, 0.0, 0.5, 0.2), (935, -0.3, 1.0, 0.45), (1040, -0.3, 1.0, 0.35), (1070, 0.0, 1.0, 0.6), (1120, 0.1, 0.8, 0.3),
                      (1500, 0.2, 0.5, 0.05), (END, 0.3, 0.4, 0.05)):
    key_face(WR, f, smile=sm, brow=br, jaw=jw)
blinks(WR, [960, 1020, 1090, 1150, 1560, 1640, 1710])

# ================================================================== loose stones hop as the rail vibrates (f420-532)
for i in range(7):
    s = O["TR_Hop%d" % i]; base = s.location.copy(); rr = random.Random(20 + i)
    s.keyframe_insert("location", frame=1); s.keyframe_insert("location", frame=420)
    f = 424 + i * 2
    while f < 532:
        h = 0.006 + 0.025 * ((f - 420) / 112.0) * rr.random()
        s.location = base + V(rr.uniform(-0.004, 0.004), rr.uniform(-0.004, 0.004), h); s.keyframe_insert("location", frame=f)
        s.location = base; s.keyframe_insert("location", frame=f + 3)
        f += 5 + int(rr.random() * 4)
    s.location = base; s.keyframe_insert("location", frame=540)

# ================================================================== EXPLAINER: the loose muscle sways, the force arrow pushes, it flows with it
LAT = O["EX_Lattice"]; KB = LAT.data.shape_keys.key_blocks
def kk(name, f, v): KB[name].value = v; KB[name].keyframe_insert("value", frame=f)
for f in range(1180, 1520, 10):
    s_ = math.sin((f - 1180) / 22.0)
    loose = smoothstep((f - 1186) / 40.0)
    push = smoothstep((f - 1392) / 32.0) * (1 - smoothstep((f - 1460) / 40.0))
    kk("sag", f, 0.55 * loose)
    kk("swayA", f, max(0, s_) * loose * (1 - push))
    kk("swayB", f, max(0, -s_) * loose * (1 - push))
    kk("flow", f, push)
AR = O["EX_Arrow"]
for f, x in ((1180, 3.4), (1360, 3.4), (1390, 0.85), (1424, 0.06), (1460, 0.16), (1500, 3.4)):
    AR.location = EX + V(x, 0, 0); AR.keyframe_insert("location", frame=f)

# ================================================================== camera: ONE camera, PCHIP keys, level horizon
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.dof.use_dof = False; cam_d.clip_start = 0.02; cam_d.clip_end = 400
CAM.rotation_mode = 'QUATERNION'
def face(R, f): fs(f); return (Wh(R, "eye.L") + Wh(R, "eye.R")) / 2
def bone(R, n, f): fs(f); return Wh(R, n)
def look_q(p, a, up=Vector((0, 0, 1))):
    z_ = (p - a).normalized(); y_ = (up - z_ * up.dot(z_)); y_ = y_.normalized() if y_.length > 1e-6 else V(0, 1, 0)
    return Matrix((y_.cross(z_), y_, z_)).transposed().to_quaternion()
K = []      # (frame, pos, target, lens)
def key(f, p, t, l): K.append((f, Vector(p), Vector(t), l))
# 1) the stagger: in front-right of him, weaving with him (face + bottle in frame)
for f in range(1, 96, 8):
    fc = face(MR, f); bt = BOT.matrix_world.translation.copy()
    key(f, fc + V(0.85, -1.15, -0.05), fc.lerp(bt, 0.40) + V(0, 0, -0.03), 30)
# 2) the bottle drops: the camera tilts down and follows it to the ballast (he falls behind the camera)
key(104, BOT_REST + V(0.55, -0.85, 0.85), BOT_REST + V(0, 0.0, 0.25), 32)
key(118, BOT_REST + V(0.42, -0.55, 0.42), BOT_REST + V(-0.02, 0.05, 0.02), 36)
key(126, BOT_REST + V(0.32, -0.45, 0.32), BOT_REST + V(-0.05, 0.02, 0.02), 38)
key(140, BOT_REST + V(0.25, -0.70, 0.48), BOT_REST + V(-0.35, -0.45, 0.06), 32)
# 3) glide low along the ground to his face on the rail (head at x~0.85, his left side faces +Y)
H1 = face(MR, 200)
key(156, V(2.05, 1.10, 0.62), H1 + V(0.3, 0.0, -0.05), 28)
key(199, H1 + V(0.45, 0.95, 0.20), H1 + V(-0.05, -0.25, -0.04), 30)
key(270, H1 + V(0.22, 0.88, 0.28), H1 + V(-0.08, -0.45, -0.04), 32)
# 4) the train comes down the rail behind his head (target pulls along the rail toward -Y; his face stays in frame)
key(343, H1 + V(0.35, 0.95, 0.16), H1 + V(-0.10, -0.90, 0.02), 32)
key(420, H1 + V(0.18, 0.74, 0.20), H1 + V(-0.12, -1.10, 0.04), 33)
# 5) up and over the track to the -X side (the train is still >8 m away), he lies across the rails, the train at frame right
key(448, V(1.15, 1.25, 0.75), V(0.9, -1.2, 0.30), 32)
key(472, V(-0.2, 1.30, 1.70), V(1.0, -0.3, 0.25), 32)
key(496, V(-2.4, -1.6, 1.35), V(1.4, 0.0, 0.25), 36)
key(516, V(-3.1, -2.9, 1.10), V(1.5, 0.0, 0.25), 40)
key(534, V(-3.4, -3.1, 1.10), V(1.4, 0.0, 0.35), 40)
# 6) the locomotive passes (hides the hit), the camera backs off, then drops low to look under the wagon
key(556, V(-4.6, -2.8, 2.40), V(0.0, 1.5, 1.2), 20)
key(590, V(-4.7, -0.8, 3.20), V(0.0, 2.5, 1.9), 20)
key(626, V(-4.4, 0.6, 3.30), V(0.0, 2.0, 1.6), 22)
key(648, V(-4.0, 1.0, 2.80), V(0.0, y_drag(648) + 0.6, 0.9), 24)
key(662, V(-3.0, y_drag(662) + 0.5, 1.20), V(0.0, y_drag(662) + 0.2, 0.3), 23)
# 7) dragged: the camera runs with him, low, looking under the wagon (bogies outside the frame)
for f in range(676, 771, 10):
    y = y_drag(f); key(f, V(-2.2, y + 0.45, 0.42), V(0.0, y + 0.10, 0.15), 22)
# 8) braking: wider so the sparking rear bogie shows at the frame edge, then the stop
for f in range(780, 861, 10):
    y = y_drag(f); u = smoothstep((f - 780) / 50.0)
    key(f, V(-2.2 - 0.8 * u, y + 0.45 + 0.3 * u, 0.42 + 0.15 * u), V(0.0, y - 0.9 * u, 0.18), 22 - 3 * u)
# 9) pull out and up: the stopped wagon (logo container) and the worker running up; his shocked face
key(895, V(-2.3, Y_S - 2.4, 0.80), V(-0.6, Y_S + 0.4, 0.45), 24)
key(930, V(-2.2, Y_S - 2.8, 1.15), V(-1.6, Y_S + 0.7, 0.85), 24)
key(965, V(-2.15, Y_S - 2.9, 1.25), V(-1.7, Y_S + 0.8, 0.95), 25)
key(1000, V(-2.2, Y_S - 2.8, 1.20), V(-1.5, Y_S + 0.6, 0.80), 25)
# 10) he rolls out toward the camera side, sits up and stands (worker in frame left)
key(1020, V(-2.55, Y_S - 2.6, 0.95), V(-0.8, Y_S, 0.35), 26)
key(1048, V(-2.75, Y_S - 2.4, 0.95), V(-1.9, Y_S - 0.2, 0.40), 26)
key(1080, V(-2.70, Y_S - 2.45, 1.10), V(-2.05, Y_S - 0.3, 0.70), 28)
key(1118, V(-2.55, Y_S - 2.35, 1.45), V(-2.08, Y_S - 0.4, 1.35), 30)
# 11) dazed and loose: push in to his loose hanging right arm -> flash into the muscle
key(1150, V(-2.45, Y_S - 2.00, 1.45), V(-2.15, Y_S - 0.4, 1.40), 32)
FA = bone(MR, "lowerarm01.R", 1182); FC = face(MR, 1182)
key(1182, FC.lerp(FA, 0.5) + V(0.10, -1.05, 0.05), FC.lerp(FA, 0.5), 34)
# 12) EXPLAINER (after the flash): orbit and push on the muscle; the arrow comes down at 1398
key(1190, EX + V(0.9, -4.4, 0.45), EX + V(0.0, 0, 0.0), 40)
key(1290, EX + V(-0.6, -4.2, 0.25), EX + V(0.0, 0, 0.0), 42)
key(1380, EX + V(-0.3, -4.6, 0.55), EX + V(0.2, 0, 0.0), 38)
key(1450, EX + V(0.5, -4.3, 0.45), EX + V(-0.1, 0, 0.0), 38)
key(1510, EX + V(0.7, -3.9, 0.30), EX + V(0.0, 0, 0.0), 40)
# 13) after the flash: in front of him as he walks away, face + palm + the logo on his tee
for f in range(1516, END + 1, 12):
    fc = face(MR, f)
    u = smoothstep((f - PALM_UP0) / 30.0) * (1 - smoothstep((f - (PALM_UP1 - 10)) / 20.0))
    key(f, fc + V(-0.55 + 0.15 * u, -1.75 + 0.35 * u, 0.05 + 0.12 * u), fc + V(0.02, 0.0, -0.28 - 0.08 * u), 32 + 4 * u)
key(END, face(MR, END) + V(-0.50, -1.60, 0.05), face(MR, END) + V(0.02, 0, -0.26), 33)
K.sort(key=lambda k: k[0])
# separate PCHIP runs inside each flash so nothing interpolates across the scene swap
def run(keys, f0, f1):
    fx = [pchip([(k[0], k[1][i]) for k in keys]) for i in range(3)]
    ax = [pchip([(k[0], k[2][i]) for k in keys]) for i in range(3)]
    fl = pchip([(k[0], k[3]) for k in keys])
    out = {}
    for f in range(f0, f1 + 1):
        p = V(*[fx[i](f) for i in range(3)]); t = V(*[ax[i](f) for i in range(3)])
        out[f] = (p, look_q(p, t), fl(f))
    return out
CK = {}
CK.update(run([k for k in K if k[0] < FL1], 1, FL1 - 1))
CK.update(run([k for k in K if FL1 <= k[0] < FL2], FL1, FL2 - 1))
CK.update(run([k for k in K if k[0] >= FL2], FL2, END))
prev = None
for f in range(1, END + 1):
    p, q, l_ = CK[f]
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; cam_d.lens = l_
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f); cam_d.keyframe_insert("lens", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# a soft catchlight riding with the camera (eyes never read as black holes)
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 6.0; cl.size = 0.4; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.15, 0.0)
# a warm fill under the wagon while he is there (readable, not black)
uf = bpy.data.lights.new("UnderFill", 'AREA'); uf.energy = 0.0; uf.size = 1.5; uf.color = (1.0, 0.85, 0.65)
ufo = bpy.data.objects.new("UnderFill", uf); sc.collection.objects.link(ufo)
for f in range(560, 1050, 10):
    y = y_drag(min(f, 1015)); ufo.location = (-1.0, y + 0.2, 0.75); ufo.keyframe_insert("location", frame=f)
ufo.rotation_euler = (V(0, 0, 0.2) - V(-1.0, 0.2, 0.75)).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0.0), (600, 0.0), (640, 90.0), (1000, 90.0), (1050, 0.0)):
    uf.energy = e; uf.keyframe_insert("energy", frame=f)

# ================================================================== the two scene-swap flashes (camera-parented sphere, camera rays only)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=32, ring_count=16); FLS = bpy.context.active_object; FLS.name = "SwapFlash"
for p_ in FLS.data.polygons: p_.use_smooth = True
fm = bpy.data.materials.new("M_SwapFlash"); fm.use_nodes = True; nt = fm.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.97, 0.88, 1); em.inputs["Strength"].default_value = 1.6
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); lp = nt.nodes.new("ShaderNodeLightPath")
av = nt.nodes.new("ShaderNodeValue"); av.name = "FlashAlpha"; av.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(lp.outputs["Is Camera Ray"], mul.inputs[0]); nt.links.new(av.outputs[0], mul.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(mul.outputs[0], mx.inputs["Fac"]); nt.links.new(tr.outputs["BSDF"], mx.inputs[1]); nt.links.new(em.outputs["Emission"], mx.inputs[2])
nt.links.new(mx.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
FLS.data.materials.append(fm)
FLS.visible_shadow = False; FLS.visible_diffuse = False; FLS.visible_glossy = False; FLS.visible_transmission = False
for c in list(FLS.users_collection): c.objects.unlink(FLS)
sc.collection.objects.link(FLS)
FLS.parent = CAM; FLS.matrix_parent_inverse = Matrix.Identity(4); FLS.location = (0, 0, 0); FLS.scale = (0.05,) * 3
VA = av.outputs[0]
for f, a_ in ((1, 0.0), (FL1 - 6, 0.0), (FL1 - 1, 1.0), (FL1 + 2, 1.0), (FL1 + 7, 0.0), (FL2 - 6, 0.0), (FL2 - 1, 1.0), (FL2 + 2, 1.0), (FL2 + 7, 0.0), (END, 0.0)):
    VA.default_value = a_; VA.keyframe_insert("default_value", frame=f)
vis(FLS, 1, False); vis(FLS, FL1 - 7, True); vis(FLS, FL1 + 8, False); vis(FLS, FL2 - 7, True); vis(FLS, FL2 + 8, False)

# ================================================================== VO, output
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/DrunkTrain_v008_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
log("quat flips fixed", quat_continuity(MR), quat_continuity(WR))
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
