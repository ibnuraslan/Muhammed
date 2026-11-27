"""WW1Assassination v009 stage B: staging, acting, the two cars, the bomb and blast, the shots, the ONE continuous camera,
colour keys and the VO. Timing is built on the client's voiceover (v007 VO, 30.4 s) from the start.
blender -b base.blend --python 02_animate.py -- <out.blend> <vo.mp3>
VO beats (film frames, 60 fps): 1 He fired at the car | 152 aiming at the Archduke | 342 But he wasn't the first |
473 Earlier, two would-be assassins | 631 Then a third threw a bomb | 777 exploded under the car behind |
911 Later, their driver turned | 1057 right where another assassin | 1237 He fired twice | 1433 declared war | 1591 that's how WW1 began."""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline"))
exec(open(os.path.join(HERE, "lib.py")).read())
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(os.path.join(HERE, "lib_anim.py")).read())
args = sys.argv[sys.argv.index("--") + 1:]
OUT, VO = os.path.abspath(args[0]), os.path.abspath(args[1])
END = 1826
O = bpy.data.objects
random.seed(11)
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
def log(*a): print("LOG", " ".join(str(x) for x in a))

# ================================================================== CAR ROUTE: quay (y=1, heading +x) -> left turn (r=4) -> side street (x=1.6, +y)
QY = 1.0; XC = -2.4; RT = 4.0; SX = XC + RT
S_ARC0 = XC + 100.0; S_ARC1 = S_ARC0 + math.pi / 2 * RT
def route(s):
    if s <= S_ARC0: return Vector((s - 100.0, QY, 0)), 0.0
    if s <= S_ARC1:
        a = (s - S_ARC0) / RT
        return Vector((XC + RT * math.sin(a), QY + RT - RT * math.cos(a), 0)), math.degrees(a)
    return Vector((SX, QY + RT + (s - S_ARC1), 0)), 90.0
CAR1_S = pchip([(1, 91.0), (75, 95.2), (150, 99.0), (250, 103.6), (341, 106.6),
                (352, 106.3), (420, 85.0), (465, 60.0), (480, 57.5),
                (630, 61.6), (700, 64.4), (735, 65.4), (760, 66.0), (790, 68.0), (830, 72.5), (910, 84.0),
                (950, 93.0), (990, 99.4), (1025, 106.3), (1048, 112.6), (1056, 112.9), (1070, 112.9), (1112, 109.4), (1116, 109.4)])
def s1(f): return CAR1_S(f)
def car_M(s, extra=Matrix.Identity(4)):
    p, h = route(s)
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(h), 4, 'Z') @ extra
HOOD_L = Vector((-(262 * 0.0058) - 0.10, 0.18, (113 + 198) * 0.0058 + 0.02 + 0.16))
# the bomb: hits the folded hood at f735, bounces back off it onto the cobbles, rolls back toward the second car
F_REL, F_HIT, F_LAND, F_STOP, F_BOOM = 705, 735, 760, 792, 801
P_HIT = car_M(s1(F_HIT)) @ HOOD_L
P_LAND = Vector((P_HIT.x - 2.0, 0.75, 0.045))
SITE = Vector((P_LAND.x - 0.9, 0.85, 0.045))
S2_BOOM = SITE.x + 100.0 - 0.3
CAR2_S = pchip([(700, s1(700) - 12.0), (760, S2_BOOM - 5.6), (F_BOOM, S2_BOOM), (812, S2_BOOM + 0.45), (830, S2_BOOM + 0.6)])
def s2(f):
    if f <= 700: return s1(f) - 12.0
    return CAR2_S(min(f, 830))
log("SITE", tuple(round(c, 2) for c in SITE), "P_HIT", tuple(round(c, 2) for c in P_HIT))

def key_car(root, body, sfun, wheels, r, f0=1, f1=END, sway_seed=0):
    root.rotation_mode = 'XYZ'
    for f in range(f0, f1 + 1):
        s = sfun(f); p, h = route(s)
        root.location = p; root.rotation_euler = (0, 0, math.radians(h))
        root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
        for w in wheels:
            w.rotation_euler.y = s / r; w.keyframe_insert("rotation_euler", index=1, frame=f)
        if f % 3 == 0:
            v = abs(sfun(f + 1) - sfun(f - 1)) * 30
            body.location.z = 0.006 * math.sin(f * 0.9 + sway_seed) * min(1.0, v / 3.0)
            body.rotation_euler.y = 0.004 * math.sin(f * 0.5 + sway_seed) * min(1.0, v / 3.0)
            body.keyframe_insert("location", index=2, frame=f); body.keyframe_insert("rotation_euler", index=1, frame=f)
CAR1, CAR2 = O["Car1"], O["Car2"]
W1 = [o for o in O if o.parent == CAR1 and "wheel" in o.name]; W2 = [o for o in O if o.parent == CAR2 and "wheel" in o.name]
key_car(CAR1, O["Car1_Body"], s1, W1, CAR1["wheel_r"])
key_car(CAR2, O["Car2_Body"], s2, W2, CAR2["wheel_r"], sway_seed=2)
# the blast lifts car 2 (jolt + pitch, settles); nothing else is damaged on screen
B2 = O["Car2_Body"]
for f, z, ry in ((F_BOOM, 0.0, 0.0), (F_BOOM + 4, 0.32, -0.08), (F_BOOM + 10, 0.12, 0.03), (F_BOOM + 16, 0.0, 0.0), (F_BOOM + 24, 0.03, 0.0), (F_BOOM + 32, 0.0, 0.0)):
    B2.location.z = z; B2.rotation_euler.y = ry
    B2.keyframe_insert("location", index=2, frame=f); B2.keyframe_insert("rotation_euler", index=1, frame=f)

# ================================================================== PEOPLE: build the controls
SEATED = {"Archduke": ("Car1", (-1.17, -0.33), "rear"), "Duchess": ("Car1", (-1.17, 0.33), "rear"),
          "Driver": ("Car1", (0.02, 0.30), "front"), "Driver2": ("Car2", (0.02, 0.30), "front")}
P = {}
for nm, (car, seat, row) in SEATED.items():
    rig = O[nm]; p = Person(rig, seated=True)
    rig.parent = O[car + "_Body"]; rig.matrix_parent_inverse = Matrix.Identity(4)
    p.seat = Vector((seat[0], seat[1], O[car]["seat_rear_z" if row == "rear" else "seat_front_z"])); p.floor = O[car]["floor_z"] + (0.016 if nm != "Duchess" else 0.0)   # v009: soles on the car floor, not 1.7 cm into it
    P[nm] = p
