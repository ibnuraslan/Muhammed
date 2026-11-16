"""ClosetBathroom Phase 1: every shot's action keyed at 1x from its own start frame (actions are written in seconds from
the shot start and padded with live idles, so Phase 2 only moves the shot windows to the VO frames: nothing is stretched).
One camera per shot, hard cuts by timeline markers. Provisional windows follow the reference film's pacing.
blender -b work/sets.blend --python 03_shots.py -- work/film.blend"""
import bpy, sys, math, json
from mathutils import Vector, Matrix
P_ = "/home/user/Muhammed/blender/pipeline/"; HERE = "/home/user/Muhammed/blender/ClosetBathroom_v001/"
exec(open(P_ + "anim_lib.py").read()); exec(open(P_ + "hand_poses.py").read()); exec(open(HERE + "scripts/closet_lib.py").read())
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; sc.render.fps = 60; R_ = math.radians
X0 = 30.0
# ------------------------------------------------------------------ shot table (provisional; Phase 2 = VO word frames)
SHOTS = [  # id, set, f0, f1, VO words (reference)
    ("S01", "hall", 1, 96, "He opened his closet"),
    ("S02", "hall", 97, 162, "but instead"),
    ("S03", "bath", 163, 276, "discovered a bathroom"),
    ("S04", "hall", 277, 342, "Confused,"),
    ("S05", "hall", 343, 438, "he asked his roommates what happened"),
    ("S06", "hall", 439, 522, "to the closet"),
    ("S07", "hall", 523, 612, "They looked at him"),
    ("S08", "hall", 613, 690, "like he was joking"),
    ("S09", "hall", 691, 822, "insisting it had always been a bathroom"),
    ("S10", "hall", 823, 894, "He assumed"),
    ("S11", "prank", 895, 1014, "they had pulled off an elaborate prank"),
    ("S12", "prank", 1015, 1112, "while he was gone"),
    ("S13", "hall", 1113, 1236, "But as days passed"),
    ("S14", "hall", 1237, 1356, "his confusion turned to panic"),
    ("S15", "hall", 1357, 1566, "he couldn't even remember what the closet looked like"),
    ("S16", "hall", 1567, 1656, "he was losing his mind"),
    ("S17", "clinic", 1657, 1776, "the doctor"),
    ("S18", "clinic", 1777, 1926, "After some tests, they found"),
    ("S19", "clinic", 1927, 2166, "a brain tumor causing memory loss and hallucinations"),
    ("S20", "hall", 2167, 2286, "it had always"),
    ("S21", "bath", 2287, 2406, "been a bathroom"),
]
SH = {s[0]: s for s in SHOTS}
sc.frame_start = 1; sc.frame_end = SHOTS[-1][3]
def F(sid, t): return SH[sid][2] + int(round(t * 60))
def END(sid): return SH[sid][3]
def fcurves_of(idb):
    ad = getattr(idb, "animation_data", None)
    if not ad or not ad.action: return []
    act = ad.action; out_ = []
    try: out_ = list(act.fcurves)
    except Exception: out_ = []
    if not out_:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in getattr(strip, "channelbags", []): out_ += list(cb.fcurves)
    return out_
def set_interp(idb, kind):
    for fc in fcurves_of(idb):
        for kp in fc.keyframe_points: kp.interpolation = kind
def yaw_to(a, b):
    d = (Vector(b) - Vector(a)).to_2d().normalized()
    return math.degrees(math.atan2(d.x, -d.y))

# ------------------------------------------------------------------ characters
RIGS = {n: bpy.data.objects[n] for n in ("Tom", "Ray", "Ken", "Doc")}
HS = {n: setup_char(r) for n, r in RIGS.items()}
def stand(H, f, pos, yaw, flex=2.0, head=(0.0, 0.0), twist=0.0, crouch=0.0, side=0.0, arms=True, fwd=0.0, feet=True):
    p = Vector((pos[0], pos[1], H.root_head.z - crouch))
    H.key_root(f, p, yaw=yaw, flex=flex * 0.4, side=side)
    H.key_spine(f, flex=flex, twist=twist, head=head)
    if feet:
        for s in "LR": H.key_foot(s, f, H.foot_xy(s, Vector((pos[0], pos[1], 0)), yaw), yaw)
    if arms: key_hang(H, f, p, yaw, fwd=fwd)
def hang1(H, s, f, pos, yaw, crouch=0.0, fwd=0.0):
    sx = 1 if s == "L" else -1
    body_hand(H, s, f, Vector((pos[0], pos[1], H.root_head.z - crouch)), yaw, hang_off(H, s, fwd), (0.0, -0.15, -1.0), (-sx, 0.0, 0.0))
def gesture(H, s, f, pos, yaw, off, d, n, crouch=0.0, pole=None):
    """hand in the body frame: off relative to the root head (x = side, -y = forward, z = up); d finger dir, n palm normal"""
    body_hand(H, s, f, Vector((pos[0], pos[1], H.root_head.z - crouch)), yaw, off, d, n, pole_off=pole)
def palms_up(H, f, pos, yaw, k=1.0, crouch=0.0):
    for s in "LR":
        sx = 1 if s == "L" else -1
        gesture(H, s, f, pos, yaw, (0.30 * sx, -0.26 * k - 0.05, 0.12 + 0.08 * k), (0.45 * sx, -1.0, 0.05), (0.0, 0.0, 1.0), crouch,
                pole=(0.55 * sx, 0.35, 0.15))
def sit(H, f, seat, yaw, seat_z, head=(0.0, 0.0), flex=6.0, knee_out=0.0, bounce=0.0, hands=True):
    Rm = Rz(yaw)
    root = Vector((seat[0], seat[1], seat_z + 0.15)) + Rm @ Vector((0, -0.02, 0))
    H.key_root(f, root, yaw=yaw, flex=flex * 0.3)
    H.key_spine(f, flex=flex, head=head)
    for s in "LR":
        sx = 1 if s == "L" else -1
        xy = Vector((seat[0], seat[1])) + (Rm @ Vector((H.ankle[s].x * (1.15 + knee_out), -0.47, 0))).to_2d()
        H.key_foot(s, f, xy, yaw + sx * 6, lift=bounce if s == "L" else 0.0)
        pb = H.r.PB["Pole_knee." + s]; n = "Pole_knee." + s
        pole = root + Rm @ Vector((sx * 0.25, -1.2, 0.3))
        pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
        if hands:
            body_hand(H, s, f, root, yaw, (sx * 0.13, -0.33, 0.11 + (bounce if s == "L" else 0)), (sx * 0.1, -1.0, -0.25), (0.0, 0.0, -1.0),
                      pole_off=(0.45 * sx, 0.25, 0.1))
