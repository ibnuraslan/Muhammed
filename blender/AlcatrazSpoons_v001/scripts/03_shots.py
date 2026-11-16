"""AlcatrazSpoons: every shot as its own clip (character keys, props, camera + marker).
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
VX, VZ, BX = sc["VX"], sc["VZ"], sc["BX"]
X2, X3, X4, X5 = 30.0, 60.0, 90.0, 300.0
GZ = [0.0]
def ground_z(x, y): return GZ[0]          # overrides anim_lib: flat floors everywhere (raft/ladder poses key feet directly)

CH = ("P1", "P2", "P3", "Guard")
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

def foot(n, s, f, ankle, yaw, pitch=0.0, roll=0.0, knee=None):
    """ankle: world point for the ankle joint; pitch>0 lifts the toes; knee: world point the knee aims at"""
    H = HUM[n]; a_ = H.ankle[s]; Rw = Rz(yaw) @ Rx(pitch) @ Ry(roll)
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
    root = k + V((0, 0, GZ[0] + 0.075 + L * math.cos(t))) - fwd(yaw) * (L * math.sin(t)) + V((0, 0, HUM[n].root_head.z - RIG[n].BN["upperleg01.L"].head_local.z))
    body(n, f, root, yaw, flex=lean, spine=spine, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        kn = k - rgt(yaw) * sx * spread
        ank = kn - fwd(yaw) * (SHIN[n] * 0.93) + V((0, 0, GZ[0] + 0.15))
        foot(n, s, f, ank, yaw + sx * 5, pitch=toes, knee=kn + fwd(yaw) * 0.6 + V((0, 0, -0.1)))
    return root

def orient(o, loc, ydir, zhint=V((0, 0, 1))):
    y = V(ydir).normalized(); x = y.cross(V(zhint)).normalized(); z = x.cross(y)
    o.matrix_world = Matrix.Translation(V(loc)) @ Matrix((x, y, z)).transposed().to_4x4()

def spoon_at(sp, tip, ydir, zhint=V((0, 0, 1))):
    """place a spoon so its bowl tip (local y=0.197) is at `tip`, pointing along ydir"""
    y = V(ydir).normalized(); orient(sp, V(tip) - y * 0.197, y, zhint)

def scrape(n, s, f0, f1, sp, M0, piv, period=28, amp=0.028, axis=V((0, 0, 1))):
    """the hand (and the spoon pinned in it) scrapes back and forth along `axis` at 1x"""
    f = f0; k = 0
    while f <= f1:
        d = amp * (1 if k % 2 else -1) * (0.8 + 0.2 * math.sin(k * 1.7))
        key_ik(n, s, f, rigid(piv, Rx(4 * (1 if k % 2 else -1)), axis * d) @ M0)
        f += period // 2; k += 1

def p_kneel_scrape(n, sid, f0, n_fr, knees, yaw, tip, ydir, side="R", head=(24.0, 0.0), lean=18.0, spine=(20.0, 0.0, 0.0), support=None, axis=V((0, 0, 1)), period=28):
    """kneel at the vent and scrape the concrete round it with a spoon (spoon pinched in `side` hand, Child Of the wrist)"""
    f1 = f0 + n_fr - 1
    for k, f in enumerate(range(f0, f1 + 1, 40)):
        kneel(n, f, knees, yaw, lean=lean + (1.5 if k % 2 else 0), spine=(spine[0] + (2 if k % 2 else 0), spine[1], spine[2]), head=(head[0] + (2 if k % 2 else -1), head[1] + 2 * math.sin(k)))
    kneel(n, f1, knees, yaw, lean=lean, spine=spine, head=head)
    sp = prop_copy("Spoon_" + n, "Spoon_%s_%s" % (sid, n), f0, f1)
    spoon_at(sp, tip, ydir)
    sh = wpos(n, "upperarm01." + side, f0)
    out = rgt(yaw) * (1 if side == "R" else -1)
    elbow(n, side, f0, sh + out * 0.35 + V((0, 0, -0.15)) - fwd(yaw) * 0.2)
    Mw = sp.matrix_world
    M0 = hold_prop(n, side, f0, sp, Mw @ V((0, 0.03, 0.006)), Mw.to_3x3() @ V((0, 0, -1)), Mw.to_3x3() @ V((0, 1, 0)), "pinch")
    scrape(n, side, f0 + 6, f1, sp, M0, V(tip), period=period, axis=axis)
    for f in range(f0, f1 + 1, 40):
        sh = wpos(n, "upperarm01." + side, f); elbow(n, side, f, sh + out * 0.35 + V((0, 0, -0.15)) - fwd(yaw) * 0.2)
    o2 = "L" if side == "R" else "R"
    for f in (f0, f1):
        if support:     # the other palm flat on the wall beside the vent
            hand(n, o2, f, support, fwd(yaw) * -1 if False else V((0, 1, 0)) if abs(yaw) > 90 else V((0, -1, 0)), V((0, 0, 1)),
                 pole=wpos(n, "upperarm01." + o2, f) - out * 0.4 + V((0, 0, -0.2)), pose="flat_palm")
        else:
            kn = V((knees[0], knees[1], 0.0)) + fwd(yaw) * 0.05 - out * 0.13 + V((0, 0, 0.32))
            hand(n, o2, f, kn, V((0, 0, -1)), fwd(yaw), pole=wpos(n, "upperarm01." + o2, f) - out * 0.4 - fwd(yaw) * 0.2, pose="relaxed")
    return sp

def stand_idle(n, f0, f1, pos, yaw, head=(0.0, 0.0), spine=(3.0, 0.0, 0.0), every=40, arms=True, head_fn=None):
    k = 0
    for f in list(range(f0, f1, every)) + [f1]:
        hd = head_fn(f) if head_fn else (head[0] + (1.5 if k % 2 else 0), head[1] + 2 * math.sin(k))
        body(n, f, V(pos) + V((0, 0, HUM[n].root_head.z - 0.01 + (0.004 if k % 2 else 0))), yaw, spine=(spine[0] + (1.5 if k % 2 else 0), spine[1], spine[2]), head=hd)
        stand_feet(n, f, pos, yaw)
        if arms: relaxed_arm(n, "L", f, yaw); relaxed_arm(n, "R", f, yaw)
        k += 1

def hole_grow(f, scale, rub):
    c = bpy.data.objects["S1_HoleCutter"]; c.scale = (scale, scale, 1.0); c.keyframe_insert("scale", frame=f)
    r = bpy.data.objects["S1_Rubble"]; r.scale = (rub, rub, rub); r.keyframe_insert("scale", frame=f)

# ================================================================== BEAT 1
def shot_1a(f0, n):
    """CU: P1 sits on the stool, lifts a spoon to chest height and studies it; P2 and P3 lean in over his shoulders"""
    use = ("P1", "P2", "P3")
    st = V((0.15, 0.5, 0)); y1 = 0.0
    for k, f in enumerate((f0, f0 + 50, f0 + 100, f0 + n - 1)):
        sit("P1", f, st, 0.453, y1, spine=(10 + 3 * (k % 2), 0, 0), head=(14 if k == 0 else 24, -3 + 3 * k))
        knee = st + fwd(y1) * 0.40 + V((0, 0, 0.58))        # left hand rests on the left knee (never in the lap)
        hand("P1", "L", f, knee - rgt(y1) * 0.15, V((0, 0, -1)), fwd(y1) - rgt(y1) * 0.3, pole=knee - rgt(y1) * 0.45 + V((0, 0.35, 0.2)), pose="relaxed")
    for nm, pos, yw, hd in (("P2", V((-0.02, 0.92, 0)), -14.0, (14, -12)), ("P3", V((0.42, 0.9, 0)), 16.0, (14, 10))):
        for k, f in enumerate((f0, f0 + 60, f0 + 120, f0 + n - 1)):
            body(nm, f, pos + V((0, 0, HUM[nm].root_head.z - 0.015)), yw, flex=4, spine=(12 + 3 * (k % 2), 0, 0), head=(hd[0] + 3 * (k % 2), hd[1] + 3 * math.sin(k)))
            stand_feet(nm, f, pos, yw)
            relaxed_arm(nm, "L", f, yw); relaxed_arm(nm, "R", f, yw)
    # P1's right hand: the spoon is gripped low (pinch, Child Of the wrist), then the HAND is keyed up to chest height
    sp = prop_copy("Spoon_P1", "Spoon_1a", f0, f0 + n - 1)
    sp.location = V((st.x - 0.1, st.y - 0.36, 0.82)); sp.rotation_euler = (R_(-15), 0, R_(200))
    sh = wpos("P1", "upperarm01.R", f0); elbow("P1", "R", f0, sh + V((-0.3, 0.3, -0.3)))
    Mw = sp.matrix_world
    sc.frame_set(f0); bpy.context.view_layer.update()
    sp.rotation_euler = (0, 0, R_(160)); bpy.context.view_layer.update(); Mw = sp.matrix_world     # lying flat
    hand("P1", "R", f0, Mw @ V((0, 0.035, -0.014)), V((0, 0, 1)), Mw.to_3x3() @ V((0, 1, 0)), pose="flat_palm")
    M0 = ik_mat("P1", "R", f0); child_of(sp, "P1", "wrist.R", f0)
    piv = V(sp.location)
    for f, up, fw, tilt in ((f0 + 45, 0.2, -0.04, 25), (f0 + 100, 0.23, -0.05, 35), (f0 + n - 1, 0.22, -0.04, 28)):
        key_ik("P1", "R", f, rigid(piv, Rz(tilt * 0.4), (0.05, fw, up)) @ M0)
        sh = wpos("P1", "upperarm01.R", f); elbow("P1", "R", f, sh + V((-0.3, 0.3, -0.3)))
    camera("1a", f0, n, [(0, (0.16, -1.05, 1.38), (0.16, 0.55, 1.24), 28), (1, (0.16, -0.85, 1.37), (0.16, 0.55, 1.25), 28)])
    return use


def shot_1b(f0, n):
    """same trio, wider: P1 turns on the stool to look at the vent behind; P2 nods toward it"""
    use = ("P1", "P2", "P3"); st = V((0.15, 0.5, 0)); f1 = f0 + n - 1
    keys = ((f0, 0, (18, -4)), (f0 + 50, 10, (8, 30)), (f0 + 110, 25, (2, 70)), (f0 + 160, 22, (6, 65)), (f1, 18, (10, 40)))
    for f, tw, hd in keys:
        sit("P1", f, st, 0.453, 0.0, spine=(6, tw, 0), head=hd)
        knee = st + fwd(0.0) * 0.40 + V((0, 0, 0.58))
        hand("P1", "L", f, knee - rgt(0.0) * 0.15, V((0, 0, -1)), fwd(0.0) - rgt(0.0) * 0.3, pole=knee - rgt(0.0) * 0.45 + V((0, 0.35, 0.2)), pose="relaxed")
        kr = st + fwd(0.0) * 0.40 + V((0, 0, 0.58)) + rgt(0.0) * 0.15
        hand("P1", "R", f, kr, V((0, 0, -1)), fwd(0.0) + rgt(0.0) * 0.3, pole=kr + rgt(0.0) * 0.3 + V((0, 0.35, 0.2)), pose="relaxed")
    stand_idle("P2", f0, f1, V((-0.1, 0.9, 0)), -14.0, head_fn=lambda f: (10 + 10 * math.sin((f - f0) / 18.0) ** 2 if 60 < f - f0 < 130 else 8, 40 if f - f0 > 50 else -10))
    stand_idle("P3", f0, f1, V((0.45, 0.92, 0)), 16.0, head_fn=lambda f: (6, -40 if f - f0 > 70 else 8))
    camera("1b", f0, n, [(0, (-0.55, -1.15, 1.25), (0.18, 0.95, 0.85), 24), (1, (-0.15, -1.25, 1.3), (0.2, 0.95, 0.85), 24)])
    return use

def shot_1c(f0, n):
    """wide of the cell at night: P1 kneels scraping at the vent, P2 kneels beside him watching, P3 keeps watch at the bars"""
    use = ("P1", "P2", "P3"); f1 = f0 + n - 1
    p_kneel_scrape("P1", "1c", f0, n, (0.0, 1.0), 180.0, (VX - 0.15, 1.59, VZ + 0.02), V((0.25, 1, -0.35)), support=None)
    for k, f in enumerate(range(f0, f1 + 1, 45)):
        kneel("P2", f, (0.7, 0.85), 150.0, lean=10, spine=(12, -10, 0), head=(20, 25 + 4 * math.sin(k)))
        for s_ in "LR":
            kn = V((0.7, 0.85, 0.0)) + fwd(150.0) * 0.05 - rgt(150.0) * (0.13 if s_ == "L" else -0.13) + V((0, 0, 0.32))
            hand("P2", s_, f, kn, -fwd(150.0) + V((0, 0, -0.6)), V((0, 0, -1)), pole=wpos("P2", "upperarm01." + s_, f) - rgt(150.0) * (0.4 if s_ == "L" else -0.4) - fwd(150.0) * 0.2, pose="relaxed")
    stand_idle("P3", f0, f1, V((-0.02, -0.45, 0)), 20.0, head_fn=lambda f: (0, 50 * math.sin((f - f0) / 40.0)))
    camera("1c", f0, n, [(0, (0.98, -1.4, 1.95), (-0.15, 0.45, 0.7), 16), (1, (0.9, -1.25, 1.88), (-0.1, 0.55, 0.65), 16)], fstop=6.0)
    return use

# ================================================================== BEAT 2: digging
def shot_2a(f0, n):
    """low wide: P1 and P2 kneel at the vent, both scraping, rubble round their knees"""
    use = ("P1", "P2"); f1 = f0 + n - 1
    p_kneel_scrape("P1", "2a", f0, n, (-0.12, 1.0), 165.0, (VX - 0.15, 1.59, VZ), V((0.3, 1, -0.3)), support=None)
    for k, f in enumerate(range(f0, f0 + n, 40)):     # P2 kneels 75 cm to his right and watches the edge (hands on his thighs)
        kneel("P2", f, (0.55, 0.8), 200.0, lean=8, spine=(10, 0, 0), head=(28, -20 + 4 * math.sin(k)))
        for s_ in "LR":
            kn = V((0.55, 0.8, 0.0)) + fwd(200.0) * 0.05 - rgt(200.0) * (0.13 if s_ == "L" else -0.13) + V((0, 0, 0.32))
            hand("P2", s_, f, kn, -fwd(200.0) + V((0, 0, -0.6)), V((0, 0, -1)), pole=wpos("P2", "upperarm01." + s_, f) - rgt(200.0) * (0.4 if s_ == "L" else -0.4) - fwd(200.0) * 0.2, pose="relaxed")
    hole_grow(f0, 0.80, 0.55)
    camera("2a", f0, n, [(0, (-0.95, 1.42, 0.85), (0.25, 0.95, 0.62), 18), (1, (-0.95, 1.35, 0.8), (0.25, 0.95, 0.6), 18)], fstop=6.0)
    return use

def shot_2b(f0, n):
    """3/4 side of P1 kneeling and scraping the vent edge; crumbs fall"""
    use = ("P1",)
    p_kneel_scrape("P1", "2b", f0, n, (-0.12, 1.0), 165.0, (VX - 0.15, 1.59, VZ), V((0.3, 1, -0.3)), support=None)
    hole_grow(f0, 0.84, 0.65)
    camera("2b", f0, n, [(0, (0.98, 0.82, 0.72), (-0.2, 1.22, 0.7), 26), (1, (0.95, 0.9, 0.7), (-0.2, 1.25, 0.68), 26)])
    return use

def shot_2c(f0, n):
    """over the shoulder: P1's arm (to his visible shoulder) scrapes the corner of the grille"""
    use = ("P1",)
    p_kneel_scrape("P1", "2c", f0, n, (-0.12, 1.0), 165.0, (VX - 0.15, 1.59, VZ), V((0.3, 1, -0.3)), support=None)
    hole_grow(f0, 0.88, 0.75)
    camera("2c", f0, n, [(0, (0.55, 1.42, 0.36), (-0.08, 1.2, 0.72), 22), (1, (0.52, 1.44, 0.38), (-0.08, 1.2, 0.74), 22)])
    return use

