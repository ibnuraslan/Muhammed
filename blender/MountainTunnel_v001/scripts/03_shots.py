"""MountainTunnel: every shot as its own clip (character keys, props, camera + marker).
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
YF, HY = sc["YF"], sc["HY"]
GZ = [0.0]
def ground_z(x, y): return GZ[0]          # overrides anim_lib: flat floors everywhere (raft/ladder poses key feet directly)

CH = ("Man", "Wife", "V1", "V2", "V3")
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

def orient(o, loc, ydir, zhint=V((0, 0, 1))):
    y = V(ydir).normalized(); x = y.cross(V(zhint)).normalized(); z = x.cross(y)
    o.matrix_world = Matrix.Translation(V(loc)) @ Matrix((x, y, z)).transposed().to_4x4()

def stand_idle(n, f0, f1, pos, yaw, head=(0.0, 0.0), spine=(3.0, 0.0, 0.0), every=40, arms=True, head_fn=None):
    k = 0
    for f in list(range(f0, f1, every)) + [f1]:
        hd = head_fn(f) if head_fn else (head[0] + (1.5 if k % 2 else 0), head[1] + 2 * math.sin(k))
        body(n, f, V(pos) + V((0, 0, HUM[n].root_head.z - 0.01 + (0.004 if k % 2 else 0))), yaw, spine=(spine[0] + (1.5 if k % 2 else 0), spine[1], spine[2]), head=hd)
        stand_feet(n, f, pos, yaw)
        if arms: relaxed_arm(n, "L", f, yaw); relaxed_arm(n, "R", f, yaw)
        k += 1

# ================================================================== MountainTunnel helpers
CUSTOM = {}                 # shot id -> rigs whose object transform the shot keys itself (lying wife)
def key_obj(o, f, loc, rot=(0, 0, 0)):
    o.location = loc; o.rotation_euler = rot
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)

def copy_tree(src, name, f0, f1):
    """copy an empty-rooted prop (stretcher) with its children; visible only inside [f0, f1]"""
    root = bpy.data.objects[src].copy(); root.name = name; bpy.data.objects[src].users_collection[0].objects.link(root); root.animation_data_clear()
    for c in bpy.data.objects[src].children:
        k = c.copy(); k.name = name + "_" + c.name.split("_", 1)[-1]; c.users_collection[0].objects.link(k); k.parent = root; k.animation_data_clear()
        vis_window(k, f0, f1)
    return root

AGE_MATS = [m for m in bpy.data.materials if m.node_tree and "Age" in m.node_tree.nodes]
BEARD = bpy.data.objects["Man.beard"]
def key_age(f0, f1, age):
    for m in AGE_MATS:
        nd = m.node_tree.nodes["Age"].outputs[0]
        for f in (f0, f1):
            nd.default_value = age; nd.keyframe_insert("default_value", frame=f)
    show = age >= 0.6
    key_vis(BEARD, f0, show)
    s = 0.85 + 0.15 * min(1.0, max(0.0, (age - 0.6) / 0.3))
    BEARD.scale = (s, s, s); BEARD.keyframe_insert("scale", frame=f0)

CUT = bpy.data.objects["Cutter"]; CUTFACE = bpy.data.objects["CutFace"]
def key_cut(f, y):
    CUT.location = (0, y, 0); CUT.keyframe_insert("location", frame=f)
def cut_window(f0, f1, y0, y1=None):
    key_cut(f0, y0); key_cut(f1, y0 if y1 is None else y1)
def show_cutface(f0, f1):
    key_vis(CUTFACE, f0, True); key_vis(CUTFACE, f1 + 1, False)
key_vis(CUTFACE, 1, False)

# chips of rock: spawned at each strike, fall under gravity (keyed), hidden outside their flight
CHIP_N = [0]
def chips(f, at, count=3, spread=0.12):
    for k in range(count):
        src = "Chip%d" % random.randrange(6); CHIP_N[0] += 1
        o = bpy.data.objects[src].copy(); o.name = "ChipF%04d" % CHIP_N[0]; bpy.data.objects[src].users_collection[0].objects.link(o)
        o.animation_data_clear()
        v = V((random.uniform(-0.6, 0.6), random.uniform(-1.4, -0.6), random.uniform(0.2, 1.2)))
        p0 = V(at) + V((random.uniform(-0.02, 0.02), -0.02, random.uniform(-0.02, 0.02)))
        T = 0
        for i in range(0, 60, 3):
            t = i / 60.0; p = p0 + v * t + V((0, 0, -4.9 * t * t))
            if p.z < 0.01: p.z = 0.01; T = i
            o.location = p; o.rotation_euler = (i * 0.3, i * 0.2, 0); o.keyframe_insert("location", frame=f + i); o.keyframe_insert("rotation_euler", frame=f + i)
            if p.z <= 0.011: break
        key_vis(o, 1, False); key_vis(o, f, True); key_vis(o, f + 45, False)

# hammer geometry (Poly Haven cross pein hammer): handle along local Z, head on top, striking face toward +X
HAM_FACE = V((0.055, 0.0, 0.152)); HAM_GRIP = V((0.0, 0.0, -0.085))
CH_BUTT = V((0.0, -0.12, 0.0)); CH_TIP = V((0.0, 0.125, 0.0)); CH_GRIP = V((0.0, -0.035, 0.0))
def frame_from(x, z):
    x = V(x).normalized(); y = V(z).cross(x).normalized(); z = x.cross(y)
    return Matrix((x, y, z)).transposed()

def strike(sid, f0, n, yc, age, period=44, x0=0.0, tip_z=1.05, first=10, chip=True, stance=0.85, lean=12.0):
    """the man at the rock face (cut end at y=yc), chisel in his left hand on the rock, hammer in his right striking its butt.
    Strike cycle: slow raise (to shoulder height, never above the head), fast hit, short hold, recoil."""
    nm = "Man"; f1 = f0 + n - 1; yaw = 180.0
    root = V((x0 + 0.12, yc - stance, HUM[nm].root_head.z - 0.035))
    for k, f in enumerate(list(range(f0, f1, 30)) + [f1]):
        body(nm, f, root + V((0, 0, 0.004 * (k % 2))), yaw, flex=lean, spine=(10 + 2 * (k % 2), -6, 0), head=(18 + 2 * math.sin(k), -6))
        for s in "LR":
            sx = 1 if s == "L" else -1
            xy = root + rgt(yaw) * (-sx) * 0.15 + fwd(yaw) * (0.05 if s == "L" else -0.12)
            foot(nm, s, f, (xy.x, xy.y, GZ[0] + HUM[nm].ankle[s].z), yaw + sx * 12)
    # chisel: tip on the rock, pointing into it and slightly down
    ch = prop_copy("Chisel", "Chisel_" + sid, f0, f1)
    d = V((0.08, 1.0, -0.18)).normalized(); tip = V((x0, yc - 0.035, tip_z))
    Mc = frame_from(V((1, 0, 0)).cross(d) * -1, V((0, 0, 1)))       # placeholder axes, replaced below
    yax = d; xax = yax.cross(V((0, 0, 1))).normalized(); zax = xax.cross(yax)
    ch.matrix_world = Matrix.Translation(tip - yax * 0.125) @ Matrix((xax, yax, zax)).transposed().to_4x4()
    sc.frame_set(f0); bpy.context.view_layer.update()
    Mw = ch.matrix_world.copy(); butt = Mw @ CH_BUTT
    elbow(nm, "L", f0, wpos(nm, "upperarm01.L", f0) + V((-0.35, 0.05, -0.25)))
    grip_object(bpy.data.objects[nm], "L", f0, ch, Mw @ CH_GRIP, V((0.55, 0.0, -0.85)), finger_dir=V((0.4, 0, -1)), grip="wrap")
    ML = ik_mat(nm, "L", f0); child_of(ch, nm, "wrist.L", f0)
    # the chisel stays put: re-key the left hand at the same matrix on every body key
    for f in list(range(f0, f1, 30)) + [f1]:
        key_ik(nm, "L", f, ML); elbow(nm, "L", f, wpos(nm, "upperarm01.L", f) + V((-0.35, 0.05, -0.25)))
    # hammer: contact pose = striking face on the chisel butt, handle back toward his right hip
    hm = prop_copy("Hammer", "Hammer_" + sid, f0, f1)
    hx = yax.copy()                                       # face direction = strike direction
    hz = rgt(yaw) * -0.9 + V((0, 0, 0.42)) + fwd(yaw) * 0.12; hz = (hz - hx * hz.dot(hx)).normalized()   # handle runs out to his right, head up-left of the grip
    Rh = frame_from(hx, hz)
    hm.matrix_world = Matrix.Translation(butt - Rh @ HAM_FACE - hx * 0.004) @ Rh.to_4x4()
    sc.frame_set(f0); bpy.context.view_layer.update(); Mh = hm.matrix_world.copy(); G = Mh @ HAM_GRIP
    elbow(nm, "R", f0, wpos(nm, "upperarm01.R", f0) + rgt(yaw) * 0.45 - fwd(yaw) * 0.15 + V((0, 0, -0.3)))
    grip_object(bpy.data.objects[nm], "R", f0, hm, G, (-fwd(yaw) * 0.2 + V((0, 0, -1.0))).normalized(), finger_dir=fwd(yaw), grip="wrap")
    MC = ik_mat(nm, "R", f0); child_of(hm, nm, "wrist.R", f0)
    # wrist-cock swing: rotate about the axis normal to the handle/strike plane, sign chosen so the head goes back
    # raise: the head lifts up over the grip (rotation about the strike axis) and the fist draws back a little;
    # the strike drives it forward along the chisel axis. Head stays below the hairline and away from the chest.
    nax = hx.normalized(); hp = Mh @ HAM_FACE
    sg = max((1, -1), key=lambda g: (G + Matrix.Rotation(R_(60 * g), 3, nax) @ (hp - G)).z)
    UP = rigid(G, Matrix.Rotation(R_(15 * sg), 3, nax), -hx * 0.17 + rgt(yaw) * 0.17 + V((0, 0, 0.04))) @ MC
    HALF = rigid(G, Matrix.Rotation(R_(6 * sg), 3, nax), -hx * 0.07 + rgt(yaw) * 0.07 + V((0, 0, 0.02))) @ MC
    f = f0 + first; hits = []
    key_ik(nm, "R", f0, HALF)
    while f + period <= f1 + 8:
        key_ik(nm, "R", f, HALF); key_ik(nm, "R", f + int(period * 0.45), UP)
        hit = f + int(period * 0.62); key_ik(nm, "R", hit, MC); key_ik(nm, "R", hit + 3, MC); hits.append(hit)
        key_ik(nm, "R", hit + int(period * 0.25), HALF)
        f += period
    for fk in list(range(f0, f1, 30)) + [f1]:
        elbow(nm, "R", fk, wpos(nm, "upperarm01.R", fk) + rgt(yaw) * 0.45 - fwd(yaw) * 0.15 + V((0, 0, -0.3)))
    if chip:
        for h in hits:
            if h + 2 <= f1: chips(h + 1, tip)
    key_age(f0, f1, age)
    return tip, hits

def lie_pose(n, f, head=(0.0, 25.0), arm_out=0.10):
    """standing-rest pose in armature space (the object is rotated -90 deg about X to lay it on its back)"""
    o = bpy.data.objects[n]; saved = o.matrix_world.copy(); o.matrix_world = Matrix.Identity(4)
    H = HUM[n]; root = V((0, 0, H.root_head.z))
    H.key_root(f, root, yaw=0.0); H.key_spine(f, flex=-2, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        a_ = H.ankle[s]; foot(n, s, f, (a_.x * 0.9 + sx * 0.02, a_.y, a_.z), sx * 8, knee=V((a_.x * 0.9, -0.7, 0.5)))
        sh = RIG[n].BN["upperarm01." + s].head_local
        palm = sh + V((sx * (0.12 + arm_out), 0.02, -0.56))
        hand(n, s, f, palm, V((-sx, 0, 0)), V((sx * 0.15, 0, -1)), pole=sh + V((sx * 0.3, 0.45, -0.3)), pose="relaxed")
    o.matrix_world = saved

def lie_at(sid, n, f0, f1, M):
    """place the lying body: M = world matrix of the body's 'bed' frame (feet at origin, head along +Y, back on +Z=0 plane)"""
    CUSTOM.setdefault(sid, set()).add(n)
    W = M @ Matrix.Translation(V((0, 0, 0.115))) @ Matrix.Rotation(R_(-90), 4, 'X')
    loc, q, _ = W.decompose(); e = q.to_euler('XYZ')
    for f in (f0, f1): key_obj(bpy.data.objects[n], f, loc, e)

