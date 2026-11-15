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
MIC = D["MicStand"]
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
sing_pose(171, bob=0.3)
for f, hd in ((200, (20, -14)), (240, (26, -18)), (275, (24, -12)), (300, (25, -16))):
    P, Rb = stand(S, f, 0.0, 0.03 * (f - 171) / 129, flex=4, spine=6, head=hd, hands=False)
    key_relaxed(S, f, P, Rb)
jaw(S, 1, 0); jaw(S, 60, 6); jaw(S, 90, 1); jaw(S, 120, 7); jaw(S, 150, 0); jaw(S, 200, 4); jaw(S, 300, 3)

# fans: in front of the stage, facing it, arms up cheering (fists), bobbing
FANS = {"Fan1": (-0.75, -3.75, 0.0), "Fan3": (0.55, -3.95, 8.0), "Fan4": (1.55, -3.65, -6.0)}
def fan_pose(n, f, x, y, yaw, ph, up):
    H = HUM[n]; bob = 0.5 + 0.5 * math.sin(ph)
    P, Rb = stand(n, f, x, y, yaw=180 + yaw, flex=-3, spine=-6, head=(-15, 0), dz=-0.03 * bob, hands=False)
    for s, sx in (("L", 1), ("R", -1)):
        sh = bw(n, P, Rb, rest_head(n, "upperarm01." + s))
        lift = up * (0.55 + 0.12 * math.sin(ph + (0 if s == "L" else 1.7)))
        W = sh + Rb @ V((0.10 * sx, -0.18, lift)); d = (Rb @ V((0.05 * sx, -0.2, 1))).normalized(); nn = (Rb @ V((0, -1, 0))).normalized()
        key_hand(n, s, f, W, d, nn, pole=sh + Rb @ V((0.5 * sx, 0.1, -0.3)))
        apply_pose(D[n], s, "power_fist", f)
for n, (x, y, yaw) in FANS.items():
    ph0 = random.random() * 6
    for i, f in enumerate(range(1, 1301, 15)):
        fan_pose(n, f, x, y, yaw, ph0 + i * 1.1, up=1.0 if f < 330 else 0.75)

# bat flight: thrown from behind the crowd (off screen), arcs over the fans, lands right-front of the singer,
# at a spot his right hand reaches from the crouch (computed from the crouch pose so the grip is real)
STEP = V((0.62, -0.12)); YAW = -14.0
def crouch(f, amt, head=(-10, 0)):
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
wings(446, up=-15); wings(1296, up=-15)
BR.key_rot("legs", 446, [("X", 0)]); BR.key_rot("legs", 470, [("X", -55)]); BR.key_rot("legs", 675, [("X", -55)]); BR.key_rot("legs", 695, [("X", 0)]); BR.key_rot("legs", 960, [("X", 0)]); BR.key_rot("legs", 985, [("X", -55)]); BR.key_rot("legs", 1296, [("X", -55)])   # legs hang free at the bite (curled legs read as a blob in the close-ups); BR.key_rot("legs", 1320, [("X", 0)])   # wings stay relaxed/drooping while held (a fold test swung them across his face)
BAT_REST = Mloc(LAND + V((0.02, 0.01, 0.026)), BAT_LIE)
bat_key(300, BAT_REST)

# ================================================================= B: pick it up (300-620)
# release the stand (hand back to relaxed), small step toward the bat, crouch, grip, rise, look at it
P, Rb = stand(S, 300, 0.0, 0.03, flex=4, spine=6, head=(25, -16), hands=False); key_relaxed(S, 300, P, Rb)
P, Rb = stand(S, 335, 0.0, 0.06, flex=2, spine=4, head=(16, -12), hands=False); key_relaxed(S, 335, P, Rb)
# step: shift to stand at (0.25, -0.15) turned slightly right (yaw -15) -> right foot moves first
def steps(f0):
    H = HUM[S]
    for s, fa, fb in (("R", f0, f0 + 22), ("L", f0 + 18, f0 + 40)):
        a = H.ankle[s]
        A0 = V((0, 0, 0)) + V((a.x, a.y - H.root_head.y, a.z)); B0 = V((STEP.x, STEP.y, 0)) + Rz(YAW) @ V((a.x, a.y - H.root_head.y, a.z))
        for k in range(0, 5):
            u = k / 4; f = round(fa + (fb - fa) * u)
            p = A0.lerp(B0, smooth(u)); p.z += 0.07 * math.sin(math.pi * u)
            key_foot_free(S, s, f, p, Rz(YAW * smooth(u)) @ Rx(-12 * math.sin(math.pi * u)))
        key_foot_free(S, s, fb + 1, B0, Rz(YAW))
