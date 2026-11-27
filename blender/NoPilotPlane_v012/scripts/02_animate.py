"""NoPilotPlane v012 stage B: everybody's acting, the props (mic, yokes, throttles), the plane's attitude (the world
moves), the alarms, and the ONE camera (no cuts). Built straight to the client's VO beats (v009/v011 timing).
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>"""
import bpy, sys, math, random, os, json
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
def ground_z(x, y): return 0.0
def vpchip(keys):
    """monotone (PCHIP) interpolation of Vectors, per component: no overshoot loops"""
    n = len(keys[0][1]); fns = [pchip([(k[0], k[1][i]) for k in keys]) for i in range(n)]
    return lambda x: Vector([fn(x) for fn in fns])          # flat cabin/cockpit floor (overrides the farm version in anim_lib)
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(12)
END = 3481
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
def F(t): return 1 + round(t * 60)
UP = Vector((0, 0, 1))

# ================================================================== speed: no mesh evaluation while keying poses
CHAR_MESHES = [o for o in bpy.data.collections["CHARACTERS"].objects if o.type == 'MESH']
def meshes(on):
    for o in CHAR_MESHES: o.hide_viewport = not on
    upd()
meshes(False)

# ================================================================== characters
class Char:
    def __init__(self, name):
        self.n = name; self.rig = O[name]; self.body = O[name + ".body"]; self.cl = O[name + ".clothes"]
        self.CT = make_human_ctrl(self.rig)
        add_hand_limits(self.rig)
        for pb in self.rig.pose.bones: pb.rotation_mode = 'QUATERNION'
        for s in "LR":
            lo = self.rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
        self.H = Human(self.CT)
        # head yaw/pitch signs, solved at rest
        pb = self.rig.pose.bones["head"]; upd(); e0 = Wh(self.rig, "eye.L"); out = {}
        for ax, i in (("X", 0), ("Z", 2)):
            pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
            out[ax] = Wh(self.rig, "eye.L") - e0; pb.rotation_quaternion = Quaternion(); upd()
        self.hs = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
        self.fit = Vector((0, 0, 0))
    def root(self, f, pos, yaw=180.0, flex=0.0, side=0.0):
        self.H.key_root(f, Vector(pos) + self.fit, yaw=yaw, flex=flex, side=side)
    def spine(self, f, flex=0.0, twist=0.0, side=0.0):
        for n, w in Human.SPINE_W.items():
            self.CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
    def head(self, f, yaw, pitch, roll=0.0):
        """yaw +: toward his own left; pitch +: look down; roll +: tilt toward his own left (sign as solved)"""
        sx, sz = self.hs
        for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
            self.CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])
    def foot(self, s, f, xy, yaw=180.0, lift=0.0, pitch=0.0):
        self.H.key_foot(s, f, Vector((xy[0], xy[1])), yaw, lift, pitch)
    def pole(self, s, f, target, kind="elbow"):
        n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = self.CT.PB[n]
        pb.location = self.CT.rest(n).to_3x3().inverted() @ (Vector(target) - self.CT.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def ikw(self, s, f, M):
        """key IK_hand.<s> to a world matrix (rig at the origin: world = armature space)"""
        self.CT.key_world("IK_hand." + s, f, M)
    def ik_world(self, s):
        return self.rig.pose.bones["IK_hand." + s].matrix.copy()
    def wh(self, b): return Wh(self.rig, b)
    def eyes(self):
        return (Wh(self.rig, "eye.L") + Wh(self.rig, "eye.R")) / 2
    def fwd(self):
        M = self.rig.pose.bones["spine03"].matrix
        v = -(M.to_3x3() @ Vector((0, 0, 1)))       # placeholder, replaced below
        return v

def yaw_vec(yaw):
    a = math.radians(yaw); return Vector((math.sin(a), -math.cos(a), 0.0))

C = {n: Char(n) for n in ("HERO", "CAPT", "FO", "PAX1", "PAX2", "PAX3", "PAX4", "PAX5", "PAX6", "PAX7", "PAX8", "PAX9", "PAX10")}
HERO, CAPT, FO = C["HERO"], C["CAPT"], C["FO"]

# ================================================================== surfaces
def bvh_of(objs):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); V = []; P = []
    for obj in objs:
        e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world; k = len(V)
        V += [Mw @ v.co for v in me.vertices]; P += [[k + i for i in p.vertices] for p in me.polygons]; e.to_mesh_clear()
    return BVHTree.FromPolygons(V, P)
def ray(objs, origin, direction, dist=3.0):
    return bvh_of(objs).ray_cast(Vector(origin), Vector(direction).normalized(), dist)
SEAT = lambda r, i: O["SEAT_r%d_%d" % (r, i)]
SEAT_X = (-1.12, -0.62, 0.62, 1.12)
ROW_Y = {r: -4.55 + 0.95 * (r - 1) for r in range(1, 7)}

def cushion_top(seat, x, y):
    h = ray([seat], (x, y, 2.0), (0, 0, -1), 3.0); return h[0].z if h[0] else 0.46

# ================================================================== seating (R3: pelvis snapped to the cushion, back on the backrest, feet on the floor)
def body_pts(ch, prefixes, zmax=None):
    """evaluated body + clothes points whose dominant bone starts with one of `prefixes`"""
    meshes(True)
    dom = dom_bones(ch.body, ch.rig)
    pts = [p for i, p, n in eval_points(ch.body, lambda i: dom.get(i) and dom[i].startswith(prefixes))]
    domc = dom_bones(ch.cl, ch.rig)
    pts += [p for i, p, n in eval_points(ch.cl, lambda i: domc.get(i) and domc[i].startswith(prefixes))]
    meshes(False)
    return pts

def sit_keys(ch, f, P, yaw=180.0, recline=-6.0, side=0.0, feet_fwd=0.50, feet_w=0.13, flex=0.0, twist=0.0, sside=0.0, feet=True):
    fw = yaw_vec(yaw); rt = Vector((fw.y, -fw.x, 0))      # his right
    ch.root(f, P, yaw=yaw, flex=recline, side=side)
    ch.spine(f, flex=flex, twist=twist, side=sside)
    if feet:
        for s, sg in (("L", -1), ("R", 1)):
            xy = Vector(P).to_2d() + fw.to_2d() * feet_fwd + rt.to_2d() * sg * feet_w
            ch.foot(s, f, xy, yaw)
            ch.pole(s, f, Vector((xy.x, xy.y, 0.5)) + fw * 0.5 + UP * 0.3, kind="knee")

def fit_to_seat(ch, f, seat_objs, cushion_z, back_dir):
    """move the pelvis so the lowest seat-region point rests 4 mm on the cushion and the back rests 1 cm off the backrest"""
    fs(f)
    for it in range(3):
        pts = body_pts(ch, ("pelvis", "upperleg01", "root"))
        lo = min(p.z for p in pts)
        dz = cushion_z + 0.004 - lo
        fs(f)
        ch.fit += Vector((0, 0, dz))
        log("fit", ch.n, "it", it, "dz_mm", round(dz * 1000, 1))
        if abs(dz) < 0.002: break
        return dz
    return 0.0

# Seated pelvis height above the cushion is measured once per character (rest proportions) and applied as ch.fit.
def measure_seat_offset(ch, f, P, cushion_z, **kw):
    sit_keys(ch, f, P, **kw); fs(f)
    pts = body_pts(ch, ("pelvis", "upperleg01", "upperleg02"))
    zlo = min(p.z for p in pts)
    return cushion_z + 0.004 - zlo

def hand_on_thigh(ch, s, f, u=0.55, inward=0.25, lift=0.0):
    """palm resting on the top of the thigh (ray-cast onto the evaluated clothes), fingers toward the knee"""
    fs(f)
    hip = ch.wh("upperleg01." + s); knee = ch.wh("lowerleg01." + s)
    p = hip.lerp(knee, u)
    meshes(True)
    h = ray([ch.cl, ch.body], p + UP * 0.30, (0, 0, -1), 0.6)
    meshes(False)
    top = h[0] if h[0] else p + UP * 0.08
    fd = (knee - hip); fd.z = 0; fd.normalize()
    rt = Vector((fd.y, -fd.x, 0))
    sg = -1 if s == "L" else 1
    fdir = (fd - rt * sg * inward - UP * 0.15).normalized()
    place_hand(ch.rig, s, f, top + UP * (0.004 + lift), Vector((0, 0, -1)), fdir, skin=0.012)
    sh = ch.wh("upperarm01." + s)
    ch.pole(s, f, sh + rt * sg * 0.35 - fd * 0.35 - UP * 0.25)
    apply_pose(ch.rig, s, "relaxed", f)

def hang_hand(ch, s, f, fwd_v, swing=0.0, drop=0.52, out=0.07):
    """standing: hand hanging relaxed by his side, elbow bent ~20 deg, swinging along `fwd_v`"""
    fs(f); sh = ch.wh("upperarm01." + s)
    rt = Vector((fwd_v.y, -fwd_v.x, 0)); sg = -1 if s == "L" else 1
    wrist = sh - UP * drop + fwd_v * (0.06 + swing) + rt * sg * out
    d = (-UP * 1.0 + fwd_v * 0.25).normalized(); n = -rt * sg
    ch.H.key_hand(s, f, wrist, d, n, pole=sh + rt * sg * 0.25 - fwd_v * 0.45 - UP * 0.25)
    apply_pose(ch.rig, s, "relaxed", f)

def chest_hand(ch, s, f, fwd_v, height=-0.05, ahead=0.30, out=0.16, pose="open_alarm", amount=1.0):
    """hands raised in front of the chest (alarm / bracing), clear of the body"""
    fs(f); ch_ = ch.wh("spine01"); sh = ch.wh("upperarm01." + s)
    rt = Vector((fwd_v.y, -fwd_v.x, 0)); sg = -1 if s == "L" else 1
    wrist = Vector((sh.x, sh.y, sh.z)) + fwd_v * ahead + rt * sg * (out - 0.18) + UP * height - UP * 0.12
    d = (fwd_v * 0.8 + UP * 0.4).normalized(); n = (-rt * sg * 0.6 + fwd_v * 0.4).normalized()
    ch.H.key_hand(s, f, wrist, d, n, pole=sh + rt * sg * 0.35 - UP * 0.45)
    apply_pose(ch.rig, s, pose, f, amount=amount)

