"""B13 WomanSuckedOut, Phase 1 clips: every shot is its own 1x clip (~30% longer than the expected beat), one camera per
shot bound by a timeline marker (hard cuts). Phase 2 trims the tails to the VO; nothing is time-stretched.
blender -b base.blend --python 02_anim.py -- <build_dir>"""
import bpy, math, os, sys, random
from mathutils import Vector, Matrix, Quaternion, Euler
R_ = math.radians
BUILD = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(HERE + "/../../..")
exec(open(REPO + "/blender/pipeline/anim_lib.py").read())
exec(open(REPO + "/blender/pipeline/hand_poses.py").read())
def ground_z(x, y): return 0.018      # aisle carpet top
sc = bpy.context.scene; D = bpy.data; OB = D.objects
sc.render.fps = 60; sc.render.resolution_x = 1080; sc.render.resolution_y = 1920

# ------------------------------------------------------------------ shot table (name, frames)
SHOTS = [("S01", 100), ("S02", 150), ("S03", 120), ("S04", 120), ("S05", 120), ("S06", 100), ("S07", 150), ("S08", 120),
         ("S09", 120), ("S10", 120), ("S11", 156), ("S12", 156), ("S13", 156), ("S14", 156), ("S15", 120), ("S16", 100), ("S17", 120)]
T = {}; f = 1
for n, L in SHOTS: T[n] = (f, f + L - 1); f += L
sc.frame_start, sc.frame_end = 1, f - 1
EXTERIOR = {"S03", "S04", "S05", "S06", "S07", "S09", "S12", "S16", "S17"}
ROW0, PITCH = -2.4, 0.81
def rowy(i): return ROW0 - PITCH * (i - 1)
HOLE = Vector((-1.45, -5.58, 1.20))

def coll(name):
    c = D.collections.get(name) or D.collections.new(name)
    if c.name not in [x.name for x in sc.collection.children]: sc.collection.children.link(c)
    return c
cCam = coll("CAMS")

