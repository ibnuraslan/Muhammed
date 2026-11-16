"""B08 BatBite animation: every beat's action at 1x on a master timeline (each block ~30% longer than the expected VO beat,
so Phase 2 can trim/shift blocks to the VO without stretching).
blender -b scene.blend --python 05_anim.py -- anim.blend

Master blocks (frames, 60 fps):
  A    1-300  concert; a fan's bat flies over the crowd and lands by the singer's feet; he notices it
  B  300-620  he lets go of the mic stand, steps, crouches, picks the bat up by the body, rises and looks at it
  C  620-960  brings it to his mouth and bites the head (jaw opens, closes on the bat's head, playful shake)
  D  960-1280 pulls it away fast: shock, a light red trace at the lip corner, stares at the bat
  E 1280-1600 drops it, bends over with hands on the thighs, heavy breaths
  F 1600-2100 hospital: reclined in bed with an oxygen mask; doctor beside the bed with a syringe
"""
import sys, os, math, random
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = Vector
random.seed(8)
D = bpy.data.objects
AUD_Z = -1.3          # audience floor
HX = 60.0             # hospital offset

def ground_z(x, y):   # overrides anim_lib's: stage deck at 0, audience floor in front of the stage, hospital floor 0
    if -6.0 < x < 6.0 and y < -2.6: return AUD_Z
    return 0.0

def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def Ry(d): return Matrix.Rotation(R_(d), 3, 'Y')
def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')

NAMES = ["Singer", "Doctor", "Fan1", "Fan3", "Fan4"]
RIG, HUM = {}, {}
for n in NAMES:
    RIG[n] = make_human_ctrl(D[n]); HUM[n] = Human(RIG[n])
    add_hand_limits(D[n])
    for s in "LR":   # MPFB rest elbow is ~46 deg: open the IK limit so arms can straighten (no A-pose)
        lo = D[n].pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(140)

def rest_head(n, bone): return RIG[n].BN[bone].head_local.copy()
def body_R(yaw=0.0, flex=0.0, side=0.0): return Rz(yaw) @ Rx(flex) @ Ry(side)
def bw(n, P, Rb, local): return P + Rb @ (local - HUM[n].root_head)

def key_foot_free(n, s, f, W, Rw, pole=None):
    H = HUM[n]; a = H.ankle[s]
    M = Matrix.Translation(W) @ Rw.to_4x4() @ Matrix.Translation(-a) @ H.r.rest("IK_foot." + s)
    H.r.key_world("IK_foot." + s, f, M)
    if pole is None: pole = W + Rw @ V((0, -0.7, 0.45))
    pb = H.r.PB["Pole_knee." + s]; nm = "Pole_knee." + s
    pb.location = H.r.rest(nm).to_3x3().inverted() @ (pole - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)

def stand_feet(n, f, x, y, yaw, width=1.0, fwdL=0.0, fwdR=0.0):
    H = HUM[n]; g = ground_z(x, y); Rw = Rz(yaw)
    for s, fw in (("L", fwdL), ("R", fwdR)):
        a = H.ankle[s]; loc = V((x, y, g)) + Rw @ V((a.x * width, a.y - H.root_head.y - fw, a.z))
        key_foot_free(n, s, f, loc, Rw)

def relaxed_hand(n, P, Rb, s, fwd=0.0, out=0.0, up=0.0):
    sx = 1 if s == "L" else -1
    sh = rest_head(n, "upperarm01." + s); wr = rest_head(n, "wrist." + s)
    L = (sh - wr).length
    loc = sh + V((sx * (0.07 + out), -fwd, -L * 0.93 + up))
    W = bw(n, P, Rb, loc)
    d = Rb @ V((0, -0.15 * fwd - 0.05, -1)).normalized(); nn = Rb @ V((-sx, 0, 0))
    return W, d, nn

def elbow_pole(n, P, Rb, s, back=0.55, out=0.25, down=-0.1):
    sx = 1 if s == "L" else -1
    return bw(n, P, Rb, rest_head(n, "lowerarm01." + s) + V((out * sx, back, down)))

def key_hand(n, s, f, W, d, nn, pole=None, P=None, Rb=None):
    if pole is None: pole = elbow_pole(n, P, Rb, s)
    HUM[n].key_hand(s, f, W, d, nn, pole)

def key_relaxed(n, f, P, Rb, sides="LR", pose="relaxed"):
    for s in sides:
        W, d, nn = relaxed_hand(n, P, Rb, s)
        key_hand(n, s, f, W, d, nn, P=P, Rb=Rb); apply_pose(D[n], s, pose, f)

def stand(n, f, x, y, yaw=0.0, flex=0.0, side=0.0, spine=0.0, twist=0.0, head=(0.0, 0.0), dz=0.0, hands=True, fwdL=0.0, fwdR=0.0, feet=True):
    H = HUM[n]; g = ground_z(x, y)
    P = V((x, y, g + H.root_head.z - 0.02 + dz)); Rb = body_R(yaw, flex, side)
    H.key_root(f, P, yaw=yaw, flex=flex, side=side); H.key_spine(f, flex=spine, twist=twist, head=head)
    if feet: stand_feet(n, f, x, y, yaw, fwdL=fwdL, fwdR=fwdR)
    if hands: key_relaxed(n, f, P, Rb)
    return P, Rb

def jaw(n, f, deg):
    RIG[n].key_rot("jaw", f, [("X", deg)])

def bone_world(n, bone):
    return D[n].matrix_world @ D[n].pose.bones[bone].matrix

def rest_point_on(n, bone, p_rest):
    """world position of a rest-pose point carried by `bone` at the current frame"""
    M = D[n].pose.bones[bone].matrix @ RIG[n].rest(bone).inverted()
    return D[n].matrix_world @ (M @ p_rest)

# ---------------------------------------------------------------- reference points on the singer
MOUTH_REST = V((0.0, -0.163, 1.622))   # between the lips, in front of the upper teeth (rest pose)
LIPC_REST = V((-0.023, -0.150, 1.617))  # right lip corner

# ---------------------------------------------------------------- props: bat
BAT, BR = D["BatRig"], RIG.get("BatRig") or Rig(D["BatRig"])
def bat_key(f, M):
    BAT.matrix_world = M; BAT.keyframe_insert("location", frame=f); BAT.rotation_mode = 'QUATERNION'
    BAT.keyframe_insert("rotation_quaternion", frame=f)
def bat_set(M):
    BAT.rotation_mode = 'QUATERNION'; BAT.matrix_world = M
def wings(f, up=0.0, fold=0.0, head=0.0):
    """up: wing tips raised (deg, + = up); fold: swept back (deg)"""
    for s, sx in (("L", 1), ("R", -1)):
        BR.key_rot("wing1." + s, f, [("Y", -up * sx), ("Z", fold * sx)])
        BR.key_rot("wing2." + s, f, [("Y", -up * 0.6 * sx)])
    BR.key_rot("head", f, [("X", head)])
def Mloc(p, R3): return Matrix.Translation(p) @ R3.to_4x4()

# ================================================================= A: concert + bat flight (1-300)
S = "Singer"; SP = V((0.0, 0.0))
MIC = D["MicStand"]; MIC.location.y -= 0.025   # keeps the mic >= 3 cm from his face and hair while he sings
# mic stand: shaft at (0,-0.45); right hand grips the shaft at chest height
SHAFT = V((0.0, -0.45, 1.30))
def sing_pose(f, bob=0.0, head=(0.0, 0.0), lpump=0.0):
    P, Rb = stand(S, f, 0.0, 0.0, flex=4 + bob * 2, spine=8 + bob * 3, head=(head[0] - 6 + bob * 4, head[1]), dz=-bob * 0.02, hands=False)
    # right hand around the stand shaft (grip solved once, see below); left arm: relaxed or pumping
    W, d, nn = relaxed_hand(S, P, Rb, "L")
    if lpump > 0:
        sh = bw(S, P, Rb, rest_head(S, "upperarm01.L"))
        W = sh + V((0.18, -0.25, -0.05 + 0.30 * lpump)); d = V((0.15, -0.35, 1.0)).normalized(); nn = V((-0.6, -0.6, 0)).normalized()
        key_hand(S, "L", f, W, d, nn, pole=sh + V((0.45, 0.25, -0.35)))
        apply_pose(D[S], "L", "power_fist", f)
    else:
        key_hand(S, "L", f, W, d, nn, P=P, Rb=Rb); apply_pose(D[S], "L", "relaxed", f)
    key_relaxed(S, f, P, Rb, sides="R")       # right hand hangs relaxed: no contact with the stand (simplest safe staging)
    return P, Rb