def shot_2d(f0, n):
    """close on the grille corner: the spoon tip scrapes, the gap widens and crumbs build up"""
    use = ("P1",)
    p_kneel_scrape("P1", "2d", f0, n, (-0.12, 1.0), 165.0, (VX - 0.15, 1.59, VZ), V((0.3, 1, -0.3)), support=None)
    hole_grow(f0, 0.9, 0.8); hole_grow(f0 + n - 1, 1.0, 1.0)
    camera("2d", f0, n, [(0, (0.5, 0.85, 0.55), (0.05, 1.6, 0.44), 36), (1, (0.45, 0.92, 0.53), (0.05, 1.6, 0.44), 36)], fstop=11.0)
    return use

# ================================================================== BEAT 3: the drill
def drill_copy(sid, f0, f1, spin=False):
    d = prop_copy("Drill", "Drill_" + sid, f0, f1)
    kids = []
    for c_ in bpy.data.objects["Drill"].children:
        k = c_.copy(); k.name = c_.name + "_" + sid; c_.users_collection[0].objects.link(k); k.parent = d; k.animation_data_clear(); vis_window(k, f0, f1); kids.append(k)
    fan = next(k for k in kids if k.name.startswith("Drill_Fan"))
    if spin:
        for i, f in enumerate(range(f0, f1 + 1, 2)):
            fan.rotation_euler = (R_(i * 75), R_(90), 0); fan.keyframe_insert("rotation_euler", frame=f)
    return d