def const_interp(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in all_fc(o):
        if fc.data_path in ("hide_render", "hide_viewport") or "influence" in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def all_fc(o):
    ad = o.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for bag in strip.channelbags: out += list(bag.fcurves)
    return out
def vis(o, f, on):
    o.hide_render = not on; o.hide_viewport = not on
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
def key_loc(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert("location", frame=f)
    if rot is not None: o.rotation_mode = 'XYZ'; o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert("scale", frame=f)

# ------------------------------------------------------------------ exterior / interior visibility per shot
EXT = list(D.collections["EXT_PLANE"].objects)
SHARDS = [o for o in EXT if o.name.startswith("SHARD_")]
DEBRIS = [o for o in EXT if o.name.startswith("DEBRIS_")]
SMOKE = [o for o in EXT if o.name.startswith("SMOKE_")]
SPECIAL = set(SHARDS + DEBRIS + SMOKE + [OB["PANE"], OB["NACELLE_ARC_L"], OB["BLADE_BREAK_L"]])
for n, (f0, f1) in T.items():
    for o in EXT:
        if o in SPECIAL: continue
        vis(o, f0, n in EXTERIOR)
    for nm in ("CABIN_FIXED", "CABIN_SHELL", "HOLE_TRIM", "CABIN_BACKWALL", "COCKPIT_SHELL"):   # bins poke through the skin outside
        if nm in OB: vis(OB[nm], f0, n not in EXTERIOR)
# effects start hidden
for o in SHARDS + DEBRIS + SMOKE: vis(o, 1, False)
# pane intact until the window breaks (S07 impact); the cabin sees it as glass (S01, S02 before the burst)
# arc/blade intact until S06 break
# exposure: exteriors one stop darker so the white airframe keeps its shading against the deep sky (director P1 note)
for n, (f0, f1) in T.items():
    sc.view_settings.exposure = -0.9 if n in EXTERIOR else 0.0
    sc.view_settings.keyframe_insert("exposure", frame=f0)
# ------------------------------------------------------------------ helpers: cameras
def cam(name, lens=30, fstop=8.0):
    c = OB.get(name) or D.objects.new(name, D.cameras.new(name))
    if c.name not in cCam.objects: cCam.objects.link(c)
    c.data.lens = lens; c.data.sensor_width = 36; c.data.sensor_fit = 'AUTO'; c.data.clip_start = 0.03; c.data.clip_end = 200000
    c.data.dof.use_dof = True; c.data.dof.aperture_fstop = fstop
    return c
def look(c, f, eye, tgt, lens=None):
    c.location = Vector(eye); d = Vector(tgt) - Vector(eye)
    c.rotation_mode = 'XYZ'; c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
    c.data.dof.focus_distance = d.length; c.data.dof.keyframe_insert("focus_distance", frame=f)
    if lens: c.data.lens = lens; c.data.keyframe_insert("lens", frame=f)
def shot_cam(n, keys, lens=30, fstop=8.0):
    """keys: list of (u 0..1, eye, tgt[, lens])"""
    c = cam("CAM_" + n, lens, fstop); f0, f1 = T[n]
    for k in keys:
        look(c, int(round(f0 + k[0] * (f1 - f0))), k[1], k[2], k[3] if len(k) > 3 else None)
    m = sc.timeline_markers.new(n, frame=f0); m.camera = c
    return c

# ------------------------------------------------------------------ helpers: FK posing (MPFB default rig)
SPW = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HDW = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
def fk_spine(R, f, flex=0, side=0, twist=0, hflex=0, hside=0, htwist=0):
    for n_, w in SPW.items(): R.key_rot(n_, f, [("X", flex * w), ("Y", side * w), ("Z", twist * w)])
    for n_, w in HDW.items(): R.key_rot(n_, f, [("X", hflex * w), ("Y", hside * w), ("Z", htwist * w)])
def fk_arm(R, s, f, down=40, fwd=20, elbow=60, out=0, twist=0, wrist=0):
    sx = 1 if s == "L" else -1
    R.key_rot("upperarm01." + s, f, [("Y", sx * down), ("X", -fwd), ("Z", sx * out)])
    R.key_rot("lowerarm01." + s, f, [("X", -elbow), ("Z", sx * twist)])
    R.key_rot("wrist." + s, f, [("X", wrist)])
def fk_leg(R, s, f, hip=88, knee=80, splay=4, ankle=0):
    sx = 1 if s == "L" else -1
    R.key_rot("upperleg01." + s, f, [("X", -hip), ("Z", sx * splay)])
    R.key_rot("lowerleg01." + s, f, [("X", knee)])
    R.key_rot("foot." + s, f, [("X", ankle)])
def eyes(R, f, closed=0.0):
    for s in "LR":
        R.key_rot("orbicularis03." + s, f, [("X", 28 * closed)]); R.key_rot("orbicularis04." + s, f, [("X", -8 * closed)])
def look_eyes(R, f, yaw=0, pitch=0):
    for s in "LR":
        if "eye." + s in R.PB: R.key_rot("eye." + s, f, [("X", pitch), ("Z", yaw)])
_PC = {}
def hand_pose(rig, s, f, pose="relaxed"):
    k = (rig.name, s, pose)
    if k not in _PC: sc.frame_set(1); _PC[k] = _pose_rots(rig, s, pose)
    _key(rig, s, _PC[k], f, 1.0)

def set_ik(rig, f, arms, legs):
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.type in ('IK', 'COPY_ROTATION'):
                isarm = "arm" in pb.name or "wrist" in pb.name
                c.influence = float(arms if isarm else legs)
                c.keyframe_insert("influence", frame=f)
HEROES = [OB["W"], OB["HA"], OB["HB"]]
RG = {r.name: Rig(r) for r in HEROES}
HU = {r.name: Human(RG[r.name]) for r in HEROES}
def reset_pose(rig, f):
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
def hold_end(rig, f):
    sc.frame_set(f)
    for pb in rig.pose.bones:
        pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    rig.keyframe_insert("location", frame=f); rig.keyframe_insert("rotation_euler", frame=f)
def place(rig, f, loc, rot):
    rig.rotation_mode = 'XYZ'; rig.location = loc; rig.rotation_euler = rot
    rig.keyframe_insert("location", frame=f); rig.keyframe_insert("rotation_euler", frame=f)
def away(rig, f):
    place(rig, f, (0, 30, -20), (0, 0, 0))

def seated(rig, f, x, y, look_turn=0.0, hflex=-4, flex=9, side=0, arms=None, legs=(86, 78)):
    R = RG[rig.name] if rig.name in RG else Rig(rig)
    place(rig, f, (x, y + 0.06 + (0.04 if rig.name == "W" else 0), -0.17 + (0.05 if rig.name == "W" else 0)), (0, 0, math.pi))
    wl = rig.name == "W"      # window seat: her left foot stays off the curved wall
    fk_leg(R, "L", f, hip=legs[0], knee=legs[1], splay=-6 if wl else 1); fk_leg(R, "R", f, hip=legs[0] - 2, knee=legs[1] + 3, splay=3 if wl else 1)
    fk_spine(R, f, flex=flex, side=side, htwist=look_turn, hflex=hflex)
    a = arms or {}
    for s in "LR":
        dn, fw, el, ou = a.get(s, (38, 16, 74, 0))
        fk_arm(R, s, f, down=dn, fwd=fw, elbow=el, out=ou)

# ------------------------------------------------------------------ passengers: awake, upright, breathing, looking around
PASS = [o for o in D.collections["PASSENGERS"].objects if o.type == 'ARMATURE']
for a in PASS:
    for pb in a.pose.bones: pb.rotation_mode = 'QUATERNION'
    R = Rig(a); rnd = random.Random(hash(a.name) % 1000)
    left = a.location.x < 0; window = abs(a.location.x) > 0.8
    sl = (6 if left else -6) * (1 if window else -1) * rnd.uniform(0.3, 1.0)
    ph = rnd.uniform(0, 6.28)
    for s in "LR": hand_pose(a, s, 1, "relaxed")
    fk_leg(R, "L", 1, hip=86 + rnd.uniform(-5, 3), knee=78 + rnd.uniform(-6, 6), splay=rnd.uniform(2, 8))
    fk_leg(R, "R", 1, hip=86 + rnd.uniform(-5, 3), knee=78 + rnd.uniform(-6, 6), splay=rnd.uniform(2, 8))
    for s in "LR":
        inner = (s == "L") == (not left) if not window else (s == "L") == left
        fk_arm(R, s, 1, down=40 - (6 if inner else 0), fwd=26 + (6 if inner else 0), elbow=60, out=-8 if inner else 0)
    eyes(R, 1, 0.0); R.key_rot("jaw", 1, [("X", 2)])
    tw0 = rnd.uniform(-20, 20)
    S8 = T["S08"][0]
    for fr in range(1, sc.frame_end + 1, 45):
        b = math.sin(2 * math.pi * fr / 270 + ph)
        if fr >= S8:      # after the blast: heads up toward the masks / turned toward the hole
            fk_spine(R, fr, flex=2 + 1.5 * b, side=sl * 0.5, twist=rnd.uniform(-6, 6), hflex=-22 + 3 * b, hside=0, htwist=(25 if left else -25) * rnd.uniform(0.2, 1))
        else:
            fk_spine(R, fr, flex=4 + 1.5 * b, side=sl, twist=0, hflex=rnd.uniform(-8, 6) + 1.2 * b, hside=0, htwist=tw0 + 6 * math.sin(fr / 300 + ph))
print("PASSENGERS posed", len(PASS))

# ------------------------------------------------------------------ hero base keys per shot
W, HA, HB = OB["W"], OB["HA"], OB["HB"]
RW, RA, RB = RG["W"], RG["HA"], RG["HB"]
_CUR = [None]
def _begin(n):
    """close the previous shot (hold every hero channel at its last frame) and key a clean base pose for shot n"""
    if _CUR[0]:
        for r in HEROES: hold_end(r, T[_CUR[0]][1])
    _CUR[0] = n
    if n is None: return
    f0 = T[n][0]
    for r in HEROES:
        reset_pose(r, f0); set_ik(r, f0, 0, 0); away(r, f0)
        for s in "LR": hand_pose(r, s, f0, "relaxed")
        eyes(RG[r.name], f0, 0.0)

# W world poses --------------------------------------------------------------------------------------------------------
REST_ROOT = W.data.bones["root"].head_local.copy()
def place_pelvis(rig, f, Rm, pelvis):
    """object rotation Rm (3x3), translate so the root bone head lands on `pelvis` (world)"""
    loc = Vector(pelvis) - Rm @ rig.data.bones["root"].head_local
    place(rig, f, loc, Rm.to_euler('XYZ'))
# face-down hanging: head out of the hole (-x), back up, left side toward the tail
R_HANG = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0)))
def hang_pose(f, out=0.0, flutter=0.0, t=0.0, arms_in=0.0):
    """out: how far the pelvis is outside the wall plane (0 = at the hole centre)."""
    place_pelvis(W, f, R_HANG, (HOLE.x - 0.12 - out, HOLE.y, HOLE.z - 0.04))
    w1 = math.sin(t * 9.0); w2 = math.sin(t * 7.3 + 1.0)
    # wind folds the upper body back toward the tail (her left side) and lifts the arms back
    fk_spine(RW, f, flex=-4 + 2 * flutter * w1, side=12 + 3 * flutter * w2, twist=3 * flutter * w1, hflex=10, hside=8 + 4 * flutter * w2, htwist=0)
    a = arms_in      # pulled back in: arms go overhead (narrowest shape through the hole, clear of the seat backs)
    fk_arm(RW, "L", f, down=(-20 + 6 * flutter * w1) * (1 - a) - 80 * a, fwd=-30 * (1 - a), elbow=(25 + 8 * flutter * w2) * (1 - a) + 10 * a, out=0)
    fk_arm(RW, "R", f, down=(10 + 6 * flutter * w2) * (1 - a) - 80 * a, fwd=-55 * (1 - a), elbow=(30 + 8 * flutter * w1) * (1 - a) + 10 * a, out=0)
    # legs inside, near straight and level (held by the passengers)
    fk_leg(RW, "L", f, hip=18, knee=22, splay=3, ankle=-25); fk_leg(RW, "R", f, hip=14, knee=18, splay=-2, ankle=-25)
    eyes(RW, f, 1.0)
