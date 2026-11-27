"""BelugaRescue v009 stage B: the diver, the beluga, the spectators, bubbles/splash, the ONE camera (no cuts), VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO from the start (BelugaRescue_v008 recording, 1736 frames). Beat frames = 1 + round(s*60):
1 'She dove' / 179 'but as she sank' / 300 'the cold sent her legs' / 480 'She couldn't swim back up' / 572 'as she started to drown'
683 'a beluga whale noticed' / 826 'These whales are smart' / 980 'it could tell' / 1100 'It swam over' / 1166 'took her leg'
1278 'started pushing her up' / 1387 'just as she ran out of breath' / 1496 'the beluga lifted her' / 1605 'where she could finally breathe'"""
import bpy, sys, math, random, os, json
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(22)
END = 1736
FLOOR = -5.0
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
DR, DB = O["Diver"], O["Diver.body"]
BR, BW = O["Beluga"], O["Beluga.body"]

# ================================================================== diver rig
CT = make_human_ctrl(DR)
add_hand_limits(DR)
for pb in DR.pose.bones: pb.rotation_mode = 'QUATERNION'
for s in "LR":
    lo = DR.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
H = Human(CT)
RH = H.root_head.copy()

def body_M(pos, ypr):
    y, p, r = ypr
    return Matrix.Translation(Vector(pos)) @ (Matrix.Rotation(math.radians(y), 4, 'Z') @ Matrix.Rotation(math.radians(p), 4, 'X') @
                                             Matrix.Rotation(math.radians(r), 4, 'Y')) @ Matrix.Translation(-RH)
def key_body(f, pos, ypr):
    CT.key_world("root", f, body_M(pos, ypr) @ CT.rest("root"))
def key_spine(f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
_HS = {}
def head_signs():
    if _HS: return _HS["s"]
    pb = DR.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(DR, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(DR, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS["s"] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS["s"]
def key_head(f, yaw, pitch, roll=0.0):
    """yaw +: toward her own left; pitch +: chin down"""
    sx, sz = head_signs()
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])
def key_pole(s, f, target, kind):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(target) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)
REST_ANK = {s: CT.BN["foot." + s].head_local.copy() for s in "LR"}
def key_foot_world(s, f, ankle_w, R3, pole_w):
    M = Matrix.Translation(ankle_w) @ R3.to_4x4() @ Matrix.Translation(-REST_ANK[s]) @ CT.rest("IK_foot." + s)
    CT.key_world("IK_foot." + s, f, M); key_pole(s, f, pole_w, "knee")

# ---------------------------------------------------------------- channels: (frame, value) tables, PCHIP-interpolated
def P3(keys):
    fx = [pchip([(k[0], k[1][i]) for k in keys]) for i in range(3)]
    return lambda f: Vector([fx[i](f) for i in range(3)])
def P1(keys):
    return pchip(keys)
# body position (pelvis/root) and orientation (yaw, pitch(+ = lean forward / head toward -Y), roll)
POS = P3([(1, (0.55, 1.10, 1.30)), (12, (0.55, 1.05, 0.25)), (30, (0.50, 0.70, -1.05)), (60, (0.42, 0.25, -2.00)),
          (100, (0.35, -0.10, -2.70)), (150, (0.28, -0.25, -3.15)), (200, (0.22, -0.20, -3.55)), (250, (0.20, -0.12, -3.85)),
          (285, (0.20, -0.10, -4.06)), (300, (0.20, -0.10, -4.10)), (330, (0.20, -0.08, -4.16)), (480, (0.20, -0.08, -4.14)),
          (500, (0.20, -0.08, -4.00)), (540, (0.18, -0.08, -3.30)), (572, (0.18, -0.06, -2.95)), (620, (0.16, -0.04, -2.78)),
          (683, (0.15, 0.00, -2.68)), (800, (0.12, 0.05, -2.56)), (980, (0.10, 0.08, -2.36)), (1100, (0.10, 0.10, -2.10)),
          (1166, (0.10, 0.10, -1.86)), (1200, (0.10, 0.10, -1.78)), (1278, (0.10, 0.12, -1.55)), (1387, (0.10, 0.14, -1.20)),
          (1450, (0.10, 0.15, -0.95)), (1496, (0.10, 0.15, -0.78)), (1525, (0.10, 0.14, -0.62)), (1560, (0.10, 0.12, -0.50)),
          (1605, (0.10, 0.10, -0.54)), (1650, (0.10, 0.08, -0.50)), (1700, (0.10, 0.06, -0.53)), (END, (0.10, 0.05, -0.51))])
ROT = P3([(1, (0, 155, 0)), (30, (0, 150, 0)), (60, (0, 140, -4)), (100, (0, 120, 4)), (150, (0, 90, 0)), (200, (0, 45, 0)),
          (250, (0, 12, 0)), (285, (0, 4, 0)), (300, (0, 6, 0)), (330, (0, 10, 0)), (480, (0, 10, 0)), (500, (0, 2, 0)),
          (540, (0, -4, 0)), (572, (0, -2, 3)), (620, (0, 2, -3)), (683, (0, 0, 2)), (800, (0, 3, -2)), (980, (0, 2, 2)),
          (1100, (0, 4, 0)), (1166, (0, -8, 0)), (1278, (0, -10, 0)), (1387, (0, -10, 0)), (1496, (0, -8, 0)), (1525, (0, -4, 0)),
          (1605, (0, 2, 0)), (END, (0, 0, 0))])
SPINE = P3([(1, (-6, 0, 0)), (60, (-4, 0, 0)), (100, (6, 0, 0)), (150, (4, 0, 0)), (250, (2, 0, 0)), (285, (8, 0, 0)), (300, (6, 0, 0)),
            (330, (40, 0, 0)), (480, (40, 0, 0)), (500, (6, 0, 0)), (540, (-8, 0, 0)), (572, (-6, 0, 0)), (683, (2, 0, 0)),
            (980, (6, 0, 0)), (1166, (4, 0, 0)), (1278, (-4, 0, 0)), (1387, (-8, 0, 0)), (1496, (-10, 0, 0)), (1540, (-6, 0, 0)),
            (1605, (-4, 0, 0)), (END, (-2, 0, 0))])