def shot_3a(f0, n):
    """P3 kneels and turns the vacuum motor in both hands, studying it"""
    use = ("P3",); f1 = f0 + n - 1; kp = V((0.6, 0.15)); yw = 20.0
    for k, f in enumerate(range(f0, f1 + 1, 40)):
        kneel("P3", f, kp, yw, lean=8, spine=(18, 0, 0), head=(26, 4 * math.sin(k)))
    kneel("P3", f1, kp, yw, lean=8, spine=(18, 0, 0), head=(26, 0))
    d = drill_copy("3a", f0, f1)
    for k_ in d.children:
        if k_.name.startswith("Drill_Cord"): key_vis(k_, f0, False)
    sh = (wpos("P3", "upperarm01.L", f0) + wpos("P3", "upperarm01.R", f0)) / 2
    c = sh + fwd(yw) * 0.34 + V((0, 0, -0.24))
    orient(d, c, rgt(yw) * -1)        # motor axis across the body
    sc.frame_set(f0); bpy.context.view_layer.update(); Mw = d.matrix_world
    shR = wpos("P3", "upperarm01.R", f0); ex = -1 if (Mw @ V((-0.092, 0, 0)) - shR).length < (Mw @ V((0.092, 0, 0)) - shR).length else 1
    hand("P3", "R", f0, Mw @ V((0.095 * ex, 0, 0)), Mw.to_3x3() @ V((-ex, 0, 0)), Mw.to_3x3() @ V((0, 0, 1)), pose="cup_hold")
    M0 = ik_mat("P3", "R", f0); child_of(d, "P3", "wrist.R", f0)
    for k, f in enumerate(range(f0 + 30, f1 + 1, 45)):
        key_ik("P3", "R", f, rigid(c, Rz(25 * math.sin(k * 1.3)) @ Rx(15 * math.cos(k)), (0, 0, 0.03 * (k % 2))) @ M0)
    for f in sorted(set(list(range(f0, f1 + 1, 15)) + [f1])):
        sc.frame_set(f); Mw = d.matrix_world
        kq = V((kp.x, kp.y, 0.0)) + fwd(yw) * 0.05 - rgt(yw) * 0.13 + V((0, 0, 0.32))
        hand("P3", "L", f, kq, -fwd(yw) + V((0, 0, -0.6)), V((0, 0, -1)), pole=wpos("P3", "upperarm01.L", f) - rgt(yw) * 0.4 - fwd(yw) * 0.2, pose="relaxed")
        elbow("P3", "R", f, wpos("P3", "upperarm01.R", f) + rgt(yw) * 0.4 + V((0, 0, -0.3)))
    camera("3a", f0, n, [(0, (0.2, -0.95, 1.0), (0.6, 0.1, 0.72), 26), (1, (0.3, -0.88, 0.98), (0.6, 0.1, 0.72), 26)])
    return use

def shot_3b(f0, n):
    """insert: the home-made drill resting on the floor by the vent, the fan spins up (no hands)"""
    f1 = f0 + n - 1; d = drill_copy("3b", f0, f1, spin=True)
    orient(d, V((0.55, 1.2, 0.05)), V((0.3, 1, 0)).normalized().cross(V((0, 0, 1))))
    camera("3b", f0, n, [(0, (0.95, 0.95, 0.32), (0.56, 1.2, 0.06), 45), (1, (0.85, 1.0, 0.28), (0.56, 1.2, 0.06), 45)], fstop=11.0, catch=False)
    return ()

