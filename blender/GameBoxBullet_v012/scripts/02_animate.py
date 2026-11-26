"""GameBoxBullet v012 stage B: staging, acting, the one bullet, the one box, the wall break, the ONE continuous camera.
blender -b base.blend --python 02_animate.py -- <out.blend> [blocking]
Built to the client's VO (same file as v010/v011, 21.4 s) from the start: beat frames = 1 + round(sec * 60), see beats.json.
VO (frames): A stray bullet 1 | ripped through 51 | the wall of his house 97-150 | flying straight for his chest 169-247 |
But he was holding his brand new video game collector's box 277-462 | The bullet slammed into it 497-588 |
The case cracked 603-651 | the discs shattered 675-730 | and layer by layer 755-817 | they ate up the bullet's energy 831-907 |
It stopped halfway through 941-1016 | buried inside the box 1039-1102 | His game collection 1137-1185 | just saved his life 1185-1263."""
import bpy, bmesh, sys, os, math, random, json
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline"))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; MODE = args[1] if len(args) > 1 else ""
random.seed(21)
END = 1311
O = bpy.data.objects
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail
def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M
def key_M(o, f, M):
    o.matrix_world = M
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
def euler_fix(o):
    """keep keyed euler rotations continuous (no 360-degree flips between keys)"""
    if not (o.animation_data and o.animation_data.action): return
    fcs = [fc for fc in iter_fcurves(o.animation_data.action) if fc.data_path == "rotation_euler"]
    for fc in fcs:
        prev = None
        for kp in fc.keyframe_points:
            if prev is not None:
                while kp.co.y - prev > math.pi: kp.co.y -= 2 * math.pi
                while kp.co.y - prev < -math.pi: kp.co.y += 2 * math.pi
            prev = kp.co.y
        fc.update()
def linear(o):
    if o.animation_data and o.animation_data.action:
        for fc in iter_fcurves(o.animation_data.action):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

HERO, SHOOT = O["Hero"], O["Shooter"]
HB = part(HERO, ".body"); SB = part(SHOOT, ".body")
SEAT_TOP = sc["SEAT_TOP"]; SEAT_FRONT_Y = sc["SEAT_FRONT_Y"]; WALL_T = sc["WALL_T"]
BW, BH, BD = sc["BOX_DIMS"]; IMP_LOCAL = Vector(sc["IMP_LOCAL"]); NW, ND, ZTOP = sc["NOTCH"]
LAY = json.loads(sc["LAYER_INFO"])
BOX = O["GameBoxSet"]; BUL = O["Bullet"]; GUN = O["Pistol"]; FLASH = O["MuzzleFlash"]; RING = O["EnergyRing"]

# ================================================================== rigs
RIG = {}
for r in (HERO, SHOOT):
    RIG[r.name] = make_human_ctrl(r); add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in "LR":
        lo = r.pose.bones["lowerarm01." + s_]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-30); lo.ik_max_x = R_(145)
HU = {n: Human(RIG[n]) for n in RIG}
HR = RIG["Hero"]; HH = HU["Hero"]; SR = RIG["Shooter"]; HS = HU["Shooter"]
# the shooter's gun hand: wrist solved by the IK target (no clamp fighting it)
for c in list(SHOOT.pose.bones["wrist.R"].constraints):
    if c.name == "HandLimit": SHOOT.pose.bones["wrist.R"].constraints.remove(c)

def hand_world(rig, s, f, W_wrist, fdir, palm, pole=None):
    Mi = rig.matrix_world.inverted(); R3 = Mi.to_3x3()
    HU[rig.name].key_hand(s, f, Mi @ Vector(W_wrist), R3 @ Vector(fdir), R3 @ Vector(palm), pole=None if pole is None else Mi @ Vector(pole))

# ================================================================== HERO: seated ON the sofa (pelvis on the seat, feet on the floor)
HIP_Y = SEAT_FRONT_Y + 0.20
HERO.location = (0.0, HIP_Y - HR.BN["upperleg01.L"].head_local.y, 0.0); HERO.rotation_euler = (0, 0, 0)
HERO.keyframe_insert("location", frame=1); HERO.keyframe_insert("rotation_euler", frame=1)
upd()
hip_rest_z = HR.BN["upperleg01.L"].head_local.z
# thigh thickness under the hip joint, measured on the body mesh (rest): lowest skin below the hip joint near the thigh axis
thz = [v.co.z for v in HB.data.vertices if abs(abs(v.co.x) - 0.10) < 0.035 and abs(v.co.y - 0.0) < 0.06 and hip_rest_z - 0.30 < v.co.z < hip_rest_z - 0.02]
UNDER = 0.085
SEAT_SINK = 0.0           # the seat cushion gives a little under him
DROP = hip_rest_z - (SEAT_TOP - SEAT_SINK + UNDER)
log("seated: hip rest z", round(hip_rest_z, 3), "drop", round(DROP, 3), "seat top", round(SEAT_TOP, 3))
ROOT0 = HR.BN["root"].head_local.copy()
# body acting curves (frame, flex fwd deg, twist deg, head pitch deg (+ = down), head yaw deg, root dy (+ = back))
BODY = [(1, 14, 0, 22, 4, 0.0), (120, 15, 3, 24, -2, 0.0), (220, 13, -3, 20, 3, 0.0), (300, 14, 2, 18, -3, 0.0), (380, 12, -2, 16, 2, 0.0),
        (440, 10, 0, 6, -2, 0.0), (480, 8, 0, -2, 0, 0.0), (519, 8, 0, -3, 0, 0.0), (530, 1, 0, -8, 0, 0.022), (552, 4, 0, 8, 2, 0.015),
        (603, 10, 0, 22, 0, 0.0), (680, 12, 2, 26, -3, 0.0), (760, 13, -2, 26, 3, 0.0), (840, 12, 0, 24, -7, 0.0), (860, 12, 0, 24, 7, 0.0),
        (880, 12, 0, 24, -6, 0.0), (900, 12, 0, 24, 2, 0.0), (960, 15, 3, 28, 4, 0.0), (1040, 16, 0, 28, -2, 0.0), (1100, 20, 0, 32, 0, 0.0),
        (1137, 14, 0, 14, 0, 0.0), (1165, 6, -2, -8, -10, 0.0), (1200, 8, 0, 0, -4, 0.0), (1228, 6, 0, 4, 2, 0.0), (1265, 4, 0, -2, 6, 0.0), (END, 4, 0, -2, 8, 0.0)]