for nm in ("Gunman", "Bomber", "Nerve1", "Nerve2", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "C1", "C2", "C3"):
    P[nm] = Person(O[nm])
for nm, p in P.items():
    for s in "LR": apply_pose(p.o, s, "relaxed", 1)

# ---- seated acting (car-local). heads: (pitch down +, yaw left +)
def seated_track(p, keys, f0=1, f1=END, step=10, seed=0, flex0=4.0):
    """keys: [(frame, dict(head=(pitch,yaw), flex=, twist=, side=))] interpolated (pchip); breathing on top"""
    fr = [k[0] for k in keys]
    def comp(name, idx=None, default=0.0):
        pts = []
        for f, d in keys:
            v = d.get(name, default if idx is None else (0.0, 0.0))
            pts.append((f, v if idx is None else v[idx]))
        return pchip(pts)
    hp, hy, fl, tw, sd = comp("head", 0), comp("head", 1), comp("flex", None, flex0), comp("twist"), comp("side")
    fs = sorted(set(list(range(f0, f1 + 1, step)) + [f for f in fr if f0 <= f <= f1]))
    for f in fs:
        b = math.sin((f + seed * 13) / 40.0 * 2 * math.pi)
        p.key_body(f, p.seat, yaw=90, spine=(fl(f) + 1.0 * b, tw(f), sd(f)), head=(hp(f), hy(f)))
        p.key_feet_seated(f, p.seat, 90, p.floor) if f == fs[0] else None
    return fs

AR, DU, DR, DR2 = P["Archduke"], P["Duchess"], P["Driver"], P["Driver2"]
# Archduke (right rear): B1 looks ahead/right; B2 turns right toward the shot; B4-5 nods left to the crowd; B6 looks back;
# B7-8 looks around; B9 hit at 1290: slumps forward (no blood, no wound)
ar_keys = [(1, dict(head=(0, -10))), (70, dict(head=(-3, -25))), (95, dict(head=(-5, -45), flex=-2)), (200, dict(head=(-2, -55), flex=-2)),
           (341, dict(head=(0, -40))), (480, dict(head=(0, 15))), (560, dict(head=(3, 35))), (640, dict(head=(0, 25))), (720, dict(head=(-2, 40))),
           (745, dict(head=(-4, 55), twist=10)), (805, dict(head=(-4, 70), twist=18)), (880, dict(head=(0, 30), twist=8)), (960, dict(head=(0, 0))),
           (1060, dict(head=(0, -20))), (1180, dict(head=(-2, -35))), (1270, dict(head=(-4, -50), flex=-2)), (1290, dict(head=(-6, -55), flex=-3)),
           (1300, dict(head=(10, -40), flex=8)), (1330, dict(head=(35, -15), flex=30, side=4)), (1380, dict(head=(40, -10), flex=34, side=5)), (END, dict(head=(40, -10), flex=34, side=5))]
du_keys = [(1, dict(head=(0, 15))), (80, dict(head=(-3, -10))), (110, dict(head=(-5, -35))), (220, dict(head=(-3, -40))), (341, dict(head=(0, -20))),
           (480, dict(head=(0, 30))), (630, dict(head=(-2, 45))), (700, dict(head=(-3, 50))), (740, dict(head=(-6, 70), twist=12)),
           (805, dict(head=(-5, 80), twist=20)), (880, dict(head=(0, 35), twist=8)), (960, dict(head=(0, 10))), (1100, dict(head=(0, -15))),
           (1250, dict(head=(-2, -40))), (1316, dict(head=(-4, -45))), (1326, dict(head=(10, -20), flex=10)), (1365, dict(head=(38, 10), flex=33, side=-4)),
           (END, dict(head=(40, 10), flex=34, side=-4))]
dr_keys = [(1, dict(head=(0, 0))), (300, dict(head=(0, -10))), (800, dict(head=(0, 30), twist=10)), (870, dict(head=(0, 0))),
           (1050, dict(head=(0, 0))), (1062, dict(head=(0, 70), twist=25)), (1110, dict(head=(0, 75), twist=25)), (1150, dict(head=(0, 0))),
           (1295, dict(head=(-3, -55), twist=-15)), (END, dict(head=(-3, -55), twist=-15))]
dr2_keys = [(1, dict(head=(0, 0))), (F_BOOM, dict(head=(0, 0))), (F_BOOM + 8, dict(head=(-10, 25), flex=-6, twist=8)), (F_BOOM + 60, dict(head=(5, 10))), (END, dict(head=(0, 0)))]
for p, keys, sd in ((AR, ar_keys, 1), (DU, du_keys, 2), (DR, dr_keys, 3), (DR2, dr2_keys, 4)):
    p.frames = seated_track(p, keys, seed=sd)
# arms: lap by default; Duchess waves to the crowd (B4-B5) with her left hand; both startle at the shot (B2) and at the blast
def arms_seated(p, plan):
    """plan(f) -> {"L": ("lap"|"wave"|"chest", amount), ...}"""
    for f in p.frames:
        for s in "LR":
            kind = plan(f, s)
            if kind == "lap": p.arm_lap(s, f)
            elif kind == "wave": p.arm_wave(s, f, phase=f / 9.0, height=0.6)
            elif kind == "chest": p.arm_chest(s, f, k=0.8)
AR.lap_up = 0.09; DU.lap_up = 0.03   # v009: the Archduke's hands sank into his thighs (clip_scan)
arms_seated(AR, lambda f, s: "chest" if (s == "L" and 95 <= f <= 160) else "lap")
arms_seated(DU, lambda f, s: ("wave" if (s == "L" and 500 <= f <= 690) else ("chest" if (s == "R" and (100 <= f <= 170 or 805 <= f <= 850)) else "lap")))
for p in (AR, DU, DR2):
    for s in "LR":
        apply_pose(p.o, s, "relaxed", 1)
