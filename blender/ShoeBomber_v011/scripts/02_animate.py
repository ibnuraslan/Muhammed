"""ShoeBomber v011 stage B: staging, acting, props, the one continuous camera, set switching inside whips.
blender -b base.blend --python 02_animate.py -- <out.blend>
Built straight on the client's VO (vo_words.json; frame = 1 + round(t*60)); frames 1..1469.
Beat frames: 1 he tries to light the shoe | 158 attendant | 216 smelled | 303 caught him | 373 passengers and crew |
414 tackled | 503 sedated (564) | 623 examined his shoes | 713 found a fuse | 805 each one | 873 shoes were packed |
978 bring down the entire plane | 1134 that's why ... airport security (1406) | end 1469."""
import bpy, bmesh, sys, math, random, json
from mathutils import Vector, Matrix, Quaternion, Euler
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = "/home/user/Muhammed/blender/ShoeBomber_v011/scripts"
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; STAGE = args[1] if len(args) > 1 else "all"
random.seed(17)
END = 1469
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
sc.frame_start, sc.frame_end = 1, END

# ================================================================== rigs
NAMES = ["Bomber", "Attendant", "Steward", "PaxA", "PaxW", "Traveller", "AirWoman"]
RIG = {n: O[n] for n in NAMES}; BODY = {n: O[n + ".body"] for n in NAMES}
CTRL = {n: make_human_ctrl(RIG[n]) for n in NAMES}; HUM = {n: Human(CTRL[n]) for n in NAMES}
for n in NAMES:
    r = RIG[n]; add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
DOM = {n: dom_bones(BODY[n], RIG[n]) for n in NAMES}

def key_pole(n, side, f, target, kind="elbow"):
    ctrl = CTRL[n]; nm = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + side; pb = ctrl.PB[nm]
    pb.location = ctrl.rest(nm).to_3x3().inverted() @ (Vector(target) - ctrl.BN[nm].head_local)
    pb.keyframe_insert("location", frame=f, group=nm)
def key_head(n, f, yaw=0.0, pitch=0.0, roll=0.0):
    for b, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CTRL[n].key_rot(b, f, [("X", -pitch * w), ("Y", roll * w), ("Z", yaw * w)])   # pitch<0 = look down, yaw>0 = turn to own left
def key_spine(n, f, flex=0.0, twist=0.0, side=0.0):
    for b, w in Human.SPINE_W.items():
        CTRL[n].key_rot(b, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
def key_root(n, f, pos, yaw=0.0, flex=0.0, side=0.0):
    HUM[n].key_root(f, Vector(pos), yaw=yaw, flex=flex, side=side)
def foot(n, s, f, xy, yaw, z=0.0, pitch=0.0, pole=None):
    """IK foot flat on the floor (z = sole height offset) at xy, toes along yaw (0 = facing -Y)"""
    ctrl = CTRL[n]; a = ctrl.BN["foot." + s].head_local
    M = Matrix.Translation(Vector((xy[0], xy[1], a.z + z))) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(pitch), 4, 'X') @ \
        Matrix.Translation(-a) @ ctrl.rest("IK_foot." + s)
    ctrl.key_world("IK_foot." + s, f, M)
    if pole is None:
        pole = Vector((xy[0], xy[1], 0.6)) + Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Vector((0, -0.8, 0))
    key_pole(n, s, f, pole, kind="knee")
def pinch_pt(rig, s): return (Wt(rig, "finger1-3." + s) + Wt(rig, "finger2-3." + s)) / 2
def reach(n, s, f, P, fdir, palm, pose="pinch", it=6, pt=pinch_pt, pole=None):
    rig = RIG[n]; apply_pose(rig, s, pose, f)
    place_hand(rig, s, f, Vector(P) - Vector(fdir).normalized() * 0.07, palm, fdir, skin=0.0)
    if pole is not None: key_pole(n, s, f, pole)
    pb = rig.pose.bones["IK_hand." + s]; Rr = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    for k in range(it):
        fs(f); err = Vector(P) - pt(rig, s)
        if err.length < 0.0008: break
        pb.location = pb.location + Rr @ err; pb.keyframe_insert("location", frame=f, group=pb.name)
    fs(f); e = (Vector(P) - pt(rig, s)).length
    if e > 0.006: log("REACH_ERR", n, s, f, round(e * 1000, 1), "mm")
    return e
def rest_hand(n, s, f, P, fdir, palm, pose="relaxed", pole=None, skin=0.012):
    apply_pose(RIG[n], s, pose, f); place_hand(RIG[n], s, f, P, palm, fdir, skin=skin)
    if pole is not None: key_pole(n, s, f, pole)
def hand_free(n, s, f, P, fdir, palm, pose="relaxed", pole=None):
    """hand in the air (gesture) at palm point P"""
    apply_pose(RIG[n], s, pose, f); place_hand(RIG[n], s, f, P, palm, fdir, skin=0.0)
    if pole is not None: key_pole(n, s, f, pole)

