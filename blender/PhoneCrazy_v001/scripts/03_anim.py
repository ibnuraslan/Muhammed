"""Animation + camera for every shot. blender -b work/sets.blend -P 03_anim.py -- <out.blend> [timing.json]
One camera object, keyed every frame; a cut = a jump. Each shot's action is keyed at 1x from its start and runs ~30% past
its planned length (trimmed by the next cut). Phase 2: timing.json {"S1": seconds, ...} replaces the reference starts."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "hand_poses.py")).read())
def ground_z(x, y): return 0.0
args = sys.argv[sys.argv.index("--") + 1:]; out = args[0]
FPS = 60
T = {"S1": 0.0, "S2": 1.0, "S3": 2.0, "S4": 5.0, "S5": 6.0, "S6": 8.0, "S7": 9.0, "S8": 11.0, "S9": 14.0, "S10": 16.0, "S11": 18.0,
     "S12": 19.0, "S13": 20.0, "S14": 22.0, "S15": 24.0, "S16": 26.0, "S17": 28.0, "S18": 29.0, "S19": 31.0, "S20": 33.0, "S21": 35.0,
     "S22": 36.5, "END": 38.5}
if len(args) > 1: T.update(json.load(open(args[1])))
F = {k: 1 + round(v * FPS) for k, v in T.items()}
ORDER = sorted(["S%d" % i for i in range(1, 23)], key=lambda k: (F[k], int(k[1:])))   # VO order; a shot sharing its start frame with a later one is dropped
ORDER = [k for i, k in enumerate(ORDER) if not (i + 1 < len(ORDER) and F[ORDER[i + 1]] == F[k])]
ALL = ["S%d" % i for i in range(1, 23)]
def f0(s): return F[s]
def f1(s):
    if s not in ORDER: return F[s]          # dropped shot: zero length
    i = ORDER.index(s); return (F[ORDER[i + 1]] if i + 1 < len(ORDER) else F["END"]) - 1
def dur(s): return f1(s) - f0(s) + 1
def fx(s, extra=1.3): return f0(s) + int(dur(s) * extra)
def sec(s, t): return f0(s) + round(t * FPS)
sc.frame_start = 1; sc.frame_end = F["END"]
OB = bpy.data.objects
ev(1)
PIT = Vector((0.0, 7.0, 0.0)); PR, PD = 3.6, 2.0

# ------------------------------------------------------------------ characters: the rig object is placed per shot (constant keys); poses are keyed in rig space
NAMES = ("Foreman", "Digger", "Mate")
CH = {n: Human(Rig(OB[n])) for n in NAMES}
for n in NAMES: OB[n].animation_data_create(); add_hand_limits(OB[n])
PLACE = {n: [] for n in NAMES}
def put(n, s, pos, yaw):
    PLACE[n].append((f0(s), Vector((pos[0], pos[1], 0.0)), yaw))
def bake_places():
    for n in NAMES:
        o = OB[n]; o.rotation_mode = 'QUATERNION'
        for f, p, yaw in sorted(PLACE[n], key=lambda x: x[0]):
            o.location = p; o.rotation_quaternion = Quaternion((0, 0, 1), R_(yaw))
            o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
        constant_all(o)
def frs(a, b, step):
    r = list(range(a, b + 1, step))
    if r and r[-1] != b: r.append(b)
    return r
def stand(H, f, flex=4, spine=4, twist=0.0, head=(4, 0), side=0.0, dz=0.0):
    H.key_root(f, Vector((0, 0, H.root_head.z - 0.015 + dz)), yaw=0, flex=flex, side=side)
    H.key_spine(f, flex=spine, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector((0, 0, 0)), 0), 0)
def shoulder(H, s): return H.r.BN["upperarm01." + s].head_local
def hand_hang(H, s, f, sway=0.0, fwd=0.0):
    sx = 1 if s == "L" else -1; sh = shoulder(H, s)
    W = Vector((sh.x + 0.05 * sx, sh.y - 0.03 - fwd + sway * sx, sh.z - 0.58 + fwd * 0.3))
    H.key_hand(s, f, W, Vector((0, -0.12 - fwd, -1)), Vector((-sx, 0.0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.25)))
    apply_pose(H.r.o, s, "relaxed", f)
def hand_point(H, s, f, tgt_local):
    """index finger toward a rig-space target, forearm about 95 deg at the elbow"""
    sx = 1 if s == "L" else -1; sh = shoulder(H, s)
    d = (tgt_local - sh).normalized()
    W = sh + d * 0.46 + Vector((0.06 * sx, 0, -0.10))
    H.key_hand(s, f, W, d, Vector((-sx * 0.4, 0, -1)), pole=W + Vector((0.35 * sx, 0.45, -0.25)))
    apply_pose(H.r.o, s, "point", f)
def hand_open(H, s, f):
    """surprised open hand at belly height, palm forward-down (no claw: relaxed_even preset)"""
    sx = 1 if s == "L" else -1; sh = shoulder(H, s)
    W = Vector((sh.x + 0.02 * sx, sh.y - 0.28, sh.z - 0.38))
    H.key_hand(s, f, W, Vector((0.15 * sx, -0.6, 0.35)), Vector((0, -0.6, -0.8)), pole=W + Vector((0.4 * sx, 0.35, -0.2)))
    apply_pose(H.r.o, s, "open_alarm", f)
def face(H, f, brow=0.0, lid=-6, jaw=0.0):
    if lid > -50: lid = max(lid, -12.0)
    brow = min(max(brow, -0.002), 0.003); PB_ = H.r.PB
    for s_ in "LR":
        for b_ in ("oculi01.", "oculi02."):
            if b_ + s_ in PB_: pb = PB_[b_ + s_]; pb.location = (0, 0, brow); pb.keyframe_insert("location", frame=f)
        if "orbicularis03." + s_ in PB_:
            pb = PB_["orbicularis03." + s_]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(lid), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    pb = PB_["jaw"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(jaw), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
def blinks(H, fa, fb, brow=0.0, lid=-6, jaw=0.0, every=140, ofs=25):
    face(H, fa, brow, lid, jaw); face(H, fb, brow, lid, jaw)
    for b in range(fa + ofs, fb - 12, every):
        face(H, b, brow, lid, jaw); face(H, b + 4, brow, -55, jaw); face(H, b + 9, brow, lid, jaw)
def to_local(n, s, p):
    yaw = [y for f, q, y in PLACE[n] if f == f0(s)][0]; pos = [q for f, q, y in PLACE[n] if f == f0(s)][0]
    return Matrix.Rotation(R_(-yaw), 4, 'Z') @ (Vector(p) - pos)
def yaw_to(pos, tgt):
    d = (Vector(tgt) - Vector((pos[0], pos[1], 0))).to_2d().normalized(); return math.degrees(math.atan2(d.x, -d.y))
def idle(n, s, fa, fb, flex=4, spine=4, head=(4, 0), twist=0.0, amp=1.2, hands="hang", tgt=None, brow=0.0, jaw=0.0, head_end=None, spine_end=None):
    """breathing idle with optional head move from head -> head_end and spine -> spine_end; hands 'hang' | ('point', side) | ('open', side)"""
    H = CH[n]
    for i, f in enumerate(frs(fa, fb, 20)):
        u = smooth((f - fa) / max(1, fb - fa))
        hd = head if head_end is None else (head[0] + (head_end[0] - head[0]) * u, head[1] + (head_end[1] - head[1]) * u)
        sp = spine if spine_end is None else spine + (spine_end - spine) * u
        stand(H, f, flex, sp + amp * math.sin(i * 1.1), twist, (hd[0] + 0.8 * amp * math.sin(i * 0.9 + 1), hd[1]))
        for sd in "LR":
            if isinstance(hands, tuple) and hands[1] == sd:
                if hands[0] == "point": hand_point(H, sd, f, tgt)
                else: hand_open(H, sd, f)
            else: hand_hang(H, sd, f, sway=0.01 * math.sin(i * 0.8))
    blinks(H, fa, fb, brow=brow, jaw=jaw)

# hard hats: bone-parented to the head, seated on the scalp (lowest drop with no hat/scalp triangle overlap, then 3 mm up)
from mathutils.bvhtree import BVHTree
for n in NAMES:
    HAT = OB[n + ".hardhat"]; rig = OB[n]; bn = rig.data.bones["head"]; body = OB[n + ".body"]
    hv = {g.index for g in body.vertex_groups if g.name == "head"}
    gi = body.vertex_groups["head"].index
    hidx = {v.index for v in body.data.vertices if any(g.group == gi and g.weight > 0.5 for g in v.groups)}
    M_b = rig.matrix_world.inverted() @ body.matrix_world
    bv = [M_b @ v.co for v in body.data.vertices]
    tris = [list(p.vertices) for p in body.data.polygons if all(i in hidx for i in p.vertices)]
    head_t = BVHTree.FromPolygons(bv, tris)
    E = rig.data.bones["eye.L"].head_local; ER = rig.data.bones["eye.R"].head_local     # base-mesh coords ignore MPFB shape keys: use the eye bones
    eye_z = (E.z + ER.z) / 2; top = eye_z + 0.115; cx = (E.x + ER.x) / 2; cy = (E.y + ER.y) / 2 + 0.085
    hz = [v.co.z for v in HAT.data.vertices]; hh_ = max(hz) - min(hz)
    want = hh_                                         # keep the model's proportions
    HAT.data = HAT.data.copy()
    if True:
        HAT.data.transform(Matrix.Diagonal((1, 1, want / hh_, 1))); HAT["fitted"] = 1
    best = Vector((cx, cy + 0.004, eye_z + 0.032)); print("HAT seat", n, best, "top", top, "eye", eye_z, "zscale", want / hh_)
    desired = Matrix.Translation(best)
    HAT.parent = rig; HAT.parent_type = 'BONE'; HAT.parent_bone = "head"
    Mb = Matrix.Translation(bn.tail_local) @ bn.matrix_local.to_3x3().to_4x4()
    HAT.matrix_parent_inverse = Matrix.Identity(4); HAT.matrix_basis = Mb.inverted() @ desired

# ------------------------------------------------------------------ phone screen + vibration
PHONE = OB["Phone"]; P0 = PHONE.location.copy(); R0 = PHONE.rotation_euler.copy()
TILE = bpy.data.materials["PhoneScreen"].node_tree.nodes["Tile"]
SCHED = []          # (frame, tile)
def tiles(s, seq):
    for t, i in seq: SCHED.append((sec(s, t), i))
JIT = []            # (fa, fb): glitch shots, screen offset jitter
BUZZ = []           # (fa, fb): phone vibrates on the lid
def bake_screen():
    rnd = random.Random(4)
    SCHED.sort()
    fr = sorted(set([f for f, _ in SCHED] + [f for a, b in JIT for f in range(a, b + 1, 3)]))
    cur = 0; si = 0
    for f in range(1, F["END"] + 1):
        while si < len(SCHED) and SCHED[si][0] <= f: cur = SCHED[si][1]; si += 1
        jx = 0.0
        if any(a <= f <= b for a, b in JIT) and rnd.random() < 0.45: jx = rnd.uniform(-0.006, 0.006)
        c, r = cur % 8, cur // 8
        TILE.inputs["Location"].default_value = (c / 8 + jx, 1 - (r + 1) / 3, 0)
        TILE.inputs["Location"].keyframe_insert("default_value", frame=f)
    for fc in fcurves_of(bpy.data.materials["PhoneScreen"].node_tree.animation_data.action):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    PHONE.rotation_mode = 'XYZ'
    for f in range(1, F["END"] + 1, 2):
        on = any(a <= f <= b for a, b in BUZZ)
        ph = f * 2.1
        PHONE.location = P0 + (Vector((0.0016 * math.sin(ph * 3.1), 0.0016 * math.cos(ph * 2.3), 0.0)) if on else Vector())
        PHONE.rotation_euler = (R0.x, R0.y, R0.z + (R_(1.2) * math.sin(ph * 2.7) if on else 0.0))
        PHONE.keyframe_insert("location", frame=f); PHONE.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ excavator: continuous dig cycle (keys every 2 frames)
EXR = OB["EXC_root"]; EXC_POS = Vector((5.9, 8.0, 0.0))
EXR.location = EXC_POS + Vector((0, 0, EXR["base_off"])); EXR.rotation_euler = (0, 0, R_(90))
J = {k: OB[k] for k in ("arm_01_GEO1", "Arm_2_GEO", "claw_GEO", "shovel_GEO", "Body_GEO")}
for o in J.values(): o.rotation_mode = 'QUATERNION'
DIG = [  # (phase, boom, stick, bucket, swing)
    (0.00, 10, 26, -10, 0), (0.18, -4, 30, -25, 0), (0.38, -12, 16, 5, 0), (0.55, -8, 2, 40, 0),
    (0.72, 12, 4, 50, 0), (0.86, 16, 22, -15, 0), (1.00, 10, 26, -10, 0)]
def dig_pose(t, period=4.4, ofs=0.0):
    p = ((t + ofs) / period) % 1.0
    for a, b in zip(DIG, DIG[1:]):
        if p <= b[0]:
            u = smooth((p - a[0]) / (b[0] - a[0])); return [a[i] + (b[i] - a[i]) * u for i in range(1, 5)]
    return DIG[-1][1:]
def bake_excavator(ranges):
    """ranges: [(fa, fb, period, ofs)]"""
    for fa, fb, per, ofs in ranges:
        for f in frs(fa, fb, 2):
            bm, st, bk, sw = dig_pose((f - fa) / FPS, per, ofs)
            J["arm_01_GEO1"].rotation_quaternion = Quaternion((1, 0, 0), R_(bm))
            J["Arm_2_GEO"].rotation_quaternion = Quaternion((1, 0, 0), R_(st))
            J["shovel_GEO"].rotation_quaternion = Quaternion((1, 0, 0), R_(bk)); J["claw_GEO"].rotation_quaternion = Quaternion((1, 0, 0), R_(bk))
            for k in ("arm_01_GEO1", "Arm_2_GEO", "shovel_GEO", "claw_GEO"): J[k].keyframe_insert("rotation_quaternion", frame=f)

# ------------------------------------------------------------------ water: level + swirl keyed per frame
WATER = OB["PitWater"]; VORT = OB["Vortex"]; SWIRL = bpy.data.materials["PitWater"].node_tree.nodes["Swirl"]; SPIN = bpy.data.materials["Whirlpool"].node_tree.nodes["Spin"]
def water_r(z): u = 1 - (-z / PD) ** (1 / 1.3) if z < 0 else 1.0; return PR * math.sqrt(max(u, 0.0)) * 1.06   # edge tucked under the dirt
def key_water(f, z, swirl_deg, vort):
    vis = z > -PD + 0.08
    WATER.location = (PIT.x, PIT.y, z); r = water_r(z); WATER.scale = (r, r, 1)
    VORT.location = (PIT.x, PIT.y, z + 0.004); VORT.scale = (r * 0.6 * vort + 0.001, r * 0.6 * vort + 0.001, max(0.001, vort * 1.4))
    SWIRL.inputs["Rotation"].default_value = (0, 0, R_(swirl_deg))
    for o in (WATER, VORT):
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    SWIRL.inputs["Rotation"].keyframe_insert("default_value", frame=f)
    SPIN.outputs[0].default_value = -R_(swirl_deg) * 3.0; SPIN.outputs[0].keyframe_insert("default_value", frame=f)
    key_vis(WATER, [(f, vis)]); key_vis(VORT, [(f, vis and vort > 0.01)])

# ------------------------------------------------------------------ camera
cam = OB.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.02; cam.data.clip_end = 1500; cam.data.dof.use_dof = False; cam.data.sensor_width = 36
CAM = {}
def camshot(s, keys): CAM[s] = keys
def cam_at(s, f):
    ks = CAM[s]; u = (f - f0(s)) / max(1, dur(s) * 1.3)
    if u <= ks[0][0]: k = ks[0]; return Vector(k[1]), Vector(k[2]), k[3]
    for a, b in zip(ks, ks[1:]):
        if u <= b[0]:
            t = smooth((u - a[0]) / (b[0] - a[0])) * 0.5 + (u - a[0]) / (b[0] - a[0]) * 0.5
            return Vector(a[1]).lerp(Vector(b[1]), t), Vector(a[2]).lerp(Vector(b[2]), t), a[3] + (b[3] - a[3]) * t
    k = ks[-1]; return Vector(k[1]), Vector(k[2]), k[3]
def bake_camera():
    cam.rotation_mode = 'QUATERNION'
    for s in ORDER:
        for f in range(f0(s), f1(s) + 1):
            loc, tg, lens = cam_at(s, f)
            cam.location = loc; cam.rotation_quaternion = (tg - loc).to_track_quat('-Z', 'Y'); cam.data.lens = lens
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam.data.keyframe_insert("lens", frame=f)
    for o in (cam, cam.data):
        for fc in fcurves_of(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'

exec(open(os.path.join(HERE, "03a_shots.py")).read())

bake_places(); bake_screen(); bake_camera()
json.dump([{"shot": s, "frame": f0(s), "end": f1(s), "seconds": T[s]} for s in ORDER], open(os.path.join(FILM, "work", "shots.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("ANIM OK", F["END"])