HEAD = P3([(1, (0, 28, 0)), (60, (0, 22, 0)), (150, (0, 12, 0)), (250, (0, 10, 0)), (285, (0, 14, 0)), (330, (0, 26, 0)),
           (420, (6, 22, 0)), (480, (0, 8, 0)), (520, (0, -26, 0)), (572, (0, -22, 0)), (620, (-6, -10, 0)), (683, (8, -6, 0)),
           (760, (22, -4, 0)), (850, (20, -10, 0)), (980, (18, -6, 0)), (1100, (14, -4, 0)), (1166, (0, 14, 0)), (1240, (0, 18, 0)),
           (1300, (0, -14, 0)), (1387, (0, -6, 0)), (1440, (0, 6, 4)), (1496, (0, -10, 0)), (1525, (0, -28, 0)), (1560, (0, -26, 0)),
           (1605, (0, -8, 0)), (1640, (-24, -2, 0)), (1690, (-30, 0, 0)), (END, (-28, 2, 0))])
# arms: wrist offset from the shoulder in the BODY frame (x = her left, y = back, z = up), mirrored for R (x -> -x)
def arm_tab(keys): return P3(keys)
ARM_L = arm_tab([(1, (0.05, -0.10, 0.48)), (60, (0.06, -0.10, 0.48)), (85, (0.20, -0.12, 0.42)), (110, (0.42, 0.05, -0.05)),
                 (130, (0.20, -0.05, -0.30)), (150, (0.12, -0.15, 0.30)), (175, (0.30, -0.10, 0.20)), (200, (0.42, -0.06, -0.05)),
                 (250, (0.36, -0.10, -0.20)), (285, (0.36, -0.10, -0.10)), (300, (0.30, -0.12, -0.15)),
                 (480, (0.30, -0.12, -0.15)), (490, (0.36, -0.10, 0.25)), (520, (0.40, 0.08, -0.20)), (545, (0.30, -0.10, 0.20)),
                 (572, (0.22, -0.16, 0.42)), (600, (0.38, -0.05, 0.10)), (625, (0.15, -0.20, 0.44)), (650, (0.40, -0.02, 0.05)),
                 (683, (0.20, -0.18, 0.40)), (720, (0.38, -0.10, 0.00)), (760, (0.25, -0.20, 0.32)), (800, (0.38, -0.08, -0.05)),
                 (850, (0.26, -0.20, 0.25)), (900, (0.40, -0.06, -0.06)), (980, (0.30, -0.18, 0.20)), (1040, (0.40, -0.05, -0.10)),
                 (1100, (0.32, -0.15, 0.10)), (1166, (0.36, -0.10, -0.05)), (1278, (0.38, -0.08, 0.05)), (1387, (0.36, -0.04, -0.12)),
                 (1460, (0.30, -0.06, -0.25)), (1496, (0.30, -0.10, -0.25)), (1525, (0.34, -0.20, -0.20)), (1560, (0.36, -0.22, -0.22)),
                 (1605, (0.34, -0.24, -0.20)), (1650, (0.36, -0.20, -0.24)), (1700, (0.34, -0.24, -0.20)), (END, (0.36, -0.22, -0.22))])
ARM_R = arm_tab([(1, (0.05, -0.10, 0.48)), (60, (0.06, -0.10, 0.48)), (85, (0.20, -0.12, 0.42)), (110, (0.42, 0.05, -0.05)),
                 (130, (0.20, -0.05, -0.30)), (150, (0.12, -0.15, 0.30)), (175, (0.30, -0.10, 0.20)), (200, (0.42, -0.06, -0.05)),
                 (250, (0.36, -0.10, -0.20)), (285, (0.36, -0.10, -0.10)), (300, (0.30, -0.12, -0.15)),
                 (480, (0.30, -0.12, -0.15)), (490, (0.36, -0.10, 0.25)), (520, (0.40, 0.08, -0.20)), (545, (0.30, -0.10, 0.20)),
                 (572, (0.40, -0.04, 0.08)), (600, (0.18, -0.20, 0.44)), (625, (0.40, -0.04, 0.06)), (650, (0.16, -0.22, 0.42)),
                 (683, (0.38, -0.08, 0.02)), (720, (0.22, -0.20, 0.38)), (760, (0.38, -0.08, 0.02)), (800, (0.26, -0.20, 0.30)),
                 (850, (0.40, -0.06, -0.04)), (900, (0.28, -0.20, 0.24)), (980, (0.40, -0.06, -0.08)), (1040, (0.30, -0.18, 0.18)),
                 (1100, (0.38, -0.08, -0.08)), (1166, (0.30, -0.16, 0.10)), (1278, (0.36, -0.10, 0.02)), (1387, (0.34, -0.06, -0.14)),
                 (1460, (0.30, -0.06, -0.25)), (1496, (0.30, -0.10, -0.25)), (1525, (0.34, -0.20, -0.20)), (1560, (0.36, -0.22, -0.22)),
                 (1605, (0.34, -0.24, -0.20)), (1650, (0.36, -0.20, -0.24)), (1700, (0.34, -0.24, -0.20)), (END, (0.36, -0.22, -0.22))])
# legs: ankle offset from the hip in the BODY frame (x mirrored for R), plus toe point (deg, + = pointed)
LEG_L = P3([(1, (-0.02, 0.02, -0.84)), (60, (-0.02, 0.04, -0.82)), (90, (-0.02, 0.18, -0.74)), (115, (-0.02, -0.04, -0.83)),
            (140, (-0.02, 0.18, -0.74)), (165, (-0.02, -0.02, -0.83)), (200, (0.02, 0.10, -0.78)), (250, (0.04, -0.06, -0.80)),
            (285, (0.06, -0.04, -0.80)), (480, (0.06, -0.04, -0.80)), (500, (0.04, -0.02, -0.84)), (540, (0.02, 0.04, -0.84)),
            (683, (0.03, 0.02, -0.84)), (980, (0.04, 0.04, -0.83)), (1100, (0.05, 0.02, -0.83)), (1166, (0.08, 0.22, -0.76)),
            (1200, (0.10, 0.26, -0.72)), (1496, (0.10, 0.26, -0.72)), (1525, (0.06, -0.20, -0.70)), (1605, (0.06, -0.10, -0.78)),
            (1660, (0.06, 0.08, -0.76)), (END, (0.06, -0.06, -0.78))])
LEG_R = P3([(1, (-0.02, 0.02, -0.84)), (60, (-0.02, 0.04, -0.82)), (90, (-0.02, -0.02, -0.83)), (115, (-0.02, 0.18, -0.74)),
            (140, (-0.02, -0.02, -0.83)), (165, (-0.02, 0.18, -0.74)), (200, (0.02, -0.04, -0.80)), (250, (0.04, 0.06, -0.78)),
            (285, (0.06, -0.04, -0.80)), (300, (0.06, -0.06, -0.78)), (330, (0.04, -0.34, -0.30)), (480, (0.04, -0.34, -0.30)),
            (500, (0.04, -0.06, -0.83)), (540, (0.02, 0.02, -0.84)), (683, (0.03, 0.03, -0.84)), (980, (0.04, 0.02, -0.84)),
            (1100, (0.05, 0.04, -0.83)), (1150, (0.05, -0.40, -0.68)), (1180, (0.05, -0.50, -0.62)), (1496, (0.05, -0.50, -0.62)),
            (1525, (0.05, -0.30, -0.74)), (1560, (0.05, 0.10, -0.76)), (1605, (0.05, 0.10, -0.76)), (1660, (0.05, -0.08, -0.76)),
            (END, (0.05, 0.06, -0.78))])