for i, f in enumerate(range(1, 171, 12)):
    bob = math.sin(i * 1.3) * 0.5 + 0.5
    sing_pose(f, bob=bob, head=(0, 6 * math.sin(i * 0.9)), lpump=(1.0 if i % 2 == 0 else 0.3) if 20 < f < 150 else 0.0)
# grip the stand shaft with the right hand (frame 1, held to 300)
ARM_L = {}
def key_ikhand_matrix(n, s, f, M, clamp=True):
    """key IK_hand to M (armature space); the target is pulled in to 92% of the arm's reach so the IK always arrives
    (a held prop is baked to this target, so an unreachable target would leave the prop floating off the hand)"""
    if clamp:
        if (n, s) not in ARM_L: ARM_L[n, s] = (RIG[n].BN["upperarm01." + s].head_local - RIG[n].BN["wrist." + s].head_local).length
        sc.frame_set(int(f)); sh = D[n].pose.bones["upperarm01." + s].head
        v = M.translation - sh
        if v.length > 0.92 * ARM_L[n, s]:
            M = M.copy(); M.translation = sh + v.normalized() * 0.92 * ARM_L[n, s]
    pb = D[n].pose.bones["IK_hand." + s]; Rr = RIG[n].rest("IK_hand." + s)
    loc, q, _ = (Rr.inverted() @ M).decompose()
    if pb.rotation_quaternion.dot(q) < 0: q = -q
    pb.location = loc; pb.rotation_quaternion = q
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
# notices the bat: head turns down to his right front
def step_back(f0):
    H = HUM[S]
    for s_, fa, fb in (("R", f0, f0 + 18), ("L", f0 + 16, f0 + 34)):
        a = H.ankle[s_]; A = V((a.x, a.y - H.root_head.y, a.z)); B = A + V((0, 0.10, 0))
        key_foot_free(S, s_, fa, A, Rz(0))
        for k in range(1, 5):
            u = k / 4; f = round(fa + (fb - fa) * u); p = A.lerp(B, smooth(u)); p.z += 0.05 * math.sin(math.pi * u)
            key_foot_free(S, s_, f, p, Rx(-10 * math.sin(math.pi * u)))
        for f in (fb + 1, 345): key_foot_free(S, s_, f, B, Rz(0))
step_back(244)
sing_pose(171, bob=0.3)
for f, hd in ((200, (20, -14)), (240, (26, -18)), (275, (24, -12)), (300, (25, -16))):
    P, Rb = stand(S, f, 0.0, 0.10 * smooth((f - 240) / 40), flex=3, spine=4, head=(hd[0] * 0.8, hd[1]), hands=False, feet=False)
    key_relaxed(S, f, P, Rb)
jaw(S, 1, 0); jaw(S, 60, 6); jaw(S, 90, 1); jaw(S, 120, 7); jaw(S, 150, 0); jaw(S, 200, 4); jaw(S, 300, 3)

# fans: in front of the stage, facing it, arms up cheering (fists), bobbing
FANS = {"Fan1": (-0.75, -3.75, 0.0), "Fan3": (0.55, -3.95, 8.0), "Fan4": (1.55, -3.65, -6.0)}
# a real crowd: the 3 fans cloned to 13 people, each in its own non-skin clothes colour, one or both hands up
def clone(src, name, rgb):
    so = D[src]; o = so.copy(); o.name = name; sc.collection.objects.link(o)
    o.animation_data_clear()
    for pb in o.pose.bones:
        for c_ in pb.constraints:
            for k in ('target', 'pole_target'):
                if getattr(c_, k, None) == so: setattr(c_, k, o)
    for ch in so.children:
        c2 = ch.copy(); c2.parent = o; c2.matrix_parent_inverse = ch.matrix_parent_inverse.copy(); sc.collection.objects.link(c2); c2.name = name + "." + ch.name.split(".", 1)[1]
        for m in c2.modifiers:
            if m.type == 'ARMATURE': m.object = o
        if any(t in ch.name for t in ("suit", "worksuit")):
            for sl in c2.material_slots:
                mm = sl.material.copy(); sl.material = mm
                for nd in mm.node_tree.nodes:
                    if nd.type == 'MIX' and nd.blend_type == 'MULTIPLY': nd.inputs['B'].default_value = (*rgb, 1)
                    if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs['Base Color'].links: nd.inputs['Base Color'].default_value = (*rgb, 1)
    RIG[name] = Rig(o); HUM[name] = Human(RIG[name])
PAL = [(0.08, 0.12, 0.35), (0.05, 0.45, 0.45), (0.40, 0.12, 0.55), (0.06, 0.06, 0.07), (0.92, 0.92, 0.95), (0.95, 0.45, 0.05),
       (0.35, 0.40, 0.10), (0.55, 0.06, 0.10), (0.15, 0.30, 0.75), (0.85, 0.80, 0.10)]
CROWD_POS = [(-2.35, -3.55, 6), (-1.55, -4.25, -4), (2.45, -3.70, -8), (3.25, -4.30, 4), (-3.30, -4.05, 10),
             (-1.05, -4.85, 3), (1.65, -4.95, -3), (-2.70, -4.95, 7), (2.40, -5.05, -6), (0.05, -3.35, 0)]
SRC = ["Fan1", "Fan3", "Fan4"]
ARMS = {}
for k, (x, y, yaw) in enumerate(CROWD_POS):
    n = "Crowd%02d" % k; clone(SRC[k % 3], n, PAL[k]); FANS_EXTRA = None
    ARMS[n] = ("LR", "L", "R")[k % 3]
    FANS_X = None
FANS_ALL = dict(FANS)
for k, (x, y, yaw) in enumerate(CROWD_POS): FANS_ALL["Crowd%02d" % k] = (x, y, float(yaw))
def fan_pose(n, f, x, y, yaw, ph, up):
    H = HUM[n]; bob = 0.5 + 0.5 * math.sin(ph)
    P, Rb = stand(n, f, x, y, yaw=180 + yaw, flex=-3, spine=-6, head=(-15, 0), dz=-0.03 * bob, hands=False)
    for s, sx in (("L", 1), ("R", -1)):
        if s not in ARMS.get(n, "LR"):
            key_relaxed(n, f, P, Rb, sides=s); continue
        sh = bw(n, P, Rb, rest_head(n, "upperarm01." + s))
        lift = up * (0.55 + 0.12 * math.sin(ph + (0 if s == "L" else 1.7)))
        W = sh + Rb @ V((0.10 * sx, -0.18, lift)); d = (Rb @ V((0.05 * sx, -0.2, 1))).normalized(); nn = (Rb @ V((0, -1, 0))).normalized()
        key_hand(n, s, f, W, d, nn, pole=sh + Rb @ V((0.5 * sx, 0.1, -0.3)))
        apply_pose(D[n], s, "power_fist", f)
for n, (x, y, yaw) in FANS_ALL.items():
    ph0 = random.random() * 6
    for i, f in enumerate(range(1, 1301, 15)):
        fan_pose(n, f, x, y, yaw, ph0 + i * 1.1, up=1.0 if f < 330 else 0.75)

# bat flight: thrown from behind the crowd (off screen), arcs over the fans, lands right-front of the singer,
# at a spot his right hand reaches from the crouch (computed from the crouch pose so the grip is real)
STEP = V((0.62, -0.12)); YAW = -14.0
def crouch(f, amt, head=(-50, 0)):
    H = HUM[S]
    P = V((STEP.x, STEP.y + 0.16 * amt, H.root_head.z - 0.02 - 0.58 * amt)); Rb = body_R(YAW, 10 + 36 * amt)
    H.key_root(f, P, yaw=YAW, flex=10 + 36 * amt); H.key_spine(f, flex=12 + 30 * amt, head=head)
    return P, Rb
