"""PrisonKeyCake v011 stage B: staging, acting, props, the one continuous camera, VO.
blender -b base.blend --python 02_animate.py -- <out.blend> [upto_frame]
Timing is built on the client's VO word times from the start (vo_words.json, frame = 1 + round(t*60)); END 1836.
Every held prop is driven through its grip: IK_hand world = prop world @ inverse(prop-in-hand), so the prop sits IN the fingers."""
import bpy, bmesh, sys, math, random, json, os
from mathutils import Vector, Matrix, Quaternion, Euler
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = "/home/user/Muhammed/blender/PrisonKeyCake_v011/scripts"
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
random.seed(11)
END = 1836
GX = -4.3
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
PRIS, VIS, SMITH = O["Pris"], O["Vis"], O["Smith"]
PB_, VB_, SB_ = O["Pris.body"], O["Vis.body"], O["Smith.body"]
MKEY, KEY1, KEY2 = O["MasterKey"], O["KeyCopy1"], O["KeyCopy2"]
TIN1, TIN2, WAX1, WAX2 = O["Mold1_Tin"], O["Mold2_Tin"], O["Mold1_Wax"], O["Mold2_Wax"]
CAKE_WS, CAKE_C, CAKE_C2, BASKET = O["CakeWS"], O["CakeCell"], O["CakeCell2"], O["Basket"]
DOOR, GATE1, WICKET, CRUC, STREAM = O["CellDoor"], O["Gate1"], O["Wicket"], O["Crucible"], O["PourStream"]
CAND, WICK = O["Candle"], O["CandleWick"]
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
def F(t): return 1 + round(t * 60)

# ================================================================== rigs
CTRL = {}
for r in (PRIS, VIS, SMITH):
    CTRL[r.name] = make_human_ctrl(r)
    add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
PR, VR, SR = CTRL["Pris"], CTRL["Vis"], CTRL["Smith"]
HP, HV, HS = Human(PR), Human(VR), Human(SR)
HUM = {"Pris": HP, "Vis": HV, "Smith": HS}

def key_pole(ctrl, side, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + side; pb = ctrl.PB[n]
    pb.location = ctrl.rest(n).to_3x3().inverted() @ (Vector(target) - ctrl.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def key_spine(ctrl, f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        ctrl.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])

# ---- head aiming: signs solved numerically once per rig
_HS = {}
def head_signs(rig):
    if rig.name in _HS: return _HS[rig.name]
    ctrl = CTRL[rig.name]; pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(rig, "eye.L"); h0 = Wh(rig, "head")
    out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        d = Wh(rig, "eye.L") - e0
        out[ax] = d
        pb.rotation_quaternion = q0; upd()
    # X rotation: + moves the eye down? ; Z rotation: + moves the eye to the rig's left (+x at rest)?
    _HS[rig.name] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS[rig.name]

def key_head(ctrl, f, yaw, pitch, roll=0.0):
    """yaw +: turn toward the rig's own left; pitch +: look down (signs fixed per rig)"""
    rig = ctrl.o if hasattr(ctrl, "o") else None
    sx, sz = head_signs(ctrl.o)
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        ctrl.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])

def look_at(ctrl, f, target, limit=(70, 45), blend=1.0, base=(0.0, 0.0)):
    """key the neck/head so the face turns toward target (world). Evaluated after the root/spine keys of f."""
    rig = ctrl.o
    key_head(ctrl, f, base[0], base[1]); fs(f)
    hd = Wh(rig, "head"); eye = (Wh(rig, "eye.L") + Wh(rig, "eye.R")) / 2
    fwd = (eye - hd); fwd.z = 0
    if fwd.length < 1e-4: return
    fwd.normalize()
    left = Vector((-fwd.y, fwd.x, 0))      # rig's left when facing fwd (rest faces -Y, its left is +X)
    v = Vector(target) - eye
    yaw = math.degrees(math.atan2(v.dot(left), v.dot(fwd)))
    pitch = math.degrees(math.atan2(-v.z, Vector((v.x, v.y)).length))
    # eye forward already points slightly down at rest
    yaw = max(-limit[0], min(limit[0], yaw)) * blend + base[0]
    pitch = max(-limit[1], min(limit[1], pitch - 4.0)) * blend + base[1]
    key_head(ctrl, f, yaw, pitch)

def yaw_dir(yaw):   # facing direction of a rig turned by yaw degrees (rest faces -Y)
    a = math.radians(yaw); return Vector((math.sin(a), -math.cos(a), 0))