def shot_3c(f0, n):
    """P3 kneels at the vent and holds the drill to the grille edge with both hands; the red cord trails; dust puffs"""
    use = ("P3",); f1 = f0 + n - 1; kp = V((-0.02, 0.98)); yw = 160.0
    for k, f in enumerate(range(f0, f1 + 1, 40)):
        kneel("P3", f, kp, yw, lean=16, spine=(18 + (2 if k % 2 else 0), 0, 0), head=(22, 3 * math.sin(k)))
    kneel("P3", f1, kp, yw, lean=16, spine=(18, 0, 0), head=(22, 0))
    hole_grow(f0, 1.0, 1.0)
    d = drill_copy("3c", f0, f1, spin=True)
    tip = V((VX + 0.17, 1.58, VZ - 0.02)); ax = V((0.15, 1, 0.05)).normalized()
    orient(d, tip - ax * 0.23, ax)
    sc.frame_set(f0); bpy.context.view_layer.update(); Mw = d.matrix_world
    hand("P3", "R", f0, Mw @ V((-0.02, 0, 0.088)), Mw.to_3x3() @ V((0, 0, -1)), Mw.to_3x3() @ V((1, 0, 0)), pose="cup_hold")
    M0 = ik_mat("P3", "R", f0); child_of(d, "P3", "wrist.R", f0)
    for k, f in enumerate(range(f0 + 8, f1 + 1, 10)):
        key_ik("P3", "R", f, rigid(tip, Rz(1.5 * (1 if k % 2 else -1)), ax * (0.004 * (k % 2)) + V((0, 0, 0.01 * math.sin(k * 0.4)))) @ M0)
    for f in sorted(set(list(range(f0, f1 + 1, 10)) + [f1])):
        sc.frame_set(f); Mw = d.matrix_world
        kq = V((kp.x, kp.y, 0.0)) + fwd(yw) * 0.05 - rgt(yw) * 0.13 + V((0, 0, 0.32))
        hand("P3", "L", f, kq, -fwd(yw) + V((0, 0, -0.6)), V((0, 0, -1)), pole=wpos("P3", "upperarm01.L", f) - rgt(yw) * 0.4 - fwd(yw) * 0.2, pose="relaxed")
        elbow("P3", "R", f, wpos("P3", "upperarm01.R", f) + rgt(yw) * 0.45 + V((0, 0, -0.3)))
    # dust puffs at the bit (small grey spheres, keyed scale, no Scene Time)
    for i in range(10):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1); pf = bpy.context.active_object; pf.name = "Puff_3c_%d" % i
        pf.data.materials.append(bpy.data.materials["M_Rubble"]); vis_window(pf, f0, f1)
        t0 = f0 + 10 + i * (n - 20) // 10
        base = tip + V((random.uniform(-0.03, 0.03), -0.02, random.uniform(-0.02, 0.02)))
        for f, sz, off in ((t0, 0.002, 0), (t0 + 12, 0.012, 0.04), (t0 + 30, 0.0005, 0.09)):
            pf.location = base + V((0, -off, -off * 0.6)); pf.scale = (sz,) * 3
            pf.keyframe_insert("location", frame=f); pf.keyframe_insert("scale", frame=f)
    camera("3c", f0, n, [(0, (0.92, 0.35, 0.85), (0.1, 1.3, 0.6), 24), (1, (0.9, 0.42, 0.83), (0.1, 1.32, 0.58), 24)])
    return use

# ================================================================== BEAT 4: dummy heads and the bed check
def beam_sweep(sid, f0, f1, frm, to_a, to_b):
    L = bpy.data.lights.new("Beam_" + sid, 'SPOT'); L.spot_size = R_(22); L.spot_blend = 0.6; L.color = (1, 0.93, 0.78); L.energy = 0
    o = bpy.data.objects.new("Beam_" + sid, L); sc.collection.objects.link(o); o.location = frm; o.rotation_mode = 'QUATERNION'
    for f, tgt, e in ((f0, to_a, 0), (f0 + 8, to_a, 140), (f0 + (f1 - f0) * 0.6, to_b, 140), (f1 - 6, to_b, 140), (f1, to_b, 0)):
        o.rotation_quaternion = (V(tgt) - V(frm)).to_track_quat('-Z', 'Y'); L.energy = e
        o.keyframe_insert("rotation_quaternion", frame=int(f)); L.keyframe_insert("energy", frame=int(f))
    return o

def shot_4a(f0, n):
    """CU: the dummy head on the pillow under the blanket; a flashlight beam slides across it"""
    f1 = f0 + n - 1
    beam_sweep("4a", f0, f1, V((-0.06, -2.1, 1.45)), V((-0.6, -1.3, 0.6)), V((-0.85, -1.05, 0.66)))
    camera("4a", f0, n, [(0, (-0.25, -0.55, 1.05), (BX, -1.12, 0.66), 40), (1, (-0.3, -0.62, 1.0), (BX, -1.12, 0.66), 40)])
    return ()

def shot_4b(f0, n):
    """the guard at the bars raises his flashlight, looks in, nods and lowers it (shot from inside the cell, his face in a gap)"""
    use = ("Guard",); f1 = f0 + n - 1; gp = V((-0.06, -2.75, 0)); yw = 180.0
    stand_idle("Guard", f0, f1, gp, yw, arms=False, head_fn=lambda f: (5 if 35 < f - f0 < 95 else 0, -10 + 12 * ss((f - f0) / 60.0) + (0 if f - f0 < 70 else 6 * math.sin((f - f0) / 6.0))))
    fl = prop_copy("Flashlight", "Flashlight_4b", f0, f1)
    sh = wpos("Guard", "upperarm01.R", f0)
    orient(fl, sh + V((-0.05, 0.47, -0.38)), V((0, 1, -0.3)))
    M0 = hold_prop("Guard", "R", f0, fl, fl.matrix_world @ V((0, -0.06, 0)), fl.matrix_world.to_3x3() @ V((0, 0, -1)), fl.matrix_world.to_3x3() @ V((1, 0, 0)), "wrap")
    for f, up, tl in ((f0 + 35, 0.05, -8), (f0 + 85, 0.06, -10), (f1 - 10, 0.02, 0), (f1, 0.0, 0)):
        key_ik("Guard", "R", f, rigid(fl.matrix_world.translation, Rx(tl), (0, 0.06 * (up > 0.1), up)) @ M0)
        elbow("Guard", "R", f, wpos("Guard", "upperarm01.R", f) + V((0.35, 0.1, -0.3)))
    for f in (f0, f1): relaxed_arm("Guard", "L", f, yw)
    spot = bpy.data.lights.new("FlashSpot_4b", 'SPOT'); spot.spot_size = R_(24); spot.spot_blend = 0.5; spot.energy = 0; spot.color = (1, 0.93, 0.78)
    so = bpy.data.objects.new("FlashSpot_4b", spot); sc.collection.objects.link(so)      # world-space beam from his hand into the cell
    so.location = (gp.x + 0.15, gp.y + 0.35, 1.32); so.rotation_mode = 'QUATERNION'
    so.rotation_quaternion = (V((BX, -1.1, 0.66)) - so.location).to_track_quat('-Z', 'Y')
    for f, e in ((f0, 0), (f0 + 30, 0), (f0 + 38, 120), (f1 - 12, 120), (f1 - 4, 0)):
        spot.energy = e; spot.keyframe_insert("energy", frame=f)
    camera("4b", f0, n, [(0, (-0.06, -0.5, 1.7), (-0.06, -2.8, 1.66), 70), (1, (-0.06, -0.58, 1.7), (-0.06, -2.8, 1.66), 70)])
    return use