R_LIE = Matrix.Rotation(R_(90), 3, 'X') @ Matrix.Rotation(R_(180), 3, 'Z')   # face up, head toward -y (rear)
def lie_pose(f, breath=0.0):
    place_pelvis(W, f, R_LIE, (0.0, -6.05, 0.115))
    fk_spine(RW, f, flex=2 * breath, side=0, twist=0, hflex=-8, hside=0, htwist=-18)
    fk_arm(RW, "L", f, down=80, fwd=-2, elbow=10, out=0); fk_arm(RW, "R", f, down=80, fwd=-2, elbow=12, out=0)
    for s in "LR": hand_pose(W, s, f, "relaxed")
    fk_leg(RW, "L", f, hip=8, knee=14, splay=4); fk_leg(RW, "R", f, hip=4, knee=8, splay=-3)
    eyes(RW, f, 1.0)

SEAT_W = (-1.03, rowy(5)); SEAT_A = (-0.55, rowy(5))

# ================================================================== S01: In 2018, a woman was ...
_begin("S01")
f0, f1 = T["S01"]
for k, (fr, tw, hf) in enumerate(((f0, -6, -6), (f0 + 40, -14, -8), (f0 + 70, -20, -8), (f1, -22, -8))):
    seated(W, fr, SEAT_W[0] - 0.01, SEAT_W[1], look_turn=tw, hflex=hf - 12, side=-4, arms={"R": (42, 10, 88, 0)})
    seated(HA, fr, SEAT_A[0] + 0.06, SEAT_A[1], look_turn=-6 + 3 * k, hflex=8, side=4, arms={"L": (44, 8, 80, 0)})
