"""LegoInNose v013 stage B: staging, acting, the one-brick story, the nose x-ray, the void, the one continuous camera.
blender -b base.blend --python 02_animate.py -- <out.blend> [stage]
Timing is built on the client's VO word times from the start (vo_words.json, frame = 1 + round(t*60)); end 2036."""
import bpy, bmesh, sys, math, random, json, os
from mathutils import Vector, Matrix, Quaternion, Euler
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = "/home/user/Muhammed/blender/LegoInNose_v013/scripts"
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_v013.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; STAGE = args[1] if len(args) > 1 else "all"
random.seed(11)
END = 2036
BED_X, BATH_X = 8.0, 16.0
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
BOY, MOM, MAN = O["Boy"], O["Mom"], O["Man"]
BB, MB, NB = O["Boy.body"], O["Mom.body"], O["Man.body"]
RED, YEL, TWZ, INH, BOOK = O["BrickRed"], O["BrickYellow"], O["Tweezers"], O["Inhaler"], O["Book"]
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False

# ================================================================== rigs
PR, MR, NR = make_human_ctrl(BOY), make_human_ctrl(MOM), make_human_ctrl(MAN)
HB_, HM_, HN_ = Human(PR), Human(MR), Human(NR)
for r in (BOY, MOM, MAN):
    add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":   # natural elbow range (MPFB rest elbow is bent): allow straightening
        lo = r.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(145)
DOMB, DOMM, DOMN = dom_bones(BB, BOY), dom_bones(MB, MOM), dom_bones(NB, MAN)

def key_pole(ctrl, side, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + side; pb = ctrl.PB[n]
    pb.location = ctrl.rest(n).to_3x3().inverted() @ (Vector(target) - ctrl.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def key_head(ctrl, f, yaw, pitch, roll=0.0):
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        ctrl.key_rot(n, f, [("X", pitch * w), ("Y", roll * w), ("Z", yaw * w)])

def key_spine(ctrl, f, flex=0.0, twist=0.0, side=0.0):
    for n, w in Human.SPINE_W.items():
        ctrl.key_rot(n, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])

def pinch_pt(rig, s):
    return (Wt(rig, "finger1-3." + s) + Wt(rig, "finger2-3." + s)) / 2

def reach(rig, ctrl, s, f, P, fdir, palm, pose="pinch", it=5, pt=pinch_pt, pole=None):
    """key IK_hand so the hand's grip point (default: thumb+index tips) lands on world point P"""
    apply_pose(rig, s, pose, f)
    place_hand(rig, s, f, Vector(P) - Vector(fdir).normalized() * 0.07, palm, fdir, skin=0.0)
    if pole is not None: key_pole(ctrl, s, f, pole)
    pb = rig.pose.bones["IK_hand." + s]; Rr = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    for k in range(it):
        fs(f); err = Vector(P) - pt(rig, s)
        if err.length < 0.0008: break
        pb.location = pb.location + Rr @ err; pb.keyframe_insert("location", frame=f, group=pb.name)
    fs(f); e = (Vector(P) - pt(rig, s)).length
    if e > 0.004: log("REACH_ERR", rig.name, s, f, round(e * 1000, 1), "mm")
    return e

def rest_hand(rig, ctrl, s, f, P, fdir, palm, pose="relaxed", pole=None):
    """hand resting with the palm on a surface point P"""
    apply_pose(rig, s, pose, f)
    place_hand(rig, s, f, P, palm, fdir, skin=0.012)
    if pole is not None: key_pole(ctrl, s, f, pole)

# ================================================================== BOY: seated ON the rug (R3), feet on the rug
BX = -0.48
RUG = 0.012
fs(1)
def boy_root(f, dx=0.0, dy=0.0, dz=0.0, flex=-4.0, yaw=0.0, side=0.0):
    HB_.key_root(f, Vector((BX + dx, 0.0 + dy, BOY_Z + dz)), yaw=yaw, flex=flex, side=side)
BOY_Z = 0.15
boy_root(1)
for s in "LR":
    a = PR.BN["foot." + s].head_local
    tgt = Vector((BX + a.x * 1.15, -0.40, RUG + a.z))
    PR.key_world("IK_foot." + s, 1, Matrix.Translation(tgt - a) @ PR.rest("IK_foot." + s))
    key_pole(PR, s, 1, (BX + a.x * 1.6, -0.9, 0.9), kind="knee")
fs(1)
trs = O["Boy.trousers"]
def lowest_under(obj, xy_c, r=0.12):
    pts = eval_points(obj)
    return min(p[1].z for p in pts if (p[1].to_2d() - Vector(xy_c)).length < r)
for _ in range(4):
    low = lowest_under(trs, (BX, 0.02))
    BOY_Z += (RUG + 0.004) - low
    boy_root(1)
fs(1); log("boy seat snapped: trousers low", round(lowest_under(trs, (BX, 0.02)), 4), "rug", RUG)

# ================================================================== MOM: seated ON the sofa, facing +X
SOFA = O["Sofa"]
MY = -0.30
seat_top = ray_down([SOFA], -1.10, MY)
front = None
for xx in [x / 100 for x in range(-120, -40, 2)]:
    z_ = ray_down([SOFA], xx, MY)
    if z_ is None or z_ < seat_top - 0.10: front = xx; break
log("sofa seat top", round(seat_top or -1, 3), "front edge x", front)
MOM_X = (front or -0.9) - 0.30
MOM_Z = 0.80
def mom_root(f, dx=0.0, dz=0.0, flex=0.0, yaw=90.0):
    HM_.key_root(f, Vector((MOM_X + dx, MY, MOM_Z + dz)), yaw=yaw, flex=flex)
mom_root(1)
for s in "LR":
    a = MR.BN["foot." + s].head_local
    side = 1 if s == "L" else -1      # facing +X: her left is +Y
    tgt = Vector(((front or -0.9) + 0.12, MY + side * 0.11, a.z))
    M = Matrix.Translation(tgt) @ Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation(-a) @ MR.rest("IK_foot." + s)
    MR.key_world("IK_foot." + s, 1, M)
    key_pole(MR, s, 1, (tgt.x + 0.8, tgt.y, 0.7), kind="knee")
fs(1)
mt = O["Mom.trousers"]
for _ in range(4):
    lowm = lowest_under(mt, (MOM_X - 0.05, MY), r=0.14)
    MOM_Z += (seat_top + 0.006) - lowm
    mom_root(1)
fs(1); log("mom seat snapped: trousers low", round(lowest_under(mt, (MOM_X - 0.05, MY), r=0.14), 4), "seat", round(seat_top, 4))

# ================================================================== MAN: propped up ON the mattress (bedroom), later standing in the tub
BED = O["Bed"]
fs(1)
mat_top = ray_down([BED], BED_X, 0.5)
head_y = 1.2
for yy in [y / 100 for y in range(160, 40, -2)]:
    z_ = ray_down([BED], BED_X, yy)
    log("bed profile y", yy, round(z_ or -1, 3)) if yy in (1.5, 1.3, 1.1, 0.9, 0.5, 0.0) else None
log("mattress top", round(mat_top, 3))
sc["mat_top"] = mat_top

exec(open(HERE + "/02b_story.py").read())
if True:
    for o_ in O:
        for m_ in getattr(o_, "modifiers", []):
            if m_.type == 'SUBSURF': m_.show_viewport = True
    open(OUT + ".log.txt", "w").write("\n".join(LOG))
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True); print("ANIM_OK", OUT); raise SystemExit
if STAGE == "pose":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); open(OUT + ".log.txt", "w").write("\n".join(LOG)); print("POSE_OK"); raise SystemExit