# ---- faces (bone nudges, directions solved per rig) from LegoInNose v013
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
def key_face(n, f, smile=0.0, jaw=0.0, brow=0.0, squint=0.0):
    rig = RIG[n]; up = Vector((0, 0, 1))
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
        b = "orbicularis04." + s
        if b in rig.pose.bones:
            q = nudge_q(rig, b, up, 12); pb = rig.pose.bones[b]; pb.rotation_quaternion = Quaternion().slerp(q, squint); pb.keyframe_insert("rotation_quaternion", frame=f)
    q = nudge_q(rig, "jaw", -up, 14); pb = rig.pose.bones["jaw"]; pb.rotation_quaternion = Quaternion().slerp(q, jaw); pb.keyframe_insert("rotation_quaternion", frame=f)
def lids(n, f, u):
    rig = RIG[n]
    for s in "LR":
        b = "orbicularis03." + s; pb = rig.pose.bones[b]; q = nudge_q(rig, b, Vector((0, 0, -1)), 26)
        pb.rotation_quaternion = Quaternion().slerp(q, u); pb.keyframe_insert("rotation_quaternion", frame=f)
def blinks(n, frames):
    lids(n, 1, 0)
    for bf in frames:
        for df, u in ((0, 0), (3, 1), (6, 1), (11, 0)): lids(n, bf + df, u)
def saccades(n, f0, f1, every=45, amp=(3, 5), seed=1):
    rnd = random.Random(seed)
    for f in range(f0, f1, every):
        for s in "LR":
            CTRL[n].key_rot("eye." + s, f, [("X", rnd.uniform(-amp[0], amp[0])), ("Z", rnd.uniform(-amp[1], amp[1]))])

def low_point(n, f, parts=(".trousers", ".body"), xy=None, r=0.25):
    fs(f); best = 9
    for suf in parts:
        o = O.get(n + suf)
        if not o: continue
        for _, p, _ in eval_points(o):
            if xy is None or (p.to_2d() - Vector(xy)).length < r: best = min(best, p.z)
    return best

CAB = O["SET_Cabin"]
SEATOBJ = {o.name: o for o in O if o.name.startswith("Seat_")}
def seat(side, k, ry): return SEATOBJ["Seat_%s%d_%.2f" % (side, k, ry)]
fs(1)
def seat_top(side, k, ry):
    s_ = seat(side, k, ry); x, y = s_.location.x, s_.location.y
    best = None
    for dy in (0.0, 0.05, 0.10):
        z = ray_down([s_], x, y + dy, 2.0)
        if z is not None and z < 0.8: best = z if best is None else max(best, z)
    # cushion front edge
    front = None
    for k_ in range(0, 50):
        yy = y + k_ * 0.01; z = ray_down([s_], x, yy, 0.9)
        if z is None or z < (best or 0.45) - 0.08: front = yy; break
    return best, front
B_SEAT, B_FRONT = seat_top("L", 0, 0.0); M_SEAT, M_FRONT = seat_top("L", 1, 0.0); P_SEAT, P_FRONT = seat_top("R", 0, 0.0)
W_SEAT, W_FRONT = seat_top("R", 0, -0.85)
log("seat tops", B_SEAT, B_FRONT, "mid", M_SEAT, "paxA", P_SEAT, P_FRONT, "paxW", W_SEAT, W_FRONT)

# ================================================================== generic seated pose
def sit(n, f, x, y_seat, seat_z, front, yaw=180.0, flex=-2.0, spine=8.0, knee_spread=0.11, feet_fwd=0.30, z=None, depth=0.22):
    """seated ON the cushion (R3): hip joints over the cushion, feet flat on the floor ahead of the seat edge, knees ~90 deg"""
    yy = (front - depth) if yaw == 180.0 else (front + depth)
    ctrl = CTRL[n]; rh = ctrl.BN["root"].head_local; hj = ctrl.BN["upperleg01.L"].head_local
    zz = z if z is not None else seat_z + (rh.z - hj.z) + 0.085
    key_root(n, f, (x, yy, zz), yaw=yaw, flex=flex)
    fy = front + feet_fwd if yaw == 180.0 else front - feet_fwd
    for s in "LR":
        sx = (1 if s == "L" else -1) * (-1 if yaw == 180.0 else 1)
        foot(n, s, f, (x + sx * knee_spread, fy), yaw, pole=(x + sx * knee_spread * 1.5, fy + (0.9 if yaw == 180.0 else -0.9), 0.6))
    key_spine(n, f, flex=spine)
    return zz, yy
def snap_seat(n, f, x, seat_z, front, **kw):
    zz, yy = sit(n, f, x, None, seat_z, front, **kw)
    low = low_point(n, f, xy=(x, yy), r=0.09)
    zz += max(-0.03, min(0.03, (seat_z + 0.004) - low))
    sit(n, f, x, None, seat_z, front, z=zz, **kw)
    log("seat snap", n, round(zz, 3), "low", round(low_point(n, f, xy=(x, yy), r=0.09), 4), "seat", round(seat_z, 3))
    return zz

exec(open(HERE + "/02b_story.py").read())
