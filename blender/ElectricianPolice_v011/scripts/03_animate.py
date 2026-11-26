"""ElectricianPolice v011 stage 3: staging, acting, story props, lighting changes and the ONE continuous camera.
blender -b set.blend --python 03_animate.py -- <out.blend> <VO.mp3>
Built to the client's VO from the start (scripts/vo_words.json). Film frames 1-1446 at 60 fps; beat = 1 + round(s*60).
  1   "He got fined by the police"           the officer flags the bike down in front of the police station
  96  "for riding his motorcycle"            the bike rolls to a stop, wheels turning, his foot comes down
  155 "without a helmet"                     the officer points at his bare head
  251 "Big mistake,"                         he smirks, glances up at the pole transformer and the wires
  306 "because he was an electrician"        the camera follows the wires to the substation: Ravi in a hard hat
  396 "with access to the power grid"        crane up: pylons and lines spreading over the town
  515 "So, he dug through the records"       through the control-room window: Ravi at the laptop
  600 "and found the police station ..."     a red row with a police badge; calendar pages flip three times
  882 "The bill was huge,"                   the red bar grows across the screen; he leans back, delighted
  967 "so he cut their power."               he turns to the switchgear and pulls the big lever: sparks, lamp to red
  1080 "For five hours,"                     out of the window, across the street: the station's windows go dark, dusk falls
  1153 "the station sat in total darkness,"  inside: the officer by candlelight fans himself; the clock spins five hours
  1291 "all because they fined the wrong guy." back out to the dusk street: Ravi by his bike, a smirk and a nod"""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline"))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]; VO = args[1]; STOP = args[2] if len(args) > 2 else ""
random.seed(21)
END = 1446
O = bpy.data.objects
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
def upd(): bpy.context.view_layer.update()
def fs(f): sc.frame_set(int(f))
def W(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].matrix
def Wh(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].head
def Wt(rig, bone): return rig.matrix_world @ rig.pose.bones[bone].tail
def frame_from(y_dir, z_hint, origin):
    y = Vector(y_dir).normalized(); z = Vector(z_hint); z = (z - y * z.dot(y)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(origin); return M
def const_interp(obj, path_prefix=None):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            if path_prefix is None or fc.data_path.startswith(path_prefix):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
def key_obj_matrix(o, f, M):
    o.matrix_world = M
    o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
def MZ(loc, yaw_deg):
    return Matrix.Translation(Vector(loc)) @ Matrix.Rotation(R_(yaw_deg), 4, 'Z')

M = {"blackm": bpy.data.materials.get("M_BlackMetal") or mat("M_BlackMetal", (0.03, 0.03, 0.035), rough=0.4, metal=0.6)}
RAVI, OFF = O["Ravi"], O["Officer"]
RB, OB = part(RAVI, ".body"), part(OFF, ".body")
BIKE = O[sc["BIKE"]]
EX, WX = sc["EX"], sc["WX"]
RIG = {}
for r in (RAVI, OFF):
    RIG[r.name] = make_human_ctrl(r); add_hand_limits(r)
    for pb in r.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in "LR":
        lo = r.pose.bones["lowerarm01." + s_]; lo.use_ik_limit_x = True; lo.ik_min_x = R_(-30); lo.ik_max_x = R_(145)
# the tool hands get their wrist solved by the IK target rotation (no clamp fighting it)
for r in (RAVI, OFF):
    for s_ in "LR":
        for c in list(r.pose.bones["wrist." + s_].constraints):
            if c.name == "HandLimit": r.pose.bones["wrist." + s_].constraints.remove(c)
HU = {n: Human(RIG[n]) for n in RIG}
RR, RO = RIG["Ravi"], RIG["Officer"]; HR, HO = HU["Ravi"], HU["Officer"]

def hand_world(rig, s, f, W_wrist, fdir, palm, pole=None):
    Mi = rig.matrix_world.inverted(); R3 = Mi.to_3x3()
    HU[rig.name].key_hand(s, f, Mi @ Vector(W_wrist), R3 @ Vector(fdir), R3 @ Vector(palm), pole=None if pole is None else Mi @ Vector(pole))
def key_pole_world(rig, s, f, pole_w):
    R = RIG[rig.name]; n = "Pole_elbow." + s; pb = R.PB[n]
    p = rig.matrix_world.inverted() @ Vector(pole_w)
    pb.location = R.rest(n).to_3x3().inverted() @ (p - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
def copy_bone_keys(rig, names, f_src, f_dsts):
    fs(f_src)
    vals = {n: (rig.pose.bones[n].location.copy(), rig.pose.bones[n].rotation_quaternion.copy()) for n in names}
    for f in f_dsts:
        for n, (l, q) in vals.items():
            pb = rig.pose.bones[n]; pb.location = l; pb.rotation_quaternion = q
            pb.keyframe_insert("location", frame=f, group=n); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
FINGERS = lambda s: [_b(k, j, s) for k in (1, 2, 3, 4, 5) for j in (1, 2, 3)]

# ------------------------------------------------------------------ faces (numeric axis finding, from the approved rebuilds)
def lid_sign(rig, s):
    pb = rig.pose.bones["orbicularis03." + s]; upd()
    t0 = Wt(rig, pb.name).z; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(20)); upd(); t1 = Wt(rig, pb.name).z
    pb.rotation_quaternion = Quaternion(); upd()
    return 1.0 if t1 < t0 else -1.0
def blinks(rig, frames, base=0.0):
    for s in "LR":
        n = "orbicularis03." + s
        if n not in rig.pose.bones: continue
        sg = lid_sign(rig, s); pb = rig.pose.bones[n]
        def lid(f, ang):
            pb.rotation_quaternion = Quaternion((1, 0, 0), R_(ang * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
        lid(1, base)
        for bf in frames:
            lid(bf, base); lid(bf + 4, 24); lid(bf + 7, 24); lid(bf + 13, base)
def corner_axis(rig, bone, want):
    pb = rig.pose.bones[bone]; upd(); base = Wt(rig, bone); best = None
    for ax in ((1, 0, 0), (0, 0, 1), (0, 1, 0)):
        for sg in (1, -1):
            pb.rotation_quaternion = Quaternion(ax, R_(12 * sg)); upd()
            d = rig.matrix_world.inverted().to_3x3() @ (Wt(rig, bone) - base)
            v = d.dot(want)
            if best is None or v > best[0]: best = (v, ax, sg)
    pb.rotation_quaternion = Quaternion(); upd()
    return best
def expression(rig, keys, bones_want):
    for bone, (want, deg) in bones_want.items():
        if bone not in rig.pose.bones: continue
        _, ax, sg = corner_axis(rig, bone, Vector(want))
        pb = rig.pose.bones[bone]
        for f, amt in keys:
            pb.rotation_quaternion = Quaternion(ax, R_(deg * sg * amt)); pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)
def jaw_talk(rig, f0, f1, amp=6.0, seed=1):
    _, ax, sg = corner_axis(rig, "jaw", Vector((0, 0, -1)))
    pb = rig.pose.bones["jaw"]; rr = random.Random(seed)
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f0 - 4, group="jaw")
    f = f0
    while f < f1:
        a_ = rr.uniform(0.3, 1.0) * amp
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
        f += rr.randint(6, 10)
        pb.rotation_quaternion = Quaternion(ax, R_(a_ * 0.25 * sg)); pb.keyframe_insert("rotation_quaternion", frame=f, group="jaw")
        f += rr.randint(4, 8)
    pb.rotation_quaternion = Quaternion(); pb.keyframe_insert("rotation_quaternion", frame=f1 + 4, group="jaw")
SMILE = {"risorius03.L": ((1, 0, 0.6), 14), "risorius03.R": ((-1, 0, 0.6), 14), "levator05.L": ((0.3, 0, 1), 10), "levator05.R": ((-0.3, 0, 1), 10),
         "oris04.L": ((1, 0, 0.5), 10), "oris04.R": ((-1, 0, 0.5), 10)}
SMIRK = {"risorius03.L": ((1, 0, 0.7), 16), "levator05.L": ((0.3, 0, 1), 12), "oris04.L": ((1, 0, 0.5), 10)}
FROWN = {"risorius03.L": ((1, 0, -0.5), 10), "risorius03.R": ((-1, 0, -0.5), 10), "oris04.L": ((1, 0, -0.5), 7), "oris04.R": ((-1, 0, -0.5), 7)}

# ------------------------------------------------------------------ body helpers
def look_angles(rig, f, target, base_yaw=0.0, flex=0.0, twist=0.0):
    """head (pitch, yaw) in degrees so the face points at `target` (world); rotations are about armature axes,
    forward = -Y; spine twist/root yaw already turn the head, so they are subtracted"""
    fs(f)
    hp = Wh(rig, "head") + rig.matrix_world.to_3x3() @ Vector((0, 0, 0.08))
    d = rig.matrix_world.inverted().to_3x3() @ (Vector(target) - hp)
    yaw = math.degrees(math.atan2(d.x, -d.y)) - base_yaw - twist
    pitch = math.degrees(math.atan2(-d.z, math.hypot(d.x, d.y))) - flex
    return max(-40, min(40, pitch)), max(-70, min(70, yaw))
def stand_feet(R, H, f, dx=0.0, dy=0.0, yaw=0.0, spread=0.0):
    for s in "LR":
        a = R.BN["foot." + s].head_local
        sx = 1 if s == "L" else -1
        off = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((a.x + sx * spread, a.y - H.root_head.y, 0))
        H.key_foot(s, f, Vector((dx + off.x, dy + off.y)), yaw, 0.0, 0.0)
def hang(rig, s, f, out=0.10, fwd=-0.03, down=0.07, swing=0.0):
    """a relaxed hanging arm: elbow bent ~20 deg, hand beside the thigh, >= 4 cm off the trousers"""
    sx = 1 if s == "L" else -1; fs(f); Mw = rig.matrix_world; R3 = Mw.to_3x3()
    sh = Wh(rig, "upperarm01." + s)
    wr = Wh(rig, "upperleg01." + s) + R3 @ Vector((sx * (out + 0.06), fwd - swing, -down - 0.02))
    hand_world(rig, s, f, wr, R3 @ Vector((sx * 0.08, -0.22, -1)), R3 @ Vector((-sx, 0.15, 0)),
               pole=sh + R3 @ Vector((sx * 0.35, 0.55, -0.35)))
    apply_pose(rig, s, "relaxed", f)
def breathe(H, R, f0, f1, base_pos, yaw=0.0, flex=0.0, step=10, amp=0.004, head=None, twist=0.0, sway=0.004):
    for f in range(f0, f1 + 1, step):
        ph = f / 60.0
        p = base_pos + Vector((sway * math.sin(ph * 2 * math.pi / 3.3), 0, -amp * (1 + math.sin(ph * 2 * math.pi / 3.8))))
        H.key_root(f, p, yaw=yaw)
        hd = head(f) if callable(head) else (head or (0, 0))
        H.key_spine(f, flex=flex + 1.2 * math.sin(ph * 2 * math.pi / 3.8), twist=twist, head=hd)

# ------------------------------------------------------------------ the tool/prop grip (Child Of the wrist bone, R4)
def prop_in_hand(rig, side, prop, f_setup, grip_y=-0.10, along=0.0, name="Hand"):
    """prop's local +Y along the fingers, its local Z across the palm, positioned between thumb and index tips;
    Child Of the wrist so it never moves without the hand"""
    fs(f_setup); upd()
    th = Wt(rig, "finger1-3." + side); ix = Wt(rig, "finger2-3." + side)
    G = (th + ix) / 2
    fdir = (Wt(rig, "finger3-3." + side) - Wh(rig, "finger3-1." + side)).normalized()
    wr = Wh(rig, "wrist." + side)
    across = (Wh(rig, "finger2-1." + side) - Wh(rig, "finger5-1." + side)).normalized()
    palmN = fdir.cross(across) if side == "L" else across.cross(fdir)
    if (G - (wr + fdir * 0.05)).dot(palmN) < 0: palmN = -palmN
    T = frame_from(fdir, palmN, G) @ Matrix.Translation(Vector((along, -grip_y, 0)))
    prop.matrix_world = T
    c = prop.constraints.new('CHILD_OF'); c.name = name; c.target = rig; c.subtarget = "wrist." + side
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones["wrist." + side].matrix).inverted()
    return c