# drivers: hands on the steering wheel rim (10 and 2), wrap grip; car-local wheel centre from the CC-BY model
SW_C = Vector((70 * 0.0058, 45 * 0.0058, (117 + 198) * 0.0058)); SW_UP = Vector((0.8, 0, 0.6)); SW_N = Vector((-0.6, 0, 0.8))
def wheel_hands(p, frames, cy):
    for f in frames:
        for s, sy in (("L", 1), ("R", -1)):
            W = Vector((SW_C.x, cy, SW_C.z)) + Vector((0, sy * 0.17, 0)) + SW_UP * 0.10 - SW_N * 0.035
            d = (SW_UP * 0.6 + SW_N * 0.2 + Vector((0, -sy * 0.3, 0))).normalized()
            n = Vector((0.7, -sy * 0.5, -0.2)).normalized()
            p.H.key_hand(s, f, W, d, n, pole=W + Vector((-0.3, sy * 0.5, -0.5)))
        if f == frames[0]:
            for s in "LR": apply_pose(p.o, s, "wrap_grip", f)
wheel_hands(DR, DR.frames, 0.26)
wheel_hands(DR2, [f for f in DR2.frames if f < F_BOOM + 2] + [F_BOOM + 2], 0.26)
for f in [f for f in DR2.frames if f > F_BOOM + 2]:
    for s in "LR": DR2.arm_chest(s, f, k=0.7) if f < F_BOOM + 60 else DR2.arm_lap(s, f)

# ---- standing people
def stand(p, f0, f1, pos, yaw, step=10, seed=0, head=None, flex=0.0, arms=None, feet=True):
    """idle standing: weight shift + breathing, head look function, arm plan function arms(f, s) -> kind"""
    pos = Vector(pos)
    if feet: p.key_feet_stand(f0, pos, yaw); p.key_feet_stand(f1, pos, yaw)
    fs = sorted(set(list(range(f0, f1 + 1, step)) + [f1]))
    for f in fs:
        b = math.sin((f + seed * 17) / 44.0 * 2 * math.pi); w = math.sin((f + seed * 29) / 150.0 * 2 * math.pi)
        hd = head(f) if head else (0.0, 0.0)
        fl = flex(f) if callable(flex) else flex
        p.key_body(f, pos + yawM(yaw) @ Vector((0.012 * w, 0, 0)), yaw=yaw, flex=fl * 0.4, side=1.5 * w, spine=(fl + 1.0 * b, 0, -1.0 * w), head=hd)
        for s in "LR":
            kind = arms(f, s) if arms else "relaxed"
            if kind == "relaxed": p.arm_relaxed(s, f, swing=0.01 * b)
            elif kind == "wave": p.arm_wave(s, f, phase=(f + seed * 5) / 8.0)
            elif kind == "chest": p.arm_chest(s, f)
            elif kind == "lapel": p.arm_chest(s, f, k=0.45)
    return fs
def walk(p, pts, f0, f1, arms_kind="relaxed", step=2, stride=0.68):
    pts = [Vector(q) for q in pts]
    L = [0.0]
    for a_, b_ in zip(pts, pts[1:]): L.append(L[-1] + (b_ - a_).length)
    def path(f):
        u = smooth((f - f0) / (f1 - f0)) * L[-1]
        for i in range(len(pts) - 1):
            if u <= L[i + 1] or i == len(pts) - 2:
                t = (u - L[i]) / max(1e-6, L[i + 1] - L[i]); return pts[i].lerp(pts[i + 1], min(1, t))
    def yawf(f):
        a_ = path(max(f0, f - 3)); b_ = path(min(f1, f + 3)); d = (b_ - a_)
        if d.length < 1e-4: d = pts[-1] - pts[0]
        return math.degrees(math.atan2(d.x, -d.y))
    p.H.walk(path, yawf, f0, f1, stride=stride, step=step)
    for f in range(f0, f1 + 1, 4):
        q = path(f); p.pos[f] = Vector((q.x, q.y, ground_z(q.x, q.y))); p.yaw[f] = yawf(f)
        ph = math.sin(2 * math.pi * ((f - f0) / 40.0))
        for s, sg in (("L", 1), ("R", -1)):
            if arms_kind == "relaxed": p.arm_relaxed(s, f, swing=0.06 * ph * sg)
    return path, yawf
def faceyaw(frm, to):
    d = Vector(to) - Vector(frm); return math.degrees(math.atan2(d.x, -d.y))
def gz(x, y): return ground_z(x, y)

# ---- the gunman: B1 he has stepped to the kerb and fires as the car turns; the rewind takes him back to the cafe awning;
# B8 he steps out again; B9 fires twice from 2.5 m. The pistol is in his right hand the whole film (bone-parented, posed grip).
GP = P["Gunman"]
G_WAIT = Vector((5.45, 10.7, PAVE_Z)); G_KERB = Vector((4.35, 9.9, 0.0))
def ar_head_world(f):
    M = car_M(s1(f)); return M @ Vector((-1.17, -0.33, CAR1["seat_rear_z"] + 0.80))
aim_frames_1 = list(range(1, 342, 5))
yaw_kerb = lambda f: faceyaw(G_KERB, ar_head_world(f))
GP.key_feet_stand(1, G_KERB, yaw_kerb(60))
for f in aim_frames_1:
    yw = yaw_kerb(f); tgt = ar_head_world(f)
    b = math.sin(f / 44.0 * 2 * math.pi)
    GP.key_body(f, G_KERB, yaw=yw, spine=(2 + 0.8 * b, 0, 0), head=(2, -4))
    raise_ = smooth((f - 1) / 30.0)
    if raise_ < 0.999 and f < 32:
        GP.arm_relaxed("R", f) if f == 1 else GP.arm_aim("R", f, tgt + Vector((0, 0, -1.2 * (1 - raise_))))
    else:
        GP.arm_aim("R", f, tgt)
    GP.arm_relaxed("L", f, swing=0.01 * b)
