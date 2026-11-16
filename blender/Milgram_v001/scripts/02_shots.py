"""Milgram: every shot as its own clip (character keys, props, camera + marker).
blender -b sets.blend --python 03_shots.py -- <out.blend> <shots.json> [only=1a,1b]
shots.json: [{"id": "1a", "f0": 1, "len": 156}, ...]  (Phase 1: provisional, contiguous; Phase 2: VO frames, trimmed)
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
XB, XH = sc["XB"], sc["XH"]
TABLE_Z = sc["TABLE_Z"]; SWX = list(sc["SWX"]); SWZ = sc["SWZ"]; LAMPZ = sc["LAMPZ"]; GEN = list(sc["GEN"])
GZ = [0.0]
def ground_z(x, y): return GZ[0]
CH = ("Stranger", "Subject", "Doc")
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

def sit(n, f, seat, seat_z, yaw, knee_fwd=0.46, spread=0.13, lean=0.0, spine=(0.0, 0.0, 0.0), head=(0.0, 0.0), feet_back=0.0, heel=0.0):
    """seated on a surface at seat_z: pelvis on the seat, thighs forward, feet flat on the floor below the knees"""
    root = V((seat[0], seat[1], seat_z + 0.16))
    body(n, f, root, yaw, flex=lean, spine=spine, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        ank = root + fwd(yaw) * (knee_fwd - feet_back) - rgt(yaw) * sx * spread
        pitch = -math.degrees(math.asin(min(0.9, heel / 0.15))) if heel > 0 else 0.0     # heels up, toes on the floor
        foot(n, s, f, (ank.x, ank.y, GZ[0] + HUM[n].ankle[s].z + heel), yaw + sx * 4, pitch=pitch, knee=ank + fwd(yaw) * 0.6 + V((0, 0, 0.5)))
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

# ================================================================== MILGRAM SHOTS (spliced into 02_shots.py)
# ---- setup: park rigs, measure seats, hide props by default, levers up, lamps off
for n in CH: bpy.data.objects[n].location = PARK[n]
bpy.context.view_layer.update()
def ray_down(x, y, z0=1.2):
    dg = bpy.context.evaluated_depsgraph_get(); hit, loc, *_ = sc.ray_cast(dg, V((x, y, z0)), V((0, 0, -1)))
    return loc.z if hit else None
SEAT_A = V((0.0, -0.76)); SEAT_AZ = ray_down(0.0, -0.78, 0.8) + 0.06
SEAT_B = V((XB, 0.48)); SEAT_BZ = ray_down(XB, 0.47, 0.8) + 0.075
print("SEATS", SEAT_AZ, SEAT_BZ)
for n in CH: bpy.data.objects[n].location = (0, 0, 0)
bpy.context.view_layer.update()
def orient(o, loc, ydir, zhint=V((0, 0, 1))):
    y = V(ydir).normalized(); x = y.cross(V(zhint)).normalized(); z = x.cross(y)
    o.matrix_world = Matrix.Translation(V(loc)) @ Matrix((x, y, z)).transposed().to_4x4()

PROPS = [o for o in bpy.data.collections["Props"].objects]
for o in PROPS:
    if o.parent is None: o.location = V(o.location) + V((60.0, 0, 0))
    key_vis(o, 1, False)
LEVERS = [bpy.data.objects["Gen_LeverPivot%02d" % i] for i in range(30)]
LAMPS = [bpy.data.materials["M_Lamp%02d" % i] for i in range(30)]
UP, DOWN = R_(-25), R_(22)
def const_keys(idb):
    for fc in all_fcurves(idb):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def lever(i, f, down):
    LEVERS[i].rotation_euler = (DOWN if down else UP, 0, 0); LEVERS[i].keyframe_insert("rotation_euler", index=0, frame=f)
def lamp(i, f, on):
    P = LAMPS[i].node_tree.nodes["Principled BSDF"].inputs['Emission Strength']; P.default_value = 7.0 if on else 0.0
    P.keyframe_insert("default_value", frame=f)
def panel_state(f, n_down):
    for i in range(30): lever(i, f, i < n_down); lamp(i, f, i < n_down)
def wrong_lamp(f, on):
    P = bpy.data.materials["M_WrongLamp"].node_tree.nodes["Principled BSDF"].inputs['Emission Strength']; P.default_value = 30.0 if on else 0.0
    P.keyframe_insert("default_value", frame=f)
    L = bpy.data.objects["LabA_WrongGlow"].data; L.energy = 25.0 if on else 0.0; L.keyframe_insert("energy", frame=f)
panel_state(1, 0); wrong_lamp(1, False)
def lever_tip(i, down=False):
    piv = LEVERS[i]; a = DOWN if down else UP
    return V(piv.location) + Rx(math.degrees(a)) @ V((0, -0.028, 0))

# ---- expressions (Stranger has MPFB expression shape keys) and the jaw (everyone)
SK = bpy.data.objects["Stranger.body"].data.shape_keys
XK = [kb.name for kb in SK.key_blocks if kb.name.startswith("X_")]
def expr(f, **vals):
    for nm in XK:
        kb = SK.key_blocks[nm]; kb.value = vals.get(nm[2:].replace("-", "_"), 0.0); kb.keyframe_insert("value", frame=f)
def jaw(n, f, deg):
    RIG[n].key_rot("jaw", f, [("X", deg)])
def talk(n, f0, f1, every=9, amp=5.0, start=0):
    k = 0
    for f in range(f0, f1 + 1, every):
        jaw(n, f, 0.0 if (k % 2 == 0 or f - f0 < start) else amp * (0.6 + 0.4 * math.sin(k * 1.3))); k += 1
    jaw(n, f1, 0.0)

# ---- subject seated at the generator (yaw 180: faces +Y)
YS = 180.0
def subj_body(f, lean=12.0, spine=(10.0, 0.0, 0.0), head=(8.0, 0.0)):
    if lean > 3.0: spine = (spine[0] + lean - 3.0, spine[1], spine[2]); lean = 3.0     # bend in the spine, pelvis level on the seat
    return sit("Subject", f, SEAT_A, SEAT_AZ, YS, knee_fwd=0.44, lean=lean, spine=spine, head=head, heel=0.04)
def subj_hand_table(s, f, x=None, y=-0.25):
    sx = 1 if s == "R" else -1
    p = V(((0.28 if x is None else x) * sx, y, TABLE_Z + 0.028))
    sh = wpos("Subject", "upperarm01." + s, f)
    hand("Subject", s, f, p, V((0, 0, -1)), V((-0.25 * sx, 1, 0)), pole=sh + V((0.40 * sx, -0.10, -0.08)), pose="flat_palm")
def subj_hand_lap(s, f):
    """idle hand resting on top of the thigh (the table top made fingertips graze in every flat pose)"""
    hp = wpos("Subject", "upperleg01." + s, f); kn = wpos("Subject", "lowerleg01." + s, f)
    p = hp.lerp(kn, 0.55) + V((0, 0, 0.085)); sh = wpos("Subject", "upperarm01." + s, f)
    sx = 1 if s == "R" else -1
    hand("Subject", s, f, p, V((0, 0, -1)), (kn - hp).normalized() + V((-0.3 * sx, 0, -0.2)), pole=sh + V((0.35 * sx, -0.20, -0.25)), pose="relaxed")
def subj_seated(f0, n, heads, lean=12.0, hands=("table", "table"), spine_tw=None, flex=10.0):
    """heads: [(u, (pitch, yaw))] eased; hands on the table unless a shot overrides them"""
    f1 = f0 + n - 1; ks = list(range(f0, f1, 24)) + [f1]
    for k, f in enumerate(ks):
        u = (f - f0) / max(1, n - 1)
        hd = interp_keys(heads, u)
        tw = interp_keys(spine_tw, u) if spine_tw else 0.0
        subj_body(f, lean=lean + (0.8 if k % 2 else 0.0), spine=(flex + (1.2 if k % 2 else 0), tw, 0.0), head=hd)
        if hands[0] == "table": subj_hand_lap("L", f)
        if hands[1] == "table": subj_hand_lap("R", f)
def interp_keys(keys, u):
    if isinstance(keys, (int, float)): return keys
    for (u0, a0), (u1, a1) in zip(keys, keys[1:]):
        if u <= u1:
            t = ss((u - u0) / max(1e-6, u1 - u0))
            if isinstance(a0, tuple): return tuple(x + (y - x) * t for x, y in zip(a0, a1))
            return a0 + (a1 - a0) * t
    return keys[-1][1]

def fingertip(n, s, f):
    return wpos(n, "finger2-3." + s, f, tail=True)
def put_tip(n, s, f, pt, dirf, normal=V((0, 0, -1)), pose="point"):
    """key the hand so the index fingertip lands on pt (point pose), fingers along dirf"""
    sh = wpos(n, "upperarm01." + s, f); out = rgt(YS) * (1 if s == "R" else -1)
    hand(n, s, f, V(pt) - dirf * 0.10, normal, dirf, pole=sh + out * 0.30 + V((0, 0, -0.35)) - fwd(YS) * 0.10, pose=pose)
    ob = bpy.data.objects[n]; pb = ob.pose.bones["IK_hand." + s]; R3 = ob.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted()
    for _ in range(3):
        sc.frame_set(int(f)); d = V(pt) - fingertip(n, s, f)
        pb.location = pb.location + R3 @ d; pb.keyframe_insert("location", frame=f, group=pb.name)
    sc.frame_set(int(f)); return (V(pt) - fingertip(n, s, f)).length

def press(f_t, i, appr=26, hold=16, back=22, s=None):
    """the subject's right index finger comes in, rests on lever i, pushes it down; the lamp over it lights"""
    s = s or ("R" if SWX[i] > -0.05 else "L")
    tip = lever_tip(i) + V((0, 0, 0.020)); tip_dn = lever_tip(i, True) + V((0, -0.004, 0.022))
    sh = wpos("Subject", "upperarm01." + s, f_t)
    dirf = (tip - sh); dirf.z *= 0.6; dirf.normalize()
    e = [put_tip("Subject", s, f_t - appr, tip - dirf * 0.06 + V((0, 0, 0.04)), dirf)]
    e.append(put_tip("Subject", s, f_t, tip, dirf))
    lever(i, f_t, False); lever(i, f_t + 6, True)
    for k_ in (1, 2, 3, 4, 5):      # the fingertip follows the lever knob along its arc (no crossing mid-press)
        t_ = k_ / 6.0; ang = UP + (DOWN - UP) * t_
        LEVERS[i].rotation_euler = (ang, 0, 0); LEVERS[i].keyframe_insert("rotation_euler", index=0, frame=f_t + k_)
        kt = V(LEVERS[i].location) + Rx(math.degrees(ang)) @ V((0, -0.028, 0)) + V((0, -0.004 * t_, 0.020 + 0.002 * t_))
        put_tip("Subject", s, f_t + k_, kt, dirf)
    e.append(put_tip("Subject", s, f_t + 6, tip_dn, dirf))
    lamp(i, f_t + 6, True)
    e.append(put_tip("Subject", s, f_t + 6 + hold, tip_dn, dirf))
    e.append(put_tip("Subject", s, f_t + 6 + hold + back, tip_dn - dirf * 0.07 + V((0, 0, 0.05)), dirf))
    print("PRESS", i, "tip err mm", [round(x * 1000, 1) for x in e])