TOE = P1([(1, 40), (250, 35), (275, 10), (285, 0), (300, 0), (330, 45), (480, 45), (500, 50), (980, 45), (1140, 45), (1166, 55), (1496, 55), (1560, 35), (END, 30)])
PLANT_L = (285, 480)                     # left foot planted on the tank floor
PLANT_R = (285, 318)                     # right foot planted until the cramp pulls the knee up

hip = {s: CT.BN["upperleg01." + s].head_local.copy() for s in "LR"}
plant_pos = {}
def legs_key(f, Bm, R3):
    for s, tab in (("L", LEG_L), ("R", LEG_R)):
        sx = 1 if s == "L" else -1
        o = tab(f); o = Vector((o.x * sx, o.y, o.z))
        hipw = Bm @ hip[s]
        pl = PLANT_L if s == "L" else PLANT_R
        if pl[0] <= f <= pl[1]:
            if s not in plant_pos:
                fs(pl[0]); a_ = (body_M(POS(pl[0]), ROT(pl[0])) @ (hip[s] + Vector((o.x, o.y, o.z))))
                plant_pos[s] = Vector((a_.x, a_.y, FLOOR + REST_ANK[s].z + 0.002))
            ank = plant_pos[s]; Rf = Matrix.Rotation(0, 3, 'Z')
            pole = ank + Vector((sx * 0.05, -0.8, 0.5))
        else:
            ank = Bm @ (hip[s] + o)
            pt = TOE(f) if not (s == "R" and 300 <= f <= 1100) else TOE(f) + 10
            Rf = R3 @ Matrix.Rotation(math.radians(-pt), 3, 'X')
            pole = Bm @ (hip[s] + Vector((sx * 0.06, -0.8, -0.35)))
        key_foot_world(s, f, ank, Rf, pole)

SH = {s: CT.BN["upperarm01." + s].head_local.copy() for s in "LR"}
def arms_key(f, Bm, R3, skip=()):
    for s, tab in (("L", ARM_L), ("R", ARM_R)):
        if s in skip: continue
        sx = 1 if s == "L" else -1
        o = tab(f); o = Vector((o.x * sx * 0.62, o.y - 0.10, o.z))
        if o.length > 0.40: o = o * (0.40 / o.length)
        if f > 200:                                       # sculling: arms never freeze
            ph = f * 0.10 + (0.0 if s == "L" else 1.7)
            o = o + Vector((0.0, 0.04 * math.cos(ph), 0.06 * math.sin(ph)))
        shw = Wh(DR, "upperarm01." + s)
        Wr = shw + R3 @ o
        d = (Wr - shw).normalized()
        n = (R3 @ Vector((-sx * 0.3, 0.6, -0.4))).normalized()          # palm back/inward: a natural sweep
        pole = shw + R3 @ Vector((sx * 0.30, 0.45, -0.15))
        H.key_hand(s, f, Wr, (d + R3 @ Vector((0, 0, -0.15))).normalized(), n, pole=pole)

# ---------------------------------------------------------------- key the diver every 3 frames
KF = sorted(set(list(range(1, END + 1, 3)) + [END]))
for f in KF:
    fs(f)
    pos, rot = POS(f), ROT(f)
    # small life: a breathing/shiver on the cramp, a bob while floating
    if 330 <= f <= 480: pos = pos + Vector((0.010 * math.sin(f * 1.9), 0, 0.008 * math.sin(f * 2.3)))
    key_body(f, pos, rot)
    sp = SPINE(f); key_spine(f, flex=sp.x + 1.2 * math.sin(2 * math.pi * f / 150), twist=sp.y, side=sp.z)
    hd = HEAD(f); key_head(f, hd.x, hd.y, hd.z)
    upd()
    Bm = body_M(pos, rot); R3 = Bm.to_3x3().normalized()
    legs_key(f, Bm, R3)
    arms_key(f, Bm, R3, skip=("L", "R") if 330 <= f <= 470 else ())
log("diver keyed", len(KF))

# ---- the cramp: both hands clutch the right calf (f330-470); palms on the leggings surface (ray-cast), 8 mm skin gap
LEGS_OBJ = O["Diver.leggings"]
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
for f in list(range(330, 471, 6)) + [470]:
    fs(f); bv = bvh_eval(LEGS_OBJ)
    k0, k1 = Wh(DR, "lowerleg01.R"), Wt(DR, "lowerleg02.R")
    R3 = body_M(POS(f), ROT(f)).to_3x3().normalized()
    axis = (k1 - k0).normalized()
    for s, frac, side_dir in (("R", 0.30, R3 @ Vector((-1, 0.25, 0))), ("L", 0.42, R3 @ Vector((1, 0.35, 0)))):
        c = k0.lerp(k1, frac); sd = (side_dir - axis * side_dir.dot(axis)).normalized()
        hit = bv.ray_cast(c + sd * 0.25, -sd, 0.5)
        pt = hit[0] if hit[0] is not None else c + sd * 0.06
        fing = (axis * -0.2 + (R3 @ Vector((0, 1, 0)))).normalized()
        fing = (fing - sd * fing.dot(sd)).normalized()
        place_hand(DR, s, f, pt, -sd, fing, skin=0.010)
        shw = Wh(DR, "upperarm01." + s); sx = 1 if s == "L" else -1
        key_pole(s, f, shw + R3 @ Vector((sx * 0.45, 0.20, -0.25)), "elbow")
for s in "LR":
    for f in (318, 330, 470, 485):
        apply_pose(DR, s, "relaxed" if f in (318, 485) else "cup_hold", f)
for s in "LR":
    for f in (1, 60, 286, 500, 572, 980, 1166, 1496, 1605, END):
        apply_pose(DR, s, "relaxed" if f not in (572, 980) else "open_alarm", f, amount=0.8)
