"""ToddlerWell v009 stage B: the acting, the ropes, the digger, the head torch, the ONE camera (no cuts), the VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (ToddlerWell_v008 timing, frames 1-1728). Beats (frame = 1 + round(s*60)):
 1 f1 fell / 2 f201 ropes / 3 f397 machinery / 4 f565 11 hours / 5 f781 teenager / 6 f991 rope waist / 7 f1093 head first
 8 f1216 flashlight / 9 f1321 grabbed / 10 f1456 pulled up / 11 f1537 alive.
Scene changes happen inside the move: every time skip happens while its people are out of frame (the camera is down the
shaft, or looking up at the pulley, or whip-panned to the rescuer)."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(17)
END = 1728
Z_BOT = -9.0
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
sc.frame_start, sc.frame_end = 1, END

# ================================================================== rigs
def setup(name):
    rig = O[name]
    ct = make_human_ctrl(rig)
    add_hand_limits(rig)
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
    return rig, ct, Human(ct)
TODR, TCT, TH = setup("Toddler")
TEENR, ECT, EH = setup("Teen")
RESR, RCT, RH = setup("Rescuer")
PEOPLE = ((TODR, TCT, TH), (TEENR, ECT, EH), (RESR, RCT, RH))

def body_M(H, pos, yaw=0.0, flex=0.0, side=0.0, roll=0.0):
    """world matrix of the root (pelvis) frame: pos = where root_head goes; yaw about Z, flex about X, side about Y"""
    Rw = Matrix.Rotation(R_(roll), 3, 'Y') @ Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(flex), 3, 'X') @ Matrix.Rotation(R_(side), 3, 'Y')
    return Matrix.Translation(pos) @ Rw.to_4x4()

def key_body(CT, H, f, Mb):
    CT.key_world("root", f, Mb @ Matrix.Translation(-H.root_head) @ CT.rest("root"))

def to_world(H, Mb, rest_pt):
    return Mb @ (Vector(rest_pt) - H.root_head)

def key_pole(CT, s, f, world, kind):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = CT.PB[n]
    pb.location = CT.rest(n).to_3x3().inverted() @ (Vector(world) - CT.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def key_feet_rel(CT, H, f, Mb, lift=(0.0, 0.0), back=(0.0, 0.0), spread=0.0):
    """feet follow the body frame (standing pose relative to the pelvis): lift/back in body-local metres"""
    for i, s in enumerate("LR"):
        sx = 1 if s == "L" else -1
        off = Vector((sx * spread, back[i], lift[i]))
        M = Mb @ Matrix.Translation(-H.root_head + off) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        kn = CT.BN["lowerleg01." + s].head_local
        key_pole(CT, s, f, to_world(H, Mb, kn + Vector((0, -0.6, 0.0))), "knee")

def key_feet_ground(CT, H, f, xy_yaw, spread=0.10):
    """both feet planted on the ground at (x, y), yaw"""
    x, y, yaw = xy_yaw
    for s in "LR":
        sx = 1 if s == "L" else -1
        a = CT.BN["foot." + s].head_local
        R = Matrix.Rotation(R_(yaw), 4, 'Z')
        tgt = Vector((x, y, 0.0)) + (R @ Vector((sx * spread, 0.0, 0.0)).to_4d()).to_3d() + Vector((0, 0, a.z))
        M = Matrix.Translation(tgt) @ R @ Matrix.Translation(-a) @ CT.rest("IK_foot." + s)
        CT.key_world("IK_foot." + s, f, M)
        key_pole(CT, s, f, tgt + (R @ Vector((sx * 0.05, -0.8, 0.45)).to_4d()).to_3d(), "knee")

def arm_len(CT, s):
    return (CT.BN["lowerarm01." + s].head_local - CT.BN["upperarm01." + s].head_local).length + \
           (CT.BN["wrist." + s].head_local - CT.BN["lowerarm01." + s].head_local).length

def key_hand_local(CT, H, s, f, Mb, wrist_local, d_local, n_local, pole_local, pose="relaxed", amount=1.0):
    """hand target given in the body's rest frame (rest coordinates, i.e. as if the root were at rest)"""
    R3 = Mb.to_3x3()
    W = to_world(H, Mb, wrist_local)
    H.key_hand(s, f, W, R3 @ Vector(d_local), R3 @ Vector(n_local), pole=to_world(H, Mb, pole_local))
    apply_pose(H_RIG[id(H)], s, pose, f, amount)
H_RIG = {id(TH): TODR, id(EH): TEENR, id(RH): RESR}

def hang(CT, H, s, f, Mb, fwd=0.04, out=0.05, bend=0.0, pose="relaxed"):
    """arm hanging relaxed beside the body (body frame), elbow bent ~15-25 deg"""
    sx = 1 if s == "L" else -1
    sh = CT.BN["upperarm01." + s].head_local; L = arm_len(CT, s)
    hip_w = abs(CT.BN["upperleg01." + s].head_local.x) + 0.10 * L / 0.55
    w = Vector((sx * max(hip_w + out * L / 0.55, abs(sh.x) * 0.9), sh.y - fwd * L / 0.55 - bend * 0.08, sh.z - 0.88 * L + bend * 0.1))
    d = Vector((sx * 0.06, -0.15, -1.0)); n = Vector((-sx, 0.0, 0.0))
    key_hand_local(CT, H, s, f, Mb, w, d, n, sh + Vector((sx * 0.25, 0.45, -0.25)), pose)

def arms_up(CT, H, s, f, Mb, reach=0.95, out=0.12, fwd=0.04, pose="open_alarm"):
    """arm raised overhead (body frame): wrist above the shoulder"""
    sx = 1 if s == "L" else -1
    sh = CT.BN["upperarm01." + s].head_local; L = arm_len(CT, s)
    w = sh + Vector((sx * out * L / 0.55, -fwd * L / 0.55, reach * L))
    d = Vector((sx * 0.1, -0.1, 1.0)); n = Vector((0.0, -1.0, 0.0))
    key_hand_local(CT, H, s, f, Mb, w, d, n, sh + Vector((sx * 0.4, 0.2, -0.1)), pose)