for s in "LR": hand_pose(W, s, f0, "relaxed"); hand_pose(HA, s, f0, "relaxed")
shot_cam("S01", [(0, (-0.38, -4.50, 1.66), (-0.98, -5.78, 1.10), 30), (1, (-0.42, -4.68, 1.62), (-1.0, -5.78, 1.10), 34)])
# ================================================================== S02: ... sucked out of a window (burst + lurch)
_begin("S02")
f0, f1 = T["S02"]; fb = f0 + 24
for fr, tw in ((f0, -22), (fb, -22)):      # identical to the S01 end pose (checked clean)
    seated(W, fr, SEAT_W[0] - 0.01, SEAT_W[1], look_turn=tw, hflex=-20, side=-4, arms={"R": (42, 10, 88, 0)})
    seated(HA, fr, SEAT_A[0] + 0.06, SEAT_A[1], look_turn=3, hflex=8, side=4, arms={"L": (44, 8, 80, 0)})
vis(OB["PANE"], 1, True); vis(OB["PANE"], fb, False)
for fr, j in ((fb + 4, 0), (fb + 22, 1), (fb + 40, 0), (f1, 1)):      # fast flinch: the raised arm clears HA within 4 frames
    # W yanked toward the hole: whole body slides toward the window, torso folds left toward it, arms flung up
    seated(W, fr, SEAT_W[0] - 0.01, SEAT_W[1], look_turn=40, hflex=4, side=20 + 3 * j, flex=6,
           arms={"R": (-30 - 6 * j, 50, 60, 0)})
    if fr == fb + 4: continue      # HA eases away over the next 20 frames (his left arm stays clear of her)
    seated(HA, fr, SEAT_A[0] + 0.06, SEAT_A[1], look_turn=-32, hflex=-6, side=-14 - 2 * j, arms={"L": (44, 8, 80, 0), "R": (20, 42, 95, 0)})
# the flinch arm swings forward first (in front of her chest, clear of HA's forearm), then up; HA leans away at once
seated(W, fb + 2, SEAT_W[0] - 0.01, SEAT_W[1], look_turn=20, hflex=-6, side=8, flex=6, arms={"R": (20, 75, 85, 0)})
for s in "LR": hand_pose(W, s, fb + 10, "open_alarm"); hand_pose(HA, s, fb + 10, "open_alarm")
# shards burst outward from the pane, papers fly into the hole
rnd = random.Random(3)
for i, o in enumerate(SHARDS):
    h = Vector(o["home"]); v = Vector((-rnd.uniform(2.5, 5), -rnd.uniform(1, 4), rnd.uniform(-0.8, 0.8)))
    vis(o, fb, True); key_loc(o, fb, h, (0, 0, 0)); key_loc(o, fb + 20, h + v * 0.33, (rnd.uniform(-6, 6), rnd.uniform(-6, 6), rnd.uniform(-6, 6)))
    vis(o, fb + 21, False)
