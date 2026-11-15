"""Animation + camera for every shot. blender -b work/sets.blend -P 03_anim.py -- <out.blend> [timing.json]
Each shot's action is keyed at 1x from the shot's start frame and runs ~30% past its planned length (trimmed by the next cut).
Phase 2: timing.json {"S1": seconds, ...} replaces the reference start times; nothing is time-stretched."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "hand_poses.py")).read())
def ground_z(x, y): return 0.0
args = sys.argv[sys.argv.index("--") + 1:]; out = args[0]
FPS = 60
# reference start seconds (Phase 1); the last entry is the film end
T = {"S1": 0.0, "S2": 2.0, "S3": 4.0, "S4": 6.0, "S5": 8.5, "S6": 11.0, "S7": 12.0, "S8": 14.0, "S9": 17.0, "S10": 18.0, "S11": 19.0,
     "S12": 21.0, "S13": 23.0, "S14": 25.0, "S15": 27.0, "S16": 30.0, "S17": 33.0, "S18": 34.0, "S19": 36.0, "S20": 37.0, "S21": 39.0,
     "S22": 40.0, "END": 43.5}
if len(args) > 1: T.update(json.load(open(args[1])))
ORDER = ["S%d" % i for i in range(1, 23)]
F = {k: 1 + round(v * FPS) for k, v in T.items()}
def f0(s): return F[s]
def f1(s): i = ORDER.index(s); return (F[ORDER[i + 1]] if i + 1 < len(ORDER) else F["END"]) - 1
def dur(s): return f1(s) - f0(s) + 1
CONT = {"S1", "S2", "S4", "S7", "S9", "S11", "S12", "S19"}     # the next shot reuses this shot's characters/props: no overrun into it
def fx(s, extra=1.3): return f1(s) + 1 if s in CONT else f0(s) + int(dur(s) * extra)       # action end (30% longer than planned)
sc.frame_start = 1; sc.frame_end = F["END"]
OB = bpy.data.objects
ev(1)

# ------------------------------------------------------------------ characters
CH = {}
for n in ("Father", "Boy", "Mother", "Neighbour", "Dad2", "Worker"):
    r = Rig(OB[n]); CH[n] = Human(r)
    OB[n].animation_data_create()
PARK = Matrix.Translation((0, -5000, -500))

def put(n, s_list):
    """rig object placement per shot: [(shot, world_xy_z, yaw_deg or Matrix)] -> constant keys; parked elsewhere"""
    o = OB[n]; o.rotation_mode = 'QUATERNION'
    marks = []
    PK = Matrix.Translation((list(CH).index(n) * 40.0, -5000, -500))
    starts = sorted(f0(s) for s, _, _ in s_list)
    for s, pos, yaw in s_list:
        M = yaw if isinstance(yaw, Matrix) else Matrix.Translation(Vector(pos)) @ Matrix.Rotation(R_(yaw), 4, 'Z')
        nxt = min([x for x in starts if x > f0(s)] or [10 ** 6])
        park = min(fx(s) + 2, nxt)                    # stays placed through its overrun (keys computed there stay valid)
        marks.append((f0(s), M))
        if park < nxt: marks.append((park, PK))
    marks.sort(key=lambda m: m[0])
    o.matrix_world = Matrix.Translation((list(CH).index(n) * 40.0, -5000, -500)); o.keyframe_insert("location", frame=0); o.keyframe_insert("rotation_quaternion", frame=0)
    for f, M in marks:
        loc, q, _ = M.decompose(); o.location = loc; o.rotation_quaternion = q
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
    constant_all(o)

def at_shot(n, s, M=None):
    """evaluate the rig at its placement for shot s (for world-space hand targets)"""
    ev(f0(s) + 1)

def stand(H, f, pos=(0, 0), yaw=0.0, flex=4, spine=4, twist=0.0, head=(4, 0), side=0.0, dz=0.0):
    H.key_root(f, Vector((pos[0], pos[1], H.root_head.z - 0.015 + dz)), yaw=yaw, flex=flex, side=side)
    H.key_spine(f, flex=spine, twist=twist, head=head)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector(pos), yaw), yaw)

def breathe(H, fa, fb, pos=(0, 0), yaw=0.0, flex=4, spine=4, head=(4, 0), step=30, amp=1.5, twist=0.0):
    for i, f in enumerate(range(fa, fb + 1, step)):
        stand(H, f, pos, yaw, flex, spine + amp * math.sin(i * 1.7), twist, (head[0] + amp * math.sin(i * 1.3), head[1]))

def arms_hang(H, f, sway=0.0):
    """relaxed hands at the thighs (local frame: character faces -Y)"""
    for s, sx in (("L", 1), ("R", -1)):
        sh = H.r.BN["upperarm01." + s].head_local
        W = Vector((sh.x + 0.05 * sx, sh.y - 0.03 + sway * sx, sh.z - 0.58))
        H.key_hand(s, f, W, Vector((0, -0.12, -1)), Vector((-sx, 0.0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.25)))
        apply_pose(H.r.o, s, "relaxed", f)

def face(H, f, brow=0.0, lid=-6, jaw=0.0):
    """tested limits: oculi offsets below -0.002 bare the eye whites; lids past -12 read as closed (blinks use -55)"""
    if lid > -50: lid = max(lid, -12.0)
    brow = min(max(brow, -0.002), 0.003)
    PB_ = H.r.PB
    for s_ in "LR":
        for b_ in ("oculi01.", "oculi02."):
            if b_ + s_ in PB_:
                pb = PB_[b_ + s_]; pb.location = (0, 0, brow); pb.keyframe_insert("location", frame=f)
        if "orbicularis03." + s_ in PB_:
            pb = PB_["orbicularis03." + s_]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(lid), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)
    pb = PB_["jaw"]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R_(jaw), 0, 0); pb.keyframe_insert("rotation_euler", frame=f)

def blinks(H, fa, fb, brow=0.0, lid=-6, every=150, ofs=20):
    for fb_ in range(fa + ofs, fb, every):
        face(H, fb_, brow, lid); face(H, fb_ + 4, brow, -55); face(H, fb_ + 9, brow, lid)

def face_point(H, kind):
    """rest-pose point on the face in rig space ('nose', 'mouth', 'chin') from the body mesh"""
    body = OB[H.r.o.name + ".body"]; eye = H.r.BN["eye.L"].head_local if "eye.L" in H.r.BN else H.r.BN["head"].head_local + Vector((0.03, -0.08, 0.1))
    co = [v.co for v in body.data.vertices if abs(v.co.x) < 0.012]
    dz = {"nose": -0.035, "mouth": -0.075, "chin": -0.11}[kind]
    band = [c for c in co if abs(c.z - (eye.z + dz)) < 0.012]
    p = min(band, key=lambda c: c.y)
    return Vector((0, p.y, p.z))

def posed(H, p_rest, bone="head"):
    """rest-space point carried by a bone's current pose (rig space)"""
    return H.r.PB[bone].matrix @ H.r.BN[bone].matrix_local.inverted() @ p_rest