GP.key_feet_stand(341, G_KERB, yaw_kerb(330))
# rewind (B3): arm lowers, two steps back to the awning (played backwards in time)
GP.key_body(352, G_KERB, yaw=yaw_kerb(341), spine=(2, 0, 0)); GP.arm_relaxed("R", 372); GP.arm_relaxed("L", 372)
GP.key_body(372, G_KERB, yaw=yaw_kerb(341), spine=(2, 0, 0))
walk(GP, [G_KERB, G_WAIT], 380, 430, step=2)
yaw_wait = -70.0
stand(GP, 432, 1120, G_WAIT, yaw_wait, seed=5, head=lambda f: (0, 0) if f < 1000 else (0, -15 if f < 1060 else -25))
# B8: steps out (two strides) toward the stalled car
walk(GP, [G_WAIT, G_KERB], 1122, 1180, step=2)
ar_stall = car_M(s1(1200)) @ Vector((-1.17, -0.33, CAR1["seat_rear_z"] + 0.80))
yk = faceyaw(G_KERB, ar_stall)
GP.key_feet_stand(1182, G_KERB, yk)
for f in range(1184, END + 1, 4):
    b = math.sin(f / 44.0 * 2 * math.pi)
    GP.key_body(f, G_KERB, yaw=yk, spine=(2 + 0.8 * b, 0, 0), head=(1, -3))
    if f < 1244: GP.arm_relaxed("R", f)
    elif f < 1272:
        u = smooth((f - 1244) / 28.0); GP.arm_aim("R", f, ar_stall + Vector((0, 0, -1.3 * (1 - u))))
    elif f < 1326: GP.arm_aim("R", f, ar_stall + Vector((0, 0, 0.06 if f in (1292, 1320) else 0.0)))
    elif f < 1352:
        u = smooth((f - 1326) / 26.0); GP.arm_aim("R", f, ar_stall + Vector((0, 0, -1.3 * u)))
    else: GP.arm_relaxed("R", f)      # v009: arm down before the camera rises (no lone arm at the frame edge)
    GP.arm_relaxed("L", f, swing=0.01 * b)
apply_pose(GP.o, "R", "wrap_grip", 1); apply_pose(GP.o, "L", "relaxed", 1)
FLASH_FRAMES = [38, 1290, 1318]
for f in FLASH_FRAMES:            # recoil: the wrist kicks up 5 cm for 3 frames
    pass

# ---- the bomber (B5): holds the bomb low in his right hand, winds up, throws at the passing car (release 705)
BO = P["Bomber"]; B_POS = Vector((-32.5, 4.85, PAVE_Z)); b_yaw = -32.0
def bomber_arm(f, s):
    return "relaxed"
stand(BO, 1, 640, B_POS, b_yaw, seed=7, head=lambda f: (0, 0) if f < 560 else (0, -25))
BO.key_feet_stand(641, B_POS, b_yaw, fwd=(0.12, -0.08))
S = BO.sh["R"]
throw = [(641, (S.x - 0.12, S.y - 0.30, S.z - 0.30), 0), (680, (S.x - 0.12, S.y - 0.32, S.z - 0.22), 2), (692, (S.x - 0.30, S.y + 0.22, S.z + 0.12), -8),
         (F_REL, (S.x - 0.18, S.y - 0.50, S.z + 0.12), 14), (F_REL + 10, (S.x + 0.02, S.y - 0.45, S.z - 0.28), 18), (740, (S.x - 0.05, S.y - 0.30, S.z - 0.40), 6),
         (800, (S.x - 0.08, S.y - 0.10, S.z - 0.50), 0)]
for f, W, lean in throw:
    BO.key_body(f, B_POS, yaw=b_yaw, spine=(lean, -lean * 0.8, 0), head=(-4 if f >= 680 else 0, -28))
    d = (Vector((0, -1, 0.3)) if f >= F_REL else Vector((0, -0.4, 1))).normalized()
    BO.key_hand_local("R", f, W, d, (0.6, 0.0, 0.8) if f < 692 else (0.0, -0.3, 1.0), elbow_local=(S.x - 0.45, S.y + 0.20, S.z - 0.35))
    BO.arm_relaxed("L", f, out=0.04)
apply_pose(BO.o, "R", "cup_hold", 641); apply_pose(BO.o, "R", "cup_hold", F_REL - 1); apply_pose(BO.o, "R", "relaxed", F_REL + 6)
stand(BO, 810, END, B_POS, b_yaw, seed=7, step=12, head=lambda f: (0, 35), feet=False)

# ---- the two who lose their nerve (B4): watch the car come, one's hand goes to his coat front, both look down and walk away
N1, N2 = P["Nerve1"], P["Nerve2"]
N1P = Vector((-41.0, 5.0, PAVE_Z)); N2P = Vector((-39.8, 5.45, PAVE_Z))
stand(N1, 1, 586, N1P, -8, seed=11, head=lambda f: (0, 0) if f < 485 else ((0, -35) if f < 545 else (18, -10)),
      arms=lambda f, s: "lapel" if (s == "R" and 505 <= f <= 575) else "relaxed")
stand(N2, 1, 592, N2P, 10, seed=12, head=lambda f: (0, 0) if f < 490 else ((0, -40) if f < 552 else (15, 10)))
walk(N1, [N1P, Vector((-42.2, 6.0, PAVE_Z)), Vector((-45.8, 6.3, PAVE_Z))], 590, 700)
walk(N2, [N2P, Vector((-40.6, 6.7, PAVE_Z)), Vector((-43.8, 7.0, PAVE_Z))], 596, 704)
stand(N1, 706, END, Vector((-45.8, 6.3, PAVE_Z)), 120, seed=13)
stand(N2, 710, END, Vector((-43.8, 7.0, PAVE_Z)), 150, seed=14)

for nm_, ro_ in (("Q6", 0.08), ("Q2", 0.04), ("Q4", 0.04), ("C2", 0.04)): P[nm_].relax_out = ro_   # v009: hands off the hips (clip_scan / limb_check)
# ---- quay crowd: watch, wave as the car passes (B4-B5), recoil from the blast (B6)
QS = {"Q1": ((-36.4, 5.55), 8, "R"), "Q2": ((-34.5, 6.25), -10, None), "Q3": ((-30.0, 5.45), 12, "L"), "Q4": ((-28.3, 6.35), -6, None),
      "Q5": ((-46.6, 5.0), 15, "L"), "Q6": ((-38.2, 6.65), 5, None)}   # v009: Q6 no wave (hand through own head, clip_scan)
for i, (nm, ((x, y), yw, wav)) in enumerate(QS.items()):
    p = P[nm]; pos = Vector((x, y, PAVE_Z))
    def head(f, x=x):
        cx = route(s1(f))[0].x
        look = max(-60, min(60, (cx - x) * -6.0))
        if F_BOOM + 2 <= f <= F_BOOM + 70 and abs(x - SITE.x) < 9: return (-6, 40 if x > SITE.x else -40)
        return (0, look)
    def arms(f, s, wav=wav, x=x):
        if F_BOOM + 2 <= f <= F_BOOM + 60 and abs(x - SITE.x) < 9: return "chest"
        if wav and s == wav and 470 <= f <= 760 and abs(route(s1(f))[0].x - x) < 10: return "wave"
        return "relaxed"
    stand(p, 1, END, pos, yw, seed=20 + i, head=head, arms=arms, flex=(lambda f, x=x: -8.0 if (F_BOOM + 2 <= f <= F_BOOM + 50 and abs(x - SITE.x) < 9) else 0.0))
    for s in "LR": apply_pose(p.o, s, "relaxed", 1)