# ================================================================== RAVI on the BIKE (1-321)
F_YARD = 322; F_CTRL = 452; F_END = 1292
def bike_y(f):
    # 10 m/s, constant deceleration to a stop at y = 0 by frame 118
    T = 117.0; t = min(max(f - 1, 0), T)
    return -10.0 + 10.0 * (t / T) * (2 - t / T) * 1.0 - 0.0 if True else 0
BX = 2.3
for f in list(range(1, 121, 1)):
    BIKE.location = (BX, bike_y(f) * 1.0, 0.0); BIKE.keyframe_insert("location", frame=f)
# wheels: radius 0.26, rolling with the distance travelled
for tag in ("F", "R"):
    w_ = O["Bike_wheel" + tag]
    for f in range(1, 121, 2):
        w_.rotation_euler = ((bike_y(f) + 10.0) / 0.26, 0, 0); w_.keyframe_insert("rotation_euler", frame=f)
def M_RIDE(f): return Matrix.Translation(Vector((BX, bike_y(f), 0.0))) @ Matrix.Rotation(math.pi, 4, 'Z')
for f in range(1, 121):
    key_obj_matrix(RAVI, f, M_RIDE(f))
# yard and control room and the end (teleports while he is off camera; ONE model)
M_YARD = MZ((-9.4, 19.4, 0.01), 125.0)
CON = sc["CON"]; LAP_BB = sc["LAP_BB"]; SWG = sc["SWG_BB"]
RAVI_CX = CON[0] - CON[4] / 2 - 0.25        # 25 cm behind the counter edge (body centre)
RAVI_CY = 2.72
M_CTRL = MZ((RAVI_CX, RAVI_CY, 0.05), 90.0)  # faces +x (the window)
M_ENDP = MZ((3.35, -0.55, 0.0), 90.0)        # on the road beside his bike, facing the station (+x)
key_obj_matrix(RAVI, F_YARD, M_YARD); key_obj_matrix(RAVI, F_CTRL, M_CTRL); key_obj_matrix(RAVI, F_END, M_ENDP)
const_interp(RAVI)
for f in (F_YARD - 1,):
    key_obj_matrix(RAVI, f, M_RIDE(120))
const_interp(RAVI)
# wardrobe/hair visibility: hard hat for the yard + control room
HAT, HAIR_F, HAIR_H = O["Ravi.hardhat"], O["Ravi.hair_full"], O["Ravi.hair_hat"]
key_vis([HAT, HAIR_H], 1, False); key_vis([HAIR_F], 1, True)
key_vis([HAT, HAIR_H], F_YARD, True); key_vis([HAIR_F], F_YARD, False)
key_vis([HAT, HAIR_H], F_END, False); key_vis([HAIR_F], F_END, True)

# seated on the bike: hips on the seat, feet on the pegs, hands on the grips
fs(1)
hipL = RR.BN["upperleg01.L"].head_local; rootH = HR.root_head
SEAT = Vector((0.0, 0.27, 0.723 + 0.105))           # hip-joint height above the seat top (rig local; bike seat y=-0.25)
ROOT_RIDE = rootH + Vector((0.0, SEAT.y - hipL.y, SEAT.z - hipL.z))
log("root rest", tuple(round(x, 3) for x in rootH), "hip", tuple(round(x, 3) for x in hipL), "ride root", tuple(round(x, 3) for x in ROOT_RIDE))
PEG = {"L": Vector((0.20, 0.06)), "R": Vector((-0.20, 0.06))}
def ride_body(f, lean=18.0, head=(0, 0), twist=0.0, foot_down=0.0):
    ph = f / 60.0
    HR.key_root(f, ROOT_RIDE + Vector((0.004 * math.sin(ph * 5.0), 0, 0.003 * math.sin(ph * 7.0))), yaw=0.0)
    HR.key_spine(f, flex=lean, twist=twist, head=head)
    for s in "LR":
        if s == "L" and foot_down > 0:
            p = PEG["L"].lerp(Vector((0.36, 0.10)), foot_down)
            HR.key_foot(s, f, p, 8.0 * foot_down, 0.36 * (1 - foot_down) + 0.05 * math.sin(math.pi * foot_down), -12 * (1 - foot_down))
        else:
            HR.key_foot(s, f, PEG[s], 0.0, 0.36, -12.0)
# head: rides looking ahead, then turns to the officer (on his right), annoyed, then to the camera / up at the wires (set after the camera)
for f in range(1, 96, 6): ride_body(f, lean=18.0, head=(8, 0))
for f, fd in ((96, 0.0), (104, 0.25), (112, 0.75), (118, 1.0)):
    ride_body(f, lean=14.0, head=(6, -10 * fd), foot_down=fd)
for f in range(124, F_YARD, 8): ride_body(f, lean=8.0, foot_down=1.0)
ride_body(F_YARD - 1, lean=8.0, foot_down=1.0)
# hand grips: helper bars at the bike's grips (bike-local x +-0.222, y 0.25, z 0.98), wrap grip, then held constant
fs(1); upd()
GRIP_HELP = {}
for s, bxl in (("L", -0.222), ("R", 0.222)):
    c = cyl("GripHelper" + s, 0.017, 0.11, (0, 0, 0), M["metal"] if False else mat("M_GripH", (0, 0, 0)), rot=(0, math.pi / 2, 0), verts=16)
    c.matrix_world = BIKE.matrix_world @ Matrix.Translation(Vector((bxl + (0.02 if bxl > 0 else -0.02), 0.25, 0.98))) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    GRIP_HELP[s] = c