# ================================================================== SHOTS
YC0 = -YF + 2.6          # the cut end on day one (a shallow notch in the steep foot of the ridge)

def shot_1a(f0, n):
    """CU: hammer strikes the chisel on the rock, chips fly; his face 3/4 above the hands"""
    use = ("Man",); cut_window(f0, f0 + n - 1, YC0); show_cutface(f0, f0 + n - 1)
    tip, hits = strike("1a", f0, n, YC0, 0.0)
    c = tip + V((1.25, -0.30, 0.32)); a_ = tip + V((-0.05, -0.42, 0.16))
    camera("1a", f0, n, [(0, c, a_, 30), (1, c + V((-0.12, -0.05, -0.02)), a_ + V((0, 0, 0.02)), 32)], fstop=8.0)
    return use

def shot_1b(f0, n):
    """aerial: the rock ridge with the village at its foot; slow crane down toward the tiny worksite"""
    use = ("Man",); cut_window(f0, f0 + n - 1, YC0)
    strike("1b", f0, n, YC0, 0.0, chip=False)
    camera("1b", f0, n, [(0, (-60, -175, 95), (0, -40, 8), 30), (1, (-45, -150, 70), (0, -45, 5), 30)], fstop=11.0, catch=False)
    return use

def shot_2a(f0, n):
    """wide: the man small at the foot of the huge rock face, striking; slow push"""
    use = ("Man",); cut_window(f0, f0 + n - 1, YC0)
    tip, hits = strike("2a", f0, n, YC0, 0.0, chip=False)
    camera("2a", f0, n, [(0, (7, -70, 2.2), (0, -48, 8.5), 24), (1, (6, -67, 2.0), (0, -48, 8.0), 24)], fstop=8.0, catch=False)
    return use