bf = {k: pchip([(b[0], b[i]) for b in BODY]) for i, k in enumerate(("f", "flex", "tw", "hp", "hy", "dy")) if i}
def breath(f, amp=1.0, per=3.6):
    return amp * math.sin(2 * math.pi * (f / 60.0) / per)
def b_amp(f):
    # hard breathing after the hit, a long exhale on "saved his life"
    if 530 <= f <= 940: return 2.2
    if 1213 <= f <= 1290: return 3.0
    return 1.0
for f in list(range(1, END, 3)) + [END]:
    ba = b_amp(f); per = 2.4 if 530 <= f <= 940 else (4.5 if f >= 1213 else 3.6)
    HH.key_root(f, ROOT0 + Vector((0, bf["dy"](f), -DROP - 0.002 * (1 + breath(f, ba * 0.5, per)))), flex=0)
    HH.key_spine(f, flex=bf["flex"](f) + breath(f, ba * 0.8, per), twist=bf["tw"](f), head=(bf["hp"](f), bf["hy"](f)))
# feet flat on the floor in front of the seat, knees bent ~90 degrees
for s in "LR":
    sx = 1 if s == "L" else -1
    for f in (1, END):
        HR.key_world("IK_foot." + s, f, Matrix.Translation(Vector((sx * 0.03, -0.40, 0.0))) @ HR.rest("IK_foot." + s))
        n = "Pole_knee." + s; pb = HR.PB[n]; pb.location = Vector((0, 0, 0.45)); pb.keyframe_insert("location", frame=f, group=n)
log("hero body keyed")

# ================================================================== THE BOX: held in front of his chest (3.5 cm clear of the shirt)
def chest_frame(f):
    fs(f)
    sp = Wh(HERO, "spine04"); nk = Wh(HERO, "neck01")
    up = (nk - sp).normalized()
    side = (Wh(HERO, "upperarm01.L") - Wh(HERO, "upperarm01.R")).normalized()
    fwd = up.cross(side).normalized()   # points to his front (-Y at rest)
    if fwd.y > 0: fwd = -fwd
    return sp, up, side, fwd
# shirt front depth at chest height: measured on the posed top at frame 1
def front_depth(f, zc):
    fs(f); dg = bpy.context.evaluated_depsgraph_get()
    best = 9.0
    for ob in (O["Hero.top"], HB):
        ev_ = ob.evaluated_get(dg); me = ev_.to_mesh()
        for v in me.vertices:
            w = ob.matrix_world @ v.co
            if abs(w.x) < 0.15 and zc - 0.02 < w.z < zc + 0.16 and w.y > HIP_Y - 0.45: best = min(best, w.y)
        ev_.to_mesh_clear()
    return best
# box acting (frame, lift m, tilt deg (+ = top toward him), turn deg, x shift, push-back m)
BOXK = [(1, 0.0, 6, -6, 0.0, 0.0), (90, 0.01, 8, 5, 0.0, 0.0), (170, 0.005, 5, -4, 0.0, 0.0), (250, 0.012, 7, 6, 0.0, 0.0),
        (330, 0.02, 3, 0, 0.0, 0.0), (420, 0.02, 2, 0, 0.0, 0.0), (480, 0.015, 0, 0, 0.0, 0.0), (519, 0.015, 0, 0, 0.0, 0.0),
        (527, 0.02, -2, 0, 0.0, 0.016), (545, 0.015, 1, 0, 0.0, 0.01), (603, 0.0, 6, 0, 0.0, 0.0), (760, 0.0, 8, 2, 0.0, 0.0),
        (900, 0.0, 9, -2, 0.0, 0.0), (1000, 0.0, 10, 0, 0.0, 0.0), (1040, 0.0, 10, 0, 0.0, 0.0), (1105, -1.0, 12, 0, 0.0, 0.0),
        (1137, -1.0, 12, 0, 0.0, 0.0), (END, -1.0, 12, 0, 0.0, 0.0)]
bk = {k: pchip([(b[0], b[i]) for b in BOXK]) for i, k in enumerate(("f", "lift", "tilt", "turn", "dx", "push")) if i}
fs(1)
sp0, up0, side0, fwd0 = chest_frame(1)
BOX_ZC = Wh(HERO, "upperarm01.L").z - 0.115 - BH / 2        # box centre height: top 11.5 cm below the shoulders
YF = front_depth(1, BOX_ZC)
BOX_Y = YF - 0.060 - BD / 2
# lap pose: the box rests ON his thighs (bottom on the thigh tops), measured below
def thigh_top(f):
    fs(f); dg = bpy.context.evaluated_depsgraph_get(); best = -9.0
    for ob in (O["Hero.trousers"],):
        ev_ = ob.evaluated_get(dg); me = ev_.to_mesh()
        for v in me.vertices:
            w = ob.matrix_world @ v.co
            if abs(w.x) < 0.17 and BOX_Y - BD / 2 - 0.02 < w.y < BOX_Y + BD / 2 + 0.02: best = max(best, w.z)
        ev_.to_mesh_clear()
    return best