# ---- corner crowd (cafe): watch, then step toward the car after the shots (B9)
CS = {"C1": ((6.3, 14.6), -95), "C2": ((12.0, 5.3), 15), "C3": ((-6.3, 10.6), 95)}
for i, (nm, ((x, y), yw)) in enumerate(CS.items()):
    p = P[nm]; pos = Vector((x, y, gz(x, y)))
    stand(p, 1, 1338, pos, yw, seed=40 + i, head=lambda f: (0, 0) if f < 1288 else (-4, 15),
          arms=lambda f, s: "chest" if (1292 <= f <= 1338 and s == "R") else "relaxed")
    for s in "LR": apply_pose(p.o, s, "relaxed", 1)
walk(P["C1"], [Vector((6.3, 14.6, PAVE_Z)), Vector((5.0, 13.9, 0)), Vector((3.7, 13.2, 0))], 1340, 1420)
walk(P["C3"], [Vector((-6.3, 10.6, PAVE_Z)), Vector((-4.6, 10.9, 0)), Vector((-1.2, 11.2, 0))], 1344, 1424)
stand(P["C1"], 1424, END, Vector((3.7, 13.2, 0)), -100, seed=50, feet=True)
stand(P["C3"], 1428, END, Vector((-1.2, 11.2, 0)), 95, seed=51, feet=True)
stand(P["C2"], 1340, END, Vector((12.0, 5.3, PAVE_Z)), 30, seed=52, feet=False, arms=lambda f, s: "chest" if s == "R" and f < 1400 else "relaxed")
# ---- faces: both-eye blinks for everyone, light smiles while the crowd greets the car, eyes closed after the shots
sc.frame_set(1)
rngf = random.Random(5)
for nm, p in P.items():
    fr = []; f = rngf.randint(20, 90)
    while f < END - 20:
        fr.append(f); f += rngf.randint(110, 200)
    if nm in ("Archduke", "Duchess"): fr = [x for x in fr if x < 1290]
    blinks(p.o, fr)
for nm, keys in (("Duchess", [(1, 0.3), (90, 0.0), (480, 0.0), (520, 0.55), (700, 0.5), (735, 0.0)]),
                 ("Archduke", [(1, 0.2), (90, 0.0), (520, 0.0), (560, 0.35), (700, 0.3), (735, 0.0)]),
                 ("Q1", [(1, 0.2), (480, 0.6), (760, 0.5), (800, 0.0)]), ("Q3", [(1, 0.2), (480, 0.5), (760, 0.4), (800, 0.0)]),
                 ("Q5", [(1, 0.3), (480, 0.5), (760, 0.5), (800, 0.0)]), ("C1", [(1, 0.2), (1280, 0.2), (1292, 0.0)])):
    for f, sm in keys: key_face(P[nm].o, f, smile=sm, brow=0.3 if sm > 0.3 else 0.0)
for nm, f0 in (("Archduke", 1300), ("Duchess", 1330)):
    eyes_closed(P[nm].o, f0, END + 40)
key_face(P["Gunman"].o, 1, brow=-0.6, squint=0.4); key_face(P["Bomber"].o, 1, brow=-0.5, squint=0.3)
log("ACTING keyed")

# ================================================================== PROPS IN HANDS
sc.frame_set(150); bpy.context.view_layer.update()
def palm_frame(rig, s="R"):
    PB = rig.pose.bones; Mw = rig.matrix_world
    wr = Mw @ PB["wrist." + s].head; f3 = Mw @ PB["finger3-1." + s].head; f2 = Mw @ PB["finger2-1." + s].head; f5 = Mw @ PB["finger5-1." + s].head
    d = (f3 - wr).normalized(); aa = (f5 - f2).normalized(); n = d.cross(aa).normalized() if s == "R" else aa.cross(d).normalized()
    return wr, d, aa, n, wr.lerp(f3, 0.55)
GUN = O["Pistol"]
wr, d, aa, n, palm = palm_frame(GP.o)
X = -d; Z = -(aa - d * aa.dot(d)).normalized(); Y = Z.cross(X)
M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = palm + n * 0.028
GUN.parent = GP.o; GUN.parent_type = 'BONE'; GUN.parent_bone = "wrist.R"
bpy.context.view_layer.update(); GUN.matrix_world = M
log("GUN parented; palm normal", tuple(round(c, 2) for c in n))
# bomb: baked into the bomber's palm until release, then a single ballistic arc -> hood -> cobbles -> roll -> blast
BOMB = O["Bomb"]; BOMB.rotation_mode = 'XYZ'
for f in range(1, F_REL + 1):
    if f < 630 and f % 10: continue
    sc.frame_set(f); wr, d, aa, n, palm = palm_frame(BO.o)
    BOMB.location = palm + n * 0.075 + d * 0.01
    BOMB.keyframe_insert("location", frame=f)
P_REL = BOMB.location.copy()
def arc(a, b, h, u): return a.lerp(b, u) + Vector((0, 0, h * 4 * u * (1 - u)))
for f in range(F_REL + 1, F_BOOM + 1):
    if f <= F_HIT: q = arc(P_REL, P_HIT, 0.9, (f - F_REL) / (F_HIT - F_REL))
    elif f <= F_LAND: q = arc(P_HIT, P_LAND, 0.55, (f - F_HIT) / (F_LAND - F_HIT))
    elif f <= F_STOP:
        u = (f - F_LAND) / (F_STOP - F_LAND); q = P_LAND.lerp(SITE, 1 - (1 - u) ** 2)
    else: q = SITE
    BOMB.location = q; BOMB.rotation_euler = (0, -(f - F_REL) * 0.35, 0.2)
    BOMB.keyframe_insert("location", frame=f); BOMB.keyframe_insert("rotation_euler", frame=f)