def shot_2b(f0, n):
    """he walks across the grass to the rock face (the tools wait there), arms swinging"""
    use = ("Man",); f1 = f0 + n - 1; cut_window(f0, f1, YC0)
    p0, p1 = V((-4.0, -62.0, 0)), V((-0.4, -54.2, 0))
    d = (p1 - p0); L = d.length; yaw = math.degrees(math.atan2(d.x, -d.y))
    path = lambda f: p0.lerp(p1, min(1.0, (f - f0) / (n - 1)))
    HUM["Man"].walk(path, lambda f: yaw, f0, f1, stride=0.66, lift=0.07)
    for f in range(f0, f1 + 1, 12): HUM["Man"].key_spine(f, flex=5, head=(-2 + 3 * math.sin(f / 13.0), 6 * math.sin(f / 30.0)))
    walk_arms("Man", f0, f1, lambda f: yaw)
    key_age(f0, f1, 0.0)
    camera("2b", f0, n, [(0, (-8.5, -60.5, 1.5), (-3.5, -58.5, 1.1), 26), (1, (-7.5, -57.5, 1.6), (-0.8, -55.5, 1.2), 26)], fstop=8.0)
    return use

def walk_arms(n, f0, f1, yaw_fn, every=8, amp=0.16):
    for i, f in enumerate(sorted(set(list(range(f0, f1 + 1, every)) + [f1]))):
        sw = amp * math.sin((f - f0) * math.pi / 22.0)
        relaxed_arm(n, "L", f, yaw_fn(f), fwd_=0.08 + sw, up=0.13 + 0.06 * max(0.0, sw / amp))
        relaxed_arm(n, "R", f, yaw_fn(f), fwd_=0.08 - sw, up=0.13 + 0.06 * max(0.0, -sw / amp))