def shot_4c(f0, n):
    """the dummy head again from the wall side as the beam leaves; slow pull-back"""
    f1 = f0 + n - 1
    beam_sweep("4c", f0, f1, V((-0.06, -2.1, 1.45)), V((-0.8, -1.1, 0.66)), V((-0.2, -0.4, 0.5)))
    camera("4c", f0, n, [(0, (-1.02, -0.62, 0.98), (BX, -1.13, 0.66), 42), (1, (-1.02, -0.5, 1.02), (BX, -1.13, 0.66), 42)])
    return ()

# ================================================================== BEAT 5: break-through and the corridor
FZ2 = 0.2
def shot_5a(f0, n):
    """corridor side: the vent grille in the wall, crumbs trickle from its edges"""
    f1 = f0 + n - 1
    for i in range(8):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1); c_ = bpy.context.active_object; c_.name = "Crumb_5a_%d" % i
        c_.data.materials.append(bpy.data.materials["M_Rubble"]); vis_window(c_, f0, f1); sz = random.uniform(0.004, 0.009); c_.scale = (sz,) * 3
        x = X2 + random.uniform(-0.25, 0.25); t0 = f0 + 10 + i * (n - 30) // 8; z0 = VZ + 0.04 - 0.17
        for f, z in ((f0, z0), (t0, z0), (t0 + 12, FZ2 + sz)):
            c_.location = (x, 0.03 + 0.02 * random.random(), z); c_.keyframe_insert("location", frame=f)
    camera("5a", f0, n, [(0, (X2 + 0.55, 1.45, 0.6), (X2, 0, 0.46), 32), (1, (X2 + 0.4, 1.15, 0.55), (X2, 0, 0.46), 32)], catch=False)
    return ()

def crawl_pose(n, f, pelvis_xy, yaw, phase, gz, head=(-35.0, 0.0), hand_pose="relaxed", reach=0.16):
    """hands and knees. phase 0..1 per stride (diagonal pairs); pelvis_xy at hip height"""
    L = THIGH[n]; root = V((pelvis_xy[0], pelvis_xy[1], gz + 0.12 + L * 0.98)) + V((0, 0, HUM[n].root_head.z - RIG[n].BN["upperleg01.L"].head_local.z))
    body(n, f, root, yaw, flex=86, spine=(10, 0, 0), head=head)
    sc.frame_set(f)
    for s, ph in (("L", 0.0), ("R", 0.5)):
        sx = 1 if s == "L" else -1; u = (phase + ph) % 1.0
        swing = math.sin(math.pi * u * 2) * 0.08                   # hands and the opposite knee alternate
        kn = root - rgt(yaw) * sx * 0.12 + fwd(yaw) * (0.02 - swing) ; kn.z = gz + 0.11
        ank = kn - fwd(yaw) * (SHIN[n] * 0.96); ank.z = gz + 0.14
        foot(n, s, f, ank, yaw, pitch=170, knee=kn + fwd(yaw) * 0.5 + V((0, 0, -0.2)))
    for s, ph in (("L", 0.5), ("R", 0.0)):
        sx = 1 if s == "L" else -1; u = (phase + ph) % 1.0
        swing = math.sin(math.pi * u * 2) * 0.09; lift = max(0.0, math.sin(math.pi * u * 2)) * 0.05
        sh = wpos(n, "upperarm01." + s)
        palm = V((sh.x, sh.y, gz)) + fwd(yaw) * (reach + swing) - rgt(yaw) * sx * 0.04; palm.z = gz + 0.02 + lift
        hand(n, s, f, palm, V((0, 0, -1)), fwd(yaw) - rgt(yaw) * sx * 0.25, pole=sh + fwd(yaw) * -0.25 - rgt(yaw) * sx * 0.45 + V((0, 0, 0.05)), pose=hand_pose)

def shot_5b(f0, n):
    """P1's hands push the grille out from inside the duct; it drops to the floor in a burst of dust"""
    use = ("P1",); f1 = f0 + n - 1; GZ[0] = FZ2; yw = 180.0
    g = bpy.data.objects["S2_Grille"]
    gpos = V(g.location); push_end = f0 + 40
    for f in (f0, f0 + 20, push_end, push_end + 20, f1):
        u = min(1.0, (f - f0) / 40.0)
        crawl_pose("P1", f, (X2, -0.95 + 0.15 * u), yw, 0.0, 0.13, head=(-30, 0))
    # the hands are flat on the grille's back while it is pushed (contact keyed on both), then the grille falls on its own weight
    for f, dy in ((f0, 0.0), (f0 + 20, 0.05), (push_end, 0.14)):
        g.location = gpos + V((0, dy, 0)); g.rotation_euler = (0, 0, R_(180)); g.keyframe_insert("location", frame=f); g.keyframe_insert("rotation_euler", frame=f)
        for s, dx in (("L", -1.0), ("R", 1.0)):
            hand("P1", s, f, gpos + V((dx * 0.335, dy - 0.01, 0.0)), V((-dx, 0, 0)), V((0, 1, 0)), pole=wpos("P1", "upperarm01." + s, f) + V((dx * 0.12, -0.25, -0.35)), pose="relaxed")
    for s, dx in (("L", -1.0), ("R", 1.0)):     # release: hands open and come off the frame sides before it tips
        hand("P1", s, push_end + 2, gpos + V((dx * 0.5, 0.08, 0.0)), V((-dx, 0, 0)), V((0, 1, 0)), pole=wpos("P1", "upperarm01." + s, push_end + 3) + V((dx * 0.12, -0.25, -0.35)), pose="flat_palm")
    for f, loc, rx in ((push_end + 8, gpos + V((-0.03, 0.24, -0.05)), 25), (push_end + 16, gpos + V((-0.4, 0.38, -0.2)), 80), (push_end + 20, V((X2 - 0.6, gpos.y + 0.45, FZ2 + 0.012)), 90), (push_end + 24, V((X2 - 0.62, gpos.y + 0.47, FZ2 + 0.03)), 85), (push_end + 28, V((X2 - 0.63, gpos.y + 0.48, FZ2 + 0.012)), 90)):
        g.location = loc; g.rotation_euler = (R_(rx), 0, R_(180)); g.keyframe_insert("location", frame=f); g.keyframe_insert("rotation_euler", frame=f)
    for s, dx in (("L", -1.0), ("R", 1.0)):     # hands come back through the middle of the opening
        hand("P1", s, push_end + 10, V((X2 + dx * 0.15, -0.15, 0.5)), V((0, 0, -1)), V((0, 1, 0)), pole=wpos("P1", "upperarm01." + s, push_end + 10) + V((dx * 0.15, -0.2, -0.3)), pose="relaxed")
    for f, hd in ((push_end + 20, -40), (push_end + 45, -50), (f1, -48)):     # palms back on the duct floor; he looks up and out
        crawl_pose("P1", f, (X2, -1.0), yw, 0.0, 0.13, head=(hd, 6 * math.sin(f / 9.0)), hand_pose="flat_palm", reach=0.0)
    for i in range(14):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1); pf = bpy.context.active_object; pf.name = "Puff_5b_%d" % i
        pf.data.materials.append(bpy.data.materials["M_Rubble"]); vis_window(pf, f0, f1)
        base = V((X2 + random.uniform(-0.3, 0.3), gpos.y + random.uniform(0.2, 0.5), FZ2 + 0.02))
        t0 = push_end + 18 + random.randint(0, 6)
        for f, sz, up in ((f0, 0.0005, 0), (t0, 0.0005, 0), (t0 + 10, 0.03, 0.06), (t0 + 40, 0.004, 0.18)):
            pf.location = base + V((0, 0, up)); pf.scale = (sz,) * 3; pf.keyframe_insert("location", frame=f); pf.keyframe_insert("scale", frame=f)
    camera("5b", f0, n, [(0, (X2 + 0.45, 1.45, 0.45), (X2, -0.2, 0.55), 30), (1, (X2 + 0.4, 1.3, 0.42), (X2, -0.2, 0.55), 30)])
    GZ[0] = 0.0
    return use