LAP_Z = thigh_top(1137) + 0.004
# held pose: the box bottom stays at least 2.5 cm above his thighs (never through the lap)
BOX_ZC = max(BOX_ZC, thigh_top(1) + 0.025 + BH / 2)
log("box: shirt front y", round(YF, 3), "box centre y", round(BOX_Y, 3), "z", round(BOX_ZC, 3), "lap: thigh top", round(LAP_Z, 3))
def box_M(f):
    lift = bk["lift"](f)
    if lift <= -0.5:
        zc = LAP_Z + BH / 2; yc = BOX_Y - 0.02
    elif lift < 0:
        u = -lift; zc = BOX_ZC * (1 - u) + (LAP_Z + BH / 2) * u; yc = BOX_Y - 0.02 * u
    else:
        zc = BOX_ZC + lift; yc = BOX_Y
    if 1040 < f < 1105:
        u = smooth((f - 1040) / 65.0); zc = BOX_ZC * (1 - u) + (LAP_Z + BH / 2) * u; yc = BOX_Y - 0.02 * u
    yc += bk["push"](f) * 0.6
    Rm = Matrix.Rotation(R_(bk["turn"](f)), 4, 'Z') @ Matrix.Rotation(R_(-bk["tilt"](f)), 4, 'X')
    # origin is the box bottom centre: rotate about the centre
    return Matrix.Translation(Vector((bk["dx"](f), yc, zc))) @ Rm @ Matrix.Translation(Vector((0, 0, -BH / 2)))
for f in range(1, END + 1, 2):
    key_M(BOX, f, box_M(f))
key_M(BOX, END, box_M(END))
log("box keyed")

# ---- hands: palms on the two side faces (back half of the box), fingers forward-up; every 2 frames
for f in list(range(1, END + 1, 2)) + [END]:
    Mb = box_M(f); R3 = Mb.to_3x3()
    for s in "LR":
        sx = 1 if s == "L" else -1
        pp = Mb @ Vector((sx * BW / 2, 0.004, BH / 2 + 0.005))
        # fingers run forward along the side face, in line with the forearm (no wrist bend that would turn them into the box)
        place_hand(HERO, s, f, pp, R3 @ Vector((-sx, 0, 0)), R3 @ Vector((0, -1.0, 0.12)).normalized(), skin=0.016)
        if f == 1 or f % 60 == 1:
            n = "Pole_elbow." + s; pb = HR.PB[n]
            pb.location = HR.rest(n).to_3x3().inverted() @ (Vector((sx * 0.16, 0.45, -0.55)) + HR.BN["upperarm01." + s].head_local - HR.BN[n].head_local)
            pb.keyframe_insert("location", frame=f, group=n)
for s in "LR":
    for f in (1, END):
        apply_pose(HERO, s, "flat_palm", f)
log("hands keyed")
if MODE == "blocking":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== THE BULLET PATH (one straight line from the muzzle to the impact point)
F_FIRE, F_WALL, F_EXIT, F_HIT = 10, 99, 104, 519
fs(F_HIT); upd()
P_IMP = box_M(F_HIT) @ IMP_LOCAL
H_WANT = Vector((0.26, 0.0, P_IMP.z + 0.12))
# the shooter stands on the sidewalk; iterate: line through the impact and the hole, his gun aimed along it
D = (P_IMP - H_WANT).normalized()
SH_Y = -10.15
def shooter_setup(D, f=1):
    yaw = math.atan2(D.x, -D.y)
    # body faces along D (rest faces -Y, so rotate by yaw)
    t = (SH_Y - H_WANT.y) / D.y; base = H_WANT + D * t
    pos = Vector((base.x + 0.30 * math.cos(yaw) - 0.0, SH_Y, 0.0))
    return yaw, pos
for it in range(3):
    yaw, spos = shooter_setup(D)
    SHOOT.matrix_world = Matrix.Translation(spos) @ Matrix.Rotation(yaw, 4, 'Z'); upd()
    fs(1)
    shR = Wh(SHOOT, "upperarm01.R")
    wrist_p = shR + D * 0.50 + Vector((0, 0, 0.02))
    side_v = Vector((0, 0, 1)).cross(D).normalized()       # points to his left
    hand_world(SHOOT, "R", 1, wrist_p, D + Vector((0, 0, -0.15)), side_v, pole=shR + Vector((0, 0, -0.5)) - side_v * 0.3)
    apply_pose(SHOOT, "R", "wrap_grip", 1)
    fs(1); upd()
    k1 = Wh(SHOOT, "finger2-1.R"); k5 = Wh(SHOOT, "finger5-1.R"); wr = Wh(SHOOT, "wrist.R"); mid = Wh(SHOOT, "finger3-2.R")
    across = (k1 - k5).normalized(); palm_c = (k1 + k5) / 2 * 0.6 + wr * 0.4
    inward = (mid - palm_c); inward = (inward - across * inward.dot(across)).normalized()
    grip_c = palm_c + inward * 0.018
    # gun frame: +Y along D (barrel), +Z up (slide on top); the grip (local origin) in the fist
    GM = frame_from(D, Vector((0, 0, 1)), grip_c)
    muzzle = GM @ Vector(GUN["muzzle"])
    D = (P_IMP - muzzle).normalized()
