"""FrozenTearsGun v011 stage B: staging, acting, tears, the freezing and firing, the memory, the one continuous camera.
blender -b base.blend --python 02_animate.py -- <out.blend> [stop_after]
Built on the client's VO (v010 recording, 27.0 s) from the start; beat frames = 1 + round(seconds*60) of the VO words (vo_words.json).
Frames 1-1655."""
import bpy, bmesh, sys, os, math, random, json
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline"))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; STOP = args[1] if len(args) > 1 else ""
random.seed(13)
END = 1655
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
def lerp(a, b, t): return a + (b - a) * t
def const_interp(obj, path_sub=None):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            if path_sub is None or path_sub in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def linear_interp(obj, path_sub=None):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            if path_sub is None or path_sub in fc.data_path:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

INV, MEN = O["Inventor"], O["Mentor"]
IB, MB = part(INV, ".body"), part(MEN, ".body")
GUN = O["GUN"]; VALVE = O["G_Valve"]; TRIG = O["G_TriggerPivot"]; SPRING = O["G_Spring"]; PLUNGER = O["G_Plunger"]
BENCH_TOP = sc["BENCH_TOP"]; SEAT_Z = sc["SEAT_Z"]; DESK_TOP = sc["DESK_TOP"]; TGT_C = Vector(sc["TGT_C"])
GLASSES = [o for o in O if o.get("glasses")]

# ================================================================== the schedule (VO frames: 1 + round(t*60))
VO = json.load(open(os.path.join(HERE, "vo_words.json")))
def wf(i): return 1 + round(VO[i][0] * 60)
F_TEARS = 75; F_GUN = 227; F_VALVE = 278; F_CO2 = 345; F_BLAST = 408; F_FREEZE = 497; F_ICE = 600
F_PULL = 651; F_TRIG = 669; F_SPRING = 720; F_FIRES = 737; F_BULLETS = 818
F_YOUSEE = 883; F_MENTOR = 995; F_TEARS2 = 1028; F_UPSET = 1118; F_WISHED = 1195; F_SHOOT1 = 1242; F_BUILT = 1315
F_FINISHED = 1413; F_HERMENTOR = 1488; F_LET = 1548; F_SHOOT2 = 1598; F_HIM = 1596
F_INV_OFFICE = 760; F_INV_BACK = 1262; F_MEN_IN = 800; F_MEN_RANGE = 1400

# ================================================================== rigs
RIG = {}
for r in (INV, MEN):
    RIG[r.name] = make_human_ctrl(r); add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in "LR":
        for c in list(r.pose.bones["wrist." + s_].constraints):
            if c.name == "HandLimit": r.pose.bones["wrist." + s_].constraints.remove(c)
        lo = r.pose.bones["lowerarm01." + s_]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-30); lo.ik_max_x = R_(145)
HU = {n: Human(RIG[n]) for n in RIG}
IR, MR = RIG[INV.name], RIG[MEN.name]; IH, MH = HU[INV.name], HU[MEN.name]
def key_pole(rig, side, f, pole_world):
    R = RIG[rig.name]; n = "Pole_elbow." + side; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (Vector(pole_world) - R.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)
def hand_world(rig, s, f, W_wrist, fdir, palm, pole=None):
    HU[rig.name].key_hand(s, f, Vector(W_wrist), Vector(fdir), Vector(palm), pole=None if pole is None else Vector(pole))
def copy_key(rig, bone, f_src, f_dst):
    """re-key a bone's current (evaluated at f_src) pose channels at f_dst"""
    fs(f_src); pb = rig.pose.bones[bone]
    for ch in ("location", "rotation_quaternion"):
        pb.keyframe_insert(ch, frame=f_dst, group=bone)
def hold_hand(rig, s, f_src, frames):
    fs(f_src)
    pbh = rig.pose.bones["IK_hand." + s]; loc, q = pbh.location.copy(), pbh.rotation_quaternion.copy()
    pbp = rig.pose.bones["Pole_elbow." + s]; pl = pbp.location.copy()
    fing = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in [b.name for b in rig.pose.bones if b.name.startswith("finger") and b.name.endswith("." + s)]}
    for f in frames:
        pbh.location = loc; pbh.rotation_quaternion = q; pbh.keyframe_insert("location", frame=f, group=pbh.name); pbh.keyframe_insert("rotation_quaternion", frame=f, group=pbh.name)
        pbp.location = pl; pbp.keyframe_insert("location", frame=f, group=pbp.name)
        for n, qq in fing.items():
            rig.pose.bones[n].rotation_quaternion = qq; rig.pose.bones[n].keyframe_insert("rotation_quaternion", frame=f, group=n)

# ================================================================== HER: seated at the bench (yaw 180, faces +Y) / in the office chair
BENCH_ROOT = Vector((0.0, -0.13, SEAT_Z + 0.088))
CHAIR_ROOT = Vector((-2.10, 2.76, 0.500 + 0.088))
def inv_seat(f, root, flex=6.0, twist=0.0, side=0.0, head=(8.0, 0.0), feet_fwd=0.33, breathe=0.0):
    IH.key_root(f, root + Vector((0, 0, breathe)), yaw=180.0)
    IH.key_spine(f, flex=flex, twist=twist, side=side, head=head)
    for s, sx in (("L", -1), ("R", 1)):     # yaw 180: her left is world -X
        IH.key_foot(s, f, Vector((root.x + sx * 0.105, root.y + feet_fwd)), 180.0)
# bench: 1 .. F_INV_OFFICE-1 ; office: F_INV_OFFICE .. F_INV_BACK-1 ; bench again: F_INV_BACK .. END
INV_BENCH_HEAD = [(1, 6, -4), (40, 10, -2), (75, 14, 0), (150, 20, 2), (227, 22, 4), (260, 18, 10), (300, 20, 14), (345, 22, 8),
                  (420, 24, 2), (497, 24, 0), (560, 22, -2), (600, 10, -4), (640, 4, 0), (669, 6, 2), (700, 2, 0), (759, 2, 0)]
INV_BENCH_FLEX = [(1, 6), (120, 8), (227, 10), (300, 12), (420, 12), (560, 10), (640, 6), (759, 6)]
hp_f = pchip([(f, p) for f, p, _ in INV_BENCH_HEAD]); hy_f = pchip([(f, y) for f, _, y in INV_BENCH_HEAD]); fl_f = pchip(INV_BENCH_FLEX)
for f in list(range(1, F_INV_OFFICE, 6)) + [F_INV_OFFICE - 1]:
    inv_seat(f, BENCH_ROOT, flex=fl_f(f), head=(hp_f(f), hy_f(f)), twist=-3.0 * math.sin(f / 90.0), breathe=0.003 * math.sin(f / 22.0))
INV_OFFICE_HEAD = [(F_INV_OFFICE, 2, 0), (F_YOUSEE, 2, 0), (940, 0, 0), (995, -2, 3), (1028, 10, 0), (1062, 26, -4), (1110, 28, 2),
                   (1130, 12, 0), (1160, 2, 4), (1195, -2, 2), (1240, 0, 6), (F_INV_BACK - 1, 0, 6)]
INV_OFFICE_FLEX = [(F_INV_OFFICE, 4), (995, 6), (1040, 12), (1110, 16), (1140, 8), (1200, 4), (F_INV_BACK - 1, 4)]
hp2 = pchip([(f, p) for f, p, _ in INV_OFFICE_HEAD]); hy2 = pchip([(f, y) for f, _, y in INV_OFFICE_HEAD]); fl2 = pchip(INV_OFFICE_FLEX)
for f in list(range(F_INV_OFFICE, F_INV_BACK, 4)) + [F_INV_BACK - 1]:
    sob = 1.6 * math.sin((f - 1040) * 2 * math.pi / 14) if 1040 <= f <= 1112 else 0.0     # shoulders shake while she cries
    inv_seat(f, CHAIR_ROOT, flex=fl2(f) + sob, side=sob * 0.4, head=(hp2(f) + sob * 0.6, hy2(f)), feet_fwd=0.36, breathe=0.003 * math.sin(f / 20.0))