def fp_cam(sid, f0, n, i, push=0.05, lens=30, mode="mid"):
    """first person: just in front of the subject's face, looking down at switch i (his head is behind the lens).
    mode: mid (one hand, a few levers), tight (one lever fills the frame), wide (the panel and both hands)"""
    x = SWX[i]
    side = -1 if x > -0.05 else 1          # away from the pressing arm
    aim = V((x, GEN[2] + 0.01, SWZ + 0.02))
    if mode == "tight":
        c0 = V((x + 0.02 * side, -0.36, 1.17)); lens = 42; push = 0.04
    elif mode == "ots":      # over his right shoulder, high: both hands at the generator
        sd = 1 if x > 0 else -1     # over the shoulder of the pressing arm
        aim = V((x * 0.8, GEN[2] + 0.02, SWZ + 0.04)); c0 = V((0.55 * sd, -1.10, 1.60)); lens = 32; push = 0.12
    else:
        c0 = V((x + 0.03 * side, -0.41, 1.27))
    c1 = c0 + (aim - c0).normalized() * push
    camera(sid, f0, n, [(0, c0, aim, lens), (1, c1, aim, lens)], fstop=8.0, catch=False)

def fp_shot(sid, f0, n, n_down, presses, lens=30, mode="mid", brace=False):
    f1 = f0 + n - 1
    panel_state(f0, n_down)
    s_ = "R" if SWX[presses[-1][1]] > -0.05 else "L"
    subj_seated(f0, n, [(0, (22.0, 0.0)), (1, (26.0, 0.0))], lean=2.0, flex=4.0, hands=("table", "press") if s_ == "R" else ("press", "table"))
    first = True
    for (u, i) in presses:
        ft = f0 + int(u * n)
        if first:
            sc.frame_set(f0)
        press(ft, i)
        first = False
    if presses and f0 + int(presses[0][0] * n) - 26 > f0:   # resting before the first approach
        i = presses[0][1]; tip = lever_tip(i) + V((0, 0, 0.007)); sh = wpos("Subject", "upperarm01." + s_, f0)
        dirf = (tip - sh); dirf.z *= 0.6; dirf.normalize()
        put_tip("Subject", s_, f0, tip - dirf * 0.10 + V((0, 0, 0.06)), dirf)
    if brace:   # the other hand braced flat on the generator's top, in view in the wide framing
        o_ = "L" if s_ == "R" else "R"; sxo = 1 if o_ == "R" else -1
        for f in (f0, f0 + n // 2, f0 + n - 1):
            sh = wpos("Subject", "upperarm01." + o_, f)
            hand("Subject", o_, f, V((0.22 * sxo, GEN[2] + 0.05, GEN[5] + 0.040)), V((0, 0, -1)), V((-0.2 * sxo, 1, 0)), pole=sh + V((0.40 * sxo, -0.05, -0.10)), pose="flat_palm")
    fp_cam(sid, f0, n, presses[-1][1], lens=lens, mode=mode)

def eyes(n, f):
    return (wpos(n, "eye.L", f) + wpos(n, "eye.R", f)) / 2
GEN_OBS = [o for o in bpy.data.objects if o.name.startswith("Gen_")]
def face_cam(sid, f0, n, who, yaw_c, side_deg, dist, dz, lens, push=0.85, fstop=8.0):
    """camera on the face: from the character's front turned by side_deg, dz above (negative = below) the eyes.
    The generator sits between this lens and his face (it read as a grey slab across the frame): it is hidden for the
    close-up only (render + viewport keyed together); it is outside the frame of a face close-up anyway."""
    f1 = f0 + n - 1; keys = []
    for o in GEN_OBS:
        if not all_fcurves(o) or not any(fc.data_path == "hide_render" for fc in all_fcurves(o)): key_vis(o, 1, True)
        key_vis(o, f0, False); key_vis(o, f1 + 1, True); const_keys(o)
    for u, f, d in ((0, f0, dist), (1, f1, dist * push)):
        e = eyes(who, f); dv = Rz(side_deg) @ fwd(yaw_c)
        keys.append((u, e + dv * d + V((0, 0, dz)), e + V((0, 0, -0.03)), lens))
    camera(sid, f0, n, keys, fstop=fstop)

# ---- the doctor (Lab A, right of the subject, facing -X)
DOC = V((1.0, -1.05, 0.0)); YD = -90.0
def doc_body(f, head=(0.0, 0.0), spine=(3.0, 0.0, 0.0), dz=0.0, shift=0.0):
    body("Doc", f, DOC + rgt(YD) * shift + V((0, 0, HUM["Doc"].root_head.z - 0.012 + dz - abs(shift) * 0.2)), YD, spine=spine, head=head, side=-shift * 60)
    stand_feet("Doc", f, DOC, YD)
CLIP = {}
def doc_clipboard(sid, f0, f1, tilt=15.0, height=1.08):
    """the clipboard is placed in front of his left side and gripped (pinch) on its near long edge, Child Of the wrist"""
    cb = prop_copy("Clipboard_Doc", "Clip_" + sid, f0, f1)
    for c in cb.children: vis_window(c, f0, f1)
    fw = fwd(YD); lf = -rgt(YD); up = V((0, 0, 1))
    sc.frame_set(f0); chest = wpos("Doc", "spine03", f0)
    ctr = V((chest.x, chest.y, height)) + fw * 0.40 + lf * 0.10
    ydir = (fw * math.cos(R_(tilt)) + up * math.sin(R_(tilt))).normalized()
    orient(cb, ctr, ydir); bpy.context.view_layer.update()
    Mw = cb.matrix_world; xax = (Mw.to_3x3() @ V((1, 0, 0))).normalized()
    side = 1 if xax.dot(lf) > 0 else -1
    edge = ctr + xax * side * 0.112 - ydir * 0.03
    sh = wpos("Doc", "upperarm01.L", f0); elbow("Doc", "L", f0, sh + lf * 0.25 + V((0, 0, -0.35)) - fw * 0.15)
    zax = (Mw.to_3x3() @ V((0, 0, 1))).normalized()
    if zax.z < 0: zax = -zax
    palm = ctr + xax * side * 0.05 - ydir * 0.095 - zax * 0.016      # palm flat under the board, fingers along it
    hand("Doc", "L", f0, palm, zax, ydir, pole=sh + lf * 0.25 + V((0, 0, -0.35)) - fw * 0.15, pose="flat_palm")
    child_of(cb, "Doc", "wrist.L", f0); M0 = ik_mat("Doc", "L", f0)
    CLIP[sid] = (cb, M0)
    return cb, M0
def doc_point(f, target, amt=1.0):
    sh = wpos("Doc", "upperarm01.R", f); d = (V(target) - sh).normalized()
    hand("Doc", "R", f, sh + d * 0.52 + V((0, 0, -0.02)), V((0, 0, -1)), d, pole=sh + rgt(YD) * 0.35 + V((0, 0, -0.3)) - fwd(YD) * 0.2, pose="point")
def doc_gesture(f, amt=1.0):
    """right hand forward at waist height, palm up: 'please continue'"""
    sh = wpos("Doc", "upperarm01.R", f)
    p = sh + fwd(YD) * 0.38 + rgt(YD) * 0.08 + V((0, 0, -0.24))
    hand("Doc", "R", f, p, V((0, 0, 1)), fwd(YD) + rgt(YD) * 0.3, pole=sh + rgt(YD) * 0.30 + V((0, 0, -0.35)) - fwd(YD) * 0.1, pose="relaxed")
def doc_shot(sid, f0, n, heads, point=None, talk_from=None, gesture=None):
    """Doc standing, clipboard in the left hand; right arm relaxed or pointing (point = [(u0, u1, target)])"""
    f1 = f0 + n - 1; ks = list(range(f0, f1, 30)) + [f1]
    for k, f in enumerate(ks):
        u = (f - f0) / max(1, n - 1)
        hd = interp_keys(heads, u); nod = 5.0 * math.sin(k * 1.9) if k % 3 == 1 else 0.0
        doc_body(f, head=(hd[0] + nod, hd[1]), spine=(3.0 + (1.0 if k % 2 else 0), 0.0, 2.5 * math.sin(k * 0.9)), dz=0.003 * (k % 2), shift=0.025 * math.sin(k * 0.9))
    cb = None      # P1 simplify (LESSONS 2.15): the clipboard grip crossed his fingers/forearm twice; he holds nothing
    for f in ks: relaxed_arm("Doc", "R", f, YD); relaxed_arm("Doc", "L", f, YD)
    if point:
        u0, u1, tgt = point
        fa, fb = f0 + int(u0 * n), min(f1, f0 + int(u1 * n))
        relaxed_arm("Doc", "R", max(f0, fa - 18), YD)
        for f in range(fa, fb + 1, 20): doc_point(f, tgt)
        doc_point(fb, tgt)
        if fb + 24 <= f1: relaxed_arm("Doc", "R", fb + 24, YD)
    if gesture:
        u0, u1 = gesture; fa, fb = f0 + int(u0 * n), min(f1, f0 + int(u1 * n))
        relaxed_arm("Doc", "R", max(f0, fa - 20), YD); doc_gesture(fa); doc_gesture((fa + fb) // 2); doc_gesture(fb)
        if fb + 22 <= f1: relaxed_arm("Doc", "R", fb + 22, YD)
    if talk_from is not None: talk("Doc", f0 + int(talk_from * n), f1)
    return cb

# ---- the stranger (Lab B, seated at his table, facing -Y; forearms on the table, cuff on the right wrist)
YB = 0.0
def str_body(f, lean=10.0, spine=(8.0, 0.0, 0.0), head=(4.0, 0.0), dz=0.0):
    if lean > 3.0: spine = (spine[0] + lean - 3.0, spine[1], spine[2]); lean = 3.0
    return sit("Stranger", f, SEAT_B + V((0, dz)), SEAT_BZ, YB, knee_fwd=0.54, lean=lean, spine=spine, head=head, heel=0.04)
RW = V((XB - 0.13, -0.15, TABLE_Z + 0.004))
def str_right_on_table(f, curl="relaxed", lift=0.0):
    """the cuffed right hand rests on the table: loosely curled, knuckles just above the top (flat palms grazed it)"""
    curl = "power_fist"      # the strapped hand rests as a loose fist: open/relaxed fingers grazed the table top
    lift = max(lift, 0.05 if curl == "power_fist" else 0.045)
    sh = wpos("Stranger", "upperarm01.R", f)
    hand("Stranger", "R", f, RW + V((0, 0, lift)), V((0, 0, -1)), V((0.15, -1, 0)), pole=sh + V((-0.35, 0.2, -0.3)), pose=curl)
def str_left_on_table(f):
    """free left hand rests on his left thigh (under the table edge)"""
    hp = wpos("Stranger", "upperleg01.L", f); kn = wpos("Stranger", "lowerleg01.L", f)
    p = hp.lerp(kn, 0.5) + V((0, 0, 0.085)); sh = wpos("Stranger", "upperarm01.L", f)
    hand("Stranger", "L", f, p, V((0, 0, -1)), (kn - hp).normalized() + V((0.3, 0, -0.2)), pole=sh + V((0.35, 0.20, -0.25)), pose="relaxed")
def cuff_on(sid, f0, f1):
    """electrode cuff round the right forearm just above the wrist, Child Of lowerarm02.R"""
    cu = prop_copy("Cuff", "Cuff_" + sid, f0, f1); el = prop_copy("CuffElectrode", "CuffEl_" + sid, f0, f1)
    sc.frame_set(f0); a_ = wpos("Stranger", "lowerarm02.R", f0); b_ = wpos("Stranger", "wrist.R", f0)
    ax = (b_ - a_).normalized(); c = b_ - ax * 0.045
    q = ax.to_track_quat('Z', 'Y'); cu.rotation_mode = 'QUATERNION'; cu.rotation_quaternion = q; cu.location = c
    bpy.context.view_layer.update()
    side = q.to_matrix() @ V((0, 1, 0))
    el.rotation_mode = 'QUATERNION'; el.rotation_quaternion = (side).to_track_quat('Z', 'Y'); el.location = c + side * 0.059
    for o in (cu, el): child_of(o, "Stranger", "lowerarm02.R", f0)
    return cu, el
def arcs(prefix, centre, f0, f1, every=3, frac=0.5, seed=1, rot=True):
    rnd = random.Random(seed)
    obs = [o for o in bpy.data.objects if o.name.startswith(prefix)]
    for o in obs:
        o.location = V(centre); o.keyframe_insert("location", frame=f0)
        key_vis(o, 1, False); key_vis(o, f0, False)
        for f in range(f0, f1 + 1, every):
            on = rnd.random() < frac; key_vis(o, f, on)
            if rot: o.rotation_euler = (0, 0, rnd.uniform(0, 6.28)); o.keyframe_insert("rotation_euler", frame=f)
        key_vis(o, f1 + 1, False)
        const_keys(o)

# ================================================================== SHOTS
def shot_01(f0, n):
    """the stranger at his table answers: raises his left index finger, head tilts; cuff on the right wrist"""
    f1 = f0 + n - 1
    for k, f in enumerate((f0, f0 + 30, f0 + 60, f1)):
        str_body(f, lean=8.0, spine=(6.0, -4.0 + 4 * k, 0), head=((6.0, -8.0), (2.0, -4.0), (0.0, 0.0), (2.0, 4.0))[k])
        str_right_on_table(f)
    str_left_on_table(f0)
    for f in (f0 + 28, f1):
        sh = wpos("Stranger", "upperarm01.L", f)
        hand("Stranger", "L", f, sh + V((0.06, -0.30, -0.12)), V((0.3, -1, 0)), V((0, -0.2, 1)), pole=sh + V((0.3, 0.1, -0.3)), pose="point")
    expr(f0, mouth_open=0.0); expr(f0 + 30, mouth_open=0.15, eyebrows_left_up=0.3, eyebrows_right_up=0.3); expr(f1, mouth_open=0.05, eyebrows_left_up=0.3, eyebrows_right_up=0.3)
    cuff_on("01", f0, f1)
    camera("01", f0, n, [(0, (XB + 1.25, -1.35, 1.30), (XB, 0.05, 1.05), 30), (1, (XB + 1.05, -1.15, 1.28), (XB, 0.1, 1.06), 30)])
    return ("Stranger",)

def shot_02(f0, n):
    """the red 'wrong answer' lamp on the wall lights up over the generator; the subject's head in the lower frame"""
    f1 = f0 + n - 1
    subj_seated(f0, n, [(0, (4.0, 0.0)), (0.4, (-6.0, 0.0)), (1, (-10.0, 0.0))], lean=8.0)
    wrong_lamp(f0, False); wrong_lamp(f0 + 18, True); wrong_lamp(f1 + 1, False)
    camera("02", f0, n, [(0, (0.45, 0.75, 1.45), (0.0, 2.36, 1.75), 36), (1, (0.35, 1.05, 1.5), (0.0, 2.36, 1.75), 36)])
    return ("Subject",)

def shot_03(f0, n):
    """first person: the subject's right hand comes in and presses the next switch"""
    fp_shot("03", f0, n, 2, [(0.45, 2)], mode="tight")
    return ("Subject",)

def shot_04(f0, n):
    """close on the stranger's strapped wrist: small arcs at the electrode, the hand clenches"""
    f1 = f0 + n - 1
    for k, f in enumerate((f0, f0 + 40, f0 + 80, f1)):
        str_body(f, lean=8.0 + 6 * (k % 2), spine=(8.0, 0.0, 0.0), head=(14.0, 0.0))
    str_right_on_table(f0); str_right_on_table(f0 + 20, "relaxed"); str_right_on_table(f0 + 30, "power_fist", lift=0.01); str_right_on_table(f1, "power_fist", lift=0.01)
    str_left_on_table(f0)
    cu, el = cuff_on("04", f0, f1)
    sc.frame_set(f0 + 20); c = el.matrix_world.translation.copy()
    arcs("ArcW", c, f0 + 22, f1, every=3, frac=0.55, seed=4)
    camera("04", f0, n, [(0, (XB - 0.62, -0.65, 1.02), (XB - 0.15, -0.12, 0.80), 38), (1, (XB - 0.55, -0.57, 0.98), (XB - 0.15, -0.12, 0.80), 38)], fstop=10.0)
    return ("Stranger",)

def shot_05(f0, n):
    """the man in the lab coat with his clipboard: looks down at it, then up at the subject"""
    doc_shot("05", f0, n, gesture=(0.55, 0.95), heads=[(0, (28.0, -10.0)), (0.5, (24.0, -10.0)), (0.75, (2.0, 18.0)), (1, (0.0, 20.0))])
    camera("05", f0, n, [(0, (-0.55, -1.75, 1.50), (1.0, -1.05, 1.42), 32), (1, (-0.35, -1.65, 1.52), (1.0, -1.05, 1.45), 32)])
    return ("Doc",)

def shot_06(f0, n):
    """3/4 behind the subject at the generator; the red lamp flashes above it"""
    f1 = f0 + n - 1
    panel_state(f0, 3)
    subj_seated(f0, n, [(0, (6.0, 0.0)), (0.5, (-8.0, 0.0)), (1, (-10.0, 0.0))], lean=8.0)
    wrong_lamp(f0, False); wrong_lamp(f0 + 14, True); wrong_lamp(f0 + 50, False); wrong_lamp(f0 + 62, True); wrong_lamp(f1 + 1, False)
    camera("06", f0, n, [(0, (-1.25, -1.55, 1.62), (0.1, 0.8, 1.3), 26), (1, (-1.15, -1.40, 1.60), (0.1, 0.85, 1.3), 26)])
    return ("Subject",)

def shot_07(f0, n):
    """first person: press, then the next one: the lamps climb along the panel"""
    fp_shot("07", f0, n, 6, [(0.25, 6), (0.65, 7)], mode="ots", brace=False)
    return ("Subject",)

def shot_08(f0, n):
    """the stranger screams: jolts back, left hand grips his strapped right forearm"""
    f1 = f0 + n - 1
    keys = ((f0, 8.0, (4.0, 0.0)), (f0 + 10, -4.0, (-14.0, 4.0)), (f0 + 40, -2.0, (-10.0, -6.0)), (f0 + 75, 2.0, (-6.0, 6.0)), (f1, 0.0, (-8.0, 0.0)))
    for f, ln, hd in keys:
        str_body(f, lean=ln, spine=(4.0, 0.0, 0.0), head=hd)
        str_right_on_table(f, "power_fist" if f > f0 else "relaxed", lift=0.01 if f > f0 else 0.0)
    str_left_on_table(f0)
    cu, el = cuff_on("08", f0, f1)
    for f in (f0 + 12, f1):    # left hand on the right forearm (one hand on the hurt place)
        sc.frame_set(f); a_ = wpos("Stranger", "lowerarm01.R", f); b_ = wpos("Stranger", "wrist.R", f)
        p = a_.lerp(b_, 0.40) + V((0, 0, 0.055))
        sh = wpos("Stranger", "upperarm01.L", f)
        hand("Stranger", "L", f, p, V((0, 0, -1)), V((-1, -0.25, -0.2)), pole=sh + V((0.35, 0.0, -0.3)), pose="wrap_grip", amount=0.7)
    expr(f0); expr(f0 + 8, mouth_open=0.75, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, eye_left_slit=0.5, eye_right_slit=0.5)
    expr(f1, mouth_open=0.6, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, eye_left_slit=0.4, eye_right_slit=0.4)
    jaw("Stranger", f0, 0); jaw("Stranger", f0 + 8, 8); jaw("Stranger", f1, 6)
    camera("08", f0, n, [(0, (XB + 0.85, -1.55, 1.40), (XB, 0.25, 1.15), 34), (1, (XB + 0.65, -1.25, 1.38), (XB, 0.25, 1.17), 34)])
    return ("Stranger",)

def shot_09(f0, n):
    """he begs to stop: leans toward us over the table, left palm up toward the camera"""
    f1 = f0 + n - 1
    for k, f in enumerate((f0, f0 + 40, f0 + 80, f1)):
        str_body(f, lean=(10.0, 22.0, 24.0, 22.0)[k], spine=((8.0, 14.0, 16.0, 14.0)[k], 0.0, 0.0), head=((-2.0, 0.0), (-16.0, 4.0), (-18.0, -4.0), (-16.0, 2.0))[k])
        str_right_on_table(f, "relaxed")
    str_left_on_table(f0)
    for f in (f0 + 34, f0 + 70, f1):
        sh = wpos("Stranger", "upperarm01.L", f)
        hand("Stranger", "L", f, sh + V((0.10, -0.34, -0.02)) + V((0, 0, 0.02 * ((f - f0) % 2))), V((0, 1, 0)), V((0, -0.15, 1)), pole=sh + V((0.35, 0.15, -0.3)), pose="flat_palm")
    cuff_on("09", f0, f1)
    expr(f0, mouth_open=0.3, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0)
    expr(f0 + 30, mouth_open=0.45, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, mouth_depression=0.4)
    expr(f1, mouth_open=0.35, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, mouth_depression=0.4)
    talk("Stranger", f0 + 10, f1, every=10, amp=4.0)
    camera("09", f0, n, [(0, (XB - 0.15, -1.85, 1.30), (XB, 0.1, 1.12), 34), (1, (XB - 0.10, -1.55, 1.30), (XB, 0.1, 1.14), 34)])
    return ("Stranger",)

def shot_10(f0, n):
    """but the man in the lab coat points at the generator and tells him to keep going"""
    doc_shot("10", f0, n, [(0, (4.0, 20.0)), (0.3, (6.0, 25.0)), (1, (4.0, 22.0))], point=(0.15, 1.0, V((0.0, -0.1, 0.95))), talk_from=0.2)
    camera("10", f0, n, [(0, (-0.40, -1.95, 1.40), (1.0, -1.0, 1.40), 30), (1, (-0.20, -1.80, 1.42), (1.0, -1.0, 1.42), 30)])
    return ("Doc",)

def shot_11(f0, n):
    """the subject looks back at the doctor, then turns to the panel again (face 3/4 front)"""
    subj_seated(f0, n, [(0, (0.0, -45.0)), (0.35, (2.0, -45.0)), (0.8, (14.0, 0.0)), (1, (16.0, 0.0))], lean=10.0, spine_tw=[(0, -12.0), (0.4, -12.0), (0.8, 0.0), (1, 0.0)])
    panel_state(f0, 8)
    face_cam("11", f0, n, "Subject", YS, -45.0, 1.0, 0.02, 40)
    return ("Subject",)

def shot_12(f0, n):
    """first person: so you do: the next switch goes down"""
    fp_shot("12", f0, n, 12, [(0.4, 12)], mode="tight")
    return ("Subject",)

def collapse(sid, f0, n, phase):
    """the stranger on the floor beside his chair: on hands and knees (phase 0), then sinking down (phase 1); arcs round him"""
    f1 = f0 + n - 1; K = V((XB + 0.95, -0.85)); yw = -20.0
    if phase == 0:
        keys = ((f0, 18.0, 12.0, (18.0, 0, 0), (2.0, 0.0)), (f0 + 50, 22.0, 18.0, (24.0, 0, 4), (-4.0, 10.0)), (f0 + 100, 20.0, 15.0, (22.0, 0, -4), (0.0, -8.0)), (f1, 26.0, 20.0, (26.0, 0, 0), (-2.0, 6.0)))
    else:
        keys = ((f0, 26.0, 20.0, (26.0, 0, 0), (-2.0, 6.0)), (f0 + 60, 45.0, 30.0, (32.0, 0, 8), (-6.0, 14.0)), (f1, 55.0, 34.0, (34.0, 0, 10), (-8.0, 18.0)))
    for k, (f, tb, ln, sp, hd) in enumerate(keys):
        kneel("Stranger", f, K, yw, thigh_back=tb, lean=ln, spine=sp, head=hd)
        for s in "LR":
            sx = 1 if s == "L" else -1
            sh = wpos("Stranger", "upperarm01." + s, f)
            if phase == 1 and s == "L" and k > 0:      # left palm goes to the floor beside the knee to hold him up
                p = V((K.x, K.y, 0.0)) - rgt(yw) * 0.30 + fwd(yw) * 0.12 + V((0, 0, 0.012))
                hand("Stranger", s, f, p, V((0, 0, -1)), fwd(yw) - rgt(yw) * 0.3, pole=sh - rgt(yw) * 0.35 + V((0, 0, 0.1)) - fwd(yw) * 0.25, pose="flat_palm")
            else:                                         # palm on the front of the thigh, near the knee
                hp = wpos("Stranger", "upperleg01." + s, f); kn = wpos("Stranger", "lowerleg01." + s, f)
                th = hp.lerp(kn, 0.72) + fwd(yw) * (0.085 if s == "L" else 0.15) + V((0, 0, 0.05 if s == "L" else 0.09))
                hand("Stranger", s, f, th, -fwd(yw), V((0, 0, -1)) + fwd(yw) * 0.3, pole=sh - rgt(yw) * sx * 0.30 - fwd(yw) * 0.15 + V((0, 0, -0.25)), pose="relaxed")
    expr(f0, mouth_open=0.55, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, eye_left_slit=0.6, eye_right_slit=0.6)
    expr(f1, mouth_open=0.45 if phase == 0 else 0.3, eyebrows_left_inner_up=1.0, eyebrows_right_inner_up=1.0, eye_left_slit=0.7, eye_right_slit=0.7)
    cuff_on(sid, f0, f1)
    sc.frame_set(f0); c = wpos("Stranger", "spine03", f0)
    arcs("ArcB", c, f0, f1 if phase == 0 else f0 + n // 2, every=3, frac=0.45, seed=7 + phase)
    return ("Stranger",)

def shot_13a(f0, n):
    use = collapse("13a", f0, n, 0)
    camera("13a", f0, n, [(0, (XB + 0.35, -2.45, 0.85), (XB + 0.95, -0.85, 0.65), 28), (1, (XB + 0.45, -2.25, 0.82), (XB + 0.95, -0.85, 0.62), 28)])
    return use
def shot_13b(f0, n):
    use = collapse("13b", f0, n, 1)
    camera("13b", f0, n, [(0, (XB + 1.55, -2.35, 0.70), (XB + 0.85, -0.85, 0.50), 30), (1, (XB + 1.45, -2.15, 0.62), (XB + 0.85, -0.85, 0.45), 30)])
    return use

def shot_14(f0, n):
    """side view of the subject at the panel, listening: head lifts and tilts, a breath"""
    subj_seated(f0, n, [(0, (10.0, 0.0)), (0.5, (2.0, -12.0)), (1, (4.0, -16.0))], lean=12.0)
    panel_state(f0, 13)
    camera("14", f0, n, [(0, (-1.75, -0.35, 1.35), (0.0, -0.35, 1.08), 30), (1, (-1.55, -0.55, 1.33), (0.0, -0.35, 1.08), 30)])
    return ("Subject",)

def shot_15(f0, n):
    """the man in the lab coat, closer: he talks, looks at the subject, then down at his clipboard"""
    doc_shot("15", f0, n, [(0, (2.0, 18.0)), (0.6, (4.0, 22.0)), (0.85, (24.0, -6.0)), (1, (26.0, -8.0))], talk_from=0.0)
    camera("15", f0, n, [(0, (-0.10, -1.55, 1.58), (1.0, -1.05, 1.55), 36), (1, (0.05, -1.45, 1.58), (1.0, -1.05, 1.57), 36)])
    return ("Doc",)

def shot_16(f0, n):
    """what you don't know: we follow the generator's cable along the floor toward the wall"""
    camera("16", f0, n, [(0, (0.80, 0.75, 0.62), (1.0, 1.25, 0.05), 26), (1, (1.15, 1.25, 0.42), (1.55, 1.95, 0.02), 26)])
    return ()

def shot_17(f0, n):
    """the plug lies on the carpet, next to the wall socket: never plugged in"""
    camera("17", f0, n, [(0, (1.25, 1.55, 0.42), (1.62, 2.12, 0.08), 32), (1, (1.38, 1.72, 0.32), (1.63, 2.14, 0.08), 32)], fstop=10.0)
    return ()

def shot_18(f0, n):
    """the stranger is an actor: he sits back, smiles and gives a small wave"""
    f1 = f0 + n - 1
    for k, f in enumerate((f0, f0 + 40, f0 + 90, f1)):
        str_body(f, lean=(10.0, 0.0, -2.0, -1.0)[k], spine=(4.0, 0.0, 0.0), head=((-4.0, 0.0), (0.0, 8.0), (2.0, 10.0), (0.0, 6.0))[k])
        str_right_on_table(f)
    str_left_on_table(f0)
    for k, f in enumerate((f0 + 40, f0 + 60, f0 + 80, f0 + 100, f1)):
        sh = wpos("Stranger", "upperarm01.L", f)
        hand("Stranger", "L", f, sh + V((0.16 + 0.03 * (k % 2), -0.22, 0.02)), V((0, 1, 0)), V((0.12 * (1 if k % 2 else -1), -0.1, 1)), pole=sh + V((0.35, 0.15, -0.3)), pose="flat_palm")
    cuff_on("18", f0, f1)
    expr(f0, mouth_open=0.1); expr(f0 + 30, mouth_corner_puller=0.9, mouth_open=0.12, eyebrows_left_up=0.3, eyebrows_right_up=0.3)
    expr(f1, mouth_corner_puller=1.0, mouth_open=0.1, eyebrows_left_up=0.3, eyebrows_right_up=0.3)
    camera("18", f0, n, [(0, (XB - 0.45, -1.70, 1.30), (XB, 0.25, 1.15), 34), (1, (XB - 0.35, -1.45, 1.30), (XB, 0.25, 1.17), 34)])
    return ("Stranger",)

def shot_19(f0, n):
    """the subject, surprised: head jerks back, mouth opens"""
    f1 = f0 + n - 1
    subj_seated(f0, n, [(0, (10.0, -5.0)), (0.2, (-6.0, -8.0)), (1, (-8.0, -10.0))], lean=6.0)
    jaw("Subject", f0, 0); jaw("Subject", f0 + 14, 9); jaw("Subject", f1, 8)
    panel_state(f0, 15)
    face_cam("19", f0, n, "Subject", YS, 45.0, 1.0, 0.02, 40)
    return ("Subject",)

def shot_20(f0, n):
    """the clipboard on the table: the subject's own photo on the sheet (he is the real test subject)"""
    cb = bpy.data.objects["Clipboard_Table"]; c = cb.matrix_world.translation
    camera("20", f0, n, [(0, (c.x - 0.10, c.y - 0.42, c.z + 0.40), (c.x, c.y, c.z), 34), (1, (c.x - 0.06, c.y - 0.28, c.z + 0.30), (c.x, c.y, c.z), 34)], fstop=10.0, catch=False)
    return ()

def shot_21(f0, n):
    """the subject close: uneasy, eyes down to the panel, a glance toward the doctor, a swallow"""
    subj_seated(f0, n, [(0, (10.0, 0.0)), (0.4, (6.0, -30.0)), (0.7, (8.0, -10.0)), (1, (12.0, 0.0))], lean=10.0)
    panel_state(f0, 16)
    face_cam("21", f0, n, "Subject", YS, 45.0, 1.0, 0.02, 42)
    return ("Subject",)

def shot_22(f0, n):
    """you keep going: the subject at the panel, the doctor standing behind him"""
    f1 = f0 + n - 1
    panel_state(f0, 18)
    subj_seated(f0, n, [(0, (14.0, 0.0)), (1, (20.0, 0.0))], lean=14.0)
    doc_shot("22", f0, n, [(0, (8.0, 30.0)), (1, (10.0, 32.0))])
    camera("22", f0, n, [(0, (-1.25, 0.35, 1.55), (0.45, -0.9, 1.30), 26), (1, (-1.15, 0.25, 1.53), (0.45, -0.9, 1.30), 26)])
    return ("Subject", "Doc")

def shot_23(f0, n):
    """first person: the finger moves on into the red danger switches"""
    fp_shot("23", f0, n, 24, [(0.35, 24), (0.7, 25)])
    return ("Subject",)

def shot_24(f0, n):
    """an authority figure: the doctor from below, straightening up"""
    doc_shot("24", f0, n, [(0, (10.0, 10.0)), (0.5, (14.0, 0.0)), (1, (16.0, -4.0))], talk_from=0.5, gesture=(0.25, 0.85))
    camera("24", f0, n, [(0, (-0.15, -1.25, 0.95), (1.0, -1.05, 1.52), 26), (1, (-0.05, -1.22, 0.92), (1.0, -1.05, 1.54), 26)])
    return ("Doc",)

def shot_25(f0, n):
    """first person: the last switch goes down"""
    fp_shot("25", f0, n, 29, [(0.4, 29)], mode="tight")
    return ("Subject",)

def shot_26(f0, n):
    """wide of the lab: the subject at the generator, the doctor beside him; our poster on the back wall"""
    panel_state(f0, 30)
    subj_seated(f0, n, [(0, (16.0, 0.0)), (1, (18.0, -10.0))], lean=12.0)
    doc_shot("26", f0, n, [(0, (10.0, 30.0)), (1, (8.0, 28.0))])
    camera("26", f0, n, [(0, (-0.95, -3.15, 1.75), (0.62, 0.9, 1.15), 22), (1, (-0.85, -2.85, 1.72), (0.62, 0.9, 1.15), 22)], fstop=10.0)
    return ("Subject", "Doc")

def shot_27(f0, n):
    """the sixties: a living room, the subject's picture on the television; slow push in past the armchair"""
    camera("27", f0, n, [(0, (XH - 0.75, -1.35, 1.25), (XH, 1.6, 0.85), 30), (1, (XH - 0.45, -0.55, 1.10), (XH, 1.6, 0.85), 30)], catch=False)
    return ()

def shot_28(f0, n):
    """the subject: how far ordinary people will go: he looks down at his finger on the switch, breathes"""
    subj_seated(f0, n, [(0, (2.0, -6.0)), (0.5, (8.0, 0.0)), (1, (12.0, 2.0))], lean=10.0)
    panel_state(f0, 30)
    face_cam("28", f0, n, "Subject", YS, -45.0, 1.0, 0.02, 40)
    return ("Subject",)

def shot_29(f0, n):
    """following orders: the doctor points at the subject, talks; slow push in"""
    doc_shot("29", f0, n, [(0, (6.0, 18.0)), (1, (4.0, 14.0))], point=(0.1, 1.0, V((0.05, -0.55, 1.20))), talk_from=0.15)
    camera("29", f0, n, [(0, (0.05, -1.75, 1.45), (1.0, -1.02, 1.45), 30), (1, (0.25, -1.62, 1.47), (1.0, -1.02, 1.47), 30)])
    return ("Doc",)

def _flat(nm, rgb, r):
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm); m.use_nodes = True; P_ = m.node_tree.nodes["Principled BSDF"]
    P_.inputs['Base Color'].default_value = (*rgb, 1); P_.inputs['Roughness'].default_value = r; return m
_flat("M_Paper", (0.93, 0.93, 0.90), 0.8); _flat("M_InkLine", (0.55, 0.56, 0.6), 0.8)
cbt = bpy.data.objects["Clipboard_Table"]
bpy.ops.mesh.primitive_plane_add(size=1.0); pap = bpy.context.active_object; pap.name = "Clipboard_Paper"
pap.scale = (0.205, 0.28, 1); bpy.ops.object.transform_apply(scale=True); pap.data.materials.append(bpy.data.materials["M_Paper"])
for c_ in list(pap.users_collection): c_.objects.unlink(pap)
cbt.users_collection[0].objects.link(pap); pap.parent = cbt; pap.location = (0.0, -0.01, 0.0075)
for k_ in range(4):     # grey lines (no text) under the photo
    bpy.ops.mesh.primitive_plane_add(size=1.0); ln = bpy.context.active_object; ln.name = "Clipboard_Line%d" % k_
    ln.scale = (0.15 - 0.03 * (k_ % 2), 0.006, 1); bpy.ops.object.transform_apply(scale=True); ln.data.materials.append(bpy.data.materials["M_InkLine"])
    for c_ in list(ln.users_collection): c_.objects.unlink(ln)
    cbt.users_collection[0].objects.link(ln); ln.parent = cbt; ln.location = (0.0, -0.105 - 0.022 * k_, 0.0080)
# ---- portrait image for the TV and the clipboard photo (rendered once from shot 21's camera; see PLAN)
PORT = os.path.join(HERE, "..", "assets_gen", "portrait.png")
if os.path.exists(PORT):
    img = bpy.data.images.load(PORT)
    def img_mat(name, emit, bw=0.0):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; P = nt.nodes["Principled BSDF"]
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
        hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Saturation'].default_value = 1.0 - bw
        nt.links.new(t.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs[0], P.inputs['Base Color'])
        if emit:
            nt.links.new(hs.outputs[0], P.inputs['Emission Color']); P.inputs['Emission Strength'].default_value = emit
        P.inputs['Roughness'].default_value = 0.4; return m
    scr = bpy.data.objects["Home_TVScreen"]; scr.data.materials[0] = img_mat("M_TVPortrait", 1.2, bw=0.9)
    for cbn in ("Clipboard_Table",):
        cb = bpy.data.objects[cbn]
        bpy.ops.mesh.primitive_plane_add(size=1.0); ph = bpy.context.active_object; ph.name = cbn + "_Photo"
        ph.scale = (0.10, 0.125, 1); bpy.ops.object.transform_apply(scale=True); ph.data.materials.append(img_mat("M_Photo_" + cbn, 0.0, bw=0.85))
        for c_ in list(ph.users_collection): c_.objects.unlink(ph)
        cb.users_collection[0].objects.link(ph)
        ph.parent = cb; ph.location = (0.0, 0.03, 0.0082); ph.rotation_euler = (0, 0, 0)

SHOT_FUNCS = {k[5:]: v for k, v in list(globals().items()) if k.startswith("shot_")}

def all_fcurves(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    out = []
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out
def hold_ends(f0, f1):
    """key every channel that moves inside [f0, f1] at f0 and f1 (evaluated now, before the next shot exists), so no shot's
    edge frame interpolates toward the next shot's pose"""
    ids = list(bpy.data.objects) + list(bpy.data.lights) + list(bpy.data.cameras)
    for idb in ids:
        for fc in all_fcurves(idb):
            ks = [kp.co.x for kp in fc.keyframe_points]
            if not any(f0 <= k <= f1 for k in ks): continue
            for f in (f0, f1):
                if not any(abs(k - f) < 0.01 for k in ks):
                    fc.keyframe_points.insert(f, fc.evaluate(f), options={'FAST'})
            fc.update()

# ================================================================== build
shots = json.load(open(SHOTS))
sc.frame_start = 1; sc.frame_end = max(s_["f0"] + s_["len"] - 1 for s_ in shots)
used = {}
for s_ in shots:
    if s_["id"] not in SHOT_FUNCS or (ONLY and s_["id"] not in ONLY): continue
    print("SHOT", s_["id"], s_["f0"], s_["len"])
    for n_ in CH: jaw(n_, s_["f0"], 0.0)          # faces start neutral every shot (no expression leaks across a cut)
    expr(s_["f0"])
    used[s_["id"]] = SHOT_FUNCS[s_["id"]](s_["f0"], s_["len"])
    hold_ends(s_["f0"], s_["f0"] + s_["len"] - 1)
for s_ in shots:
    if s_["id"] not in used: continue
    for n in CH: place_rig(n, s_["f0"], s_["f0"] + s_["len"] - 1, n in used[s_["id"]])
for o in bpy.data.objects:      # object-level parking keys must not interpolate between shots
    ad = o.animation_data
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path in ("location", "hide_render", "hide_viewport") and o.type == 'ARMATURE':
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
                        if fc.data_path in ("hide_render", "hide_viewport"):
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", list(used))