SHOOT.keyframe_insert("location", frame=1); SHOOT.keyframe_insert("rotation_euler", frame=1)
GUN.matrix_world = GM
c = GUN.constraints.new('CHILD_OF'); c.name = "Hand"; c.target = SHOOT; c.subtarget = "wrist.R"
c.inverse_matrix = W(SHOOT, "wrist.R").inverted(); c.set_inverse_pending = False
MUZ = muzzle.copy()
t_wall = (0.0 - MUZ.y) / D.y; H = MUZ + D * t_wall; HIN = MUZ + D * ((WALL_T - MUZ.y) / D.y)
L_TOT = (P_IMP - MUZ).length
log("path: muzzle", tuple(round(x, 2) for x in MUZ), "hole", tuple(round(x, 3) for x in H), "impact", tuple(round(x, 3) for x in P_IMP), "len", round(L_TOT, 2))
# shooter legs, body, other arm: standing, side-on aim, weight on the back foot; recoil kicks the hand up
for f in (1, 60):
    for s in "LR":
        sx = 1 if s == "L" else -1
        SR.key_world("IK_foot." + s, f, Matrix.Translation(Vector((sx * 0.06, (0.08 if s == "R" else -0.10), 0.0))) @ SR.rest("IK_foot." + s))
        n = "Pole_knee." + s; pb = SR.PB[n]; pb.location = Vector((0, 0, 0)); pb.keyframe_insert("location", frame=f, group=n)
for f, hp, hy in ((1, 2, 0), (9, 2, 0), (14, -3, 0), (30, 2, 4), (60, 4, 6)):
    HS.key_spine(f, flex=2, twist=-6, head=(hp, hy))
fs(1)
for f, dz, dback in ((1, 0, 0), (9, 0, 0), (12, 0.06, 0.035), (18, 0.03, 0.015), (30, 0.0, 0.0), (60, -0.02, 0.0)):
    wp = Wh(SHOOT, "upperarm01.R") + D * (0.50 - dback) + Vector((0, 0, 0.02 + dz))
    side_v = Vector((0, 0, 1)).cross(D).normalized()
    hand_world(SHOOT, "R", f, wp, D + Vector((0, 0, -0.15 + dz * 4)), side_v, pole=Wh(SHOOT, "upperarm01.R") + Vector((0, 0, -0.5)) - side_v * 0.3)
    apply_pose(SHOOT, "R", "wrap_grip", f)
fs(1)
for f in (1, 60):
    Mi = SHOOT.matrix_world
    wr = Wh(SHOOT, "upperleg01.L") + Mi.to_3x3() @ Vector((0.17, 0.02, -0.12))
    hand_world(SHOOT, "L", f, wr, Mi.to_3x3() @ Vector((0, -0.25, -1)), Mi.to_3x3() @ Vector((-1, 0.2, 0)),
               pole=Wh(SHOOT, "upperarm01.L") + Mi.to_3x3() @ Vector((0.45, 0.5, -0.3)))
    apply_pose(SHOOT, "L", "relaxed", f)
# muzzle flash (f10-13)
for f, s_ in ((9, 0.001), (10, 1.0), (11, 1.4), (12, 0.8), (13, 0.001)):
    FLASH.matrix_world = Matrix.Translation(MUZ + D * 0.03 * s_) @ frame_from(D, Vector((0, 0, 1)), (0, 0, 0)).to_3x3().to_4x4() @ Matrix.Diagonal((s_, s_ * 2.2, s_, 1))
    FLASH.keyframe_insert("location", frame=f); FLASH.keyframe_insert("rotation_euler", frame=f); FLASH.keyframe_insert("scale", frame=f)
log("shooter keyed")

# ---- bullet nose position along the line: s(f) (m from the muzzle); slow motion once it is inside the room
S_WALL = (H - MUZ).length; S_EXIT = (HIN - MUZ).length
SK = [(F_FIRE, 0.0), (20, 0.55), (40, 2.2), (70, 5.6), (F_WALL, S_WALL), (F_EXIT, S_EXIT + 0.06), (130, S_EXIT + 0.20),
      (200, S_EXIT + 0.55), (300, S_EXIT + 0.95), (420, L_TOT - 0.55), (F_HIT, L_TOT)]
s_of = pchip(SK)
# inside the box: depth of the nose behind the front face (m); layer breaks as the nose reaches each layer
DK = [(F_HIT, 0.0), (560, 0.004), (640, 0.0070), (690, 0.0238), (775, 0.0386), (810, 0.0533), (900, 0.0585), (965, 0.0600), (END, 0.0600)]
d_of = pchip(DK)
BL = 0.0164
fs(F_HIT); MB_HIT = box_M(F_HIT); D_LOC = (MB_HIT.to_3x3().inverted() @ D).normalized()
def bullet_M(f):
    """world matrix of the bullet (origin at its base, +Z = nose direction)"""
    if f < F_FIRE:
        nose = MUZ - D * 0.002; Rm = frame_from(D, Vector((0, 0, 1)), (0, 0, 0))
        # local +Z must be the flight direction: rotate the frame so z = D
        return Matrix.Translation(nose - D * BL) @ (Vector((0, 0, 1)).rotation_difference(D)).to_matrix().to_4x4()
    if f <= F_HIT:
        nose = MUZ + D * s_of(f)
        return Matrix.Translation(nose - D * BL) @ (Vector((0, 0, 1)).rotation_difference(D)).to_matrix().to_4x4()
    Mb = box_M(f); nose_l = IMP_LOCAL + D_LOC * d_of(f)
    Rl = (Vector((0, 0, 1)).rotation_difference(D_LOC)).to_matrix().to_4x4()
    return Mb @ Matrix.Translation(nose_l - D_LOC * BL) @ Rl
for f in range(1, END + 1):
    BUL.matrix_world = bullet_M(f)
    BUL.keyframe_insert("location", frame=f); BUL.keyframe_insert("rotation_euler", frame=f)
euler_fix(BUL)
def nose_w(f):
    return bullet_M(f) @ Vector((0, 0, BL))
log("bullet keyed")

# ================================================================== WALL BREAK: hole decals, splinters out, drywall chips into the room (slow motion)
def key_hole(name, f, P, n_out):
    o = O[name]
    for ff, s_ in ((f - 1, 0.001), (f, 0.6), (f + 2, 1.0)):
        o.matrix_world = Matrix.Translation(P + n_out * 0.0015) @ (Vector((0, 0, 1)).rotation_difference(n_out)).to_matrix().to_4x4() @ Matrix.Diagonal((s_, s_, s_, 1))
        o.keyframe_insert("location", frame=ff); o.keyframe_insert("rotation_euler", frame=ff); o.keyframe_insert("scale", frame=ff)