INV_BACK_HEAD = [(F_INV_BACK, 8, 0), (1360, 12, 4), (1413, 6, -2), (1450, 0, 0), (1488, -1, 0), (1548, 0, 0), (1580, 2, 0), (1600, 0, -2), (END, -2, 4)]
INV_BACK_FLEX = [(F_INV_BACK, 6), (1413, 6), (1500, 4), (1585, 6), (END, 4)]
hp3 = pchip([(f, p) for f, p, _ in INV_BACK_HEAD]); hy3 = pchip([(f, y) for f, _, y in INV_BACK_HEAD]); fl3 = pchip(INV_BACK_FLEX)
for f in list(range(F_INV_BACK, END + 1, 6)) + [END]:
    inv_seat(f, BENCH_ROOT, flex=fl3(f), head=(hp3(f), hy3(f)), twist=-2.0 * math.sin(f / 80.0), breathe=0.003 * math.sin(f / 22.0))

# ---- her hands at the bench: RIGHT holds the pistol grip all the time (the gun rests in its cradle); LEFT rests / turns the valve
GRIP = O["G_Grip"]
fs(1); upd()
gM = GRIP.matrix_world
grip_c = gM @ (sum((Vector(v.co) for v in GRIP.data.vertices), Vector()) / len(GRIP.data.vertices))
rpt = grip_object(INV, "R", 1, GRIP, grip_c + Vector((0.013, 0.0, 0.012)), Vector((-1.0, 0.25, 0.0)))
log("grip R report", rpt)
key_pole(INV, "R", 1, Wh(INV, "upperarm01.R") + Vector((0.30, -0.10, -0.35)))
GRIP_FRAMES_A = list(range(1, F_INV_OFFICE, 30)) + [F_INV_OFFICE - 1]
hold_hand(INV, "R", 1, GRIP_FRAMES_A[1:])
# trigger pull 1 (669-683): trigger rotates back, the index curls a little further
def trigger_pull(f0, f1):
    TRIG.rotation_mode = 'XYZ'
    for f, a_ in ((f0 - 1, 0.0), (f1, -14.0), (f1 + 40, -14.0), (f1 + 50, 0.0)):
        TRIG.rotation_euler = (R_(a_), 0, 0); TRIG.keyframe_insert("rotation_euler", frame=f)
    apply_pose(INV, "R", "power_fist", f1, amount=0.25)
    hold_hand(INV, "R", f1, [f1 + 40])
    fs(f0 - 1)
trigger_pull(F_TRIG, F_TRIG + 12)
# left hand rest on the bench, left of the cradle; reach to the valve, pinch, turn 60 deg, release, back to rest
def left_rest(f):
    place_hand(INV, "L", f, Vector((-0.20, 0.20, BENCH_TOP)), Vector((0, 0, -1)), Vector((0.25, 1.0, 0.0)), skin=0.022)
    apply_pose(INV, "L", "relaxed", f)
    key_pole(INV, "L", f, Wh(INV, "upperarm01.L") + Vector((-0.35, -0.10, -0.30)))
for f in (1, 120, 236):
    left_rest(f)