# ================================================================== PASSENGERS: asleep in their seats (one model each)
PAX = [  # name, row, seat index, head (yaw, pitch, roll), body side, jaw
    ("PAX1", 5, 2, (-25, 30, -12), -4, 0.10),
    ("PAX2", 5, 3, (-30, 22, -16), -6, 0.0),
    ("PAX3", 4, 1, (20, -14, 6), 2, 0.35),        # head back on the headrest, mouth open
    ("PAX4", 4, 0, (35, 18, 14), 5, 0.0),
    ("PAX5", 6, 1, (15, 34, 8), 3, 0.15),
    ("PAX6", 6, 3, (-35, 20, -14), -5, 0.0),
    ("PAX7", 3, 3, (-30, 24, -14), -5, 0.0),
    ("PAX8", 3, 1, (25, 26, 10), 4, 0.1),
    ("PAX9", 2, 2, (-20, -12, -6), -3, 0.3),
    ("PAX10", 2, 0, (30, 22, 12), 5, 0.0),
]
SEATED = {}
for (nm, row, si, hd, sd, jaw) in PAX:
    ch = C[nm]; sx = SEAT_X[si]; sy = ROW_Y[row]; seat = SEAT(row, si)
    cz = cushion_top(seat, sx, sy - 0.02)
    P = Vector((sx, sy + 0.02, cz + 0.10))
    dz = measure_seat_offset(ch, 1, P, cz, recline=-8.0, side=sd)
    P.z += dz
    SEATED[nm] = (P, cz)
    log("seat", nm, "cushion", round(cz, 3), "pelvis", tuple(round(v, 3) for v in P))
    ph = random.uniform(0, 6.28); per = random.uniform(210, 260)
    for f in list(range(1, END + 1, 40)) + [END]:
        br = 1.3 * math.sin(2 * math.pi * f / per + ph)
        sit_keys(ch, f, P, recline=-8.0, side=sd, flex=6.0 + br, sside=sd * 0.8, feet=(f == 1 or f >= END))
        ch.head(f, hd[0] + 2 * math.sin(f / 300 + ph), hd[1] + 1.5 * math.sin(2 * math.pi * f / per + ph + 0.6), hd[2])
    for s in "LR":
        hand_on_thigh(ch, s, 1, u=0.55 if s == "L" else 0.5, inward=0.3)
        hand_on_thigh(ch, s, END, u=0.55 if s == "L" else 0.5, inward=0.3)
    eyes_closed(ch.rig, -20, END + 40, ramp=8)
    key_face(ch.rig, 1, smile=0.0, jaw=jaw); key_face(ch.rig, END, smile=0.0, jaw=jaw)

# ================================================================== CAPTAIN: collapsed sitting on the floor against the bulkhead, just inside the doorway (left)
CP = Vector((-0.74, 2.30, 0.10))
for f in list(range(1, END + 1, 40)) + [END]:
    br = 1.0 * math.sin(2 * math.pi * f / 230)
    CAPT.root(f, CP, yaw=180.0, flex=-24.0, side=6.0)
    CAPT.spine(f, flex=18.0 + br, twist=-6.0, side=8.0)
    CAPT.head(f, 18.0, 32.0 + br, 14.0)
    if f == 1 or f >= END:
        for s, xy in (("L", (-0.95, 2.95)), ("R", (-0.52, 3.05))):
            CAPT.foot(s, f, xy, 180.0 + (12 if s == "R" else -8))
            CAPT.pole(s, f, Vector((xy[0], xy[1] - 0.25, 0.6)) + Vector((0.1 if s == "R" else -0.1, 0, 0)), kind="knee")
# pelvis on the floor
dzc = None
fs(1)
pts = body_pts(CAPT, ("pelvis", "upperleg01", "upperleg02"))
dzc = 0.004 - min(p.z for p in pts)
CAPT.fit = Vector((0, 0, dzc)); log("capt floor fit mm", round(dzc * 1000, 1))
for f in list(range(1, END + 1, 40)) + [END]:
    br = 1.0 * math.sin(2 * math.pi * f / 230)
    CAPT.root(f, CP, yaw=180.0, flex=-24.0, side=6.0)
# hands: right palm on his right thigh, left hand palm-down on the floor beside his hip
hand_on_thigh(CAPT, "R", 1, u=0.6, inward=0.35); hand_on_thigh(CAPT, "R", END, u=0.6, inward=0.35)
for f in (1, END):
    fs(f); hip = CAPT.wh("upperleg01.L")
    place_hand(CAPT.rig, "L", f, Vector((hip.x - 0.17, hip.y + 0.10, 0.004)), Vector((0, 0, -1)), Vector((-0.3, 1.0, 0)).normalized(), skin=0.012)
    sh = CAPT.wh("upperarm01.L"); CAPT.pole("L", f, sh + Vector((-0.4, -0.3, -0.2)))
    apply_pose(CAPT.rig, "L", "relaxed", f)
eyes_closed(CAPT.rig, -20, END + 40, ramp=8)
key_face(CAPT.rig, 1, jaw=0.12); key_face(CAPT.rig, END, jaw=0.12)

# ================================================================== YOKES, throttles: keyed controls (both yokes linked)
YP = {t: O["YOKE_piv" + t] for t in "LR"}; YW = {t: O["YOKE_wheel" + t] for t in "LR"}
YOKE_PITCH = [(1, 0), (1420, 0), (1470, -2), (1488, -9), (1500, -8), (1830, -8), (1880, -6), (1950, -2), (2010, 2),
              (2100, 3), (2225, 0), (2400, 1), (2600, -1), (2800, 0.5), (3000, -0.5), (3200, 0.5), (END, 0)]
YOKE_ROLL = [(1, 0), (1420, 0), (1470, -38), (1500, -34), (1830, -32), (1890, -12), (1950, 9), (2010, -5), (2080, 3),
             (2150, 0), (2400, -2), (2600, 1.5), (2800, 0), (3000, -1), (3200, 1), (END, 0)]
yp = pchip(YOKE_PITCH); yr = pchip(YOKE_ROLL)
def shake(f, f0, f1, amp, rate=0.9, seed=0):
    if f < f0 or f > f1: return 0.0
    u = min(1.0, (f - f0) / 20.0, (f1 - f) / 20.0)
    return amp * u * (math.sin(f * rate + seed) * 0.6 + math.sin(f * rate * 2.3 + seed * 2) * 0.4)
for f in range(1, END + 1, 2):
    for t in "LR":
        YP[t].rotation_euler = (math.radians(yp(f) + shake(f, 1830, 2006, 1.6, 1.3)), 0, 0)
        YP[t].keyframe_insert("rotation_euler", frame=f)
        YW[t].rotation_euler = (0, math.radians(yr(f) + shake(f, 1830, 2006, 3.0, 1.1, 2)), 0)
        YW[t].keyframe_insert("rotation_euler", frame=f)
THR = [O["THR_piv0"], O["THR_piv1"]]
# v012 round 1: the lever arm ends inside the knob (it poked 5 cm above it, through his hand)
for k in (0, 1):
    arm = O["THR_arm%d" % k]; h = max(c[2] for c in arm.bound_box)
    arm.scale.z = (0.162 - arm.location.z) / h
for f, a in ((1, -12), (2812, -12), (2842, 0), (2854, -2), (2884, 10), (2900, 10), (END, 10)):
    for t in THR:
        t.rotation_euler = (math.radians(a), 0, 0); t.keyframe_insert("rotation_euler", frame=f)

def grip_rel(ch, s, f, grip_obj, approach, finger_dir=None):
    """grip `grip_obj` at frame f (hand_poses.grip_object) and return the IK_hand pose relative to the grip object"""
    fs(f)
    rep = grip_object(ch.rig, s, f, grip_obj, grip_obj.matrix_world.translation, approach, finger_dir=finger_dir)
    fs(f)
    rel = grip_obj.matrix_world.inverted() @ ch.ik_world(s)
    log("grip", ch.n, s, grip_obj.name, f, rep)
    return rel

def hold(ch, s, grip_obj, rel, f0, f1, step=2):
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        fs(f); ch.ikw(s, f, grip_obj.matrix_world @ rel)

# ================================================================== FIRST OFFICER: slumped in the right seat, left hand resting on the yoke horn
FP = Vector((0.56, 4.0, 0.0))
seatR = O["PSEAT_R"]
czR = cushion_top(seatR, 0.56, 3.98)
FP.z = czR + 0.10
FO_SIDE = [(1, -12.0), (1420, -12.0), (1440, -6.0), (1470, 2.0), (1500, 0.0), (1525, -16.0), (1545, -12.0), (END, -12.0)]
FO_TWIST = [(1, -8.0), (1420, -8.0), (1470, 14.0), (1500, 10.0), (1530, -10.0), (1550, -8.0), (END, -8.0)]
FO_FLEX = [(1, 14.0), (1420, 14.0), (1470, 2.0), (1500, 8.0), (1530, 20.0), (1550, 16.0), (END, 16.0)]
FO_HEAD = [(1, -15, 28, -18), (1420, -15, 28, -18), (1470, 10, 10, 4), (1500, 5, 25, -5), (1535, -18, 34, -20), (END, -18, 32, -20)]
fside = pchip(FO_SIDE); ftw = pchip(FO_TWIST); ffx = pchip(FO_FLEX)
dzF = measure_seat_offset(FO, 1, FP, czR, recline=-6.0, side=-5.0, feet_fwd=0.55)
FP.z += dzF; log("FO pelvis", FP)
FO_KF = sorted(set(list(range(1, END + 1, 40)) + list(range(1400, 1561, 4)) + [END]))
for f in FO_KF:
    br = 1.0 * math.sin(2 * math.pi * f / 240)
    sit_keys(FO, f, FP, recline=-6.0, side=-5.0 + 0.3 * fside(f), flex=ffx(f) + br, twist=ftw(f), sside=fside(f),
             feet_fwd=0.55, feet=(f == 1 or f >= END))
hp_ = [pchip([(k[0], k[i]) for k in FO_HEAD]) for i in (1, 2, 3)]
for f in FO_KF:
    FO.head(f, hp_[0](f), hp_[1](f), hp_[2](f))
eyes_closed(FO.rig, -20, END + 40, ramp=8)
key_face(FO.rig, 1, jaw=0.08); key_face(FO.rig, END, jaw=0.08)
# right hand on his right thigh throughout; left hand on the left horn of HIS yoke until the jerk, then into his lap
hand_on_thigh(FO, "R", 1, u=0.55); hand_on_thigh(FO, "R", END, u=0.55)
GRIP_RL = O["YOKE_gripRL"]
fs(1)
relFO = grip_rel(FO, "L", 1, GRIP_RL, Vector((1, 0.2, 0)).normalized())
for f in (1, 1400, 1500):
    fs(f); sh = FO.wh("upperarm01.L"); FO.pole("L", f, sh + Vector((-0.35, -0.1, -0.35)))