BOMB.scale = (1.45, 1.45, 1.2); BOMB.keyframe_insert("scale", frame=1); BOMB.keyframe_insert("scale", frame=F_BOOM + 1)
BOMB.scale = (0, 0, 0); BOMB.keyframe_insert("scale", frame=F_BOOM + 2)
for fc in BOMB.animation_data.action.fcurves if hasattr(BOMB.animation_data.action, "fcurves") else []:
    pass
key_vis([BOMB, BOMB.children[0]] if BOMB.children else [BOMB], F_BOOM + 2, False)
key_vis([BOMB] + list(BOMB.children), 1, True)

# ================================================================== FX: muzzle flashes, the blast
fx = bpy.data.collections.new("FX"); sc.collection.children.link(fx)
def emis(name, col, strength):
    m = mat(name, col, emit=(col, strength)); return m
flash_m = emis("M_MuzzleFlash", (1.0, 0.75, 0.35), 25.0)
for i, f in enumerate(FLASH_FRAMES):
    mz = Vector(GUN["muzzle"])
    bm = bmesh.new()
    for k in range(7):        # a star of tapered spikes along the barrel + a bright core
        ang = 2 * math.pi * k / 7
        dirv = Vector((-1.0, 0.45 * math.cos(ang), 0.45 * math.sin(ang))).normalized()
        r = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.0, depth=0.12,
                                  matrix=Matrix.Translation(mz + dirv * 0.06) @ dirv.to_track_quat('Z', 'Y').to_matrix().to_4x4())
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.025, matrix=Matrix.Translation(mz + Vector((-0.02, 0, 0))))
    me = bpy.data.meshes.new("MuzzleFlash%d" % i); bm.to_mesh(me); bm.free()
    fo = bpy.data.objects.new("MuzzleFlash%d" % i, me); fx.objects.link(fo); me.materials.append(flash_m)
    fo.parent = GUN
    lt = bpy.data.objects.new("MuzzleLight%d" % i, bpy.data.lights.new("MuzzleLight%d" % i, 'POINT')); fx.objects.link(lt)
    lt.parent = GUN; lt.location = mz + Vector((-0.08, 0, 0)); lt.data.color = (1.0, 0.7, 0.35); lt.data.shadow_soft_size = 0.05
    for ff, sc_, en in ((f - 1, 0.0, 0.0), (f, 1.0, 60.0), (f + 1, 0.8, 30.0), (f + 2, 0.0, 0.0)):
        fo.scale = (sc_ + 1e-4,) * 3; fo.keyframe_insert("scale", frame=ff)
        lt.data.energy = en; lt.data.keyframe_insert("energy", frame=ff)
    key_vis([fo], 1, False); key_vis([fo], f, True); key_vis([fo], f + 2, False)
def soften(m, edge=0.85):
    """soft, volumetric-looking edges for puffs: mix toward transparent at grazing angles (fresnel)"""
    nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N["Material Output"]; pr = N["Principled BSDF"]
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.45
    mr = N.new("ShaderNodeMath"); mr.operation = 'MULTIPLY'; mr.inputs[1].default_value = edge
    L.new(lw.outputs["Facing"], mr.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(mr.outputs[0], mx.inputs[0]); L.new(pr.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
# blast under car 2: flash core, fireball, rolling smoke, cobble debris, a light; no bodies, no gore
fire_m = bpy.data.materials.new("M_Fireball"); fire_m.use_nodes = True; nt = fire_m.node_tree; N = nt.nodes; L_ = nt.links
pr = N["Principled BSDF"]; nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.25, 0.03, 0.0, 1); cr.color_ramp.elements[1].color = (1.0, 0.62, 0.10, 1); cr.color_ramp.elements[0].position = 0.35
L_.new(nz.outputs["Fac"], cr.inputs["Fac"]); L_.new(cr.outputs["Color"], pr.inputs["Emission Color"]); L_.new(cr.outputs["Color"], pr.inputs["Base Color"])
pr.inputs["Emission Strength"].default_value = 14.0; nz.inputs["Scale"].default_value = 7.0; nz.inputs["Detail"].default_value = 10
cr.color_ramp.elements[0].position = 0.45; cr.color_ramp.elements[1].position = 0.62
soften(fire_m, 0.95)
smoke_m = bpy.data.materials.new("M_Smoke"); smoke_m.use_nodes = True; nt = smoke_m.node_tree; N = nt.nodes; L_ = nt.links
pr = N["Principled BSDF"]; nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 5
cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.10, 0.08, 0.07, 1); cr.color_ramp.elements[1].color = (0.38, 0.32, 0.27, 1)
L_.new(nz.outputs["Fac"], cr.inputs["Fac"]); L_.new(cr.outputs["Color"], pr.inputs["Base Color"]); pr.inputs["Roughness"].default_value = 1.0
pr.inputs["Sheen Weight"].default_value = 0.5
soften(smoke_m, 0.9)
def puff(name, r, m, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=(0, 0, -60))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m)
    for c in list(o.users_collection): c.objects.unlink(o)
    fx.objects.link(o)
    tex = bpy.data.textures.new(name + "_n", 'CLOUDS'); tex.noise_scale = r * 0.6; tex.noise_depth = 2
    dp = o.modifiers.new("billow", 'DISPLACE'); dp.texture = tex; dp.strength = r * 0.35; dp.texture_coords = 'LOCAL'
    smo = o.modifiers.new("soft", 'SMOOTH'); smo.factor = 0.8; smo.iterations = 3
    bpy.ops.object.shade_smooth()
    return o
for j, (off, k, dl) in enumerate(((Vector((0, 0, 0)), 1.0, 0), (Vector((0.7, 0.3, 0.3)), 0.7, 2), (Vector((-0.8, -0.2, 0.2)), 0.65, 3),
                                   (Vector((0.2, -0.6, 0.6)), 0.6, 4), (Vector((-0.3, 0.6, 0.9)), 0.55, 5), (Vector((1.0, -0.3, 0.1)), 0.45, 1),
                                   (Vector((-1.1, 0.4, 0.5)), 0.5, 2), (Vector((0.4, 0.9, 1.2)), 0.4, 6), (Vector((-0.2, -0.9, 1.0)), 0.45, 4))):
    FB = puff("Fireball%d" % j, 0.8, fire_m, j)
    FB.modifiers["billow"].strength = 0.55
    for f, s_, z in ((F_BOOM + dl, 0.05, 0.3), (F_BOOM + dl + 4, 0.8, 0.8), (F_BOOM + dl + 10, 1.25, 1.3), (F_BOOM + dl + 18, 1.3, 1.9), (F_BOOM + dl + 28, 0.7, 2.5), (F_BOOM + dl + 36, 0.02, 2.8)):
        FB.location = SITE + off * (0.5 + s_) + Vector((0, 0, z)); FB.scale = (s_ * k * 1.1, s_ * k, s_ * k * 0.9)
        FB.rotation_euler = (0, 0, f * 0.05)
        FB.keyframe_insert("location", frame=f); FB.keyframe_insert("scale", frame=f); FB.keyframe_insert("rotation_euler", frame=f)
    key_vis([FB], 1, False); key_vis([FB], F_BOOM + dl, True); key_vis([FB], F_BOOM + dl + 37, False)