RIM = O["G_ValveRim"]
VALVE.rotation_mode = 'XYZ'
fs(290); upd()
vax = (VALVE.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()       # the wheel axis (empty Z after its 90 deg Y turn)
vcen = VALVE.matrix_world.translation.copy()
place_hand(INV, "L", 290, vcen + Vector((-0.010, 0, 0.016)), Vector((1, 0, 0)), Vector((0, 0.45, 1.0)).normalized(), skin=0.020)
apply_pose(INV, "L", "wrap_grip", 290, amount=0.55)
key_pole(INV, "L", 290, Wh(INV, "upperarm01.L") + Vector((-0.35, -0.05, -0.30)))
# approach 252 (hand open above the wheel), pinch 290, turn 300-336 (wheel and hand rotate together), release 348
fs(290); pbh = INV.pose.bones["IK_hand.L"]
M_ik0 = INV.matrix_world @ INV.data.bones["IK_hand.L"].matrix_local @ Matrix.Translation(Vector()) 
H0 = (INV.matrix_world @ pbh.matrix).copy()
def key_ik_world(rig, s, f, Mw):
    IR_ = RIG[rig.name]; IR_.key_world("IK_hand." + s, f, rig.matrix_world.inverted() @ Mw)
apply_pose(INV, "L", "open_alarm", 262, amount=1.0)
key_ik_world(INV, "L", 262, Matrix.Translation(Vector((-0.05, -0.03, 0.06))) @ H0)
hold_hand(INV, "L", 290, [298])
TURN = 50.0
for f in range(300, 337, 3):
    u = smooth((f - 300) / 36.0); ang = R_(TURN * u)
    Rv = Matrix.Translation(vcen) @ Matrix.Rotation(-ang, 4, vax) @ Matrix.Translation(-vcen)
    key_ik_world(INV, "L", f, Rv @ H0)
    VALVE.rotation_euler = (0, math.pi / 2, 0); VALVE.rotation_euler.rotate_axis('Z', -ang); VALVE.keyframe_insert("rotation_euler", frame=f)
VALVE.rotation_euler = (0, math.pi / 2, 0); VALVE.keyframe_insert("rotation_euler", frame=299)
hold_hand(INV, "L", 336, [344])
fs(344); Hend = (INV.matrix_world @ pbh.matrix).copy()
apply_pose(INV, "L", "relaxed", 360)
key_ik_world(INV, "L", 358, Matrix.Translation(Vector((-0.05, -0.04, 0.05))) @ Hend)
for f in (392, 520, F_INV_OFFICE - 1):
    left_rest(f)

# finale at the bench (F_INV_BACK..END): same grip (the cradle has not moved), left hand on the bench; trigger pull 2
fs(1)
hold_hand(INV, "R", 1, [F_INV_BACK] + list(range(F_INV_BACK + 30, END, 40)) + [END])
for f in (F_INV_BACK, 1400, 1500, END):
    left_rest(f)
trigger_pull(F_SHOOT2 - 8, F_SHOOT2 + 2)

if STOP == "inv_bench":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ---- her hands in the office chair: on her lap (palms down on the thighs, 1 cm above the cloth), wiping nothing (no face contact)
def lap_point(s, f):
    """top of her thigh at mid-length (world), found on the evaluated trousers"""
    fs(f); dg = bpy.context.evaluated_depsgraph_get()
    hip = Wh(INV, "upperleg01." + s); knee = Wh(INV, "lowerleg01." + s); p = hip.lerp(knee, 0.62)
    trs = O["Inv.trousers"]; ev_ = trs.evaluated_get(dg); inv = trs.matrix_world.inverted()
    hit, loc, nrm, idx = ev_.ray_cast(inv @ (p + Vector((0, 0, 0.25))), Vector((0, 0, -1)))
    return (trs.matrix_world @ loc) if hit else p + Vector((0, 0, 0.07)), (knee - hip).normalized()
def lap_hands(f, pose="relaxed"):
    for s in "LR":
        pt, fwd = lap_point(s, f)
        sx = -1 if s == "L" else 1
        place_hand(INV, s, f, pt + Vector((-sx * 0.02, 0, 0)), Vector((0, 0, -1)), (fwd + Vector((-sx * 0.25, 0, 0))).normalized(), skin=0.024)
        apply_pose(INV, s, pose, f)
        key_pole(INV, s, f, Wh(INV, "upperarm01." + s) + Vector((sx * 0.30, -0.15, -0.35)))
for f in list(range(F_INV_OFFICE, F_INV_BACK, 24)) + [F_INV_BACK - 1]:
    lap_hands(f)
for s in "LR":                 # constant between the bench and the office (teleport while off camera)
    pass

# ================================================================== HIM: stands behind his desk (office), later at the end of the range
OFFICE_ROOT = Vector((-2.10, 4.27, 0.0)); RANGE_ROOT = Vector((0.0, 3.80, 0.0))
MEN_ROOT_Z = MR.BN["root"].head_local.z
def men_stand(f, base, flex=0.0, twist=0.0, side=0.0, head=(0.0, 0.0), dz=-0.012, sway=0.0, lean_back=0.0):
    MH.key_root(f, base + Vector((sway, 0.0, MEN_ROOT_Z + dz)), yaw=0.0, flex=-lean_back)
    MH.key_spine(f, flex=flex, twist=twist, side=side, head=head)
    for s, sx in (("L", 1), ("R", -1)):
        MH.key_foot(s, f, Vector((base.x + sx * 0.12, base.y + 0.01)), sx * -6.0)
def men_hang(s, f, out=0.06, fwd=-0.02, down=0.10):
    sx = 1 if s == "L" else -1; fs(f); M3 = MEN.matrix_world.to_3x3()
    wr = Wh(MEN, "upperleg01." + s) + M3 @ Vector((sx * (out + 0.10), fwd - 0.03, -down + 0.06))
    hand_world(MEN, s, f, wr, Vector((0, -0.15, -1)), Vector((-sx, 0.15, 0)), pole=Wh(MEN, "upperarm01." + s) + Vector((sx * 0.45, 0.5, -0.3)))
    apply_pose(MEN, s, "relaxed", f)
def men_gesture(s, f, lift, fwd=0.30, lat=0.16, palm_up=True):
    """an open-hand talking gesture in front of his chest (elbow bent ~90 deg, clear of his torso by >= 10 cm)"""
    sx = 1 if s == "L" else -1; fs(f)
    sh = Wh(MEN, "upperarm01." + s)
    wr = sh + Vector((sx * lat * 0.6, -fwd * 0.8, -0.34 + lift))
    hand_world(MEN, s, f, wr, Vector((-sx * 0.25, -1.0, 0.15)), Vector((0, 0, 1)) if palm_up else Vector((0, 1, 0)),
               pole=sh + Vector((sx * 0.40, 0.30, -0.40)))
    apply_pose(MEN, s, "relaxed", f)
# office (F_MEN_IN .. F_MEN_RANGE-1): lecturing, finger-wag-free open-hand beats, head nods
MEN_OFF_HEAD = [(F_MEN_IN, 4, 0), (900, 6, -4), (930, 2, 6), (960, 8, 0), (995, 4, -8), (1028, 10, 0), (1062, 6, 6), (1100, 8, 0),
                (1150, 4, -4), (1200, 2, 0), (1245, 2, 0), (1252, -6, 18), (1262, -8, 24), (1285, -4, 14), (1315, 0, 4), (F_MEN_RANGE - 1, 0, 4)]
mh_p = pchip([(f, p) for f, p, _ in MEN_OFF_HEAD]); mh_y = pchip([(f, y) for f, _, y in MEN_OFF_HEAD])
for f in list(range(F_MEN_IN, F_MEN_RANGE, 6)) + [F_MEN_RANGE - 1]:
    flinch = max(0.0, 1.0 - abs(f - 1262) / 25.0)
    men_stand(f, OFFICE_ROOT, flex=2.0 + 2 * math.sin(f / 37.0), twist=4 * math.sin(f / 53.0), head=(mh_p(f), mh_y(f)), lean_back=6 * flinch,
              sway=0.006 * math.sin(f / 41.0))
for f in list(range(F_MEN_IN, F_MEN_RANGE, 30)) + [F_MEN_RANGE - 1]:
    men_hang("L", f)
lifts = [(F_MEN_IN, 0.02), (905, 0.10), (925, 0.04), (950, 0.12), (975, 0.05), (1000, 0.14), (1025, 0.06), (1050, 0.12), (1080, 0.05),
         (1110, 0.03), (1150, 0.02), (1240, 0.02), (1256, 0.16), (1290, 0.10), (F_MEN_RANGE - 1, 0.04)]
def men_talk_hand(s, f, lift):
    sx = 1 if s == "L" else -1; fs(f); sh = Wh(MEN, "upperarm01." + s)
    wr = sh + Vector((sx * 0.10, -0.22, -0.42 + lift * 0.6))
    hand_world(MEN, s, f, wr, Vector((-sx * 0.3, -1.0, 0.1)), Vector((-sx * 0.3, 0, 1)), pole=sh + Vector((sx * 0.25, 0.30, -0.45)))
    apply_pose(MEN, s, "relaxed", f)
for i, (f, l) in enumerate(lifts):
    men_talk_hand("R", f, l)
    if 900 <= f <= 1110 and i % 2 == 0: men_talk_hand("L", f + 6, l * 0.7)
    elif f > 1110: men_hang("L", f)
# range (F_MEN_RANGE .. END): stands in front of the target, hands up palms out ("go on then"), wince, the hit, a laugh
MEN_RNG_HEAD = [(F_MEN_RANGE, 2, 0), (1488, 0, 4), (1520, -2, -4), (1548, 2, 0), (1590, 6, 8), (1607, 8, 14), (1614, 14, 22), (1626, 6, 16),
                (1638, -10, 6), (1648, -8, 0), (END, -6, -2)]
mr_p = pchip([(f, p) for f, p, _ in MEN_RNG_HEAD]); mr_y = pchip([(f, y) for f, _, y in MEN_RNG_HEAD])
for f in list(range(F_MEN_RANGE, END + 1, 4)) + [END]:
    hit = max(0.0, 1.0 - abs(f - 1616) / 14.0)
    laugh = 1.5 * math.sin((f - 1630) * 2 * math.pi / 12) if 1630 <= f <= END else 0.0
    men_stand(f, RANGE_ROOT, flex=2.0 + 10 * hit + laugh, twist=-6 * hit, head=(mr_p(f), mr_y(f)), lean_back=0.0, sway=0.006 * math.sin(f / 33.0))
def men_palms_out(s, f, lift=0.0, fwd=0.25, lat=0.10):
    sx = 1 if s == "L" else -1; fs(f); sh = Wh(MEN, "upperarm01." + s)
    wr = sh + Vector((sx * lat, -fwd, -0.12 + lift))
    hand_world(MEN, s, f, wr, Vector((sx * 0.15, -0.25, 1.0)), Vector((0, -1, 0.1)), pole=sh + Vector((sx * 0.30, 0.10, -0.50)))
    apply_pose(MEN, s, "shield", f)
for f in list(range(F_MEN_RANGE, 1607, 30)):
    for s in "LR": men_palms_out(s, f, lift=0.02 * math.sin(f / 9.0))
for s in "LR":
    men_palms_out(s, 1607, lift=0.05); men_palms_out(s, 1617, lift=0.10, fwd=0.22, lat=0.26)
for f in (1636, END):
    men_hang("L", f, out=0.08, fwd=-0.06); men_hang("R", f, out=0.08, fwd=-0.06)

if STOP == "people":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== visibility: one model per character; teleports only while off camera
VISCHG = []      # (frame, [objects]) -> checked against the camera frustum at the end
def vis(objs, f, on):
    key_vis(objs, f, on); VISCHG.append((f, list(objs)))
MEN_PARTS = [c for c in MEN.children if c.type == 'MESH']
vis(MEN_PARTS, 1, False); vis(MEN_PARTS, F_MEN_IN, True)
# ================================================================== the collector tube: head-side points ride the head, gun-side points sit on the inlet
TH = O["TubeHeadAnchor"]
fs(1); upd()
def gw(v): return GUN.matrix_world @ Vector(v)
HP = [Vector(p) for p in sc["TUBE_HEAD_PTS"]]
P_head = [TH.matrix_world @ p for p in HP]
G0 = gw((0, 0.012, 0.113)); G1 = gw((0, 0.012, 0.150))
J = empty("TubeJ", HP[-1]); J.parent = TH          # TH is identity in its own space (rest coords)
J.location = HP[-1]
GE = empty("TubeG", G1)
mids = []
for k, (t, sag) in enumerate(((0.35, 0.035), (0.70, 0.030))):
    mb = empty("TubeMid%d" % k, (0, 0, 0))
    c1 = mb.constraints.new('COPY_LOCATION'); c1.target = J
    c2 = mb.constraints.new('COPY_LOCATION'); c2.target = GE; c2.influence = t
    mc = empty("TubeMidOff%d" % k, (0, 0, -sag)); mc.parent = mb
    mids.append(mc)
upd()
pts = P_head + [m.matrix_world.translation.copy() for m in mids] + [G1, G0]
cu = bpy.data.curves.new("CollectorTube", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0028; cu.bevel_resolution = 3
cu.use_path = True; cu.use_fill_caps = True
sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1); sp.order_u = 4; sp.use_endpoint_u = True; sp.resolution_u = 12
for p_, q in zip(sp.points, pts): p_.co = (*q, 1)
TUBE = bpy.data.objects.new("CollectorTube", cu); sc.collection.objects.link(TUBE); tube_m = mat("M_Tube", (0.75, 0.92, 1.0), rough=0.05); tp = tube_m.node_tree.nodes["Principled BSDF"]
tp.inputs["Transmission Weight"].default_value = 1.0; tp.inputs["IOR"].default_value = 1.33
cu.materials.append(tube_m)
def hook(obj, idx):
    h = TUBE.modifiers.new("hook_" + obj.name, 'HOOK'); h.object = obj; h.vertex_indices_set(idx)
    h.matrix_inverse = obj.matrix_world.inverted()
hook(TH, [0, 1, 2, 3]); hook(mids[0], [4]); hook(mids[1], [5])
GLASSES_ALL = GLASSES + [TUBE]
vis(GLASSES_ALL, 1, True); vis(GLASSES_ALL, F_INV_OFFICE, False); vis(GLASSES_ALL, F_INV_BACK, True)

# ================================================================== tears on her right cheek -> the cup ; drops down the tube -> the chamber
IBV = BVHTree.FromPolygons([v.co.copy() for v in IB.data.vertices], [tuple(p.vertices) for p in IB.data.polygons])
ER = Vector(sc["EYE_R"]); EL = Vector(sc["EYE_L"]); CUPC = Vector(sc["CUP_C"]); CX = CUPC.x
def on_skin(x, z, off=0.0016):
    hit = IBV.ray_cast(Vector((x, -0.5, z)), Vector((0, 1, 0)))
    loc, nrm = hit[0], hit[1]
    return loc + nrm * off
water = mat("M_Water", (0.55, 0.85, 1.0), rough=0.02); wp_ = water.node_tree.nodes["Principled BSDF"]
wp_.inputs["Transmission Weight"].default_value = 1.0; wp_.inputs["IOR"].default_value = 1.33
wp_.inputs["Emission Color"].default_value = (0.35, 0.75, 1.0, 1); wp_.inputs["Emission Strength"].default_value = 0.6
def drop_mesh(name, r, parent=None, m=water):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=16, ring_count=8); o = bpy.context.active_object; o.name = name
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    if parent is not None: o.parent = parent
    return o