hold(FO, "L", GRIP_RL, relFO, 1, 1500, step=4)
hand_on_thigh(FO, "L", 1535, u=0.55, inward=0.2); hand_on_thigh(FO, "L", END, u=0.55, inward=0.2)
apply_pose(FO.rig, "L", "relaxed", 1520)

# ================================================================== HERO
HS = Vector((0.62, ROW_Y[4], 0.0))                   # his cabin seat (row 4, right aisle seat)
seatH = SEAT(4, 2)
czH = cushion_top(seatH, 0.62, ROW_Y[4] - 0.02)
HS.z = czH + 0.10
HS.y += 0.02
dzH = measure_seat_offset(HERO, 1, HS, czH, recline=-8.0)
HS.z += dzH; log("HERO cabin pelvis", HS)
STAND_Z = HERO.H.root_head.z - 0.015
# ---------- seated in the cabin: 1 .. 430
SEAT_A = [  # f, flex, twist, side
    (1, 10, 0, -4), (60, 10, 0, -4), (110, 0, 0, 0), (150, 2, 10, 0), (205, 4, 3, 0), (245, 2, -6, -3), (275, 6, -16, -9),
    (370, 6, -16, -9), (400, 2, -4, -2), (418, 14, 0, 0)]
fa = [pchip([(k[0], k[i]) for k in SEAT_A]) for i in (1, 2, 3)]
for f in list(range(1, 421, 6)) + [420]:
    br = 1.2 * math.sin(2 * math.pi * f / (240 if f < 100 else 150))
    sit_keys(HERO, f, HS, recline=-8.0, flex=fa[0](f) + br, twist=fa[1](f), sside=fa[2](f), feet=(f in (1, 420)))
HEAD_A = [(1, -10, 28, -8), (60, -10, 26, -6), (100, 0, 6, 0), (130, 30, 2, 0), (165, 42, 4, 3), (200, 8, 8, 0), (230, 0, 4, 0),
          (262, -48, 0, -3), (300, -62, -4, -4), (340, -58, 2, -3), (372, -50, -2, -3), (395, 0, 4, 0), (418, 0, 10, 0)]
ha = [pchip([(k[0], k[i]) for k in HEAD_A]) for i in (1, 2, 3)]
for f in list(range(1, 421, 4)) + [420]:
    HERO.head(f, ha[0](f), ha[1](f), ha[2](f))
for s in "LR":
    for f in (1, 120, 240, 300, 380, 418):
        hand_on_thigh(HERO, s, f, u=0.55 if s == "L" else 0.6, inward=0.3)
# ---------- stand up into the aisle (420 .. 520), turn left, step out
fwH = yaw_vec(180)
STAND1 = [  # f, pos, yaw, flex
    (420, HS, 180, -8), (445, HS + Vector((0, 0.10, 0.04)), 180, 18), (478, Vector((0.50, -1.36, STAND_Z - 0.10)), 192, 12),
    (500, Vector((0.32, -1.32, STAND_Z)), 215, 3), (520, Vector((0.12, -1.25, STAND_Z)), 190, 3)]
for i in range(len(STAND1) - 1):
    f0, p0, y0, x0 = STAND1[i]; f1, p1, y1, x1 = STAND1[i + 1]
    for f in range(f0, f1 + 1, 2):
        u = smooth((f - f0) / (f1 - f0))
        HERO.root(f, p0.lerp(p1, u), yaw=y0 + (y1 - y0) * u, flex=x0 + (x1 - x0) * u)
        HERO.spine(f, flex=pchip([(420, 14), (445, 18), (478, 10), (500, 4), (520, 4)])(f), twist=0, side=0)
# feet: planted in front of the seat while rising, then the left steps out into the aisle, the right follows
SEATF = {s: Vector(HS).to_2d() + fwH.to_2d() * 0.50 + Vector((sg * 0.13, 0)) for s, sg in (("L", -1), ("R", 1))}
for f, s, xy, yw, lift in ((420, "L", SEATF["L"], 180, 0), (478, "L", SEATF["L"], 180, 0), (492, "L", (0.24, -1.20), 200, 0.08),
                           (500, "L", (0.18, -1.18), 205, 0),
                           (420, "R", SEATF["R"], 180, 0), (495, "R", SEATF["R"], 180, 0), (508, "R", (0.30, -1.24), 195, 0.08),
                           (516, "R", (0.24, -1.28), 190, 0)):
    HERO.foot(s, f, xy, yw, lift)
for f in (420, 478, 520):
    for s in "LR":
        fs(f); kn = HERO.wh("lowerleg01." + s); HERO.pole(s, f, kn + fwH * 0.5 + UP * 0.1, kind="knee")
# hands: push off the thighs (420-478), then hang
for s in "LR":
    hand_on_thigh(HERO, s, 445, u=0.75, inward=0.2)
for s in "LR":
    for f in (480, 500, 520):
        hang_hand(HERO, s, f, yaw_vec(195), swing=0.02)
# ---------- walk up the aisle to the doorway (520 .. 650)
WALK1 = [(520, Vector((0.12, -1.25))), (560, Vector((0.06, -0.55))), (610, Vector((0.05, 0.75))), (650, Vector((0.08, 1.70)))]
wp = vpchip([(f, p) for f, p in WALK1])
def path1(f): return Vector((*wp(f), 0.0))
HERO.H.walk(path1, lambda f: 180.0, 520, 650, stride=0.62, lift=0.07, bob=0.018, crouch=0.03, lean=4.0)
for f in range(520, 651, 4):
    cyc = math.sin(2 * math.pi * (f - 520) / 34)
    for s, sg in (("L", 1), ("R", -1)):
        hang_hand(HERO, s, f, fwH, swing=0.17 * sg * cyc, drop=0.49)
# ---------- in the doorway: stops, looks down at the captain (650 .. 725)
DOOR_P = Vector((0.08, 1.70, STAND_Z))
for f, flex, dz in ((650, 6, 0), (665, 16, -0.02), (700, 20, -0.03), (725, 10, -0.01)):
    HERO.root(f, DOOR_P + Vector((0, 0.0, dz)), yaw=180, flex=flex * 0.4)
    HERO.spine(f, flex=flex, twist=8 if f > 655 else 0, side=0)
for s, xy in (("L", (-0.05, 1.72)), ("R", (0.21, 1.66))):
    HERO.foot(s, 650, xy); HERO.foot(s, 725, xy)
for s in "LR":
    for f in (655, 690, 725):
        hang_hand(HERO, s, f, fwH, swing=0.03)
# ---------- steps into the cockpit, past the captain's feet (725 .. 800), stands looking at the FO (800 .. 935)
WALK2 = [(725, Vector((0.08, 1.70))), (765, Vector((0.12, 2.65))), (800, Vector((0.10, 3.50)))]
wp2 = vpchip([(f, p) for f, p in WALK2])
def path2(f): return Vector((*wp2(f), 0.0))
HERO.H.walk(path2, lambda f: 180.0 - 30.0 * smooth((f - 770) / 30.0), 725, 800, stride=0.55, lift=0.08, bob=0.015, crouch=0.03, lean=3.0)
for f in range(725, 801, 4):
    cyc = math.sin(2 * math.pi * (f - 725) / 34)
    for s, sg in (("L", 1), ("R", -1)):
        hang_hand(HERO, s, f, yaw_vec(180 - 30 * smooth((f - 770) / 30.0)), swing=0.08 * sg * cyc)
P_FO_LOOK = Vector((0.10, 3.55, STAND_Z))
for f, yw, flex in ((800, 148, 4), (830, 140, 14), (880, 138, 18), (915, 142, 10), (935, 110, 4)):
    HERO.root(f, P_FO_LOOK, yaw=yw, flex=flex * 0.4)
    HERO.spine(f, flex=flex, twist=-6, side=0)
for s, xy in (("L", (0.00, 3.50)), ("R", (0.20, 3.58))):
    HERO.foot(s, 800, xy, 145); HERO.foot(s, 915, xy, 145)
for f in (805, 920, 930):
    hang_hand(HERO, "R", f, yaw_vec(140), swing=0.03)
for f in (805, 850, 900, 930):
    hang_hand(HERO, "L", f, yaw_vec(140), swing=0.03)
# he shakes the FO by the left shoulder (right hand on the top of the shoulder, carried with the FO's upper arm)
for f in range(846, 911, 4):
    w_ = math.sin((f - 846) * 0.55) * smooth((f - 846) / 10.0) * smooth((910 - f) / 10.0)
    FO.spine(f, flex=ffx(f), twist=ftw(f) + 4.0 * w_, side=fside(f) + 2.0 * w_)
    FO.head(f, hp_[0](f) + 5.0 * w_, hp_[1](f), hp_[2](f) + 4.0 * w_)
fs(850); meshes(True)
shF0 = FO.wh("upperarm01.L")
topS = ray([FO.cl, FO.body], shF0 + Vector((-0.02, -0.02, 0.30)), (0, 0, -1), 0.6)
meshes(False)
P_sh = topS[0] if topS[0] else shF0 + UP * 0.07
place_hand(HERO.rig, "R", 850, P_sh, Vector((0, 0, -1)), Vector((0.6, 0.6, -0.3)).normalized(), skin=0.014)
apply_pose(HERO.rig, "R", "cup_hold", 850); apply_pose(HERO.rig, "R", "shield", 836); apply_pose(HERO.rig, "R", "relaxed", 922)
fs(850); BfS = FO.rig.matrix_world @ FO.rig.pose.bones["upperarm01.L"].matrix
relS = BfS.inverted() @ HERO.ik_world("R")
HERO.ikw("R", 836, Matrix.Translation(Vector((-0.08, -0.08, 0.08))) @ HERO.ik_world("R"))
for f in range(850, 907, 2):
    fs(f); BfS = FO.rig.matrix_world @ FO.rig.pose.bones["upperarm01.L"].matrix; HERO.ikw("R", f, BfS @ relS)
fs(906); HERO.ikw("R", 914, Matrix.Translation(Vector((-0.10, -0.08, 0.06))) @ HERO.ik_world("R"))
for f in (836, 850, 906):
    fs(f); sh = HERO.wh("upperarm01.R"); HERO.pole("R", f, sh + Vector((0.30, -0.25, -0.40)))