PAP = [o for o in OB if o.name.startswith("PAPER_")]
for i, o in enumerate(PAP):
    st = Vector((-0.2 - 0.12 * i, rowy(6) + 0.25 * (i % 3), 0.75 + 0.05 * i))
    vis(o, 1, False); vis(o, fb + 2 + 3 * i, True)
    key_loc(o, fb + 2 + 3 * i, st, (0, 0, 0)); key_loc(o, fb + 30 + 3 * i, HOLE + Vector((-0.4, 0, 0)), (R_(200), R_(90 * i), R_(60)))
    vis(o, fb + 31 + 3 * i, False)
shot_cam("S02", [(0, (-0.12, -6.75, 1.88), (-1.15, -5.62, 1.0), 26), (1, (-0.16, -6.60, 1.84), (-1.20, -5.60, 1.02), 28)])
# ================================================================== S03: on a Southwest flight (exterior, right side, tail logo)
_begin("S03")
f0, f1 = T["S03"]
shot_cam("S03", [(0, (18.5, -11.0, 0.4), (0.0, -18.6, 3.7), 40), (1, (17.5, -15.5, 0.8), (0.0, -19.2, 3.9), 40)], fstop=11)
# ================================================================== S04: headed to Dallas (exterior, W out of the window, wide)
_begin("S04")
f0, f1 = T["S04"]
for fr in range(f0, f1 + 1, 8): hang_pose(fr, out=0.0, flutter=1.0, t=fr / 60)
shot_cam("S04", [(0, (-4.5, -3.4, 0.25), (-2.0, -5.85, 1.2), 42), (1, (-4.3, -3.8, 0.35), (-2.0, -5.85, 1.2), 46)], fstop=11)
# ================================================================== S05: It happened when an engine (fan spinning)
_begin("S05")
FAN = OB["FAN_L"]; FAN.rotation_mode = 'XYZ'
FAN.rotation_euler = (0, 0, 0); FAN.keyframe_insert("rotation_euler", frame=1)
FAN.rotation_euler = (0, R_(-7.0 * (T["S06"][0] + 30 - 1)), 0); FAN.keyframe_insert("rotation_euler", frame=T["S06"][0] + 30)
FAN.rotation_euler = (0, R_(-7.0 * (T["S06"][0] + 30 - 1) - 2.0 * (sc.frame_end - T["S06"][0] - 30)), 0); FAN.keyframe_insert("rotation_euler", frame=sc.frame_end)
for fc in all_fc(FAN):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
FR_ = OB["FAN_R"]; FR_.rotation_mode = 'XYZ'; FR_.rotation_euler = (0, 0, 0); FR_.keyframe_insert("rotation_euler", frame=1)
FR_.rotation_euler = (0, R_(7.0 * sc.frame_end), 0); FR_.keyframe_insert("rotation_euler", frame=sc.frame_end)
for fc in all_fc(FR_):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
shot_cam("S05", [(0, (-6.4, 2.4, -1.7), (-4.5, -2.4, -0.92), 30), (1, (-5.9, 1.2, -1.5), (-4.5, -2.5, -0.92), 34)], fstop=11)
# ================================================================== S06: broke in the air (arc + blade break off, debris, smoke)
_begin("S06")
f0, f1 = T["S06"]; fb6 = f0 + 30
ARC, BLD = OB["NACELLE_ARC_L"], OB["BLADE_BREAK_L"]
vis(ARC, 1, True); vis(ARC, fb6, False); vis(BLD, 1, True); vis(BLD, fb6, False)
rnd = random.Random(11); lip = Vector((-4.5, -2.15, -0.92))
for i, o in enumerate(DEBRIS[:10]):
    a = R_(rnd.uniform(-15, 75)); st = lip + Vector((0.8 * math.cos(a), -0.05, 0.8 * math.sin(a)))
    v = Vector((rnd.uniform(0.5, 2.5), -rnd.uniform(4, 9), rnd.uniform(0.3, 2.2)))
    vis(o, fb6, True); key_loc(o, fb6, st, (0, 0, 0))
    key_loc(o, f1, st + v, (rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9))); vis(o, f1 + 1, False)
for i, o in enumerate(SMOKE):
    a = R_(rnd.uniform(-20, 80)); st = lip + Vector((0.7 * math.cos(a), 0.0, 0.7 * math.sin(a)))
    vis(o, fb6 + 2 * i, True); key_loc(o, fb6 + 2 * i, st, scale=(0.15, 0.15, 0.15))
    key_loc(o, f1, st + Vector((0.3, -4.5 - i * 0.4, 0.3)), scale=(0.9 + 0.1 * i,) * 3)
    vis(o, f1 + 1, False)