upd()
for s in "LR":
    sx = 1 if s == "L" else -1
    rep = grip_object(RAVI, s, 1, GRIP_HELP[s], GRIP_HELP[s].matrix_world.translation, Vector((0, 0.45, -1.0)).normalized())
    log("ride grip", s, rep)
    key_pole_world(RAVI, s, 1, Wh(RAVI, "upperarm01." + s) + RAVI.matrix_world.to_3x3() @ Vector((sx * 0.45, 0.35, -0.25)))
hand_bones = ["IK_hand.L", "IK_hand.R", "Pole_elbow.L", "Pole_elbow.R"] + FINGERS("L") + FINGERS("R")
copy_bone_keys(RAVI, hand_bones, 1, [F_YARD - 1])
for c in GRIP_HELP.values(): bpy.data.objects.remove(c, do_unlink=True)
# expressions on the bike: annoyed frown at the officer, then the smirk at "Big mistake"
expression(RAVI, [(1, 0), (140, 0), (160, 1.0), (240, 1.0), (256, 0.0), (F_YARD, 0.0)], FROWN)
expression(RAVI, [(1, 0), (250, 0), (268, 1.0), (300, 1.0), (318, 0.3), (F_YARD, 0.0)], SMIRK)

# ================================================================== the OFFICER on the sidewalk (1-699), then at his desk in the dark station
F_OFF_IN = 700
OFF_P = Vector((4.62, 1.05, 0.15))
def off_yaw_to(target):
    d = Vector(target) - OFF_P; return math.degrees(math.atan2(-d.x, d.y)) + 180.0
OYAW = off_yaw_to((BX, -1.0, 0))
M_OFF_ST = MZ(OFF_P, OYAW)
DESK = sc["ST_DESK"]; DTOP = sc["ST_DESK_TOP"]
M_OFF_DESK = MZ((DESK[0] + 0.475 + 0.24, DESK[1], 0.05), -90.0)     # behind the desk, faces -x (the window)
key_obj_matrix(OFF, 1, M_OFF_ST); key_obj_matrix(OFF, F_OFF_IN, M_OFF_DESK); const_interp(OFF)
log("officer yaw", round(OYAW, 1))
fs(1)
OBASE = HO.root_head.copy()
for f in (1, F_OFF_IN - 1):
    stand_feet(RO, HO, f, spread=0.03)
breathe(HO, RO, 1, F_OFF_IN - 1, OBASE, step=12)
# left hand: the ticket pad (clipboard asset) held at the waist, board on the fingers, thumb on top
fs(1); R3 = OFF.matrix_world.to_3x3()
def pad_hold(f, up=0.0):
    fs(f); R3 = OFF.matrix_world.to_3x3()
    wr = Wh(OFF, "upperleg01.L") + R3 @ Vector((0.04, -0.27, 0.16 + up))
    hand_world(OFF, "L", f, wr, R3 @ Vector((-0.75, -0.55, 0.15)), R3 @ Vector((0.0, -0.25, 1.0)),
               pole=Wh(OFF, "upperarm01.L") + R3 @ Vector((0.45, 0.35, -0.3)))
    apply_pose(OFF, "L", "hold_flat_object", f)
for f in (1, 150, 240, 330, F_OFF_IN - 1): pad_hold(f, up=0.02 * math.sin(f))
# right hand: palm up 'stop' (1-95), lowers, points at Ravi's bare head (155-235), relaxed after
def off_stop(f):
    fs(f); R3 = OFF.matrix_world.to_3x3()
    sh = Wh(OFF, "upperarm01.R")
    wr = sh + R3 @ Vector((-0.10, -0.36, 0.22))
    hand_world(OFF, "R", f, wr, R3 @ Vector((0.05, -0.25, 1.0)), R3 @ Vector((0, -1, 0.1)), pole=sh + R3 @ Vector((-0.45, 0.2, -0.45)))
    apply_pose(OFF, "R", "shield", f)
def off_point(f, target):
    fs(f); sh = Wh(OFF, "upperarm01.R"); d = (Vector(target) - sh).normalized()
    R3 = OFF.matrix_world.to_3x3()
    wr = sh + d * 0.46 + Vector((0, 0, -0.06))
    hand_world(OFF, "R", f, wr, d, Vector((0, 0, -1)), pole=sh + R3 @ Vector((-0.45, 0.25, -0.4)))
    apply_pose(OFF, "R", "point", f)