def relax_fingers(r, frames):
    for f in frames:
        for s in "LR": apply_pose(r, s, "relaxed", f)
def seat_top(obj_name, x, y):
    o = bpy.data.objects[obj_name]; inv = o.matrix_world.inverted()
    ok, loc, nrm, idx = o.ray_cast(inv @ Vector((x, y, 3.0)), inv.to_3x3() @ Vector((0, 0, -1)))
    return (o.matrix_world @ loc).z if ok else 0.48

# park everyone off-set until used
for n, H in HS.items():
    stand(H, 0, (60 + list(HS).index(n) * 2, 60), 0)

# ================================================================== HALL: Tom opens the door (S01-S02)
T = HS["Tom"]; TR = RIGS["Tom"]
piv = bpy.data.objects["DoorPivot"]
DW = 0.9 - 0.045
def door_key(f, deg):
    piv.rotation_euler = (0, 0, R_(deg)); piv.keyframe_insert("rotation_euler", frame=f, index=2)
door_key(0, 0); door_key(F("S01", 0.25), 0)
th = pchip([(F("S01", 0.25), 0.0), (F("S01", 0.55), 4.0), (F("S01", 0.95), 30.0), (F("S01", 1.25), 70.0), (F("S01", 1.55), 93.0), (F("S01", 1.75), 95.0)])
for f in range(F("S01", 0.25), F("S01", 1.75) + 1, 3): door_key(f, th(f))
door_key(SH["S01"][3] + 1, 95)
fc_door = fcurves_of(piv)
# Tom walks up to the door, palm on the panel above the lever, pushes it open while stepping into the doorway
P0 = Vector((0.16, -0.50, 0)); P1 = Vector((0.10, -0.16, 0))
Y180 = 180.0
stand(T, 0, P0, Y180); stand(T, F("S01", 0.0), P0, Y180)
stand(T, F("S01", 0.35), P0, Y180, flex=4)
path = lambda f: P0.lerp(P1, smooth(min(1, max(0, (f - F("S01", 0.45)) / (F("S01", 1.15) - F("S01", 0.45))))))
T.walk(path, lambda f: Y180, F("S01", 0.45), F("S01", 1.15), stride=0.55, step=2, crouch=0.0, lean=4.0, bob=0.01)
stand(T, F("S01", 1.3), P1, Y180, flex=5, head=(-4, 6), arms=False)
stand(T, END("S01"), P1, Y180, flex=6, head=(-6, -8), arms=False)
hang1(T, "L", F("S01", 0.0), P0, Y180); hang1(T, "L", F("S01", 1.15), P1, Y180); hang1(T, "L", END("S01"), P1, Y180)
hang1(T, "R", F("S01", 0.0), P0, Y180)
def door_point(deg, r=0.56, z=1.12):
    return Vector((piv.location.x, piv.location.y, 0)) + Rz(deg) @ Vector((r, -0.03, z)), Rz(deg) @ Vector((0, 1, 0))
# simplest safe staging (LESSONS 2.15): no hand-on-door contact. The right hand rises toward the door in front of his chest
# (hidden by his own back from this camera) and drops as the door swings away; nothing touches the leaf.
t0, t1 = F("S01", 0.30), F("S01", 0.62)
for f in (t0, t1):
    gesture(T, "R", f, P0, Y180, (-0.14, -0.36, 0.30), (0.0, -0.5, 1.0), (0.0, -1.0, 0.2), pole=(-0.5, 0.2, -0.1))
apply_pose(TR, "R", "relaxed", F("S01", 0.0)); apply_pose(TR, "R", "flat_palm", t0); apply_pose(TR, "R", "flat_palm", t1)
hang1(T, "R", F("S01", 0.95), P1, Y180, fwd=0.04); hang1(T, "R", END("S01"), P1, Y180)
apply_pose(TR, "R", "relaxed", F("S01", 1.3)); apply_pose(TR, "L", "relaxed", F("S01", 0.0))
# S02: in the doorway, he leans in and looks around the room (head left/right)
stand(T, F("S02", 0.0), P1, Y180, flex=6, head=(-6, -8))
stand(T, F("S02", 0.4), P1, Y180, flex=9, head=(-2, 14), fwd=0.03)
stand(T, F("S02", 0.75), P1, Y180, flex=10, head=(-4, -16), fwd=0.03)
stand(T, END("S02"), P1, Y180, flex=8, head=(-6, -4), fwd=0.02)
relax_fingers(TR, [F("S02", 0.0)])