# face: calm -> wince (cold) -> pain grimace -> panic -> drowning -> fading -> gasp -> relief smile
for f, sm, br, jaw, sq in ((1, 0.1, 0.2, 0.0, 0.0), (179, 0.0, 0.1, 0.0, 0.0), (300, -0.2, -0.4, 0.05, 0.3), (330, -0.5, -0.9, 0.15, 0.7),
                           (470, -0.5, -0.9, 0.15, 0.7), (500, -0.2, 0.5, 0.05, 0.1), (572, -0.3, 0.9, 0.25, 0.0), (683, -0.3, 0.9, 0.35, 0.0),
                           (980, -0.3, 0.8, 0.30, 0.0), (1166, -0.2, 0.6, 0.15, 0.2), (1387, -0.1, 0.2, 0.10, 0.5), (1480, 0.0, 0.1, 0.05, 0.6),
                           (1525, -0.1, 0.6, 0.30, 0.0), (1548, -0.1, 0.9, 0.90, 0.0), (1580, -0.1, 0.8, 0.80, 0.0), (1610, 0.0, 0.5, 0.40, 0.0), (1640, 0.4, 0.4, 0.15, 0.1),
                           (1670, 0.9, 0.3, 0.05, 0.2), (END, 0.9, 0.3, 0.05, 0.2)):
    key_face(DR, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(DR, [40, 230, 520, 700, 900, 1120, 1300, 1620, 1700])
eyes_closed(DR, 1440, 1515, ramp=12)
saccades(CT, 500, 1380, every=30, amp=(2.0, 3.0), seed=4)
log("quat flips fixed", quat_continuity(DR))

# ---- the cramp cue: a pulsing red glow on the leggings over the right calf (mesh-attached: Generated coords)
LM = LEGS_OBJ.data.materials[0]; nt = LM.node_tree
pr = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
bb = [Vector(c) for c in LEGS_OBJ.bound_box]; mn = Vector([min(v[i] for v in bb) for i in range(3)]); mx_ = Vector([max(v[i] for v in bb) for i in range(3)])
ka, kb = CT.BN["lowerleg01.R"].head_local, CT.BN["lowerleg01.R"].tail_local
calf = ka.lerp(kb, 0.45) + Vector((0, 0.035, 0))
cg = Vector([(calf[i] - mn[i]) / (mx_[i] - mn[i]) for i in range(3)])
tc = nt.nodes.new("ShaderNodeTexCoord"); sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'
sub.inputs[1].default_value = cg; nt.links.new(tc.outputs["Generated"], sub.inputs[0])
scl = nt.nodes.new("ShaderNodeVectorMath"); scl.operation = 'MULTIPLY'
scl.inputs[1].default_value = ((mx_.x - mn.x) / 0.07, (mx_.y - mn.y) / 0.07, (mx_.z - mn.z) / 0.13); nt.links.new(sub.outputs[0], scl.inputs[0])
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; nt.links.new(scl.outputs[0], ln.inputs[0])
fall = nt.nodes.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = 1.0
fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0; fall.interpolation_type = 'SMOOTHSTEP'
nt.links.new(ln.outputs[1], fall.inputs["Value"])
pv = nt.nodes.new("ShaderNodeValue"); pv.name = "CrampPulse"; pv.outputs[0].default_value = 0.0
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; nt.links.new(fall.outputs[0], mul.inputs[0]); nt.links.new(pv.outputs[0], mul.inputs[1])
pr.inputs["Emission Color"].default_value = (1.0, 0.05, 0.02, 1); nt.links.new(mul.outputs[0], pr.inputs["Emission Strength"])
PV = pv.outputs[0]
for f in range(1, END + 1, 4):
    v = 0.0
    if 318 <= f <= 520:
        env = min(1.0, (f - 318) / 20.0) * (1.0 if f < 480 else max(0.0, 1 - (f - 480) / 40.0))
        v = env * (2.2 + 1.8 * math.sin((f - 318) * 2 * math.pi / 36.0))
    PV.default_value = v; PV.keyframe_insert("default_value", frame=f)

# ================================================================== spectators: standing ON the gallery floor, watching the whale
for nm in ("SpecMan", "SpecWoman"):
    SR = O[nm]; home = Vector(SR["home"])
    C_ = make_human_ctrl(SR); add_hand_limits(SR)
    for pb in SR.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = SR.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    H_ = Human(C_); rh = H_.root_head
    ra = {s: C_.BN["foot." + s].head_local for s in "LR"}
    for f in (1, 500, 820, 900, 980, 1100, END):
        sway = 0.01 * math.sin(f * 0.02 + (1 if nm == "SpecMan" else 2))
        H_.key_root(f, Vector((home.x + sway, home.y, home.z + rh.z - 0.01)), yaw=0.0, flex=2.0)
        for s, sx in (("L", 1), ("R", -1)):
            a_ = ra[s]; tgt = Vector((home.x + sx * 0.11, home.y, home.z + a_.z))
            C_.key_world("IK_foot." + s, f, Matrix.Translation(tgt) @ Matrix.Translation(-a_) @ C_.rest("IK_foot." + s))
            n = "Pole_knee." + s; pb = C_.PB[n]; pb.location = C_.rest(n).to_3x3().inverted() @ (tgt + Vector((sx * 0.05, -0.8, 0.45)) - C_.BN[n].head_local)
            pb.keyframe_insert("location", frame=f, group=n)
        fs(f)
        for s, sx in (("L", 1), ("R", -1)):
            sh = Wh(SR, "upperarm01." + s)
            Wr = sh + Vector((sx * 0.10, -0.08, -0.50))
            H_.key_hand(s, f, Wr, Vector((sx * 0.08, -0.2, -1.0)), Vector((-sx, 0.0, 0.0)), pole=sh + Vector((sx * 0.25, 0.45, -0.25)))
            apply_pose(SR, s, "relaxed", f)
    for f in range(1, END + 1, 40):
        for n_, w in Human.SPINE_W.items():
            C_.key_rot(n_, f, [("X", (2.0 + 1.0 * math.sin(2 * math.pi * f / 230)) * w)])
    blinks(SR, [60, 420, 760, 880, 1010, 1300] if nm == "SpecMan" else [120, 500, 800, 930, 1150])
    for f, sm in ((1, 0.2), (820, 0.3), (880, 0.9), (980, 0.8), (1060, 0.3), (END, 0.3)):
        key_face(SR, f, smile=sm, brow=0.4 if 860 < f < 1000 else 0.1, jaw=0.15 if 880 <= f <= 980 else 0.0)
    SR["ctrl"] = True
log("spectators keyed")

# ================================================================== the beluga: path + undulation + head turns + the jaw
for pb in BR.pose.bones: pb.rotation_mode = 'XYZ'
BR.rotation_mode = 'QUATERNION'
GRIP_L = Vector((0.0, -0.80 * 4.0 / 1.81, 0.028 * 4.0 / 1.81))       # a point between the lips, 16 cm behind the snout tip
def whale_M(pos, fwd, up):
    """object matrix so the whale's head (-Y local) points along fwd and its back (+Z) toward up"""
    yv = -Vector(fwd).normalized(); z = Vector(up); z = (z - yv * z.dot(yv)).normalized(); x = yv.cross(z)
    M = Matrix((x, yv, z)).transposed().to_4x4(); M.translation = Vector(pos); return M
# free swimming path (chest position, heading) on the beats; the grip phase (1185-1600) is solved from her shin below
WPOS = P3([(1, (-5.5, 4.0, -2.2)), (200, (-4.5, 3.5, -2.4)), (400, (-3.0, 4.6, -2.0)), (600, (-4.0, 3.0, -2.6)), (683, (-3.0, 2.4, -2.4)),
           (760, (-2.6, 3.8, -2.7)), (826, (-2.2, 4.6, -2.9)), (900, (-0.6, 4.75, -3.0)), (980, (0.8, 4.7, -3.0)),
           (1040, (1.5, 3.2, -2.9)), (1100, (1.6, 0.2, -2.9)), (1150, (0.9, -1.7, -3.0))])
WFWD = P3([(1, (1, -0.3, 0)), (200, (1, 0.4, 0.05)), (400, (-0.6, -0.8, -0.1)), (600, (1, -0.6, 0)), (683, (0.6, 0.6, 0)),
           (760, (0.3, 1.0, -0.05)), (826, (1, 0.2, -0.05)), (900, (1, 0.0, 0.0)), (960, (1, -0.1, 0.0)), (1000, (0.6, -0.8, 0.0)),
           (1040, (0.2, -1.0, 0.0)), (1100, (-0.3, -1.0, 0.0)), (1150, (-0.3, 0.6, 0.6))])
GRIP0, GRIP1 = 1185, 1590
# the lips' gap with the jaw at its grip angle (head/neck straight): ankle sits 9 cm inside, between the lips
for bn in ("neck", "head", "jaw"): BR.pose.bones[bn].rotation_euler = (0, 0, 0)
BR.pose.bones["jaw"].rotation_euler = (math.radians(-20), 0, 0); BR.location = (0, 0, 0); BR.rotation_quaternion = (1, 0, 0, 0); upd()
LOWER = BR.pose.bones["jaw"].tail.copy(); UPPER = Vector((0, -0.885 * 4.0 / 1.81, 0.040 * 4.0 / 1.81))
GRIP_L = (LOWER + UPPER) / 2 + Vector((0, 0.09, 0))
BR.pose.bones["jaw"].rotation_euler = (0, 0, 0); upd()
log("grip gap mm", round((LOWER - UPPER).length * 1000), "grip local", tuple(round(x, 3) for x in GRIP_L))
def shin_pt(f):
    fs(f); k = Wh(DR, "lowerleg01.R"); a_ = Wt(DR, "lowerleg02.R"); return a_, (a_ - k).normalized()
WM = {}
def grip_M(f):
    p, s_dir = shin_pt(f)
    fwd = -s_dir                                          # nose points up the shin toward her knee
    M = whale_M((0, 0, 0), fwd, Vector((0, 0, 1)))          # its back up: the mouth opens up/down round her ankle
    M.translation = p - M.to_3x3() @ GRIP_L
    return M
for f in range(1, END + 1, 2):
    if f < 1150:
        M = whale_M(WPOS(f), WFWD(f), (0, 0, 1))
    elif f < GRIP0:
        u = smoothstep((f - 1150) / (GRIP0 - 1150)); M0 = whale_M(WPOS(1150), WFWD(1150), (0, 0, 1)); M1 = grip_M(GRIP0)
        q = M0.to_quaternion().slerp(M1.to_quaternion(), u); M = q.to_matrix().to_4x4(); M.translation = M0.translation.lerp(M1.translation, u)
    elif f <= GRIP1:
        M = grip_M(f)
    else:
        # release: slides back from her leg and comes up beside her, head out of the water (spy-hop)
        u = smoothstep((f - GRIP1) / 70.0); M1 = grip_M(GRIP1)
        Mt = whale_M((1.05, 0.55, -1.25), (0.1, -0.25, 1.0), (0, -1, 0.2))
        q = M1.to_quaternion().slerp(Mt.to_quaternion(), u); M = q.to_matrix().to_4x4(); M.translation = M1.translation.lerp(Mt.translation, u)
        if f > GRIP1 + 70:
            M.translation = M.translation + Vector((0, 0, 0.06 * math.sin((f - GRIP1 - 70) * 0.05)))
    WM[f] = M
prev = None
for f in sorted(WM):
    loc, q, _ = WM[f].decompose()
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    BR.location = loc; BR.rotation_quaternion = q
    BR.keyframe_insert("location", frame=f); BR.keyframe_insert("rotation_quaternion", frame=f)
set_interp(BR, 'LINEAR')
# undulation: tail beats (rate/amp per beat), head turns, flippers, jaw
def beat(f):
    if f < 980: return 0.9, 7.0
    if f < 1150: return 1.6, 12.0
    if f < GRIP0: return 1.0, 6.0
    if f <= GRIP1: return 1.7, 13.0
    return 0.7, 4.0
HEADTURN = P3([(1, (0, 0, 0)), (683, (0, 0, 0)), (720, (0, 0, -22)), (790, (-4, 0, -26)), (826, (0, 0, -8)), (870, (6, 0, 14)),
               (900, (-6, 0, 12)), (930, (6, 0, 10)), (960, (-4, 0, 6)), (990, (0, 0, -18)), (1040, (0, 0, -6)), (1150, (8, 0, 0)),
               (1170, (0, 0, 0)), (GRIP1, (0, 0, 0)), (1680, (-6, 0, 8)), (END, (-4, 0, 6))])
JAW = P1([(1, 0), (1120, 0), (1150, 24), (1175, 24), (1195, 20), (GRIP1, 20), (1612, 2), (END, 0)])
phase = 0.0
for f in range(1, END + 1, 2):
    rate, amp = beat(f); phase += 2 * math.pi * rate * 2 / 60.0
    for i, (bn, w) in enumerate((("belly", 0.35), ("tail1", 0.6), ("tail2", 0.85), ("fluke", 1.0))):
        a_ = math.radians(amp * w * math.sin(phase - i * 0.7))
        pb = BR.pose.bones[bn]; pb.rotation_euler = (a_, 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    ht = HEADTURN(f)
    for bn, w in (("neck", 0.45), ("head", 0.55)):
        pb = BR.pose.bones[bn]; pb.rotation_euler = (math.radians(ht.x * w), 0, math.radians(ht.z * w)); pb.keyframe_insert("rotation_euler", frame=f)
    for s, sx in (("L", 1), ("R", -1)):
        pb = BR.pose.bones["flipper." + s]; pb.rotation_euler = (math.radians(8 * math.sin(phase * 0.5 + 1)), 0, math.radians(sx * 6 * math.sin(phase * 0.5)))
        pb.keyframe_insert("rotation_euler", frame=f)
    pb = BR.pose.bones["jaw"]; pb.rotation_euler = (math.radians(-JAW(f)), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
for pb in BR.pose.bones:
    pass
log("beluga keyed")

# ================================================================== bubbles + splash droplets: ONE geometry-nodes system on a keyed clock
EV = []      # (t0, p0, v, g, life, r, kind 0=bubble 1=splash)
def mouth_pt(f):
    fs(f); h = Wh(DR, "head"); t = Wt(DR, "head")
    R3 = (DR.matrix_world @ DR.pose.bones["head"].matrix).to_3x3().normalized()
    return h.lerp(t, 0.15) + R3 @ Vector((0, 0.11, 0)) if False else Wh(DR, "jaw").lerp(Wt(DR, "jaw"), 0.9)
rnd = random.Random(7)
def burst(f, n, spread=0.03, rmin=0.006, rmax=0.016, src=None):
    p = src if src is not None else mouth_pt(f)
    for i in range(n):
        t0 = f + rnd.uniform(0, 10)
        EV.append((t0, p + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), 0)),
                   Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), rnd.uniform(0.25, 0.45))), 0.35, 260, rnd.uniform(rmin, rmax), 0))