boom_l = bpy.data.objects.new("BlastLight", bpy.data.lights.new("BlastLight", 'POINT')); fx.objects.link(boom_l)
boom_l.location = SITE + Vector((0, 0, 1.2)); boom_l.data.color = (1.0, 0.55, 0.2); boom_l.data.shadow_soft_size = 0.8
for f, e in ((F_BOOM - 1, 0), (F_BOOM + 1, 9000), (F_BOOM + 8, 6000), (F_BOOM + 20, 1500), (F_BOOM + 36, 0)):
    boom_l.data.energy = e; boom_l.data.keyframe_insert("energy", frame=f)
rng = random.Random(8)
for i in range(14):
    sm = puff("Smoke%d" % i, 0.6, smoke_m, i)
    off = Vector((rng.uniform(-1.2, 1.6), rng.uniform(-0.4, 1.2), 0))
    f0 = F_BOOM + 6 + i * 2
    for f, s_, z in ((f0, 0.05, 0.6), (f0 + 20, 0.9, 1.6), (f0 + 60, 1.3, 3.2), (f0 + 140, 1.2, 5.0), (f0 + 220, 0.01, 6.0)):
        sm.location = SITE + off * (1 + (f - f0) / 80.0) + Vector((0.3 * (f - f0) / 100.0, 0, z)); sm.scale = (s_,) * 3
        sm.rotation_euler = (0, 0, (f - f0) * 0.01)
        sm.keyframe_insert("location", frame=f); sm.keyframe_insert("scale", frame=f); sm.keyframe_insert("rotation_euler", frame=f)
    key_vis([sm], 1, False); key_vis([sm], f0, True); key_vis([sm], f0 + 221, False)
deb_m = mat("M_Debris", (0.35, 0.28, 0.22), rough=0.8)
for i in range(22):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rng.uniform(0.04, 0.09), location=(0, 0, -60))
    o = bpy.context.active_object; o.name = "Debris%d" % i; o.data.materials.append(deb_m); o.scale = (1, 0.8, 0.6)
    for c in list(o.users_collection): c.objects.unlink(o)
    fx.objects.link(o)
    v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized() * rng.uniform(2.0, 6.0)
    up = rng.uniform(4.0, 8.0); T = 2 * up / 9.81
    for k in range(0, 41, 2):
        t = min(T, k / 60.0); f = F_BOOM + k
        p_ = SITE + Vector((v.x * t, v.y * t, 0.1 + up * t - 4.9 * t * t))
        p_.z = max(0.05, p_.z)
        if abs(p_.y) > 3.9: p_.y = 3.9 * (1 if p_.y > 0 else -1)
        o.location = p_; o.rotation_euler = (k * 0.3, k * 0.2, 0); o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
    key_vis([o], 1, False); key_vis([o], F_BOOM, True)
log("FX done")