# ================================================================== HALL: confused, asks the roommates (S04-S06)
PT = Vector((0.12, -0.42, 0)); RAY_P = Vector((-1.0, -3.4, 0)); KEN_P = Vector((-2.05, -3.0, 0))
YT_R = yaw_to(PT, RAY_P)
stand(T, F("S04", 0.0), PT, YT_R + 10, head=(4, -6), flex=0)
stand(T, F("S04", 0.35), PT, YT_R + 10, head=(8, 4), flex=-3, side=2)
stand(T, F("S04", 0.7), PT, YT_R + 10, head=(5, -10), flex=-2, side=-2)
stand(T, END("S04"), PT, YT_R + 10, head=(3, -4), flex=-1)
# S05: both palms up, "what happened?"
stand(T, F("S05", 0.0), PT, YT_R + 10, head=(3, -4), flex=-1)
stand(T, F("S05", 0.45), PT, YT_R + 4, head=(0, 2), flex=3, arms=False)
stand(T, F("S05", 1.1), PT, YT_R, head=(-3, 0), flex=4, arms=False)
stand(T, END("S05"), PT, YT_R, head=(-1, 4), flex=3, arms=False)
key_hang(T, F("S05", 0.0), Vector((PT.x, PT.y, T.root_head.z)), YT_R + 10)
palms_up(T, F("S05", 0.45), PT, YT_R + 4, 0.6); palms_up(T, F("S05", 0.9), PT, YT_R, 1.0); palms_up(T, F("S05", 1.3), PT, YT_R, 0.85)
palms_up(T, END("S05"), PT, YT_R, 0.9)
apply_pose(TR, "L", "relaxed", F("S05", 0.0)); apply_pose(TR, "R", "relaxed", F("S05", 0.0))
for s in "LR": apply_pose(TR, s, "open_alarm", F("S05", 0.6)); apply_pose(TR, s, "open_alarm", END("S05"))
# S06: right arm sweeps back toward the doorway, open palm, "to the closet"
stand(T, F("S06", 0.0), PT, YT_R, head=(-1, 4), flex=3, arms=False)
stand(T, F("S06", 0.5), PT, YT_R + 8, head=(0, 28), flex=2, twist=-10, arms=False)
stand(T, F("S06", 1.0), PT, YT_R + 8, head=(-2, 6), flex=3, twist=-8, arms=False)
stand(T, END("S06"), PT, YT_R + 8, head=(-3, 0), flex=3, twist=-6, arms=False)
palms_up(T, F("S06", 0.0), PT, YT_R, 0.9)
hang1(T, "L", F("S06", 0.45), PT, YT_R + 8); hang1(T, "L", END("S06"), PT, YT_R + 8)
for f, k in ((F("S06", 0.45), 1.0), (F("S06", 0.9), 1.0), (END("S06"), 0.9)):
    gesture(T, "R", f, PT, YT_R + 8, (-0.40 * k, 0.02, 0.17), (-1.0, 0.25, 0.1), (0.0, -0.3, 1.0), pole=(-0.55, 0.45, 0.1))
apply_pose(TR, "R", "open_alarm", F("S06", 0.45)); apply_pose(TR, "R", "open_alarm", END("S06"))
apply_pose(TR, "L", "relaxed", F("S06", 0.45))

# ================================================================== roommates react (S07-S09)
RY = HS["Ray"]; RR = RIGS["Ray"]; KN = HS["Ken"]; KR = RIGS["Ken"]
YR_T = yaw_to(RAY_P, PT); YK_T = yaw_to(KEN_P, PT)
for sid in ("S07", "S08"):
    pass
stand(RY, F("S07", 0.0), RAY_P, YR_T, head=(2, 0)); stand(KN, F("S07", 0.0), KEN_P, YK_T, head=(0, 0))
stand(RY, F("S07", 0.5), RAY_P, YR_T, head=(-2, -6), flex=1, side=3, arms=False)
stand(RY, F("S07", 1.0), RAY_P, YR_T, head=(-4, -10), flex=1, side=4, arms=False)
stand(RY, END("S07"), RAY_P, YR_T, head=(-3, -8), flex=1, side=3, arms=False)
key_hang(RY, F("S07", 0.0), Vector((RAY_P.x, RAY_P.y, RY.root_head.z)), YR_T)
palms_up(RY, F("S07", 0.5), RAY_P, YR_T, 0.7); palms_up(RY, F("S07", 1.0), RAY_P, YR_T, 0.9); palms_up(RY, END("S07"), RAY_P, YR_T, 0.8)
stand(KN, F("S07", 0.7), KEN_P, YK_T + 4, head=(-3, 8), side=-2)
stand(KN, END("S07"), KEN_P, YK_T + 6, head=(-2, 10), side=-3)
# S08: Ray laughs it off (head back, right hand waves), Ken grins
stand(RY, F("S08", 0.0), RAY_P, YR_T, head=(-3, -8), flex=1, side=3, arms=False)
stand(RY, F("S08", 0.35), RAY_P, YR_T, head=(-12, 4), flex=-4, arms=False)
stand(RY, F("S08", 0.75), RAY_P, YR_T, head=(-6, -4), flex=2, arms=False)
stand(RY, END("S08"), RAY_P, YR_T, head=(-4, 2), flex=1, arms=False)
palms_up(RY, F("S08", 0.0), RAY_P, YR_T, 0.8)
hang1(RY, "L", F("S08", 0.35), RAY_P, YR_T); hang1(RY, "L", END("S08"), RAY_P, YR_T)
for f, dx in ((F("S08", 0.35), 0.0), (F("S08", 0.6), 0.06), (F("S08", 0.85), -0.02), (END("S08"), 0.03)):
    gesture(RY, "R", f, RAY_P, YR_T, (-0.27 + dx, -0.30, 0.35), (-0.2, -0.3, 1.0), (0.0, -1.0, 0.1), pole=(-0.55, 0.3, 0.0))
apply_pose(RR, "R", "open_alarm", F("S08", 0.35)); apply_pose(RR, "L", "relaxed", F("S08", 0.35))
stand(KN, F("S08", 0.0), KEN_P, YK_T + 6, head=(-2, 10), side=-3)
stand(KN, F("S08", 0.5), KEN_P, YK_T + 6, head=(-8, 6), side=-1, flex=-2)
stand(KN, END("S08"), KEN_P, YK_T + 4, head=(-4, 4), side=-2)
relax_fingers(KR, [F("S07", 0.0)]); relax_fingers(RR, [F("S07", 0.0)])
for s in "LR": apply_pose(RR, s, "open_alarm", F("S07", 0.5))
# S09: two-shot at the doorway, Ray walks up and insists, open palm toward the bathroom
PT9 = Vector((0.42, -0.55, 0)); PR9 = Vector((-0.42, -1.12, 0))
C9 = Vector((0.6, -2.7, 0)); YT9 = yaw_to(PT9, PR9) * 0.6 + yaw_to(PT9, C9) * 0.4; YR9 = yaw_to(PR9, PT9) * 0.55 + yaw_to(PR9, C9) * 0.45
print("YAW9", round(YT9), round(YR9))
stand(T, F("S09", 0.0), PT9, YT9, head=(0, 0)); stand(T, F("S09", 1.0), PT9, YT9, head=(-3, -5), side=2); stand(T, END("S09"), PT9, YT9, head=(2, 4))
relax_fingers(TR, [F("S09", 0.0)])
stand(RY, F("S09", 0.0), PR9, YR9, arms=False); stand(RY, F("S09", 0.6), PR9, YR9 - 4, head=(0, 10), twist=8, arms=False)
stand(RY, F("S09", 1.3), PR9, YR9, head=(-2, -2), arms=False); stand(RY, END("S09"), PR9, YR9 - 3, head=(0, 6), twist=6, arms=False)
hang1(RY, "R", F("S09", 0.0), PR9, YR9); hang1(RY, "R", END("S09"), PR9, YR9)
hang1(RY, "L", F("S09", 0.0), PR9, YR9)
for f, k in ((F("S09", 0.5), 1.0), (F("S09", 1.0), 0.85), (F("S09", 1.5), 1.0), (END("S09"), 0.9)):
    gesture(RY, "L", f, PR9, YR9, (0.40 * k, -0.12, 0.20), (1.0, -0.45, 0.15), (0.0, -0.2, 1.0), pole=(0.6, 0.4, 0.1))