def laugh(n, f0, f1, pos, yaw, head_yaw=0.0, period=16, bend=0.0, point=None, hands_knees=False):
    """laughing: head tips back and forward in quick beats, shoulders shake; optional pointing arm"""
    k = 0
    for f in list(range(f0, f1, period // 2)) + [f1]:
        u = k % 2; k += 1
        pitch = (-14 if u else -4) + bend * 0.6
        body(n, f, V(pos) + V((0, 0, HUM[n].root_head.z - 0.012 - 0.006 * u - bend * 0.004)), yaw, flex=bend * 0.5,
             spine=(4 + bend + 3 * u, 3 * math.sin(k * 0.7), 0), head=(pitch, head_yaw + 4 * math.sin(k * 0.9)))
        stand_feet(n, f, pos, yaw, spread=0.03)
        if hands_knees:
            for s in "LR":
                sx = 1 if s == "L" else -1
                th = V(pos) + fwd(yaw) * 0.22 - rgt(yaw) * sx * 0.12 + V((0, 0, 0.58))
                hand(n, s, f, th, V((0, 0, -1)), fwd(yaw) * 0.6 + V((0, 0, -1)), pole=wpos(n, "upperarm01." + s, f) - rgt(yaw) * sx * 0.35 - fwd(yaw) * 0.2, pose="relaxed")
        else:
            relaxed_arm(n, "L", f, yaw, up=0.04 * u)
            if point is None: relaxed_arm(n, "R", f, yaw, up=0.04 * u)
        if point is not None:
            sh = wpos(n, "upperarm01.R", f); dr = (V(point) - sh).normalized()
            hand(n, "R", f, sh + dr * 0.56 + V((0, 0, -0.04 * u)), V((0, 0, -1)), dr, pole=sh + dr * 0.25 + V((0, 0, -0.35)) + rgt(yaw) * 0.25, pose="point")

def shot_3a(f0, n):
    """three villagers on the grass laugh at him; one points at the ridge where he works (tiny, behind them); logo crate beside them"""
    use = ("V1", "V2", "V3", "Man"); f1 = f0 + n - 1; cut_window(f0, f1, YC0)
    strike("3a", f0, n, YC0, 0.0, chip=False)
    laugh("V1", f0, f1, V((-6.2, -65.2, 0)), 160.0, head_yaw=10, point=(0, -53.5, 1.3))
    laugh("V2", f0, f1, V((-7.3, -66.0, 0)), 205.0, head_yaw=-20, period=18)
    laugh("V3", f0, f1, V((-5.0, -66.3, 0)), 140.0, head_yaw=15, period=14, bend=10)
    camera("3a", f0, n, [(0, (-3.3, -62.4, 1.55), (-6.6, -66.4, 1.15), 24), (1, (-3.5, -62.6, 1.5), (-6.6, -66.4, 1.15), 24)], fstop=8.0)
    return use

def shot_3b(f0, n):
    """closer: two villagers laughing, one bent forward with his hands on his thighs"""
    use = ("V2", "V3"); f1 = f0 + n - 1
    laugh("V2", f0, f1, V((-7.3, -66.0, 0)), 205.0, head_yaw=-30, period=18)
    laugh("V3", f0, f1, V((-5.0, -66.3, 0)), 140.0, head_yaw=25, period=14, bend=22, hands_knees=True)
    camera("3b", f0, n, [(0, (-4.9, -64.0, 1.5), (-6.3, -66.2, 1.3), 30), (1, (-5.1, -63.9, 1.47), (-6.3, -66.2, 1.28), 30)], fstop=8.0)
    return use

def shot_4a(f0, n):
    """day after day: low side view, he walks back to the rock face in the morning light"""
    use = ("Man",); f1 = f0 + n - 1; cut_window(f0, f1, YC0 + 1.2)
    p0, p1 = V((3.5, -63.0, 0)), V((0.4, -55.0, 0))
    d = (p1 - p0); yaw = math.degrees(math.atan2(d.x, -d.y))
    path = lambda f: p0.lerp(p1, min(1.0, (f - f0) / (n - 1)))
    HUM["Man"].walk(path, lambda f: yaw, f0, f1, stride=0.68, lift=0.07)
    for f in range(f0, f1 + 1, 12): HUM["Man"].key_spine(f, flex=5, head=(-4 + 3 * math.sin(f / 13.0), 0))
    walk_arms("Man", f0, f1, lambda f: yaw); key_age(f0, f1, 0.1)
    camera("4a", f0, n, [(0, (8.5, -61.5, 0.6), (2.2, -58.5, 1.6), 22), (1, (7.8, -59.0, 0.7), (1.0, -55.5, 1.8), 22)], fstop=8.0)
    return use

def shot_4b(f0, n):
    """medium side: with just a hammer and a chisel"""
    use = ("Man",); yc = YC0 + 1.2; cut_window(f0, f0 + n - 1, yc); show_cutface(f0, f0 + n - 1)
    tip, hits = strike("4b", f0, n, yc, 0.1)
    c = tip + V((1.55, -0.30, 0.35)); a_ = tip + V((0.0, -0.60, -0.1))
    camera("4b", f0, n, [(0, c, a_, 22), (1, c + V((-0.1, -0.15, 0.05)), a_, 22)], fstop=8.0)
    return use

def shot_4c(f0, n):
    """macro: the chisel edge on the rock, the hammer lands, chips fly (hands with forearms to the frame edge)"""
    use = ("Man",); yc = YC0 + 1.2; cut_window(f0, f0 + n - 1, yc); show_cutface(f0, f0 + n - 1)
    tip, hits = strike("4c", f0, n, yc, 0.1, period=40)
    c = tip + V((-1.25, -0.25, 0.35)); a_ = tip + V((0.1, -0.38, 0.12))
    camera("4c", f0, n, [(0, c, a_, 30), (1, c + V((0.08, -0.06, 0.0)), a_, 32)], fstop=8.0)
    return use

# ---- the wife (years earlier): a narrow ledge path on the ridge's west face
LEDGE_Y, LEDGE_Z, LEDGE_EDGE = sc["LEDGE"][0], sc["LEDGE"][1], sc["LEDGE"][2]
def shot_5a(f0, n):
    """years earlier: his wife walks along the narrow ledge path high on the rock face"""
    use = ("Wife",); f1 = f0 + n - 1; GZ[0] = LEDGE_Z
    p0, p1 = V((-24.0, LEDGE_Y, 0)), V((-18.5, LEDGE_Y + 0.1, 0))
    yaw = -90.0
    path = lambda f: p0.lerp(p1, min(1.0, (f - f0) / (n - 1)))
    HUM["Wife"].walk(path, lambda f: yaw, f0, f1, stride=0.55, lift=0.06)
    for f in range(f0, f1 + 1, 12): HUM["Wife"].key_spine(f, flex=4, head=(4 + 3 * math.sin(f / 14.0), -12 + 8 * math.sin(f / 35.0)))
    walk_arms("Wife", f0, f1, lambda f: yaw, amp=0.12)
    camera("5a", f0, n, [(0, (-15.6, LEDGE_Y - 3.4, LEDGE_Z + 0.7), (-21.0, LEDGE_Y, LEDGE_Z + 1.0), 26), (1, (-15.4, LEDGE_Y - 3.3, LEDGE_Z + 0.8), (-19.5, LEDGE_Y, LEDGE_Z + 1.0), 26)], fstop=8.0)
    GZ[0] = 0.0
    return use

def shot_5b(f0, n):
    """her foot slips at the crumbling edge: stones break away (cut before any fall)"""
    use = ("Wife",); f1 = f0 + n - 1; GZ[0] = LEDGE_Z
    p0 = V((-18.0, LEDGE_EDGE + 0.45, 0)); yaw = -90.0
    for k, f in enumerate((f0, f0 + 25, f0 + 45, f1)):
        u = ss((f - f0 - 20) / 30.0)
        body("Wife", f, p0 + V((0, -0.05 * u, LEDGE_Z + HUM["Wife"].root_head.z - 0.01 - 0.06 * u)), yaw, flex=4 - 8 * u, side=-10 * u, spine=(4, 0, -8 * u), head=(10 + 25 * u, -10))
        foot("Wife", "L", f, (p0.x - 0.1, p0.y + 0.1, GZ[0] + HUM["Wife"].ankle["L"].z), yaw)
        rf = V((p0.x + 0.15, p0.y - 0.12 - 0.22 * u, GZ[0] + HUM["Wife"].ankle["R"].z - 0.05 * u))
        foot("Wife", "R", f, rf, yaw - 10 * u, pitch=-15 * u)
        relaxed_arm("Wife", "L", f, yaw, out=0.04 + 0.2 * u, up=0.25 * u, pose="open_alarm" if u > 0.5 else "relaxed")
        relaxed_arm("Wife", "R", f, yaw, out=0.04 + 0.2 * u, up=0.25 * u, pose="open_alarm" if u > 0.5 else "relaxed")
    for i in range(5):     # pebbles break off the edge under her foot
        src = "Chip%d" % (i % 6); o = bpy.data.objects[src].copy(); o.name = "Pebble5b_%d" % i; bpy.data.objects[src].users_collection[0].objects.link(o)
        o.animation_data_clear(); o.scale = (3, 3, 3); p_ = V((-17.9 + 0.08 * i, LEDGE_EDGE + 0.06, LEDGE_Z + 0.03))
        for j in range(0, 50, 3):
            t = max(0, j - 24) / 60.0; o.location = p_ + V((0, -0.5 * t, -4.9 * max(0.0, t - 0.15) ** 2)); o.rotation_euler = (j * 0.2, 0, 0)
            o.keyframe_insert("location", frame=f0 + j); o.keyframe_insert("rotation_euler", frame=f0 + j)
        key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, f1 + 1, False)
    camera("5b", f0, n, [(0, (-16.9, LEDGE_EDGE - 1.5, LEDGE_Z + 0.25), (-17.9, LEDGE_EDGE + 0.3, LEDGE_Z + 0.35), 30), (1, (-17.0, LEDGE_EDGE - 1.6, LEDGE_Z + 0.3), (-17.9, LEDGE_EDGE + 0.3, LEDGE_Z + 0.5), 30)], fstop=8.0)
    GZ[0] = 0.0
    return use

def shot_5c(f0, n):
    """stones tumble down the rock face (no person on screen)"""
    use = (); f1 = f0 + n - 1
    for i in range(7):
        src = "Chip%d" % (i % 6); o = bpy.data.objects[src].copy(); o.name = "Stone5c_%d" % i; bpy.data.objects[src].users_collection[0].objects.link(o)
        o.animation_data_clear(); s_ = random.uniform(4, 8); o.scale = (s_, s_, s_)
        p_ = V((-17.6 + random.uniform(-0.5, 0.5), LEDGE_EDGE - 0.3, LEDGE_Z - 0.2 + random.uniform(0, 0.6)))
        for j in range(0, n + 6, 3):
            t = (j + 6 * i) / 60.0; z = p_.z - 4.9 * t * t * 0.45
            yy = p_.y - 1.6 * t
            z = max(z, 0.08); o.location = (p_.x + 0.3 * math.sin(t * 5 + i), yy, z); o.rotation_euler = (j * 0.25, j * 0.1 * i, 0)
            o.keyframe_insert("location", frame=f0 + j); o.keyframe_insert("rotation_euler", frame=f0 + j)
        key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, f1 + 1, False)
    camera("5c", f0, n, [(0, (-13.0, -60.5, 1.6), (-17.5, LEDGE_Y - 2.0, LEDGE_Z - 1.5), 28), (1, (-13.2, -60.9, 1.4), (-17.5, LEDGE_Y - 3.0, 2.0), 28)], fstop=8.0, catch=False)
    return use

