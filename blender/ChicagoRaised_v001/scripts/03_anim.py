"""Animation + camera for every shot. blender -b work/sets.blend -P 03_anim.py -- <out.blend> [timing.json]
Each shot's action is keyed at 1x from the shot's start frame and runs ~30% past its planned length (trimmed by the next cut).
The jack crews crank continuously from S1 to S7 (one real-time action shared by S1, S2, S4, S5, S7; S3/S6 are cut-aways).
Phase 2: timing.json {"S1": seconds, ...} replaces the reference start times; nothing is time-stretched."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "anim_lib.py")).read())
exec(open(os.path.join(FILM, "..", "pipeline", "hand_poses.py")).read())
def ground_z(x, y): return 0.0
args = sys.argv[sys.argv.index("--") + 1:]; out = args[0]
FPS = 60
T = {"S1": 0.0, "S2": 1.0, "S3": 3.0, "S4": 4.0, "S5": 5.5, "S6": 7.0, "S7": 9.0, "S8": 10.0, "S9": 12.0, "S10": 13.0, "S11": 15.0,
     "S12": 17.0, "S13": 18.0, "S14": 20.0, "S15": 21.0, "S16": 22.5, "S17": 25.0, "S18": 26.0, "S19": 28.0, "S20": 30.0, "S21": 31.0,
     "S22": 34.0, "END": 37.5}
if len(args) > 1: T.update(json.load(open(args[1])))
ORDER = sorted([k for k in T if k != "END"], key=lambda k: T[k])     # shot order follows the timing (VO)
F = {k: 1 + round(v * FPS) for k, v in T.items()}
def f0(s): return F[s]
def f1(s): i = ORDER.index(s); return (F[ORDER[i + 1]] if i + 1 < len(ORDER) else F["END"]) - 1
def dur(s): return f1(s) - f0(s) + 1
def fx(s, extra=1.3): return f0(s) + int(dur(s) * extra)
sc.frame_start = 1; sc.frame_end = F["END"]
OB = bpy.data.objects
ev(1)

CH = {}
NAMES = ("W1", "W2", "W3", "W4", "W5", "W6", "Mason", "Foreman", "Lady", "SickMan", "TownMan", "TownWoman")
for n in NAMES:
    CH[n] = Human(Rig(OB[n])); OB[n].animation_data_create()
for H in CH.values(): add_hand_limits(H.r.o)

def put_ranges(n, ranges):
    """rig object placement: [(fa, fb, world_pos, yaw_deg)] -> constant keys; parked far away outside the ranges"""
    o = OB[n]; o.rotation_mode = 'QUATERNION'
    PK = Matrix.Translation((NAMES.index(n) * 40.0 if n in NAMES else 900, -5000, -500))
    marks = [(0, PK)]
    rs = sorted(ranges, key=lambda r: r[0])
    rs = [(fa, min(fb, rs[i + 1][0] - 1) if i + 1 < len(rs) else fb, pos, yaw) for i, (fa, fb, pos, yaw) in enumerate(rs)]   # an overrun never parks over the next placement
    for fa, fb, pos, yaw in rs:
        marks.append((fa, Matrix.Translation(Vector(pos)) @ Matrix.Rotation(R_(yaw), 4, 'Z'))); marks.append((fb + 1, PK))
    for f, M in marks:
        loc, q, _ = M.decompose(); o.location = loc; o.rotation_quaternion = q
        o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
    constant_all(o)

def frs(a, b, step):
    r = list(range(a, b + 1, step))
    if r and r[-1] != b: r.append(b)
    return r

def stand(H, f, pos=(0, 0), yaw=0.0, flex=4, spine=4, twist=0.0, head=(4, 0), side=0.0, dz=0.0, feet=None):
    H.key_root(f, Vector((pos[0], pos[1], H.root_head.z - 0.015 + dz)), yaw=yaw, flex=flex, side=side)
    H.key_spine(f, flex=spine, twist=twist, head=head)
    fp = feet or (0, 0)
    for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector(fp), yaw), yaw)

def arms_hang(H, f, sway=0.0, out=0.08):
    for s, sx in (("L", 1), ("R", -1)):
        sh = H.r.BN["upperarm01." + s].head_local
        W = Vector((sh.x + out * sx, sh.y - 0.03 + sway * sx, sh.z - 0.58))
        H.key_hand(s, f, W, Vector((0, -0.12, -1)), Vector((-sx, 0.0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.25)))
        apply_pose(H.r.o, s, "relaxed", f)

def face(H, f, brow=0.0, lid=-6, jaw=0.0):
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

def key_pole(H, s, f, p_local):
    n = "Pole_elbow." + s; pb = H.r.PB[n]
    pb.location = H.r.rest(n).to_3x3().inverted() @ (p_local - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)

def grip_follow(rig, side, obj, fg, frames, contact, approach):
    rep = grip_object(rig, side, fg, obj, contact, approach, finger_radius=0.015)
    ev(fg); bn = "IK_hand." + side
    rel = obj.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones[bn].matrix
    for f in frames:
        ev(f); A = rig.matrix_world.inverted() @ obj.matrix_world @ rel
        l_, q_, _ = (rig.data.bones[bn].matrix_local.inverted() @ A).decompose(); pb = rig.pose.bones[bn]
        if pb.rotation_quaternion.dot(q_) < 0: q_ = -q_
        pb.location = l_; pb.rotation_quaternion = q_
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
    return rep

def hold_fingers(rig, s, fa, fb):
    """re-key the finger pose evaluated at fa on fb, so a later pose change never blends across the hold"""
    ev(fa)
    for pb in rig.pose.bones:
        if pb.name.endswith("." + s) and pb.name.startswith("finger"):
            pb.keyframe_insert("rotation_quaternion", frame=fb, group=pb.name)

GRIP_OFF = float(os.environ.get("GRIP_OFF", "0.04")); GRIP_POSE = os.environ.get("GRIP_POSE", "palm")
def hand_follow(rig, side, obj, fg, frames, contact, normal, finger_dir, pose):
    """palm placed `contact` facing `normal`, fingers along `finger_dir`, posed once; then the hand rides with the object (translation)"""
    place_hand(rig, side, fg, contact, normal, finger_dir); apply_pose(rig, side, pose, fg)
    ev(fg); bn = "IK_hand." + side
    rel = obj.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones[bn].matrix
    for f in frames:
        ev(f); A = rig.matrix_world.inverted() @ obj.matrix_world @ rel
        l_, q_, _ = (rig.data.bones[bn].matrix_local.inverted() @ A).decompose(); pb = rig.pose.bones[bn]
        if pb.rotation_quaternion.dot(q_) < 0: q_ = -q_
        pb.location = l_; pb.rotation_quaternion = q_
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)

def crank_palm(rig, side, bar, dx, frames, pose="cup_hold"):
    """palm resting ON the crank bar, hand aligned with the forearm (pronated, palm down) so the wrist limits never clamp it;
    the fingers reach past the bar and do not wrap it (no crossing). Two passes per frame (forearm depends on the wrist spot)."""
    up = Vector((0, 0, 1))
    if os.environ.get("NOWRISTLIM", "1") == "1":     # the target is forearm-aligned (natural); the limit clamp only tilted the palm into the bar
        c_ = rig.pose.bones["wrist." + side].constraints.get("HandLimit")
        if c_: c_.mute = True
    for f in frames:
        ev(f); b = bar.matrix_world.translation + Vector((dx, 0, 0))
        n = Vector((0, 0.15, -1)).normalized(); fd = Vector((0, 1, 0.15)).normalized()
        for it in range(3):
            P = b - n * (0.02 + float(os.environ.get("PALM_GAP", "0.008")))
            place_hand(rig, side, f, P, n, fd)
            ev(f); el = rig.matrix_world @ rig.pose.bones["lowerarm01." + side].head; wr = rig.matrix_world @ rig.pose.bones["wrist." + side].head
            fd = (wr - el).normalized()
            n = -(up - fd * up.dot(fd)).normalized()
        # de-penetration: every metacarpal/phalanx (3 samples each, ~1.1 cm flesh radius) must stay clear of the bar axis
        gap = 0.02 + float(os.environ.get("PALM_GAP", "0.008"))
        for _ in range(10):
            ev(f); Mw = rig.matrix_world; dmin = 9.0
            for pb in rig.pose.bones:
                if not pb.name.endswith("." + side) or not (pb.name.startswith("finger") or pb.name.startswith("metacarpal")): continue
                for u in (0.0, 0.5, 1.0):
                    q = Mw @ pb.head.lerp(pb.tail, u); d = math.hypot(q.y - b.y, q.z - b.z)
                    if abs(q.x - b.x) < 0.30: dmin = min(dmin, d)
            if dmin >= 0.032: break
            gap += 0.034 - dmin
            place_hand(rig, side, f, b - n * gap, n, fd)
    apply_pose(rig, side, pose, frames[0]); hold_fingers(rig, side, frames[0], frames[-1])

def grip_roll(rig, side, obj, fg, frames, contact, approach):
    """wrap grip on a bar along world X; the hand then rides the bar AND rolls about the bar axis so the wrist stays in line
    with the shoulder->bar direction (a wrap rolled about its own cylinder never cuts into it)"""
    grip_object(rig, side, fg, obj, contact, approach, finger_radius=0.015)
    def frame_at(f):
        ev(f); b = obj.matrix_world.translation.copy(); sh = rig.matrix_world @ rig.pose.bones["upperarm01." + side].head
        d = b - sh; a = math.atan2(d.z, d.y)
        return Matrix.Translation(b) @ Matrix.Rotation(a, 4, 'X')
    ev(fg); bn = "IK_hand." + side
    rel = frame_at(fg).inverted() @ rig.matrix_world @ rig.pose.bones[bn].matrix
    for f in frames:
        Fm = frame_at(f); A = rig.matrix_world.inverted() @ Fm @ rel
        l_, q_, _ = (rig.data.bones[bn].matrix_local.inverted() @ A).decompose(); pb = rig.pose.bones[bn]
        if pb.rotation_quaternion.dot(q_) < 0: q_ = -q_
        pb.location = l_; pb.rotation_quaternion = q_
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)

def key_prop(o, f, loc=None, rot=None):
    o.rotation_mode = 'XYZ'
    if loc is not None: o.location = Vector(loc); o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_euler = Euler([R_(a) for a in rot]); o.keyframe_insert("rotation_euler", frame=f)

def key_vis_all(objs, states):
    for o in objs: key_vis(o, states)

# ------------------------------------------------------------------ camera (one object, keyed every frame; a cut = a jump)
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam)
sc.camera = cam; cam.data.clip_start = 0.05; cam.data.clip_end = 3000; cam.data.dof.use_dof = False; cam.data.sensor_width = 36
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

# ================================================================== building height per shot (Bldg empty), cribbing and foundation
BLDG = OB["Bldg"]
FA_CR, FB_CR = f0("S1"), f1("S7")                      # the continuous cranking span
Z_CR0, LIFT = 1.60, 0.03                               # m, m/s while cranking
def z_crank(f): return Z_CR0 + LIFT * (f - FA_CR) / FPS
Z_S8 = 2.30; Z_TOP = 2.85
BK = sorted([(0, Z_CR0, 'CONSTANT'), (FA_CR, Z_CR0, 'LINEAR'), (FB_CR, z_crank(FB_CR), 'CONSTANT'),
      (f0("S9"), 1.85, 'LINEAR'), (f1("S9"), Z_S8, 'CONSTANT'),              # "Slowly, the buildings rose into the air"
      (f0("S8"), Z_S8, 'CONSTANT'), (f0("S11"), Z_TOP, 'CONSTANT'),
      (f0("S10"), 2.50, 'LINEAR'), (f1("S10"), Z_TOP, 'CONSTANT')])        # "Raised the buildings above the swamp"
for f, z, _ in BK:
    BLDG.location.z = z; BLDG.keyframe_insert("location", index=2, frame=f)
for fc in fcurves_of(BLDG.animation_data.action):
    for k in fc.keyframe_points:
        k.interpolation = next(i for f, z, i in BK if f == int(k.co.x))

# cribbing: per shot, the number of visible layers in each stack = what fits under the needles at that height
def crib_layers(z0): return max(0, min(14, int((z0 - 0.62) / 0.2)))
CRIBS = {}
for o in OB:
    if o.name.startswith("Crib") and ".L" in o.name:
        st, l = o.name.split(".L"); CRIBS.setdefault(st, []).append((int(l[:2]), o))
HERO_CRIB = "Crib0"; HERO_L = 5                                        # S8: the stack being built (5 layers, the timber goes on as layer 5)
def crib_state(f, z0, hero_upto=None, front=True):
    for st, lst in CRIBS.items():
        n = crib_layers(z0)
        if st == HERO_CRIB and hero_upto is not None: n = hero_upto
        if st.startswith("Crib") and not st.startswith("CribB") and not front: n = 0
        for l, o in lst: key_vis(o, [(f, l < n)])
crib_state(0, Z_CR0)
crib_state(f0("S1"), Z_CR0)
crib_state(f0("S9"), 1.85)
crib_state(f0("S8"), Z_S8, hero_upto=HERO_L)
crib_state(f0("S11"), Z_TOP, front=False)
crib_state(f0("S10"), 2.5)
COURSES = sorted([o for o in OB if o.name.startswith("FoundCourse")], key=lambda o: o.name)
key_vis_all(COURSES, [(0, False)])
NC = int((Z_TOP - 0.32) / 0.25); COURSES = COURSES[:NC]                 # top course stays under the sill
for o in [o for o in OB if o.name.startswith("Jack") or o.name.startswith("Crank") or o.name.startswith("Screw")]:
    pass

# ================================================================== S1-S7: the jack crews (continuous cranking)
JX = sorted({round(OB["CrankGrip.%d" % i]["axle"][0], 3) for i in range(20) if "CrankGrip.%d" % i in OB})
NJ = len(JX)
CREW = {"W1": 2, "W2": 1, "W3": 0, "W5": 5, "W6": 6}     # jack 3 (under the sign) and jack 4 unmanned: W4's short arms could not reach the far side of the crank without the bar cutting his palm            # worker -> jack index (centre jack 3 under the sign is unmanned)
CREW = {k: v for k, v in CREW.items() if v < NJ}
OMEGA = 2 * math.pi * 0.5                                              # rad/s (one turn per 2 s)
def theta(f, ph=0.0): return ph + OMEGA * (f - FA_CR) / FPS            # 0 = grip toward the worker, 90 deg = bottom
FRAMES_CR = list(range(FA_CR - 1, FB_CR + 2))
for n_ in [n for n in ("W1", "W2", "W3", "W4", "W5", "W6") if n not in CREW]: put_ranges(n_, [])      # unused workers parked off-set for the whole film
for i in sorted(CREW.values()):          # unmanned cranks (jacks 3 and 4) stay still
    g = OB["CrankGrip.%d" % i]; P = OB["CrankPivot.%d" % i]; ax_ = Vector(g["axle"]); r_ = g["radius"]
    for f in FRAMES_CR:
        th = theta(f)
        key_prop(g, f, ax_ + r_ * Vector((0, -math.cos(th), -math.sin(th))))
        key_prop(P, f, None, (math.degrees(th) - 90.0, 0, 0))
    for o in (g, P):
        for fc in fcurves_of(o.animation_data.action):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
SHOULDER_DY = 0.50
for n, ji in CREW.items():
    H = CH[n]; g = OB["CrankGrip.%d" % ji]; ax_ = Vector(g["axle"])
    sh = H.r.BN["upperarm01.L"].head_local
    BNs = H.r.BN; L_arm = sum(BNs[b_ + ".L"].length for b_ in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02"))
    D = float(os.environ.get("REACH", "0.78")) * L_arm; dz = sh.z * 0.97 - Vector(g["axle"]).z            # shoulder -> axle: the 0.12 m crank circle stays well inside the reach
    sdy = SHOULDER_DY * min(1.0, L_arm / 0.549)            # shorter arms stand closer to the crank
    print("CREW", n, "arm", round(L_arm, 3), "shoulder->axle", round(D, 3), "dy", round(sdy, 3))
    base = Vector((ax_.x, ax_.y - sdy - sh.y * -1.0 - 0.02, 0))      # rig faces +Y (yaw 180): local -y -> world +y
    put_ranges(n, [(FA_CR, FB_CR, base, 180)])
    ph_n = 0.0
    for f in frs(FA_CR, FB_CR, 3):
        th = theta(f)
        rock = -math.cos(th)                                                 # +1 when the grip is at the back (lean in)
        stand(H, f, (0, -0.04 * rock), 0, flex=10 + 4 * rock, spine=8 + 5 * rock, head=(-6 - 3 * rock, 0), feet=(0, 0))
    for s, sx in (("L", 1), ("R", -1)):
        shl = H.r.BN["upperarm01." + s].head_local
        key_pole(H, s, FA_CR, shl + Vector((sx * 0.38, 0.35, -0.55)))
    for s, dx in (("L", -0.12), ("R", 0.12)):                               # world x: his left hand is at world -x (he faces +Y)
        ev(FA_CR); nA = Vector((0, float(os.environ.get("GRIP_NY", "0.2")), -1)).normalized()
        c = g.matrix_world.translation + Vector((dx, 0, 0)) - nA * GRIP_OFF            # palm held clear of the bar (no crossing)
        if GRIP_POSE == "palm":
            crank_palm(H.r.o, s, g, dx, frs(FA_CR, FB_CR, 2), os.environ.get("PALM_POSE", "flat_palm"))
        elif GRIP_POSE == "wrap":
            grip_roll(H.r.o, s, g, FA_CR, frs(FA_CR, FB_CR, 2), c, nA); hold_fingers(H.r.o, s, FA_CR, FB_CR)
        else:
            hand_follow(H.r.o, s, g, FA_CR, frs(FA_CR, FB_CR, 2), c, nA, Vector((0, 0.83, 0.55)), GRIP_POSE)
    face(H, FA_CR, -0.002, -9); blinks(H, FA_CR, FB_CR, -0.002, -9, every=170, ofs=40 + 13 * ji)

# ---- cameras S1, S2, S4, S5, S7 (set A, worker side is -Y)
def wpos(n): return Vector(OB["CrankGrip.%d" % CREW[n]]["axle"])
a1 = wpos("W1")
camshot("S1", [(0, a1 + Vector((2.55, 0.62, 0.62)), a1 + Vector((0, -0.34, 0.56)), 66), (1, a1 + Vector((2.45, 0.62, 0.62)), a1 + Vector((0, -0.34, 0.57)), 68)])   # face + shoulders, hands out of frame
camshot("S2", [(0, Vector((0, -26, 3.2)), Vector((0, 4, 6.5)), 26), (1, Vector((0, -22, 2.8)), Vector((0, 4, 6.2)), 26)])
camshot("S4", [(0, Vector((9.2, -0.42, 0.88)), Vector((-3, -1.15, 1.25)), 30), (1, Vector((8.5, -0.42, 0.9)), Vector((-3.5, -1.15, 1.3)), 30)])
camshot("S5", [(0, Vector((-9.2, -0.42, 0.88)), Vector((3, -1.15, 1.3)), 30), (1, Vector((-8.6, -0.42, 0.9)), Vector((3, -1.15, 1.35)), 30)])
camshot("S7", [(0, Vector((-8.4, -0.32, 0.75)), Vector((-5.0, -1.2, 1.3)), 45), (1, Vector((-8.0, -0.32, 0.78)), Vector((-5.0, -1.2, 1.32)), 47)])
# the windlasses come off after the cranking (S8 on): only the jack bodies and screws stay under the needles
WINDLASS = [o for o in OB if o.name.split(".")[0] in ("JackUpright", "JackUpFoot", "JackAxle", "JackShaft", "JackGear", "JackGearArm", "CrankArm", "CrankGrip")]
key_vis_all(WINDLASS, [(0, True), (f0("S8"), False)])

# ================================================================== S3: the Foreman calls the turn
FM = CH["Foreman"]; fa, fb = f0("S3"), f1("S3")
FPOS = Vector((0.9, -4.2, 0))
put_ranges("Foreman", [(fa, f1("S3"), FPOS, 20)])
stand(FM, fa, head=(2, 0)); arms_hang(FM, fa); face(FM, fa, 0.0, -6)
stand(FM, fa + 25, head=(-4, 0), spine=2); face(FM, fa + 25, 0.002, -4, 0)
shR = FM.r.BN["upperarm01.R"].head_local
for f, up in ((fa + 10, 0.0), (fa + 32, 1.0), (fa + 70, 1.0), (fa + 90, 0.8), (fb, 0.8)):
    W = shR.lerp(shR + Vector((-0.18, -0.30, 0.38)), up) + Vector((-0.09 * (1 - up), -0.04 * (1 - up), -0.55 * (1 - up)))   # starts beside the thigh, never inside the torso
    FM.key_hand("R", f, W, Vector((0.1, -0.15, 1.0)) if up > 0.5 else Vector((0, -0.12, -1)), Vector((0, -1, 0)) if up > 0.5 else Vector((1, 0, 0)), pole=shR + Vector((-0.45, 0.25, -0.35)))
apply_pose(FM.r.o, "R", "relaxed", fa + 10); apply_pose(FM.r.o, "R", "flat_palm", fa + 32)
face(FM, fa + 32, 0.003, -4, 8); face(FM, fa + 60, 0.003, -4, 4); face(FM, fa + 75, 0.003, -4, 9); face(FM, fb, 0.002, -5, 2)
stand(FM, fb, head=(-5, -6), spine=3)
F3 = FPOS + Vector((0, 0, 1.5))
camshot("S3", [(0, FPOS + Vector((0.7, -2.6, 1.15)), F3 + Vector((0, 0, 0.05)), 50), (1, FPOS + Vector((0.6, -2.3, 1.15)), F3 + Vector((0, 0, 0.08)), 52)])

# ================================================================== S6: the Lady in her armchair, the room rises
LD = CH["Lady"]; fa, fb = f0("S6"), fx("S6")
CH_ = OB["Armchair"]; cmn, cmx = bbox([CH_])
seat = Vector(((cmn.x + cmx.x) / 2, (cmn.y + cmx.y) / 2 - 0.04, 0))
put_ranges("Lady", [(fa, fb, (seat.x, seat.y, 0), 0)])
SEATZ = 0.49
def sit(H, f, head=(0, 0), spine=-6):
    H.key_root(f, Vector((0, -0.02, SEATZ + 0.10)), yaw=0, flex=-4)
    H.key_spine(f, flex=spine, head=head)
    for s in "LR":
        a = H.ankle[s]; xy = Vector((a.x * 1.05, -0.47))
        H.key_foot(s, f, xy, 0)
sit(LD, fa, head=(12, 0), spine=0); sit(LD, fa + 25, head=(2, -38), spine=2); sit(LD, fa + 55, head=(-2, -30), spine=4); sit(LD, fa + 85, head=(-6, 42), spine=3); sit(LD, fb, head=(-4, 48), spine=2)
ev(fa + 1)
thl = [LD.r.o.matrix_world @ LD.r.PB["upperleg02." + s].tail for s in "LR"]
thh = [LD.r.o.matrix_world @ LD.r.PB["upperleg01." + s].head for s in "LR"]
lap = (thl[0] + thl[1] + thh[0] + thh[1]) / 4
BOOK = OB["LapBook"]; BOOK.location = lap + Vector((0, -0.05, 0.125)); BOOK.rotation_euler = (R_(-12), 0, 0)
key_vis(BOOK, [(0, False), (fa, True), (fb + 1, False)]); key_vis(OB["LapBookPages"], [(0, False), (fa, True), (fb + 1, False)])
ev(fa + 1); bm_ = BOOK.matrix_world; nrm = (bm_.to_3x3() @ Vector((0, 0, 1))).normalized()
dg_ = bpy.context.evaluated_depsgraph_get()
def armrest_top(sx):
    """top surface of the armrest on side sx (+1 = her left, world +x), found by casting down onto the chair"""
    best = None
    for dxa in (0.30, 0.33, 0.36, 0.39):
        o_ = Vector((seat.x + sx * dxa, seat.y - 0.08, 1.5)); hit, loc, n_, i_, ob_, m_ = sc.ray_cast(dg_, o_, Vector((0, 0, -1)))
        if hit and ob_.name == "Armchair" and 0.45 < loc.z < 0.85 and (best is None or loc.z > best.z): best = loc
    return best
for s, dx in (("L", 0.09), ("R", -0.09)):
    p = bm_ @ Vector((dx, -0.02, 0.03)); sx = 1 if s == "L" else -1
    for f in (fa, fa + 50): place_hand(LD.r.o, s, f, p, -nrm, (bm_.to_3x3() @ Vector((0, -1, 0))).normalized())
    top = armrest_top(sx)
    if top is not None:                     # grips the armrest as the room lifts (palm on top, fingers forward over the front)
        for f in (fa + 72, fb): place_hand(LD.r.o, s, f, top + Vector((0, 0, 0.004)), Vector((0, 0, -1)), Vector((0, -1, 0)), skin=0.018)
        apply_pose(LD.r.o, s, "relaxed", fa + 50); apply_pose(LD.r.o, s, "cup_hold", fa + 72)
    else:
        for f in (fa + 72, fb): place_hand(LD.r.o, s, f, p, -nrm, (bm_.to_3x3() @ Vector((0, -1, 0))).normalized())
        apply_pose(LD.r.o, s, "relaxed", fa)
    print("ARMREST", s, top)
    shl = LD.r.BN["upperarm01." + s].head_local; sx = 1 if s == "L" else -1
    key_pole(LD, s, fa, shl + Vector((sx * 0.4, 0.25, -0.4)))
face(LD, fa, 0.0, -10); face(LD, fa + 50, 0.0, -6); face(LD, fa + 85, 0.002, -4); blinks(LD, fa, fb, every=130, ofs=30)
WV = OB["WindowView"]; z0w = WV.location.z
key_prop(WV, 0, (WV.location.x, WV.location.y, z0w)); key_prop(WV, fa, (WV.location.x, WV.location.y, z0w)); key_prop(WV, fb, (WV.location.x, WV.location.y, z0w - 1.4))
L0 = Vector((seat.x, seat.y, 1.0))
camshot("S6", [(0, Vector((seat.x - 1.7, seat.y - 2.5, 1.45)), L0 + Vector((0.15, 0, 0.0)), 30), (1, Vector((seat.x - 0.95, seat.y - 1.6, 1.3)), L0 + Vector((0.1, 0, 0.12)), 34)])   # 3/4, slow push-in

# ================================================================== S8: W2 slides a timber onto the hero crib stack
W2 = CH["W2"]; fa, fb = f0("S8"), f1("S8")          # W2 parks after S8: every key ends ON the cut
cr = [o for l, o in CRIBS[HERO_CRIB] if l == 0]; cx = (cr[0].location.x + cr[1].location.x) / 2; cy = (cr[0].location.y + cr[1].location.y) / 2
TB = OB["SlideTimber"]; TB.rotation_euler = (0, 0, 0)                 # along X: the near timber of layer 4
tz = 0.2 * HERO_L + 0.1; tx = cx
y_end = cy + 0.6; y_start = y_end + 0.5
key_vis(TB, [(0, False), (fa, True), (f1("S8") + 1, False)])
t0 = fa + 30; t1 = fa + 30 + 70
for f in (fa, t0): key_prop(TB, f, (tx, y_start, tz))
key_prop(TB, t1, (tx, y_end, tz)); key_prop(TB, fb, (tx, y_end, tz))
start = Vector((tx, y_start + 0.62, 0))
put_ranges("W2", [(fa, f1("S8"), start, 0)])
path = lambda f: Vector((0, -(min(max(f - t0, 0), t1 - t0) / (t1 - t0)) * 0.5, 0))
W2.walk(path, lambda f: 0.0, fa, fb, stride=0.42, lift=0.05, bob=0.01, lean=14, step=2)
for s, dx in (("L", 0.13), ("R", -0.13)):
    for f in frs(fa, fb, 2):
        ev(f); p = TB.matrix_world.translation + Vector((dx, 0.05, 0.118))
        place_hand(W2.r.o, s, f, p, Vector((0, -0.35, -1)).normalized(), Vector((0, -1, -0.1)).normalized())
    apply_pose(W2.r.o, s, "flat_palm", fa)
    shl = W2.r.BN["upperarm01." + s].head_local; sx = 1 if s == "L" else -1
    key_pole(W2, s, fa, shl + Vector((sx * 0.4, 0.3, -0.5)))
face(W2, fa, -0.002, -9); blinks(W2, fa, fb, -0.002, -9, ofs=50)
camshot("S8", [(0, Vector((tx - 0.5, -1.9, 2.25)), Vector((tx, y_end + 0.45, 1.05)), 36), (1, Vector((tx - 0.15, -1.05, 2.15)), Vector((tx, y_end + 0.4, 1.05)), 38)])   # high: arms on the timber, push-in

# ================================================================== S9 / S10: the building on its cribbing, rising to the new street level
camshot("S9", [(0, Vector((-17, -19, 0.8)), Vector((0, 2, 4.5)), 24), (1, Vector((-10.5, -13.0, 1.8)), Vector((0, 2, 5.0)), 24)])
camshot("S10", [(0, Vector((-5.0, -5.5, 0.5)), Vector((-6.0, 0.5, 0.9)), 22), (1, Vector((-5.0, -5.5, 2.9)), Vector((-6.0, 0.5, 3.0)), 22)])

# ================================================================== S11: Mason builds the new brick foundation from behind it (face to camera)
MS = CH["Mason"]; fa, fb = f0("S11"), f1("S11")
for o in OB:
    if o.parent == MS.r.o and o.name.split(".")[-1] in ("cap", "visor"): o.hide_render = o.hide_viewport = True
    if o.parent == MS.r.o and "short0" in o.name: o.hide_render = o.hide_viewport = False
MX = 3.0; wall_y = 0.25
MPOS = Vector((MX + 0.14, wall_y + 0.50, 0))       # close behind the wall (back face at wall_y + 0.21): the reach stays ~0.4 m
put_ranges("Mason", [(fa, f1("S11"), MPOS, 0)])
BR = OB["HandBrick"]; key_vis(BR, [(0, False), (fa, True), (fb + 1, False)])
n0 = 2
key_vis_all(COURSES[:n0], [(fa, True)])
cyc = 66; c_ = n0
for i, f in enumerate(range(fa, fb, cyc)):
    top = 0.25 * c_
    stand(MS, f, flex=12, spine=16 + 4 * i, head=(-14, 0), feet=(0, 0.10)); stand(MS, f + cyc // 2, flex=14, spine=20 + 4 * i, head=(-10, 0), feet=(0, 0.10))
    key_prop(BR, f, (MX, wall_y, top + 0.10)); key_prop(BR, f + 40, (MX, wall_y, top + 0.0375)); key_prop(BR, f + cyc - 1, (MX, wall_y, top + 0.0375))
    if c_ < len(COURSES): key_vis(COURSES[c_], [(0, False), (f + 50, True)]); key_vis(BR, [(f + 50, False), (f + cyc, True)])
    c_ += 1
for o in COURSES[c_:]: key_vis(o, [(fa, False)])
for fc in fcurves_of(BR.animation_data.action):
    for k in fc.keyframe_points:
        if (int(k.co.x) - fa) % cyc == cyc - 1: k.interpolation = 'CONSTANT'
for s, dx in (("R", 0.0), ("L", 0.30)):   # right palm on the brick, left palm resting on the wall top beside it
    for f in frs(fa, fb, 2):
        ev(f)
        if s == "R": p = BR.matrix_world.translation + Vector((0, 0, 0.0375 + 0.012))
        else:
            vis_n = sum(1 for o in COURSES if not o.hide_render); p = Vector((MX + dx, wall_y, 0.25 * max(vis_n, n0) + 0.012))
        place_hand(MS.r.o, s, f, p, Vector((0, -0.2, -1)).normalized(), Vector((0, -1, 0)))
    apply_pose(MS.r.o, s, "flat_palm", fa)
    shl = MS.r.BN["upperarm01." + s].head_local; sx = 1 if s == "L" else -1
    key_pole(MS, s, fa, shl + Vector((sx * 0.45, 0.2, -0.5)))
face(MS, fa, -0.002, -10); blinks(MS, fa, fb, -0.002, -10, ofs=35)
camshot("S11", [(0, Vector((MX + 0.8, -2.3, 1.55)), Vector((MX, wall_y + 0.5, 1.15)), 38), (1, Vector((MX + 0.7, -2.0, 1.5)), Vector((MX, wall_y + 0.5, 1.2)), 38)])
# S12: the foundation complete across the front
fa = f0("S12")
key_vis_all(COURSES, [(fa, True)]); key_vis(BR, [(fa, False)])
key_vis_all(COURSES, [(f0("S10"), False)])              # S10 (the rise to street level) comes before the foundation in the story
camshot("S12", [(0, Vector((2.8, -5.0, 0.6)), Vector((0.5, 0.3, 0.9)), 32), (1, Vector((2.0, -3.6, 0.9)), Vector((0.5, 0.3, 2.1)), 32)])   # push-in + tilt-up, the sign stays above the frame   # push-in + tilt-up

# ================================================================== S13 / S14: facade on its new foundation, crane over the roof
camshot("S13", [(0, Vector((-4.5, -9.0, 0.8)), Vector((0, 0, 6.0)), 22), (1, Vector((-4.0, -8.5, 0.9)), Vector((0, 0, 11.0)), 22)])
camshot("S14", [(0, Vector((-8.0, 30.0, 10.0)), Vector((0, 8, 17.0)), 24), (1, Vector((-6.0, 27.0, 24.0)), Vector((0, -10, 26.0)), 24)])   # from behind: the sign (front face) never in frame

# ================================================================== S15: swamp aerial | S16: 1850s town aerial with chimney smoke
camshot("S15", [(0, Vector((600, -70, 32)), Vector((600, 40, 0)), 30), (1, Vector((600, -40, 26)), Vector((600, 60, 0)), 30)])
camshot("S16", [(0, Vector((1200, -110, 60)), Vector((1200, 10, 0)), 30), (1, Vector((1200, -80, 38)), Vector((1200, 10, 0)), 30)])
fa, fb = f0("S16"), fx("S16")
for k, o in enumerate([o for o in OB if o.name.startswith("Smoke.")]):
    p0 = o.location.copy()
    key_prop(o, 0, p0); o.scale = (0.6, 0.6, 0.6); o.keyframe_insert("scale", frame=fa)
    key_prop(o, fa, p0); key_prop(o, fb, p0 + Vector((3, 2, 8))); o.scale = (1.8, 1.8, 1.8); o.keyframe_insert("scale", frame=fb)

# ================================================================== S17-S20: the flood street
X0 = 1800.0; WZ = 0.35
TM, TWn, SM = CH["TownMan"], CH["TownWoman"], CH["SickMan"]
# S17: TownMan wades toward camera, TownWoman further back crossing
fa, fb = f0("S17"), fx("S17")
pass   # TownMan placements: see S21 (all three ranges set together)
pth = lambda f: Vector((0, -0.9 * (f - fa) / FPS, 0))
TM.walk(pth, lambda f: 0.0, fa, fb, stride=0.6, lift=0.09, bob=0.02, lean=6)
def walk_arms(H, fa, fb, path, stride=0.6, step=2, amp=0.09, out=0.06):
    d = 0.0; prev = path(fa)
    for f in range(fa, fb + 1):
        p = path(f); d += (p - prev).length; prev = p
        if (f - fa) % step and f != fb: continue
        ph = math.sin(2 * math.pi * d / stride)
        for s, sx, sg in (("L", 1, 1), ("R", -1, -1)):
            sh = H.r.BN["upperarm01." + s].head_local
            W = Vector((p.x + sh.x + out * sx, p.y + sh.y - 0.02 - amp * ph * sg, sh.z - 0.6))
            H.key_hand(s, f, W, Vector((0, -0.15 * ph * sg, -1)), Vector((-sx, 0, 0)), pole=W + Vector((0.3 * sx, 0.5, 0.3)))
    for s in "LR": apply_pose(H.r.o, s, "relaxed", fa)
walk_arms(TM, fa, fb, pth); face(TM, fa, 0.0, -7); blinks(TM, fa, fb)
put_ranges("TownWoman", [(f0("S19"), f1("S19"), (X0 - 1.0, 23.5, 0), 200), (f0("S20"), fx("S20"), (X0 - 2.2, 28.0, 0), 0)])
pthw = lambda f: Vector((0, -0.7 * (f - fa) / FPS, 0))

camshot("S17", [(0, Vector((X0 - 1.0, 23.6, 1.25)), Vector((X0 - 1.5, 26.0, 1.15)), 32), (1, Vector((X0 - 1.0, 23.1, 1.25)), Vector((X0 - 1.5, 25.2, 1.15)), 32)])   # knees-up, he wades toward camera
# S18: the horse in the water lifts its head; TownMan wades past behind
HR = OB["Horse_rig"]; HR.rotation_mode = 'XYZ'; HRIG = Rig(HR)
HP = Vector((X0 - 1.0, 28, 0))
def horse_place(f, pos, yaw):
    HR.location = pos; HR.rotation_euler = (0, 0, R_(yaw)); HR.keyframe_insert("location", frame=f); HR.keyframe_insert("rotation_euler", frame=f)
horse_place(0, Vector((0, -6000, -600)), 0)
fa, fb = f0("S18"), fx("S18")
horse_place(fa, HP, -60); horse_place(f0("S19"), Vector((0, -6000, -600)), 0)
horse_place(f0("S20"), HP + Vector((0.5, 3, 0)), -100); horse_place(fx("S20") + 1, Vector((0, -6000, -600)), 0)
constant_all(HR)
def horse_head(f, nod, turn):
    HRIG.key_rot("neck1", f, [("X", nod * 0.4), ("Z", turn * 0.4)]); HRIG.key_rot("neck2", f, [("X", nod * 0.3), ("Z", turn * 0.3)]); HRIG.key_rot("head", f, [("X", nod * 0.3), ("Z", turn * 0.3)])
horse_head(fa, 14, 0); horse_head(fa + 45, -6, 4); horse_head(fa + 100, -12, -6); horse_head(fb, -10, -8)
pth2 = lambda f: Vector((0, -0.8 * (f - fa) / FPS, 0))
TM.walk(pth2, lambda f: 0.0, fa, fb, stride=0.6, lift=0.09, bob=0.02, lean=6); walk_arms(TM, fa, fb, pth2)
camshot("S18", [(0, HP + Vector((-3.2, -3.4, 1.2)), HP + Vector((0.4, 0.2, 1.4)), 30), (1, HP + Vector((-2.8, -3.0, 1.15)), HP + Vector((0.4, 0.2, 1.45)), 30)])
# S19: the sick man doubles over coughing, the woman behind looks on
fa, fb = f0("S19"), f1("S19")
SP = Vector((X0 - 1.6, 20, 0))
put_ranges("SickMan", [(fa, f1("S19"), SP, 20)])
stand(SM, fa, flex=12, spine=22, head=(-12, 0))      # already doubled over at the cut: hands on the knees from the first frame
for k, f in enumerate(frs(fa + 20, fb, 30)):
    stand(SM, f, flex=14 + 4 * (k % 2), spine=26 + 8 * (k % 2), head=(-14 - 6 * (k % 2), 0))
    face(SM, f, -0.002, -10 if k % 2 else -12, 6 if k % 2 else 2)
arms_hang(SM, fa)
ev(fa + 21)
for f in frs(fa, fb, 4):
    ev(f); M_ = SM.r.o.matrix_world; fwd = (M_.to_3x3() @ Vector((0, -1, 0))).normalized(); up = Vector((0, 0, 1))
    for s_ in "LR":
        kn = M_ @ SM.r.PB["lowerleg01." + s_].head
        nrm = (-fwd * 0.55 - up * 0.85).normalized()
        place_hand(SM.r.o, s_, f, kn + fwd * 0.11 + up * 0.09, nrm, (fwd * 0.25 - up).normalized(), skin=0.02)
apply_pose(SM.r.o, "R", "relaxed", fa); apply_pose(SM.r.o, "L", "relaxed", fa)
for s, sx in (("L", 1), ("R", -1)):
    key_pole(SM, s, fa, SM.r.BN["upperarm01." + s].head_local + Vector((sx * 0.45, 0.2, -0.45)))
stand(TWn, fa, head=(4, 0)); arms_hang(TWn, fa); stand(TWn, fa + 70, head=(8, 10)); face(TWn, fa, 0.002, -5)
camshot("S19", [(0, SP + Vector((1.6, -3.0, 1.35)), SP + Vector((0, 0, 1.15)), 32), (1, SP + Vector((1.3, -2.5, 1.3)), SP + Vector((0, 0, 1.15)), 34)])
# S20: the horse turns its head; the woman walks away down the street
fa, fb = f0("S20"), fx("S20")
horse_head(fa, 0, -4); horse_head(fa + 50, -4, 18); horse_head(fb, -6, 22)
pthw2 = lambda f: Vector((0, -0.8 * (f - fa) / FPS, 0))
TWn.walk(pthw2, lambda f: 0.0, fa, fb, stride=0.55, lift=0.08, bob=0.02, lean=5); walk_arms(TWn, fa, fb, pthw2, stride=0.55, out=0.13)
camshot("S20", [(0, Vector((X0 - 2.6, 24.9, 1.35)), Vector((X0 - 1.9, 28.0, 1.2)), 34), (1, Vector((X0 - 2.6, 24.6, 1.35)), Vector((X0 - 1.9, 27.4, 1.2)), 34)])   # she fills about half the height

# ================================================================== S21: rise from the water up the new foundation | S22: modern skyline
camshot("S21", [(0, Vector((X0 + 6.5, 102.5, 1.2)), Vector((X0 + 1.0, 120, 2.8)), 30), (1, Vector((X0 + 5.2, 104.5, 1.4)), Vector((X0 + 0.5, 121, 3.8)), 32)])   # push-in
fa, fb = f0("S21"), f1("S21")
RS, RF = OB["RaisedShop"], OB["RaisedFoundation"]
z_top = RS.location.z; h_f = RF.dimensions.z
for f, u in ((0, 1.0), (fa, 0.0), (fa + int(dur("S21") * 0.85), 1.0), (fb + 1, 1.0)):       # the block rises 1.6 m out of the water to the new street level
    RS.location.z = z_top - 1.6 * (1 - u); RS.keyframe_insert("location", index=2, frame=f)
    k_ = (h_f - 1.6 * (1 - u)) / h_f; RF.scale.z = k_; RF.location.z = h_f * k_ / 2; RF.keyframe_insert("scale", index=2, frame=f); RF.keyframe_insert("location", index=2, frame=f)
for o in (RS, RF):
    for fc in fcurves_of(o.animation_data.action):
        for k in fc.keyframe_points:
            if int(k.co.x) == 0: k.interpolation = 'CONSTANT'
put_ranges("TownMan", [(f0("S17"), f1("S17"), (X0 - 1.5, 26, 0), 0), (f0("S18"), fx("S18"), (X0 + 3.5, 34, 0), 90), (fa, fb, (X0 + 6.6, 108.0, 0), -90)])
pth21 = lambda f: Vector((0, -0.85 * (f - fa) / FPS, 0))
TM.walk(pth21, lambda f: 0.0, fa, fb, stride=0.6, lift=0.09, bob=0.02, lean=6); walk_arms(TM, fa, fb, pth21, out=0.08); face(TM, fa, 0.0, -7)
camshot("S22", [(0, Vector((2600 - 60, -125, 12)), Vector((2600 + 15, 60, 30)), 24), (1, Vector((2600 - 5, -80, 42)), Vector((2600 + 25, 90, 44)), 24)])

# fill light under the raised building for S8 and S11 (faces in the building's shadow); keyed on only in those shots
UF = bpy.data.objects.new("UnderFill", bpy.data.lights.new("UnderFill", 'AREA')); sc.collection.objects.link(UF)
UF.data.energy = 0.0; UF.data.size = 1.2; UF.data.color = (1.0, 0.95, 0.88)
for s_, pos, tgt in (("S8", Vector((tx + 0.2, y_end - 1.6, 1.7)), Vector((tx + 0.2, y_end + 0.4, 1.2))), ("S11", Vector((MX + 0.3, -1.3, 1.9)), Vector((MX + 0.3, 0.7, 1.2))),
                     ("S19", SP + Vector((1.4, -2.2, 1.9)), SP + Vector((0, 0, 1.3)))):     # S19: the sick man is back-lit by the sun
    UF.location = pos; UF.keyframe_insert("location", frame=f0(s_))
    UF.rotation_mode = 'QUATERNION'; UF.rotation_quaternion = (tgt - pos).to_track_quat('-Z', 'Y'); UF.keyframe_insert("rotation_quaternion", frame=f0(s_))
    UF.data.energy = 120.0; UF.data.keyframe_insert("energy", frame=f0(s_)); UF.data.energy = 0.0; UF.data.keyframe_insert("energy", frame=f1(s_) + 1)
UF.data.energy = 0.0; UF.data.keyframe_insert("energy", frame=0)
for o in (UF, UF.data): constant_all(o)
bake_camera()
json.dump([{"shot": s, "frame": f0(s), "end": f1(s), "seconds": T[s]} for s in ORDER], open(os.path.join(FILM, "work", "shots.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("ANIM_OK")
