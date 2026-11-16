"""NeverBathed: every shot as its own clip (character keys, props, camera + marker).
blender -b sets.blend --python 03_shots.py -- <out.blend> <shots.json> [only=1a,1b]
shots.json: [{"id": "1a", "f0": 1, "len": 110}, ...]  (Phase 1: provisional, contiguous; Phase 2: VO frames, trimmed)
Each shot function receives (f0, n) and keys its action at 1x from f0; a shot shorter than its clip is trimmed (cut), never stretched."""
import sys, os, math, json, random
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion
V = Vector
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
a = sys.argv[sys.argv.index("--") + 1:]; OUT, SHOTS = a[0], a[1]
ONLY = set(a[2].split("=", 1)[1].split(",")) if len(a) > 2 and a[2].startswith("only=") else None
sc = bpy.context.scene; R_ = math.radians
GZ = [0.0]
def ground_z(x, y): return GZ[0]          # overrides anim_lib: flat floors everywhere (raft/ladder poses key feet directly)

CH = ("AmouY", "AmouO", "V1", "V2")
RIG = {n: Rig(bpy.data.objects[n]) for n in CH}; HUM = {n: Human(RIG[n]) for n in CH}
for n in CH:
    o = bpy.data.objects[n]; add_hand_limits(o)
    for s in "LR":   # re-open the elbow after add_hand_limits (MPFB rest elbow ~46 deg: min 0 gives mannequin A-pose arms)
        lo = o.pose.bones["lowerarm01." + s]; lo.ik_min_x = R_(-40); lo.ik_max_x = R_(100)
    o.animation_data_create()
PARK = {n: V((-400.0 - 10 * i, 0, 0)) for i, n in enumerate(CH)}

def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def Ry(d): return Matrix.Rotation(R_(d), 3, 'Y')
def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')
def fwd(yaw): return Rz(yaw) @ V((0, -1, 0))          # MPFB faces -Y at yaw 0
def rgt(yaw): return Rz(yaw) @ V((-1, 0, 0))          # character's own right
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ visibility / parking
def key_vis(o, f, show):
    o.hide_render = o.hide_viewport = not show
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
ACTIVE = {}          # shot id -> set of characters used
def place_rig(n, f0, f1, active):
    o = bpy.data.objects[n]
    o.location = (0, 0, 0) if active else PARK[n]
    for f in (f0, f1): o.keyframe_insert("location", frame=f)

# ------------------------------------------------------------------ body keys
def body(n, f, root, yaw=0.0, flex=0.0, side=0.0, spine=(0.0, 0.0, 0.0), head=(0.0, 0.0)):
    """root: world position of the pelvis root head; flex>0 tips the pelvis forward; spine=(flex, twist, side); head=(pitch, yaw)"""
    HUM[n].key_root(f, V(root), yaw=yaw, flex=flex, side=side)
    HUM[n].key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)

SOLE = 0.015
def foot(n, s, f, ankle, yaw, pitch=0.0, roll=0.0, knee=None):
    """ankle: world point for the ankle joint; pitch>0 lifts the toes; knee: world point the knee aims at"""
    H = HUM[n]; a_ = H.ankle[s]; Rw = Rz(yaw) @ Rx(pitch) @ Ry(roll)
    ankle = V(ankle) + V((0, 0, SOLE))          # MPFB shoe soles sit ~1.5 cm below the rest ankle height
    M = Matrix.Translation(V(ankle)) @ Rw.to_4x4() @ Matrix.Translation(-a_) @ H.r.rest("IK_foot." + s)
    H.r.key_world("IK_foot." + s, f, M)
    if knee is None: knee = V(ankle) + Rz(yaw) @ V((0, -0.7, 0.45))
    nm = "Pole_knee." + s; pb = H.r.PB[nm]
    pb.location = H.r.rest(nm).to_3x3().inverted() @ (V(knee) - H.r.BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)

def stand_feet(n, f, root, yaw, spread=0.0, back=0.0):
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = V(root) + rgt(yaw) * (-sx) * (0.11 + spread) + fwd(yaw) * (0.02 - back * sx * 0.5)
        foot(n, s, f, (xy.x, xy.y, GZ[0] + HUM[n].ankle[s].z), yaw + sx * 6)

def elbow(n, s, f, pole):
    nm = "Pole_elbow." + s; pb = RIG[n].PB[nm]
    pb.location = RIG[n].rest(nm).to_3x3().inverted() @ (V(pole) - RIG[n].BN[nm].head_local); pb.keyframe_insert("location", frame=f, group=nm)

def wpos(n, bone, f=None, tail=False):
    if f is not None: sc.frame_set(int(f))
    pb = bpy.data.objects[n].pose.bones[bone]
    return bpy.data.objects[n].matrix_world @ (pb.tail if tail else pb.head)