steps(345)
for f, u in ((345, 0.0), (365, 0.5), (387, 1.0)):
    p = V((0, 0.06)).lerp(STEP, smooth(u)); p.y += 0.06 * math.sin(math.pi * u)   # steps right and slightly back, clear of the mic
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
# grip the bat body from above at 450
sc.frame_set(450)
bat_set(BAT_REST); bpy.context.view_layer.update()
bat_body = BAT_REST @ V((0, 0.0, -0.075))        # lower body / legs: keeps the hand well clear of his face at the bite
up_dir = (BAT_REST.to_3x3() @ V((0, -1, 0)))     # local -Y (face) is down when lying, so the back faces +Z
fd = (BAT_REST.to_3x3() @ V((1, 0, 0))).normalized()
gr = grip_object(D[S], "R", 450, D["Bat"], bat_body + V((0, 0, 0.045)), V((0, 0, -1)), finger_dir=fd)
print("GRIP bat", gr)
apply_pose(D[S], "R", "shield", 450); apply_pose(D[S], "R", "wrap_grip", 455, amount=0.85)     # fingers close once the hand is there round the bat's lower body (open-hand contact report above)
P, Rb = crouch(450, 1.0); key_relaxed(S, 450, P, Rb, sides="L")
apply_pose(D[S], "R", "shield", 432); apply_pose(D[S], "R", "shield", 446)      # open hand on the way down
sc.frame_set(450)
IKR_GRAB = D[S].pose.bones["IK_hand.R"].matrix.copy()
print("REACH err at grab (m):", round((bone_world(S, "wrist.R").to_translation() - (D[S].matrix_world @ IKR_GRAB).to_translation()).length, 4))
REL = (D[S].matrix_world @ IKR_GRAB).inverted() @ BAT_REST     # bat in the hand from here on
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
    key_ikhand_matrix(S, "R", f, hand_for_bat(Mb)); return Mb
# raise toward the mouth (620-700), jaw opens 680-700, bite 700-712, playful shake, hold
for f, hd in ((640, (8, 0)), (665, (4, 0))):
    P, Rb = head_frame(f, hd)
    u = (f - 620) / 45; bat_front(f, P, Rb, fwd=0.46 - 0.04 * u, up=0.08 + 0.14 * u, yaw=0, tilt=-10 - 30 * u)
jaw(S, 620, 2); jaw(S, 680, 3); jaw(S, 700, 16); jaw(S, 712, 9); jaw(S, 960, 9)
P, Rb = head_frame(690, (2, 0)); bat_at_mouth(690, depth=-0.07)
P, Rb = head_frame(700, (0, 0)); bat_at_mouth(700, depth=-0.010)
P, Rb = head_frame(712, (3, 0)); bat_at_mouth(712, depth=0.008)
for i, f in enumerate(range(730, 961, 18)):
    sh = 7 * math.sin(i * 1.6) if f < 880 else 0
    P, Rb = head_frame(f, (3 + 2 * math.sin(i), sh), side=2 * math.sin(i * 1.6))
    bat_at_mouth(f, depth=0.008, roll=sh * 0.6)

# ================================================================= D: pulls it away, shock (960-1280)
P, Rb = head_frame(972, (6, 0), flex=2, spine=4); bat_at_mouth(972, depth=-0.06)
for f, hd, yw in ((985, (16, -6), 0), (1010, (24, -8), 5), (1060, (27, -12), -8), (1120, (25, -7), 4), (1180, (28, -11), -4), (1240, (26, -8), 0), (1280, (26, -6), 2)):
    P, Rb = stand(S, f, STEP.x, STEP.y, yaw=YAW, flex=-2, spine=-4, head=hd, hands=False, feet=False)
    bat_front(f, P, Rb, fwd=0.38, up=0.0, yaw=yw, tilt=-20)
    # left hand comes up, open, in shock (not touching the face)
    sh = bw(S, P, Rb, rest_head(S, "upperarm01.L"))
    if f >= 1010:
        W = sh + Rb @ V((0.13, -0.27, -0.06)); key_hand(S, "L", f, W, (Rb @ V((-0.2, -0.3, 1))).normalized(), (Rb @ V((-0.3, -1, 0))).normalized(),
                                                       pole=sh + Rb @ V((0.4, 0.2, -0.4)))
        apply_pose(D[S], "L", "open_alarm", f)
    else:
        key_relaxed(S, f, P, Rb, sides="L")