# entry: a cloud of air dragged down by her body (f12-70)
for f in range(12, 70, 2):
    fs(f); c = Wh(DR, "spine03")
    for i in range(6):
        EV.append((f + rnd.uniform(0, 2), c + Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(-0.4, 0.4))),
                   Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), rnd.uniform(0.2, 0.6))), 0.5, 220, rnd.uniform(0.008, 0.03), 0))
for f, n in ((360, 14), (420, 8), (520, 10), (590, 22), (640, 18), (700, 10), (760, 8), (860, 6), (960, 8), (1060, 5), (1200, 6),
             (1300, 5), (1390, 8), (1430, 3)):
    burst(f, n)
for f in range(150, 1480, 26):
    burst(f, 1, rmin=0.004, rmax=0.008)
# splash at the break (f1508-1530): droplets thrown up round her head and shoulders
for i in range(140):
    t0 = 1508 + rnd.uniform(0, 18); a_ = rnd.uniform(0, 6.283); r_ = rnd.uniform(0.15, 0.45)
    p0 = Vector((0.10 + r_ * math.cos(a_), 0.15 + r_ * math.sin(a_), 0.02))
    v = Vector((math.cos(a_) * rnd.uniform(0.4, 1.4), math.sin(a_) * rnd.uniform(0.4, 1.4), rnd.uniform(1.5, 3.4)))
    EV.append((t0, p0, v, -9.8, 50, rnd.uniform(0.008, 0.022), 1))