def hand(n, s, f, palm, normal, fingers, pole=None, pose="relaxed", amount=1.0):
    place_hand(bpy.data.objects[n], s, f, V(palm), V(normal), V(fingers))
    if pole is not None: elbow(n, s, f, pole)
    if pose: apply_pose(bpy.data.objects[n], s, pose, f, amount)

def relaxed_arm(n, s, f, yaw, fwd_=0.04, out=0.04, up=0.0, pose="relaxed"):
    """arm hanging with a soft elbow, palm toward the thigh. Call after the body keys for frame f."""
    sx = 1 if s == "L" else -1
    sh = wpos(n, "upperarm01." + s, f)
    down = V((0, 0, -1)); r = rgt(yaw) * (-sx)          # outward for this side
    palm = sh + down * (0.58 - up) + r * (0.03 + out) + fwd(yaw) * fwd_
    hand(n, s, f, palm, -r, down + fwd(yaw) * 0.15, pole=sh + down * 0.3 + r * 0.2 - fwd(yaw) * 0.45, pose=pose)

def sit(n, f, seat, seat_z, yaw, knee_fwd=0.46, spread=0.13, lean=0.0, spine=(0.0, 0.0, 0.0), head=(0.0, 0.0), feet_back=0.0):
    """seated on a surface at seat_z: pelvis on the seat, thighs forward, feet flat on the floor below the knees"""
    root = V((seat[0], seat[1], seat_z + 0.16))
    body(n, f, root, yaw, flex=lean, spine=spine, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        ank = root + fwd(yaw) * (knee_fwd - feet_back) - rgt(yaw) * sx * spread
        foot(n, s, f, (ank.x, ank.y, GZ[0] + HUM[n].ankle[s].z), yaw + sx * 4, knee=ank + fwd(yaw) * 0.6 + V((0, 0, 0.5)))
    return root

def breathe(n, f0, f1, root, yaw, every=40, spine=(4.0, 0, 0), head=(0, 0), amp=0.006, **kw):
    """idle: chest rises and falls, head drifts a little (never a frozen hold)"""
    k = 0
    for f in range(f0, f1 + 1, every // 2):
        u = (k % 2); k += 1
        body(n, f, V(root) + V((0, 0, amp * u)), yaw, spine=(spine[0] + 1.5 * u, spine[1], spine[2]), head=(head[0] + 1.5 * u, head[1] + 2.0 * math.sin(k)), **kw)

# ------------------------------------------------------------------ props
def prop_copy(src, name, f0, f1):
    o = bpy.data.objects[src].copy(); o.name = name; bpy.data.objects[src].users_collection[0].objects.link(o)
    o.animation_data_clear()
    for c in o.children: pass
    vis_window(o, f0, f1)
    return o
def vis_window(o, f0, f1):
    key_vis(o, 1, False) if f0 > 1 else None
    key_vis(o, f0, True); key_vis(o, f1 + 1, False)
def child_of(o, n, bone, f):
    """attach o to the bone keeping its current world matrix at frame f"""
    sc.frame_set(int(f)); c = o.constraints.new('CHILD_OF'); c.target = bpy.data.objects[n]; c.subtarget = bone
    bpy.context.view_layer.update()
    pb = bpy.data.objects[n].pose.bones[bone]
    c.inverse_matrix = (bpy.data.objects[n].matrix_world @ pb.matrix).inverted()
    return c

def ik_mat(n, s, f):
    sc.frame_set(int(f)); return bpy.data.objects[n].pose.bones["IK_hand." + s].matrix.copy()
def key_ik(n, s, f, M):
    pb = bpy.data.objects[n].pose.bones["IK_hand." + s]; pb.matrix = M
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
def rigid(pivot, rot3, move):
    """world-space rigid transform: rotate about pivot, then translate by move"""
    return Matrix.Translation(V(pivot) + V(move)) @ rot3.to_4x4() @ Matrix.Translation(-V(pivot))
def hold_prop(n, s, f, prop, contact, approach, finger_dir, grip):
    """grip the prop where it stands at frame f and pin it to the wrist; returns the IK_hand matrix at the grip"""
    sc.frame_set(int(f)); bpy.context.view_layer.update()
    grip_object(bpy.data.objects[n], s, f, prop, V(contact), V(approach), finger_dir=V(finger_dir), grip=grip)
    M0 = ik_mat(n, s, f); child_of(prop, n, "wrist." + s, f); return M0

# ------------------------------------------------------------------ cameras (one per shot, marker-bound at its first frame: hard cuts)
CAMS = {}
def camera(sid, f0, n, keys, fstop=8.0, catch=True):
    """keys: [(u 0..1, cam_pos, aim, lens)] eased per segment; keyed every frame of the clip"""
    cd = bpy.data.cameras.new("CAM_" + sid); cd.sensor_fit = 'AUTO'; cd.clip_start = 0.03; cd.clip_end = 3000
    cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new("CAM_" + sid, cd); sc.collection.objects.link(cam)
    for i in range(n):
        u = i / max(1, n - 1)
        for (u0, c0, a0, l0), (u1, c1, a1, l1) in zip(keys, keys[1:]):
            if u <= u1 or (u1 == keys[-1][0]):
                t = ss((u - u0) / max(1e-6, u1 - u0)); break
        c = V(c0).lerp(V(c1), t); aim = V(a0).lerp(V(a1), t); lens = l0 + (l1 - l0) * t
        cam.location = c; cam.rotation_mode = 'QUATERNION'
        cam.rotation_quaternion = (aim - c).to_track_quat('-Z', 'Y')
        cd.lens = lens; cd.dof.focus_distance = (aim - c).length
        f = f0 + i
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
        cd.keyframe_insert("lens", frame=f); cd.keyframe_insert("dof.focus_distance", frame=f)
    m = sc.timeline_markers.new("S" + sid, frame=f0); m.camera = cam
    if catch:   # small specular-only catchlight near the lens (eyes read, no fill on skin)
        L = bpy.data.lights.new("Catch_" + sid, 'POINT'); L.energy = 3.0; L.shadow_soft_size = 0.02
        lo = bpy.data.objects.new("Catch_" + sid, L); sc.collection.objects.link(lo); lo.parent = cam; lo.location = (0.08, 0.1, 0)
        lo.visible_diffuse = False; lo.visible_transmission = False; lo.visible_volume_scatter = False
        key_vis(lo, 1, False) if f0 > 1 else None; key_vis(lo, f0, True); key_vis(lo, f0 + n, False)
    CAMS[sid] = cam
    return cam

# ================================================================== SHOTS

# ------------------------------------------------------------------ reusable actions
THIGH = {n: (RIG[n].BN["upperleg01.L"].head_local - RIG[n].BN["lowerleg01.L"].head_local).length for n in CH}
SHIN = {n: (RIG[n].BN["lowerleg01.L"].head_local - RIG[n].BN["foot.L"].head_local).length for n in CH}
def kneel(n, f, knees, yaw, thigh_back=15.0, lean=20.0, spine=(25.0, 0.0, 0.0), head=(15.0, 0.0), spread=0.13, toes=78.0):
    """both knees on the floor (knees = midpoint, world), toes tucked, pelvis above and slightly behind the knees"""
    k = V((knees[0], knees[1], 0.0)); L = THIGH[n]; t = R_(thigh_back)
    root = k + V((0, 0, GZ[0] + 0.09 + L * math.cos(t))) - fwd(yaw) * (L * math.sin(t)) + V((0, 0, HUM[n].root_head.z - RIG[n].BN["upperleg01.L"].head_local.z))
    body(n, f, root, yaw, flex=lean, spine=spine, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        kn = k - rgt(yaw) * sx * spread
        ank = kn - fwd(yaw) * (SHIN[n] * 0.93) + V((0, 0, GZ[0] + 0.185))
        foot(n, s, f, ank, yaw + sx * 5, pitch=toes, knee=kn + fwd(yaw) * 0.6 + V((0, 0, -0.1)))
    return root

def stand_idle(n, f0, f1, pos, yaw, head=(0.0, 0.0), spine=(3.0, 0.0, 0.0), every=40, arms=True, head_fn=None):
    k = 0
    for f in list(range(f0, f1, every)) + [f1]:
        hd = head_fn(f) if head_fn else (head[0] + (1.5 if k % 2 else 0), head[1] + 2 * math.sin(k))
        body(n, f, V(pos) + V((0, 0, HUM[n].root_head.z - 0.01 + (0.004 if k % 2 else 0))), yaw, spine=(spine[0] + (1.5 if k % 2 else 0), spine[1], spine[2]), head=hd)
        stand_feet(n, f, pos, yaw)
        if arms: relaxed_arm(n, "L", f, yaw); relaxed_arm(n, "R", f, yaw)
        k += 1
def walk_arms(n, f0, f1, yaw_fn, every=8, amp=0.16):
    """bent elbows (~35 deg), forearms swinging opposite to the legs"""
    for i, f in enumerate(sorted(set(list(range(f0, f1 + 1, every)) + [f1]))):
        sw = amp * math.sin((f - f0) * math.pi / 22.0)
        relaxed_arm(n, "L", f, yaw_fn(f), fwd_=0.08 + sw, up=0.13 + 0.06 * max(0.0, sw / amp))
        relaxed_arm(n, "R", f, yaw_fn(f), fwd_=0.08 - sw, up=0.13 + 0.06 * max(0.0, -sw / amp))