key_hole("WallHole_out", F_WALL, H + Vector((0, -0.016, 0)), Vector((0, -1, 0)))
key_hole("WallHole_in", F_EXIT, HIN, Vector((0, 1, 0)))
rr = random.Random(7)
for side in (0, 1):
    for k in range(14):
        o = O["Chip_%d_%02d" % (side, k)]
        f0 = F_WALL if side == 0 else F_EXIT
        P0 = (H + Vector((0, -0.017, 0))) if side == 0 else HIN
        if side == 0:
            v = Vector((rr.uniform(-0.6, 0.6), rr.uniform(-1.5, -0.6), rr.uniform(-0.2, 0.9))) * 0.020   # m per frame (outside: fast)
            g = -0.0009
        else:
            v = Vector((rr.uniform(-0.5, 0.5), rr.uniform(0.4, 1.2), rr.uniform(-0.1, 0.6))) * 0.0028    # inside: slow motion
            g = -0.000018
        rot0 = Euler((rr.uniform(0, 6), rr.uniform(0, 6), rr.uniform(0, 6))); spin = Vector((rr.uniform(-0.2, 0.2), rr.uniform(-0.2, 0.2), rr.uniform(-0.2, 0.2))) * (1 if side == 0 else 0.06)
        landed = None
        for f in [f0 - 1] + list(range(f0, END + 1, 3)):
            if f < f0:
                o.matrix_world = Matrix.Translation(P0) @ Matrix.Diagonal((0.001, 0.001, 0.001, 1)); o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f); continue
            t = f - f0
            p = P0 + v * t + Vector((0, 0, 0.5 * g * t * t))
            if p.z < 0.004:
                if landed is None: landed = p.copy(); landed.z = 0.004
                p = landed
            if side == 0 and f > 150:
                break
            o.location = p; o.rotation_euler = Euler((rot0.x + spin.x * min(t, 400), rot0.y + spin.y * min(t, 400), rot0.z + spin.z * min(t, 400)))
            o.scale = (1, 1, 1)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f); o.keyframe_insert("scale", frame=f)
        if side == 0:
            key_vis([o], 1, True); key_vis([o], 152, False)
log("wall break keyed")

# ================================================================== IMPACT + LAYERS: crack decal (keyed radius), hole, energy rings, chunks and shards
art = bpy.data.materials["M_BoxArt"].node_tree.nodes
for f, r_ in ((1, 0.0), (F_HIT - 1, 0.0), (F_HIT, 0.006), (F_HIT + 12, 0.022), (603, 0.026), (612, 0.03), (650, 0.075), (700, 0.085), (END, 0.085)):
    art["CrackRadius"].outputs[0].default_value = r_; art["CrackRadius"].outputs[0].keyframe_insert("default_value", frame=f)
for f, r_ in ((1, 0.0), (F_HIT - 1, 0.0), (F_HIT, 0.0058), (END, 0.0058)):
    art["HoleRadius"].outputs[0].default_value = r_; art["HoleRadius"].outputs[0].keyframe_insert("default_value", frame=f)
def ring_at(f0, P_loc, n_loc, r_max, dur=22):
    """the energy ring expands from P (box local) over dur frames; parented to the box (follows it)"""
    keys = []
    for k in range(0, dur + 1, 2):
        u = k / dur; s_ = 0.25 + (r_max / 0.02) * u
        keys.append((f0 + k, s_ * (1.0 - 0.85 * u)))
    return keys
RING.parent = BOX
ring_keys = []
def key_ring(f0, P_loc, axis_loc, r_max, dur=22):
    Rl = (Vector((0, 0, 1)).rotation_difference(axis_loc)).to_matrix().to_4x4()
    RING.matrix_parent_inverse = Matrix.Identity(4)
    RING.matrix_basis = Matrix.Translation(P_loc) @ Rl @ Matrix.Diagonal((0.001, 0.001, 0.001, 1))
    RING.keyframe_insert("location", frame=f0 - 1); RING.keyframe_insert("rotation_euler", frame=f0 - 1); RING.keyframe_insert("scale", frame=f0 - 1)
    for k in range(0, dur + 1, 2):
        u = k / dur; s_ = (0.3 + (r_max / 0.02 - 0.3) * u) * (1 if k < dur else 0.001)
        RING.matrix_basis = Matrix.Translation(P_loc) @ Rl @ Matrix.Diagonal((s_, s_, s_ * (1 - 0.7 * u), 1))
        RING.keyframe_insert("location", frame=f0 + k); RING.keyframe_insert("rotation_euler", frame=f0 + k); RING.keyframe_insert("scale", frame=f0 + k)