def shot_5d(f0, n):
    """she lies on the grass at the foot of the rock, badly injured (eyes closed, no close-up); slow push from the side"""
    use = ("Wife",); f1 = f0 + n - 1
    for f in (f0, f1): lie_pose("Wife", f, head=(0, -25), arm_out=0.16)
    M = Matrix.Translation(V((-18.5, -58.2, 0.0))) @ Matrix.Rotation(R_(-75), 4, 'Z')
    lie_at("5d", "Wife", f0, f1, M)
    camera("5d", f0, n, [(0, (-16.0, -61.6, 2.4), (-17.7, -58.7, 0.3), 28), (1, (-16.3, -61.0, 2.1), (-17.7, -58.7, 0.3), 30)], fstop=8.0)
    return use

# ---- map views (aerial, no text)
def shot_6a(f0, n):
    """map: a blue arrow grows straight from the village toward the hospital; a red X stamps it at the ridge"""
    use = (); f1 = f0 + n - 1
    sh, hd = bpy.data.objects["ArrowBlue_Shaft"], bpy.data.objects["ArrowBlue_Head"]
    for o in (sh, hd): key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, f1 + 1, False)
    for f, L in ((f0, 0.5), (f0 + 10, 0.5), (f0 + int(n * 0.5), 145.0), (f1, 145.0)):
        sh.scale = (1, L, 1); sh.keyframe_insert("scale", frame=f)
        hd.location = (0, -66 + L - 0.5, 40); hd.keyframe_insert("location", frame=f)
    xr = bpy.data.objects["RedX"]
    for o in xr.children: key_vis(o, 1, False); key_vis(o, f0 + int(n * 0.55), True); key_vis(o, f1 + 1, False)
    for f, s_ in ((f0, 0.01), (f0 + int(n * 0.55), 0.01), (f0 + int(n * 0.55) + 8, 1.25), (f0 + int(n * 0.55) + 14, 1.0), (f1, 1.0)):
        xr.scale = (s_, s_, s_); xr.keyframe_insert("scale", frame=f)
    camera("6a", f0, n, [(0, (0, -40, 330), (0, 5, 0), 26), (1, (0, -30, 300), (0, 8, 0), 26)], fstop=11.0, catch=False)
    return use

ROAD = [V((p[0], p[1], 0)) for p in sc["ROAD"]]
def road_at(x_target):
    """point and direction on the straight village stretch of the road nearest to x"""
    best = min(range(len(ROAD) - 1), key=lambda i: abs(ROAD[i].x - x_target) if ROAD[i].y < -50 else 1e9)
    p = ROAD[best]; d = (ROAD[best + 1] - ROAD[best]).normalized(); return p, d