# ================================================================== THE CAMERA: one continuous move (no cuts), level horizon, no DOF blur
cam = bpy.data.objects.new("CAM_Film", bpy.data.cameras.new("CAM_Film")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'AUTO'; cam.data.clip_start = 0.05; cam.data.clip_end = 14000; cam.data.dof.use_dof = False
def CL(f, loc): return car_M(s1(f)) @ Vector(loc)
REAR = (-1.17, 0.0, 2.05)
ar_face = lambda f: CL(f, (-1.0, -0.33, 2.15)); du_face = lambda f: CL(f, (-1.0, 0.33, 2.12))
GPH = lambda p_: Vector((p_.x, p_.y, p_.z + 1.62))
KEYS = [  # frame, camera position, look-at point, lens
    (1, Vector((3.0, 8.15, 1.62)), GPH(G_KERB) + Vector((0, 0, -0.05)), 35),
    (40, Vector((3.1, 8.35, 1.7)), GPH(G_KERB) + Vector((-0.45, -0.4, 0.0)), 33),
    (45, Vector((3.0, 8.2, 1.78)), Vector((-1.0, 12.7, 1.8)), 31),     # v009: a whip through the street, not a target sweeping past the lens
    (50, Vector((2.9, 8.1, 1.85)), CL(50, REAR), 30),
    (68, Vector((2.5, 7.9, 2.0)), CL(68, REAR), 28),
    (95, CL(95, (3.4, -3.0, 2.4)), CL(95, REAR), 30),
    (150, CL(150, (2.6, -2.5, 2.25)), CL(150, REAR), 30),
    (230, CL(230, (2.7, -2.1, 2.2)), CL(230, (-1.1, 0, 2.1)), 34),
    (300, Vector((5.3, 7.0, 2.05)), CL(300, (-1.05, 0, 2.1)), 38),
    (341, Vector((5.5, 6.6, 2.1)), CL(341, (-1.05, 0, 2.1)), 38),
    (375, Vector((6.0, 2.5, 7.0)), CL(375, REAR), 28),
    (420, Vector((-10.0, -2.2, 6.0)), CL(420, REAR), 26),
    (462, Vector((-33.5, 2.2, 3.0)), Vector((-40.4, 5.3, 1.7)), 28),
    (480, Vector((-38.4, 2.85, 1.85)), Vector((-40.4, 5.25, 1.45)), 24),
    (530, Vector((-39.0, 3.05, 1.75)), Vector((-40.4, 5.25, 1.5)), 27),
    (575, Vector((-39.2, 2.6, 1.75)), Vector((-40.4, 5.4, 1.55)), 30),
    (600, Vector((-36.6, 2.7, 1.75)), Vector((-38.5, 5.6, 1.5)), 32),
    (640, Vector((-34.4, 3.4, 1.75)), Vector((-32.5, 4.9, 1.6)), 34),
    (690, Vector((-34.7, 3.2, 2.1)), Vector((-32.5, 4.9, 1.6)), 28),
    (706, Vector((-33.8, 3.8, 2.9)), Vector((-35.4, 1.6, 2.1)), 28),
    (722, Vector((-33.5, 3.9, 3.4)), P_HIT + Vector((0.6, 0.6, 0.1)), 28),
    (745, Vector((-36.0, 2.45, 2.45)), arc(P_HIT, P_LAND, 0.55, 10 / 25.0), 42),
    (760, Vector((-37.2, 2.25, 1.35)), P_LAND + Vector((0, 0, 0.05)), 42),
    (777, Vector((-39.5, 1.2, 4.5)), Vector((-43.5, 1.0, 1.3)), 26),
    (792, Vector((-45.0, -2.4, 3.0)), SITE + Vector((2.0, 0.8, 0.9)), 26),
    (860, Vector((-50.0, -5.6, 7.5)), SITE + Vector((3.5, 1.5, 1.6)), 26),
    (885, Vector((-41.0, -2.0, 11.0)), CL(885, REAR), 26),     # v009: above the cross bunting (6-8.5 m) and the lamp heads
    (910, CL(910, (-11.0, -1.0, 10.0)), CL(910, REAR), 26),
    (960, CL(960, (-6.5, -2.0, 10.0)), CL(960, REAR), 28),
    (1000, Vector((-8.0, -2.0, 12.0)), CL(1000, (0, 0, 1.0)), 28),
    (1040, Vector((-3.5, 0.5, 9.0)), CL(1040, (0, 0, 1.0)), 30),
    (1080, Vector((-2.4, 6.4, 7.5)), Vector((6.3, 12.6, 3.6)), 26),
    (1140, Vector((-1.6, 7.3, 4.6)), Vector((6.6, 12.2, 3.2)), 28),
    (1180, Vector((3.4, 6.6, 2.4)), GPH(G_KERB) + Vector((0, 0, 0.0)), 35),
    (1236, Vector((3.2, 8.25, 1.66)), GPH(G_KERB) + Vector((-0.06, -0.02, 0.0)), 45),
    (1244, Vector((4.9, 8.1, 1.8)), GPH(G_KERB) + Vector((-0.2, 0.0, 0.0)), 36),
    (1254, Vector((5.9, 9.7, 1.8)), GPH(G_KERB) + Vector((-0.3, 0.0, 0.0)), 32),
    (1272, Vector((4.7, 13.4, 1.85)), Vector((3.3, 9.8, 1.75)), 28),     # v009: side-on from the north: profile, arm and the gap to the car read
    (1290, Vector((4.6, 13.3, 1.85)), Vector((3.2, 9.7, 1.8)), 28),
    (1320, Vector((4.5, 13.1, 1.9)), Vector((3.1, 9.7, 1.8)), 30),
    (1345, Vector((4.5, 13.0, 2.0)), Vector((3.0, 9.7, 1.7)), 30),      # v009: hold the gunman in frame while the arm drops
    (1362, Vector((4.9, 12.6, 2.6)), Vector((2.6, 9.6, 1.6)), 30),
    (1378, Vector((5.0, 10.3, 3.2)), Vector((2.0, 9.8, 1.2)), 30),
    (1405, Vector((4.6, 9.2, 6.0)), ar_stall + Vector((0, 0.3, -1.2)), 30),
    (1432, Vector((1.6, 10.5 - 0.12 * 14.0, 14.0)), Vector((1.6, 10.5, 0.0)), 30),     # v009: meets the rise formula exactly (no 2.4 m jump at f1433)
]
def alt(f):
    """the rise to the map: exponential altitude from 14 m (f1432) to 1100 m (f1560) and 2500 m (END), so the blurry low-altitude
    view of the map is spent above the cloud layer"""
    if f <= 1560: return 14.0 * (1100.0 / 14.0) ** ((f - 1432) / (1560 - 1432))
    return 1100.0 + (2500.0 - 1100.0) * smooth((f - 1560) / (END - 1560)) ** 0.8
cp = {k: pchip([(f, p_[k]) for f, p_, t_, l_ in KEYS]) for k in range(3)}
tp = {k: pchip([(f, t_[k]) for f, p_, t_, l_ in KEYS]) for k in range(3)}
lp = pchip([(f, l_) for f, p_, t_, l_ in KEYS])
cam.rotation_mode = 'QUATERNION'; prev = None
MAP_T = Vector((-150.0, 520.0, 0.0))
for f in range(1, END + 1):
    if f <= 1432:
        loc = Vector((cp[0](f), cp[1](f), cp[2](f))); tgt = Vector((tp[0](f), tp[1](f), tp[2](f))); lens = lp(f)
    else:
        u = smooth((f - 1432) / (END - 1432)); h = alt(f)
        tgt = Vector((1.6, 10.5, 0.0)).lerp(MAP_T, smooth((f - 1470) / (END - 1470)) ** 1.3)
        loc = tgt + Vector((0.0, -0.12 * h, h))
        lens = 30.0
    q = (tgt - loc).to_track_quat('-Z', 'Y')
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    cam.location = loc; cam.rotation_quaternion = q; cam.data.lens = lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cam.data.keyframe_insert("lens", frame=f)
log("CAMERA keyed")

# ================================================================== colour keys: rewind tint (B3), muzzle/blast exposure blips
vs = sc.view_settings
try:
    vs.use_white_balance = True
    for f, t in ((1, 6500.0), (345, 6500.0), (360, 4300.0), (455, 4300.0), (472, 6500.0)):
        vs.white_balance_temperature = t; vs.keyframe_insert("white_balance_temperature", frame=f)
except Exception as e:
    log("no white balance", e)
for f, e in ((1, 0.0), (344, 0.0), (352, 0.25), (462, 0.25), (474, 0.0)):
    vs.exposure = e; vs.keyframe_insert("exposure", frame=f)

# ================================================================== VO, output, quaternion continuity
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
strip = sc.sequence_editor.strips.new_sound("VO", VO, 1, 1) if hasattr(sc.sequence_editor, "strips") else sc.sequence_editor.sequences.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/WW1Assassination_v009_####.png"
sc.render.image_settings.file_format = 'PNG'
sc["beats"] = [1, 152, 342, 473, 631, 777, 911, 1057, 1237, 1433, 1591]
sc["bomb"] = {"rel": F_REL, "hit": F_HIT, "boom": F_BOOM}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
log("ANIM_DONE", OUT)