# head 420 .. 1010 (keyed every 2 frames so it overrides the walk cycle's neutral head keys)
HEAD_B = [(420, 0, 10, 0), (445, 0, 20, 0), (480, 0, 4, 0), (520, 0, -2, 0), (600, 0, -4, 0), (650, 0, 4, 0), (668, 25, 36, 0),
          (700, 30, 40, 4), (725, 12, 14, 0), (765, 0, -2, 0), (800, -25, 8, 0), (830, -32, 14, -4), (880, -35, 16, -6),
          (915, -20, 8, 0), (935, 0, 2, 0), (980, -8, 6, 0), (1010, -10, 10, 0)]
hb_ = [pchip([(k[0], k[i]) for k in HEAD_B]) for i in (1, 2, 3)]
for f in range(420, 1011, 2):
    HERO.head(f, hb_[0](f), hb_[1](f), hb_[2](f))
# ---------- getting into the captain's (left) seat: helper used twice (935-1010 and 1500-1575)
PS_L = O["PSEAT_L"]
czL = cushion_top(PS_L, -0.56, 3.98)
HC = Vector((-0.56, 4.02, czL + 0.10))
dzC = measure_seat_offset(HERO, 2000, HC, czL, recline=-6.0, feet_fwd=0.58, feet_w=0.12)
HC.z += dzC; log("HERO cockpit pelvis", HC, "cushion", czL)
BESIDE = Vector((0.00, 3.86, STAND_Z))           # standing beside the seat, facing +X (back to the seat)
SEAT_FEET = {"L": (-0.68, 4.60), "R": (-0.44, 4.60)}
def sit_down(f0, start_pos, start_yaw):
    """f0: start standing at start_pos/yaw; turns his back to the seat, lowers onto it, swings round to face the nose"""
    K = [(f0, start_pos, start_yaw, 2), (f0 + 18, BESIDE, 90, 6), (f0 + 40, Vector((-0.30, 3.96, czL + 0.32)), 125, 20),
         (f0 + 58, HC + Vector((0.02, -0.02, 0.02)), 165, 0), (f0 + 75, HC, 180, -6)]
    for i in range(len(K) - 1):
        a0, p0, y0, x0 = K[i]; a1, p1, y1, x1 = K[i + 1]
        for f in range(a0, a1 + 1, 2):
            u = smooth((f - a0) / (a1 - a0)); HERO.root(f, p0.lerp(p1, u), yaw=y0 + (y1 - y0) * u, flex=x0 + (x1 - x0) * u)
            HERO.spine(f, flex=pchip([(f0, 4), (f0 + 18, 6), (f0 + 40, 18), (f0 + 58, 6), (f0 + 75, 4)])(f), twist=0, side=0)
    # feet: step beside the seat, then swing in front of it (between the seat front and the pedestal)
    sp = start_pos.to_2d()
    HERO.foot("L", f0, sp + Vector((-0.06, -0.05)), start_yaw); HERO.foot("R", f0, sp + Vector((0.06, 0.05)), start_yaw)
    HERO.foot("L", f0 + 10, (0.00, 3.72), 90, 0.06); HERO.foot("L", f0 + 18, (0.02, 3.74), 90)
    HERO.foot("R", f0 + 12, (0.06, 3.98), 90, 0.06); HERO.foot("R", f0 + 20, (0.08, 3.98), 90)
    HERO.foot("L", f0 + 40, (0.02, 3.74), 90); HERO.foot("R", f0 + 42, (0.08, 3.98), 90)
    HERO.foot("R", f0 + 52, (-0.20, 4.42), 150, 0.10); HERO.foot("R", f0 + 62, SEAT_FEET["R"], 180)
    HERO.foot("L", f0 + 56, (-0.30, 4.36), 140, 0.10); HERO.foot("L", f0 + 70, SEAT_FEET["L"], 180)
    for f in (f0, f0 + 20, f0 + 42, f0 + 58, f0 + 75):
        for s in "LR":
            fs(f); kn = HERO.wh("lowerleg01." + s); fwv = yaw_vec(180 if f >= f0 + 58 else 120)
            HERO.pole(s, f, kn + fwv * 0.5 + UP * 0.15, kind="knee")
def stand_up(f0, end_pos, end_yaw):
    K = [(f0, HC, 180, -6), (f0 + 16, HC + Vector((0.04, 0.02, 0.03)), 160, 20), (f0 + 34, Vector((-0.26, 3.94, czL + 0.34)), 120, 14),
         (f0 + 52, BESIDE, 95, 4), (f0 + 70, end_pos, end_yaw, 4)]
    for i in range(len(K) - 1):
        a0, p0, y0, x0 = K[i]; a1, p1, y1, x1 = K[i + 1]
        for f in range(a0, a1 + 1, 2):
            u = smooth((f - a0) / (a1 - a0)); HERO.root(f, p0.lerp(p1, u), yaw=y0 + (y1 - y0) * u, flex=x0 + (x1 - x0) * u)
            HERO.spine(f, flex=pchip([(f0, 4), (f0 + 16, 20), (f0 + 34, 14), (f0 + 52, 4), (f0 + 70, 4)])(f), twist=0, side=0)
    HERO.foot("L", f0, SEAT_FEET["L"], 180); HERO.foot("R", f0, SEAT_FEET["R"], 180)
    HERO.foot("L", f0 + 22, SEAT_FEET["L"], 180); HERO.foot("R", f0 + 18, SEAT_FEET["R"], 180)
    HERO.foot("R", f0 + 30, (-0.20, 4.40), 140, 0.10); HERO.foot("R", f0 + 40, (0.08, 3.98), 100)
    HERO.foot("L", f0 + 36, (-0.30, 4.30), 130, 0.10); HERO.foot("L", f0 + 48, (0.00, 3.74), 95)
    ep = end_pos.to_2d()
    HERO.foot("L", f0 + 60, ep + Vector((-0.08, -0.06)), end_yaw, 0.05); HERO.foot("L", f0 + 70, ep + Vector((-0.08, -0.06)), end_yaw)
    HERO.foot("R", f0 + 64, ep + Vector((0.08, 0.06)), end_yaw, 0.05); HERO.foot("R", f0 + 72, ep + Vector((0.08, 0.06)), end_yaw)
    for f in (f0, f0 + 18, f0 + 40, f0 + 52, f0 + 72):
        for s in "LR":
            fs(f); kn = HERO.wh("lowerleg01." + s); fwv = yaw_vec(180 if f <= f0 + 18 else 120)
            HERO.pole(s, f, kn + fwv * 0.5 + UP * 0.15, kind="knee")

SIT1 = 935
sit_down(SIT1, P_FO_LOOK, 110)
for s in "LR":
    for f in (SIT1 + 10, SIT1 + 30, SIT1 + 50):
        hang_hand(HERO, s, f, yaw_vec(110 if f < SIT1 + 50 else 150), swing=0.04, out=0.10)
for s in "LR":
    hand_on_thigh(HERO, s, SIT1 + 72, u=0.6, inward=0.3)
SEATED_FROM = SIT1 + 75     # 1010
# seated idle spine (breathing) where no other spine key is set below
def seat_spine(f0, f1, flex_fn, twist_fn=lambda f: 0.0, side_fn=lambda f: 0.0, per=150, amp=1.2):
    for f in list(range(f0, f1 + 1, 8)) + [f1]:
        HERO.root(f, HC, yaw=180, flex=-6.0)
        HERO.spine(f, flex=flex_fn(f) + amp * math.sin(2 * math.pi * f / per), twist=twist_fn(f), side=side_fn(f))

# ---------- the radio (1010 .. 1330): left hand takes the mic from the hook, holds it in front of his mouth, screams; no one answers
MIC = O["MIC"]
seat_spine(SEATED_FROM, 1330, pchip([(1010, 4), (1060, 6), (1100, 10), (1160, 14), (1225, 6), (1275, 12), (1330, 6)]),
           twist_fn=pchip([(1010, 0), (1050, 10), (1100, 4), (1225, 0), (1300, 8), (1330, 0)]),
           side_fn=pchip([(1010, 0), (1050, 6), (1100, 0), (1300, 5), (1330, 0)]), per=70, amp=1.6)
hand_on_thigh(HERO, "R", 1010, u=0.6, inward=-0.15); hand_on_thigh(HERO, "R", 1330, u=0.6, inward=-0.15)
for f in (1100, 1225):
    hand_on_thigh(HERO, "R", f, u=0.55, inward=-0.15)
# left: reach (1030), grab (1062), raise (1100)
fs(1040); sh = HERO.wh("upperarm01.L")
mic_M0 = MIC.matrix_world.copy()
relMic = None
fs(1062)
rep = grip_object(HERO.rig, "L", 1062, MIC, MIC.matrix_world.translation + Vector((0, 0, 0.012)), Vector((-1, 0.15, 0)).normalized())
log("mic grip", rep)
fs(1062); W_grab = HERO.ik_world("L")
rel_mic_in_hand = W_grab.inverted() @ MIC.matrix_world          # mic relative to the IK_hand frame
for f in (1030, 1062, 1100):
    fs(f); sh = HERO.wh("upperarm01.L"); HERO.pole("L", f, sh + Vector((-0.30, -0.05, -0.45)))
# approach: 10 cm short of the grip along the approach line, open hand
HERO.ikw("L", 1040, Matrix.Translation(Vector((0.10, -0.02, 0.03))) @ W_grab)
apply_pose(HERO.rig, "L", "shield", 1040)
owner_switch(MIC, 1063, HERO.rig, "wrist.L", log=log)
def mic_at_mouth(f, fwd=0.11, down=0.035, side=0.04):
    """the hand pose that puts the mic grill `fwd` m in front of his mouth (head frame), mic upright"""
    fs(f)
    hm = HERO.rig.matrix_world @ HERO.rig.pose.bones["head"].matrix
    eye = HERO.eyes(); jaw = HERO.wh("jaw")
    face_fwd = (hm.to_3x3() @ Vector((0, 0, 1))).normalized()
    # head bone: +Y up the head; the face direction is found from eyes relative to the head bone line
    hb = HERO.wh("head"); ht = Wt(HERO.rig, "head")
    upv = (ht - hb).normalized(); fdir = (eye - hb); fdir = (fdir - upv * fdir.dot(upv)).normalized()
    mouth = eye - upv * 0.075 + fdir * 0.02
    rt = fdir.cross(upv).normalized()
    pos = mouth + fdir * fwd - upv * down - rt * side
    y_ax = fdir.copy()                   # mic local +Y points away from his face (grill on -Y faces the mouth)
    z_ax = (upv - y_ax * upv.dot(y_ax)).normalized(); x_ax = y_ax.cross(z_ax)
    Mmic = Matrix((x_ax, y_ax, z_ax)).transposed().to_4x4(); Mmic.translation = pos
    return Mmic @ rel_mic_in_hand.inverted()