def shot_5c(f0, n):
    """P1 crawls out of the hole on hands and knees into the corridor"""
    use = ("P1",); f1 = f0 + n - 1; yw = 180.0
    g = bpy.data.objects["S2_Grille"]; gl = V(g.location)
    for f in (f0, f1): g.keyframe_insert("location", frame=f); g.keyframe_insert("rotation_euler", frame=f)
    stride = 0.32; dist = 0.15
    for f in range(f0, f1 + 1, 6):
        u = (f - f0) / (n - 1); y = 0.74 + dist * ss(u)
        crawl_pose("P1", f, (X2 + 0.35, y), yw + 10 * ss(u), (y - 0.74) / stride, FZ2, head=(-30 - 10 * math.sin(u * 3), 35 * math.sin(u * 5)))
    camera("5c", f0, n, [(0, (X2 + 1.6, 1.85, 1.35), (X2 + 0.3, 0.95, 0.5), 22), (1, (X2 + 1.6, 1.85, 1.32), (X2 + 0.35, 1.25, 0.52), 22)], fstop=6.0)
    return use

def walk_arms(n, f0, f1, yaw_fn, every=8, amp=0.16):
    """bent elbows (~35 deg), forearms swinging opposite to the legs"""
    for i, f in enumerate(sorted(set(list(range(f0, f1 + 1, every)) + [f1]))):
        sw = amp * math.sin((f - f0) * math.pi / 22.0)
        relaxed_arm(n, "L", f, yaw_fn(f), fwd_=0.08 + sw, up=0.13 + 0.06 * max(0.0, sw / amp))
        relaxed_arm(n, "R", f, yaw_fn(f), fwd_=0.08 - sw, up=0.13 + 0.06 * max(0.0, -sw / amp))

def shot_5d(f0, n):
    """P1 and P2 walk along the service corridor toward camera among the pipes; the supply crate (logo) behind them"""
    use = ("P1", "P2"); f1 = f0 + n - 1; GZ[0] = FZ2
    g = bpy.data.objects["S2_Grille"]
    for f in (f0, f1):
        g.location = (X2 - 0.75, 0.09, FZ2 + 0.28); g.rotation_euler = (R_(-12), 0, R_(180))
        g.keyframe_insert("location", frame=f); g.keyframe_insert("rotation_euler", frame=f)
    for nm, y, x0, x1, d0 in (("P1", 0.55, X2 - 1.2, X2 + 1.4, 0), ("P2", 0.78, X2 - 2.1, X2 + 0.6, 10)):
        path = lambda f, x0=x0, x1=x1, y=y: V((x0 + (x1 - x0) * (f - f0) / (n - 1), y, 0))
        HUM[nm].walk(path, lambda f: 90.0, f0, f1, stride=0.62, lift=0.07)
        for f in range(f0, f1 + 1, 12):
            HUM[nm].key_spine(f, flex=6, twist=0, head=(-6 + 4 * math.sin(f / 15.0), 20 * math.sin((f - f0 + d0) / 35.0)))
        walk_arms(nm, f0, f1, lambda f: 90.0)
    camera("5d", f0, n, [(0, (X2 + 2.7, 0.75, 1.45), (X2 - 1.5, 1.15, 0.95), 22), (1, (X2 + 3.3, 0.75, 1.42), (X2 - 0.9, 1.15, 0.95), 22)])
    GZ[0] = 0.0
    return use

# ================================================================== BEAT 6: up the shaft, down the pipe
def climb(n, f0, f1, z_start, rate, lad_x, lad_y, yaw=180.0, phase=0.0):
    """ladder climb at 1x: hands grip rungs at most head height, feet stand on rungs; root rises at `rate` m/frame"""
    RUNG = 0.30; rung_z = lambda k: 0.30 + k * RUNG
    for f in range(f0, f1 + 1, 4):
        t = f - f0; z = z_start + rate * t
        root = V((lad_x, lad_y - 0.38, z)); body(n, f, root, yaw, flex=8, spine=(4, 0, 0), head=(-18, 10 * math.sin(t / 30.0)))
        cyc = (rate * t / RUNG + phase)
        for s, ph in (("L", 0.0), ("R", 0.5)):
            sx = 1 if s == "L" else -1
            c = cyc + ph; k = math.floor(c); u = c - k
            # foot: stands on rung below the hip (hip - 0.85), moves up one rung in the second half of its cycle
            base = (z - 0.95 - 0.30) / RUNG
            kf = math.floor(base + ph); uf = (base + ph) - kf
            zf = rung_z(kf) if uf < 0.6 else rung_z(kf) + RUNG * ss((uf - 0.6) / 0.4)
            sw = math.sin(math.pi * (uf - 0.6) / 0.4) if uf >= 0.6 else 0.0
            ank = V((lad_x - sx * 0.12, lad_y - 0.1 - 0.2 * sw, zf + 0.11 + 0.06 * sw))
            foot(n, s, f, ank, yaw, pitch=-5, knee=ank + V((0, -0.6, 0.4)))
            # hand: grips the rung near head height, shifts up one rung in the other half
            kh = math.floor(base + 0.5 + ph); uh = (base + 0.5 + ph) - kh
            top = z + 0.45
            zh = min(top, rung_z(kh) + 4 * RUNG) if uh < 0.6 else min(top, rung_z(kh) + 4 * RUNG + RUNG * ss((uh - 0.6) / 0.4))
            zh = rung_z(round((zh - 0.30) / RUNG)) if uh < 0.6 else zh
            if uh < 0.6:      # gripping a rung: contact-aware grip closes the fingers onto it
                k_r = int(round((zh - 0.30) / RUNG)); rung = bpy.data.objects.get("S3_Rung%02d" % k_r)
                elbow(n, s, f, V((lad_x - sx * 0.45, lad_y - 0.55, zh - 0.35)))
                grip_object(bpy.data.objects[n], s, f, rung, V((lad_x - sx * 0.11, lad_y - 0.014, zh)), V((0, 1, 0)), finger_dir=V((0, 0.3, 1)), grip="wrap")
            else:             # moving up to the next rung, 8 cm in front of the ladder
                hand(n, s, f, V((lad_x - sx * 0.11, lad_y - 0.09, zh)), V((0, 1, 0)), V((0, 0, 1)),
                     pole=V((lad_x - sx * 0.45, lad_y - 0.55, zh - 0.35)), pose="relaxed")