def key_loc(o, f, p, sc_=None):
    o.location = p; o.keyframe_insert("location", frame=f)
    if sc_ is not None:
        o.scale = (sc_, sc_, sc_) if not isinstance(sc_, tuple) else sc_; o.keyframe_insert("scale", frame=f)
CHEEK_PATH = [on_skin(ER.x * 1.10, ER.z - 0.011), on_skin(ER.x * 1.25, ER.z - 0.018), on_skin(ER.x * 1.38, ER.z - 0.025),
              CUPC + Vector((0, 0.004, -0.002)), CUPC + Vector((0, 0, -0.010))]
def path_at(path, u):
    n = len(path) - 1; x = max(0.0, min(0.9999, u)) * n; i = int(x); return path[i].lerp(path[i + 1], x - i)
TEAR_STARTS = [8, 30, 52, 74, 96]
BEADS = []
bead_m = bpy.data.materials.new("M_Bead"); bead_m.use_nodes = True; bnt = bead_m.node_tree; bout = bnt.nodes["Material Output"]
bnt.nodes.remove(bnt.nodes["Principled BSDF"])
pw = bnt.nodes.new("ShaderNodeBsdfPrincipled"); pw.inputs["Base Color"].default_value = (0.55, 0.85, 1.0, 1); pw.inputs["Roughness"].default_value = 0.02
pw.inputs["Transmission Weight"].default_value = 1.0; pw.inputs["IOR"].default_value = 1.33
pw.inputs["Emission Color"].default_value = (0.35, 0.75, 1.0, 1); pw.inputs["Emission Strength"].default_value = 0.6
pi_ = bnt.nodes.new("ShaderNodeBsdfPrincipled"); pi_.inputs["Base Color"].default_value = (0.80, 0.93, 1.0, 1); pi_.inputs["Roughness"].default_value = 0.35
pi_.inputs["Subsurface Weight"].default_value = 0.4; pi_.inputs["Coat Weight"].default_value = 1.0
pi_.inputs["Emission Color"].default_value = (0.6, 0.85, 1.0, 1); pi_.inputs["Emission Strength"].default_value = 0.35
nz = bnt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 900.0
bp = bnt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bnt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); bnt.links.new(bp.outputs["Normal"], pi_.inputs["Normal"])
mixs = bnt.nodes.new("ShaderNodeMixShader"); bnt.links.new(pw.outputs[0], mixs.inputs[1]); bnt.links.new(pi_.outputs[0], mixs.inputs[2]); bnt.links.new(mixs.outputs[0], bout.inputs["Surface"])
FRZ = bnt.nodes.new("ShaderNodeValue"); FRZ.name = "Freeze"; bnt.links.new(FRZ.outputs[0], mixs.inputs[0])
for f, v in ((1, 0.0), (F_FREEZE, 0.0), (F_FREEZE + 70, 1.0)):
    FRZ.outputs[0].default_value = v; FRZ.outputs[0].keyframe_insert("default_value", frame=f)
ice_m = bpy.data.materials.new("M_Ice"); ice_m.use_nodes = True; ip = ice_m.node_tree.nodes["Principled BSDF"]
ip.inputs["Base Color"].default_value = (0.80, 0.93, 1.0, 1); ip.inputs["Roughness"].default_value = 0.3; ip.inputs["Coat Weight"].default_value = 1.0
ip.inputs["Emission Color"].default_value = (0.6, 0.85, 1.0, 1); ip.inputs["Emission Strength"].default_value = 0.5
BEAD_POS = [Vector((0, 0.012, 0.0245)) + Vector(d) for d in ((0, 0, 0), (0.009, 0.004, 0), (-0.009, 0.005, 0), (0.004, -0.009, 0), (-0.005, -0.008, 0))]
BR = 0.0034
for k, f0 in enumerate(TEAR_STARTS):
    t = drop_mesh("Tear%d" % k, 0.0026, parent=TH)
    for i in range(0, 45, 3):
        u = i / 44.0; sc_ = min(1.0, 0.25 + i / 8.0) if i < 9 else (1.0 if u < 0.9 else max(0.05, 1.0 - (u - 0.9) * 9))
        key_loc(t, f0 + i, path_at(CHEEK_PATH, smooth(u) * 0.6 + u * 0.4), sc_)
    key_loc(t, f0 - 1, CHEEK_PATH[0], 0.0); key_loc(t, f0 + 45, CHEEK_PATH[-1], 0.0)
    vis([t], 1, False); vis([t], f0 - 1, True); vis([t], f0 + 46, False)
    # the same tear then runs down the tube (it re-forms in the brass nozzle at the cup bottom) and drops into the chamber
    d = drop_mesh("Bead%d" % k, 0.0016, parent=GUN, m=bead_m)
    fp = d.constraints.new('FOLLOW_PATH'); fp.target = TUBE; fp.use_fixed_location = True
    ta, tb = f0 + 44, f0 + 44 + 66
    for f, of in ((ta, 0.0), (tb, 1.0)):
        fp.offset_factor = of; fp.keyframe_insert("offset_factor", frame=f)
    for f, inf in ((1, 1.0), (tb, 1.0), (tb + 1, 0.0)):
        fp.influence = inf; fp.keyframe_insert("influence", frame=f)
    key_loc(d, 1, Vector((0, 0, 0)), 1.0)
    key_loc(d, tb, Vector((0, 0.012, 0.100)), 1.0); key_loc(d, tb + 1, Vector((0, 0.012, 0.100)), BR / 0.0016)
    key_loc(d, tb + 9, BEAD_POS[k] + Vector((0, 0, 0.004)), (BR / 0.0016, BR / 0.0016, BR / 0.0016 * 0.70))
    key_loc(d, tb + 13, BEAD_POS[k] + Vector((0, 0, -0.0008)), (BR / 0.0016 * 1.08, BR / 0.0016 * 1.08, BR / 0.0016 * 0.62))
    key_loc(d, F_FREEZE, BEAD_POS[k] + Vector((0, 0, -0.0008)), (BR / 0.0016 * 1.08, BR / 0.0016 * 1.08, BR / 0.0016 * 0.62))
    key_loc(d, F_FREEZE + 60, BEAD_POS[k] + Vector((0, 0, 0.0002)), BR / 0.0016)
    vis([d], 1, False); vis([d], ta, True)
    BEADS.append(d)
    const_interp(d, "influence")
# a tiny pool in the cup that grows as the tears arrive (so nothing vanishes)
POOL = drop_mesh("CupPool", 0.0045, parent=TH)
for f, s_ in ((1, 0.0), (52, 0.0), (60, 0.6), (140, 1.0), (F_INV_OFFICE - 1, 1.0)):
    key_loc(POOL, f, CUPC + Vector((0, 0, -0.008)), (s_, s_, s_ * 0.45))