def world(H, p): return H.r.o.matrix_world @ p
def local(H, p): return H.r.o.matrix_world.inverted() @ p

def follow_bone(prop, rig, bone, fa, fb, step=1):
    """prop rides on a bone from fa to fb with the offset it has at fa (Child-Of style, keyed)"""
    prop.rotation_mode = 'QUATERNION'
    ev(fa); OFF = (rig.matrix_world @ rig.pose.bones[bone].matrix).inverted() @ prop.matrix_world
    for f in list(range(fa, fb + 1, step)) + [fb]:
        ev(f); M = rig.matrix_world @ rig.pose.bones[bone].matrix @ OFF
        l_, q_, _ = M.decompose(); prop.location = l_; prop.rotation_quaternion = q_
        prop.keyframe_insert("location", frame=f); prop.keyframe_insert("rotation_quaternion", frame=f)

def grip_follow(rig, side, obj, fg, frames, contact, approach):
    """grip_object once at fg (fingers close until they touch), then the hand rides with the object (same relative IK pose)"""
    rep = grip_object(rig, side, fg, obj, contact, approach)
    ev(fg); bn = "IK_hand." + side
    rel = obj.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones[bn].matrix
    for f in frames:
        ev(f); A = rig.matrix_world.inverted() @ obj.matrix_world @ rel
        l_, q_, _ = (rig.data.bones[bn].matrix_local.inverted() @ A).decompose(); pb = rig.pose.bones[bn]
        if pb.rotation_quaternion.dot(q_) < 0: q_ = -q_
        pb.location = l_; pb.rotation_quaternion = q_
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
    return rep

def key_prop(o, f, loc=None, rot=None):
    o.rotation_mode = 'XYZ'
    if loc is not None: o.location = Vector(loc); o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = Euler([R_(a) for a in rot]); o.keyframe_insert("rotation_euler", frame=f)

for H in CH.values(): add_hand_limits(H.r.o)

# ------------------------------------------------------------------ camera (one object, keyed every frame; a cut = a jump)
cam = OB.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if cam.name not in sc.collection.objects: sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.05; cam.data.clip_end = 1500; cam.data.dof.use_dof = False; cam.data.sensor_width = 36
CAM = {}       # shot -> list of (u 0..1, loc, target, lens)
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
            cam.location = loc; cam.rotation_quaternion = (tg - loc).to_track_quat('-Z', 'Y')
            cam.data.lens = lens
            cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam.data.keyframe_insert("lens", frame=f)
    for o in (cam, cam.data):
        for fc in fcurves_of(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'

exec(open(os.path.join(HERE, "03a_street.py")).read())
exec(open(os.path.join(HERE, "03b_inside.py")).read())
exec(open(os.path.join(HERE, "03c_dump.py")).read())
exec(open(os.path.join(HERE, "03d_end.py")).read())

bake_camera()
json.dump([{"shot": s, "frame": f0(s), "end": f1(s), "seconds": T[s]} for s in ORDER], open(os.path.join(FILM, "work", "shots.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