crouch(450, 1.0); stand_feet(S, 450, STEP.x, STEP.y, YAW); sc.frame_set(450)
_sh = bone_world(S, "upperarm01.R").to_translation()
_arm = (RIG[S].BN["upperarm01.R"].head_local - RIG[S].BN["wrist.R"].head_local).length
_dir = (Rz(YAW + 22) @ V((0, -1, 0)))
_best = None
for k in range(80):
    q = V((_sh.x, _sh.y, 0)) + _dir * (0.05 + k * 0.01); q.z = 0.0
    dd = (q + V((0, 0, 0.11)) - _sh).length
    if _best is None or abs(dd - 0.86 * _arm) < abs(_best[1] - 0.86 * _arm): _best = (q, dd)
LAND = _best[0] - (Rz(YAW) @ V((0.0, 0.0, 0)))
print("LAND", tuple(round(x, 3) for x in LAND), "shoulder", tuple(round(x, 3) for x in _sh), "arm", round(_arm, 3))
BAT_LIE = Rz(200) @ Rx(90)                      # belly down, head toward the singer side, wings flat
P0, T0, T1 = V((0.05, -4.6, -0.6)), 24, 108   # starts below frame, between the fans
g = 9.8; T = (T1 - T0) / 60.0
z1 = 0.026; v0z = (z1 - P0.z + 0.5 * g * T * T) / T
def bat_flight(f):
    t = (f - T0) / 60.0; u = t / T
    p = P0.lerp(V((LAND.x, LAND.y, 0)), u); p.z = P0.z + v0z * t - 0.5 * g * t * t
    return p
BAT.rotation_mode = 'QUATERNION'
for f in range(1, T0 + 1, 4):
    bat_key(f, Mloc(V((0.9, -9.0, -3.0)), Rx(30)))       # out of sight below the audience floor before the throw
for f in range(T0, T1 + 1, 2):
    u = (f - T0) / (T1 - T0)
    R3 = (Rz(170 + 40 * u) @ Rx(60 - 10 * math.sin(u * 6.0)) @ Ry(25 * math.sin(u * 7.0))) if u < 0.85 else \
        (Rz(200) @ Rx(60 + (90 - 60) * (u - 0.85) / 0.15))
    bat_key(f, Mloc(bat_flight(f), R3))
for f in range(T0, T1 + 1, 4):    # floppy rubber-like flutter in the air
    wings(f, up=18 * math.sin((f - T0) * 0.55), fold=6 * math.sin((f - T0) * 0.3), head=8 * math.sin(f * 0.4))
# land + tiny bounce, then rest
bat_key(T1 + 4, Mloc(LAND + V((0.0, 0.0, 0.05)), BAT_LIE)); bat_key(T1 + 9, Mloc(LAND + V((0.02, 0.01, 0.026)), BAT_LIE))
wings(T1 + 4, up=-10); wings(T1 + 9, up=-14); wings(T1 + 14, up=-15)
HOLD_FOLD = float(os.environ.get("BAT_HOLD_FOLD", "-60")); HOLD_UP = float(os.environ.get("BAT_HOLD_UP", "25"))
HW = float(os.environ.get('HOLD_WING', '-75'))
HF = float(os.environ.get('HOLD_FOLD', '40'))   # tips swing to the belly side, away from his forearm
wings(446, up=-15); wings(472, up=HW, fold=HF); wings(862, up=HW, fold=HF)   # wings folded along the body while he holds it (clear of his arms and body)
for f_, a_ in ((446, 0), (470, -55), (675, -55), (695, 0), (830, 0), (848, -55), (862, -55), (898, 0)):
    BR.key_rot("legs", f_, [("X", a_)])   # legs hang free only at the bite (curled legs read as a blob in close-up)
BAT_REST = Mloc(LAND + V((0.02, 0.01, 0.026)), BAT_LIE)
bat_key(300, BAT_REST)

# ================================================================= B: pick it up (300-620)
# release the stand (hand back to relaxed), small step toward the bat, crouch, grip, rise, look at it
P, Rb = stand(S, 300, 0.0, 0.10, flex=3, spine=4, head=(20, -16), hands=False, feet=False); key_relaxed(S, 300, P, Rb)
P, Rb = stand(S, 335, 0.0, 0.10, flex=2, spine=4, head=(16, -12), hands=False, feet=False); key_relaxed(S, 335, P, Rb)
# step: shift to stand at (0.25, -0.15) turned slightly right (yaw -15) -> right foot moves first
def steps(f0):
    H = HUM[S]
    for s, fa, fb in (("R", f0, f0 + 22), ("L", f0 + 18, f0 + 40)):
        a = H.ankle[s]
        A0 = V((0, 0.10, 0)) + V((a.x, a.y - H.root_head.y, a.z)); B0 = V((STEP.x, STEP.y, 0)) + Rz(YAW) @ V((a.x, a.y - H.root_head.y, a.z))
        for k in range(0, 5):
            u = k / 4; f = round(fa + (fb - fa) * u)
            p = A0.lerp(B0, smooth(u)); p.z += 0.07 * math.sin(math.pi * u)
            key_foot_free(S, s, f, p, Rz(YAW * smooth(u)) @ Rx(-12 * math.sin(math.pi * u)))
        key_foot_free(S, s, fb + 1, B0, Rz(YAW))
steps(345)
for f, u in ((345, 0.0), (365, 0.5), (387, 1.0)):
    p = V((0, 0.10)).lerp(STEP, smooth(u)); p.y += 0.04 * math.sin(math.pi * u)   # steps right and slightly back, clear of the mic
    P, Rb = stand(S, f, p.x, p.y, yaw=YAW * u, flex=2 + 6 * u, spine=4 + 8 * u, head=(16 + 12 * u, -8 * (1 - u)), hands=False, feet=False,
                  dz=-0.02 * math.sin(math.pi * u))
    key_relaxed(S, f, P, Rb)
# crouch: deep knee bend, torso forward, right hand down to the bat
for f, a in ((395, 0.0), (415, 0.45), (435, 0.9), (450, 1.0)):
    P, Rb = crouch(f, a)
    if f < 450:
        key_relaxed(S, f, P, Rb, sides="L")
        W, d, nn = relaxed_hand(S, P, Rb, "R", fwd=0.25 * a); key_hand(S, "R", f, W, d, nn, P=P, Rb=Rb); apply_pose(D[S], "R", "relaxed", f)
# feet stay planted at the step position from here (keys at the end of the block)
for f in (450, 470, 520, 620):
    pass
# the hold, built from the hand's own geometry (director: the bat must sit INSIDE the closed fingers):
# bat body centre 2.8 cm off the palm centre on the palm side, its back against the palm, head out past the index finger
_wr, _B0, _basis, _palm = _rest_hand(D[S], "R"); _sg = _rest_palm_sign(D[S], "R", _B0.col[2])
_d, _a, _n = _B0.col[0].normalized(), _B0.col[1].normalized(), (_B0.col[2] * _sg).normalized()
_Z = _a; _Y = (-_n - _Z * (-_n).dot(_Z)).normalized(); _X = _Y.cross(_Z)
BAT_IN_HAND = Mloc(_palm + _n * 0.028 + _d * 0.008 - _Z * 0.010, Matrix((_X, _Y, _Z)).transposed())   # armature rest space
REL = (D[S].matrix_world @ RIG[S].rest("IK_hand.R")).inverted() @ (D[S].matrix_world @ BAT_IN_HAND)
sc.frame_set(450); bat_set(BAT_REST); bpy.context.view_layer.update()
P, Rb = crouch(450, 1.0); key_relaxed(S, 450, P, Rb, sides="L")
key_ikhand_matrix(S, "R", 450, D[S].matrix_world.inverted() @ (BAT_REST @ REL.inverted()))
apply_pose(D[S], "R", "shield", 432); apply_pose(D[S], "R", "shield", 446); apply_pose(D[S], "R", "shield", 450)
apply_pose(D[S], "R", "wrap_grip", 455, amount=0.85)     # fingers close round the bat's body
sc.frame_set(450)
IKR_GRAB = D[S].pose.bones["IK_hand.R"].matrix.copy()
print("REACH err at grab (m):", round((bone_world(S, "wrist.R").to_translation() - (D[S].matrix_world @ IKR_GRAB).to_translation()).length, 4))
_ach = (D[S].matrix_world @ IKR_GRAB) @ REL
print("HOLD check: bat placed at grab off its floor pose by (m)", round((_ach.to_translation() - BAT_REST.to_translation()).length, 4))
# hold the crouch a beat, then rise holding it at chest height in front, looking at it
key_ikhand_matrix(S, "R", 458, IKR_GRAB); P, Rb = crouch(458, 1.0); key_relaxed(S, 458, P, Rb, sides="L")
def hand_for_bat(Mbat):
    return D[S].matrix_world.inverted() @ (Mbat @ REL.inverted())