def drag(sid, f0, n, x0, speed=0.012):
    """the man pulls his wife on the bamboo drag-stretcher along the road (poles in his hands at hip height, rear ends on the road)"""
    nm = "Man"; f1 = f0 + n - 1
    st = copy_tree("Stretcher", "Stretcher_" + sid, f0, f1)
    p_, d = road_at(x0); side = V((-d.y, d.x, 0)); off = side * 1.6
    TIPF = 0.16      # pole tips this far ahead of the pelvis line (hands hang slightly forward while pulling)
    yaw = math.degrees(math.atan2(d.x, -d.y))
    path = lambda f: p_ + off + d * (speed * (f - f0))
    HUM[nm].walk(path, lambda f: yaw, f0, f1, stride=0.52, lift=0.06, lean=18.0, crouch=0.05)
    for f in range(f0, f1 + 1, 10): HUM[nm].key_spine(f, flex=14, head=(-8 + 3 * math.sin(f / 11.0), 0))
    hz = HUM[nm].root_head.z - 0.30            # grip height (hands at the hips, arms hanging)
    tilt = math.asin((hz - 0.03) / 2.6)
    for i, f in enumerate(sorted(set(list(range(f0, f1 + 1, 2)) + [f1]))):
        tipc = path(f) + d * TIPF
        Ms = Matrix.Translation(tipc - d * 2.6 * math.cos(tilt) + V((0, 0, 0.0))) @ Matrix.Rotation(math.atan2(-d.x, d.y), 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X')
        loc, q, _ = Ms.decompose(); key_obj(st, f, loc, q.to_euler('XYZ'))
        if f in (f0, f1) or i % 2 == 0:
            for s in "LR":
                sx = 1 if s == "L" else -1
                pt = Ms @ V(((0.31 if (rgt(yaw).dot(Ms.to_3x3() @ V((1, 0, 0))) < 0) == (s == "L") else -0.31), 2.48, 0.028))
                inward = (path(f) - pt); inward.z = 0; inward.normalize()
                hand(nm, s, f, pt - inward * 0.032, inward, V((0, 0, -1)), pole=pt + V((0, 0, 0.3)) - inward * 0.3 + d * -0.25, pose="wrap_grip")
        if f == f0 or f == f1 or i % 2 == 0:
            for f_ in (f,):
                lie_pose("Wife", f_, head=(0, 20), arm_out=0.02)
                W = Ms @ Matrix.Translation(V((0, 0.35, 0.06))) @ Matrix.Translation(V((0, 0, 0.115))) @ Matrix.Rotation(R_(-90), 4, 'X')
                loc, q, _ = W.decompose(); key_obj(bpy.data.objects["Wife"], f_, loc, q.to_euler('XYZ'))
    CUSTOM.setdefault(sid, set()).add("Wife")
    key_age(f0, f1, 0.0)
    return path, d, yaw, st

def shot_7a(f0, n):
    """side tracking: he drags her on the bamboo stretcher along the long road round the mountain"""
    use = ("Man", "Wife"); path, d, yaw, st = drag("7a", f0, n, 10.0)
    side = V((-d.y, d.x, 0))
    c0 = path(f0) - side * 5.2 + V((0, 0, 1.3)) - d * 0.9; c1 = path(f0 + n - 1) - side * 5.2 + V((0, 0, 1.3)) - d * 0.9
    camera("7a", f0, n, [(0, c0, path(f0) - d * 0.9 + V((0, 0, 0.8)), 26), (1, c1, path(f0 + n - 1) - d * 0.9 + V((0, 0, 0.8)), 26)], fstop=8.0)
    return use

def shot_7b(f0, n):
    """map: the white route line draws along the road, all the way round the ridge's far end to the hospital"""
    use = (); f1 = f0 + n - 1
    rl = bpy.data.objects["RouteLine"]; key_vis(rl, 1, False); key_vis(rl, f0, True); key_vis(rl, f1 + 1, False)
    cu = rl.data
    for f, e in ((f0, 0.0), (f0 + 6, 0.0), (f0 + int(n * 0.85), 1.0), (f1, 1.0)):
        cu.bevel_factor_end = e; cu.keyframe_insert("bevel_factor_end", frame=f)
    cu.bevel_factor_start = 0.0
    camera("7b", f0, n, [(0, (120, -60, 640), (120, 10, 0), 24), (1, (120, -50, 600), (120, 12, 0), 24)], fstop=11.0, catch=False)
    return use

def shot_7c(f0, n):
    """front three-quarter: he leans into the pull, the stretcher behind him"""
    use = ("Man", "Wife"); path, d, yaw, st = drag("7c", f0, n, 30.0)
    side = V((-d.y, d.x, 0))
    c0 = path(f0) + d * 4.6 - side * 1.8 + V((0, 0, 1.45)); c1 = c0 - d * 0.9
    camera("7c", f0, n, [(0, c0, path(f0) - d * 0.6 + V((0, 0, 1.0)), 28), (1, c1, path(f0 + n - 1) - d * 0.8 + V((0, 0, 1.0)), 28)], fstop=8.0)
    return use

def death_setup(sid, f0, n):
    """the stretcher lies flat on the road verge, she lies on it; he kneels at her side"""
    f1 = f0 + n - 1; st = copy_tree("Stretcher", "Stretcher_" + sid, f0, f1)
    p_, d = road_at(40.0); side = V((-d.y, d.x, 0)); base = p_ + side * 2.2
    Ms = Matrix.Translation(base) @ Matrix.Rotation(math.atan2(-d.x, d.y), 4, 'Z')
    loc, q, _ = Ms.decompose()
    for f in (f0, f1): key_obj(st, f, loc, q.to_euler('XYZ'))
    for f in (f0, f1): lie_pose("Wife", f, head=(0, 22), arm_out=0.02)
    lie_at(sid, "Wife", f0, f1, Ms @ Matrix.Translation(V((0, 0.35, 0.06))))
    return Ms, d, side

def shot_8a(f0, n):
    """he kneels beside the stretcher on the roadside; his hand rests on the bamboo pole; she lies still (no close-up)"""
    use = ("Man", "Wife"); f1 = f0 + n - 1
    Ms, d, side = death_setup("8a", f0, n)
    knees = Ms @ V((-0.62, 1.5, 0)); yaw = math.degrees(math.atan2((Ms.to_3x3() @ V((1, 0, 0))).x, -(Ms.to_3x3() @ V((1, 0, 0))).y))
    for k, f in enumerate(list(range(f0, f1, 40)) + [f1]):
        u = ss((f - f0) / (n * 0.6))
        kneel("Man", f, knees, yaw, lean=14 + 10 * u, spine=(18 + 10 * u, 0, 0), head=(22 + 18 * u, -5))
        pole_pt = Ms @ V((-0.31, 1.25, 0.06))
        hand("Man", "R", f, pole_pt, V((0, 0, -1)), (Ms.to_3x3() @ V((1, 0.3, 0))).normalized(), pole=wpos("Man", "upperarm01.R", f) + rgt(yaw) * 0.3 - fwd(yaw) * 0.25, pose="wrap_grip")
        th = V((knees[0], knees[1], 0)) + fwd(yaw) * 0.05 - rgt(yaw) * -0.13 + V((0, 0, 0.33))
        hand("Man", "L", f, th, V((0, 0, -1)), fwd(yaw), pole=wpos("Man", "upperarm01.L", f) + rgt(yaw) * -0.35 - fwd(yaw) * 0.2, pose="relaxed")
    key_age(f0, f1, 0.0)
    c = Ms @ V((3.2, 2.6, 1.45)); a_ = Ms @ V((-0.55, 1.3, 0.55))
    camera("8a", f0, n, [(0, c, a_, 28), (1, c + (a_ - c).normalized() * 0.5, a_, 28)], fstop=8.0)
    return use

def shot_8b(f0, n):
    """closer on him: head bowed, then lifts a little; her body out of focus range, only her sari at the frame edge"""
    use = ("Man", "Wife"); f1 = f0 + n - 1
    Ms, d, side = death_setup("8b", f0, n)
    knees = Ms @ V((-0.62, 1.5, 0)); xax = Ms.to_3x3() @ V((1, 0, 0)); yaw = math.degrees(math.atan2(xax.x, -xax.y))
    for k, f in enumerate(list(range(f0, f1, 40)) + [f1]):
        u = ss((f - f0) / (n * 0.8))
        kneel("Man", f, knees, yaw, lean=24 - 6 * u, spine=(28 - 8 * u, 0, 0), head=(40 - 22 * u, -5 + 4 * u))
        pole_pt = Ms @ V((-0.31, 1.25, 0.06))
        hand("Man", "R", f, pole_pt, V((0, 0, -1)), (Ms.to_3x3() @ V((1, 0.3, 0))).normalized(), pole=wpos("Man", "upperarm01.R", f) + rgt(yaw) * 0.3 - fwd(yaw) * 0.25, pose="wrap_grip")
        th = V((knees[0], knees[1], 0)) + fwd(yaw) * 0.05 + rgt(yaw) * 0.13 + V((0, 0, 0.33))
        hand("Man", "L", f, th, V((0, 0, -1)), fwd(yaw), pole=wpos("Man", "upperarm01.L", f) - rgt(yaw) * 0.35 - fwd(yaw) * 0.2, pose="relaxed")
    key_age(f0, f1, 0.0)
    hd = wpos("Man", "head", f0)
    c = hd + rgt(yaw) * 1.3 - fwd(yaw) * 0.05 + V((0, 0, 0.05)); a_ = hd + V((0, 0, -0.08))
    camera("8b", f0, n, [(0, c, a_, 38), (1, c + (a_ - c).normalized() * 0.2, a_, 38)], fstop=8.0)
    return use

def shot_9a(f0, n):
    """he stands at the foot of the mountain, turns and looks up at it with resolve; low angle"""
    use = ("Man",); f1 = f0 + n - 1; cut_window(f0, f1, YC0)
    pos = V((0.6, -58.5, 0))
    for k, f in enumerate(list(range(f0, f1, 30)) + [f1]):
        u = ss((f - f0) / (n * 0.7))
        yaw = 150 + 30 * u
        body("Man", f, pos + V((0, 0, HUM["Man"].root_head.z - 0.01 + 0.004 * (k % 2))), yaw, spine=(-2 - 3 * u, 0, 0), head=(-6 - 16 * u, 10 - 10 * u))
        stand_feet("Man", f, pos, yaw)
        relaxed_arm("Man", "L", f, yaw, pose="power_fist" if u > 0.6 else "relaxed"); relaxed_arm("Man", "R", f, yaw, pose="power_fist" if u > 0.6 else "relaxed")
    key_age(f0, f1, 0.05)
    camera("9a", f0, n, [(0, (2.6, -61.6, 0.55), (0.3, -57.5, 2.4), 24), (1, (2.2, -61.0, 0.5), (0.2, -57.5, 2.6), 24)], fstop=8.0)
    return use

def shot_9b(f0, n):
    """close: his face, set and determined, the rock wall behind him"""
    use = ("Man",); f1 = f0 + n - 1; cut_window(f0, f1, YC0)
    pos = V((0.6, -58.5, 0)); yaw = 180.0
    for k, f in enumerate(list(range(f0, f1, 30)) + [f1]):
        u = ss((f - f0) / n)
        body("Man", f, pos + V((0, 0, HUM["Man"].root_head.z - 0.01 + 0.004 * (k % 2))), yaw - 20 * (1 - u), spine=(-4, 0, 0), head=(-18 + 6 * u, 12 * (1 - u)))
        stand_feet("Man", f, pos, yaw); relaxed_arm("Man", "L", f, yaw, pose="power_fist"); relaxed_arm("Man", "R", f, yaw, pose="power_fist")
    key_age(f0, f1, 0.05)
    hd = wpos("Man", "head", f0)
    c = hd + V((0.35, 1.15, -0.30)); a_ = hd + V((0, 0, -0.02))
    camera("9b", f0, n, [(0, c, a_, 40), (1, c + V((-0.05, 0.15, 0.0)), a_ + V((0, 0, 0.02)), 40)], fstop=8.0)
    return use

def shot_10a(f0, n):
    """aerial time-lapse: the cut creeps through the ridge, year after year"""
    use = (); f1 = f0 + n - 1
    for f in range(f0, f1 + 1, 2): key_cut(f, YC0 + (30.0 - YC0) * ss((f - f0) / (n - 1)))
    key_cut(f1, 30.0)
    camera("10a", f0, n, [(0, (-42, -80, 75), (0, -10, 0), 28), (1, (-36, -70, 68), (0, -5, 0), 28)], fstop=11.0, catch=False)
    return use

def shot_10b(f0, n):
    """deep in the gorge, his hair greying: still striking"""
    use = ("Man",); yc = 8.0; cut_window(f0, f0 + n - 1, yc); show_cutface(f0, f0 + n - 1)
    tip, hits = strike("10b", f0, n, yc, 0.45)
    c = tip + V((1.55, -0.30, 0.35)); a_ = tip + V((0.0, -0.62, 0.0))
    camera("10b", f0, n, [(0, c, a_, 20), (1, c + V((0.0, -0.12, 0.0)), a_, 20)], fstop=8.0)
    return use

def shot_10c(f0, n):
    """older now, white-bearded: the strike, closer"""
    use = ("Man",); yc = 38.0; cut_window(f0, f0 + n - 1, yc); show_cutface(f0, f0 + n - 1)
    tip, hits = strike("10c", f0, n, yc, 0.85)
    c = tip + V((-1.45, -0.25, 0.42)); a_ = tip + V((0.1, -0.62, 0.25))
    camera("10c", f0, n, [(0, c, a_, 26), (1, c + V((0.06, -0.08, 0.0)), a_, 28)], fstop=8.0)
    return use

# ---- the last wall: a rock slab across the cut end that breaks and falls outward
M_RCU = bpy.data.materials["M_RockCU"]
SLAB_Y = YF - 1.6
SLABS = []
for i, (x, z, w, h) in enumerate(((-0.95, 1.0, 1.7, 2.0), (0.9, 1.0, 1.8, 2.0), (-0.9, 3.0, 1.8, 2.0), (0.95, 3.0, 1.7, 2.0))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, SLAB_Y, z)); o = bpy.context.active_object; o.name = "Slab%d" % i
    o.scale = (w, 0.7, h); bpy.ops.object.transform_apply(scale=True); o.data.materials.append(M_RCU)
    bv = o.modifiers.new("B", 'BEVEL'); bv.width = 0.08; bv.segments = 2
    o.hide_render = o.hide_viewport = True; SLABS.append(o)