vis([POOL], 1, True); vis([POOL], F_INV_OFFICE, False); vis([POOL], F_INV_BACK, True)

# ================================================================== CO2 blast: soft white gas puffs swirl into the chamber (Object-colour alpha fade)
def puff_mat(name, col, emit=0.4, dens=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; out = nt.nodes["Material Output"]; nt.nodes.remove(nt.nodes["Principled BSDF"])
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.inputs["Base Color"].default_value = (*col, 1); p.inputs["Roughness"].default_value = 0.6
    p.inputs["Emission Color"].default_value = (*col, 1); p.inputs["Emission Strength"].default_value = emit
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); oi = nt.nodes.new("ShaderNodeObjectInfo")
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.6
    mu = nt.nodes.new("ShaderNodeMath"); mu.operation = 'MULTIPLY'; nt.links.new(oi.outputs["Alpha"], mu.inputs[0]); nt.links.new(lw.outputs["Facing"], mu.inputs[1])
    inv_ = nt.nodes.new("ShaderNodeMath"); inv_.operation = 'SUBTRACT'; inv_.inputs[0].default_value = 1.0; nt.links.new(lw.outputs["Facing"], inv_.inputs[1])
    mu2 = nt.nodes.new("ShaderNodeMath"); mu2.operation = 'MULTIPLY'; nt.links.new(oi.outputs["Alpha"], mu2.inputs[0]); nt.links.new(inv_.outputs[0], mu2.inputs[1])
    mu3 = nt.nodes.new("ShaderNodeMath"); mu3.operation = 'MULTIPLY'; mu3.inputs[1].default_value = dens; nt.links.new(mu2.outputs[0], mu3.inputs[0])
    nt.links.new(mu3.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(p.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m
gas_m = puff_mat("M_Gas", (0.92, 0.97, 1.0), emit=0.5, dens=0.45)
frost_m = puff_mat("M_FrostPuff", (0.80, 0.93, 1.0), emit=0.9, dens=0.70)
def puff(name, r, parent, m, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=r, subdivisions=3); o = bpy.context.active_object; o.name = name
    tx = bpy.data.textures.new(name + "_n", 'CLOUDS'); tx.noise_scale = r * 0.9
    d = o.modifiers.new("lumps", 'DISPLACE'); d.texture = tx; d.strength = r * 0.45; d.mid_level = 0.4; d.texture_coords = 'OBJECT'
    o.data.materials.append(m); bpy.ops.object.shade_smooth()
    if parent is not None: o.parent = parent
    return o
def key_col(o, f, a_):
    o.color = (1, 1, 1, a_); o.keyframe_insert("color", frame=f)
GAS = []
rr = random.Random(5)
for k in range(7):
    g = puff("Gas%d" % k, 0.008, GUN, gas_m, k)
    c0 = Vector((0, 0.012, 0.045)) + Vector((rr.uniform(-0.012, 0.012), rr.uniform(-0.012, 0.012), rr.uniform(-0.015, 0.02)))
    f0 = F_BLAST - 6 + k * 3
    key_loc(g, f0 - 1, Vector((-0.024, 0.012, 0.030)), 0.05); key_col(g, f0 - 1, 0.0)
    key_loc(g, f0 + 10, c0, 0.9); key_col(g, f0 + 6, 0.9)
    key_loc(g, f0 + 60, c0 + Vector((0, 0, 0.012)), 1.25); key_col(g, f0 + 60, 0.7)
    key_loc(g, F_FREEZE + 70, c0 + Vector((0, 0, 0.018)), 1.3); key_col(g, F_FREEZE + 70, 0.0)
    g.rotation_euler = (0, 0, 0); g.keyframe_insert("rotation_euler", frame=f0); g.rotation_euler = (0, 0, R_(160 + 40 * k)); g.keyframe_insert("rotation_euler", frame=F_FREEZE + 70)
    vis([g], 1, False); vis([g], f0 - 1, True); vis([g], F_FREEZE + 72, False)
    GAS.append(g)
# a little jet at the gas inlet inside the chamber
# frost creeping up the inside of the glass (a thin frosted sleeve whose alpha rises)
bpy.ops.mesh.primitive_cylinder_add(radius=0.0245, depth=0.066, location=(0, 0.012, 0.058), vertices=48, end_fill_type='NOTHING')
FROST = bpy.context.active_object; FROST.name = "ChamberFrost"; FROST.parent = GUN
fm = bpy.data.materials.new("M_GlassFrost"); fm.use_nodes = True; fnt = fm.node_tree; fout = fnt.nodes["Material Output"]; fnt.nodes.remove(fnt.nodes["Principled BSDF"])
fpb = fnt.nodes.new("ShaderNodeBsdfPrincipled"); fpb.inputs["Base Color"].default_value = (0.9, 0.97, 1.0, 1); fpb.inputs["Roughness"].default_value = 0.5
fpb.inputs["Emission Color"].default_value = (0.7, 0.9, 1.0, 1); fpb.inputs["Emission Strength"].default_value = 0.8
ftr = fnt.nodes.new("ShaderNodeBsdfTransparent"); fmx = fnt.nodes.new("ShaderNodeMixShader"); foi = fnt.nodes.new("ShaderNodeObjectInfo")
fnz = fnt.nodes.new("ShaderNodeTexVoronoi"); fnz.inputs["Scale"].default_value = 260.0; ftc = fnt.nodes.new("ShaderNodeTexCoord"); fnt.links.new(ftc.outputs["Object"], fnz.inputs["Vector"])
fcmp = fnt.nodes.new("ShaderNodeMath"); fcmp.operation = 'LESS_THAN'; fnt.links.new(fnz.outputs["Distance"], fcmp.inputs[0]); fnt.links.new(foi.outputs["Alpha"], fcmp.inputs[1])
fmu = fnt.nodes.new("ShaderNodeMath"); fmu.operation = 'MULTIPLY'; fmu.inputs[1].default_value = 0.85; fnt.links.new(fcmp.outputs[0], fmu.inputs[0])
fnt.links.new(fmu.outputs[0], fmx.inputs[0]); fnt.links.new(ftr.outputs[0], fmx.inputs[1]); fnt.links.new(fpb.outputs[0], fmx.inputs[2]); fnt.links.new(fmx.outputs[0], fout.inputs["Surface"])
FROST.data.materials.append(fm)
for f, a_ in ((1, 0.0), (F_FREEZE - 10, 0.0), (F_FREEZE + 90, 0.35), (END, 0.35)):
    key_col(FROST, f, a_)

# ================================================================== firing: spring, plunger, pellets out of the barrel, to the target / to his chest
L0 = sc["SPRING_L0"]
def spring_key(f, s_):
    SPRING.scale = (1, s_, 1); SPRING.keyframe_insert("scale", frame=f)
    PLUNGER.location = Vector((0, -0.128 + L0 * s_ + 0.0035, 0)); PLUNGER.keyframe_insert("location", frame=f)
for f, s_ in ((1, 0.36), (F_SPRING, 0.36), (F_SPRING + 3, 1.05), (F_SPRING + 6, 0.97), (F_SPRING + 9, 1.0), (F_INV_BACK - 1, 1.0), (F_INV_BACK, 0.36),
              (F_SHOOT2 + 2, 0.36), (F_SHOOT2 + 5, 1.05), (F_SHOOT2 + 8, 0.97), (F_SHOOT2 + 11, 1.0)):
    spring_key(f, s_)
for o in (SPRING, PLUNGER):
    ad = o.animation_data.action
    for fc in iter_fcurves(ad):
        for kp in fc.keyframe_points:
            if int(kp.co.x) in (F_INV_BACK - 1,): kp.interpolation = 'CONSTANT'
GINV = GUN.matrix_world.inverted()
MUZ = Vector((0, 0.2773, 0))
tgt_front_y = TGT_C.y - 0.03
def gun_local(pw_): return GINV @ pw_
HITS_A = []
for k, d in enumerate(BEADS):
    # drop into the breech (into the bore below the chamber floor)
    fdrop = 700 + k * 2
    key_loc(d, fdrop, BEAD_POS[k] + Vector((0, 0, 0.0002)), BR / 0.0016)
    key_loc(d, fdrop + 6, Vector((0, 0.012 + k * 0.0075, 0.0)), BR / 0.0016)
    key_loc(d, F_SPRING + k * 3, Vector((0, 0.012 + k * 0.0075, 0.0)), BR / 0.0016)
    key_loc(d, F_SPRING + k * 3 + 3, MUZ, BR / 0.0016)
    off = Vector(((k - 2) * 0.022, 0, 0.018 * math.sin(k * 2.1)))
    hitw = Vector((TGT_C.x, tgt_front_y, TGT_C.z)) + off
    hl = gun_local(hitw); fexit = F_SPRING + k * 3 + 3; fhit = fexit + 58
    key_loc(d, fexit + 3, MUZ + Vector((0, 0.06, 0)), BR / 0.0016 * 1.6)
    key_loc(d, fhit, hl, BR / 0.0016 * 1.6)
    key_loc(d, fhit + 3, hl + Vector((0, 0.0015, 0)), (BR / 0.0016 * 1.9, BR / 0.0016 * 0.9, BR / 0.0016 * 1.9))
    linear_interp(d, "location")
    HITS_A.append((fhit, hitw))
def burst(name, pw_, f, r=0.035, life=24, parent=None):
    b = puff(name, r, parent, frost_m, 0)
    b.location = pw_
    key_loc(b, f - 1, b.location.copy(), 0.05); key_col(b, f - 1, 0.0)
    key_loc(b, f + 4, b.location.copy(), 1.0); key_col(b, f + 3, 1.0)
    key_loc(b, f + life, b.location.copy() + Vector((0, 0, 0.02)), 1.5); key_col(b, f + life, 0.0)
    vis([b], 1, False); vis([b], f - 1, True); vis([b], f + life + 1, False)
    return b
for k, (fh, pw_) in enumerate(HITS_A):
    burst("HitBurst%d" % k, pw_ + Vector((0, -0.01, 0)), fh, r=0.03)
burst("MuzzlePuffA", MUZ + Vector((0, 0.03, 0)), F_SPRING + 4, r=0.020, life=20, parent=GUN)
# second shot (the finale): five more pellets parked inside the breech, out at F_SHOOT2+2, onto his chest
fs(1616); upd(); dg = bpy.context.evaluated_depsgraph_get()
muzw = GUN.matrix_world @ MUZ
chest = (Wh(MEN, "upperarm01.L") + Wh(MEN, "upperarm01.R")) / 2 + Vector((0, 0, -0.12))
suit = O["Men.suit"]; ev_ = suit.evaluated_get(dg); sinv = suit.matrix_world.inverted()
dvec = (chest - muzw).normalized()
hit, loc, nrm, idx = ev_.ray_cast(sinv @ muzw, (sinv.to_3x3() @ dvec).normalized())
CHEST_HIT = suit.matrix_world @ loc if hit else chest + Vector((0, -0.12, 0))
CHEST_N = (suit.matrix_world.to_3x3() @ nrm).normalized() if hit else Vector((0, -1, 0))
log("chest hit", hit, tuple(round(x, 3) for x in CHEST_HIT))
for k in range(5):
    p = drop_mesh("PelletB%d" % k, BR, parent=GUN, m=ice_m)
    key_loc(p, 1, Vector((0, 0.012 + k * 0.0075, 0.0)), 1.0)
    fx = F_SHOOT2 + 2 + k; key_loc(p, fx, Vector((0, 0.012 + k * 0.0075, 0.0)), 1.0); key_loc(p, fx + 2, MUZ, 1.8)
    hl = gun_local(CHEST_HIT - dvec * 0.004 + Vector(((k - 2) * 0.012, 0, 0.01 * math.sin(k * 2.0)))); fh = fx + 2 + 14
    key_loc(p, fh, hl, 1.8); key_loc(p, fh + 3, hl, 0.0)
    linear_interp(p, "location")
    vis([p], 1, True); vis([p], fh + 4, False)
burst("MuzzlePuffB", MUZ + Vector((0, 0.03, 0)), F_SHOOT2 + 4, r=0.022, life=20, parent=GUN)
F_HIT2 = F_SHOOT2 + 2 + 2 + 14
burst("ChestBurst", CHEST_HIT - dvec * 0.02, F_HIT2, r=0.045, life=26)
# the frost patch stays on his jacket (bound to his chest bone)
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.020, subdivisions=3, location=CHEST_HIT - CHEST_N * 0.002)
FP = bpy.context.active_object; FP.name = "FrostPatch"; FP.data.materials.append(frost_m); key_col(FP, 1, 0.75)
FP.rotation_euler = CHEST_N.to_track_quat('Z', 'Y').to_euler(); FP.scale = (1, 1, 0.10)
tx = bpy.data.textures.new("FrostPatch_n", 'CLOUDS'); tx.noise_scale = 0.02
dm = FP.modifiers.new("lumps", 'DISPLACE'); dm.texture = tx; dm.strength = 0.012
upd(); Mw = FP.matrix_world.copy()
cb = "spine04" if "spine04" in MEN.pose.bones else "spine03"
FP.parent = MEN; FP.parent_type = 'BONE'; FP.parent_bone = cb; upd(); FP.matrix_world = Mw; upd()
s0 = FP.scale.copy()
for f, u in ((1, 0.0), (F_HIT2, 0.0), (F_HIT2 + 6, 1.0)):
    FP.scale = (s0.x * max(u, 0.001), s0.y * max(u, 0.001), s0.z * max(u, 0.001)); FP.keyframe_insert("scale", frame=f)
vis([FP], 1, False); vis([FP], F_HIT2, True)


# ================================================================== the memory: tears down both cheeks (1030-1110), then the wished-for shot (1195-1250)
MEMT = []
for k, (E, f0) in enumerate(((ER, 1030), (EL, 1044), (ER, 1066), (EL, 1080))):
    sx = 1 if E.x > 0 else -1
    path = [on_skin(E.x * 1.08, E.z - 0.011), on_skin(E.x * 1.25, E.z - 0.024), on_skin(E.x * 1.45, E.z - 0.042),
            on_skin(E.x * 1.62, E.z - 0.060), on_skin(E.x * 1.75 - sx * 0.002 * k, E.z - 0.074)]
    t = drop_mesh("MemTear%d" % k, 0.0027, parent=TH)
    for i in range(0, 61, 3):
        u = i / 60.0; key_loc(t, f0 + i, path_at(path, smooth(u)), min(1.0, 0.25 + i / 9.0))
    key_loc(t, f0 - 1, path[0], 0.0)
    vis([t], 1, False); vis([t], f0 - 1, True); vis([t], F_INV_BACK, False)
    MEMT.append(t)
# her wished-for tear shot: three tears well up at her lids and fly across the desk into his face (fantasy), small splashes
FLY = []
for k, (E, fw, fh) in enumerate(((ER, 1195, 1238), (EL, 1201, 1244), (ER, 1207, 1250))):
    d = drop_mesh("FlyTear%d" % k, 0.0042)
    lid = on_skin(E.x * 1.08, E.z - 0.012, off=0.002)
    for f in range(fw, fw + 13, 2):
        fs(f); key_loc(d, f, TH.matrix_world @ lid, min(1.0, 0.2 + (f - fw) / 10.0))
    fl = fw + 12; fs(fl); p0 = TH.matrix_world @ lid
    fs(fh); hb = Wh(MEN, "head"); face = hb + Vector(((k - 1) * 0.03, -0.115, 0.04 + 0.03 * (k % 2)))
    for i in range(0, fh - fl + 1, 2):
        u = i / float(fh - fl); p = p0.lerp(face, u) + Vector((0, 0, 0.14 * math.sin(math.pi * u)))
        key_loc(d, fl + i, p, 1.0)
    key_loc(d, fh, face, 1.0); key_loc(d, fh + 3, face, 0.0)
    vis([d], 1, False); vis([d], fw - 1, True); vis([d], fh + 4, False)
    burst("Splash%d" % k, face + Vector((0, -0.01, 0)), fh, r=0.014, life=14)
    FLY.append(d)

# ================================================================== FACES: blinks, cry, anger, a sly smile, his lecture and his laugh (numeric axis finding)
def lid_sign(rig, s):
    pb = rig.pose.bones["orbicularis03." + s]; upd()
    t0 = Wt(rig, pb.name).z; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20)); upd(); t1 = Wt(rig, pb.name).z
    pb.rotation_quaternion = Quaternion(); upd()
    return 1.0 if t1 < t0 else -1.0