key_ring(F_HIT, IMP_LOCAL + Vector((0, -0.004, 0)), Vector((0, 1, 0)), 0.06, dur=26)
rr = random.Random(9)
BREAKS = []
for i, li in enumerate(LAY):
    depth_front = li["y0"] - (-BD / 2)
    fb = None
    for f in range(F_HIT, END + 1):
        if d_of(f) >= depth_front: fb = f; break
    if fb is None: continue
    BREAKS.append((i, fb)); log("layer", li["name"], "breaks at", fb)
    if fb > F_HIT + 30:
        key_ring(fb, Vector((0, (li["y0"] + li["y1"]) / 2, ZTOP + 0.002)), Vector((0, 0, 1)), 0.035 - 0.005 * i, dur=24)
    # the two chunk halves split, flip up and out over the side, then drop away
    for cn in li["chunks"]:
        o = O[cn]; sx = 1 if cn.endswith("L") else -1
        base = o.matrix_basis.copy()
        piv = Vector((sx * NW / 4, (li["y0"] + li["y1"]) / 2, ZTOP - ND / 2))
        v = Vector((sx * rr.uniform(0.0014, 0.0022), rr.uniform(-0.0006, 0.0006), rr.uniform(0.0022, 0.0032)))
        g = -0.00005; spin = sx * rr.uniform(0.05, 0.09)
        o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1)
        o.keyframe_insert("location", frame=fb); o.keyframe_insert("rotation_euler", frame=fb)
        for k in range(2, 62, 2):
            dp = v * k + Vector((0, 0, 0.5 * g * k * k))
            Rk = Matrix.Translation(piv + dp) @ Matrix.Rotation(spin * k, 4, 'Y') @ Matrix.Translation(-piv)
            o.matrix_basis = Rk @ base
            o.keyframe_insert("location", frame=fb + k); o.keyframe_insert("rotation_euler", frame=fb + k)
        o.matrix_basis = base
        key_vis([o], 1, True); key_vis([o], fb + 62, False)
    # shards / flakes from inside the chunk
    for k in range(10):
        nm = "Shard_%s_%d" % (li["name"].split("_")[1], k)
        o = O.get(nm)
        if not o: continue
        p0 = o.location.copy()
        v = Vector((rr.uniform(-0.0016, 0.0016), rr.uniform(-0.0009, 0.0009), rr.uniform(0.0015, 0.0035)))
        g = -0.00006; spin = Vector((rr.uniform(-0.3, 0.3), rr.uniform(-0.3, 0.3), rr.uniform(-0.3, 0.3)))
        o.keyframe_insert("location", frame=1); o.keyframe_insert("rotation_euler", frame=1); o.keyframe_insert("location", frame=fb)
        for kk in range(2, 56, 3):
            o.location = p0 + v * kk + Vector((0, 0, 0.5 * g * kk * kk))
            o.rotation_euler = Euler((spin.x * kk, spin.y * kk, spin.z * kk))
            o.keyframe_insert("location", frame=fb + kk); o.keyframe_insert("rotation_euler", frame=fb + kk)
        key_vis([o], 1, True); key_vis([o], fb + 56, False)
# shards of the layers that never break stay hidden inside their chunk (they are inside the solid chunk; never visible)
broken = {LAY[i]["name"] for i, _ in BREAKS}
log("broken layers", sorted(broken))

# ================================================================== FACES: blinks, smile, startle, relief (numeric axis finding)
def lid_sign(rig, s):
    pb = rig.pose.bones["orbicularis03." + s]; upd()
    t0 = Wt(rig, pb.name).z; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20)); upd(); t1 = Wt(rig, pb.name).z
    pb.rotation_quaternion = Quaternion(); upd()
    return 1.0 if t1 < t0 else -1.0
def blinks(rig, frames, base_keys):
    for s in "LR":
        n = "orbicularis03." + s
        if n not in rig.pose.bones: continue
        sg = lid_sign(rig, s); pb = rig.pose.bones[n]
        def lid(f, ang):
            pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
        for f, a_ in base_keys: lid(f, a_)
        for bf_ in frames:
            cur = 0.0
            for f, a_ in base_keys:
                if f <= bf_: cur = a_
            lid(bf_, cur); lid(bf_ + 4, 24); lid(bf_ + 7, 24); lid(bf_ + 13, cur)
def corner_axis(rig, bone, want):
    pb = rig.pose.bones[bone]; upd(); base = Wt(rig, bone); best = None
    for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
        for sg in (1, -1):
            pb.rotation_quaternion = Quaternion(ax, R_(12 * sg)); upd()
            d = rig.matrix_world.inverted().to_3x3() @ (Wt(rig, bone) - base)
            v = d.dot(want)
            if best is None or v > best[0]: best = (v, ax, sg)
    pb.rotation_quaternion = Quaternion(); upd()
    return best
def expression(rig, keys, bones_want):
    for bone, (want, deg) in bones_want.items():
        if bone not in rig.pose.bones: continue
        _, ax, sg = corner_axis(rig, bone, Vector(want))
        pb = rig.pose.bones[bone]
        for f, amt in keys:
            pb.rotation_quaternion = Quaternion(ax, R_(deg * sg * amt)); pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)
def eyes(rig, R, f0, f1, step=40, amp=(3, 5), seed=2):
    r_ = random.Random(seed)
    for f in range(f0, f1, step):
        a_, b_ = r_.uniform(-amp[0], amp[0]), r_.uniform(-amp[1], amp[1])
        for s in "LR": R.key_rot("eye." + s, f, [("X", a_), ("Z", b_)])
SMILE = {"risorius03.L": ((1, 0, 0.6), 14), "risorius03.R": ((-1, 0, 0.6), 14), "levator05.L": ((0.3, 0, 1), 10), "levator05.R": ((-0.3, 0, 1), 10),
         "oris04.L": ((1, 0, 0.5), 10), "oris04.R": ((-1, 0, 0.5), 10)}
fs(1)
# eyes wide (lids slightly up = negative), blink on the hit, relief at the end
blinks(HERO, [70, 190, 300, 410, 522, 640, 760, 880, 990, 1100, 1180, 1240],
       [(1, 0), (470, 0), (500, -6), (519, -8), (700, -5), (940, -2), (1213, 3), (1260, 0)])