def shot_11a(f0, n):
    """the last wall: his final blows crack the slab, it falls outward, daylight and the plain beyond pour in"""
    use = ("Man",); f1 = f0 + n - 1; yc = SLAB_Y - 0.35
    cut_window(f0, f1, YF + 6.0)
    tip, hits = strike("11a", f0, min(n, 100), yc, 0.95, chip=True)
    br = f0 + 100
    for f in range(f0 + 100, f1 + 1, 4):     # after the last blow he lowers the tools and watches
        pass
    for i, o in enumerate(SLABS):
        key_vis(o, 1, False); key_vis(o, f0, True); key_vis(o, f1 + 1, False)
        p0 = o.location.copy()
        for j in range(0, n, 3):
            t = max(0, j - 100 - 3 * i) / 60.0
            o.location = p0 + V((0.2 * (o.location.x), 1.2 * t, -min(p0.z - 0.5, 4.9 * t * t * 1.4))); o.rotation_euler = (R_(min(80, 160 * t)), 0, 0)
            o.keyframe_insert("location", frame=f0 + j); o.keyframe_insert("rotation_euler", frame=f0 + j)
            o.location = p0
    # after the break the man stands back, tools lowered (the strike rig keeps him at the face; hold the last pose)
    c = V((1.2, yc - 3.4, 1.7)); a_ = V((0.0, SLAB_Y + 0.5, 1.7))
    camera("11a", f0, n, [(0, c, a_, 24), (1, c + V((-0.3, 0.6, 0)), a_, 24)], fstop=8.0)
    return use