def stair_climb(n, f0, f1, k0, k1, x, delay=0):
    """walk up the open-tread stair from tread k0 to k1 at 1x: each foot steps up two treads per stride, swinging clear of the
    tread edges; the pelvis rises on a smooth ramp; arms swing loosely (no hand contacts)"""
    RISE, RUN, Y0 = 0.2, 0.29, -3.5
    yaw = 180.0; S = k1 - k0; T = (f1 - f0 - delay) / max(1, S)          # frames per tread
    ty = lambda k: Y0 + (k - 1) * RUN + 0.035 if k > 0 else Y0 - 0.42
    tz = lambda k: max(0, k) * RISE + 0.025
    def foot_at(s, f):
        """tread events: event i lifts the L foot (even i) or R foot (odd i) onto tread k0+i+1 over 0.9 T frames"""
        sx = 1 if s == "L" else -1; t = f - f0 - delay; k = k0; D = 0.9 * T
        for i in range(S):
            if (i % 2 == 0) != (s == "L"): continue
            ti = i * T; kn = min(k1, k0 + i + 1)
            if t >= ti + D: k = kn; continue
            if t > ti:
                u = ss((t - ti) / D)
                uy = ss(max(0.0, (u - 0.35) / 0.65)); uz = ss(min(1.0, u / 0.55))       # lift first, then forward
                y = ty(k) + (ty(kn) - ty(k)) * uy - 0.13 * math.sin(math.pi * min(1.0, u / 0.6)); z = tz(k) + (tz(kn) - tz(k)) * uz + 0.14 * math.sin(math.pi * u)
                return V((x - sx * 0.11, y, z + HUM[n].ankle[s].z)), -15 * math.sin(math.pi * u)
            break
        return V((x - sx * 0.11, ty(k), tz(k) + HUM[n].ankle[s].z)), 0.0
    for f in range(f0, f1 + 1, 2):
        prog = min(S, max(0.0, (f - f0 - delay) / T))
        aL, _ = foot_at("L", f); aR, _ = foot_at("R", f)          # pelvis between the feet, slightly crouched: both legs always reach
        root = V((x, (aL.y + aR.y) / 2 + 0.03, (aL.z + aR.z) / 2 - HUM[n].ankle["L"].z + HUM[n].root_head.z - 0.2))
        body(n, f, root, yaw, flex=5, spine=(8, -6 * math.sin(math.pi * prog), 0), head=(-14, 8 * math.sin(f / 25.0)))
        for s in "LR":
            ank, pt = foot_at(s, f); foot(n, s, f, ank, yaw, pitch=pt, knee=ank + fwd(yaw) * 0.12 + V((0, 0, 0.8)))
    walk_arms(n, f0, f1, lambda f: yaw, every=8, amp=0.08)

def shot_6a(f0, n):
    """P1 and P2 climb the steep steel stair up the service shaft toward the roof hatch (seen from the top, faces up)"""
    use = ("P1", "P2"); f1 = f0 + n - 1
    stair_climb("P1", f0, f1, 2, 7, X3 - 0.7)
    stair_climb("P2", f0, f1, 0, 4, X3 - 0.7, delay=10)
    camera("6a", f0, n, [(0, (X3 - 0.7, -0.6, 3.6), (X3 - 0.7, -2.6, 1.3), 26), (1, (X3 - 0.65, -0.62, 3.65), (X3 - 0.7, -2.1, 1.6), 26)], fstop=6.0)
    return use

def shot_6b(f0, n):
    """outside at night: P1 slides down the vent pipe, hands wrapped round it at chest height, knees and feet hugging it; he lands"""
    use = ("P1",); f1 = f0 + n - 1; px, py = X4, -0.30
    land = f0 + int(n * 0.72)
    walk_from = land + 10
    for f in [x for x in range(f0, f1 + 1, 4) if x <= walk_from] + [walk_from]:
        if f <= land:
            u = (f - f0) / (land - f0); z = 4.6 - 3.6 * u            # root height: slides at a steady rate
        else:
            u = (f - land) / max(1, f1 - land); z = HUM["P1"].root_head.z - 0.12 * math.sin(math.pi * min(1, u * 1.5)) * (1 - u)
        on_pipe = f <= land
        root = V((px, py - 0.42, z)) if on_pipe else V((px + 0.05, py - 0.5, z))
        yw6 = 180.0 if on_pipe else 180.0 - 55.0 * ss((f - land) / 10.0)
        body("P1", f, root, yw6, flex=(0 if on_pipe else 4), spine=(-4 if on_pipe else 6, 0, 0), head=(-12 if on_pipe else 0, 40 if on_pipe else 30 * math.sin((f - land) / 20.0)))
        if on_pipe:
            for s in "LR":
                sx = 1 if s == "L" else -1
                ank = V((px - sx * 0.15, py - 0.28, z - 0.78)); foot("P1", s, f, ank, 180 - sx * 20, pitch=-10, knee=ank + V((-sx * 0.45, -0.3, 0.35)))
            for s, dz in (("L", 0.42), ("R", 0.28)):
                sx = 1 if s == "L" else -1
                hp = V((px - sx * 0.015, py - 0.095, z + dz)); hand("P1", s, f, hp, V((0, 1, 0)), V((-sx, 0, 0.3)), pole=hp + V((-sx * 0.5, -0.3, -0.25)), pose="relaxed")
        else:
            stand_feet("P1", f, root - V((0, 0, root.z)), yw6)
            relaxed_arm("P1", "L", f, yw6); relaxed_arm("P1", "R", f, yw6)
    p0 = V((px + 0.05, py - 0.5, 0)); p1 = V((px + 0.6, py - 1.25, 0))
    path6 = lambda f: p0.lerp(p1, ss((f - walk_from) / max(1, f1 - walk_from)))
    yaw6 = lambda f: 125.0 - 85.0 * ss((f - walk_from) / max(1, (f1 - walk_from) * 0.6))
    HUM["P1"].walk(path6, yaw6, walk_from, f1, stride=0.6, lift=0.07)
    for f in range(walk_from, f1 + 1, 8): HUM["P1"].key_spine(f, flex=4, head=(-4, 10 * math.sin(f / 14.0)))
    walk_arms("P1", walk_from, f1, yaw6)
    camera("6b", f0, n, [(0, (X4 + 3.2, -4.0, 4.6), (X4, -0.4, 4.0), 26), (0.75, (X4 + 3.0, -4.2, 2.4), (X4, -0.5, 1.4), 26), (1, (X4 + 2.8, -4.0, 2.0), (X4, -0.6, 1.1), 26)], fstop=6.0)
    return use