expression(HERO, [(1, 0.35), (170, 0.75), (300, 0.9), (420, 0.7), (470, 0.0), (519, 0.0), (1200, 0.0), (1235, 0.5), (1275, 0.9), (END, 0.95)], SMILE)
if "jaw" in HERO.pose.bones:
    _, ax, sg = corner_axis(HERO, "jaw", Vector((0, 0, -1)))
    pb = HERO.pose.bones["jaw"]
    for f, a_ in ((1, 0), (470, 0), (500, 3), (525, 7), (560, 5), (640, 4), (760, 3), (900, 2), (1000, 1), (1213, 1), (1230, 5), (1260, 2), (1290, 0), (END, 0)):
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
eyes(HERO, HR, 1, 440, step=45, amp=(2, 4), seed=4)
eyes(HERO, HR, 560, 1130, step=38, amp=(2, 3), seed=5)
eyes(SHOOT, SR, 1, 60, step=30, amp=(1, 2), seed=6)
blinks(SHOOT, [30], [(1, 4)])
# brows up on the startle (levator / frontal bones if present)
for bn in ("levator03.L", "levator03.R"):
    pass
log("faces keyed")

# ================================================================== CAMERA: ONE continuous move (pchip through framings; level horizon; no cuts)
fs(1)
def face_pt(f):
    fs(f); return Wh(HERO, "head") + (Wt(HERO, "head") - Wh(HERO, "head")) * 0.35
def box_c(f): return box_M(f) @ Vector((0, 0, BH / 2))
def box_top(f): return box_M(f) @ Vector((0, 0, BH))
def notch_pt(f): return box_M(f) @ Vector((0, IMP_LOCAL.y + d_of(f) * 0.5 + 0.01, ZTOP - 0.008))
SH_FACE = Wh(SHOOT, "head") + Vector((0, 0, 0.06)); fs(1)
GUN_P = GUN.matrix_world.translation.copy()
side_r = Vector((0, 0, 1)).cross(D).normalized() * -1          # to the right of the flight (+X-ish)
WINC = Vector(((sc["WIN"][0] + sc["WIN"][1]) / 2, 0.0, 1.40))
CK = []    # (frame, position, aim, lens)
def ck(f, p, a_, lens=35): CK.append((f, Vector(p), Vector(a_), lens))
# 1-40: the shooter (face, the gun, the flash), then the camera swings onto the bullet
sh_fwd = D.copy(); sh_fwd.z = 0; sh_fwd.normalize()
ck(1, SH_FACE + sh_fwd * 1.15 + side_r * 0.85 + Vector((0, 0, -0.10)), (SH_FACE + GUN_P) / 2 + Vector((0, 0, -0.05)), 32)
ck(9, SH_FACE + sh_fwd * 1.10 + side_r * 0.80 + Vector((0, 0, -0.10)), (SH_FACE + GUN_P) / 2 + Vector((0, 0, -0.04)), 32)
ck(22, nose_w(22) + side_r * 0.55 - D * 0.35 + Vector((0, 0, 0.10)), nose_w(22) + D * 0.6, 34)
for f in range(34, 92, 6):
    ck(f, nose_w(f) + side_r * 0.075 - D * 0.05 + Vector((0, 0, 0.022)), nose_w(f) - D * 0.006, 38)
ck(96, H + side_r * 0.22 + Vector((0, -0.40, 0.06)), H + Vector((0, 0, 0.0)), 34)
ck(104, H + side_r * 0.30 + Vector((0, -0.75, 0.12)), H, 32)
ck(118, WINC + Vector((0.0, -0.62, 0.0)), WINC + Vector((-0.10, 1.0, -0.15)), 28)
ck(134, WINC + Vector((0.0, 0.05, -0.02)), WINC + Vector((-0.25, 1.0, -0.25)), 28)
ck(152, nose_w(152) + Vector((0.28, -0.10, 0.10)), nose_w(152), 30)
for f in (178, 205, 232, 258):
    u_ = (face_pt(f) - nose_w(f)).normalized()
    ck(f, nose_w(f) - u_ * 0.11 + side_r * 0.035 + Vector((0, 0, 0.012)), nose_w(f) + u_ * 0.30, 30)