def shot_11b(f0, n):
    """he walks out through the finished passage toward the light; camera follows behind and to the side"""
    use = ("Man",); f1 = f0 + n - 1; cut_window(f0, f1, YF + 6.0)
    p0, p1 = V((0.2, 44.0, 0)), V((0.2, 44.0 + 0.0115 * n * 60 / 60, 0))
    path = lambda f: p0.lerp(p1, (f - f0) / (n - 1))
    HUM["Man"].walk(path, lambda f: 180.0, f0, f1, stride=0.6, lift=0.06)
    for f in range(f0, f1 + 1, 12): HUM["Man"].key_spine(f, flex=4, head=(-6 + 3 * math.sin(f / 13.0), 15 * math.sin(f / 40.0)))
    walk_arms("Man", f0, f1, lambda f: 180.0); key_age(f0, f1, 0.95)
    camera("11b", f0, n, [(0, (0.9, 39.8, 1.75), (0.0, 47.0, 1.3), 26), (1, (0.9, 40.8, 1.75), (0.0, 48.5, 1.3), 26)], fstop=8.0)
    return use

def shot_12a(f0, n):
    """aerial along the finished passage: a green two-headed arrow spans it end to end (as long as a football field)"""
    use = (); f1 = f0 + n - 1; cut_window(f0, f1, YF + 6.0)
    ga = bpy.data.objects["Arrow_Green"]; key_vis(ga, 1, False); key_vis(ga, f0 + 10, True); key_vis(ga, f1 + 1, False)
    for f, s_ in ((f0, 0.02), (f0 + 10, 0.02), (f0 + 50, 1.0), (f1, 1.0)):
        ga.scale = (1, s_, 1); ga.location = (0, -YF * s_, 33); ga.keyframe_insert("scale", frame=f); ga.keyframe_insert("location", frame=f)
    camera("12a", f0, n, [(0, (-38, -95, 85), (0, 0, 10), 26), (1, (-30, -88, 80), (0, 2, 10), 26)], fstop=11.0, catch=False)
    return use

def shot_13a(f0, n):
    """a quick route: two villagers walk through the passage toward the hospital beyond it"""
    use = ("V1", "V2"); f1 = f0 + n - 1; cut_window(f0, f1, YF + 6.0)
    for nm, x, y0 in (("V1", -0.45, 30.0), ("V2", 0.5, 29.0)):
        p0 = V((x, y0, 0)); p1 = p0 + V((0, 0.012 * n, 0))
        path = lambda f, p0=p0, p1=p1: p0.lerp(p1, (f - f0) / (n - 1))
        HUM[nm].walk(path, lambda f: 180.0, f0, f1, stride=0.62, lift=0.06)
        for f in range(f0, f1 + 1, 12): HUM[nm].key_spine(f, flex=4, head=(-4, 10 * math.sin((f + y0) / 30.0)))
        walk_arms(nm, f0, f1, lambda f: 180.0)
    camera("13a", f0, n, [(0, (0.4, 24.5, 2.0), (0.0, 36.0, 1.4), 24), (1, (0.4, 26.0, 2.0), (0.0, 38.0, 1.4), 24)], fstop=8.0)
    return use

def shot_13b(f0, n):
    """at the hospital: the villagers walk to the door; the old man watches from beside the crate (logo)"""
    use = ("V1", "V2", "Man"); f1 = f0 + n - 1; cut_window(f0, f1, YF + 6.0)
    for nm, x, y0 in (("V1", -1.0, 82.0), ("V2", 0.2, 81.0)):
        p0 = V((x, y0, 0)); p1 = p0 + V((0, 0.014 * n, 0))
        path = lambda f, p0=p0, p1=p1: p0.lerp(p1, (f - f0) / (n - 1))
        HUM[nm].walk(path, lambda f: 180.0, f0, f1, stride=0.62, lift=0.06)
        walk_arms(nm, f0, f1, lambda f: 180.0)
    stand_idle("Man", f0, f1, V((3.2, 87.0, 0)), 200.0, head_fn=lambda f: (4, -30 + 20 * ss((f - f0) / n)))
    key_age(f0, f1, 0.95)
    camera("13b", f0, n, [(0, (6.6, 83.6, 1.55), (2.6, 89.5, 1.3), 24), (1, (6.4, 84.0, 1.55), (2.4, 89.8, 1.35), 24)], fstop=8.0)
    return use

def shot_13c(f0, n):
    """close: the old man's face, a quiet nod, the hospital behind him"""
    use = ("Man",); f1 = f0 + n - 1
    pos = V((3.2, 87.0, 0)); yaw = 20.0
    for k, f in enumerate(list(range(f0, f1, 20)) + [f1]):
        nod = 8 * math.sin((f - f0) / 14.0) if 40 < f - f0 < 110 else 0
        body("Man", f, pos + V((0, 0, HUM["Man"].root_head.z - 0.01 + 0.004 * (k % 2))), yaw, spine=(2, 0, 0), head=(nod - 4, -8))
        stand_feet("Man", f, pos, yaw); relaxed_arm("Man", "L", f, yaw); relaxed_arm("Man", "R", f, yaw)
    key_age(f0, f1, 0.95)
    hd = wpos("Man", "head", f0)
    c = hd + fwd(yaw) * 1.3 + rgt(yaw) * 0.3 + V((0, 0, -0.12)); a_ = hd + V((0, 0, -0.05))
    camera("13c", f0, n, [(0, c, a_, 40), (1, c + (a_ - c).normalized() * 0.25, a_, 40)], fstop=8.0)
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
    for n in CH:
        if n in CUSTOM.get(s_["id"], set()): continue
        o = bpy.data.objects[n]; f0, f1 = s_["f0"], s_["f0"] + s_["len"] - 1
        act = n in used[s_["id"]]
        for f in (f0, f1): key_obj(o, f, (0, 0, 0) if act else PARK[n], (0, 0, 0))
for o in bpy.data.objects:
    ad = o.animation_data
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        if fc.data_path in ("location", "rotation_euler") and o.type == 'ARMATURE':
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
                        if fc.data_path in ("hide_render", "hide_viewport") or (o.name in ("Cutter", "Man.beard") and fc.data_path in ("location", "scale")):
                            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# Age values: constant between shots (no greying drift across a cut)
for m in AGE_MATS:
    ad = m.node_tree.animation_data
    if ad and ad.action:
        for layer in getattr(ad.action, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHOTS_OK", list(used))