for f, a in ((480, 0.6), (505, 0.15), (520, 0.0)):
    P, Rb = crouch(f, a, head=(20 - 30 * a, -8)); key_relaxed(S, f, P, Rb, sides="L")
# chest-height look: bat upright-ish (head up), held 0.35 m in front of the chest, face toward him
TILT = float(os.environ.get('BAT_TILT', '-60')); FWD = float(os.environ.get('BAT_FWD', '0.42'))
def bat_front(f, P, Rb, fwd=None, up=-0.06, yaw=0.0, tilt=0.0, side=-0.05):
    fwd = FWD if fwd is None else fwd; tilt = tilt + TILT
    chest = bw(S, P, Rb, rest_head(S, "spine01")) + Rb @ V((side, -fwd, up))
    R3 = Rb @ Rz(180 + yaw) @ Rx(tilt)          # bat face (-Y local) turned toward the singer
    Mb = Mloc(chest, R3); key_ikhand_matrix(S, "R", f, hand_for_bat(Mb)); return Mb
for f, a, yw, hd in ((520, 0.0, 0.0, (28, -10)), (560, 0.0, 20.0, (26, -6)), (600, 0.0, -10.0, (30, -12)), (620, 0.0, 0.0, (24, -8))):
    P, Rb = stand(S, f, STEP.x, STEP.y, yaw=YAW, flex=4, spine=8, head=hd, hands=False, feet=False)
    key_relaxed(S, f, P, Rb, sides="L"); bat_front(f, P, Rb, yaw=yw)
# low-to-chest path while rising (480, 505)
# lift straight up out in front first (clear of his thighs), then in to the chest
P, Rb = crouch(472, 0.85, head=(20 - 30 * 0.85, -8)); M = IKR_GRAB.copy(); M.translation += V((0, 0, 0.20)) + Rz(YAW) @ V((0, -0.08, 0)); key_ikhand_matrix(S, "R", 472, M)
P, Rb = crouch(495, 0.4, head=(20 - 30 * 0.4, -8)); bat_front(495, P, Rb, fwd=0.58, up=-0.40)
# feet planted at the step position for the rest of the stage action
for f in (390, 450, 620, 960, 1280, 1600):
    stand_feet(S, f, STEP.x, STEP.y, YAW)

# ================================================================= C: the bite (620-960)
def head_frame(f, hd, flex=4, spine=8, side=0.0):
    P, Rb = stand(S, f, STEP.x, STEP.y, yaw=YAW, flex=flex, spine=spine, head=hd, side=side, hands=False, feet=False)
    key_relaxed(S, f, P, Rb, sides="L"); return P, Rb
BITE_TIP = {}
def bat_at_mouth(f, depth=0.0, roll=0.0, pitch=-14.0):
    """bat head between the lips: bat local +Z (head) points into the mouth along the face direction"""
    sc.frame_set(f)
    m = rest_point_on(S, "head", MOUTH_REST)
    Mh = bone_world(S, "head"); fwd = (Mh.to_3x3() @ (RIG[S].rest("head").to_3x3().inverted() @ V((0, -1, 0)))).normalized()
    upv = (Mh.to_3x3() @ (RIG[S].rest("head").to_3x3().inverted() @ V((0, 0, 1)))).normalized()
    zb = -fwd                                    # bat head axis points back into the mouth
    xb = upv.cross(zb).normalized(); yb = zb.cross(xb)
    R3 = Matrix((xb, yb, zb)).transposed() @ Rz(180 + roll) @ Rx(pitch)
    tip = 0.054                                  # head top above the bat origin (local z)
    Mb = Mloc(m + fwd * (0.004 - depth) - upv * 0.006 - R3 @ V((0, 0, tip)), R3)
    BITE_TIP[f] = (m + fwd * (0.004 - depth) - upv * 0.006, fwd)
    key_ikhand_matrix(S, "R", f, hand_for_bat(Mb)); return Mb
# raise toward the mouth (620-700), jaw opens 680-700, bite 700-712, playful shake, hold
for f, hd in ((640, (8, 0)), (665, (6, 0))):
    P, Rb = head_frame(f, hd)
    u = (f - 620) / 45; bat_front(f, P, Rb, fwd=0.46 - 0.04 * u, up=0.08 + 0.14 * u, yaw=0, tilt=-10 - 30 * u)
jaw(S, 620, 2); jaw(S, 680, 3); jaw(S, 700, 4); jaw(S, 712, 3); jaw(S, 830, 3); jaw(S, 860, 2)
P, Rb = head_frame(690, (2, 0)); bat_at_mouth(690, depth=-0.09)
P, Rb = head_frame(702, (1, 0)); bat_at_mouth(702, depth=-0.03)
TIP_OFF = -0.007     # director: bat tip 6-8 mm off the lips through the bite (cut on visible contact)
for i_, f_ in enumerate((712, 735, 760, 785, 810, 830)):     # held at the lips (the edit shows the crowd over this hold)
    P, Rb = head_frame(f_, (2 + 1.5 * math.sin(i_), 3 * math.sin(i_ * 1.7) if 0 < i_ < 5 else 0)); bat_at_mouth(f_, depth=TIP_OFF)
# ================================================================= D: it's real: recoils, lets it fall, shock (724-1280)
P, Rb = stand(S, 842, STEP.x, STEP.y, yaw=YAW, flex=-4, spine=-6, head=(4, 0), hands=False, feet=False); key_relaxed(S, 842, P, Rb, sides="L")
bat_front(842, P, Rb, fwd=0.44, up=0.00, tilt=-20)
P, Rb = stand(S, 858, STEP.x, STEP.y, yaw=YAW, flex=-3, spine=-5, head=(14, 0), hands=False, feet=False); key_relaxed(S, 858, P, Rb, sides="L")
Mb = bat_front(858, P, Rb, fwd=0.44, up=-0.14, tilt=-25)
P, Rb = stand(S, 864, STEP.x, STEP.y, yaw=YAW, flex=-3, spine=-5, head=(16, 0), hands=False, feet=False); key_relaxed(S, 864, P, Rb, sides="L")
Mb = bat_front(864, P, Rb, fwd=0.44, up=-0.15, tilt=-25)
GF = float(os.environ.get('BITE_LOOSEN', '0.0'))
apply_pose(D[S], "R", "cup_hold", 672, amount=GF); apply_pose(D[S], "R", "cup_hold", 830, amount=GF)   # a looser fist at the bite (fingers resting on the fur)
apply_pose(D[S], "R", "wrap_grip", 846, amount=0.85); apply_pose(D[S], "R", "wrap_grip", 862, amount=0.85); apply_pose(D[S], "R", "open_alarm", 868)   # lets go: the bat drops
DROP = V((STEP.x, STEP.y, 0.026)) + Rz(YAW) @ V((0.12, -0.66, 0))   # in front of his feet, clear of both shoes and the stand base
def shock_stand(f, hd, mouth_hand=False):
    P, Rb = stand(S, f, STEP.x, STEP.y, yaw=YAW, flex=2, spine=4, head=hd, hands=False, feet=False)
    key_relaxed(S, f, P, Rb, sides="R")
    if mouth_hand:     # left hand raised toward his mouth, ~6 cm clear of the lips
        sc.frame_set(f); m = rest_point_on(S, "head", MOUTH_REST)
        Mh = bone_world(S, "head"); fwd = (Mh.to_3x3() @ (RIG[S].rest("head").to_3x3().inverted() @ V((0, -1, 0)))).normalized()
        sh = bone_world(S, "upperarm01.L").to_translation()
        hf = Rz(YAW) @ V((0, -1, 0)); W = m + hf * 0.15 + V((0, 0, -0.15)) + (Rz(YAW) @ V((0.03, 0, 0)))   # wrist below/in front: fingertips stop ~7 cm in front of the lips
        key_hand(S, "L", f, W, (V((0, 0, 0.92)) - hf * 0.39).normalized(), -hf, pole=sh + Rz(YAW) @ V((0.45, 0.25, -0.45)))
        apply_pose(D[S], "L", "relaxed", f)
    else:
        key_relaxed(S, f, P, Rb, sides="L")