shot_cam("S06", [(0, (-7.4, 1.2, -1.4), (-4.3, -2.6, -0.8), 30), (1, (-7.2, 0.6, -1.2), (-3.9, -3.6, -0.6), 30)], fstop=11)
# ================================================================== S07: causing debris to break a window
_begin("S07")
f0, f1 = T["S07"]; fi = f0 + 46
vis(OB["PANE"], f0, True); vis(OB["PANE"], fi, False)
rnd = random.Random(5)
for i, o in enumerate(DEBRIS[10:14]):
    st = Vector((-4.2 + 0.3 * i, -2.6 - 0.2 * i, -0.4)); tgt = HOLE + Vector((-0.12, rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1)))
    if i: tgt = HOLE + Vector((-0.3 - 0.2 * i, -1.2 - 0.5 * i, 0.4 * i))
    vis(o, f0 + 2, True); key_loc(o, f0 + 2, st, (0, 0, 0)); key_loc(o, fi, tgt, (R_(400), R_(200), 0))
    key_loc(o, fi + 30, tgt + Vector((-1.5, -6, 1.0)), (R_(700), R_(500), 0)); vis(o, fi + 31, False)
rnd = random.Random(9)
for i, o in enumerate(SHARDS):
    h = Vector(o["home"]); v = Vector((-rnd.uniform(1.5, 3.5), -rnd.uniform(3, 7), rnd.uniform(-0.6, 0.9)))
    vis(o, fi, True); key_loc(o, fi, h, (0, 0, 0)); key_loc(o, fi + 36, h + v, (rnd.uniform(-9, 9), rnd.uniform(-9, 9), rnd.uniform(-9, 9)))
    vis(o, fi + 37, False)
shot_cam("S07", [(0, (-7.0, -2.4, -0.7), (-1.6, -5.4, 1.5), 34), (1, (-6.5, -3.2, -0.5), (-1.6, -5.6, 1.5), 38)], fstop=11)
# ================================================================== S08: the cabin to depressurize (masks drop, papers fly)
_begin("S08")
f0, f1 = T["S08"]; fm = f0 + 12
MASKS = [o for o in OB if o.name.startswith("OXYDROP_") and o.type == 'MESH' and "MOUNT" not in o.name]
rnd = random.Random(2)
for o in MASKS:
    home = o.location.copy(); d = rnd.randint(0, 6)
    vis(o, 1, False); vis(o, fm + d, True)
    key_loc(o, fm + d, home + Vector((0, 0, 0.42)), (0, 0, 0)); key_loc(o, fm + d + 9, home - Vector((0, 0, 0.03)))
    key_loc(o, fm + d + 15, home + Vector((0, 0, 0.01)))
    for fr in range(fm + d + 21, sc.frame_end + 1, 20):
        key_loc(o, fr, home, (R_(rnd.uniform(-6, 6)), R_(rnd.uniform(-6, 6)), 0))
for fr in (f0, f1):
    seated(W, fr, -0.99, SEAT_W[1], look_turn=40, hflex=4, side=26, flex=6, arms={"R": (-36, 50, 60, 0)})
    seated(HA, fr, SEAT_A[0], SEAT_A[1], look_turn=-35, hflex=-10, side=-16, arms={"L": (40, 12, 82, 0), "R": (20, 42, 95, 0)})
shot_cam("S08", [(0, (0.15, -3.55, 1.72), (0.35, -8.6, 0.95), 24), (1, (0.12, -3.95, 1.68), (0.30, -8.6, 0.95), 26)])
# ================================================================== S09: and suck the nearby woman out (emerging, exterior)
_begin("S09")
f0, f1 = T["S09"]
for fr in range(f0, f1 + 1, 6):
    u = min(1.0, (fr - f0) / 50.0); u = u * u * (3 - 2 * u)
    hang_pose(fr, out=-0.55 * (1 - u), flutter=u, t=fr / 60)
shot_cam("S09", [(0, (-4.4, -7.5, 1.55), (-1.9, -5.7, 1.2), 42), (1, (-4.2, -7.2, 1.5), (-1.9, -5.7, 1.2), 46)], fstop=11)

# ------------------------------------------------------------------ helpers for the hold / pull shots
def leg_point(s, which, f, up=0.0):
    """world point on the top of W's shin/thigh (which: 'knee', 'shin', 'ankle'), lifted `up` m along world z"""
    sc.frame_set(f); M = W.matrix_world; PB = W.pose.bones
    kn = M @ PB["lowerleg01." + s].head; an = M @ PB["foot." + s].head
    p = {"knee": kn.lerp(an, 0.12), "shin": kn.lerp(an, 0.5), "ankle": kn.lerp(an, 0.85)}[which]
    return p + Vector((0, 0, up))
def stand(rig, f, x, y, yaw, flex=0.0, crouch=0.0, stance=0.9):
    """IK legs: feet planted under the hips in the aisle (yaw deg, 0 = facing -y)"""
    H = HU[rig.name]; R = RG[rig.name]
    if "IK_foot.L" not in rig.pose.bones:          # HB has no leg IK: plain FK standing, feet flat on the floor
        place(rig, f, (x, y, -crouch), (0, 0, R_(yaw)))
        R.key_rot("root", f, [("X", flex * 0.3)])
        for s in "LR": fk_leg(R, s, f, hip=flex * 0.3 + 4, knee=8 + crouch * 60, splay=3, ankle=-4)
        return
    place(rig, f, (0, 0, 0), (0, 0, 0))
    p = Vector((x, y, H.root_head.z - crouch))
    H.key_root(f, p, yaw=yaw, flex=flex)
    for s in "LR":
        fx = H.foot_xy(s, p, yaw); c = Vector((x, y)); fx = c + (fx - c) * stance
        H.key_foot(s, f, fx, yaw)