# keyed after the head keys (below) so the mic follows the head: hold 1100-1225, lower 1225-1275, back to the hook 1290-1325
# ---------- head acting in the seat 1010 .. 1330
HEAD_R = [(1010, -10, 10, 0), (1040, 35, 22, 0), (1062, 40, 26, 0), (1090, 5, 4, 0), (1110, 0, -4, 0), (1135, -6, -6, -3),
          (1160, 6, -4, 3), (1185, -4, -8, -2), (1210, 4, -4, 2), (1225, 0, 0, 0), (1250, -12, 20, 0), (1275, -8, 22, 0),
          (1300, 30, 22, 0), (1330, 20, 10, 0)]
hr = [pchip([(k[0], k[i]) for k in HEAD_R]) for i in (1, 2, 3)]
for f in range(1010, 1331, 3):
    HERO.head(f, hr[0](f), hr[1](f), hr[2](f))
for f in list(range(1100, 1226, 4)):
    sh_ = 0.006 * math.sin(f * 0.9)                # panic shake of the hand holding the mic
    HERO.ikw("L", f, Matrix.Translation(Vector((sh_, 0, sh_ * 0.6))) @ mic_at_mouth(f))
for f in (1240, 1260, 1275):
    HERO.ikw("L", f, mic_at_mouth(f, fwd=0.20, down=0.22, side=0.05))
for f in (1110, 1160, 1215):
    fs(f); log("mic to mouth cm", f, round((MIC.matrix_world.translation - (HERO.eyes() - Vector((0, 0, 0.075)))).length * 100, 1))
HERO.ikw("L", 1300, Matrix.Translation(Vector((0.08, -0.02, 0.04))) @ W_grab)
HERO.ikw("L", 1324, W_grab)
apply_pose(HERO.rig, "L", "shield", 1326)       # releases the mic
owner_switch(MIC, 1325, None, log=log)
hand_on_thigh(HERO, "L", 1345, u=0.6, inward=0.3)
for f in (1300, 1324, 1345):
    fs(f); sh = HERO.wh("upperarm01.L"); HERO.pole("L", f, sh + Vector((-0.30, -0.05, -0.45)))
# ---------- stands up (1345 .. 1415) and grips the FO by the left shoulder and upper arm; pulls (1430-1490); loses grip (1500)
HAUL_P = Vector((0.04, 4.05, STAND_Z))
stand_up(1345, HAUL_P, 128)
for f in (1360, 1380, 1400):
    hang_hand(HERO, "R", f, yaw_vec(128), swing=0.05)
hang_hand(HERO, "L", 1380, yaw_vec(128), swing=0.05); hang_hand(HERO, "L", 1400, yaw_vec(128), swing=0.08)
HAUL = [(1415, 12, 0.0), (1430, 20, 0.0), (1460, 4, -0.10), (1490, -4, -0.16), (1500, -2, -0.15), (1515, 2, -0.22), (1530, 4, -0.20)]
for f, flex, back in HAUL:
    if f <= 1500:
        HERO.root(f, HAUL_P + yaw_vec(128) * back, yaw=128, flex=flex * 0.4)
        HERO.spine(f, flex=flex, twist=0, side=0)
for s, xy in (("L", (-0.04, 3.99)), ("R", (0.12, 4.11))):
    HERO.foot(s, 1415, xy, 128)
HERO.foot("L", 1460, (-0.04, 3.99), 128); HERO.foot("R", 1450, (0.12, 4.11), 128)
HERO.foot("R", 1470, (0.04, 3.99), 128, 0.05); HERO.foot("R", 1480, (0.0, 3.95), 128)
# hand targets on the FO, ray-cast onto his shirt at 1420, then carried with his left upper arm bone
fs(1420); meshes(True)
shF = FO.wh("upperarm01.L"); elF = FO.wh("lowerarm01.L")
top = ray([FO.cl, FO.body], shF + Vector((-0.02, -0.02, 0.30)), (0, 0, -1), 0.6)
armP = shF.lerp(elF, 0.45)
side_hit = ray([FO.cl, FO.body], armP + Vector((-0.30, -0.12, 0.0)), (Vector((0.30, 0.12, 0.0))), 0.6)
meshes(False)
P_top = top[0] if top[0] else shF + UP * 0.07
P_side = side_hit[0] if side_hit[0] else armP + Vector((-0.05, 0, 0))
log("haul contacts", P_top, P_side)
place_hand(HERO.rig, "R", 1428, P_top, Vector((0, 0, -1)), Vector((0.6, 0.6, -0.3)).normalized(), skin=0.014)
place_hand(HERO.rig, "L", 1428, P_side, Vector((0.92, 0.38, 0)).normalized(), Vector((0.2, 0.3, -1.0)).normalized(), skin=0.014)
apply_pose(HERO.rig, "R", "cup_hold", 1428); apply_pose(HERO.rig, "L", "wrap_grip", 1428, amount=0.6)
apply_pose(HERO.rig, "R", "shield", 1412); apply_pose(HERO.rig, "L", "shield", 1412)
fs(1428); Bf = FO.rig.matrix_world @ FO.rig.pose.bones["upperarm01.L"].matrix
relH = {s: Bf.inverted() @ HERO.ik_world(s) for s in "LR"}
HERO.ikw("R", 1412, Matrix.Translation(Vector((-0.10, -0.08, 0.06))) @ HERO.ik_world("R"))
HERO.ikw("L", 1412, Matrix.Translation(Vector((-0.12, -0.10, 0.0))) @ HERO.ik_world("L"))
for f in range(1428, 1499, 2):
    fs(f); Bf = FO.rig.matrix_world @ FO.rig.pose.bones["upperarm01.L"].matrix
    for s in "LR": HERO.ikw(s, f, Bf @ relH[s])
for s in "LR":
    for f in (1412, 1428, 1470, 1498):
        fs(f); sh = HERO.wh("upperarm01." + s); fw_ = yaw_vec(128); rt = Vector((fw_.y, -fw_.x, 0)); sg = -1 if s == "L" else 1
        HERO.pole(s, f, sh + rt * sg * 0.35 - UP * 0.45 - fw_ * 0.1)
# loses grip: hands fly off, he stumbles back, then drops into the seat (sit_down 1505)
for s in "LR":                                  # grip lost: hands spring up and back off his shoulder (clear of the headrest)
    fs(1498); fw_ = yaw_vec(128); rt = Vector((fw_.y, -fw_.x, 0)); sg = -1 if s == "L" else 1
    HERO.ikw(s, 1506, Matrix.Translation(-fw_ * 0.14 + UP * 0.02 + rt * sg * 0.14) @ HERO.ik_world(s))
    apply_pose(HERO.rig, s, "open_alarm", 1506)
    chest_hand(HERO, s, 1520, yaw_vec(128), height=-0.06, ahead=0.22, out=0.28)
SIT2 = 1505
sit_down(SIT2, HAUL_P + yaw_vec(128) * -0.18, 128)
for s in "LR":
    chest_hand(HERO, s, SIT2 + 30, yaw_vec(120), height=-0.05, ahead=0.28, out=0.22)
# ---------- alarms (1550-1820): in the seat, hands up in panic, looking around; braces as the nose drops
SEATED2 = SIT2 + 75   # 1580
seat_spine(SEATED2, 1832, pchip([(1580, -2), (1620, 4), (1700, -6), (1760, -8), (1832, 6)]),
           twist_fn=pchip([(1580, 0), (1640, -8), (1700, 6), (1760, 0), (1832, 0)]), per=45, amp=2.0)
for f in (1595, 1640, 1690, 1740, 1790):
    for s in "LR":
        chest_hand(HERO, s, f, yaw_vec(180), height=0.02 + 0.03 * math.sin(f), ahead=0.30, out=0.20)
HEAD_P = [(1505, 30, 0, 0), (1550, 0, -10, 0), (1575, -15, -16, 0), (1600, 20, -8, 3), (1630, -5, 8, 0), (1660, 30, -6, 0),
          (1700, 0, -12, 0), (1740, -5, -14, 0), (1790, 0, -6, 0), (1832, 0, 4, 0)]
hpp = [pchip([(k[0], k[i]) for k in HEAD_P]) for i in (1, 2, 3)]
for f in range(1505, 1833, 3):
    HERO.head(f, hpp[0](f) + 2 * math.sin(f * 0.7), hpp[1](f), hpp[2](f))
# ---------- grabs the controls (1832) and flies (to the end); right hand to the throttles 2700-2930
GRIP = {"L": O["YOKE_gripLL"], "R": O["YOKE_gripLR"]}
fs(1832)
relY = {}
relY["L"] = grip_rel(HERO, "L", 1832, GRIP["L"], Vector((1, 0.15, 0)).normalized())
relY["R"] = grip_rel(HERO, "R", 1832, GRIP["R"], Vector((-1, 0.15, 0)).normalized())
for s in "LR":
    fs(1815); HERO.ikw(s, 1815, Matrix.Translation(Vector((0, -0.10, 0.04))) @ (GRIP[s].matrix_world @ relY[s]))
    apply_pose(HERO.rig, s, "shield", 1815)
hold(HERO, "L", GRIP["L"], relY["L"], 1832, END, step=2)
hold(HERO, "R", GRIP["R"], relY["R"], 1832, 2700, step=2)
THK = O["THR_knob0"]
relT = grip_rel(HERO, "R", 2800, THK, Vector((0.05, 1.0, -0.30)).normalized())
fs(2760); HERO.ikw("R", 2760, Matrix.Translation(Vector((0.0, -0.09, 0.05))) @ (THK.matrix_world @ relT))
apply_pose(HERO.rig, "R", "shield", 2760)
fs(2700); MA = GRIP["R"].matrix_world @ relY["R"]
fs(2760); MB = Matrix.Translation(Vector((0.0, -0.09, 0.05))) @ (THK.matrix_world @ relT)
for f_, u in ((2715, 0.3), (2730, 0.55), (2745, 0.8)):
    q_ = MA.to_quaternion().slerp(MB.to_quaternion(), u); t_ = MA.translation.lerp(MB.translation, u) + Vector((0.02, -0.03, 0.04 * math.sin(math.pi * u)))
    HERO.ikw("R", f_, Matrix.Translation(t_) @ q_.to_matrix().to_4x4())