for i in range(60):                      # the whale's spy-hop splash (f1640)
    t0 = 1636 + rnd.uniform(0, 14); a_ = rnd.uniform(0, 6.283); r_ = rnd.uniform(0.25, 0.4)
    p0 = Vector((1.05 + r_ * math.cos(a_), 0.55 + r_ * math.sin(a_), 0.02))
    v = Vector((math.cos(a_) * rnd.uniform(0.3, 1.0), math.sin(a_) * rnd.uniform(0.3, 1.0), rnd.uniform(1.0, 2.4)))
    EV.append((t0, p0, v, -9.8, 45, rnd.uniform(0.008, 0.02), 1))
me = bpy.data.meshes.new("FX_Drops"); me.from_pydata([e[1][:] for e in EV], [], [])
for nm, typ in (("t0", 'FLOAT'), ("vel", 'FLOAT_VECTOR'), ("g", 'FLOAT'), ("life", 'FLOAT'), ("rad", 'FLOAT'), ("kind", 'FLOAT')):
    me.attributes.new(nm, typ, 'POINT')
for i, e in enumerate(EV):
    me.attributes["t0"].data[i].value = e[0]; me.attributes["vel"].data[i].vector = e[2]; me.attributes["g"].data[i].value = e[3]
    me.attributes["life"].data[i].value = e[4]; me.attributes["rad"].data[i].value = e[5]; me.attributes["kind"].data[i].value = e[6]
DROPS = bpy.data.objects.new("FX_Drops", me); bpy.data.collections["SET"].objects.link(DROPS)
CLK = bpy.data.objects.new("FX_Clock", None); bpy.data.collections["SET"].objects.link(CLK)
for f in (1, END):
    CLK.location = (f, 0, 0); CLK.keyframe_insert("location", frame=f)
set_interp(CLK, 'LINEAR')
ng = bpy.data.node_groups.new("GN_Drops", 'GeometryNodeTree')
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry'); ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, L = ng.nodes, ng.links
gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = CLK
sep = N.new("ShaderNodeSeparateXYZ"); L.new(oi.outputs["Location"], sep.inputs[0])
def attr(nm, typ='FLOAT'):
    a_ = N.new("GeometryNodeInputNamedAttribute"); a_.data_type = typ; a_.inputs["Name"].default_value = nm; return a_.outputs["Attribute"]
def m(op, a_, b_=None):
    n = N.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a_, b_)):
        if x is None: continue
        if isinstance(x, (int, float)): n.inputs[i].default_value = x
        else: L.new(x, n.inputs[i])
    return n.outputs[0]