hang(OFF, "R", 1)
for f in (8, 30, 70, 92): off_stop(f)
hang(OFF, "R", 118)
fs(170); RHEAD = Wh(RAVI, "head") + Vector((0, 0, 0.12))
for f in (150, 165, 200, 232): off_point(f, RHEAD)
for f in (252, 330, 460, 600, F_OFF_IN - 1): hang(OFF, "R", f, swing=0.01 * ((f // 10) % 2))
# the officer's head: on the rider, a stern nod on "fine", talks while pointing
oh = [(1, 8, 10), (60, 4, 12), (90, -2, 12), (150, 2, 8), (200, 6, 6), (250, 0, 4), (400, 2, 8), (F_OFF_IN - 1, 2, 8)]
for f, p, y in oh:
    pass
jaw_talk(OFF, 20, 80, amp=6, seed=3); jaw_talk(OFF, 160, 228, amp=7, seed=4)
expression(OFF, [(1, 0.6), (F_OFF_IN - 1, 0.6), (F_OFF_IN, 1.0), (END, 1.0)], FROWN)
blinks(OFF, [50, 170, 300, 520, 1170, 1240])

# the ticket pad: one prop, Child Of his left wrist the whole time
fs(1); upd()
PAD = O["Ticket_Pad"] if "Ticket_Pad" in O else None
if PAD is None:
    src = [o for o in O if o.name.startswith("P_clipboard")]
    PAD = box("Ticket_Pad", (0.16, 0.22, 0.012), (0, 0, 0), mat("M_TicketPad", (0.95, 0.93, 0.80), rough=0.5), bevel=0.003)
    box("Ticket_Pad_top", (0.16, 0.05, 0.016), (0, 0.085, 0.002), mat("M_TicketPadTop", (0.75, 0.05, 0.05), rough=0.5), bevel=0.003, parent=PAD)
prop_in_hand(OFF, "L", PAD, 1, grip_y=-0.09)

# ================================================================== RAVI in the YARD (322-451): hard hat, beside the transformer
fs(F_YARD)
YBASE = HR.root_head.copy()
for f in (F_YARD, F_CTRL - 1): stand_feet(RR, HR, f, spread=0.03)
for f in range(F_YARD, F_CTRL, 10):
    HR.key_root(f, YBASE + Vector((0.004 * math.sin(f / 20), 0, -0.004 * (1 + math.sin(f / 23)))))
for s in "LR":
    for f in (F_YARD, 380, 420, F_CTRL - 1): hang(RAVI, s, f, swing=0.01 * (f % 2))

# ================================================================== RAVI at the CONTROL ROOM console (452-1291)
fs(F_CTRL)
CBASE = HR.root_head.copy() + Vector((0, 0, 0))
KEY_C = Vector((CON[0] - 0.12, 2.80, CON[3] + 0.035))       # keyboard centre (laptop base, Ravi's side)
def typing(f, k=0):
    fs(f)
    for s, dy in (("L", 0.085), ("R", -0.085)):
        bob = 0.006 * math.sin(f * 0.9 + (0 if s == "L" else 1.7))
        p = KEY_C + Vector((-0.02, dy, 0.012 + bob))
        place_hand(RAVI, s, f, p, Vector((0, 0, -1)), Vector((1, -0.15 * (1 if s == "L" else -1), -0.12)), skin=0.018)
        sx = 1 if s == "L" else -1
        key_pole_world(RAVI, s, f, Wh(RAVI, "upperarm01." + s) + Vector((-0.3, sx * 0.45, -0.45)))
        apply_pose(RAVI, s, "relaxed", f)
F_TURN = 975; F_GRAB = 1004; F_PULL0 = 1010; F_PULL1 = 1030; F_LET = 1052
for f in (F_CTRL, F_CTRL + 1) + tuple(range(F_CTRL + 6, 870, 6)) + (870,):
    typing(f)
# lean in at the discovery (600-700), grin (700-880), lean back delighted at "huge" (882-960)
LEAN = pchip([(F_CTRL, 10), (600, 10), (650, 22), (860, 22), (895, -6), (955, -4), (F_TURN, 4)])
for f in range(F_CTRL, F_TURN, 8):
    HR.key_root(f, CBASE + Vector((0.003 * math.sin(f / 21), 0.0, -0.004 * (1 + math.sin(f / 25)))))
    HR.key_spine(f, flex=LEAN(f), head=(6 - 0.3 * LEAN(f), 0))
for f in (F_CTRL, 880): stand_feet(RR, HR, f, spread=0.03)
# hands up off the keys as he leans back (880-960): relaxed in front of the chest, a small fist-pump of delight
def chest_hands(f, up=0.0, out=0.0):
    fs(f); R3 = RAVI.matrix_world.to_3x3()
    for s in "LR":
        sx = 1 if s == "L" else -1
        sh = Wh(RAVI, "upperarm01." + s)
        wr = sh + R3 @ Vector((sx * (0.10 + out), -0.26, -0.32 + up))
        hand_world(RAVI, s, f, wr, R3 @ Vector((-sx * 0.3, -0.5, 0.8)), R3 @ Vector((-sx, -0.3, 0)), pole=sh + R3 @ Vector((sx * 0.45, 0.3, -0.4)))
        apply_pose(RAVI, s, "power_fist" if up > 0.05 else "relaxed", f)
chest_hands(892, 0.0); chest_hands(910, 0.10, 0.02); chest_hands(926, 0.04); chest_hands(940, 0.11, 0.02); chest_hands(958, 0.02)
expression(RAVI, [(F_CTRL, 0), (640, 0), (700, 0.6), (820, 1.0), (880, 1.0), (900, 1.0), (960, 0.8), (1060, 0.8), (1070, 1.0), (F_END - 1, 0.6)], SMILE)

# the turn to the switchgear (975-1003): right turn of 90 deg in place with a small step, then the lever pull
LEV = {}
sw_x0, sw_y0, sw_z0, sw_x1, sw_y1, sw_z1 = SWG
LEV["pivot"] = Vector((min(sw_x1 - 0.2, RAVI_CX - 0.20), sw_y1 + 0.07, 1.28))
log("switchgear bb", [round(x, 2) for x in SWG], "lever pivot", tuple(round(x, 2) for x in LEV["pivot"]))
def lever_world(theta_deg):
    th = R_(theta_deg)
    return LEV["pivot"] + Vector((0, math.sin(th), math.cos(th))) * 0.32
# lever parts: plate, pivot boss, arm, red grip bar (axis along x), the contact blades in a slotted box above
lev_m = mat("M_LeverArm", (0.75, 0.75, 0.78), rough=0.3, metal=0.9); red_m = mat("M_LeverGrip", (0.85, 0.03, 0.02), rough=0.35, coat=0.4)
plate = box("Lever_plate", (0.26, 0.025, 0.62), LEV["pivot"] + Vector((0, -0.05, 0.12)), mat("M_LeverPlate", (0.95, 0.75, 0.05), rough=0.4), bevel=0.01)
boss = cyl("Lever_boss", 0.035, 0.09, LEV["pivot"], M["blackm"], rot=(0, math.pi / 2, 0), verts=20)
ARM = empty("Lever_pivot", LEV["pivot"])
arm = box("Lever_arm", (0.025, 0.025, 0.32), LEV["pivot"] + Vector((0, 0, 0.16)), lev_m, bevel=0.004); arm.parent = ARM; arm.matrix_parent_inverse = ARM.matrix_world.inverted()
grip = cyl("Lever_grip", 0.019, 0.15, LEV["pivot"] + Vector((0, 0, 0.32)), red_m, rot=(0, math.pi / 2, 0), verts=20); grip.parent = ARM; grip.matrix_parent_inverse = ARM.matrix_world.inverted()
cbox = box("Lever_contacts", (0.22, 0.10, 0.12), LEV["pivot"] + Vector((0, -0.01, 0.52)), M["blackm"], bevel=0.01)
LAMP_G = sphere("Lever_lampGreen", 0.022, LEV["pivot"] + Vector((0.10, -0.035, -0.12)), mat("M_LampG", (0.1, 1, 0.2), emit=((0.1, 1.0, 0.2), 6.0)), segs=12)
LAMP_R = sphere("Lever_lampRed", 0.022, LEV["pivot"] + Vector((-0.10, -0.035, -0.12)), mat("M_LampR", (1, 0.05, 0.02), emit=((1.0, 0.05, 0.02), 0.0)), segs=12)
TH_ON, TH_OFF = 18.0, 150.0
ARM.rotation_euler = (R_(-TH_ON), 0, 0); ARM.keyframe_insert("rotation_euler", frame=1)
ARM.keyframe_insert("rotation_euler", frame=F_PULL0)
ARM.rotation_euler = (R_(-TH_OFF), 0, 0); ARM.keyframe_insert("rotation_euler", frame=F_PULL1)
for fc in iter_fcurves(ARM.animation_data.action):
    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN'
upd()
# rotation sign: the grip must swing OUT toward Ravi (+y) and down
fs(F_PULL0 + 10); log("lever grip mid", tuple(round(x, 2) for x in grip.matrix_world.translation))
for m_, f, e in ((LAMP_G.data.materials[0], F_PULL1, 0.0), (LAMP_R.data.materials[0], F_PULL1, 8.0)):
    p = m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    p.default_value = 6.0 if m_ is LAMP_G.data.materials[0] else 0.0; p.keyframe_insert("default_value", frame=F_PULL1 - 1)
    p.default_value = e; p.keyframe_insert("default_value", frame=F_PULL1)
# sparks from the contact box at the cut (keyed meshes; small, bright, falling)
spark_m = mat("M_Spark", (1, 0.8, 0.3), emit=((1.0, 0.75, 0.25), 40.0))
rs = random.Random(5)
for k in range(26):
    s_ = sphere("Spark%d" % k, 0.006, (0, 0, 0), spark_m, segs=6); s_.scale = (1, 1, 2.5)
    p0 = LEV["pivot"] + Vector((rs.uniform(-0.09, 0.09), 0.05, 0.50))
    v = Vector((rs.uniform(-0.8, 0.8), rs.uniform(0.6, 1.6), rs.uniform(0.2, 1.4)))
    f0 = F_PULL1 - 2 + rs.randint(0, 6); life = rs.randint(14, 26)
    key_vis([s_], 1, False); key_vis([s_], f0, True); key_vis([s_], f0 + life, False)
    for j in range(0, life + 1, 2):
        t = j / 60.0
        s_.location = p0 + v * t + Vector((0, 0, -4.9 * t * t)); s_.keyframe_insert("location", frame=f0 + j)
flash = bpy.data.lights.new("ArcFlash", 'POINT'); flash.color = (0.7, 0.85, 1.0); flash.shadow_soft_size = 0.05
fo = bpy.data.objects.new("ArcFlash", flash); sc.collection.objects.link(fo); fo.location = LEV["pivot"] + Vector((0, 0.2, 0.5))
for f, e in ((1, 0), (F_PULL1 - 2, 0), (F_PULL1, 120), (F_PULL1 + 4, 30), (F_PULL1 + 8, 90), (F_PULL1 + 14, 0)):
    flash.energy = e; flash.keyframe_insert("energy", frame=f)

# Ravi's body for the turn + pull (root yaw -90 about his centre, a 15 cm step toward the cabinet = local -x)
fs(F_TURN)
def ctrl_body(f, yaw, step, flex, head=(4, 0)):
    HR.key_root(f, CBASE + Vector((-step, 0, -0.004)), yaw=yaw)
    HR.key_spine(f, flex=flex, head=head)
for f, yw, st, fl in ((F_TURN, 0, 0, 4), (985, -35, 0.05, 6), (995, -80, 0.12, 8), (1003, -90, 0.15, 10), (F_PULL1, -90, 0.15, 18), (1045, -90, 0.15, 10), (F_LET, -90, 0.15, 6), (1070, -82, 0.15, 4), (F_END - 1, -82, 0.15, 4)):
    ctrl_body(f, yw, st, fl)
# feet: plant / lift / plant (the right foot steps first, then the left), no sliding
def ctrl_feet(f, yaw, step, lift_s=None, lift=0.0):
    for s in "LR":
        a = RR.BN["foot." + s].head_local
        sx = 1 if s == "L" else -1
        off = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((a.x + sx * 0.03, a.y - HR.root_head.y, 0))
        HR.key_foot(s, f, Vector((-step + off.x, off.y)), yaw, lift if s == lift_s else 0.0, 0.0)
ctrl_feet(F_TURN, 0, 0); ctrl_feet(983, -25, 0.03, "R", 0.06); ctrl_feet(990, -45, 0.06, None)
ctrl_feet(996, -70, 0.10, "L", 0.06); ctrl_feet(1003, -90, 0.15, None); ctrl_feet(F_END - 1, -90, 0.15, None)
# hands: off the keys (975), relaxed during the turn, right hand to the lever grip; the left hangs
typing(F_TURN - 4)
hang(RAVI, "L", 990); hang(RAVI, "R", 990)
for f in (1010, 1040, F_LET, 1070, F_END - 1): hang(RAVI, "L", f)
# right hand on the lever: wrap grip solved once on the grip (lever up), then carried along the arc frame by frame
fs(F_GRAB); upd()
gw = grip.matrix_world.translation.copy()
rep = grip_object(RAVI, "R", F_GRAB, grip, gw, Vector((0, -0.55, -0.85)).normalized())
log("lever grip", rep)
key_pole_world(RAVI, "R", F_GRAB, Wh(RAVI, "upperarm01.R") + Vector((-0.45, 0.3, -0.35)))
fs(F_GRAB); upd()
Mgrip_arm = RAVI.pose.bones["IK_hand.R"].matrix.copy()
REL = (RAVI.matrix_world.inverted() @ grip.matrix_world).inverted() @ Mgrip_arm
for f in range(F_GRAB, F_PULL1 + 16, 2):
    fs(f); upd()
    Marm = (RAVI.matrix_world.inverted() @ grip.matrix_world) @ REL
    RR.key_world("IK_hand.R", f, RR.rest("IK_hand.R") @ (RR.rest("IK_hand.R").inverted() @ Marm) if False else Marm)
    key_pole_world(RAVI, "R", f, Wh(RAVI, "upperarm01.R") + Vector((-0.5, 0.25, -0.3)))
copy_bone_keys(RAVI, FINGERS("R"), F_GRAB, [F_PULL1 + 14])
# approach and release
hang(RAVI, "R", 993)
fs(998); R3 = RAVI.matrix_world.to_3x3()
hand_world(RAVI, "R", 998, gw + Vector((0.0, 0.12, 0.10)), Vector((0, -0.5, -0.6)), Vector((0, -0.6, -0.8)), pole=Wh(RAVI, "upperarm01.R") + Vector((-0.45, 0.3, -0.35)))
apply_pose(RAVI, "R", "open_alarm", 998)
fs(F_PULL1 + 24); hand_world(RAVI, "R", F_PULL1 + 24, lever_world(TH_OFF) + Vector((-0.04, 0.12, 0.10)), Vector((0, -0.3, -1)), Vector((0.5, -0.4, -0.6)), pole=Wh(RAVI, "upperarm01.R") + Vector((-0.45, 0.3, -0.35)))
apply_pose(RAVI, "R", "relaxed", F_PULL1 + 24)
for f in (F_LET + 6, 1075, F_END - 1): hang(RAVI, "R", f)

# ================================================================== the laptop screen UI (no text): building rows, the police row, calendar, the bill bar
lx0, ly0, lz0, lx1, ly1, lz1 = LAP_BB
SCR_C = Vector((lx1 - 0.045, (ly0 + ly1) / 2, lz0 + 0.30))
scr_h, scr_w = 0.26, 0.40
ui_bg = mat("M_UI_bg", (0.02, 0.05, 0.12), emit=((0.03, 0.08, 0.20), 2.5))
UI = empty("UI_root", SCR_C)
def ui_quad(name, w, h, pos2, material, z=0.002):
    o = box(name, (0.002, w, h), SCR_C + Vector((-z, pos2[0], pos2[1])), material, bevel=0)
    o.parent = UI; o.matrix_parent_inverse = UI.matrix_world.inverted(); return o
ui_quad("UI_bg", scr_w * 0.96, scr_h * 0.92, (0, 0), ui_bg, z=0.001)
row_cols = [(0.10, 0.55, 0.95), (0.15, 0.75, 0.45), (0.95, 0.75, 0.10), (0.20, 0.65, 0.95), (0.55, 0.85, 0.30), (0.10, 0.55, 0.95), (0.95, 0.75, 0.10)]
ROWS = []
for k in range(14):
    yz = 0.09 - k * 0.04
    rbg = ui_quad("UI_row%d" % k, scr_w * 0.88, 0.032, (0, yz), mat("M_UIrow%d" % (k % 2), (0.08, 0.14, 0.28), emit=((0.08, 0.16, 0.32), 2.0)), z=0.002)
    icon = ui_quad("UI_icon%d" % k, 0.022, 0.022, (scr_w * 0.40, yz), mat("M_UIicon%d" % (k % 7), row_cols[k % 7], emit=(row_cols[k % 7], 4.0)), z=0.003)
    bar = ui_quad("UI_bar%d" % k, 0.05 + 0.12 * random.random(), 0.012, (scr_w * 0.06, yz), mat("M_UIbar%d" % (k % 7), row_cols[(k + 3) % 7], emit=(row_cols[(k + 3) % 7], 4.0)), z=0.003)
    ROWS.append((rbg, icon, bar))
# rows scroll up while he digs (515-640); everything is clipped by keying visibility of rows outside the screen
for k, objs in enumerate(ROWS):
    for f, dz in ((F_CTRL, 0.0), (515, 0.0), (640, 0.24)):
        for o in objs:
            o.location.z = o["z0"] + dz if "z0" in o else o.location.z
    for o in objs: o["z0"] = o.location.z
for o in [x for r in ROWS for x in r]:
    for f, dz in ((F_CTRL, 0.0), (515, 0.0), (640, 0.24)):
        o.location.z = o["z0"] + dz; o.keyframe_insert("location", index=2, frame=f)
    zf = lambda dz: o["z0"] + dz
    def inside(dz): return abs((o["z0"] + dz) - 0.0) < scr_h * 0.40 + 0.0
for o in [x for r in ROWS for x in r]:
    # visible only while its row is inside the screen window (constant keys)
    vis_prev = None
    for f in range(F_CTRL, 700, 4):
        fs(f); zz = o.matrix_world.translation.z - SCR_C.z
        vis = abs(zz) < scr_h * 0.42
        if vis != vis_prev:
            key_vis([o], f, vis); vis_prev = vis
# the police row (row 9 lands mid-screen at 640): turns red with a badge at 643
POL = ROWS[8]
red = mat("M_UIred", (0.9, 0.05, 0.03), emit=((1.0, 0.06, 0.03), 0.0))
pol_hl = ui_quad("UI_polRow", scr_w * 0.9, 0.036, (0, 0.01), red, z=0.0025)
pol_hl.location.z = POL[0].location.z if False else pol_hl.location.z
key_vis([pol_hl], 1, False); key_vis([pol_hl], 643, True)
st_ = red.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((643, 0.0), (650, 6.0), (662, 3.0), (674, 6.0), (686, 3.5), (880, 3.5)):
    st_.default_value = e; st_.keyframe_insert("default_value", frame=f)
badge = star("UI_badge", (0, 0, 0), 0.008, 0.016, material=mat("M_UIbadge", (1, 0.8, 0.2), emit=((1.0, 0.75, 0.15), 6.0)), th=0.002) if "star" in dir() else None
if badge is None:
    badge = ui_quad("UI_badge", 0.026, 0.026, (scr_w * 0.40, 0.01), mat("M_UIbadge", (1, 0.8, 0.2), emit=((1.0, 0.75, 0.15), 6.0)), z=0.004)
key_vis([badge], 1, False); key_vis([badge], 648, True)
# calendar: three pages flip (one per year) at 760 / 790 / 820, then the bill bar grows (882-940)
cal_m = mat("M_UIcal", (0.95, 0.95, 0.92), emit=((0.95, 0.95, 0.92), 3.0)); calt_m = mat("M_UIcalTop", (0.9, 0.1, 0.05), emit=((0.9, 0.1, 0.05), 4.0))
CAL = []
for k in range(3):
    piv = empty("UI_calPiv%d" % k, SCR_C + Vector((-0.006 - 0.001 * k, -0.11, 0.07)))
    pg = box("UI_cal%d" % k, (0.002, 0.07, 0.07), SCR_C + Vector((-0.006 - 0.001 * k, -0.11, 0.035)), cal_m, bevel=0)
    tp = box("UI_calTop%d" % k, (0.002, 0.07, 0.014), SCR_C + Vector((-0.007 - 0.001 * k, -0.11, 0.063)), calt_m, bevel=0)
    for o in (pg, tp): o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
    key_vis([pg, tp], 1, False); key_vis([pg, tp], 700, True)
    f0 = 760 + 30 * (2 - k) if False else 760 + 30 * k
    piv.rotation_euler = (0, 0, 0); piv.keyframe_insert("rotation_euler", frame=f0)
    piv.rotation_euler = (R_(-170), 0, 0); piv.keyframe_insert("rotation_euler", frame=f0 + 12)
    key_vis([pg, tp], f0 + 13, False)
    CAL.append(piv)
# the bill bar (pivot at its left end so it grows to the right, across the whole screen)
barp = empty("UI_billPiv", SCR_C + Vector((-0.005, scr_w * 0.44, -0.07)))
bill = box("UI_bill", (0.002, 0.02, 0.05), SCR_C + Vector((-0.005, scr_w * 0.44 - 0.01, -0.07)), red, bevel=0)
bill.parent = barp; bill.matrix_parent_inverse = barp.matrix_world.inverted()
key_vis([bill], 1, False); key_vis([bill], 700, True)
for f, s_ in ((700, 1.0), (882, 1.0), (930, 19.0), (945, 18.0), (960, 18.5)):
    barp.scale = (1, s_, 1); barp.keyframe_insert("scale", frame=f)
UI.rotation_euler = (0, 0, 0)
# screen glow on his face
sg_ = bpy.data.lights.new("ScreenGlow", 'AREA'); sg_.shape = 'RECTANGLE'; sg_.size = 0.36; sg_.size_y = 0.24; sg_.color = (0.55, 0.75, 1.0); sg_.energy = 6.0
sgo = bpy.data.objects.new("ScreenGlow", sg_); sc.collection.objects.link(sgo); sgo.location = SCR_C + Vector((-0.03, 0, 0))
sgo.rotation_euler = Vector((-1, 0, 0)).to_track_quat('-Z', 'Y').to_euler()
for f, e, c in ((1, 6.0, (0.55, 0.75, 1.0)), (643, 6.0, (0.55, 0.75, 1.0)), (650, 9.0, (1.0, 0.25, 0.2)), (880, 9.0, (1.0, 0.25, 0.2)), (940, 14.0, (1.0, 0.2, 0.15))):
    sg_.energy = e; sg_.color = c; sg_.keyframe_insert("energy", frame=f); sg_.keyframe_insert("color", frame=f)
# DA KRAS FILMS logo on the back of the laptop lid (faces the street window, the camera's way in)
lg, asp = logo_plane("Logo_Laptop", sc["LOGO_DARK"], Vector((lx1 + 0.004, (ly0 + ly1) / 2, lz0 + 0.31)), 0.30, (1, 0, 0))

if STOP == "blocking_people":
    bpy.ops.wm.save_as_mainfile(filepath=OUT); raise SystemExit

# ================================================================== the OFFICER in the dark station (700-end): leans on the desk, fans himself with a file
fs(F_OFF_IN)
ODB = HO.root_head.copy()
for f in (F_OFF_IN, END): stand_feet(RO, HO, f, spread=0.03)
for f in range(F_OFF_IN, END + 1, 10):
    ph = f / 60.0
    HO.key_root(f, ODB + Vector((0.003 * math.sin(ph * 1.9), 0, -0.012 - 0.004 * math.sin(ph * 1.6))))
    HO.key_spine(f, flex=14 + 1.5 * math.sin(ph * 1.6), head=(-2 + 4 * math.sin(ph * 0.7), 8 * math.sin(ph * 0.5)))
fs(F_OFF_IN); upd()
hand_on = Vector((DESK[0] + 0.30, DESK[1] - 0.24, DTOP + 0.004))
for f in (F_OFF_IN, END):
    place_hand(OFF, "L", f, hand_on, Vector((0, 0, -1)), Vector((-1, 0.15, 0)), skin=0.012)
    key_pole_world(OFF, "L", f, Wh(OFF, "upperarm01.L") + Vector((0.35, -0.45, -0.2)))
    apply_pose(OFF, "L", "flat_palm", f)
FOLDER = box("Fan_Folder", (0.22, 0.30, 0.012), (0, 0, 0), mat("M_FanFolder", (0.95, 0.70, 0.05), rough=0.55), bevel=0.003)
def fan_hand(f, phase):
    fs(f); R3 = OFF.matrix_world.to_3x3(); sh = Wh(OFF, "upperarm01.R")
    wr = sh + R3 @ Vector((-0.16, -0.24, -0.06))
    a_ = R_(35) * math.sin(phase)
    fdir = R3 @ Vector((0.25, -0.35, 1.0))
    palm = R3 @ (Matrix.Rotation(a_, 3, 'Z') @ Vector((1.0, -0.2, 0.0)))
    hand_world(OFF, "R", f, wr, fdir, palm, pole=sh + R3 @ Vector((-0.45, 0.25, -0.45)))
fan_hand(F_OFF_IN, 0.0); apply_pose(OFF, "R", "hold_flat_object", F_OFF_IN)
prop_in_hand(OFF, "R", FOLDER, F_OFF_IN, grip_y=-0.11)
for k, f in enumerate(range(1100, END + 1, 9)):
    fan_hand(f, k * math.pi / 2)
apply_pose(OFF, "R", "hold_flat_object", END)
key_vis([FOLDER], 1, False); key_vis([FOLDER], F_OFF_IN, True)
key_vis([PAD], 1, True); key_vis([PAD] + list(PAD.children), F_OFF_IN, False); key_vis(list(PAD.children), 1, True)
expression(OFF, [(F_OFF_IN, 0.0), (1150, 0.0), (1170, 1.0), (END, 1.0)], FROWN)

# ================================================================== STATION power cut: windows go dark one by one, the fan winds down, candle + moon
CUT = 1092
GL = [O[n] for n in sc["ST_GLOWS"]]
for k, g in enumerate(GL):
    p = g.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    p.default_value = 2.5; p.keyframe_insert("default_value", frame=1); p.keyframe_insert("default_value", frame=CUT + 12 * k)
    p.default_value = 0.0; p.keyframe_insert("default_value", frame=CUT + 12 * k + 2)
tube = O[sc["ST_TUBE"]]; tp = tube.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 8.0), (CUT + 48, 8.0), (CUT + 50, 0.0)):
    tp.default_value = e; tp.keyframe_insert("default_value", frame=f)
stk = O["St_Key"].data
for f, e in ((1, 240.0), (CUT + 48, 240.0), (CUT + 50, 0.0)):
    stk.energy = e; stk.keyframe_insert("energy", frame=f)
moon = O["St_Moon"].data
for f, e in ((1, 0.0), (CUT + 48, 0.0), (CUT + 60, 70.0)):
    moon.energy = e; moon.keyframe_insert("energy", frame=f)
cl_ = O["St_CandleLight"].data
for f in range(1, END + 1, 6):
    e = 0.0 if f < CUT + 50 else 6.0 + 1.5 * math.sin(f * 1.7) + 0.8 * math.sin(f * 4.1)
    cl_.energy = e; cl_.keyframe_insert("energy", frame=f)
fl = O["St_Flame"]
key_vis([fl], 1, False); key_vis([fl], CUT + 50, True)
for f in range(CUT + 50, END + 1, 4):
    fl.scale = (0.8, 0.8, 2.0 + 0.3 * math.sin(f * 2.3)); fl.keyframe_insert("scale", frame=f)
fanb = O[sc["FAN"]]
ang = 0.0; prev = 1
for f in range(1, END + 1, 4):
    spd = 0.55 if f < CUT + 48 else max(0.0, 0.55 * (1 - (f - CUT - 48) / 60.0))
    ang += spd * 4; fanb.rotation_euler = (0, 0, ang); fanb.keyframe_insert("rotation_euler", frame=f)
# the clock: from 7 o'clock, five hours spin past (1160-1280)
HOUR, MIN = O[sc["CLOCK"][0]], O[sc["CLOCK"][1]]
for f, h in ((1, 7.0), (1160, 7.0), (1280, 12.0), (END, 12.0)):
    HOUR.rotation_euler = (-R_(30 * h), 0, 0); HOUR.keyframe_insert("rotation_euler", frame=f)
    MIN.rotation_euler = (-R_(360 * h), 0, 0); MIN.keyframe_insert("rotation_euler", frame=f)
for o_ in (HOUR, MIN):
    for fc in iter_fcurves(o_.animation_data.action):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ================================================================== day -> dusk (1080-1150), street lamps on, exposure
wnt = sc.world.node_tree
ramp = wnt.nodes["SkyRamp"].color_ramp
ramp.elements[0].position = 0.0; ramp.elements[1].position = 0.65
def key_sky(f, hor, zen, light_col, light_str):
    ramp.elements[0].color = (*hor, 1); ramp.elements[1].color = (*zen, 1)
    sc.world.node_tree.nodes["SkyRamp"].color_ramp.elements[0].keyframe_insert("color", frame=f)
    sc.world.node_tree.nodes["SkyRamp"].color_ramp.elements[1].keyframe_insert("color", frame=f)
    sl = wnt.nodes["SkyLight"]; sl.inputs["Color"].default_value = (*light_col, 1); sl.inputs["Strength"].default_value = light_str
    sl.inputs["Color"].keyframe_insert("default_value", frame=f); sl.inputs["Strength"].keyframe_insert("default_value", frame=f)
key_sky(1, (0.45, 0.78, 1.0), (0.04, 0.32, 0.95), (0.55, 0.72, 1.0), 0.9)
key_sky(1080, (0.45, 0.78, 1.0), (0.04, 0.32, 0.95), (0.55, 0.72, 1.0), 0.9)
key_sky(1150, (1.0, 0.42, 0.22), (0.10, 0.08, 0.40), (0.45, 0.40, 0.80), 0.35)
key_sky(END, (0.95, 0.38, 0.25), (0.08, 0.06, 0.35), (0.40, 0.38, 0.80), 0.32)
sun = O["Sun"]
for f, e, c, rx in ((1, 4.0, (1.0, 0.95, 0.86), 42), (1080, 4.0, (1.0, 0.95, 0.86), 42), (1150, 1.2, (1.0, 0.50, 0.25), 80), (END, 1.0, (1.0, 0.45, 0.25), 82)):
    sun.data.energy = e; sun.data.color = c; sun.data.keyframe_insert("energy", frame=f); sun.data.keyframe_insert("color", frame=f)
    sun.rotation_euler.x = R_(rx); sun.keyframe_insert("rotation_euler", index=0, frame=f)
for f, ex in ((1, 0.0), (1080, 0.0), (1150, 0.55), (1290, 0.65), (1300, 0.55), (END, 0.55)):
    sc.view_settings.exposure = ex; sc.view_settings.keyframe_insert("exposure", frame=f)
for n in sc["STREET_LIGHTS"]:
    ld = O[n].data
    for f, e in ((1, 0.0), (1110, 0.0), (1130, 160.0)):
        ld.energy = e; ld.keyframe_insert("energy", frame=f)
# a warm fill on Ravi's face for the dusk ending (a shop light off camera)
efl = bpy.data.lights.new("EndFaceFill", 'AREA'); efl.size = 1.0; efl.color = (1.0, 0.78, 0.55)
efo = bpy.data.objects.new("EndFaceFill", efl); sc.collection.objects.link(efo); efo.location = (5.4, -1.6, 2.4)
efo.rotation_euler = (Vector((3.35, -0.55, 1.5)) - efo.location).to_track_quat('-Z', 'Y').to_euler()
for f, e in ((1, 0.0), (1288, 0.0), (1292, 90.0)):
    efl.energy = e; efl.keyframe_insert("energy", frame=f)

# ================================================================== RAVI at the end (1292-1446): beside his bike, looks at the dark station, smirks at us, nods
fs(F_END)
EB = HR.root_head.copy()
for f in (F_END, END): stand_feet(RR, HR, f, spread=0.04)
breathe(HR, RR, F_END, END, EB, step=10)
for s in "LR":
    for f in (F_END, 1340, 1390, END): hang(RAVI, s, f, swing=0.008 * (f % 3))
expression(RAVI, [(F_END, 0.3), (1350, 0.3), (1366, 1.0), (END, 1.0)], SMIRK)

# ================================================================== the CAMERA: one continuous move (positions / aims, PCHIP, level horizon)
fs(1)
def headpos(rig, f, up=0.06):
    fs(f); return Wh(rig, "head") + Vector((0, 0, up))
RH = {f: headpos(RAVI, f) for f in (1, 40, 80, 118, 160, 230, 270, 300, 340, 380, 420, 560, 640, 760, 860, 900, 940, 1000, 1030, 1060, 1300, 1350, 1400, END)}
OH = {f: headpos(OFF, f) for f in (1, 60, 120, 180, 1200, 1260)}
ARMC = LEV["pivot"]
CR_ = sc["CR"]; WCR = sc["W_CR"]; WCAM = sc["W_CAM"]
WINC = Vector((WX, (WCR[0] + WCR[1]) / 2, (WCR[2] + WCR[3]) / 2))
STWIN = Vector((EX, (WCAM[0] + WCAM[1]) / 2, (WCAM[2] + WCAM[3]) / 2))
PT = Vector(sc["POLE_TRANS"])
def bh(f): return RH[f]
CK = [
    # frame, position, aim, lens, f-stop
    (1,    Vector((1.05, -4.2, 1.55)), Vector((2.3, -9.6, 1.35)), 30, 8),                 # ahead of the bike, rider's face, officer enters at right
    (40,   Vector((1.10, -2.4, 1.55)), Vector((2.6, -6.6, 1.40)), 30, 8),
    (80,   Vector((1.20, -0.4, 1.55)), Vector((3.0, -3.0, 1.45)), 30, 8),
    (118,  Vector((1.15, 1.55, 1.55)), Vector((3.1, -0.6, 1.40)), 32, 8),                 # bike stops: rider + officer (right)
    (160,  Vector((2.10, 2.55, 1.62)), Vector((3.0, -0.1, 1.45)), 32, 8),                 # arc right: officer points at his bare head
    (215,  Vector((3.05, 2.30, 1.65)), Vector((2.6, -0.1, 1.50)), 34, 8),
    (255,  Vector((2.65, 1.05, 1.62)), Vector((2.35, -0.2, 1.52)), 38, 8),                # close on Ravi: "Big mistake"
    (290,  Vector((2.55, 0.85, 1.58)), Vector((2.40, -0.2, 1.60)), 38, 8),
    (318,  Vector((2.75, 0.60, 1.90)), PT + Vector((-0.6, 0, 0.3)), 30, 8),              # tilt up to the pole transformer and the wires
    (340,  Vector((1.20, 4.50, 5.6)), Vector((-6.0, 12.0, 4.0)), 28, 8),                  # follow the wires west, over the street
    (366,  Vector((-5.0, 13.0, 3.4)), Vector((-9.4, 19.4, 1.55)), 30, 8),                 # over the yard fence (3.4 m), down to Ravi
    (392,  Vector((-7.70, 18.25, 1.75)), Vector((-9.4, 19.4, 1.62)), 34, 8),              # Ravi in his hard hat, transformers behind
    (420,  Vector((-7.60, 17.70, 2.6)), Vector((-10.5, 20.5, 2.2)), 30, 8),
    (455,  Vector((-8.5, 14.5, 9.0)), Vector((-40.0, 28.0, 10.0)), 26, 8),                # crane up: pylons and lines over the town
    (488,  Vector((-5.0, 9.0, 6.5)), Vector((-60.0, 20.0, 6.0)), 26, 8),
    (515,  Vector((-2.2, WINC.y + 0.2, 1.75)), WINC + Vector((-2.5, 0.0, -0.10)), 30, 8),  # down to the control room window: logo on the lid
    (560,  Vector((-4.6, WINC.y + 0.1, 1.68)), WINC + Vector((-3.0, -0.05, -0.15)), 32, 8),
    (600,  Vector((-6.45, WINC.y + 0.25, 1.62)), WINC + Vector((-2.6, 0.0, -0.10)), 32, 8),  # through the window (no glass)
    (640,  Vector((-9.55, 2.15, 1.78)), SCR_C + Vector((0, 0.02, 0.0)), 30, 9),           # over his right shoulder: the screen
    (700,  Vector((-9.35, 2.40, 1.62)), SCR_C, 34, 10),
    (760,  Vector((-9.05, 2.55, 1.50)), SCR_C + Vector((0, 0.03, 0.0)), 36, 11),          # calendar pages
    (830,  Vector((-7.45, 3.35, 1.62)), Vector((RAVI_CX, RAVI_CY, 1.62)), 32, 8),         # round to his grinning face
    (880,  Vector((-7.40, 3.05, 1.62)), Vector((RAVI_CX, RAVI_CY, 1.62)), 32, 8),
    (905,  Vector((-9.70, 3.30, 1.82)), SCR_C + Vector((0, 0.0, 0.0)), 28, 8),            # behind-left: the bar grows, he leans back
    (950,  Vector((-9.85, 3.55, 1.85)), SCR_C + Vector((0, -0.05, 0.05)), 26, 8),
    (985,  Vector((-7.55, 2.40, 1.70)), Vector((RAVI_CX, 2.4, 1.40)), 28, 8),             # the turn to the switchgear
    (1015, Vector((-7.70, 2.35, 1.62)), ARMC + Vector((-0.05, 0.25, 0.10)), 28, 8),       # the lever, the sparks, his face
    (1045, Vector((-7.80, 2.55, 1.58)), ARMC + Vector((0.0, 0.40, 0.20)), 28, 8),
    (1068, Vector((-7.20, WINC.y, 1.70)), Vector((RAVI_CX, RAVI_CY - 0.2, 1.55)), 28, 8),
    (1084, Vector((-5.6, WINC.y, 2.2)), STWIN + Vector((0, 0, 1.6)), 26, 8),              # whip out of the window to the station
    (1115, Vector((-1.0, 1.6, 3.2)), STWIN + Vector((0, -0.6, 1.6)), 26, 8),              # windows go dark one by one, dusk
    (1150, Vector((4.2, STWIN.y, 1.75)), STWIN + Vector((2.0, 0, -0.15)), 28, 8),
    (1172, Vector((6.70, STWIN.y, 1.68)), Vector((DESK[0] + 0.6, DESK[1], 1.45)), 30, 8),  # in through the window (no glass)
    (1215, Vector((7.25, DESK[1] - 0.55, 1.62)), Vector((DESK[0] + 0.75, DESK[1] - 0.05, 1.55)), 32, 8),
    (1262, Vector((7.20, DESK[1] + 0.45, 1.70)), Vector((DESK[0] + 0.8, DESK[1], 1.70)), 30, 8),  # officer + spinning clock
    (1286, Vector((6.10, STWIN.y, 1.70)), Vector((3.35, -0.55, 1.55)), 28, 8),           # back out of the window
    (1320, Vector((5.10, -0.20, 1.62)), Vector((3.35, -0.55, 1.60)), 30, 8),             # Ravi by his bike, dusk
    (1370, Vector((4.55, -0.40, 1.62)), Vector((3.35, -0.55, 1.62)), 34, 8),
    (1410, Vector((4.40, -0.70, 1.62)), Vector((3.35, -0.55, 1.62)), 36, 8),
    (END,  Vector((4.30, -0.60, 1.63)), Vector((3.35, -0.55, 1.63)), 38, 8),
]
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.clip_start = 0.02; cam_d.dof.use_dof = True; cam_d.dof.focus_object = AIM
yaws = []; prev = None
for f, p, a_, l_, fst in CK:
    d = a_ - p; yw = math.atan2(d.y, d.x)
    if prev is not None:
        while yw - prev > math.pi: yw -= 2 * math.pi
        while yw - prev < -math.pi: yw += 2 * math.pi
    yaws.append(yw); prev = yw
fx = pchip([(k[0], k[1].x) for k in CK]); fy = pchip([(k[0], k[1].y) for k in CK]); fz = pchip([(k[0], k[1].z) for k in CK])
fyaw = pchip([(k[0], yaws[i]) for i, k in enumerate(CK)])
fpit = pchip([(k[0], math.atan2((k[2] - k[1]).z, (k[2] - k[1]).to_2d().length)) for k in CK])
fdis = pchip([(k[0], (k[2] - k[1]).length) for k in CK]); flen = pchip([(k[0], k[3]) for k in CK]); fstp = pchip([(k[0], k[4]) for k in CK])
maxstep = 0.0; prev_y = None
for f in range(1, END + 1):
    p = Vector((fx(f), fy(f), fz(f))); yw = fyaw(f); pt = fpit(f); ds = fdis(f)
    dvec = Vector((math.cos(yw) * math.cos(pt), math.sin(yw) * math.cos(pt), math.sin(pt)))
    CAM.location = p; CAM.rotation_euler = (math.pi / 2 + pt, 0, yw - math.pi / 2)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_euler", frame=f)
    AIM.location = p + dvec * ds; AIM.keyframe_insert("location", frame=f)
    cam_d.lens = flen(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.aperture_fstop = fstp(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
    if prev_y is not None: maxstep = max(maxstep, abs(math.degrees(yw - prev_y)))
    prev_y = yw
log("camera keyed; max yaw step deg/frame", round(maxstep, 1))
def campos(f): return Vector((fx(f), fy(f), fz(f)))

# ================================================================== heads and eyes: look at what the beat needs (officer, the wires, the camera)
def clear_keys(obj, bones):
    act = obj.animation_data.action
    paths = {'pose.bones["%s"].rotation_quaternion' % b for b in bones}
    try:
        for fc in [fc for fc in act.fcurves if fc.data_path in paths]: act.fcurves.remove(fc)
    except AttributeError:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in [fc for fc in cb.fcurves if fc.data_path in paths]: cb.fcurves.remove(fc)
    for b in bones: obj.pose.bones[b].rotation_quaternion = Quaternion()
HEADB_ = ("neck01", "neck02", "neck03", "head")
clear_keys(RAVI, HEADB_); clear_keys(OFF, HEADB_)
def ravi_head_keys(keys, base_yaw_fn=lambda f: 0.0, flex_fn=lambda f: 0.0, rig=None):
    rig = rig or RAVI; R_g = RIG[rig.name]; H_g = HU[rig.name]
    for k in keys:
        f, tgt = k[0], k[1]; extra = k[2] if len(k) > 2 else 0.0
        t = tgt(f) if callable(tgt) else tgt
        p, y = look_angles(rig, f, t, base_yaw=base_yaw_fn(f), flex=flex_fn(f))
        p += extra
        for n, w in H_g.HEAD_W.items(): R_g.key_rot(n, f, [("X", p * w), ("Z", y * w)])
fs(150); OFFHEAD = Wh(OFF, "head") + Vector((0, 0, 0.05))
ravi_head_keys([(1, Vector((2.3, 6.0, 1.4))), (60, Vector((2.3, 6.0, 1.3))), (110, OFFHEAD), (150, OFFHEAD), (230, OFFHEAD), (258, campos),
                (284, campos), (300, PT), (F_YARD - 1, PT)], flex_fn=lambda f: 18 if f < 96 else 8)
ravi_head_keys([(F_YARD, Vector((-12.5, 16.0, 2.0))), (350, Vector((-12.5, 16.0, 2.2))), (368, campos), (400, campos), (430, Vector((-24.0, 22.5, 14.0))), (F_CTRL - 1, Vector((-24.0, 22.5, 14.0)))])
ravi_head_keys([(F_CTRL, SCR_C), (600, SCR_C), (650, SCR_C), (860, SCR_C), (895, SCR_C + Vector((0, 0, 0.1))), (960, SCR_C + Vector((0, 0, 0.1)))],
               flex_fn=lambda f: LEAN(f))
ravi_head_keys([(985, ARMC + Vector((0, 0, 0.1))), (1003, ARMC + Vector((0, 0.2, 0.2))), (1035, ARMC + Vector((0, 0.1, 0.45))), (1055, campos), (1070, STWIN), (F_END - 1, STWIN)],
               base_yaw_fn=lambda f: -90 if f >= 1003 else (-35 if f >= 985 else 0))
ravi_head_keys([(F_END, STWIN + Vector((0, 0, 0.5))), (1340, STWIN + Vector((0, 0, 0.5))), (1362, campos), (1392, campos), (1402, campos, 9), (1412, campos, -2), (1424, campos, 4), (END, campos)])
ravi_head_keys([(1, RHEAD), (90, RHEAD), (200, RHEAD, -4), (260, RHEAD), (F_OFF_IN - 1, RHEAD)], rig=OFF)
ravi_head_keys([(F_OFF_IN, STWIN), (1160, STWIN, 10), (1200, campos, 6), (1235, Vector(sc["CANDLE"]), 0), (1262, campos), (END, campos)], rig=OFF, flex_fn=lambda f: 14)
blinks(RAVI, [70, 200, 330, 470, 590, 720, 840, 990, 1120, 1320, 1385])

# ================================================================== VO, output, quaternion continuity
se = sc.sequence_editor_create()
coll = se.strips if hasattr(se, "strips") else se.sequences
st = coll.new_sound("VO", os.path.abspath(VO), channel=1, frame_start=1)
log("VO strip", st.frame_final_start, st.frame_final_end)
def quat_continuity(obj):
    groups = {}
    if not obj.animation_data or not obj.animation_data.action: return 0
    for fc in iter_fcurves(obj.animation_data.action):
        if fc.data_path.endswith("rotation_quaternion"): groups.setdefault(fc.data_path, {})[fc.array_index] = fc
    nfix = 0
    for dp, ch in groups.items():
        if len(ch) != 4: continue
        frames = sorted({kp.co.x for kp in ch[0].keyframe_points})
        idx = [{kp.co.x: kp for kp in ch[i].keyframe_points} for i in range(4)]
        prev = None
        for fr in frames:
            kps = [idx[i].get(fr) for i in range(4)]
            if any(k is None for k in kps): continue
            q = Quaternion([k.co.y for k in kps])
            if prev is not None and prev.dot(q) < 0:
                for k in kps:
                    k.co.y = -k.co.y; k.handle_left.y = -k.handle_left.y; k.handle_right.y = -k.handle_right.y
                q = -q; nfix += 1
            prev = q
        for c_ in ch.values(): c_.update()
    return nfix
log("quat flips fixed", [quat_continuity(r) for r in (RAVI, OFF)])
# teleport frames are hard cuts for the rig (constant): make every pose channel step at the teleports
for r, fr in ((RAVI, (F_YARD, F_CTRL, F_END)), (OFF, (F_OFF_IN,))):
    for fc in iter_fcurves(r.animation_data.action):
        kps = fc.keyframe_points
        for i in range(len(kps) - 1):
            if any(kps[i].co.x < t <= kps[i + 1].co.x for t in fr): kps[i].interpolation = 'CONSTANT'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = True
sc.frame_start, sc.frame_end = 1, END
sc.render.filepath = "//render/ElectricianPolice_v011_####.png"; sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.compression = 15
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
open(OUT + ".log.txt", "w").write("\n".join(LOG))
print("ANIM_OK", OUT)