# ================================================================== BEAT 7-8: the raft
RAFT_SEATS = {"P1": (0.18, 0.45, 180.0), "P2": (-0.2, -0.15, 180.0), "P3": (0.15, -0.78, 180.0)}
def raft_z(f): return 0.045 * math.sin(f / 20.0) + 0.015 * math.sin(f / 8.0)
def raft_shot(sid, f0, n, drift=0.0, paddle=True):
    use = ("P1", "P2", "P3"); f1 = f0 + n - 1; R = bpy.data.objects["Raft"]
    base = V((X5, 0.0 + drift * 0, 0))
    for f in sorted(set(list(range(f0, f1 + 1, 6)) + [f1])):
        u = (f - f0) / (n - 1); off = V((0, drift * u, raft_z(f))); R.location = base + off; R.rotation_euler = (0, 0, 0)
        R.keyframe_insert("location", frame=f); R.keyframe_insert("rotation_euler", frame=f)
    for nm, (x, y, yw) in RAFT_SEATS.items():
        for f in sorted(set(list(range(f0, f1 + 1, 6)) + [f1])):
            u = (f - f0) / (n - 1); off = V((0, drift * u, raft_z(f)))
            seat = base + off + V((x, y, 0))
            GZ[0] = 0.085 + off.z
            sit(nm, f, seat, 0.11 + off.z, yw, knee_fwd=0.36, spread=0.13, spine=(10 + 3 * math.sin(f / 13.0), 4 * math.sin((f + 20 * x) / 19.0), 3 * math.sin((f + 37 * y) / 23.0)), head=(-4 + 5 * math.sin((f + 50 * y) / 21.0), 30 * math.sin((f + 70 * (x + y)) / 28.0)))
            for s in "LR":
                sx = 1 if s == "L" else -1
                if nm == "P1" and s == "R" and paddle: continue
                kn = seat + fwd(yw) * 0.2 - rgt(yw) * sx * 0.14 + V((0, 0, 0.53))
                hand(nm, s, f, kn, V((0, 0, -1)), fwd(yw), pole=wpos(nm, "upperarm01." + s, f) - rgt(yw) * sx * 0.4 - fwd(yw) * 0.2, pose="relaxed")
    GZ[0] = 0.0
    paddle = False
    if paddle:
        pd = prop_copy("Paddle", "Paddle_" + sid, f0, f1)
        sc.frame_set(f0); sh = wpos("P1", "upperarm01.R", f0)
        c = sh + rgt(180.0) * 0.32 + fwd(180.0) * 0.1 + V((0, 0, -0.32))
        orient(pd, c, V((0, 0.25, -1)), V((1, 0, 0)))
        M0 = hold_prop("P1", "R", f0, pd, pd.matrix_world @ V((0, -0.2, 0)), V((-1, 0, 0)), V((0, 0, 1)), "wrap")
        for k, f in enumerate(range(f0 + 15, f1 + 1, 30)):
            ang = 25 if k % 2 else -20
            key_ik("P1", "R", f, Matrix.Translation(V((0, drift * (f - f0) / (n - 1), raft_z(f)))) @ rigid(sh, Rx(ang), (0, 0, 0)) @ M0)
            elbow("P1", "R", f, wpos("P1", "upperarm01.R", f) + rgt(180.0) * 0.45 + V((0, 0, -0.25)))
    return use

def shot_7a(f0, n):
    use = raft_shot("7a", f0, n, drift=0.5)
    camera("7a", f0, n, [(0, (X5 + 1.7, -3.0, 0.65), (X5, 3.0, 1.0), 22), (1, (X5 + 1.6, -2.7, 0.62), (X5, 3.5, 1.0), 22)], fstop=6.0)
    return use
def shot_7b(f0, n):
    use = raft_shot("7b", f0, n, drift=0.6)
    camera("7b", f0, n, [(0, (X5 + 3.3, -1.1, 0.95), (X5, -0.2, 0.6), 26), (1, (X5 + 2.9, 1.0, 0.65), (X5, 0.5, 0.6), 26)], fstop=6.0)
    return use
def shot_7c(f0, n):
    use = raft_shot("7c", f0, n, drift=0.5)
    camera("7c", f0, n, [(0, (X5 - 1.0, 3.6, 1.15), (X5, 0.0, 0.7), 26), (1, (X5 - 0.8, 3.1, 1.05), (X5, 0.3, 0.7), 26)], fstop=6.0)
    return use

def shot_8a(f0, n):
    """from the island: the searchlight sweeps the dark water; a patrol boat with a spotlight crosses the frame"""
    use = raft_shot("8a", f0, n, drift=0.3, paddle=False); f1 = f0 + n - 1
    piv = bpy.data.objects["S4_BeamPivot"]; spot = bpy.data.objects["S4_SearchSpot"].data
    vis_window(bpy.data.objects["S4_Beam"], f0, f1)
    for f, yawd in ((f0, 10), (f1, -25)):
        piv.rotation_euler = (R_(-20), 0, R_(yawd)); piv.keyframe_insert("rotation_euler", frame=f)
    for f, e in ((f0 - 1, 0), (f0, 40000), (f1, 40000), (f1 + 1, 0)):
        spot.energy = e; spot.keyframe_insert("energy", frame=f)
    b = bpy.data.objects["S4_Boat"]; bs = bpy.data.objects["S4_BoatSpot"].data
    for f, x in ((f0, X5 - 26), (f1, X5 - 10)):
        b.location = (x, -16, 0.05); b.rotation_euler = (0, 0, R_(-75)); b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f)
    for f, e in ((f0 - 1, 0), (f0, 3000), (f1, 3000), (f1 + 1, 0)):
        bs.energy = e; bs.keyframe_insert("energy", frame=f)
    camera("8a", f0, n, [(0, (X5 - 16, -43, 7.5), (X5 - 4, -6, 0), 32), (1, (X5 - 15.5, -43, 7.3), (X5 - 2, -4, 0), 32)], fstop=8.0, catch=False)
    return use

def shot_8b(f0, n):
    """wide: the small raft drifts off toward the bridge into the dusk; slow pull-back and rise"""
    use = raft_shot("8b", f0, n, drift=1.4, paddle=False)
    camera("8b", f0, n, [(0, (X5 + 1.5, -5.0, 1.4), (X5, 8, 1.6), 28), (1, (X5 + 2.5, -9.0, 3.6), (X5, 14, 3.5), 28)], fstop=8.0, catch=False)
    return use

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