def grab(rig, s, f, p, finger_dir, palm=(0, 0, -1), skin=0.060):
    place_hand(rig, s, f, p, palm, finger_dir, skin=skin)
    hand_pose(rig, s, f, "wrap_grip")
def brace(rig, s, f, p, finger_dir):
    place_hand(rig, s, f, p, (0, 0, -1), finger_dir, skin=0.014); hand_pose(rig, s, f, "flat_palm")
SEAT5_BACK_TOP = Vector((-0.55, rowy(5) - 0.30, 1.17))

def kneel(rig, f, x, y, yaw, lean=20, z=0.0):
    """kneeling on both knees in the aisle, sitting back a little, hands on the thighs"""
    R = RG[rig.name]; H = HU[rig.name]
    set_ik(rig, f, 0, 0)
    rz = R_(yaw)
    # pelvis height when kneeling ~ thigh length + a little: put the rig root down so the knees touch the floor
    place(rig, f, (x, y, -0.37 + z), (0, 0, rz))
    fk_leg(R, "L", f, hip=20, knee=110, splay=6, ankle=40); fk_leg(R, "R", f, hip=20, knee=110, splay=4, ankle=40)
    fk_spine(R, f, flex=lean, side=0, twist=0, hflex=12, htwist=0)
    fk_arm(R, "L", f, down=78, fwd=22, elbow=28, out=0); fk_arm(R, "R", f, down=78, fwd=22, elbow=28, out=0)
    for s in "LR": hand_pose(rig, s, f, "flat_palm")
def hold_shot(n, fr_list, pull=None, hb=False):
    """W hanging, HA in the aisle holding both shins, HB behind bracing on the seat back"""
    f0, f1 = T[n]
    for fr in fr_list:
        u = 0.0 if pull is None else pull(fr)
        hang_pose(fr, out=-0.30 * u, flutter=0.4 * (1 - u), t=fr / 60, arms_in=min(1.0, 3 * u))
        set_ik(HA, fr, 1, 1)
        # director P1: lean in, elbows bent, hands low on her shins, face toward the 3/4-front camera
        stand(HA, fr, 0.12 + 0.12 * u, -5.60, yaw=-90, flex=18 - 6 * u, crouch=0.05)
        fk_spine(RA, fr, flex=16, side=0, twist=-8, hflex=-26, htwist=(34 if hb else -30))
        sc.frame_set(fr)
        grab(HA, "L", fr, leg_point("L", "ankle", fr), (0, -0.25, -1), skin=0.085)
        grab(HA, "R", fr, leg_point("L", "shin", fr), (0, 0.15, -1), skin=0.11)
        if hb:
            # HB turned round, kneeling on his row-4 aisle seat, reaching back over the seat back to her knee and shin
            kneel(HB, fr, -0.33, -4.60, 0, lean=30, z=0.70)
            set_ik(HB, fr, 1, 0)
            fk_spine(RB, fr, flex=34, side=-6, twist=-10, hflex=-12, htwist=-14)
            sc.frame_set(fr)
            grab(HB, "L", fr, leg_point("R", "shin", fr), (0, -0.15, -1), skin=0.095)
            grab(HB, "R", fr, leg_point("R", "knee", fr), (0, 0.15, -1), skin=0.105)
# ================================================================== S10: out of the plane (interior wide)
_begin("S10")
f0, f1 = T["S10"]
hold_shot("S10", list(range(f0, f1 + 1, 12)) + [f1])
shot_cam("S10", [(0, (-0.45, -4.25, 1.62), (-0.30, -5.70, 1.05), 22), (1, (-0.45, -4.45, 1.58), (-0.30, -5.70, 1.05), 24)])
# ================================================================== S11: the other passengers held on to her (closer)
_begin("S11")
f0, f1 = T["S11"]
hold_shot("S11", list(range(f0, f1 + 1, 12)) + [f1], hb=True)
shot_cam("S11", [(0, (0.22, -6.75, 1.66), (-0.55, -5.25, 1.12), 26), (1, (0.20, -6.55, 1.62), (-0.55, -5.25, 1.12), 28)])
# ================================================================== S12: as she hung halfway out (exterior, orbit)
_begin("S12")
f0, f1 = T["S12"]
for fr in range(f0, f1 + 1, 6): hang_pose(fr, out=0.0, flutter=1.0, t=fr / 60)
shot_cam("S12", [(0, (-4.3, -3.7, 0.55), (-2.0, -5.85, 1.2), 44), (0.5, (-4.7, -4.6, 0.45), (-2.0, -5.9, 1.2), 44), (1, (-4.5, -5.25, 0.6), (-2.0, -5.9, 1.2), 44)], fstop=11)
# ================================================================== S13: after a few minutes they pulled her back in
_begin("S13")
f0, f1 = T["S13"]
def pull(fr):
    u = max(0.0, min(1.0, (fr - f0 - 20) / (f1 - f0 - 40))); return u * u * (3 - 2 * u)