apply_pose(HERO.rig, "R", "relaxed", 2730)
log("throttle reach path", [round(v, 3) for v in MA.translation], [round(v, 3) for v in MB.translation])
hold(HERO, "R", THK, relT, 2800, 2900, step=2)
for f_ in (2790, 2800, 2850, 2900): apply_pose(HERO.rig, "R", "wrap_grip", f_, amount=0.75)
apply_pose(HERO.rig, "R", "shield", 2915)
fs(2915); HERO.ikw("R", 2915, Matrix.Translation(Vector((0.0, -0.09, 0.06))) @ (THK.matrix_world @ relT))
fs(2935); HERO.ikw("R", 2935, Matrix.Translation(Vector((0.0, -0.08, 0.05))) @ (GRIP["R"].matrix_world @ relY["R"]))
grip_rel(HERO, "R", 2950, GRIP["R"], Vector((-1, 0.15, 0)).normalized())
hold(HERO, "R", GRIP["R"], relY["R"], 2950, END, step=2)
for s in "LR":
    for f in (1832, 2100, 2500, 2700, 2800, 2950, 3300, END):
        fs(f); sh = HERO.wh("upperarm01." + s); sg = -1 if s == "L" else 1
        HERO.pole(s, f, sh + Vector((sg * 0.40, 0.05, -0.45)))
# spine and head while flying
FLY_FLEX = [(1832, 10), (1880, 8), (1950, 0), (2006, -2), (2100, 2), (2225, 4), (2300, 10), (2420, 4), (2500, 12), (2650, 8),
            (2760, 14), (2900, 10), (2975, 2), (3060, 0), (3150, 4), (3250, 10), (3344, 6), (END, 4)]
FLY_TWIST = [(1832, 0), (2700, 0), (2780, -8), (2900, -6), (2975, 0), (3020, 18), (3110, 20), (3160, 0), (END, 0)]
seat_spine(1832, END, pchip(FLY_FLEX), twist_fn=pchip(FLY_TWIST),
           side_fn=lambda f: 2.5 * math.sin(f / 23.0) if f < 2006 else 0.0, per=120, amp=1.3)
HEAD_F = [(1832, 0, 4, 0), (1880, -6, -6, 4), (1920, 8, -4, -4), (1960, -4, -2, 2), (2006, 0, 2, 0), (2080, 4, 6, 0),
          (2160, 0, 2, 0), (2225, -4, 6, 0), (2280, -14, 30, 0), (2380, -12, 30, 0), (2430, 0, 4, 0), (2479, -14, 0, 0),
          (2560, -16, -4, 0), (2600, 0, -2, 0), (2653, 0, 0, 0), (2700, -24, 24, 0), (2800, -30, 32, 0), (2880, -20, 26, 0), (2940, 0, 2, 0),
          (2975, 0, 0, 0), (3030, 52, 4, 0), (3110, 56, 6, 0), (3150, 10, 2, 0), (3190, -15, -2, 0), (3260, -16, 0, 0), (3300, 0, -2, 0),
          (3344, 0, -2, 0), (3420, 0, -4, 0), (END, 0, -3, 0)]
hf = [pchip([(k[0], k[i]) for k in HEAD_F]) for i in (1, 2, 3)]
for f in range(1832, END + 1, 3):
    HERO.head(f, hf[0](f) + (1.5 * math.sin(f * 0.9) if f < 2006 else 0.0), hf[1](f), hf[2](f))
HERO.head(END, hf[0](END), hf[1](END), hf[2](END))
# ---------- face (expressions, blinks, eyes)
FACE = [(1, 0, 0, 0, 0), (60, 0, 0, 0, 0), (100, 0, 0.4, 0.05, 0), (160, -0.1, 0.8, 0.10, 0), (240, -0.15, 0.9, 0.12, 0),
        (330, 0.0, 0.5, 0.05, 0.1), (405, -0.1, 0.9, 0.15, 0), (520, -0.15, 0.7, 0.05, 0), (660, -0.3, 1.0, 0.30, 0),
        (725, -0.25, 0.9, 0.15, 0), (830, -0.2, 1.0, 0.25, 0), (935, -0.15, 0.7, 0.10, 0), (1100, -0.35, 0.9, 0.55, 0),
        (1160, -0.4, 1.0, 0.65, 0), (1225, -0.2, 0.8, 0.15, 0), (1260, -0.35, -0.6, 0.05, 0.3), (1330, -0.2, 0.6, 0.1, 0),
        (1430, -0.4, -0.7, 0.35, 0.4), (1500, -0.3, 1.0, 0.45, 0), (1560, -0.45, 1.0, 0.60, 0), (1700, -0.4, 1.0, 0.50, 0),
        (1840, -0.4, -0.8, 0.30, 0.5), (1950, -0.4, -0.9, 0.35, 0.5), (2006, -0.2, -0.4, 0.15, 0.3), (2150, 0.0, 0.0, 0.05, 0.1),
        (2225, -0.05, 0.3, 0.05, 0), (2330, -0.15, 0.7, 0.08, 0), (2479, 0.0, 0.8, 0.10, 0), (2560, 0.2, 0.6, 0.05, 0),
        (2653, -0.05, 0.3, 0.02, 0.2), (2800, -0.1, -0.3, 0.02, 0.3), (2975, -0.15, 0.6, 0.05, 0), (3100, -0.25, 0.8, 0.10, 0),
        (3150, 0.0, 0.3, 0.02, 0.1), (3250, 0.1, 0.2, 0.0, 0.2), (3344, 0.0, 0.9, 0.04, 0.0), (3420, 0.12, 0.9, 0.04, 0.0),
        (END, 0.18, 0.8, 0.03, 0.0)]
for f, sm, brw, jw, sq in FACE:
    key_face(HERO.rig, f, smile=sm, brow=brw, jaw=jw, squint=sq)
blinks(HERO.rig, [112, 236, 398, 560, 690, 860, 1000, 1240, 1370, 1610, 1780, 2040, 2200, 2420, 2610, 2760, 2960, 3140, 3290])
eyes_closed(HERO.rig, -9, 80, ramp=10)
saccades(HERO.CT, 90, END, every=38, amp=(1.5, 3.0), seed=3)

# ================================================================== the plane's attitude, altitude and the world
W_ROT, W_POS = O["WORLD_ROT"], O["WORLD_POS"]
PITCH = [(1, 0), (1470, 0), (1500, -6), (1580, -16), (1680, -26), (1820, -29), (1900, -22), (1980, -13), (2080, -6),
         (2225, -4.0), (2600, -4.2), (3000, -4.0), (END, -3.6)]
ROLL = [(1, 0), (1470, 0), (1490, 8), (1560, 26), (1700, 34), (1830, 30), (1890, 14), (1950, -6), (2010, 4), (2080, -2),
        (2150, 0.5), (2400, -1), (2700, 1), (3000, -0.8), (END, 0)]
pp = pchip(PITCH); rr = pchip(ROLL)
V = 200.0
alt = 1300.0; dist = 0.0; ALT = {}; DIST = {}
for f in range(1, END + 1):
    turb = 0.25 * math.sin(f * 0.05) + 0.15 * math.sin(f * 0.13)
    p = pp(f) + turb * (1 if f < 1470 or f > 2225 else 0.3); r = rr(f) + turb * 0.8
    alt += V * math.sin(math.radians(pp(f))) / 60.0
    dist += V * math.cos(math.radians(pp(f))) / 60.0
    ALT[f] = alt; DIST[f] = dist
    W_ROT.rotation_euler = (math.radians(-p), math.radians(-r), 0); W_ROT.keyframe_insert("rotation_euler", frame=f)
    W_POS.location = (0, -dist, -alt); W_POS.keyframe_insert("location", frame=f)
log("altitude", "start 1500", "at 2225", round(ALT[2225]), "at 2479", round(ALT[2479]), "end", round(ALT[END]), "dist end", round(DIST[END]))
# sky rotation follows the world
sky = bpy.context.scene.world.node_tree.nodes["SKY_ATT"]
for f in range(1, END + 1, 2):
    fs(f); e = W_ROT.rotation_euler
    sky.inputs["Rotation"].default_value = (e.x, e.y, e.z); sky.inputs["Rotation"].keyframe_insert("default_value", frame=f)
# the field starts ~1.1 km past where we end, the town before it
FL = O["FIELD"]; TW = O["TOWN"]
FC = DIST[END] + 1100 + 1600
FL.location = (0.0, FC, 0.4)
TW.location.y += FC - 9000.0
log("field y", FL.location.y, "town offset", TW.location.y)
# displays: two attitude controls (one per PFD), the needles, the alarm lamps, the radio lights
for tag in "LR":
    d = O["DISP_PFD_" + tag]
    a = bpy.data.objects.new("ATT_" + tag, None); bpy.context.scene.collection.objects.link(a); a.location = d.location.copy()
    a.rotation_mode = 'XYZ'
    for n in d.data.materials[0].node_tree.nodes:
        if n.type == 'TEX_COORD' and n.object is not None: n.object = a
    for f in range(1, END + 1, 4):
        fs(f); e = W_ROT.rotation_euler
        a.location = d.location + Vector((0, 0, max(-0.07, min(0.07, e.x * 0.25))))
        a.rotation_euler = (0, -e.y, 0)
        a.keyframe_insert("location", frame=f); a.keyframe_insert("rotation_euler", frame=f)
G = {n: O[n + "_needle"] for n in ("ALT", "SPD", "VSI", "ALT2")}
for f in range(1, END + 1, 3):
    al = ALT[f]; vs = (ALT[min(END, f + 1)] - ALT[max(1, f - 1)]) * 30.0
    G["ALT"].rotation_euler = (0, 2 * math.pi * al / 100.0, 0); G["ALT2"].rotation_euler = (0, 2 * math.pi * al / 100.0, 0)
    G["SPD"].rotation_euler = (0, -math.radians(140 + 40 * max(0, -pp(f)) / 27.0 + 3 * math.sin(f * 0.4)), 0)
    G["VSI"].rotation_euler = (0, -math.radians(max(-160, min(160, vs * 2.2))), 0)
    for g in G.values(): g.keyframe_insert("rotation_euler", frame=f)
WM = bpy.data.materials["M_Warn"].node_tree.nodes["Emission"].inputs["Strength"]
AL = O["L_Alarm"].data
for f in range(1, END + 1):
    on = 1550 <= f <= 2230 and ((f - 1550) % 24) < 12
    if f == 1 or (f >= 1545 and f <= 2240):
        WM.default_value = 30.0 if on else 0.3; WM.keyframe_insert("default_value", frame=f)
        AL.energy = 480.0 if on else 0.0; AL.keyframe_insert("energy", frame=f)