def lids(rig, keys, blink_frames):
    for s in "LR":
        n = "orbicularis03." + s
        if n not in rig.pose.bones: continue
        sg = lid_sign(rig, s); pb = rig.pose.bones[n]
        base = pchip(keys)
        def lid(f, ang):
            pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
        for f, a_ in keys: lid(f, a_)
        for bf in blink_frames:
            lid(bf, base(bf)); lid(bf + 4, 24); lid(bf + 7, 24); lid(bf + 13, base(bf + 13))
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
def jaw_keys(rig, keys):
    _, ax, sg = corner_axis(rig, "jaw", Vector((0, 0, -1))); pb = rig.pose.bones["jaw"]
    for f, a_ in keys:
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
def jaw_talk(rig, f0, f1, amp=7.0, seed=1):
    rr = random.Random(seed); ks = [(f0 - 4, 0.0)]; f = f0
    while f < f1:
        a_ = rr.uniform(0.3, 1.0) * amp; ks.append((f, a_)); f += rr.randint(6, 10); ks.append((f, a_ * 0.25)); f += rr.randint(4, 8)
    ks.append((f1 + 4, 0.0)); jaw_keys(rig, ks)
def eyes(rig, f0, f1, step=40, amp=(3, 5), seed=2):
    R = RIG[rig.name]; rr = random.Random(seed)
    for f in range(f0, f1, step):
        a_, b_ = rr.uniform(-amp[0], amp[0]), rr.uniform(-amp[1], amp[1])
        for s in "LR": R.key_rot("eye." + s, f, [("X", a_), ("Z", b_)])