hold_shot("S13", list(range(f0, f1 + 1, 6)) + [f1], pull=pull, hb=True)
shot_cam("S13", [(0, (0.28, -6.85, 1.70), (-0.45, -5.30, 1.08), 24), (1, (0.30, -6.70, 1.66), (-0.40, -5.30, 1.08), 26)])
# ================================================================== S14: back into the plane (lying in the aisle, HA kneels)
_begin("S14")
f0, f1 = T["S14"]
for fr in range(f0, f1 + 1, 30):
    lie_pose(fr, breath=math.sin(fr / 40))
    kneel(HA, fr, 0.0, -7.20, 180, lean=22 + 3 * math.sin(fr / 30))
lie_pose(f1); kneel(HA, f1, 0.0, -7.20, 180, lean=22)
shot_cam("S14", [(0, (0.12, -4.75, 1.40), (0.0, -6.85, 0.55), 26), (1, (0.10, -4.95, 1.36), (0.0, -6.85, 0.55), 29)])
# ================================================================== S15: but she had head trauma (closer, calm)
_begin("S15")
f0, f1 = T["S15"]
for fr in range(f0, f1 + 1, 30):
    lie_pose(fr, breath=math.sin(fr / 40)); kneel(HA, fr, 0.0, -7.20, 180, lean=26)
lie_pose(f1); kneel(HA, f1, 0.0, -7.20, 180, lean=26)
shot_cam("S15", [(0, (0.24, -5.62, 1.30), (0.0, -6.90, 0.55), 27), (1, (0.22, -5.75, 1.26), (0.0, -6.90, 0.55), 29)])
# ================================================================== S16: which unfortunately (exterior window row, broken window)
_begin("S16")
f0, f1 = T["S16"]
shot_cam("S16", [(0, (-6.4, -2.6, -0.5), (-1.6, -6.2, 1.6), 32), (1, (-6.2, -3.1, -0.4), (-1.6, -6.2, 1.6), 34)], fstop=11)
# ================================================================== S17: caused her death (damaged engine)
_begin("S17")
f0, f1 = T["S17"]
for i, o in enumerate(SMOKE[:3]):
    st = lip + Vector((0.6, -0.1, 0.4))
    vis(o, f0, True); key_loc(o, f0, st + Vector((0, -0.3 * i, 0)), scale=(0.25,) * 3); key_loc(o, f1, st + Vector((0.2, -3.5 - i, 0.4)), scale=(0.6,) * 3)
    vis(o, f1 + 1, False)
shot_cam("S17", [(0, (-7.4, 0.6, -2.3), (-4.4, -2.6, -0.85), 34), (1, (-6.6, -0.2, -2.0), (-4.4, -2.6, -0.85), 38)], fstop=11)

# clouds drift past (speed read on the exterior shots)
for o in D.collections["CLOUDS_NEAR"].objects:
    p0 = o.location.copy(); o.keyframe_insert("location", frame=1)
    o.location = p0 + Vector((0, -0.45 * sc.frame_end, 0)); o.keyframe_insert("location", frame=sc.frame_end)
    for fc in all_fc(o):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    o.location = p0; o.keyframe_insert("location", frame=1)
# ------------------------------------------------------------------ hold every hero channel to the end of each shot
_begin(None)
for o in list(OB):
    const_interp(o)
ad = sc.animation_data
if ad and ad.action:
    for fc in all_fc(sc):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
    for pb_c in []: pass
for r in HEROES:
    for fc in all_fc(r):
        if "influence" in fc.data_path:
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# visibility fcurves of hero rigs not keyed: 'away' parks them off set
sc.camera = OB["CAM_S01"]
# lighting: a sun for the exterior, soft cabin fill
sun = OB.get("SUN")
if sun: sun.data.energy = max(sun.data.energy, 4.0)
for l in [o for o in OB if o.type == 'LIGHT' and o.name.startswith("L_cabin")]: l.data.energy *= 1.0
with open(BUILD + "/shots.json", "w") as fh:
    import json; json.dump({n: list(v) for n, v in T.items()}, fh, indent=1)
print("SHOTS", T, "END", sc.frame_end)
bpy.ops.wm.save_as_mainfile(filepath=BUILD + "/p1.blend")
print("P1 saved")