for f, hd, mh in ((882, (22, -4), False), (905, (30, -8), False), (950, (32, -10), False), (1000, (30, -6), False), (1045, (33, -9), False),
                  (1075, (30, -7), True), (1120, (32, -10), True), (1180, (30, -6), True), (1240, (33, -9), True), (1280, (31, -7), True)):
    shock_stand(f, hd, mh)
jaw(S, 882, 3); jaw(S, 950, 2); jaw(S, 1045, 3); jaw(S, 1280, 2)
# (no blood: director / LESSONS hard limit)

# ================================================================= E: drops it, bends over (1280-1600)
wings(868, up=HW, fold=HF); wings(886, up=-20); wings(902, up=-15)
def bake_held(f0, f1):
    """bat carried by the ACTUAL wrist bone (after IK + wrist limits), not the IK target: it sits in the fingers every frame"""
    sc.frame_set(f0)
    REL_W = (D[S].matrix_world @ D[S].pose.bones["wrist.R"].matrix).inverted() @ ((D[S].matrix_world @ D[S].pose.bones["IK_hand.R"].matrix) @ REL)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        Mh = D[S].matrix_world @ D[S].pose.bones["wrist.R"].matrix
        bat_key(f, Mh @ REL_W)

def stagger(f, sway):
    P, Rb = stand(S, f, STEP.x, STEP.y + 0.03 * sway, yaw=YAW, flex=10, spine=12, side=3 * sway, head=(14, -6 * sway), hands=False, feet=False)
    sc.frame_set(f); m = rest_point_on(S, "head", MOUTH_REST)
    Mh = bone_world(S, "head"); fwd = (Mh.to_3x3() @ (RIG[S].rest("head").to_3x3().inverted() @ V((0, -1, 0)))).normalized()
    sh = bone_world(S, "upperarm01.L").to_translation()
    hf = Rz(YAW) @ V((0, -1, 0)); W = m + hf * 0.15 + V((0, 0, -0.15)) + (Rz(YAW) @ V((0.03, 0, 0)))   # fingertips ~7 cm in front of the lips
    key_hand(S, "L", f, W, (V((0, 0, 0.92)) - hf * 0.39).normalized(), -hf, pole=sh + Rz(YAW) @ V((0.45, 0.25, -0.45)))
    apply_pose(D[S], "L", "relaxed", f)
    kn = bone_world(S, "lowerleg01.R").to_translation(); fwd2 = Rz(YAW) @ V((0, -1, 0))
    place_hand(D[S], "R", f, kn + fwd2 * 0.06 + V((0, 0, 0.07)), (-fwd2 + V((0, 0, -1.2))).normalized(), (fwd2 + V((0, 0, -0.6))).normalized())
    apply_pose(D[S], "R", "relaxed", f)
    pb = D[S].pose.bones["Pole_elbow.R"]; nm = "Pole_elbow.R"; pole = bone_world(S, "upperarm01.R").to_translation() + Rz(YAW) @ V((-0.5, 0.35, 0.0))
    pb.location = RIG[S].rest(nm).to_3x3().inverted() @ (D[S].matrix_world.inverted() @ pole - RIG[S].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)
for f, sw in ((1300, 0.0), (1325, 1.0), (1350, -0.6), (1375, 0.4)):
    stagger(f, sw)
# bend over, hands on the thighs above the knees, breathing hard
def bend(f, amt, br=0.0):
    H = HUM[S]
    P = V((STEP.x, STEP.y + 0.10 * amt, H.root_head.z - 0.02 - 0.12 * amt)); Rb = body_R(YAW, 20 * amt)
    H.key_root(f, P, yaw=YAW, flex=20 * amt); H.key_spine(f, flex=(38 + 6 * br) * amt, head=(-10 + 8 * br, 0))
    return P, Rb
for f, a in ((1395, 0.0), (1420, 0.6), (1440, 1.0)):
    P, Rb = bend(f, a)
    if a < 1.0:
        key_relaxed(S, f, P, Rb)
# hands on thighs: palm on the front of each thigh, ~12 cm above the knee
def thigh_hands(f):
    sc.frame_set(f)
    for s in "LR":
        kn = bone_world(S, "lowerleg01." + s).to_translation(); hp = bone_world(S, "upperleg01." + s).to_translation()
        p = kn.lerp(hp, 0.28); fwd = (Rz(YAW) @ V((0, -1, 0)))
        sx = 1 if s == "L" else -1
        W_palm = p + fwd * 0.075 + V((0, 0, 0.01))
        place_hand(D[S], s, f, W_palm, -fwd + V((0, 0, -0.35)), (V((0, 0, -1)) + fwd * 0.4 + (Rz(YAW) @ V((-0.25 * sx, 0, 0)))).normalized())
        apply_pose(D[S], s, "relaxed", f)
        pb = D[S].pose.bones["Pole_elbow." + s]; nm = "Pole_elbow." + s
        pole = bone_world(S, "upperarm01." + s).to_translation() + Rz(YAW) @ V((0.5 * sx, 0.4, 0.0))
        pb.location = RIG[S].rest(nm).to_3x3().inverted() @ (D[S].matrix_world.inverted() @ pole - RIG[S].BN[nm].head_local)
        pb.keyframe_insert("location", frame=f, group=nm)
for i, f in enumerate(range(1440, 1601, 20)):
    bend(f, 1.0, br=math.sin(i * 1.4)); thigh_hands(f)
jaw(S, 1340, 4); jaw(S, 1400, 6); jaw(S, 1600, 5)

# ================================================================= F: hospital (1600-2100)
# hard cut at 1600: everyone moves with CONSTANT keys at the boundary
CUT = 1600
BED = D["Bed"]
bpy.context.view_layer.update(); _dg = bpy.context.evaluated_depsgraph_get()
_hit, _loc, _n, _i, _ob, _M = sc.ray_cast(_dg, V((HX, 0.6, 1.5)), V((0, 0, -1)))
MATT_Z = _loc.z if _hit and _ob.name == "Bed" else 0.62
print("MATT_Z", round(MATT_Z, 3), _ob.name if _hit else None)
# reclined on a wedge pillow: hips on the mattress, back at ~50 deg, legs straight under the blanket
HIP = V((HX, 0.85, MATT_Z + 0.16))
RECL = -32
def recline(f, br=0.0, head=(0.0, 0.0)):
    H = HUM[S]
    H.key_root(f, HIP + V((0, 0, 0.004 * br)), yaw=0, flex=RECL); H.key_spine(f, flex=6 + 2 * br, head=(8 + head[0], head[1]))
    Rb = body_R(0, RECL)
    for s in "LR":
        a = H.ankle[s]; sx = 1 if s == "L" else -1
        W = V((HX + a.x * 0.9, HIP.y - 0.93, 0))
        _h = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), V((W.x, W.y - 0.08, 1.5)), V((0, 0, -1)))
        W.z = max(MATT_Z, _h[1].z if _h[0] and _h[4].name == "Bed" else MATT_Z) + 0.17   # heel clear of the mattress at the foot end
        key_foot_free(S, s, f, W, Rx(-80), pole=W + V((0, 0.3, 0.8)))
        # forearms resting on the blanket over the belly/thighs
        sh = bw(S, HIP, Rb, rest_head(S, "upperarm01." + s))
        Wh = V((HX + 0.13 * sx, HIP.y - 0.16, MATT_Z + 0.30))
        key_hand(S, s, f, Wh, V((-0.6 * sx, -1, -0.2)).normalized(), V((0, 0.3, -1)).normalized(), pole=sh + V((0.5 * sx, 0.05, -0.3)))
        apply_pose(D[S], s, "relaxed", f)
for i, f in enumerate(range(CUT, 2101, 30)):
    recline(f, br=math.sin(i * 1.3))