dt = m('SUBTRACT', sep.outputs["X"], attr("t0")); dts = m('DIVIDE', dt, 60.0)
alive = m('MULTIPLY', m('GREATER_THAN', dt, 0.0), m('LESS_THAN', dt, attr("life")))
pos = N.new("GeometryNodeInputPosition")
vs = N.new("ShaderNodeVectorMath"); vs.operation = 'SCALE'; L.new(attr("vel", 'FLOAT_VECTOR'), vs.inputs[0]); L.new(dts, vs.inputs["Scale"])
gz = m('MULTIPLY', m('MULTIPLY', attr("g"), 0.5), m('MULTIPLY', dts, dts))
wob = m('MULTIPLY', m('SINE', m('MULTIPLY', dts, 9.0)), m('MULTIPLY', 0.02, m('SUBTRACT', 1.0, attr("kind"))))
cz_ = N.new("ShaderNodeCombineXYZ"); L.new(wob, cz_.inputs[0]); L.new(gz, cz_.inputs[2])
add1 = N.new("ShaderNodeVectorMath"); add1.operation = 'ADD'; L.new(pos.outputs[0], add1.inputs[0]); L.new(vs.outputs[0], add1.inputs[1])
add2 = N.new("ShaderNodeVectorMath"); add2.operation = 'ADD'; L.new(add1.outputs[0], add2.inputs[0]); L.new(cz_.outputs[0], add2.inputs[1])
sepp = N.new("ShaderNodeSeparateXYZ"); L.new(add2.outputs[0], sepp.inputs[0])
# bubbles live under the surface, droplets above it
under = m('LESS_THAN', sepp.outputs["Z"], -0.03); over = m('GREATER_THAN', sepp.outputs["Z"], 0.0)
kind = attr("kind")
okside = m('ADD', m('MULTIPLY', under, m('SUBTRACT', 1.0, kind)), m('MULTIPLY', over, kind))
show = m('MULTIPLY', alive, okside)
setp = N.new("GeometryNodeSetPosition"); L.new(gi.outputs[0], setp.inputs["Geometry"]); L.new(add2.outputs[0], setp.inputs["Position"])
dele = N.new("GeometryNodeDeleteGeometry"); dele.domain = 'POINT'; L.new(setp.outputs[0], dele.inputs["Geometry"]); L.new(m('LESS_THAN', show, 0.5), dele.inputs["Selection"])
ico = N.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 1.0; ico.inputs["Subdivisions"].default_value = 2
inst = N.new("GeometryNodeInstanceOnPoints"); L.new(dele.outputs[0], inst.inputs["Points"]); L.new(ico.outputs["Mesh"], inst.inputs["Instance"])
grow = m('MINIMUM', 1.0, m('DIVIDE', dt, 6.0))
L.new(m('MULTIPLY', attr("rad"), grow), inst.inputs["Scale"])
sm_ = N.new("GeometryNodeSetShadeSmooth"); L.new(inst.outputs[0], sm_.inputs["Geometry"])
smat = N.new("GeometryNodeSetMaterial"); L.new(sm_.outputs[0], smat.inputs["Geometry"])
bm_ = bpy.data.materials.new("M_Bubble"); bm_.use_nodes = True; nt = bm_.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
tr = nt.nodes.new("ShaderNodeBsdfTransparent"); gl = nt.nodes.new("ShaderNodeBsdfGlossy"); gl.inputs["Roughness"].default_value = 0.05
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.55
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.85, 0.97, 1.0, 1); em.inputs["Strength"].default_value = 0.6
ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(gl.outputs[0], ad.inputs[0]); nt.links.new(em.outputs[0], ad.inputs[1])
mx = nt.nodes.new("ShaderNodeMixShader"); nt.links.new(lw.outputs["Facing"], mx.inputs["Fac"]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(ad.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
smat.inputs["Material"].default_value = bm_
L.new(smat.outputs[0], go.inputs[0])
md = DROPS.modifiers.new("Drops", 'NODES'); md.node_group = ng
DROPS.visible_shadow = False
log("fx points", len(EV))

# ---- the whale's playful bubble ring toward the spectators (f880-1000), a keyed torus
bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.035, major_segments=48, minor_segments=12)
RING = bpy.context.active_object; RING.name = "FX_BubbleRing"; RING.data.materials.append(bm_)
for p_ in RING.data.polygons: p_.use_smooth = True
for c in list(RING.users_collection): c.objects.unlink(RING)
bpy.data.collections["SET"].objects.link(RING)
fs(885); hd = Wt(BR, "head")
RING.rotation_euler = (math.radians(90), 0, 0)
for f, dy, dz, s_ in ((885, 0.15, 0.0, 0.3), (905, 0.45, 0.05, 1.0), (940, 0.95, 0.15, 1.6), (980, 1.30, 0.28, 2.0)):
    RING.location = hd + Vector((0, dy, dz)); RING.scale = (s_,) * 3
    RING.keyframe_insert("location", frame=f); RING.keyframe_insert("scale", frame=f)
vis(RING, 1, False); vis(RING, 885, True); vis(RING, 981, False)

# ================================================================== environment motion: waves, caustics, floes
WC = O["WaveCtl"]
for f in (1, END):
    WC.location = (f * 0.0016, f * 0.0009, 0); WC.keyframe_insert("location", frame=f)
set_interp(WC, 'LINEAR')
for mname, node, rate in (("M_TankFloor", "Caustics", 0.006), ("M_Water", "Ripple", 0.005)):
    nd = bpy.data.materials[mname].node_tree.nodes[node]
    for f in (1, END):
        nd.inputs["W"].default_value = f * rate; nd.inputs["W"].keyframe_insert("default_value", frame=f)
    set_interp(bpy.data.materials[mname].node_tree, 'LINEAR')
for i in range(5):
    o = O["TK_Floe%d" % i]; z0 = o.location.z
    for f in range(1, END + 1, 30):
        o.location.z = z0 + 0.04 * math.sin(f * 0.05 + i); o.rotation_euler = (0.03 * math.sin(f * 0.04 + i), 0.03 * math.cos(f * 0.05 + i), i * 0.7)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

# ================================================================== camera: ONE camera, PCHIP paths, level horizon
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.clip_start = 0.03; cam_d.clip_end = 120; cam_d.sensor_width = 36
CAM.rotation_mode = 'QUATERNION'
def face_c(f): fs(f); return Wh(DR, "head").lerp(Wt(DR, "head"), 0.4)
def calf_c(f): fs(f); return Wh(DR, "lowerleg01.R").lerp(Wt(DR, "lowerleg02.R"), 0.4)
def pel_c(f): fs(f); return Wh(DR, "spine03")
def ank_c(f): fs(f); return Wt(DR, "lowerleg02.R")
def whead(f): fs(f); return Wh(BR, "head").lerp(Wt(BR, "head"), 0.35)
def weye(f): fs(f); return Wh(BR, "head").lerp(Wt(BR, "head"), 0.25)
def specs_c(f): fs(f); return (Wh(O["SpecMan"], "head") + Wh(O["SpecWoman"], "head")) / 2
def mix3(a_, b_, u): return a_.lerp(b_, u)
V = Vector
CAMK = [
    # f, position, aim, lens
    (1,    lambda: V((-1.6, -2.6, -2.5)),  lambda: V((0.4, 1.0, -0.4)), 22),
    (40,   lambda: V((-1.3, -2.4, -2.9)),  lambda: pel_c(40) + V((0, 0, 0.2)), 22),
    (100,  lambda: V((-1.0, -2.2, -3.4)),  lambda: pel_c(100), 24),
    (179,  lambda: V((-0.7, -2.2, -3.75)), lambda: pel_c(179), 26),
    (250,  lambda: V((-0.4, -2.3, -4.2)),  lambda: pel_c(250) + V((0, 0, 0.1)), 28),
    (300,  lambda: V((-0.2, -2.0, -4.45)), lambda: pel_c(300) + V((0, 0, 0.05)), 30),
    (340,  lambda: V((-1.00, -0.90, -4.50)), lambda: mix3(face_c(340), calf_c(340), 0.5), 28),
    (420,  lambda: V((-0.25, -1.30, -4.45)), lambda: mix3(face_c(420), calf_c(420), 0.5), 30),
    (480,  lambda: V((0.40, -1.20, -4.35)),  lambda: mix3(face_c(480), calf_c(480), 0.45), 30),
    (540,  lambda: V((-0.25, -1.80, -3.70)), lambda: face_c(540) + V((0, 0, 0.1)), 28),
    (600,  lambda: V((-0.10, -1.00, -2.30)), lambda: face_c(600), 32),
    (660,  lambda: V((0.05, -0.90, -2.20)),  lambda: face_c(660), 34),
    (700,  lambda: V((-0.6, -1.9, -2.6)),    lambda: mix3(face_c(700), whead(700), 0.45), 24),
    (780,  lambda: V((-1.6, -1.2, -2.6)),    lambda: mix3(face_c(780), whead(780), 0.6), 24),
    (860,  lambda: V((-1.4, 2.0, -2.7)),     lambda: mix3(whead(860), specs_c(860), 0.45) + V((0, 0, 0.25)), 26),
    (950,  lambda: V((-0.2, 2.3, -2.8)),     lambda: mix3(whead(950), specs_c(950), 0.5) + V((0, 0, 0.3)), 28),
    (1010, lambda: weye(1010) + V((-0.5, -1.2, 0.1)), lambda: weye(1010), 32),
    (1060, lambda: V((-0.6, -2.4, -2.4)),    lambda: mix3(whead(1060), face_c(1060), 0.35), 24),
    (1110, lambda: face_c(1110) + V((-1.5, -1.9, -0.9)),   lambda: mix3(whead(1110), face_c(1110), 0.5), 22),
    (1180, lambda: ank_c(1180) + V((2.0, -1.1, 0.9)), lambda: mix3(ank_c(1180), face_c(1180), 0.40), 20),
    (1240, lambda: ank_c(1240) + V((2.2, -1.6, 1.1)), lambda: mix3(ank_c(1240), face_c(1240), 0.40), 20),
    (1300, lambda: ank_c(1300) + V((1.4, -2.3, 0.6)), lambda: mix3(ank_c(1300), face_c(1300), 0.45), 20),
    (1387, lambda: face_c(1387) + V((-0.75, -0.75, 0.05)), lambda: face_c(1387), 30),
    (1440, lambda: face_c(1440) + V((0.6, -1.3, -1.0)), lambda: face_c(1440) + V((0, 0, -0.35)), 22),
    (1490, lambda: face_c(1490) + V((-0.9, -1.0, -0.25)), lambda: face_c(1490) + V((0, 0, 0.15)), 26),
    (1520, lambda: V((-0.75, -1.25, -0.40)), lambda: face_c(1525), 26),
    (1540, lambda: V((-0.80, -1.45, 0.30)),  lambda: face_c(1545), 26),
    (1605, lambda: V((-0.55, -1.55, 0.38)),  lambda: mix3(face_c(1605), whead(1605), 0.25), 28),
    (1670, lambda: V((-0.15, -1.75, 0.42)),  lambda: mix3(face_c(1670), whead(1670), 0.35) + V((0, 0, 0.05)), 28),
    (END,  lambda: V((0.65, -1.55, 0.50)),   lambda: mix3(face_c(END), whead(END), 0.35) + V((0, 0, 0.05)), 28),
]
ks = [(f, pf(), af(), l) for f, pf, af, l in CAMK]
fx = [pchip([(k[0], k[1][i]) for k in ks]) for i in range(3)]
ax = [pchip([(k[0], k[2][i]) for k in ks]) for i in range(3)]
fl = pchip([(k[0], k[3]) for k in ks])
def look_q(p, a_, up=Vector((0, 0, 1))):
    zc_ = (p - a_).normalized(); yc = (up - zc_ * up.dot(zc_)); yc = yc.normalized() if yc.length > 1e-6 else Vector((0, 1, 0))
    xc = yc.cross(zc_); return Matrix((xc, yc, zc_)).transposed().to_quaternion()
prev = None
CAMP = {}
for f in range(1, END + 1):
    p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
    q = look_q(p, a_)
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f); cam_d.keyframe_insert("lens", frame=f)
    CAMP[f] = p