apply_pose(RR, "L", "open_alarm", F("S09", 0.5)); apply_pose(RR, "L", "open_alarm", END("S09")); relax_fingers(RR, [F("S09", 0.0)])
stand(KN, F("S09", 0.0), KEN_P + Vector((0.4, 1.0, 0)), yaw_to(KEN_P + Vector((0.4, 1.0, 0)), PT9))
stand(KN, END("S09"), KEN_P + Vector((0.4, 1.0, 0)), yaw_to(KEN_P + Vector((0.4, 1.0, 0)), PT9), head=(-3, 5))
# S10: Tom alone, suspicious: chin down, eyes slide to the roommates
stand(T, F("S10", 0.0), PT9, YT9 + 20, head=(6, 12), flex=2)
stand(T, F("S10", 0.5), PT9, YT9 + 18, head=(10, -6), flex=3, side=-2)
stand(T, END("S10"), PT9, YT9 + 16, head=(9, -14), flex=3, side=-3)

# ================================================================== imagined prank (S11-S12), the PRANK dressing
PRT = Vector((0.03, 1.12, 0)); PKN = Vector((-0.58, 1.66, 0))
CAM11 = Vector((0.05, -1.3, 0))
YR11 = yaw_to(PRT, CAM11) + 12
stand(RY, F("S11", 0.0), PRT, YR11, head=(-2, 0), arms=False)
stand(RY, F("S11", 0.7), PRT, YR11 + 6, head=(-6, 10), twist=6, arms=False)
stand(RY, END("S11"), PRT, YR11, head=(-4, 2), arms=False)
hang1(RY, "R", F("S11", 0.0), PRT, YR11); hang1(RY, "R", END("S11"), PRT, YR11)
hang1(RY, "L", F("S11", 0.0), PRT, YR11)
for f, k in ((F("S11", 0.45), 1.0), (F("S11", 1.0), 0.9), (END("S11"), 1.0)):
    gesture(RY, "L", f, PRT, YR11, (0.38 * k, -0.18, 0.12), (1.0, -0.5, 0.0), (0.0, -0.2, 1.0), pole=(0.6, 0.4, 0.1))
relax_fingers(RR, [F("S11", 0.0)]); apply_pose(RR, "L", "open_alarm", F("S11", 0.45)); apply_pose(RR, "L", "open_alarm", END("S11"))
YR12 = yaw_to(PRT, PKN) * 0.6 + YR11 * 0.4
stand(RY, F("S12", 0.0), PRT, YR11, head=(-4, 2), arms=False)
stand(RY, F("S12", 0.6), PRT, YR12, head=(-6, 8), arms=False)
stand(RY, F("S12", 1.0), PRT, YR12, head=(4, 8), arms=False)
stand(RY, END("S12"), PRT, YR12, head=(-4, 6), arms=False)
gesture(RY, "L", F("S12", 0.0), PRT, YR11, (0.38, -0.18, 0.12), (1.0, -0.5, 0.0), (0.0, -0.2, 1.0), pole=(0.6, 0.4, 0.1))
hang1(RY, "L", F("S12", 0.5), PRT, YR12); hang1(RY, "L", END("S12"), PRT, YR12)
hang1(RY, "R", F("S12", 0.0), PRT, YR11); hang1(RY, "R", END("S12"), PRT, YR12)
apply_pose(RR, "L", "relaxed", F("S12", 0.5))
YK11 = yaw_to(PKN, Vector((0.0, -1.2, 0)))
YK12 = yaw_to(PKN, PRT) * 0.6 + YK11 * 0.4
stand(KN, F("S11", 0.0), PKN, YK11, head=(-2, 0), arms=False)
stand(KN, F("S11", 0.8), PKN, YK11 - 6, head=(-6, -8), arms=False)
stand(KN, END("S11"), PKN, YK11, head=(-4, 4), arms=False)
palms_up(KN, F("S11", 0.0), PKN, YK11, 0.6); palms_up(KN, F("S11", 0.8), PKN, YK11 - 6, 1.0); palms_up(KN, END("S11"), PKN, YK11, 0.9)
for s in "LR": apply_pose(KR, s, "open_alarm", F("S11", 0.0))
stand(KN, F("S12", 0.0), PKN, YK11, head=(-4, 4), arms=False)
stand(KN, F("S12", 0.9), PKN, YK12, head=(-2, 6), arms=False)
stand(KN, END("S12"), PKN, YK12, head=(4, 6), arms=False)
palms_up(KN, F("S12", 0.0), PKN, YK11, 0.9); hang1(KN, "L", F("S12", 0.6), PKN, YK12); hang1(KN, "L", END("S12"), PKN, YK12)
hang1(KN, "R", F("S12", 0.6), PKN, YK12); hang1(KN, "R", END("S12"), PKN, YK12)
relax_fingers(KR, [F("S12", 0.6)])