SMILE = {"risorius03.L": ((1, 0, 0.6), 14), "risorius03.R": ((-1, 0, 0.6), 14), "levator05.L": ((0.3, 0, 1), 10), "levator05.R": ((-0.3, 0, 1), 10),
         "oris04.L": ((1, 0, 0.5), 10), "oris04.R": ((-1, 0, 0.5), 10)}
SAD = {"risorius03.L": ((1, 0, -0.4), 12), "risorius03.R": ((-1, 0, -0.4), 12), "oris04.L": ((1, 0, -0.5), 8), "oris04.R": ((-1, 0, -0.5), 8)}
fs(1)
# HER: crying at the start (soft squint, mouth down), focused, a small proud smile, the memory (sad -> angry -> sly), the finale grin
lids(INV, [(1, 7), (227, 6), (300, 2), (600, 2), (640, 0), (F_INV_OFFICE, 0), (1028, 4), (1062, 9), (1110, 9), (1130, 6), (1150, 8), (1195, 9), (1240, 5),
           (F_INV_BACK, 2), (1580, 6), (1590, 10), (1605, 4), (END, 2)], [130, 260, 380, 520, 690, 905, 990, 1170, 1300, 1400, 1470, 1530, 1630])
expression(INV, [(1, 0.8), (227, 0.7), (280, 0.2), (600, 0.0), (F_INV_OFFICE, 0.0), (995, 0.3), (1028, 0.8), (1110, 1.0), (1140, 0.5), (1195, 0.4),
                 (1215, 0.0), (F_INV_BACK, 0.0), (END, 0.0)], SAD)
expression(INV, [(1, 0.0), (600, 0.0), (630, 0.5), (700, 0.3), (F_INV_OFFICE, 0.0), (1210, 0.0), (1235, 0.6), (1262, 0.6), (F_INV_BACK, 0.0), (1350, 0.0),
                 (1380, 0.8), (1450, 0.6), (1560, 0.4), (1611, 0.9), (END, 1.0)], SMILE)
jaw_keys(INV, [(1, 0), (20, 2.5), (40, 0.5), (60, 2.5), (90, 0.5), (F_INV_OFFICE, 0), (1050, 3), (1070, 1), (1090, 3.5), (1112, 0.5), (1611, 0), (1626, 5), (1645, 3), (END, 4)])
eyes(INV, 1, END, step=45, amp=(2, 3), seed=4)
# HIM: lecture (talking), the fantasy flinch, the bracing wince and the laugh
lids(MEN, [(1, 0), (1236, 0), (1240, 22), (1262, 20), (1280, 4), (1560, 0), (1606, 6), (1611, 22), (1623, 20), (1634, 10), (1646, 12), (END, 10)],
     [900, 980, 1060, 1150, 1360, 1450, 1520])
jaw_talk(MEN, 892, 1060, amp=7.0, seed=3); jaw_talk(MEN, 1100, 1190, amp=6.0, seed=5)
jaw_keys(MEN, [(1240, 0), (1250, 5), (1290, 2), (1310, 0), (1611, 0), (1622, 6), (1630, 2), (1637, 5), (1645, 2), (1650, 5), (END, 3)])
expression(MEN, [(1, 0.0), (1500, 0.0), (1530, 0.5), (1600, 0.3), (1611, 0.0), (1630, 1.3), (END, 1.3)], SMILE)
expression(MEN, [(1, 0.0), (995, 0.0), (1010, 0.4), (1060, 0.4), (1080, 0.0)], SAD)
eyes(MEN, 1, END, step=50, amp=(2, 4), seed=7)

# ================================================================== the camera: ONE camera, one continuous move (PCHIP through the beat framings)
cd = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(CAM); sc.camera = CAM
cd.sensor_fit = 'AUTO'; cd.sensor_width = 36.0; cd.clip_start = 0.004; cd.clip_end = 60
cd.dof.use_dof = True
TGT = empty("CAM_Target", (0, 0, 1)); tt = CAM.constraints.new('TRACK_TO'); tt.target = TGT; tt.track_axis = 'TRACK_NEGATIVE_Z'; tt.up_axis = 'UP_Y'
def pellet_w(f, k=2):
    fs(f); return BEADS[k].matrix_world.translation.copy()
K = [  # frame, camera, target, lens, f-stop. A face stays in frame in the macro stretches; whips <= 15 frames past coloured set dressing
 (1,    (0.12, 0.70, 1.18), (0.0, 0.05, 1.06), 35, 8),
 (55,   (0.14, 0.48, 1.15), (0.02, 0.06, 1.10), 40, 8),
 (95,   (0.16, 0.34, 1.13), (0.04, 0.06, 1.09), 45, 8),
 (135,  (0.28, 0.58, 1.10), (0.02, 0.16, 1.03), 38, 11),
 (178,  (0.24, 0.60, 1.04), (0.0, 0.24, 0.99), 40, 11),
 (215,  (0.18, 0.58, 1.00), (0.0, 0.28, 0.98), 42, 11),
 (250,  (0.05, 0.90, 1.14), (-0.03, 0.18, 1.00), 32, 8),
 (285,  (-0.34, 0.74, 1.12), (-0.05, 0.22, 0.99), 34, 8),
 (300,  (-0.20, 0.47, 0.84), (-0.075, 0.31, 0.875), 38, 11),
 (338,  (-0.18, 0.50, 0.83), (-0.075, 0.31, 0.875), 40, 11),
 (375,  (-0.36, 0.75, 1.05), (-0.08, 0.30, 0.92), 34, 11),
 (412,  (-0.26, 0.60, 1.02), (0.0, 0.29, 0.95), 40, 11),
 (470,  (-0.22, 0.58, 1.03), (0.0, 0.29, 0.96), 42, 11),
 (530,  (0.05, 0.62, 1.05), (0.0, 0.29, 0.96), 42, 11),
 (575,  (0.22, 0.58, 1.04), (0.0, 0.29, 0.96), 42, 11),
 (605,  (-0.30, 0.82, 1.14), (-0.02, 0.20, 1.00), 32, 11),
 (636,  (-0.30, 0.70, 1.06), (-0.01, 0.24, 0.96), 34, 11),
 (668,  (-0.20, 0.42, 0.78), (0.0, 0.25, 0.845), 35, 11),
 (696,  (-0.18, 0.40, 0.79), (0.0, 0.25, 0.845), 36, 11),
 (716,  (-0.24, 0.44, 1.04), (0.0, 0.22, 0.92), 36, 11),
 (731,  (-0.24, 0.50, 1.06), (0.0, 0.62, 0.95), 34, 11),
]
for f in range(738, 790, 6):      # chase: pellets in the foreground, the coloured target ahead
    p = pellet_w(f); K.append((f, tuple(p + Vector((0.10, -0.20, 0.06))), (0.0, 4.70, 1.45), 30, 11))