set_interp(CAM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# when is the lens above water? -> haze off, the water seen from above
cross = [f for f in range(2, END + 1) if CAMP[f - 1].z < 0.0 <= CAMP[f].z]
log("camera crosses the surface at", cross)
HZ = sc.compositing_node_group.nodes["HazeAmount"].outputs[0]
fc = cross[0] if cross else END
for f, v in ((1, 0.80), (fc - 1, 0.80), (fc, 0.0), (END, 0.0)):
    HZ.default_value = v; HZ.keyframe_insert("default_value", frame=f)
set_interp(sc.compositing_node_group, 'CONSTANT')
# a small catchlight + soft fill riding with the camera (eyes never read as black holes)
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 6.0; cl.size = 0.35; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); bpy.data.collections["SET"].objects.link(clo); clo.parent = CAM; clo.location = (0.25, 0.25, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - face_c(f)).length
    cl.energy = max(2.0, min(30.0, 6.0 * (d_ / 1.0) ** 2)); cl.keyframe_insert("energy", frame=f)

# ================================================================== VO, output
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/BelugaRescue_v009_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for md_ in getattr(o, "modifiers", []):
        if md_.type == 'SUBSURF': md_.show_viewport = False
sc.frame_set(1)
json.dump([{"beat": i + 1, "frame": f, "first_words": w} for i, (f, w) in enumerate((
    (1, "She dove into a freezing Arctic whale tank"), (179, "but as she sank to the bottom"), (300, "the cold sent her legs into crippling cramps"),
    (480, "She couldn't swim back up"), (572, "and as she started to drown"), (683, "a beluga whale noticed her panicking"),
    (826, "These whales are smart and playful with humans"), (980, "and it could tell something was wrong"), (1100, "It swam over"),
    (1166, "took her leg gently in its mouth"), (1278, "and started pushing her up"), (1387, "And just as she ran out of breath"),
    (1496, "the beluga lifted her to the surface"), (1605, "where she could finally breathe")))],
    open(os.path.join(os.path.dirname(HERE), "beats.json"), "w"), indent=1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