# 277-470: past the bullet to a front 3/4 medium of him with the box (logo on the box front readable 300-440)
ck(285, box_c(285) + Vector((0.40, -0.80, 0.22)), (face_pt(285) + box_c(285)) / 2, 32)
ck(330, box_c(330) + Vector((0.22, -0.78, 0.18)), (face_pt(330) + box_c(330)) / 2 + Vector((0, 0, -0.03)), 34)
ck(380, box_c(380) + Vector((0.08, -0.72, 0.16)), (face_pt(380) + box_c(380)) / 2 + Vector((0, 0, -0.03)), 34)
ck(430, box_c(430) + Vector((0.18, -0.70, 0.15)), (face_pt(430) + box_c(430)) / 2, 34)
# 470-600: around to his right side profile; the bullet crosses frame left -> right and hits on "slammed" (519)
ck(478, box_c(478) + Vector((0.62, -0.45, 0.14)), (face_pt(478) + box_c(478)) / 2 + Vector((0, -0.08, 0)), 32)
ck(505, box_c(505) + Vector((0.72, -0.12, 0.12)), (face_pt(505) + box_c(505)) / 2 + Vector((0, -0.10, 0)), 32)
ck(540, box_c(540) + Vector((0.66, -0.05, 0.10)), (face_pt(540) + box_c(540)) / 2 + Vector((0, -0.06, 0)), 33)
ck(585, box_c(585) + Vector((0.50, -0.30, 0.10)), (face_pt(585) + box_c(585)) / 2 + Vector((0, -0.04, 0)), 33)
# 603-674 "the case cracked": in front of the box, low; the crack spreads; his face above the box
ck(615, box_c(615) + Vector((0.12, -0.56, 0.20)), (box_top(615) + face_pt(615)) / 2 + Vector((0, 0, -0.06)), 36)
ck(650, box_c(650) + Vector((-0.06, -0.50, 0.22)), (box_top(650) + face_pt(650)) / 2 + Vector((0, 0, -0.07)), 38)
# 675-893: up over the open top: chunks burst, disc shards glitter, the bullet ploughs layer by layer
ck(690, box_top(690) + Vector((0.05, -0.22, 0.20)), notch_pt(690), 40)
ck(730, box_top(730) + Vector((-0.10, -0.18, 0.19)), notch_pt(730), 42)
ck(775, box_top(775) + Vector((-0.14, -0.10, 0.17)), notch_pt(775), 42)
ck(815, box_top(815) + Vector((0.12, -0.12, 0.18)), notch_pt(815), 42)
ck(855, box_c(855) + Vector((0.30, -0.62, 0.30)), (face_pt(855) + box_top(855)) / 2, 34)
ck(905, box_c(905) + Vector((0.12, -0.66, 0.28)), (face_pt(905) + box_top(905)) / 2, 34)
# 941-1092 "stopped halfway, buried inside": close orbit on the stopped bullet in the open channel, back half intact
ck(950, box_top(950) + Vector((0.16, -0.10, 0.15)), notch_pt(950), 44)
ck(990, box_top(990) + Vector((0.18, 0.02, 0.16)), notch_pt(990), 46)
ck(1030, box_top(1030) + Vector((0.06, -0.15, 0.18)), notch_pt(1030), 44)
# 1060-1311: pull out as he lowers the box onto his lap; he looks up at the hole, exhales, smiles at us; logo poster behind him
ck(1075, box_c(1075) + Vector((0.28, -0.70, 0.34)), (face_pt(1075) + box_c(1075)) / 2, 32)
ck(1120, face_pt(1120) + Vector((0.42, -0.92, -0.08)), (face_pt(1120) + box_c(1120)) / 2 + Vector((0, 0, 0.04)), 30)
ck(1160, face_pt(1160) + Vector((0.30, -0.98, -0.02)), (face_pt(1160) + box_c(1160)) / 2 + Vector((0, 0, 0.08)), 30)
ck(1210, face_pt(1210) + Vector((0.18, -0.95, 0.0)), face_pt(1210) + Vector((0, 0.0, -0.12)), 30)
ck(1260, face_pt(1260) + Vector((0.10, -0.85, 0.02)), face_pt(1260) + Vector((0, 0.0, -0.10)), 32)
ck(END, face_pt(END) + Vector((0.06, -0.80, 0.03)), face_pt(END) + Vector((0, 0.0, -0.10)), 33)
CK.sort(key=lambda k: k[0])
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.clip_start = 0.004; cam_d.dof.use_dof = False
yaws = []; prev = None
for f, p, a_, l_ in CK:
    d = a_ - p; yw = math.atan2(d.y, d.x)
    if prev is not None:
        while yw - prev > math.pi: yw -= 2 * math.pi
        while yw - prev < -math.pi: yw += 2 * math.pi
    yaws.append(yw); prev = yw
fx = pchip([(k[0], k[1].x) for k in CK]); fy = pchip([(k[0], k[1].y) for k in CK]); fz = pchip([(k[0], k[1].z) for k in CK])
fyaw = pchip([(k[0], yaws[i]) for i, k in enumerate(CK)])
fpit = pchip([(k[0], math.atan2((k[2] - k[1]).z, (k[2] - k[1]).to_2d().length)) for k in CK])
flen = pchip([(k[0], k[3]) for k in CK])
maxstep = 0.0; prev_y = None
for f in range(1, END + 1):
    p = Vector((fx(f), fy(f), fz(f))); yw = fyaw(f); pt = fpit(f)
    CAM.location = p; CAM.rotation_euler = (math.pi / 2 + pt, 0, yw - math.pi / 2)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_euler", frame=f)
    cam_d.lens = flen(f); cam_d.keyframe_insert("lens", frame=f)
    if prev_y is not None: maxstep = max(maxstep, abs(math.degrees(yw - prev_y)))
    prev_y = yw
log("camera keyed; max yaw step deg/frame", round(maxstep, 1))
# eye catchlight that rides with the camera (glossy only, small)
cl_d = bpy.data.lights.new("Catchlight", 'POINT'); cl_d.energy = 1.5; cl_d.shadow_soft_size = 0.02
CL = bpy.data.objects.new("Catchlight", cl_d); sc.collection.objects.link(CL); CL.parent = CAM; CL.location = (0.05, 0.08, 0.0)
try:
    CL.visible_diffuse = False; CL.visible_transmission = False; CL.visible_volume_scatter = False
except Exception: pass

# ================================================================== VO, output, quaternion continuity, save
try:
    se = sc.sequence_editor_create()
    vo = os.path.join(HERE, "..", "GameBoxBullet_v012_VO.mp3")
    coll = se.strips if hasattr(se, "strips") else se.sequences
    st = coll.new_sound("VO", os.path.abspath(vo), channel=1, frame_start=1)
    log("VO strip", st.frame_final_start, st.frame_final_end)
except Exception as e:
    log("vo strip failed", e)
def quat_continuity(obj):
    groups = {}
    if not obj.animation_data or not obj.animation_data.action: return 0
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        idx = [{kp.co.x: kp for kp in ch[i].keyframe_points} for i in range(4)]
        prev = None
        for fr in frames:
            kps = [idx[i].get(fr) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c_ in ch.values(): c_.update()
    return nfix
log("quat flips fixed", [quat_continuity(r) for r in (HERO, SHOOT)])
for o in (BOX, CAM):
    euler_fix(o)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
sc.frame_start, sc.frame_end = 1, END
sc.render.filepath = "//render/GameBoxBullet_v012_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc["PATH"] = json.dumps(dict(muzzle=list(MUZ), hole=list(H), hole_in=list(HIN), impact=list(P_IMP), breaks=BREAKS))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
open(OUT + ".log.txt", "w").write("\n".join(LOG))
print("ANIM_OK", OUT)