def head_signs(rig):
    key = rig.name
    if key in HS: return HS[key]
    pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = Wh(rig, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = Wh(rig, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    HS[key] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return HS[key]
HS = {}
def key_head(rig, CT, f, yaw, pitch, roll=0.0):
    """yaw +: toward own left; pitch +: look down (rest frame of the body)"""
    sx, sz = HS_[rig.name]
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        CT.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])
def key_spine(CT, f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        CT.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
for p in PEOPLE: upd()
HS_ = {r.name: head_signs(r) for r, c, h in PEOPLE}

def yaw_to(src, dst):
    """yaw (deg) that turns the rig's front (-Y at rest) toward dst"""
    d = (Vector(dst) - Vector(src)).to_2d().normalized()
    return math.degrees(math.atan2(d.x, -d.y))

def stand_pos(H, x, y, dz=0.0):
    return Vector((x, y, H.root_head.z - 0.012 + dz))

# ================================================================== the TODDLER
T_START = Vector((1.75, 1.55)); T_RIM = Vector((0.70, 0.36))
yaw_walk = yaw_to(T_START, T_RIM)
TH.walk(lambda f: T_START.lerp(T_RIM, smoothstep((f - 1) / 79.0) * 0.6 + 0.4 * ((f - 1) / 79.0)).to_3d(), lambda f: yaw_walk, 1, 80,
        stride=0.30, duty=0.62, lift=0.05, bob=0.010, crouch=0.012, lean=4.0)
tod_h = TH.root_head.z
def tod_arms_walk(f, ph):
    Mb = body_M(TH, stand_pos(TH, *T_START.lerp(T_RIM, min(1, (f - 1) / 79.0))), yaw_walk)
    for s, sg in (("L", 1), ("R", -1)):
        hang(TCT, TH, s, f, Mb, fwd=0.03 + 0.05 * sg * math.sin(ph), out=0.06, bend=0.3)
for f in range(1, 81, 10):
    tod_arms_walk(f, 2 * math.pi * f / 40.0)
blinks(TODR, [30, 150])
# at the rim: stop, look down into the hole (f80-92), step onto the lip (f92-100), slip in (100-108), fall (108-186)
FALL0, LAND = 108, 186
def tod_fall_z(f):
    if f <= FALL0: return None
    t = (f - FALL0) / 60.0
    return max(Z_BOT + tod_h - 0.012, (tod_h - 0.30) - 5.15 * t * t)
seq = [(80, Vector((0.70, 0.36)), 0.0, yaw_walk, 4), (88, Vector((0.68, 0.34)), 0.0, yaw_walk + 15, 10),
       (96, Vector((0.48, 0.26)), 0.10, yaw_walk + 30, 6), (102, Vector((0.24, 0.16)), -0.05, yaw_walk + 35, -4),
       (108, Vector((0.02, 0.07)), -0.30, yaw_walk + 40, -6)]
for f, xy, dz, yw, fl in seq:
    Mb = body_M(TH, stand_pos(TH, xy.x, xy.y, dz), yw, flex=fl)
    key_body(TCT, TH, f, Mb)
    if f <= 88:
        key_feet_ground(TCT, TH, f, (xy.x, xy.y, yw), spread=0.06)
    else:
        key_feet_rel(TCT, TH, f, Mb, lift=(0.06 if f == 96 else 0.0, 0.0))
    for s in "LR":
        if f <= 88: hang(TCT, TH, s, f, Mb, fwd=0.05, out=0.10, bend=0.4)
        else: arms_up(TCT, TH, s, f, Mb, reach=0.80 if f < 102 else 0.95, out=0.20)
    key_head(TODR, TCT, f, 0, 25 if f in (88, 96) else (-15 if f >= 102 else 5))
    key_spine(TCT, f, flex=12 if f in (88, 96) else 2)
# free fall straight down the shaft centre, arms up, legs a touch bent
for f in range(110, LAND + 1, 4):
    z = tod_fall_z(f); Mb = body_M(TH, Vector((0.0, 0.06, z)), yaw_walk + 40 + (f - 108) * 0.35, flex=-4)
    key_body(TCT, TH, f, Mb); key_feet_rel(TCT, TH, f, Mb, lift=(0.04, 0.07), back=(0.02, 0.04))
    for s in "LR": arms_up(TCT, TH, s, f, Mb, reach=0.95, out=0.18)
    key_head(TODR, TCT, f, 0, -20); key_spine(TCT, f, flex=-4)
# land, crouch, stand up crying with arms up (yaw turns him to face the camera, 3/4)
TOD_BOT = Vector((0.0, 0.06))
YB = -12.0
def tod_bottom(f, dz=0.0, yaw=YB, flex=3.0):
    return body_M(TH, Vector((TOD_BOT.x, TOD_BOT.y, Z_BOT + tod_h - 0.012 + dz)), yaw, flex=flex)
for f, dz, fl in ((LAND, 0.0, 4), (LAND + 6, -0.13, 18), (LAND + 18, -0.10, 14), (LAND + 34, 0.0, 3)):
    Mb = tod_bottom(f, dz, YB + (yaw_walk + 40 + (LAND - 108) * 0.35 - YB) * (1 if f == LAND else 0), fl)
    key_body(TCT, TH, f, Mb); key_feet_ground(TCT, TH, f, (TOD_BOT.x, TOD_BOT.y, YB), spread=0.07)
    for s in "LR":
        if f < LAND + 30: hang(TCT, TH, s, f, Mb, fwd=0.10, out=0.14, bend=0.6)
        else: arms_up(TCT, TH, s, f, Mb, reach=0.85, out=0.22)
    key_head(TODR, TCT, f, 0, 10 if f < LAND + 20 else -30)
    key_spine(TCT, f, flex=fl)

# bottom acting f220-1290: crying, reaching up (alternating arms), looking up; breath; later tired
def tod_idle(f0, f1, mood="cry"):
    for f in range(f0, f1 + 1, 12):
        ph = 2 * math.pi * (f - f0) / 96.0
        Mb = tod_bottom(f, -0.01 + 0.006 * math.sin(2 * math.pi * f / 70), YB + 6 * math.sin(ph * 0.5), 3.0)
        key_body(TCT, TH, f, Mb); key_feet_ground(TCT, TH, f, (TOD_BOT.x, TOD_BOT.y, YB), spread=0.07)
        if mood == "cry":
            arms_up(TCT, TH, "L", f, Mb, reach=0.80 + 0.12 * math.sin(ph), out=0.24)
            arms_up(TCT, TH, "R", f, Mb, reach=0.80 - 0.12 * math.sin(ph), out=0.24)
            key_head(TODR, TCT, f, 6 * math.sin(ph * 0.7), -32 + 4 * math.sin(ph))
        else:
            for s in "LR": hang(TCT, TH, s, f, Mb, fwd=0.06 + 0.02 * math.sin(ph), out=0.10, bend=0.5)
            key_head(TODR, TCT, f, 8 * math.sin(ph * 0.6), -12 + 8 * math.sin(ph * 0.8))
        key_spine(TCT, f, flex=2 + 1.5 * math.sin(2 * math.pi * f / 70))
tod_idle(LAND + 40, 470, "cry")
tod_idle(482, 1250, "tired")
tod_idle(1262, 1320, "cry")
for f, sm, br, jaw, sq in ((1, 0.35, 0.3, 0.0, 0.0), (80, 0.3, 0.3, 0.0, 0.0), (96, 0.0, 0.8, 0.3, 0.0), (120, -0.3, 0.9, 0.5, 0.0),
                           (190, -0.6, -0.8, 0.45, 0.5), (300, -0.7, -0.9, 0.55, 0.6), (470, -0.6, -0.8, 0.4, 0.5),
                           (520, -0.4, -0.5, 0.15, 0.3), (1250, -0.4, -0.5, 0.15, 0.3), (1290, -0.2, 0.6, 0.35, 0.0),
                           (1380, 0.2, 0.7, 0.2, 0.0), (1456, 0.3, 0.6, 0.15, 0.0)):
    key_face(TODR, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(TODR, [400, 640, 900, 1150])

# ================================================================== the RESCUER (hidden until f200 while the camera is down the shaft)
RES_XY = Vector((-1.05, 1.35))
def res_M(f, flex=6.0, yaw=None, dz=0.0):
    y = yaw_to(RES_XY, (0.0, 0.1)) if yaw is None else yaw
    return body_M(RH, stand_pos(RH, RES_XY.x, RES_XY.y, dz), y, flex=flex)
Y_WELL = yaw_to(RES_XY, (0.0, 0.1)); Y_CAM = yaw_to(RES_XY, (0.2, -3.0)); Y_TEEN = yaw_to(RES_XY, (-1.75, 0.55))
RES_PLAN = [(1, Y_WELL, 14, 0, 28), (380, Y_WELL, 14, 0, 28), (430, Y_WELL + 25, 6, 15, 10), (560, Y_WELL + 25, 6, 15, 8),
            (600, Y_WELL + 10, 16, 5, 22), (760, Y_WELL + 10, 18, 5, 25), (800, Y_TEEN + 10, 6, -10, 0), (980, Y_TEEN + 5, 6, -10, 6),
            (1080, Y_WELL, 10, 0, 20), (1540, Y_WELL, 12, 0, 22), (1575, Y_CAM, 2, 0, -5), (1728, Y_CAM, 2, 0, -5)]
yy = pchip([(f, y) for f, y, fl, hy, hp in RES_PLAN]); ff = pchip([(f, fl) for f, y, fl, hy, hp in RES_PLAN])
hy_ = pchip([(f, hy) for f, y, fl, hy, hp in RES_PLAN]); hp_ = pchip([(f, hp) for f, y, fl, hy, hp in RES_PLAN])
CHEER0, CHEER1 = 1566, 1728
for f in list(range(1, END + 1, 10)) + [END]:
    br = 1.2 * math.sin(2 * math.pi * f / 150)
    Mb = res_M(f, flex=ff(f) * 0.4, yaw=yy(f))
    key_body(RCT, RH, f, Mb); key_feet_ground(RCT, RH, f, (RES_XY.x, RES_XY.y, yy(f)), spread=0.13)
    key_spine(RCT, f, flex=ff(f) * 0.6 + br)
    nod = 8 * math.sin(2 * math.pi * (f - 940) / 24) if 940 <= f <= 988 else 0.0
    key_head(RESR, RCT, f, hy_(f), hp_(f) + nod)
    for s in "LR":
        if f >= CHEER0:
            ph = 2 * math.pi * (f - CHEER0) / 40.0
            arms_up(RCT, RH, s, f, Mb, reach=0.88 + 0.06 * math.sin(ph + (0 if s == "L" else 1.5)), out=0.30, pose="power_fist")
        else:
            hang(RCT, RH, s, f, Mb, fwd=0.05 + 0.015 * math.sin(2 * math.pi * f / 150 + (0 if s == "L" else 1)), out=0.07, bend=0.35)
for f, sm, br, jaw in ((1, 0.0, -0.4, 0.0), (560, 0.0, -0.5, 0.0), (640, -0.2, -0.6, 0.0), (800, 0.0, 0.5, 0.0), (900, 0.1, 0.3, 0.2),
                       (930, 0.2, 0.3, 0.0), (1080, 0.0, -0.3, 0.0), (1540, 0.1, 0.2, 0.0), (1575, 0.9, 0.5, 0.45), (1728, 0.95, 0.5, 0.4)):
    key_face(RESR, f, smile=sm, brow=br, jaw=jaw)
blinks(RESR, [250, 520, 820, 1010, 1300, 1620, 1690])
saccades(RCT, 200, END, every=45, amp=(1.5, 2.5), seed=3)
# hard hat on his head (parented to the head bone, fitted above the hair)
HAT = O["RES_HardHat"]
fs(1); upd()
def head_top(rig, body, hair_key):
    """top of the head (rest): highest vertex of the body/hair around the head bone"""
    pts = [rig.matrix_world @ v.co for c in rig.children if c.type == 'MESH' and (c == body or hair_key in c.name.lower()) for v in c.data.vertices]
    hb = rig.data.bones["head"].head_local
    pts = [p for p in pts if p.z > hb.z and abs(p.x - hb.x) < 0.15]
    return max(p.z for p in pts), hb
def parent_to_bone(obj, rig, bone, M_world_rest):
    obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = bone
    pb = rig.pose.bones[bone]
    Mbone = rig.matrix_world @ rig.data.bones[bone].matrix_local @ Matrix.Translation((0, rig.data.bones[bone].length, 0))
    obj.matrix_parent_inverse = Mbone.inverted()
    obj.matrix_world = M_world_rest
# rest pose for fitting: mute constraints and clear pose keys temporarily is complex; fit using rest-position bones instead
for r in (RESR, TEENR, TODR): r.data.pose_position = 'REST'
upd()
ztop, hb = head_top(RESR, O["Rescuer.body"], "short02")
hat_bb = [Vector(c) for c in HAT.bound_box]; hat_h = max(v.z for v in hat_bb) - min(v.z for v in hat_bb)
log("res head top", round(ztop, 3), "hat h", round(hat_h, 3))
parent_to_bone(HAT, RESR, "head", Matrix.Translation((hb.x, hb.y + 0.005, ztop - hat_h * 0.62)) @ Matrix.Rotation(math.radians(180), 4, 'Z'))

# ================================================================== the TEEN
# ---- head torch: strap round the forehead, lamp at the front, beam + spot from the lamp
def ring_fit(objs, zc, band, xc, yc, maxr=0.25):
    pts = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    pts = [p for p in pts if abs(p.z - zc) < band and abs(p.x - xc) < maxr and abs(p.y - yc) < maxr]
    return (max(abs(p.x - xc) for p in pts), max(p.y for p in pts) - yc, yc - min(p.y for p in pts))
TB = O["Teen.body"]; TCL = O["Teen.clothes"]
THAIR = [c for c in TEENR.children if c.type == 'MESH' and "short04" in c.name.lower()]
eyeL = TEENR.data.bones["eye.L"].head_local; eyeR = TEENR.data.bones["eye.R"].head_local
z_fh = (eyeL.z + eyeR.z) / 2 + 0.062
hbT = TEENR.data.bones["head"].head_local
rx, ry_back, ry_front = ring_fit([TB] + THAIR, z_fh, 0.008, hbT.x, hbT.y)
log("teen forehead ring", round(rx, 3), round(ry_back, 3), round(ry_front, 3))
STRAP, LAMP, BEAM, SPOT = O["TEEN_TorchStrap"], O["TEEN_TorchLamp"], O["TEEN_TorchBeam"], O["TEEN_TorchSpot"]
yc = hbT.y + (ry_back - ry_front) / 2
STRAP.scale = ((rx + 0.007) / 0.095, ((ry_back + ry_front) / 2 + 0.007) / 0.095, 1.0)
parent_to_bone(STRAP, TEENR, "head", Matrix.Translation((hbT.x, yc, z_fh)) @ Matrix.Diagonal((*STRAP.scale, 1.0)))
parent_to_bone(LAMP, TEENR, "head", Matrix.Translation((hbT.x, hbT.y - ry_front - 0.022, z_fh + 0.004)) @ Matrix.Rotation(math.radians(-8), 4, 'X'))
for o in (STRAP, LAMP, BEAM, SPOT, O['TEEN_TorchLens']): vis(o, 1, False); vis(o, 1105, True)
for o in (BEAM, SPOT): vis(o, 1586, False)
# ---- waist rope ring + knot (shown from f972, while the camera is on the rescuer's face)
z_w = TEENR.data.bones["spine04"].head_local.z if "spine04" in TEENR.data.bones else TEENR.data.bones["spine05"].head_local.z
pel = TEENR.data.bones["spine05"].head_local
z_w = pel.z + 0.06
wx, wyb, wyf = ring_fit([TCL], z_w, 0.012, pel.x, pel.y, 0.26)
log("teen waist ring", round(wx, 3), round(wyb, 3), round(wyf, 3))
WAIST, KNOT = O["ROPE_WaistRing"], O["ROPE_Knot"]
wyc = pel.y + (wyb - wyf) / 2
sxw, syw = (wx + 0.018) / 0.20, ((wyb + wyf) / 2 + 0.018) / 0.20
parent_to_bone(WAIST, TEENR, "spine05", Matrix.Translation((pel.x, wyc, z_w)) @ Matrix.Diagonal((sxw, syw, 1.0, 1.0)))
KNOT_REST = Vector((pel.x, wyc - (wyb + wyf) / 2 - 0.035, z_w))
parent_to_bone(KNOT, TEENR, "spine05", Matrix.Translation(KNOT_REST) @ Matrix.Diagonal((1.0, 0.8, 0.8, 1.0)))
for o in (WAIST, KNOT): vis(o, 1, False); vis(o, 972, True)
for r in (RESR, TEENR, TODR): r.data.pose_position = 'POSE'
upd()

TEEN_IN = Vector((-4.6, 2.3)); TEEN_AT = Vector((-1.75, 0.55))
YT = yaw_to(TEEN_AT, (0.6, -2.0))
# hidden until he walks into frame; walks in f770-880
for o in [TEENR] + list(TEENR.children):
    pass
def teen_path(f):
    u = smoothstep((f - 770) / 110.0) * 0.85 + 0.15 * min(1, max(0, (f - 770) / 110.0))
    return TEEN_IN.lerp(TEEN_AT, u).to_3d()
y_in = yaw_to(TEEN_IN, TEEN_AT)
EH.walk(teen_path, lambda f: y_in + (YT - y_in) * smoothstep((f - 850) / 30.0), 770, 880, stride=0.72, lift=0.08, bob=0.02)
for f in range(770, 881, 10):
    p = teen_path(f); Mb = body_M(EH, stand_pos(EH, p.x, p.y), y_in)
    ph = 2 * math.pi * (f - 770) / 62.0
    for s, sg in (("L", 1), ("R", -1)):
        hang(ECT, EH, s, f, Mb, fwd=0.04 + 0.08 * sg * math.sin(ph), out=0.05, bend=0.35)
    key_head(TEENR, ECT, f, -20 if f > 820 else 0, 4)
# park him off-set before f770 (static far left, out of every frame)
for f in (1, 760):
    Mb = body_M(EH, stand_pos(EH, TEEN_IN.x, TEEN_IN.y), y_in)
    key_body(ECT, EH, f, Mb); key_feet_ground(ECT, EH, f, (TEEN_IN.x, TEEN_IN.y, y_in))
    for s in "LR": hang(ECT, EH, s, f, Mb)
# standing with the rescuer: offers (right hand up, palm out f880-940), talks; then knots the rope f991-1090
def teen_stand(f, flex=3.0, twist=0.0, yaw=YT, dz=0.0):
    return body_M(EH, stand_pos(EH, TEEN_AT.x, TEEN_AT.y, dz), yaw, flex=flex)
for f in list(range(880, 1101, 10)):
    br = 1.0 * math.sin(2 * math.pi * f / 130)
    yaw = YT + (yaw_to(TEEN_AT, RES_XY) - YT) * 0.55 * (smoothstep((f - 880) / 30) - smoothstep((f - 960) / 30))
    Mb = teen_stand(f, flex=2 + br * 0.3, yaw=yaw)
    key_body(ECT, EH, f, Mb); key_feet_ground(ECT, EH, f, (TEEN_AT.x, TEEN_AT.y, yaw), spread=0.12)
    key_spine(ECT, f, flex=2 + br)
    if f < 980:
        hang(ECT, EH, "L", f, Mb, fwd=0.05, out=0.06, bend=0.3)
        if 890 <= f <= 940:
            sh = ECT.BN["upperarm01.R"].head_local; L = arm_len(ECT, "R")
            key_hand_local(ECT, EH, "R", f, Mb, sh + Vector((-0.12, -0.28, 0.12 + 0.02 * math.sin(f / 5))), (0, 0, 1), (0, -1, 0),
                           sh + Vector((-0.4, 0.2, -0.3)), "flat_palm")
        else:
            hang(ECT, EH, "R", f, Mb, fwd=0.05, out=0.06, bend=0.3)
        key_head(TEENR, ECT, f, 25 if 880 < f < 975 else 0, 2)
# knot: both hands at the knot (2 cm either side of it, palms facing each other, gripping the ring) and a tug
KN = KNOT_REST
for f in range(990, 1101, 6):
    Mb = teen_stand(f, flex=6, yaw=YT)
    key_body(ECT, EH, f, Mb); key_feet_ground(ECT, EH, f, (TEEN_AT.x, TEEN_AT.y, YT), spread=0.12)
    key_spine(ECT, f, flex=8)
    tug = 0.02 * max(0.0, math.sin(2 * math.pi * (f - 1010) / 30)) if f > 1010 else 0.0
    u = smoothstep((f - 990) / 18.0)
    for s in "LR":
        sx = 1 if s == "L" else -1
        sh = ECT.BN["upperarm01." + s].head_local
        w_knot = KN + Vector((sx * (0.075 + tug), -0.055, 0.035))
        w_hang = sh + Vector((sx * 0.05, -0.08, -0.48))
        w = w_hang.lerp(w_knot, u)
        key_hand_local(ECT, EH, s, f, Mb, w, Vector((-sx * 0.55, -0.15, -0.8)), Vector((-sx, -0.2, 0.0)), sh + Vector((sx * 0.35, 0.3, -0.3)),
                       "wrap_grip", amount=u)
    key_head(TEENR, ECT, f, 0, 30 - 26 * smoothstep((f - 1060) / 30.0))
for f, sm, br, jaw in ((1, 0.0, 0.0, 0.0), (870, 0.0, 0.3, 0.0), (895, 0.1, 0.6, 0.35), (910, 0.1, 0.5, 0.1), (925, 0.1, 0.5, 0.35),
                       (945, 0.2, 0.5, 0.05), (990, 0.1, -0.4, 0.0), (1090, 0.2, -0.5, 0.0), (1216, 0.0, -0.6, 0.1),
                       (1330, 0.1, 0.4, 0.25), (1400, 0.4, 0.4, 0.05), (1540, 0.5, 0.4, 0.05), (1600, 0.9, 0.5, 0.35), (1728, 0.95, 0.5, 0.3)):
    key_face(TEENR, f, smile=sm, brow=br, jaw=jaw)
blinks(TEENR, [905, 1000, 1250, 1420, 1650])
saccades(ECT, 880, 1100, every=40, amp=(1.5, 2.5), seed=6)

# ---- head first down the shaft (inverted: body yaw 0 = facing the camera, rotated 180 about the view axis Y)
# the switch happens at f1112 while the camera looks up at the pulley (he is out of frame)
INV0 = 1112
TEEN_Y = 0.09
def hips_z(f):
    """pelvis height while lowered: legs out of the rim at f1125, head reaches the toddler at f1350, rise f1440-1560"""
    return pchip([(INV0, 0.55), (1150, 0.05), (1216, -3.2), (1300, -6.6), (1350, -7.30), (1440, -7.30), (1500, -3.6), (1560, 0.4)])(f)
def inv_M(f, yaw=0.0):
    # root frame rotated 180 deg about Y: his head points down, his front still faces -Y (the camera)
    return Matrix.Translation(Vector((0.0, TEEN_Y, hips_z(f)))) @ (Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(180), 3, 'Y')).to_4x4()
GRAB = 1352
TOD_RISE0 = 1440
for f in list(range(INV0, 1561, 4)):
    sweep = 22 * math.sin(2 * math.pi * (f - 1216) / 70) if 1216 <= f <= 1320 else 0.0
    Mb = inv_M(f)
    key_body(ECT, EH, f, Mb)
    key_feet_rel(ECT, EH, f, Mb, lift=(0.02, 0.02), back=(0.05, 0.05), spread=-0.02)
    key_spine(ECT, f, flex=-4)
    key_head(TEENR, ECT, f, sweep, -18 if f < 1320 else -30)
    # arms: reaching down past the head (overhead in his body frame) toward the toddler
    for s in "LR":
        sx = 1 if s == "L" else -1
        sh = ECT.BN["upperarm01." + s].head_local; L = arm_len(ECT, s)
        if f < 1300:
            w = sh + Vector((sx * 0.14, -0.10, 0.80 * L)); pose = "relaxed"
            key_hand_local(ECT, EH, s, f, Mb, w, (sx * 0.15, -0.3, 1.0), (0, -1, 0), sh + Vector((sx * 0.45, 0.1, -0.1)), pose)
for f in list(range(INV0, 1561, 4)):
    pass
# ---- the grab: his hands close round the toddler's forearms (computed from the toddler's evaluated wrists)
def tod_arm_up_M(f, dz):
    return tod_bottom(f, dz, YB, 3.0)
# the toddler's final reach: both arms straight up, wrists apart, from f1300; he rises with the teen from TOD_RISE0
def tod_lift(f):
    return max(0.0, hips_z(f) - hips_z(TOD_RISE0)) if f >= TOD_RISE0 else 0.0
for f in list(range(1322, 1561, 4)):
    Mb = tod_bottom(f, -0.01 + tod_lift(f) + (0.02 if f >= TOD_RISE0 else 0.0), YB * 0.5, 2.0)
    key_body(TCT, TH, f, Mb)
    if f < TOD_RISE0:
        key_feet_ground(TCT, TH, f, (TOD_BOT.x, TOD_BOT.y, YB * 0.5), spread=0.07)
    else:
        key_feet_rel(TCT, TH, f, Mb, lift=(0.03, 0.05), back=(0.02, 0.05))
    for s in "LR":
        arms_up(TCT, TH, s, f, Mb, reach=0.97, out=0.10, fwd=0.02, pose="wrap_grip" if f >= GRAB else "open_alarm")
    key_head(TODR, TCT, f, 0, -38)
    key_spine(TCT, f, flex=1)
upd()
# teen hands: from f1300 reach to the toddler's forearms, grip from GRAB, hold through the rise
def tod_forearm(f, s):
    fs(f); a = Wh(TODR, "lowerarm01." + s); b = Wh(TODR, "wrist." + s)
    return a, b
for f in list(range(1300, 1561, 4)):
    fs(f); Mb = inv_M(f)
    Minv = Mb.inverted()
    for s_t, s_k in (("L", "R"), ("R", "L")):      # the teen's left hand takes the toddler's right forearm (they face each other)
        a, b = tod_forearm(f, s_k)
        axis = (b - a).normalized()
        grip_pt = b - axis * 0.07                     # 7 cm below the wrist
        # palm on the forearm's back (+Y) side? the teen is above: approach from his side (body -> forearm), fingers point down
        sxw = 1 if s_t == "L" else -1
        toward = Vector((0, 0, 0))
        n_w = Vector((0.0, 1.0, 0.0))                   # palm faces +Y (toward the shaft wall): the hand is in FRONT of the forearm
        wrist_w = grip_pt + Vector((0.0, -0.040, 0.060))  # wrist 6 cm above the grip point, palm 4 cm in front of the axis
        u = smoothstep((f - 1300) / (GRAB - 1300))
        sh = ECT.BN["upperarm01." + s_t].head_local
        w_reach_rest = sh + Vector((sxw * 0.14, -0.10, 0.80 * arm_len(ECT, s_t)))
        w_reach = to_world(EH, Mb, w_reach_rest)
        W = w_reach.lerp(wrist_w, u)
        # express in body-rest coords for key_hand_local
        Wl = (Minv @ W) + EH.root_head
        dW = Vector((0, 0, -1)); nW = n_w
        dl = Minv.to_3x3() @ dW; nl = Minv.to_3x3() @ nW
        key_hand_local(ECT, EH, s_t, f, Mb, Wl, dl, nl, sh + Vector((sxw * 0.45, 0.1, -0.1)), "wrap_grip" if f >= GRAB else "relaxed",
                       amount=1.0 if f >= GRAB else min(1.0, u))
# final tableau (after the whip to the rescuer): teen and toddler standing on the field right of the well, cheering
SW = 1586
TEEN_FIN = Vector((-1.95, 0.80)); TOD_FIN = Vector((-1.50, 0.58))
YF_T = yaw_to(TEEN_FIN, (0.4, -3.0)); YF_K = yaw_to(TOD_FIN, (0.2, -3.0))
for f in list(range(SW, END + 1, 6)) + [END]:
    ph = 2 * math.pi * (f - SW) / 44.0
    Mb = body_M(EH, stand_pos(EH, TEEN_FIN.x, TEEN_FIN.y), YF_T, flex=2)
    key_body(ECT, EH, f, Mb); key_feet_ground(ECT, EH, f, (TEEN_FIN.x, TEEN_FIN.y, YF_T), spread=0.12)
    key_spine(ECT, f, flex=2 + 1.2 * math.sin(2 * math.pi * f / 110))
    arms_up(ECT, EH, "R", f, Mb, reach=0.85 + 0.05 * math.sin(ph), out=0.35, pose="open_alarm")
    hang(ECT, EH, "L", f, Mb, fwd=0.06, out=0.08, bend=0.3)
    key_head(TEENR, ECT, f, -14, -2)
    Mk = body_M(TH, stand_pos(TH, TOD_FIN.x, TOD_FIN.y, 0.008 * math.sin(ph * 2)), YF_K, flex=2)
    key_body(TCT, TH, f, Mk); key_feet_ground(TCT, TH, f, (TOD_FIN.x, TOD_FIN.y, YF_K), spread=0.07)
    for s, sg in (("L", 1), ("R", -1)):
        arms_up(TCT, TH, s, f, Mk, reach=0.78 + 0.10 * math.sin(ph + sg), out=0.35, pose="open_alarm")
    key_head(TODR, TCT, f, 10, -8); key_spine(TCT, f, flex=1)
for f, sm, br, jaw in ((1470, 0.1, 0.6, 0.2), (SW, 0.85, 0.5, 0.35), (END, 0.9, 0.5, 0.3)):
    key_face(TODR, f, smile=sm, brow=br, jaw=jaw)

# constant interpolation at the hidden switches (no in-between flights)
def const_at(rig, ranges):
    ad = rig.animation_data
    for fc in iter_fcurves(ad.action):
        for kp in fc.keyframe_points:
            for a_, b_ in ranges:
                if a_ <= kp.co.x <= b_: kp.interpolation = 'CONSTANT'
# teen: last upright key 1100 -> first inverted key INV0 must jump; last inverted 1560 -> final SW jump; walk-in from parked
const_at(TEENR, [(1095, 1111), (1550, 1585), (755, 769)])
const_at(TODR, [(1550, 1585)])
for rig in (TODR, TEENR, RESR): quat_continuity(rig)

# ================================================================== props: ropes (16 points each, keyed per frame), loop
TOP = O["SET_Pulley"].location + Vector((0.0, 0.0, -0.10))
R1 = [O["ROPE_Loop_P%02d" % i] for i in range(16)]
R2 = [O["ROPE_Teen_P%02d" % i] for i in range(16)]
LOOP = O["ROPE_LoopRing"]; ROPE1, ROPE2 = O["ROPE_Loop"], O["ROPE_Teen"]
def key_rope(pts, f, A, B, sag=0.0):
    for i, e in enumerate(pts):
        u = i / (len(pts) - 1)
        p = A.lerp(B, u) + Vector((0, 0, -sag * 4 * u * (1 - u)))
        e.location = p; e.keyframe_insert("location", frame=f)
# rope 1: loop lowered f215-300 to just above the toddler's raised hands, swings and misses, pulled up f330-392
TOD_HANDS_Z = Z_BOT + 0.86
def loop_tip(f):
    z = pchip([(200, TOP.z - 0.05), (215, TOP.z - 0.3), (300, TOD_HANDS_Z + 0.48), (330, TOD_HANDS_Z + 0.44), (392, TOP.z - 0.25)])(f)
    sw = 0.13 * math.sin(2 * math.pi * (f - 280) / 64) * smoothstep((f - 270) / 20) * (1 - smoothstep((f - 340) / 20))
    return Vector((sw, 0.06, z))
for f in range(200, 396, 2):
    tip = loop_tip(f); key_rope(R1, f, TOP, tip)
    LOOP.location = tip + Vector((0, 0, -0.16)); LOOP.rotation_euler = (math.radians(90), math.radians(15 * math.sin(f / 9.0)), 0)
    LOOP.keyframe_insert("location", frame=f); LOOP.keyframe_insert("rotation_euler", frame=f)
for o in (ROPE1, LOOP): vis(o, 1, False); vis(o, 200, True); vis(o, 396, False)
# rope 2: pulley -> the teen's knot (evaluated), f972 onward; hidden at the whip (SW)
KNOT = O["ROPE_Knot"]
for f in range(972, SW + 1, 2):
    fs(f); kn = KNOT.matrix_world.translation.copy()
    sag = 0.12 if f < 1100 else 0.0
    key_rope(R2, f, TOP, kn + Vector((0, 0, 0.0)), sag=sag)
vis(ROPE2, 1, False); vis(ROPE2, 972, True); vis(ROPE2, SW, False)
for o in (O["ROPE_WaistRing"], KNOT):
    pass
for e in R1 + R2: set_interp(e, 'LINEAR')

# the tripod, the coil, the rescuer and the digger appear while the camera is down the shaft (f200)
for o in (O["SET_Tripod"], O["SET_Pulley"], O["SET_RopeCoil"]):
    vis(o, 1, False); vis(o, 200, True)
for o in [RESR] + list(RESR.children) + [O["RES_HardHat"]]:
    vis(o, 1, False); vis(o, 200, True)
EXC = [o for o in O if o.name.startswith(("EXC_", "arm_", "Arm_", "Body_GEO", "Tread_", "claw", "shovel", "Excavator", "RootNode",
                                           "Object_", "8a260", "back", "bottom", "left"))]
for o in EXC:
    vis(o, 1, False); vis(o, 200, True)
PROPS_ON_TEEN = {"ROPE_WaistRing", "ROPE_Knot", "TEEN_TorchStrap", "TEEN_TorchLamp", "TEEN_TorchLens", "TEEN_TorchBeam", "TEEN_TorchSpot"}
for o in [TEENR] + list(TEENR.children):
    if (o.type == 'MESH' or o.type == 'ARMATURE') and o.name not in PROPS_ON_TEEN:
        vis(o, 1, False); vis(o, 765, True)

# ================================================================== the digger: boom / stick / bucket keyed in local X
ARM1, ARM2, CLAW, SHOV = O["arm_01_GEO1"], O["Arm_2_GEO"], O["claw_GEO"], O["shovel_GEO"]
for o in (ARM1, ARM2, CLAW, SHOV): o.rotation_mode = 'XYZ'
def tip_z():
    upd(); return CLAW.matrix_world.translation.z
z0 = tip_z(); ARM1.rotation_euler.x = math.radians(10); z1 = tip_z(); ARM1.rotation_euler.x = 0
SB = 1 if z1 < z0 else -1          # + SB*deg lowers the boom
log("digger boom sign", SB, round(z0, 2), round(z1, 2))
DIG = [(200, 0, 0, 0), (397, 0, 0, 0)]
f = 400
while f < 800:
    per = 84 if f < 565 else 40        # time-lapse after f565: faster cycles
    DIG += [(f, 0, 0, 0), (f + per * 0.3, 16, 22, -30), (f + per * 0.5, 18, 30, 40), (f + per * 0.8, -6, 8, 45), (f + per, 0, 0, 0)]
    f += per
for fr, b, st, cl in DIG:
    fr = int(fr)
    ARM1.rotation_euler.x = math.radians(SB * b); ARM2.rotation_euler.x = math.radians(SB * st * 0.6)
    CLAW.rotation_euler.x = math.radians(SB * cl * 0.5); SHOV.rotation_euler.x = math.radians(SB * cl * 0.5)
    for o in (ARM1, ARM2, CLAW, SHOV): o.keyframe_insert("rotation_euler", frame=fr)
# the pit deepens 0.3 -> 1.25 m during the time-lapse (f565-760)
PIT = O["CUT_Pit"]
for fr, d in ((1, 0.3), (565, 0.35), (760, 1.25), (END, 1.25)):
    PIT.scale.z = d + 0.6; PIT.keyframe_insert("scale", frame=fr)

# ================================================================== sun time-lapse (B4): midday -> warm late afternoon
SUNO = O["Sun"]; SUN = SUNO.data
for fr, el, az, en, col in ((1, 50, -35, 4.0, (1.0, 0.95, 0.86)), (565, 50, -35, 4.0, (1.0, 0.95, 0.86)),
                            (780, 28, 55, 3.6, (1.0, 0.78, 0.55)), (END, 28, 55, 3.6, (1.0, 0.78, 0.55))):
    SUNO.rotation_euler = (math.radians(90 - el), 0, math.radians(az)); SUNO.keyframe_insert("rotation_euler", frame=fr)
    SUN.energy = en; SUN.color = col; SUN.keyframe_insert("energy", frame=fr); SUN.keyframe_insert("color", frame=fr)

# ================================================================== the ONE camera
CAM = O["CAM_Film"]
def wpt(rig, bone):
    fs_cache = None
    return Wh(rig, bone)
def face_pt(rig, f):
    fs(f); return (Wh(rig, "eye.L") + Wh(rig, "eye.R")) / 2
# camera keys: (frame, position, look-at, lens). Look-at points come from the evaluated characters where useful.
K = []
def ck(f, pos, tgt, lens):
    K.append((f, Vector(pos), Vector(tgt), lens))
# B1: on the toddler walking to the well, then dive with him
for f in (1, 40, 80):
    hp = face_pt(TODR, f); ck(f, hp + Vector((0.35, -1.65, 0.05)), hp + Vector((-0.15, 0.0, -0.22)), 30)
f = 100; hp = face_pt(TODR, f); ck(f, Vector((0.25, -1.75, 0.65)), Vector((0.1, 0.1, 0.05)), 28)
for f in (120, 140, 160, 175, 186):
    hp = face_pt(TODR, f); ck(f, Vector((0.05, -1.7, hp.z + 0.45)), hp + Vector((0, 0, -0.25)), 28)
# B2: at the bottom, toddler crying, rope loop comes down; then rise with the loop to the top (f330-397)
for f in (200, 240, 280, 320):
    hp = face_pt(TODR, f); ck(f, hp + Vector((0.25 * math.sin(f / 50.0), -1.55, 0.35)), hp + Vector((0, 0, 0.12)), 28)
ck(360, Vector((0.0, -1.9, -4.5)), Vector((0.0, 0.2, -3.6)), 26)
fs(397); rp = face_pt(RESR, 397)
ck(397, Vector((-0.45, -2.6, 1.55)), (rp + Vector((0.45, 0.0, -0.45))), 26)
# B3: pull back to the digger, rescuer's face kept left in frame
ck(450, Vector((0.2, -4.4, 2.0)), Vector((1.2, 1.0, 0.9)), 26)
ck(520, Vector((0.8, -5.6, 2.3)), Vector((1.6, 1.2, 0.8)), 26)
# B4: wide cut-away time-lapse: the pit is shallow, the toddler deep
ck(600, Vector((0.6, -9.2, -0.6)), Vector((0.6, 0.0, -3.2)), 24)
ck(690, Vector((0.4, -10.6, -2.3)), Vector((0.4, 0.0, -3.9)), 24)
# B5: swoop up and left to meet the teen walking in
fs(800); tp = face_pt(TEENR, 800)
ck(760, Vector((-1.0, -6.0, 1.0)), Vector((-1.6, 1.0, 0.9)), 26)
for f in (820, 860, 900, 940):
    tp = face_pt(TEENR, f); rp = face_pt(RESR, f); mid = (tp + rp) / 2
    ck(f, mid + Vector((0.55, -2.4, 0.0)), mid + Vector((0.0, 0.0, -0.15)), 30)
# the rescuer's nod close (waist ring appears on the teen at f972, out of frame)
for f in (962, 980):
    rp = face_pt(RESR, f); ck(f, rp + Vector((1.25, -1.55, 0.05)), rp + Vector((0.0, 0, -0.08)), 34)
# B6: the knot: chest-up on the teen, hands at his waist knot, face in frame
for f in (1000, 1040, 1080):
    tp = face_pt(TEENR, f); fs(f); kn = O["ROPE_Knot"].matrix_world.translation
    mid = (tp + kn) / 2; ck(f, mid + Vector((0.45, -1.45, 0.0)), mid, 30)
# B7: tilt up the rope to the pulley (he leaves frame), then down the rope into the well: his legs go in
ck(1100, Vector((-0.6, -1.9, 1.6)), Vector((-0.3, 0.2, 2.1)), 28)
ck(1118, Vector((-0.2, -1.8, 2.0)), Vector((0.0, 0.05, 2.45)), 28)
ck(1140, Vector((0.0, -1.9, 1.5)), Vector((0.0, 0.05, 0.2)), 28)
for f in (1170, 1200, 1230, 1260, 1290):
    fs(f); hd = face_pt(TEENR, f); ck(f, Vector((0.15, -1.55, hd.z + 0.05)), hd + Vector((0, 0, 0.0)), 28)
# B9: both faces (teen upside down above, toddler below), the grab
for f in (1320, 1352, 1390, 1430):
    a = face_pt(TEENR, f); b = face_pt(TODR, f); mid = (a + b) / 2
    ck(f, mid + Vector((0.3 * math.sin(f / 40.0), -1.65, 0.0)), mid, 28)
# B10: rise together
for f in (1470, 1500, 1530, 1552):
    a = face_pt(TEENR, f); b = face_pt(TODR, f); mid = (a + b) / 2
    ck(f, mid + Vector((0.2, -1.8, 0.15)), mid + Vector((0, 0, 0.05)), 28)
# B11: tilt up the hauling rope to the pulley (the switch happens there at SW), tilt down to the two of them cheering
ck(1568, Vector((-0.1, -2.0, 1.2)), Vector((0.0, -0.05, 1.6)), 28)
ck(1584, Vector((-0.25, -1.9, 1.9)), Vector((0.0, -0.1, 2.45)), 28)
fs(1630); tp = face_pt(TEENR, 1630); kp = face_pt(TODR, 1630); mid = (tp + kp) / 2
ck(1606, mid + Vector((0.55, -2.2, 0.55)), mid + Vector((0.15, 0, 0.15)), 30)
ck(1630, mid + Vector((0.35, -2.3, 0.10)), mid + Vector((0.1, 0, -0.15)), 30)
ck(1680, mid + Vector((0.15, -2.6, 0.30)), mid + Vector((0.1, 0, -0.12)), 30)
ck(END, mid + Vector((-0.05, -3.0, 0.75)), mid + Vector((0.1, 0, -0.08)), 30)
K.sort(key=lambda k: k[0])
px = [pchip([(k[0], k[1][i]) for k in K]) for i in range(3)]
tx = [pchip([(k[0], k[2][i]) for k in K]) for i in range(3)]
lx = pchip([(k[0], k[3]) for k in K])
CAM.rotation_mode = 'QUATERNION'
prev = None
for f in range(1, END + 1):
    P = Vector([px[i](f) for i in range(3)]); T = Vector([tx[i](f) for i in range(3)])
    q = (T - P).to_track_quat('-Z', 'Y')
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = P; CAM.rotation_quaternion = q; CAM.data.lens = lx(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f); CAM.data.keyframe_insert("lens", frame=f)
CAM.data.dof.use_dof = False

# ================================================================== VO + output
if not sc.sequence_editor: sc.sequence_editor_create()
seq = sc.sequence_editor
strips = seq.strips if hasattr(seq, "strips") else seq.sequences
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
sc.render.filepath = "//render/ToddlerWell_v009_####.png"
sc.render.image_settings.file_format = 'PNG'
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