for fc in iter_fcurves(bpy.data.materials["M_Warn"].node_tree.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for fc in iter_fcurves(AL.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
for i in range(6):
    m = bpy.data.materials["M_RadioLED%d" % i]; inp = m.node_tree.nodes["Emission"].inputs["Strength"]
    for f in range(1, END + 1, 10):
        blink = ((f // 10 + i * 3) % (4 if 1225 <= f <= 1290 else 9)) == 0
        inp.default_value = 12.0 if blink else 3.0; inp.keyframe_insert("default_value", frame=f)
    for fc in iter_fcurves(m.node_tree.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# ================================================================== the ONE camera: framings computed from the actors at their frames
meshes(False)
def face_of(ch, f):
    fs(f); return ch.eyes()
def head_fwd(ch, f):
    fs(f); hb = ch.wh("head"); ht = Wt(ch.rig, "head"); upv = (ht - hb).normalized(); d = ch.eyes() - hb
    return (d - upv * d.dot(upv)).normalized()
CAMK = []      # (frame, location, target, lens)
def K(f, loc, tgt, lens): CAMK.append((f, Vector(loc), Vector(tgt), lens))
def around(ch, f, off, lens, tgt_off=(0, 0, 0)):
    e = face_of(ch, f); K(f, e + Vector(off), e + Vector(tgt_off), lens)
# Cockpit camera stations (checked clear by camcheck.py): FC front-centre above the pedestal, FL front-left by the left
# side window, FR front-right, the CORRIDOR between the pilots (x 0.0-0.2, z 1.5) for moving front <-> back, BACK behind
# the captain seat (over-the-shoulder windscreen view). The camera never goes below z 1.3 in front of the hero except
# in the altimeter and throttle inserts.
FC = Vector((0.05, 4.62, 1.46)); FL = Vector((-0.92, 4.58, 1.42)); FR = Vector((0.28, 4.62, 1.44))
COR = Vector((0.14, 3.58, 1.56)); BACK = Vector((-0.10, 3.25, 1.52)); WS = Vector((-0.85, 6.5, 0.96))
# v012 round 1: front <-> back moves go round his LEFT side (SIDE -> BACKL -> BACK), never across the glareshield, so his
# head stays in frame the whole way
SIDE = Vector((-0.95, 4.45, 1.45)); BACKL = Vector((-0.80, 3.55, 1.62))
BACK = Vector((-0.02, 3.65, 1.55)); PROF = Vector((0.02, 4.02, 1.48))
def prof_k(f, lens=22, look=0.0): e_ = face_of(HERO, f); K(f, PROF, e_.lerp(WS, look), lens)
def back_k(f, off=(0, 0, 0), lens=16):
    p_ = BACK + Vector(off); e_ = face_of(HERO, f)
    K(f, p_, p_ + ((e_ - p_).normalized() + (WS - p_).normalized()) * 0.8, lens)
def side_k(f, lens=24): K(f, SIDE, face_of(HERO, f), lens)
def backl_k(f, lens=22): K(f, BACKL, face_of(HERO, f) + Vector((0.05, 0.60, -0.10)), lens)
def mid(a, b, u=0.5): return a.lerp(b, u)
# 0-4 s: wake up (close on his face from the aisle front-left, slowly arcing), then who is around him
around(HERO, 1, (-0.55, 0.52, 0.20), 36, (0, 0, -0.04))
around(HERO, 45, (-0.46, 0.58, 0.14), 37, (0, 0, -0.03))
around(HERO, 85, (-0.36, 0.62, 0.08), 36, (0, 0, -0.02))
around(HERO, 115, (-0.45, 0.66, 0.12), 32)
e3 = face_of(C["PAX3"], 150); eh = face_of(HERO, 150); K(150, Vector((-0.05, -0.35, 1.40)), eh.lerp(e3, 0.30), 24)
e1 = face_of(C["PAX1"], 200); eh = face_of(HERO, 200); K(200, Vector((-0.02, -0.40, 1.44)), eh.lerp(e1, 0.30), 24)
eh = face_of(HERO, 228); K(228, Vector((0.25, -1.02, 1.42)), eh, 26)
# 4-6.7 s: flying perfectly level: from above the empty window seat: his face, a pan to the window (wing, level horizon), back
eh = face_of(HERO, 255); K(255, Vector((0.55, -1.05, 1.45)), eh, 24)
# over his shoulder to the window (wing, level horizon) with his head in frame
eh = face_of(HERO, 285); K(285, Vector((0.32, -1.22, 1.46)), eh.lerp(Vector((1.80, -1.62, 1.22)), 0.38), 20)
eh = face_of(HERO, 322); K(322, Vector((0.30, -1.26, 1.44)), eh.lerp(Vector((1.80, -1.62, 1.22)), 0.38), 21)
eh = face_of(HERO, 352); K(352, Vector((0.42, -1.12, 1.42)), eh, 26)
around(HERO, 395, (0.40, 0.55, 0.10), 28)
around(HERO, 420, (-0.12, 0.62, 0.26), 26)
# 6.7-9.2 s: stands up into the aisle
around(HERO, 445, (-0.74, 0.36, 0.40), 24, (0, 0, -0.06))      # in the aisle gap beside his row: clear of the row-5 seat back
around(HERO, 500, (-0.30, 1.20, 0.05), 26, (0, 0, -0.15))
# 9.2-10.9 s: walks to the cockpit, the camera backs up the aisle ahead of him, swaying side to side (chest logo reads)
around(HERO, 540, (-0.18, 1.30, -0.02), 28, (0, 0, -0.22))
around(HERO, 580, (0.12, 1.25, 0.02), 28, (0, 0, -0.22))
around(HERO, 620, (-0.10, 1.30, -0.02), 28, (0, 0, -0.22))
around(HERO, 650, (0.05, 1.30, -0.05), 26, (-0.25, 0.4, -0.35))
# 10.9-13.2 s: the captain collapsed in the doorway: low in the cockpit looking back at both faces
ec = face_of(CAPT, 690); eh = face_of(HERO, 690); K(690, Vector((0.10, 3.45, 1.00)), ec.lerp(eh, 0.55), 20)   # corridor between the pilot seats, clear of both seat backs
ec = face_of(CAPT, 745); eh = face_of(HERO, 745); K(745, Vector((0.12, 3.55, 1.08)), ec.lerp(eh, 0.60), 20)
# 13.2-15.5 s: the first officer slumped in his seat: he shakes him by the shoulder (two-shot from the front)
ef = face_of(FO, 800); eh = face_of(HERO, 800); K(800, FC + Vector((0.10, 0, 0)), mid(ef, eh, 0.62), 21)
ef = face_of(FO, 860); eh = face_of(HERO, 860); K(860, FR, mid(ef, eh, 0.62), 21)
ef = face_of(FO, 910); eh = face_of(HERO, 910); K(910, FC + Vector((0.05, 0, 0.02)), mid(ef, eh, 0.6), 22)
# 15.5-20.4 s: he gets into the left seat and grabs the radio: front-left, close
eh = face_of(HERO, 955); K(955, FL + Vector((0.30, 0.0, 0.06)), eh, 22)
eh = face_of(HERO, 1005); K(1005, FL, eh, 26)
eh = face_of(HERO, 1045); K(1045, FL + Vector((-0.02, -0.04, -0.03)), mid(eh, Vector((-1.0, 4.1, 1.0)), 0.35), 24)
eh = face_of(HERO, 1100); K(1100, Vector((-0.16, 4.62, 1.46)), eh, 30)
eh = face_of(HERO, 1160); K(1160, Vector((-0.22, 4.64, 1.44)), eh, 32)
eh = face_of(HERO, 1220); K(1220, Vector((-0.14, 4.62, 1.46)), eh, 30)
# 20.4-21.2 s: no one answers: the radio lights and his face
eh = face_of(HERO, 1258); K(1258, Vector((0.05, 4.60, 1.32)), mid(eh, Vector((0.0, 4.40, 0.72)), 0.45), 24)
# 21.2-25.8 s: hangs the mic up, gets up and tries to pull the FO out: from the front between the seats
eh = face_of(HERO, 1305); K(1305, FC + Vector((-0.25, 0, -0.02)), eh, 26)
eh = face_of(HERO, 1370); K(1370, FR + Vector((0.0, 0.0, 0.04)), eh, 20)
ef = face_of(FO, 1420); eh = face_of(HERO, 1420); K(1420, FC + Vector((0.05, 0, 0.02)), mid(ef, eh, 0.72), 20)
ef = face_of(FO, 1470); eh = face_of(HERO, 1470); K(1470, FC + Vector((0.10, 0, 0.14)), mid(ef, eh, 0.70) + Vector((0, 0, -0.06)), 18)
ef = face_of(FO, 1505); eh = face_of(HERO, 1505); K(1505, FR + Vector((0.10, 0.04, 0.14)), mid(ef, eh, 0.80) + Vector((0, 0, -0.04)), 17)
eh = face_of(HERO, 1530); K(1530, FC + Vector((0.05, 0, 0.14)), eh, 18)
# 25.8-28.7 s: alarms, red light: he drops into the seat; on his face, with the red beacon flashing behind him
eh = face_of(HERO, 1550); K(1550, FC + Vector((-0.05, 0.0, 0.12)), eh, 20)
eh = face_of(HERO, 1600); K(1600, FC + Vector((-0.35, 0, -0.04)), eh, 28)
eh = face_of(HERO, 1660); K(1660, FL + Vector((0.12, 0.02, -0.02)), eh, 28)
eh = face_of(HERO, 1700); K(1700, FC + Vector((-0.20, 0, -0.03)), eh, 26)
# 28.7-30.3 s: diving: the camera rides the corridor back to over his shoulder: the windscreen with the ground rushing up
prof_k(1740, 18, 0.25)
prof_k(1790, 18, 0.28)
# 30.3-37 s: he grabs the controls: back through the corridor to the front, face + hands on the yoke, orbit left
eh = face_of(HERO, 1826); K(1826, FC + Vector((0.0, 0, 0.02)), eh, 22)
eh = face_of(HERO, 1840); K(1840, FC + Vector((-0.30, 0, -0.04)), mid(eh, Vector((-0.56, 4.40, 0.88)), 0.40), 22)
eh = face_of(HERO, 1920); K(1920, FL + Vector((0.15, 0.03, 0.12)), mid(eh, Vector((-0.56, 4.40, 0.88)), 0.35), 22)
eh = face_of(HERO, 1965); K(1965, FL + Vector((0.08, 0.02, 0.16)), mid(eh, Vector((-0.56, 4.40, 0.88)), 0.32), 23)
eh = face_of(HERO, 2006); K(2006, FL + Vector((0.0, -0.02, -0.02)), mid(eh, Vector((-0.56, 4.40, 0.88)), 0.30), 22)
eh = face_of(HERO, 2050); K(2050, FC + Vector((-0.30, 0, 0.02)), eh, 25)
eh = face_of(HERO, 2100); K(2100, FL + Vector((0.30, 0.03, 0.02)), eh, 26)
eh = face_of(HERO, 2180); K(2180, FC + Vector((-0.10, 0, 0)), eh, 26)
# 37-41.3 s: level but sinking: down over the pedestal to the altimeter unwinding, then up to his face
DIAL = Vector((-0.26, 5.01, 0.75)); PTOP = Vector((-0.26, 5.0, 1.05))
fs(2292); HANDR = HERO.wh("wrist.R")
eh = face_of(HERO, 2204); K(2204, FC + Vector((-0.12, 0, 0.0)), eh, 28)
K(2226, Vector((-0.12, 4.62, 1.30)), PTOP, 36)
K(2237, Vector((-0.18, 4.70, 1.06)), DIAL, 48)
K(2258, Vector((-0.20, 4.72, 1.02)), DIAL, 56)
K(2267, Vector((-0.12, 4.62, 1.30)), PTOP, 36)
eh = face_of(HERO, 2292); K(2292, Vector((-0.05, 4.66, 1.32)), eh, 28)
eh = face_of(HERO, 2440); K(2440, FC + Vector((-0.12, 0, 0)), eh, 28)
# 41.3-44.2 s: the long field ahead: through the corridor to over his shoulder, then back to his face
prof_k(2480)
back_k(2520); back_k(2562, (-0.02, 0.04, 0.0))
prof_k(2602)
eh = face_of(HERO, 2645); K(2645, FC + Vector((0.05, 0, 0)), eh, 26)
# 44.2-49.6 s: could land now; the throttles: his right hand to the levers and his face
eh = face_of(HERO, 2690); K(2690, FR, eh, 26)
eh = face_of(HERO, 2790); K(2790, Vector((0.30, 4.62, 1.30)), mid(eh, Vector((-0.05, 4.55, 0.87)), 0.55), 24)
eh = face_of(HERO, 2880); K(2880, Vector((0.22, 4.58, 1.26)), mid(eh, Vector((-0.05, 4.55, 0.87)), 0.5), 29)
eh = face_of(HERO, 2950); K(2950, FR, eh, 28)
# 49.6-52.5 s: or keep flying and hope someone wakes up: he looks back at the FO (his face and the FO)
eh = face_of(HERO, 3025); K(3025, FR + Vector((-0.05, 0, 0)), eh, 22)
ef = face_of(FO, 3065); K(3065, FR + Vector((-0.02, 0.0, 0.02)), ef + Vector((0, 0, -0.05)), 22)
eh = face_of(HERO, 3110); K(3110, FC + Vector((0.08, 0, 0)), eh, 22)
# 52.5-55.7 s: this field might be your only chance: back to the windscreen, the field filling it
prof_k(3150)
back_k(3190); back_k(3262, (-0.02, 0.05, 0.0))
prof_k(3300)
# 55.7-58 s: what do you do? the camera floats round to his face
eh = face_of(HERO, 3342); K(3342, FC + Vector((0.05, 0, 0)), eh, 28)
around(HERO, 3400, (0.25, 0.55, 0.05), 34)
around(HERO, END, (0.14, 0.45, 0.03), 40)
CAMK.sort(key=lambda k: k[0])
cl = vpchip([(f, l) for f, l, t, n in CAMK]); ctg = vpchip([(f, t) for f, l, t, n in CAMK]); cln = pchip([(f, n) for f, l, t, n in CAMK])
CAM = O["CAM_Film"]; CTG = O["CAM_Target"]
SHK = {f: Vector((shake(f, 1550, 2006, 0.010, 1.7, 1), shake(f, 1550, 2006, 0.006, 2.1, 3), shake(f, 1550, 2006, 0.010, 1.9, 5)))
       for f in range(1, END + 1)}
BASE = {f: cl(f) + SHK[f] for f in range(1, END + 1)}

# ---------- clearance pass (v012 fix): the lens keeps MIN_SET from every set mesh (static + keyed: yokes, throttles,
# mic, needles) and MIN_BODY from every character's bones (capsules round the bone axes). Pushes are solved on every
# 2nd frame, smoothed over +-0.3 s so the move stays fluid, then re-checked; three rounds, then an exact final push.
MIN_SET, MIN_BODY, MIN_HEAD = 0.12, 0.14, 0.34
SETOBJS = [o for c in ("CABIN", "COCKPIT") for o in bpy.data.collections[c].all_objects if o.type == 'MESH' and not o.hide_render]
def animated(o):
    while o:
        if o.animation_data and o.animation_data.action: return True
        o = o.parent
    return False
MOV = [o for o in SETOBJS if animated(o)]; STA = [o for o in SETOBJS if o not in MOV]
fs(1); B_STA = bvh_of(STA)
log("clearance set objects static", len(STA), "moving", len(MOV), [o.name for o in MOV][:30])
CAPS = [("head", 0.12), ("neck01", 0.07), ("spine01", 0.15), ("spine03", 0.16), ("spine05", 0.15), ("pelvis.L", 0.10), ("pelvis.R", 0.10)]
for s_ in "LR":
    CAPS += [("upperarm01." + s_, 0.065), ("upperarm02." + s_, 0.06), ("lowerarm01." + s_, 0.055), ("lowerarm02." + s_, 0.05),
             ("wrist." + s_, 0.055), ("upperleg01." + s_, 0.10), ("upperleg02." + s_, 0.09), ("lowerleg01." + s_, 0.07),
             ("lowerleg02." + s_, 0.06), ("foot." + s_, 0.06)]
def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9))); q = a + ab * t
    return (p - q).length, q
def need(f, p, bm):
    """the push vector that clears p at frame f (the frame must be set)"""
    push = Vector((0, 0, 0))
    for _ in range(4):
        q = p + push; worst = None
        for B in (B_STA, bm):
            if B is None: continue
            h = B.find_nearest(q, 1.0)
            if h[0] is not None and h[3] < MIN_SET:
                n = (q - h[0]); n = n.normalized() if n.length > 1e-6 else h[1]
                if worst is None or MIN_SET - h[3] > worst[0]: worst = (MIN_SET - h[3], n)
        for ch in C.values():
            if (ch.eyes() - q).length > 1.8: continue
            for bn, r in CAPS:
                if bn not in ch.rig.pose.bones: continue
                d, qq = seg_dist(q, ch.wh(bn), Wt(ch.rig, bn))
                gap = r + (MIN_HEAD if bn == "head" else MIN_BODY) - d
                if gap > 0 and (worst is None or gap > worst[0]):
                    n = q - qq; worst = (gap, n.normalized() if n.length > 1e-6 else Vector((0, -1, 0)))
        if worst is None: break
        push += worst[1] * (worst[0] + 0.004)
    return push
OFF = {f: Vector((0, 0, 0)) for f in range(1, END + 1)}
FR_S = list(range(1, END + 1, 2)) + [END]
def solve_round(fr):
    raw = {}
    for f in fr:
        fs(f); bm = bvh_of(MOV) if MOV else None
        raw[f] = need(f, BASE[f] + OFF[f], bm)
    return raw
W = 18                     # +-18 frames (0.3 s)
GK = [math.exp(-0.5 * (k / (W / 2.2)) ** 2) for k in range(-W, W + 1)]
for rnd in range(3):
    raw = solve_round(FR_S)
    nbad = sum(1 for v in raw.values() if v.length > 0.002)
    log("clearance round", rnd, "frames pushed", nbad, "max push", round(max(v.length for v in raw.values()), 3))
    if nbad == 0: break
    full = {}
    for f in range(1, END + 1):
        a_ = max(k for k in FR_S if k <= f); b_ = min(k for k in FR_S if k >= f)
        u = 0 if b_ == a_ else (f - a_) / (b_ - a_); full[f] = raw[a_].lerp(raw[b_], u)
    for f in range(1, END + 1):
        acc = Vector((0, 0, 0)); ws = 0.0
        for k, g in zip(range(-W, W + 1), GK):
            ff = min(END, max(1, f + k)); acc += full[ff] * g; ws += g
        sm = acc / ws
        # keep at least the raw need at this frame (smoothing must never thin the clearance)
        if full[f].length > sm.length: sm = full[f].copy()
        OFF[f] += sm * 1.15
# exact residual push on every frame
res_n = 0
for f in range(1, END + 1):
    fs(f); bm = bvh_of(MOV) if MOV else None
    r_ = need(f, BASE[f] + OFF[f], bm)
    if r_.length > 0.002: res_n += 1; OFF[f] += r_
log("clearance residual frames", res_n, "max offset", round(max(v.length for v in OFF.values()), 3))
# the face must not hide behind set geometry when the camera is on the hero: report it (lens blockers are re-staged by hand)
blk = []
for f in range(1, END + 1, 4):
    fs(f); p = BASE[f] + OFF[f]; e = HERO.eyes(); d = e - p
    fwd = (ctg(f) - p).normalized()
    if d.normalized().dot(fwd) > 0.85:
        bm = bvh_of(MOV) if MOV else None
        if B_STA.ray_cast(p, d.normalized(), d.length - 0.06)[0] is not None or (bm and bm.ray_cast(p, d.normalized(), d.length - 0.06)[0] is not None):
            blk.append(f)
log("face blocked frames", blk)
for f in range(1, END + 1):
    sh = SHK[f]
    CAM.location = BASE[f] + OFF[f]; CAM.keyframe_insert("location", frame=f)
    CTG.location = ctg(f) + sh * 0.5; CTG.keyframe_insert("location", frame=f)
    CAM.data.lens = cln(f); CAM.data.keyframe_insert("lens", frame=f)

# ================================================================== tidy + VO + save
for ch in C.values(): quat_continuity(ch.rig)
quat_continuity(MIC)
meshes(True)
sc = bpy.context.scene
if not sc.sequence_editor: sc.sequence_editor_create()
try:
    st = sc.sequence_editor.strips.new_sound("VO", VO, 1, 1)
except AttributeError:
    st = sc.sequence_editor.sequences.new_sound("VO", VO, 1, 1)
sc.frame_start, sc.frame_end = 1, END
fs(1)
json.dump(LOG, open(os.path.join(os.path.dirname(OUT), "animate_log.json"), "w"), indent=0)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