# ---- seated / standing roots
def seat_root(H, ctrl, f, pos, yaw, flex=0.0, side=0.0):
    H.key_root(f, Vector(pos), yaw=yaw, flex=flex, side=side)

def plant_feet(ctrl, f, pts, yaw, pole_fwd=0.8):
    for s in "LR":
        a = ctrl.BN["foot." + s].head_local; tgt = Vector(pts[s])
        M = Matrix.Translation(tgt) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Translation(-a) @ ctrl.rest("IK_foot." + s)
        ctrl.key_world("IK_foot." + s, f, M)
        key_pole(ctrl, s, f, tgt + yaw_dir(yaw) * pole_fwd + Vector((0, 0, 0.45)), kind="knee")

def stand(H, ctrl, f, pos, yaw, flex=3.0, side=0.0, feet=True, stance=0.11, dz=None):
    pos = Vector(pos); dz = pos.z if dz is None else dz
    H.key_root(f, Vector((pos.x, pos.y, H.root_head.z - 0.015 + dz)), yaw=yaw, flex=flex, side=side)
    if feet:
        fw = yaw_dir(yaw); lf = Vector((-fw.y, fw.x, 0))
        pts = {}
        for s, sg in (("L", 1), ("R", -1)):
            a = ctrl.BN["foot." + s].head_local
            pts[s] = pos + lf * sg * stance + Vector((0, 0, a.z)) + fw * 0.02
        plant_feet(ctrl, f, pts, yaw)

# ---- hands
def hand_frame_world(rig, s):
    """(wrist, d, n, a) in world for the current pose (rigs sit at the world origin, identity)"""
    H = _Hand(rig, s); return H.frame()

def key_ik_world(ctrl, s, f, Mw):
    ctrl.key_world("IK_hand." + s, f, Mw)

def key_prop_hand(ctrl, s, f, Kw, Rkh, pose=None, pole=None, amount=1.0, search=True, tol_deg=4.0):
    """key the hand so the prop gripped with Rkh (prop relative to wrist) sits at world Kw.
    The wrist limits may clamp the hand: search the elbow pole for the closest reachable orientation, then
    correct the IK position so the prop lands exactly where asked (logged if the angle error stays large)."""
    rig = ctrl.o
    if pose: apply_pose(rig, s, pose, f, amount=amount)
    tgt = Kw @ Rkh.inverted()
    def err():
        fs(f); K = W(rig, "wrist." + s) @ Rkh
        q = K.to_quaternion().rotation_difference(Kw.to_quaternion())
        return (K.translation - Kw.translation).length, math.degrees(abs(q.angle if q.angle <= math.pi else 2 * math.pi - q.angle))
    key_ik_world(ctrl, s, f, tgt)
    best = None
    cands = [None] if pole is None else [Vector(pole) + Vector(o) for o in ((0, 0, 0), (0.3, 0, 0), (-0.3, 0, 0), (0, 0.3, 0), (0, -0.3, 0), (0, 0, 0.3), (0, 0, -0.3))]
    if not search: cands = cands[:1]
    for pl in cands:
        if pl is not None: key_pole(ctrl, s, f, pl)
        e, a = err()
        if best is None or a + e * 300 < best[0]: best = (a + e * 300, pl, e, a)
        if a < 1.0: break
    if best[1] is not None: key_pole(ctrl, s, f, best[1])
    pb = rig.pose.bones["IK_hand." + s]
    for _ in range(3):
        fs(f); K = W(rig, "wrist." + s) @ Rkh; d = Kw.translation - K.translation
        if d.length < 0.0005: break
        M = W(rig, "IK_hand." + s).copy(); M.translation += d; key_ik_world(ctrl, s, f, M)
    e, a = err()
    if e > 0.004 or a > tol_deg: log("GRIP_ERR", rig.name, s, f, "mm", round(e * 1000, 1), "deg", round(a, 1))
    return e, a

def hang_hand(ctrl, s, f, swing=0.0, out=0.0, lift=0.0, pose="relaxed", bend=0.0):
    """a relaxed hanging arm (elbow slightly bent), hand by the thigh; swing + = forward"""
    rig = ctrl.o; fs(f)
    sh = Wh(rig, "upperarm01." + s); pel = Wh(rig, "root")
    fwd = (Wh(rig, "eye.L") + Wh(rig, "eye.R")) / 2 - Wh(rig, "head"); fwd.z = 0; fwd.normalize()
    sg = 1 if s == "L" else -1
    lat = Vector((-fwd.y, fwd.x, 0)) * sg          # outward for this side
    Wp = sh + Vector((0, 0, -0.50 + lift)) + lat * (0.035 + out) + fwd * (0.05 + swing + bend * 0.5)
    d = (Vector((0, 0, -1)) + fwd * (0.25 + swing * 1.5 + bend)).normalized()
    n = -lat
    apply_pose(rig, s, pose, f)
    HUM[rig.name].key_hand(s, f, Wp, d, n, pole=sh + Vector((0, 0, -0.3)) - fwd * 0.5 + lat * 0.25)