jaw(S, 972, 4); jaw(S, 985, 7); jaw(S, 1010, 5); jaw(S, 1280, 5)
# light red trace at the right lip corner: a thin glossy streak on the chin, carried by the jaw, revealed 975-1010
def blood_streak():
    body = D[S + ".body"]; dg = bpy.context.evaluated_depsgraph_get(); sc.frame_set(1)
    pts = []
    for k in range(9):
        u = k / 8
        p_rest = LIPC_REST + V((-0.004 * u, 0.008 * u * u, -0.032 * u))
        pts.append(p_rest)
    me = bpy.data.meshes.new("Blood"); bm = bmesh.new(); ring = []
    for k, p in enumerate(pts):
        w = 0.0032 * (1 - 0.6 * (k / 8)) + 0.0008
        a = bm.verts.new(p + V((-w, -0.0035, 0))); b = bm.verts.new(p + V((w, -0.0035, 0))); ring.append((a, b))
    for (a, b), (c, d) in zip(ring, ring[1:]): bm.faces.new((a, b, d, c))
    bm.to_mesh(me); o = bpy.data.objects.new("Blood", me); sc.collection.objects.link(o)
    sw = o.modifiers.new("Wrap", 'SHRINKWRAP'); sw.target = body; sw.wrap_mode = 'OUTSIDE_SURFACE'; sw.offset = 0.0012
    o.parent = D[S]; o.parent_type = 'BONE'; o.parent_bone = "jaw"
    bpy.context.view_layer.update()
    o.matrix_world = Matrix.Identity(4) if False else o.matrix_world
    m = bpy.data.materials.new("M_BloodLight"); m.use_nodes = True; Pn = m.node_tree.nodes["Principled BSDF"]
    Pn.inputs["Base Color"].default_value = (0.55, 0.02, 0.03, 1); Pn.inputs["Roughness"].default_value = 0.3
    me.materials.append(m)
    return o
# parent-to-bone keeps the rest offset: compute with the rig at rest
for pb in D[S].pose.bones: pass
BLD = blood_streak()
sc.frame_set(1); bpy.context.view_layer.update()
Mj = bone_world(S, "jaw")
BLD.matrix_parent_inverse = Matrix.Identity(4)
BLD.matrix_world = Matrix.Identity(4)          # will be corrected below with the jaw's rest-relative transform
jb = D[S].pose.bones["jaw"]
# bone-parent space: matrix_world = arm @ pose_bone.matrix @ T(tail) @ parent_inverse @ basis -> set parent inverse so rest mesh coords stay put at rest
tailT = Matrix.Translation(V((0, jb.length, 0)))
BLD.matrix_parent_inverse = (D[S].matrix_world @ RIG[S].rest("jaw") @ tailT).inverted()
BLD.location = (0, 0, 0); BLD.rotation_euler = (0, 0, 0)
for f, hid in ((1, True), (984, False), (1600, True)):
    BLD.hide_render = BLD.hide_viewport = hid; BLD.keyframe_insert("hide_render", frame=f); BLD.keyframe_insert("hide_viewport", frame=f)

# ================================================================= E: drops it, bends over (1280-1600)
P, Rb = stand(S, 1290, STEP.x, STEP.y, yaw=YAW, flex=-2, spine=-4, head=(18, 0), hands=False, feet=False)
Mb = bat_front(1290, P, Rb, fwd=0.38, up=0.0, yaw=0, tilt=-20)
apply_pose(D[S], "R", "wrap_grip", 1290) if False else None
# release at 1296: fingers open, the bat falls to the deck by his feet
apply_pose(D[S], "R", "wrap_grip", 1296, amount=0.85)   # fingers stay closed on the bat until the release
apply_pose(D[S], "R", "open_alarm", 1300)
DROP = V((STEP.x, STEP.y, 0.026)) + Rz(YAW) @ V((0.12, -0.66, 0))   # in front of his feet, clear of both shoes and the stand base
def bake_held(f0, f1):
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        Mh = D[S].matrix_world @ D[S].pose.bones["IK_hand.R"].matrix
        bat_key(f, Mh @ REL)
# fall
for k, f in enumerate(range(1297, 1331, 3)):
    u = (f - 1297) / 33.0
    p0 = Mb.to_translation(); p = p0.lerp(DROP, u); p.z = p0.z + (DROP.z - p0.z) * u * u
    R3 = Mb.to_3x3().to_quaternion().slerp((Rz(200 + 30) @ Rx(90)).to_quaternion(), smooth(u)).to_matrix()
    BAT_FALL = Mloc(p, R3)
wings(1297, up=0); wings(1320, up=-12); wings(1335, up=-15)
P, Rb = stand(S, 1310, STEP.x, STEP.y, yaw=YAW, flex=0, spine=-2, head=(26, 0), hands=False, feet=False)
key_relaxed(S, 1310, P, Rb, sides="L")
W, d, nn = relaxed_hand(S, P, Rb, "R", fwd=0.15); key_hand(S, "R", 1325, W, d, nn, P=P, Rb=Rb); apply_pose(D[S], "R", "relaxed", 1325)
# bend over, hands on the thighs above the knees, breathing hard
def bend(f, amt, br=0.0):
    H = HUM[S]
    P = V((STEP.x, STEP.y + 0.10 * amt, H.root_head.z - 0.02 - 0.12 * amt)); Rb = body_R(YAW, 20 * amt)
    H.key_root(f, P, yaw=YAW, flex=20 * amt); H.key_spine(f, flex=(38 + 6 * br) * amt, head=(-10 + 8 * br, 0))
    return P, Rb