# ================================================================== days pass, panic (S13-S16), Tom alone in the hall
A13 = Vector((-1.05, -2.9, 0)); B13 = Vector((0.08, -0.78, 0))
p13 = lambda f: A13.lerp(B13, smooth(min(1, max(0, (f - F("S13", 0.0)) / (F("S13", 1.55) - F("S13", 0.0))))))
y13 = lambda f: yaw_to(A13, B13) if f < F("S13", 1.3) else yaw_to(A13, B13) + (180 - yaw_to(A13, B13)) * smooth(min(1, (f - F("S13", 1.3)) / 30))
walk_with_arms(T, p13, y13, F("S13", 0.0), F("S13", 1.55), stride=1.05, amp=0.09)
stand(T, F("S13", 1.75), B13, 180, head=(-4, 0), flex=3)
stand(T, END("S13"), B13, 180, head=(-6, 8), flex=4)
relax_fingers(TR, [F("S13", 0.0)])
# S14: turns from the doorway, both hands to his head, a step back
P14 = Vector((0.08, -0.95, 0))
stand(T, F("S14", 0.0), B13, 180, head=(-6, 8), flex=4)
stand(T, F("S14", 0.5), B13, 90, head=(2, 10), flex=3, arms=False)
stand(T, F("S14", 1.0), P14, 10, head=(-4, 0), flex=-2, arms=False)
stand(T, F("S14", 1.5), P14, 0, head=(-8, 6), flex=-4, arms=False)
stand(T, END("S14"), P14, -5, head=(-6, -6), flex=-3, arms=False)
key_hang(T, F("S14", 0.0), Vector((B13.x, B13.y, T.root_head.z)), 180)
def hands_on_head(H, rig, f, pos, yaw, head):
    """palms on the sides of the head (just off the hair), elbows out; from the evaluated head bone"""
    sc.frame_set(f); bpy.context.view_layer.update()
    hb = rig.pose.bones["head"]; M = rig.matrix_world @ hb.matrix
    c = M @ Vector((0, 0.085, 0))
    side = (M.to_3x3() @ Vector((1, 0, 0))).normalized(); up = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    fwd = side.cross(up).normalized()
    for s, sx in (("L", 1), ("R", -1)):
        pp = c + side * sx * 0.098 - fwd * 0.01
        place_hand(rig, s, f, pp, -side * sx, (up * 0.8 - fwd * 0.6).normalized(), skin=0.022)
        pb = rig.pose.bones["Pole_elbow." + s]; n = "Pole_elbow." + s
        pole = c + side * sx * 0.6 - fwd * 0.3 + Vector((0, 0, -0.1))
        pb.location = H.r.rest(n).to_3x3().inverted() @ (pole - H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
for f in (F("S14", 1.0), F("S14", 1.5), END("S14")):
    hands_on_head(T, TR, f, P14, 0, None)
for s in "LR": apply_pose(TR, s, "relaxed", F("S14", 0.4)); apply_pose(TR, s, "cup_hold", F("S14", 1.0)); apply_pose(TR, s, "cup_hold", END("S14"))
# S15: close, he looks up at the memory cloud; it breaks apart
P15 = Vector((0.08, -1.0, 0))
stand(T, F("S15", 0.0), P15, 0, head=(-10, 0), flex=-2)
stand(T, F("S15", 1.2), P15, 0, head=(-14, 6), flex=-3)
stand(T, F("S15", 2.4), P15, 0, head=(-8, -6), flex=-2)
stand(T, END("S15"), P15, 0, head=(2, 4), flex=1)
relax_fingers(TR, [F("S15", 0.0)])
# S16: losing his mind: slow head shake, breath
stand(T, F("S16", 0.0), P15, 0, head=(4, 4), flex=1)
for i, t_ in enumerate((0.3, 0.6, 0.9, 1.2)):
    stand(T, F("S16", t_), P15, 0, head=(5, 9 * (-1) ** i), flex=2 + i * 0.5, side=1.5 * (-1) ** i)
stand(T, END("S16"), P15, 0, head=(7, 0), flex=3)

# ================================================================== CLINIC (S17-S19)
PCH = bpy.data.objects["Clinic_PatChair"]; DCH = bpy.data.objects["Clinic_DocChair"]
seatP = (PCH.location.x, PCH.location.y); seatD = (DCH.location.x, DCH.location.y)
YP = yaw_to(seatP, seatD); YD = yaw_to(seatD, seatP)
PCH.rotation_euler.z = R_(YP); DCH.rotation_euler.z = R_(YD); bpy.context.view_layer.update()
zP = seat_top("Clinic_PatChair", *seatP); zD = seat_top("Clinic_DocChair", *seatD)
print("SEATS", round(zP, 3), round(zD, 3), "yaws", round(YP), round(YD))
for f, hd, b in ((F("S17", 0.0), (6, 0), 0.0), (F("S17", 0.4), (4, 4), 0.025), (F("S17", 0.6), (4, 6), 0.0), (F("S17", 0.8), (2, 6), 0.025),
                 (F("S17", 1.0), (2, 2), 0.0), (F("S17", 1.4), (0, -4), 0.02), (END("S17"), (2, 0), 0.0)):
    sit(T, f, seatP, YP, zP, head=hd, bounce=b)
relax_fingers(TR, [F("S17", 0.0)])
DOC = HS["Doc"]; DR = RIGS["Doc"]
for f, hd in ((F("S17", 0.0), (2, 0)), (F("S17", 0.8), (6, -4)), (END("S17"), (4, 0))):
    sit(DOC, f, seatD, YD, zD, head=hd, flex=4)
relax_fingers(DR, [F("S17", 0.0)])
# S18: the doctor turns to the monitor and points at the scan; Tom watches (back three-quarter)
mon = bpy.data.objects["Clinic_Monitor"]
sit(T, F("S18", 0.0), seatP, YP, zP, head=(2, 0)); sit(T, F("S18", 0.8), seatP, YP, zP, head=(0, -10)); sit(T, END("S18"), seatP, YP, zP, head=(-2, -12))
YD2 = yaw_to(seatD, (mon.location.x, mon.location.y))
sit(DOC, F("S18", 0.0), seatD, YD, zD, head=(4, 0), flex=4)
sit(DOC, F("S18", 0.6), seatD, YD + 22, zD, head=(0, 28), flex=6, hands=False)
sit(DOC, END("S18"), seatD, YD + 22, zD, head=(-2, 24), flex=6, hands=False)
sc.frame_set(F("S18", 0.6))
# screen plane (found from the monitor mesh: front face of the upper part)
vs = [v.co for v in mon.data.vertices if v.co.z > 0.18]
y_front = min(v.y for v in vs); xs = [v.x for v in vs]; zs = [v.z for v in vs]
sw, shh = (max(xs) - min(xs)) * 0.93, (max(zs) - min(zs)) * 0.88
bpy.ops.mesh.primitive_plane_add(size=1); scr = bpy.context.object; scr.name = "Clinic_Screen"
for c_ in list(scr.users_collection): c_.objects.unlink(scr)
bpy.data.collections["SET_Clinic"].objects.link(scr)
scr.parent = mon; scr.location = ((max(xs) + min(xs)) / 2, y_front - 0.003, (max(zs) + min(zs)) / 2); scr.rotation_euler = (R_(90), 0, 0)
scr.scale = (sw, shh, 1)
sm = bpy.data.materials.new("ScreenScan"); sm.use_nodes = True; nt = sm.node_tree; Pn = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = bpy.data.images.load(HERE + "assets/brain_scan.png"); ti.image.pack()
Pn.inputs["Base Color"].default_value = (0, 0, 0, 1); nt.links.new(ti.outputs[0], Pn.inputs["Emission Color"]); Pn.inputs["Emission Strength"].default_value = 1.4
Pn.inputs["Roughness"].default_value = 0.25; scr.data.materials.append(sm)
bpy.context.view_layer.update()
scr_c = scr.matrix_world.translation.copy(); scr_n = (scr.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
if scr_n.y > 0: scr_n = -scr_n
print("SCREEN centre", tuple(round(x, 3) for x in scr_c), "normal", tuple(round(x, 3) for x in scr_n), "size", round(sw, 3), round(shh, 3))
tip = scr_c + scr_n * 0.05 + Vector((0.09, 0, 0.03))
for f in (F("S18", 0.9), F("S18", 1.4), END("S18")):
    place_hand(DR, "R", f, tip + scr_n * 0.1, -scr_n, (-scr_n + Vector((0, 0, 0.1))).normalized(), skin=0.0)
    apply_pose(DR, "R", "point", f)
body_hand(DOC, "R", F("S18", 0.0), Vector((seatD[0], seatD[1], zD + 0.15)), YD, (-0.13, -0.33, 0.11), (-0.1, -1.0, -0.25), (0, 0, -1), pole_off=(-0.45, 0.25, 0.1))
apply_pose(DR, "R", "relaxed", F("S18", 0.3))
for f in (F("S18", 0.6), END("S18")):
    body_hand(DOC, "L", f, Vector((seatD[0], seatD[1], zD + 0.15)), YD + 22, (0.13, -0.33, 0.11), (0.1, -1.0, -0.25), (0, 0, -1), pole_off=(0.45, 0.25, 0.1))
sit(T, F("S19", 0.0), seatP, YP, zP, head=(-2, -12)); sit(T, END("S19"), seatP, YP, zP, head=(-2, -12))
sit(DOC, F("S19", 0.0), seatD, YD + 22, zD, head=(-2, 24), flex=6); sit(DOC, END("S19"), seatD, YD + 22, zD, head=(-2, 24), flex=6)
relax_fingers(DR, [F("S19", 0.0)])

# ================================================================== it had always been a bathroom (S20)
P20 = Vector((0.1, -0.5, 0))
stand(T, F("S20", 0.0), P20, 180, head=(-4, 0), flex=3)
stand(T, F("S20", 0.6), P20, 180, head=(4, -4), flex=5)
stand(T, F("S20", 1.2), P20, 110, head=(2, -6), flex=3)
stand(T, F("S20", 1.6), P20, 62, head=(0, -4), flex=2)
stand(T, END("S20"), P20, 58, head=(3, 0), flex=3)
relax_fingers(TR, [F("S20", 0.0)])
for n, H in HS.items(): pass

# ------------------------------------------------------------------ visibility per shot: characters + dressings
def chars_in(sid):
    return {"S01": ["Tom"], "S02": ["Tom"], "S03": [], "S04": ["Tom"], "S05": ["Tom"], "S06": ["Tom"], "S07": ["Ray", "Ken"],
            "S08": ["Ray", "Ken"], "S09": ["Tom", "Ray", "Ken"], "S10": ["Tom"], "S11": ["Ray", "Ken"], "S12": ["Ray", "Ken"],
            "S13": ["Tom"], "S14": ["Tom"], "S15": ["Tom"], "S16": ["Tom"], "S17": ["Tom", "Doc"], "S18": ["Tom", "Doc"],
            "S19": ["Tom", "Doc"], "S20": ["Tom"], "S21": []}[sid]
for n, r in RIGS.items():
    rngs = [(s[2], s[3]) for s in SHOTS if n in chars_in(s[0])]
    merged = []
    for a_, b_ in rngs:
        if merged and a_ == merged[-1][1] + 1: merged[-1] = (merged[-1][0], b_)
        else: merged.append((a_, b_))
    vis_char(r, merged)
DRESS = {"hall": "DRESS_Bath", "bath": "DRESS_Bath", "prank": "DRESS_Prank", "clinic": "DRESS_Bath"}
for dn in ("DRESS_Bath", "DRESS_Closet", "DRESS_Prank"):
    names = [o.name for o in bpy.data.collections[dn].all_objects]
    rngs = [(s[2], s[3]) for s in SHOTS if DRESS[s[1]] == dn]
    key_vis(names, rngs) if rngs else key_vis(names, [])

# ------------------------------------------------------------------ memory cloud (S15): the remembered closet in a thought cloud, then it breaks apart
# assets/memory_cloud.png is made by scripts/02c_cloud.py (system python + PIL)
cimg = bpy.data.images.load(HERE + "assets/memory_cloud.png"); cimg.pack()
cm = bpy.data.materials.new("MemoryCloud"); cm.use_nodes = True; nt = cm.node_tree; Pn = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = cimg
nt.links.new(ti.outputs["Color"], Pn.inputs["Base Color"]); nt.links.new(ti.outputs["Alpha"], Pn.inputs["Alpha"])
nt.links.new(ti.outputs["Color"], Pn.inputs["Emission Color"]); Pn.inputs["Emission Strength"].default_value = 0.35
CC = bpy.data.collections.new("FX_Memory"); sc.collection.children.link(CC)
CLOUD_C = Vector((0.08, -1.05, 2.12)); CW = 0.62; N = 8
tiles = []
for i in range(N):
    for j in range(N):
        me = bpy.data.meshes.new("MemTile"); w = CW / N
        me.from_pydata([(-w / 2, 0, -w / 2), (w / 2, 0, -w / 2), (w / 2, 0, w / 2), (-w / 2, 0, w / 2)], [], [(0, 1, 2, 3)])
        uv = me.uv_layers.new(); u0, u1, v0, v1 = i / N, (i + 1) / N, j / N, (j + 1) / N
        for k, (u, v) in enumerate(((u0, v0), (u1, v0), (u1, v1), (u0, v1))): uv.data[k].uv = (u, v)
        me.materials.append(cm)
        o = bpy.data.objects.new("MemTile_%d_%d" % (i, j), me); CC.objects.link(o)
        o.location = CLOUD_C + Vector((-CW / 2 + (i + 0.5) * w, 0, -CW / 2 + (j + 0.5) * w)); tiles.append((o, i, j))
import random; random.seed(19)
fb = F("S15", 1.6)
for o, i, j in tiles:
    base = o.location.copy(); o.keyframe_insert("location", frame=fb); o.keyframe_insert("rotation_euler", frame=fb); o.keyframe_insert("scale", frame=fb)
    d0 = fb + int(random.random() * 40)
    o.keyframe_insert("location", frame=d0); o.keyframe_insert("scale", frame=d0)
    dirv = Vector((i - N / 2 + 0.5, -random.random() * 2, j - N / 2 + 0.5)).normalized()
    o.location = base + dirv * (0.18 + random.random() * 0.15); o.rotation_euler = (random.uniform(-1.5, 1.5), random.uniform(-1, 1), random.uniform(-1.5, 1.5))
    o.scale = (0.01, 0.01, 0.01); f2 = d0 + 40 + int(random.random() * 20)
    o.keyframe_insert("location", frame=f2); o.keyframe_insert("rotation_euler", frame=f2); o.keyframe_insert("scale", frame=f2)
dots = []
for k, (dx, dz, r) in enumerate(((0.0, -0.38, 0.035), (0.05, -0.47, 0.022))):
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=r, fill_type='NGON', location=CLOUD_C + Vector((dx, 0, dz)), rotation=(R_(90), 0, 0))
    d = bpy.context.object; d.name = "MemDot%d" % k
    for c_ in list(d.users_collection): c_.objects.unlink(d)
    CC.objects.link(d); d.data.materials.append(bpy.data.materials.get("Towel")); dots.append(d)
key_vis([o.name for o, i, j in tiles] + [d.name for d in dots], [(SH["S15"][2], SH["S15"][3])])

# ------------------------------------------------------------------ cameras (one per shot, Track To with world up) + face fill/catchlight
def head_pt(rig, f, up=0.08):
    sc.frame_set(f); bpy.context.view_layer.update(); hb = rig.pose.bones["head"]
    return rig.matrix_world @ hb.head + Vector((0, 0, up))
CAMS = {}
def cam(sid, keys, tkeys, lens=35):
    o = cam_shot(sid, keys, lens=lens, target_keys=tkeys); CAMS[sid] = o
    return o
h = lambda n, sid, t=0.5, up=0.08: head_pt(RIGS[n], F(sid, t), up)
cam("S01", [(F("S01", 0), (-0.55, -2.15, 1.38)), (END("S01"), (-0.4, -1.8, 1.4))], [(F("S01", 0), (0.12, 0.0, 1.08)), (END("S01"), (0.12, 0.35, 1.1))], 26)
cam("S02", [(F("S02", 0), (0.75, -1.3, 1.6)), (END("S02"), (0.58, -1.12, 1.62))], [(F("S02", 0), (-0.15, 1.5, 1.05)), (END("S02"), (-0.12, 1.5, 1.0))], 24)
cam("S03", [(F("S03", 0), (0.02, -2.25, 1.48)), (END("S03"), (0.02, -1.10, 1.42))], [(F("S03", 0), (0.0, 1.6, 1.05)), (END("S03"), (0.0, 1.6, 1.0))], 26)
hp4 = h("Tom", "S04", 0.5, 0.06)
cam("S04", [(F("S04", 0), hp4 + Rz(YT_R + 10) @ Vector((0.20, -0.95, 0.02))), (END("S04"), hp4 + Rz(YT_R + 10) @ Vector((0.16, -0.78, 0.02)))], [(F("S04", 0), hp4), (END("S04"), hp4)], 50)
hp5 = h("Tom", "S05", 0.8, -0.15)
cam("S05", [(F("S05", 0), hp5 + Rz(YT_R) @ Vector((0.35, -2.1, 0.0))), (END("S05"), hp5 + Rz(YT_R) @ Vector((0.28, -1.8, 0.02)))], [(F("S05", 0), hp5), (END("S05"), hp5 + Vector((0, 0, 0.03)))], 30)
hp6 = h("Tom", "S06", 0.8, -0.2)
cam("S06", [(F("S06", 0), hp6 + Rz(YT_R) @ Vector((-0.65, -1.9, 0.12))), (END("S06"), hp6 + Rz(YT_R) @ Vector((-0.5, -1.75, 0.12)))], [(F("S06", 0), hp6 + Vector((-0.1, 0.1, 0))), (END("S06"), hp6 + Vector((-0.1, 0.1, 0)))], 28)
mid7 = (h("Ray", "S07", 0.6, -0.25) + h("Ken", "S07", 0.6, -0.25)) / 2
cam("S07", [(F("S07", 0), Vector((0.35, -1.25, 1.55))), (END("S07"), Vector((0.2, -1.5, 1.55)))], [(F("S07", 0), mid7), (END("S07"), mid7)], 30)
hp8 = h("Ray", "S08", 0.5, -0.05)
cam("S08", [(F("S08", 0), hp8 + Rz(YR_T) @ Vector((-0.25, -1.25, 0.02))), (END("S08"), hp8 + Rz(YR_T) @ Vector((-0.2, -1.05, 0.02)))], [(F("S08", 0), hp8), (END("S08"), hp8)], 40)
mid9 = (h("Tom", "S09", 1.0, -0.2) + h("Ray", "S09", 1.0, -0.2)) / 2
cam("S09", [(F("S09", 0), mid9 + Vector((0.55, -2.25, 0.05))), (END("S09"), mid9 + Vector((0.35, -1.95, 0.05)))], [(F("S09", 0), mid9 + Vector((0, 0.3, 0))), (END("S09"), mid9 + Vector((0, 0.3, 0)))], 28)
hp10 = h("Tom", "S10", 0.5, 0.05)
cam("S10", [(F("S10", 0), hp10 + Rz(YT9 + 18) @ Vector((-0.12, -0.85, 0.0))), (END("S10"), hp10 + Rz(YT9 + 18) @ Vector((-0.08, -0.7, 0.0)))], [(F("S10", 0), hp10), (END("S10"), hp10)], 50)
cam("S11", [(F("S11", 0), (0.28, -1.35, 1.62)), (END("S11"), (0.24, -1.05, 1.58))], [(F("S11", 0), (-0.08, 1.2, 0.85)), (END("S11"), (-0.08, 1.2, 0.85))], 24)
cam("S12", [(F("S12", 0), (0.42, -1.15, 1.5)), (END("S12"), (0.3, -1.0, 1.5))], [(F("S12", 0), (-0.3, 1.35, 1.2)), (END("S12"), (-0.3, 1.35, 1.25))], 30)
cam("S13", [(F("S13", 0), (1.75, -2.9, 1.5)), (END("S13"), (1.45, -2.0, 1.5))], [(F("S13", 0), (-0.9, -2.6, 1.2)), (F("S13", 1.5), (0.0, -0.9, 1.2)), (END("S13"), (0.05, -0.6, 1.25))], 28)
cam("S14", [(F("S14", 0), (0.25, -2.75, 1.55)), (END("S14"), (0.2, -2.35, 1.6))], [(F("S14", 0), (0.08, -0.8, 1.25)), (END("S14"), (0.08, -0.9, 1.35))], 30)
hp15 = h("Tom", "S15", 1.0, 0.0)
cam("S15", [(F("S15", 0), hp15 + Vector((0.05, -0.95, -0.12))), (END("S15"), hp15 + Vector((0.03, -0.82, -0.1)))], [(F("S15", 0), hp15 + Vector((0, 0, 0.30))), (END("S15"), hp15 + Vector((0, 0, 0.28)))], 26)
hp16 = h("Tom", "S16", 0.6, 0.05)
cam("S16", [(F("S16", 0), hp16 + Vector((-0.22, -0.8, 0.0))), (END("S16"), hp16 + Vector((-0.16, -0.66, 0.0)))], [(F("S16", 0), hp16), (END("S16"), hp16)], 50)
hp17 = (h("Tom", "S17", 0.6, -0.3) + h("Doc", "S17", 0.6, -0.3)) / 2
hT17 = h("Tom", "S17", 0.6, -0.3)
cam("S17", [(F("S17", 0), Vector((X0 + 1.35, 0.3, 1.3))), (END("S17"), Vector((X0 + 1.1, 0.3, 1.28)))], [(F("S17", 0), hT17), (END("S17"), hT17 + Vector((0, 0, 0.03)))], 30)
hpT18 = h("Tom", "S18", 0.5, 0.0)
cam("S18", [(F("S18", 0), Vector((X0 + 0.15, -0.85, 1.45))), (END("S18"), Vector((X0 + 0.22, -0.62, 1.42)))], [(F("S18", 0), scr_c + Vector((0.2, -0.45, -0.15))), (END("S18"), scr_c + Vector((0.2, -0.45, -0.12)))], 28)
cam("S19", [(F("S19", 0), scr_c + scr_n * 0.62 + Vector((-0.08, 0, 0.04))), (END("S19"), scr_c + scr_n * 0.36 + Vector((-0.03, 0, 0.02)))], [(F("S19", 0), scr_c), (END("S19"), scr_c + Vector((-0.03, 0, 0.03)))], 35)
cam("S20", [(F("S20", 0), (0.95, -2.05, 1.25)), (END("S20"), (0.75, -1.75, 1.3))], [(F("S20", 0), (0.0, 0.2, 1.2)), (END("S20"), (0.0, 0.3, 1.2))], 26)
cam("S21", [(F("S21", 0), (0.0, -2.1, 1.5)), (END("S21"), (0.0, -1.08, 1.42))], [(F("S21", 0), (0.0, 1.6, 1.05)), (END("S21"), (0.0, 1.6, 0.98))], 26)
# camera-riding face fill (<= 8 W) gives every face a catchlight; on only during its own shot
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'CONSTANT'
for sid, setn, f0, f1, note in SHOTS:
    l = bpy.data.lights.new("FaceFill_" + sid, 'AREA'); l.energy = 0.0; l.size = 0.3; l.color = (1.0, 0.97, 0.93)
    lo = bpy.data.objects.new("FaceFill_" + sid, l); sc.collection.objects.link(lo)
    lo.parent = CAMS[sid]; lo.location = (0.15, 0.25, 0.0)
    l.keyframe_insert("energy", frame=0); l.energy = 8.0; l.keyframe_insert("energy", frame=f0); l.energy = 0.0; l.keyframe_insert("energy", frame=f1 + 1)
    set_interp(l, 'CONSTANT')
set_interp(sc.world.node_tree if sc.world.node_tree.animation_data else sc.world, 'CONSTANT')
for o in bpy.data.objects:
    if o.animation_data and o.type in ('MESH', 'EMPTY', 'LIGHT', 'CAMERA'):
        for fc in fcurves_of(o):
            if fc.data_path.startswith("hide"):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
json.dump([{"shot": s[0], "set": s[1], "f0": s[2], "f1": s[3], "vo": s[4]} for s in SHOTS], open(HERE + "shots_provisional.json", "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SHOTS_DONE")