def surface_hand(ctrl, s, f, P, fdir, pose="relaxed", pole=None, skin=0.012, normal=(0, 0, -1)):
    rig = ctrl.o
    apply_pose(rig, s, pose, f)
    place_hand(rig, s, f, P, Vector(normal), Vector(fdir), skin=skin)
    if pole is not None: key_pole(ctrl, s, f, pole)

def clear_keys_at(rig, f):
    ad = rig.animation_data
    if not ad or not ad.action: return
    for fc in iter_fcurves(ad.action):
        for kp in [k for k in fc.keyframe_points if abs(k.co.x - f) < 0.5]:
            fc.keyframe_points.remove(kp)

# ================================================================== grip calibration (prop relative to the wrist bone)
CAL = -200
def calib(rig, s, pose):
    ctrl = CTRL[rig.name]; fs(CAL)
    HUM[rig.name].key_root(CAL, Vector((0, 0, HUM[rig.name].root_head.z)), yaw=0)
    sh = Wh(rig, "upperarm01." + s)
    sg = 1 if s == "L" else -1
    HUM[rig.name].key_hand(s, CAL, sh + Vector((0.15 * sg, -0.35, -0.25)), Vector((0, -1, -0.3)), Vector((0, 0, -1)))
    apply_pose(rig, s, pose, CAL); fs(CAL)
    return W(rig, "wrist." + s)

def pinch_rel(rig, s):
    Ww = calib(rig, s, "pinch")
    th = Wt(rig, "finger1-3." + s); ix = Wt(rig, "finger2-3." + s); P = (th + ix) / 2
    a = (th - ix).normalized()
    d = (ix - Wh(rig, "wrist." + s)); d = (d - a * d.dot(a)).normalized()
    X = d; Z = a; Y = Z.cross(X)
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = P - X * 0.011
    return Ww.inverted() @ M

def press_rel(rig, s):
    Ww = calib(rig, s, "point")
    wr, d, n, a = hand_frame_world(rig, s)
    b = Wh(rig, "finger2-1." + s); t = Wt(rig, "finger2-3." + s); X = (t - b).normalized()
    Z = -n; Z = (Z - X * Z.dot(X)).normalized(); Y = Z.cross(X)
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = t + n * 0.0125 - X * 0.012
    return Ww.inverted() @ M

def wrap_rel(rig, s, handle_local=Vector((0, 0, 0.25))):
    Ww = calib(rig, s, "wrap_grip")
    wr, d, n, a = hand_frame_world(rig, s)
    pc = wr.lerp(Wh(rig, "finger3-1." + s), 0.85) + n * 0.022
    X = a.normalized(); Z = (-d - X * (-d).dot(X)).normalized(); Y = Z.cross(X)
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = pc - Matrix((X, Y, Z)).transposed() @ handle_local
    return Ww.inverted() @ M

R_PRESS_P = press_rel(PRIS, "R"); R_PINCH_P = pinch_rel(PRIS, "R"); R_PINCH_PL = pinch_rel(PRIS, "L")
R_PINCH_S = pinch_rel(SMITH, "R"); R_WRAP_S = None
R_WRAP_V = wrap_rel(VIS, "R")
for r in (PRIS, VIS, SMITH): clear_keys_at(r, CAL)
fs(1)

def key_obj_world(obj, f, Mw, interp='BEZIER'):
    key_basis(obj, f, Mw)

def own(obj, f, rig=None, bone=None):
    owner_switch(obj, f, rig, bone, log=log)

# ================================================================== the story, keyed in time order
try:
    exec(open(HERE + "/02b_story.py").read())
except StopIteration:
    log("story stopped at", UPTO)
if os.path.exists(HERE + "/02c_camera.py") and len(args) < 3:
    exec(open(HERE + "/02c_camera.py").read())
for o_ in O:
    for m_ in getattr(o_, "modifiers", []):
        if m_.type == 'SUBSURF': m_.show_viewport = True
open(OUT + ".log.txt", "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("ANIM_OK", OUT)