K += [
 (812,  (0.45, 3.70, 1.55), (0.0, 4.70, 1.45), 35, 11),
 (850,  (0.30, 3.85, 1.52), (0.0, 4.70, 1.45), 38, 11),
 (866,  (-0.30, 3.78, 1.52), (-2.10, 4.30, 1.60), 30, 8),
 (880,  (-1.00, 3.55, 1.50), (-2.10, 4.20, 1.55), 30, 8),
 (935,  (-1.15, 3.42, 1.48), (-2.10, 4.20, 1.52), 32, 8),
 (948,  (-0.80, 3.30, 1.45), (-2.10, 3.55, 1.35), 24, 8),
 (972,  (-1.25, 3.25, 1.34), (-2.10, 2.88, 1.13), 30, 8),
 (998,  (-1.45, 3.30, 1.25), (-2.08, 2.93, 1.08), 34, 8),
 (1010, (-1.55, 3.30, 1.20), (-2.08, 2.93, 1.07), 36, 8),
 (1060, (-1.72, 3.36, 1.15), (-2.08, 2.93, 1.07), 40, 8),
 (1110, (-1.85, 3.32, 1.12), (-2.08, 2.92, 1.06), 44, 8),
 (1150, (-1.70, 3.22, 1.18), (-2.08, 2.94, 1.07), 42, 8),
 (1190, (-1.52, 3.15, 1.22), (-2.08, 2.95, 1.08), 38, 8),
 (1218, (-0.55, 3.30, 1.45), (-2.10, 3.50, 1.30), 22, 8),
 (1250, (-1.65, 3.55, 1.47), (-2.10, 4.17, 1.60), 40, 8),
 (1292, (-1.75, 3.65, 1.50), (-2.10, 4.18, 1.58), 44, 8),
 (1334, (1.30, -1.20, 2.45), (-0.60, 1.80, 1.00), 22, 8),
 (1368, (0.48, 1.15, 1.30), (-0.05, 0.18, 1.02), 30, 8),
 (1413, (0.32, 0.95, 1.22), (-0.05, 0.18, 1.02), 32, 8),
 (1470, (0.20, 0.80, 1.16), (-0.03, 0.16, 1.04), 35, 8),
 (1502, (1.20, -1.10, 2.20), (0.0, 1.90, 1.25), 24, 8),
 (1528, (1.00, 0.20, 1.95), (0.0, 3.80, 1.42), 42, 8),
 (1548, (1.10, -0.60, 2.05), (0.0, 1.60, 1.20), 26, 8),
 (1574, (0.24, 0.02, 1.06), (0.0, 0.24, 0.86), 40, 11),
 (1602, (0.22, 0.04, 1.04), (0.0, 0.25, 0.86), 42, 11),
]
for f in range(1606, 1618, 3):    # chase the second volley to his chest
    fs(f); p = O["PelletB2"].matrix_world.translation.copy()
    K.append((f, tuple(p + Vector((0.16, -0.25, 0.08))), tuple(p + Vector((0.0, 0.6, 0.05))), 32, 8))
K += [
 (1624, (0.30, 3.05, 1.45), (0.0, 3.75, 1.35), 35, 8),
 (END,  (0.22, 3.12, 1.50), (0.0, 3.80, 1.48), 42, 8),
]
K.sort(key=lambda k: k[0])
cx = [pchip([(k[0], k[1][i]) for k in K]) for i in range(3)]
tx_ = [pchip([(k[0], k[2][i]) for k in K]) for i in range(3)]
lens_f = pchip([(k[0], k[3]) for k in K]); fst = {k[0]: k[4] for k in K}
fkeys = sorted(fst)
for f in range(1, END + 1):
    CAM.location = (cx[0](f), cx[1](f), cx[2](f)); CAM.keyframe_insert("location", frame=f)
    TGT.location = (tx_[0](f), tx_[1](f), tx_[2](f)); TGT.keyframe_insert("location", frame=f)
    cd.lens = lens_f(f); cd.keyframe_insert("lens", frame=f)
    cd.dof.focus_distance = (Vector(CAM.location) - Vector(TGT.location)).length; cd.dof.keyframe_insert("focus_distance", frame=f)
    prev = max(k for k in fkeys if k <= f); cd.dof.aperture_fstop = fst[prev]; cd.dof.keyframe_insert("aperture_fstop", frame=f)
# whip-speed check (deg per frame of the view direction) and the visibility-change frustum check (no pop-ins on camera)
def view_dir(f): return (Vector((tx_[0](f), tx_[1](f), tx_[2](f))) - Vector((cx[0](f), cx[1](f), cx[2](f)))).normalized()
mx = max((math.degrees(view_dir(f).angle(view_dir(f + 1))), f) for f in range(1, END))
log("max view rotation deg/frame", round(mx[0], 2), "at", mx[1])
from bpy_extras.object_utils import world_to_camera_view
def on_cam(o, f):
    fs(f); dg = bpy.context.evaluated_depsgraph_get()
    if o.parent is not None and o.parent.type == 'ARMATURE':
        rg = o.parent; pts = [rg.matrix_world @ pb.head for pb in rg.pose.bones if pb.bone.use_deform]
    elif o.type == 'CURVE':
        pts = [o.evaluated_get(dg).matrix_world @ Vector(p_.co[:3]) for p_ in o.data.splines[0].points]
    else:
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    for p in pts + [o.matrix_world.translation]:
        v = world_to_camera_view(sc, CAM, p)
        if 0 <= v.x <= 1 and 0 <= v.y <= 1 and v.z > 0: return True
    return False
pops = []
for f, objs in VISCHG:
    if f <= 1: continue
    for o in objs:
        if o.name.startswith(("Gas", "HitBurst", "Muzzle", "ChestBurst", "Splash", "Trail", "Tear", "Bead", "MemTear", "FlyTear", "FrostPatch")): continue
        if on_cam(o, f) or on_cam(o, f - 1): pops.append((f, o.name))
log("visibility changes on camera (pop-in risk):", pops[:20], "count", len(pops))
# lens blockers (LESSONS, Nov 2026): nothing within 6 cm of the lens across the frame, every 2nd frame
blk = []
for f in range(1, END + 1, 2):
    fs(f); dg = bpy.context.evaluated_depsgraph_get(); Mc = CAM.matrix_world; org = Mc.translation
    for u, v in ((0, 0), (-0.5, -0.8), (0.5, -0.8), (-0.5, 0.8), (0.5, 0.8)):
        d = (Mc.to_3x3() @ Vector((u * 0.56, v * 1.0, -1.6))).normalized()
        hit, loc, nrm, idx, ob, _ = sc.ray_cast(dg, org, d, distance=0.06)
        if hit and not ob.name.startswith(("Gas", "HitBurst", "Muzzle", "Chest", "Splash")): blk.append((f, ob.name)); break
log("lens blockers (<6 cm):", blk[:30], "count", len(blk))
# teleports must happen off camera too
for rig, frames in ((INV, (F_INV_OFFICE, F_INV_BACK)), (MEN, (F_MEN_RANGE,))):
    b = part(rig, ".body")
    for f in frames:
        log("teleport", rig.name, f, "on camera before/after:", on_cam(b, f - 1), on_cam(b, f))
# the teleports are hard cuts of the pose keys (constant) -> make the root/IK keys at those frames constant
for rig, frames in ((INV, (F_INV_OFFICE - 1, F_INV_BACK - 1)), (MEN, (F_MEN_RANGE - 1,))):
    for fc in iter_fcurves(rig.animation_data.action):
        for kp in fc.keyframe_points:
            if int(round(kp.co.x)) in frames: kp.interpolation = 'CONSTANT'

# ================================================================== VO, output, quaternion continuity, save
try:
    se = sc.sequence_editor_create()
    vo = os.path.abspath(os.path.join(HERE, "..", "FrozenTearsGun_v011_VO.mp3"))
    coll = se.strips if hasattr(se, "strips") else se.sequences
    st = coll.new_sound("VO", vo, channel=1, frame_start=1)
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
log("quat flips fixed", [quat_continuity(r) for r in (INV, MEN)])
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
sc.frame_start, sc.frame_end = 1, END
sc.render.filepath = "//render/FrozenTearsGun_v011_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.compression = 15
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
open(OUT + ".log.txt", "w").write("\n".join(LOG))
print("ANIM_OK", OUT)