jaw(S, CUT, 1); jaw(S, 2100, 1)
def soft_mat(n, rgb, rough=0.7):
    m = bpy.data.materials.new(n); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (*rgb, 1); Pn.inputs["Roughness"].default_value = rough; return m
def wedge():
    Rb = body_R(0, RECL); me = bpy.data.meshes.new("Wedge"); bm = bmesh.new()
    back = 0.15; L = 0.95; W = 0.34
    pts = []
    for sx in (-1, 1):
        a = HIP + Rb @ V((W * sx, back, -0.02)); b = HIP + Rb @ V((W * sx, back, L))
        pts += [V((a.x, a.y, MATT_Z)), a, b, V((b.x, b.y, MATT_Z))]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); o = bpy.data.objects.new("Wedge", me); sc.collection.objects.link(o)
    b = o.modifiers.new("B", 'BEVEL'); b.width = 0.05; b.segments = 4; o.modifiers.new("S", 'SUBSURF').levels = 2
    me.materials.append(soft_mat("M_Pillow", (0.92, 0.94, 0.96)))
    for p in me.polygons: p.use_smooth = True
wedge()
def blanket():
    """sheet draped over the posed legs: ray cast down onto the singer at the cut frame, 2 cm over the body, falling to the mattress"""
    sc.frame_set(CUT); bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new("Blanket"); bm = bmesh.new(); nx, ny = 48, 60
    x0, x1, y0, y1 = HX - 0.48, HX + 0.48, HIP.y - 1.18, HIP.y - 0.30   # legs only: the hands rest on his belly above it
    H = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny; z = MATT_Z + 0.012
            o_ = V((x, y, 2.0))
            for _ in range(16):
                hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, o_, V((0, 0, -1)))
                if not hit: break
                if ob.name.startswith(S + ".") or ob.name == S:
                    z = max(z, loc.z + 0.035); break
                o_ = loc - V((0, 0, 0.001))
            H[i, j] = z
    for _ in range(2):     # dilate: cover what lies between the samples (toes, shoe tips)
        H = {(i, j): max([H[k] for k in ((i, j), (i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if k in H]) for (i, j) in H}
    for _ in range(6):     # relax into soft folds
        H2 = dict(H)
        for (i, j), z in H.items():
            nb = [H[k] for k in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if k in H]
            H2[i, j] = max(z, 0.5 * z + 0.5 * sum(nb) / len(nb)) if z > MATT_Z + 0.013 else 0.6 * z + 0.4 * sum(nb) / len(nb)
        H = H2
    grid = {}
    for (i, j), z in H.items():
        x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
        edge = max(0.0, max(abs(x - HX) - 0.42, 0)); grid[i, j] = bm.verts.new((x, y, z - edge * 2.0))
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]))
    bm.to_mesh(me); o = bpy.data.objects.new("Blanket", me); sc.collection.objects.link(o)
    sol = o.modifiers.new("Sol", 'SOLIDIFY'); sol.thickness = 0.012; sol.offset = 1
    o.modifiers.new("Sub", 'SUBSURF').levels = 1
    me.materials.append(soft_mat("M_Blanket", (0.55, 0.72, 0.92)))
    for p in me.polygons: p.use_smooth = True
blanket()
print('BLANKET', D['Blanket'].location, len(D['Blanket'].data.vertices))
def oxygen_mask():
    """cup built from the singer's own face (nose + mouth region), pushed out into a dome: fits the face exactly"""
    body = D[S + ".body"]; C = V((0.0, -0.150, 1.625))
    # built on the face AS POSED in the hospital (the lower face follows the neck/jaw, not only the head bone),
    # then expressed in the head bone's rest frame so a Child Of (identity at rest) carries it exactly
    sc.frame_set(CUT); bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me0 = ev.to_mesh().copy()
    MW = (D[S].matrix_world @ RIG[S].rest("head")) @ (D[S].matrix_world @ D[S].pose.bones["head"].matrix).inverted() @ body.matrix_world
    MN = MW.to_3x3().inverted().transposed()
    from mathutils.bvhtree import BVHTree
    _bm = bmesh.new(); _bm.from_mesh(me0); _bm.transform(MW); _bvh = BVHTree.FromBMesh(_bm); _bm.free()
    WC = {v.index: MW @ v.co for v in me0.vertices}; WN = {v.index: (MN @ v.normal).normalized() for v in me0.vertices}
    # clean grid cap (no filled holes): directions from Ce inside an elliptical cone; radius = smooth ellipsoid,
    # but always 6 mm (rim) .. 18 mm (centre) outside the widest skin in that direction
    Ce = V((0.0, -0.095, 1.622)); bm = bmesh.new(); G = {}; N_ = 36
    for i in range(N_ + 1):
        for j in range(N_ + 1):
            a_ = -1 + 2 * i / N_; b_ = -1 + 2 * j / N_; r2 = a_ * a_ + b_ * b_
            if r2 > 1.0: continue
            dirv = V((0.50 * a_ * (0.78 - 0.30 * b_), -1.0, 0.58 * b_ - 0.04)).normalized()   # triangular: narrow at the nose bridge, wide at the chin
            k = 1.0 / math.sqrt((dirv.x / 0.056) ** 2 + (dirv.y / 0.094) ** 2 + (dirv.z / 0.060) ** 2)
            r_skin = 0.0
            for jx in (-0.006, 0.0, 0.006):
                for jz in (-0.006, 0.0, 0.006):
                    dj = (dirv + V((jx, 0, jz)) / 0.12).normalized(); hit = _bvh.ray_cast(Ce + dj * 0.4, -dj, 0.4)
                    if hit[0] is not None: r_skin = max(r_skin, (hit[0] - Ce).length)
            G[i, j] = bm.verts.new(Ce + dirv * max(k * (1 - 0.22 * r2), r_skin + 0.004 + 0.004 * (1 - r2)))   # rigid smooth shell; skin clearance only near the rim   # small, low-profile medical cup
    for i in range(N_):
        for j in range(N_):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k_ in G for k_ in q): bm.faces.new([G[k_] for k_ in q])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    vmap = G
    # visible rim: the cup's boundary loop as a soft green rubber bead
    bnd = [e for e in bm.edges if e.is_boundary]; nxt = {}
    for e in bnd:
        a_, b_ = e.verts; nxt.setdefault(a_, []).append(b_); nxt.setdefault(b_, []).append(a_)
    loop = [bnd[0].verts[0]]; prev = None
    while True:
        cands = [v for v in nxt[loop[-1]] if v is not prev]
        if not cands or cands[0] is loop[0]: break
        prev = loop[-1]; loop.append(cands[0])
    rc = bpy.data.curves.new("OxyRim", 'CURVE'); rc.dimensions = '3D'; rc.bevel_depth = 0.0028; rc.bevel_resolution = 2
    rs = rc.splines.new('POLY'); rs.points.add(len(loop) - 1); rs.use_cyclic_u = True
    for pt, v in zip(rs.points, loop): pt.co = (v.co.x, v.co.y, v.co.z, 1.0)
    rim = bpy.data.objects.new("OxyRim", rc); sc.collection.objects.link(rim); rc.materials.append(soft_mat("M_OxyRim", (0.35, 0.75, 0.55), 0.35))
    print("MASK rim points", len(loop))
    me = bpy.data.meshes.new("OxygenMask"); bm.to_mesh(me)
    o = bpy.data.objects.new("OxygenMask", me); sc.collection.objects.link(o)
    so = o.modifiers.new("Sol", 'SOLIDIFY'); so.thickness = 0.0025; so.offset = 1
    o.modifiers.new("Sub", 'SUBSURF').levels = 1
    m = soft_mat("M_OxyMask", (0.55, 0.90, 0.70), rough=0.08)
    Pn = m.node_tree.nodes["Principled BSDF"]; Pn.inputs["Alpha"].default_value = 0.32; Pn.inputs["Coat Weight"].default_value = 0.8   # clear plastic, light green tint
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    # tube from the bottom of the cup down over the chest to the bed side, and a thin elastic strap toward the ears
    cu = bpy.data.curves.new("OxyTube", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006; cu.bevel_resolution = 3
    bot = G[N_ // 2, 0].co.copy(); sp = cu.splines.new('BEZIER'); pts = [bot + V((0, -0.004, -0.004)), bot + V((0.01, -0.04, -0.12)), bot + V((0.10, -0.06, -0.32)), bot + V((0.26, -0.02, -0.48))]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    t = bpy.data.objects.new("OxyTube", cu); sc.collection.objects.link(t); cu.materials.append(soft_mat("M_Tube", (0.85, 0.95, 0.92), 0.3))
    cs = bpy.data.curves.new("OxyStrap", 'CURVE'); cs.dimensions = '3D'; cs.bevel_depth = 0.0018
    hair = D[S + ".long01"]; evh = hair.evaluated_get(bpy.context.evaluated_depsgraph_get()); mh = evh.to_mesh()
    _hb = bmesh.new(); _hb.from_mesh(mh); _hb.transform(MW @ body.matrix_world.inverted() @ hair.matrix_world); _hbvh = BVHTree.FromBMesh(_hb); _hb.free()
    HC = V((0.0, -0.01, 1.655))                       # head centre (rest frame)
    def outer(p_dir):
        best = None
        for t_ in (_bvh, _hbvh):
            hit = t_.ray_cast(HC + p_dir * 0.4, -p_dir, 0.4)
            if hit[0] is not None and (best is None or (hit[0] - HC).length > (best - HC).length): best = hit[0]
        return best
    for sx in (-1, 1):   # elastic strap: from the cup's side over the cheek, then over the hair round the back of the head
        st0 = G[N_ if sx > 0 else 0, N_ // 2].co.copy(); q = [st0]
        a0 = math.atan2((st0 - HC).x * sx, -(st0 - HC).y)
        for k_ in range(1, 61):
            ang = a0 + (math.pi - a0) * k_ / 60; d_ = V((sx * math.sin(ang), -math.cos(ang), (st0.z - HC.z) / 0.4 * (1 - k_ / 60) + 0.04 * k_ / 60)).normalized()
            h_ = outer(d_)
            if h_ is not None: q.append(h_ + (h_ - HC).normalized() * 0.012)
        s2 = cs.splines.new("POLY"); s2.points.add(len(q) - 1)
        for pt, p in zip(s2.points, q): pt.co = (p.x, p.y, p.z, 1.0)
    st = bpy.data.objects.new("OxyStrap", cs); sc.collection.objects.link(st); cs.materials.append(soft_mat("M_Strap", (0.9, 0.95, 0.95), 0.5))
    bpy.data.objects.remove(st, do_unlink=True)   # director: no visible strap (it read as a rigid stick past the cheek)
    for ob in (o, t, rim):     # Child Of the head bone (a prop, not a rig child), identity at rest
        c = ob.constraints.new('CHILD_OF'); c.target = D[S]; c.subtarget = "head"
        c.inverse_matrix = (D[S].matrix_world @ RIG[S].rest("head")).inverted()
        for f, hid in ((1, True), (CUT, False)):
            ob.hide_render = ob.hide_viewport = hid; ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
    print("MASK verts", len(vmap)); bpy.data.meshes.remove(me0)
oxygen_mask()
# doctor at the bed's right side (from the patient), facing the bed, syringe in the right hand, taps it
DP = V((HX - 0.80, 0.62))
SYR = None
def make_syringe():
    me = bpy.data.meshes.new("Syringe"); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.0075, radius2=0.0075, depth=0.085)          # barrel
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.0045, radius2=0.0045, depth=0.04,
                          matrix=Matrix.Translation((0, 0, 0.06)))                                              # plunger rod
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.011, radius2=0.011, depth=0.004,
                          matrix=Matrix.Translation((0, 0, 0.082)))                                             # thumb rest
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.0007, radius2=0.0004, depth=0.022,
                          matrix=Matrix.Translation((0, 0, -0.053)))                                            # needle
    bm.to_mesh(me); o = bpy.data.objects.new("Syringe", me); sc.collection.objects.link(o)
    m = bpy.data.materials.new("M_Syringe"); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.85, 0.92, 0.95, 1); Pn.inputs["Roughness"].default_value = 0.25
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    return o
SYR = make_syringe()
# simplest safe staging: the syringe and a vial lie on a steel tray on a cart beside the doctor (no hand contact)
def cart():
    m_st = bpy.data.materials.new("M_Steel"); m_st.use_nodes = True; Pn = m_st.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.8, 0.82, 0.85, 1); Pn.inputs["Metallic"].default_value = 0.8; Pn.inputs["Roughness"].default_value = 0.35
    cx, cy = HX - 0.62, -0.42
    parts = []
    for (sx, sy, sz, x, y, z) in ((0.55, 0.40, 0.02, cx, cy, 0.86), (0.55, 0.40, 0.02, cx, cy, 0.30), (0.40, 0.28, 0.02, cx, cy, 0.885)):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z)); o = bpy.context.object; o.scale = (sx, sy, sz); parts.append(o)
        bv = o.modifiers.new("B", 'BEVEL'); bv.width = 0.008; bv.segments = 2
    for dx in (-0.25, 0.25):
        for dy in (-0.18, 0.18):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.84, location=(cx + dx, cy + dy, 0.45)); parts.append(bpy.context.object)
    for o in parts:
        o.data.materials.append(m_st); o.name = "Cart"
    # tray rim
    return cx, cy