for f, a in ((1340, 0.0), (1370, 0.6), (1395, 1.0)):
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
for i, f in enumerate(range(1395, 1601, 25)):
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
        W = V((HX + a.x * 0.9, HIP.y - 0.86, 0))
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
            dirv = V((0.58 * a_, -1.0, 0.62 * b_ - 0.02)).normalized()
            k = 1.0 / math.sqrt((dirv.x / 0.060) ** 2 + (dirv.y / 0.100) ** 2 + (dirv.z / 0.064) ** 2)
            r_skin = 0.0
            for jx in (-0.006, 0.0, 0.006):
                for jz in (-0.006, 0.0, 0.006):
                    dj = (dirv + V((jx, 0, jz)) / 0.12).normalized(); hit = _bvh.ray_cast(Ce + dj * 0.4, -dj, 0.4)
                    if hit[0] is not None: r_skin = max(r_skin, (hit[0] - Ce).length)
            G[i, j] = bm.verts.new(Ce + dirv * max(k * (1 - 0.15 * r2), r_skin + 0.006 + 0.012 * (1 - r2)))
    for i in range(N_):
        for j in range(N_):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k_ in G for k_ in q): bm.faces.new([G[k_] for k_ in q])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    vmap = G
    me = bpy.data.meshes.new("OxygenMask"); bm.to_mesh(me)
    o = bpy.data.objects.new("OxygenMask", me); sc.collection.objects.link(o)
    so = o.modifiers.new("Sol", 'SOLIDIFY'); so.thickness = 0.0025; so.offset = 1
    o.modifiers.new("Sub", 'SUBSURF').levels = 1
    m = soft_mat("M_OxyMask", (0.72, 0.92, 0.84), rough=0.25)
    Pn = m.node_tree.nodes["Principled BSDF"]; Pn.inputs["Alpha"].default_value = 0.82
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    # tube from the bottom of the cup down over the chest to the bed side, and a thin elastic strap toward the ears
    cu = bpy.data.curves.new("OxyTube", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.006; cu.bevel_resolution = 3
    sp = cu.splines.new('BEZIER'); pts = [C + V((0, -0.035, -0.055)), C + V((0.02, -0.08, -0.20)), C + V((0.12, -0.10, -0.40)), C + V((0.28, -0.05, -0.55))]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    t = bpy.data.objects.new("OxyTube", cu); sc.collection.objects.link(t); cu.materials.append(soft_mat("M_Tube", (0.85, 0.95, 0.92), 0.3))
    cs = bpy.data.curves.new("OxyStrap", 'CURVE'); cs.dimensions = '3D'; cs.bevel_depth = 0.0025
    for sx in (-1, 1):
        s2 = cs.splines.new('BEZIER'); q = [C + V((0.045 * sx, -0.01, 0.0)), C + V((0.075 * sx, 0.05, 0.02)), C + V((0.080 * sx, 0.11, 0.035))]
        s2.bezier_points.add(len(q) - 1)
        for bp, p in zip(s2.bezier_points, q): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    st = bpy.data.objects.new("OxyStrap", cs); sc.collection.objects.link(st); cs.materials.append(soft_mat("M_Strap", (0.9, 0.95, 0.95), 0.5))
    bpy.data.objects.remove(st, do_unlink=True)   # strap hidden by the hair in reality; a free-floating strand read as a rod
    for ob in (o, t):     # Child Of the head bone (a prop, not a rig child), identity at rest
        c = ob.constraints.new('CHILD_OF'); c.target = D[S]; c.subtarget = "head"
        c.inverse_matrix = (D[S].matrix_world @ RIG[S].rest("head")).inverted()
        for f, hid in ((1, True), (CUT, False)):
            ob.hide_render = ob.hide_viewport = hid; ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
    print("MASK verts", len(vmap)); bpy.data.meshes.remove(me0)
oxygen_mask()
# doctor at the bed's right side (from the patient), facing the bed, syringe in the right hand, taps it
DP = V((HX - 0.78, 0.30))
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
    P, Rb = stand(D_, f, DP.x, DP.y, yaw=90, flex=4, spine=6, head=(16 if f < 1800 else 24, 8 if f < 1800 else 22), hands=False)
    key_relaxed(D_, f, P, Rb, sides="LR")

# doctor parked in the hospital all along (not on stage), fans hidden after the stage block (only in hospital... they stay)

# ================================================================= bake the bat in the hand (450-1296), rest after the drop
bake_held(450, 1296)
for k, f in enumerate(range(1297, 1334, 3)):
    u = min(1.0, (f - 1297) / 33.0)
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