cx, cy = cart()
D_ = "Doctor"
SYR_M = Mloc(V((cx - 0.03, cy + 0.02, 0.905)), Ry(90) @ Rx(0) @ Rz(25))
SYR.matrix_world = SYR_M
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.012, depth=0.045, location=(cx + 0.11, cy - 0.06, 0.92))
vial = bpy.context.object; vial.name = "Vial"; vial.data.materials.append(soft_mat("M_Vial", (0.85, 0.92, 0.98), 0.15))
bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.0125, depth=0.01, location=(cx + 0.11, cy - 0.06, 0.947))
cap = bpy.context.object; cap.name = "VialCap"; cap.data.materials.append(soft_mat("M_VialCap", (0.2, 0.45, 0.9), 0.4))
for f in range(CUT, 2101, 30):
    reading = (f // 120) % 2 == 1          # alternates: reads the chart / looks up at the patient
    P, Rb = stand(D_, f, DP.x, DP.y, yaw=90, flex=3, spine=5, head=(34, 10) if reading else (16, -6), hands=False)
    key_relaxed(D_, f, P, Rb, sides="R")
# chart: a blank clipboard resting flat on his left palm at chest height (palm under, thumb on top, no other contact)
CB_SIZE = (0.23, 0.31, 0.012)
bpy.ops.mesh.primitive_cube_add(size=1); CB = bpy.context.object; CB.name = "Clipboard"; CB.scale = CB_SIZE
bpy.ops.object.transform_apply(scale=True); bv = CB.modifiers.new("B", 'BEVEL'); bv.width = 0.004; bv.segments = 2
CB.data.materials.append(soft_mat("M_Clipboard", (0.35, 0.22, 0.12), 0.5))
bpy.ops.mesh.primitive_plane_add(size=1); PAPER = bpy.context.object; PAPER.name = "ChartPaper"; PAPER.scale = (0.20, 0.26, 1)
bpy.ops.object.transform_apply(scale=True); PAPER.location = (0, -0.01, 0.0065); PAPER.parent = CB
PAPER.data.materials.append(soft_mat("M_Paper", (0.95, 0.95, 0.93), 0.7))
sc.frame_set(CUT); bpy.context.view_layer.update()
Pd = D[D_].matrix_world @ D[D_].pose.bones["root"].head
fwd_d = V((1, 0, 0)); left_d = V((0, 1, 0))
CB_M = Mloc(V((DP.x, DP.y, 0)) + fwd_d * 0.42 + left_d * 0.12 + V((0, 0, 1.17)), Rz(90) @ Rx(18))   # tilted up toward his eyes, well clear of his chest
CB.matrix_world = CB_M; bpy.context.view_layer.update()
under = CB_M @ V((0.0, 0.135, -0.006 - 0.010))     # board local +y edge is the one nearest him (Rz 90)          # palm under the board's near edge: the forearm stays below the board
place_hand(D[D_], "L", CUT, under, (CB_M.to_3x3() @ V((0, 0, 1))).normalized(), (CB_M.to_3x3() @ V((0, -1, 0))).normalized())
apply_pose(D[D_], "L", "hold_flat_object", CUT)
sc.frame_set(CUT); IKDL = D[D_].pose.bones["IK_hand.L"].matrix.copy()
shL = D[D_].matrix_world @ D[D_].pose.bones["upperarm01.L"].head
pbp = D[D_].pose.bones["Pole_elbow.L"]; nmp = "Pole_elbow.L"; polep = shL + V((-0.1, 0.45, -0.35))
pbp.location = RIG[D_].rest(nmp).to_3x3().inverted() @ (D[D_].matrix_world.inverted() @ polep - RIG[D_].BN[nmp].head_local)
RELCB = (D[D_].matrix_world @ IKDL).inverted() @ CB_M
for f in range(CUT, 2101, 30):
    M = IKDL.copy(); M.translation += V((0, 0, 0.008 * math.sin(f * 0.05))); key_ikhand_matrix(D_, "L", f, M, clamp=False)
    pbp.keyframe_insert("location", frame=f, group=nmp); apply_pose(D[D_], "L", "hold_flat_object", f)
for f in range(CUT, 2101):
    sc.frame_set(f); CB.matrix_world = (D[D_].matrix_world @ D[D_].pose.bones["IK_hand.L"].matrix) @ RELCB
    CB.keyframe_insert("location", frame=f); CB.rotation_mode = 'QUATERNION'; CB.keyframe_insert("rotation_quaternion", frame=f)
sc.frame_set(CUT); print("CHART reach err mm", round((bone_world(D_, "wrist.L").to_translation() - (D[D_].matrix_world @ IKDL).to_translation()).length * 1000, 1))

# doctor parked in the hospital all along (not on stage), fans hidden after the stage block (only in hospital... they stay)

# ================================================================= bake the bat in the hand (450-1296), rest after the drop
# bite correction: the wrist limits change the hand's real orientation, so move the hand until the REAL bat's head tip
# (carried by the actual wrist) lands on the lip point; tip kept on or in front of the lips (never inside the face)
sc.frame_set(450)
REL_W0 = (D[S].matrix_world @ D[S].pose.bones["wrist.R"].matrix).inverted() @ ((D[S].matrix_world @ D[S].pose.bones["IK_hand.R"].matrix) @ REL)
for f, (tgt, fwd_) in sorted(BITE_TIP.items()):
    for it in range(12):
        sc.frame_set(f); Mw = D[S].matrix_world @ D[S].pose.bones["wrist.R"].matrix
        tipw = (Mw @ REL_W0) @ V((0, 0, 0.054)); delta = tgt - tipw
        if delta.length < 0.002: break
        pb = D[S].pose.bones["IK_hand.R"]; M = D[S].pose.bones["wrist.R"].matrix.copy()     # target rotation = the hand's real rotation
        M.translation = pb.matrix.translation + D[S].matrix_world.inverted().to_3x3() @ delta
        key_ikhand_matrix(S, "R", f, M, clamp=False)
    print("BITE tip err mm", f, round(delta.length * 1000, 1))

# director (Phase 2): bat tip 6-8 mm off the lips through the bite, and nothing touches the face on the way in (f679).
# Measure the REAL clearance (posed bat mesh, carried by the actual wrist, vs the posed face surface) and move the hand
# along the face's forward axis: bite keys are solved to 7 mm, every other key from 640 to 840 is pushed out to >= 7 mm.
from mathutils.bvhtree import BVHTree
_body = bpy.data.objects[S + ".body"]
_arm = D[S].data.bones
_headb = {b.name for b in _arm if b.name == "head" or any(p.name == "head" for p in b.parent_recursive)}
_gname = {g.index: g.name for g in _body.vertex_groups}
def _is_head(v):
    gs = [g for g in v.groups if _gname[g.group] in _arm and g.weight > 0]
    return bool(gs) and _gname[max(gs, key=lambda g: g.weight).group] in _headb
_HEADV = {v.index for v in _body.data.vertices if _is_head(v)}
_HEADP = [p.index for p in _body.data.polygons if all(i in _HEADV for i in p.vertices)]
print("CLEAR face polys", len(_HEADP))
def face_bvh():
    mods = [(m, m.show_viewport) for m in _body.modifiers if m.type != 'ARMATURE']
    for m, _ in mods: m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    e = _body.evaluated_get(dg); me = e.to_mesh()
    vs = [_body.matrix_world @ v.co for v in me.vertices]
    polys = [list(me.polygons[i].vertices) for i in _HEADP]
    e.to_mesh_clear()
    for m, sv in mods: m.show_viewport = sv
    bpy.context.evaluated_depsgraph_get().update()
    return BVHTree.FromPolygons(vs, polys)
def bat_clear(f):
    """min distance (m) from the bat (placed on the real wrist) to the face surface at frame f"""
    sc.frame_set(f); Mw = D[S].matrix_world @ D[S].pose.bones["wrist.R"].matrix
    BAT.matrix_world = Mw @ REL_W0; bpy.context.view_layer.update()
    t = face_bvh(); dg = bpy.context.evaluated_depsgraph_get()
    e = BAT.evaluated_get(dg); me = e.to_mesh()
    d = min(t.find_nearest(BAT.matrix_world @ v.co)[3] for v in me.vertices)
    e.to_mesh_clear(); return d
def face_fwd(f):
    sc.frame_set(f); Mh = bone_world(S, "head")
    return (Mh.to_3x3() @ (RIG[S].rest("head").to_3x3().inverted() @ V((0, -1, 0)))).normalized()
CLEAR, CLEAR_MAX = 0.0072, 0.0080
def solve_clear(f, exact):
    for it in range(10):
        d = bat_clear(f)
        if d >= CLEAR - 0.0006 and (not exact or d <= CLEAR_MAX): break
        fw = face_fwd(f); pb = D[S].pose.bones["IK_hand.R"]; M = D[S].pose.bones["wrist.R"].matrix.copy()
        M.translation = pb.matrix.translation + D[S].matrix_world.inverted().to_3x3() @ (fw * (CLEAR - d + 0.0005))
        key_ikhand_matrix(S, "R", f, M, clamp=False)
    print("CLEAR mm", f, round(bat_clear(f) * 1000, 1))
_ck = sorted(set(BITE_TIP) | set(range(640, 842, 4)))
for f in _ck:
    solve_clear(f, f in BITE_TIP)
# verify every frame; key any frame still under 6 mm (in-betweens of the keys above)
for _pass in range(3):
    low = [f for f in range(640, 842) if bat_clear(f) < 0.006]
    print("CLEAR low frames pass", _pass, low)
    if not low: break
    for f in low: solve_clear(f, False)
bake_held(450, 867)
sc.frame_set(867); Mb = BAT.matrix_world.copy()
for f in range(868, 903, 3):
    u = min(1.0, (f - 867) / 33.0)
    p0 = Mb.to_translation(); p = p0.lerp(DROP, u); p.z = p0.z + (DROP.z - p0.z) * u * u
    R3 = Mb.to_3x3().to_quaternion().slerp((Rz(230) @ Rx(90)).to_quaternion(), smooth(u)).to_matrix()
    bat_key(f, Mloc(p, R3))
bat_key(CUT - 1, Mloc(DROP, Rz(230) @ Rx(90)))
bat_key(CUT, Mloc(V((HX, -3, -5)), Rz(0)))          # gone in the hospital

# ================================================================= the cut: CONSTANT interpolation across 1599->1600 for everything
def constant_at(obj, f):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for fc in ad.action.fcurves if hasattr(ad.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            if f - 40 <= kp.co.x < f: kp.interpolation = 'CONSTANT' if kp.co.x == max(k.co.x for k in fc.keyframe_points if k.co.x < f) else kp.interpolation
for n in NAMES + ["BatRig", "Blood"]:
    if n in D:
        o = D[n]
        if o.animation_data and o.animation_data.action:
            act = o.animation_data.action
            fcs = act.fcurves if hasattr(act, "fcurves") else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
            for fc in fcs:
                prev = [k for k in fc.keyframe_points if k.co.x < CUT]
                if prev: max(prev, key=lambda k: k.co.x).interpolation = 'CONSTANT'
# the stage singer pose holds until 1599: key everything at 1599 by re-evaluating is implicit in CONSTANT on the last key
sc.frame_start, sc.frame_end = 1, 2100
sc.render.fps = 60
print("ANIM done")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
