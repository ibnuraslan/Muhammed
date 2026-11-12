"""RingBullet animation: rigs, owner acting, robber, bullet/fragments, ring, FX, police lights, camera.
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
exec(open(os.path.join(ROOT, "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
SOLE = 0.017   # MPFB shoe sole sits below the ankle-derived ground height
def ground_z(x, y): return SOLE
sc = bpy.context.scene
random.seed(7)
O = bpy.data.objects
def F(t): return 1 + round(t * 60)          # seconds -> frame
BEATS = [(1, 0.0, "The robber fired the gun straight at his head"), (2, 2.7, "threw his hands up to cover his face"),
         (3, 6.8, "instead of going through his skull"), (4, 9.0, "the bullet hit his wedding ring"),
         (5, 11.0, "glanced off the metal and split into two pieces"), (6, 14.4, "One piece lodged in his finger"),
         (7, 16.3, "the other went into his neck"), (8, 17.9, "minor injuries and a dented ring"), (9, 20.8, "walked away okay")]

def lerp(a, b, t): return a + (b - a) * t
def keyv(o, path, f, v, idx=-1):
    setattr(o, path, v) if idx < 0 else getattr(o, path).__setitem__(idx, v)
    o.keyframe_insert(path, frame=f, index=idx)
def hide_key(o, f, hidden):
    o.hide_render = hidden; o.keyframe_insert("hide_render", frame=f)
def const_interp(o):
    ad = o.animation_data
    if not ad or not ad.action: return
    for fc in fcurves_of(ad.action):
        if fc.data_path in ("hide_render", "hide_viewport"):
            for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
def fcurves_of(act):
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    if not out and hasattr(act, "fcurves"): out = list(act.fcurves)
    return out

# =============================================================== rigs
OW = O["Owner"]; RB = O["Robber"]
ROW = make_human_ctrl(OW); HO = Human(ROW)
RRB = make_human_ctrl(RB); HR = Human(RRB)
bpy.ops.object.mode_set(mode='OBJECT')

RING_SPLAY = {3: 9.0, 5: -10.0}   # keep middle finger and pinky off the wedding band
def key_fingers(R, s, f, curl=0.0, spread=0.0, thumb=0.0, per=None):
    """curl in degrees (+ bends toward palm), spread in degrees (fan out)"""
    for i in range(1, 6):
        c = max(4.0, per[i - 1] if per else curl)   # relaxed curl, never bent backwards
        for j in (1, 2, 3):
            n = "finger%d-%d.%s" % (i, j, s)
            if n not in R.PB: continue
            pb = R.PB[n]; pb.rotation_mode = 'QUATERNION'
            ang = c * (1.0 if j == 1 else 1.1) if i > 1 else thumb * (0.6 if j == 1 else 1.0)
            sp = (spread * (i - 3) / 2.0) if (j == 1 and i > 1) else 0.0
            if s == "L" and j == 1 and R is ROW: sp += RING_SPLAY.get(i, 0.0)
            sp = max(-10.0, min(10.0, sp)); ang = ang if i > 1 else max(-15.0, min(45.0, ang))
            q = Euler((math.radians(ang), 0, math.radians(sp * (1 if s == "L" else -1))), 'XYZ').to_quaternion()
            pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

# ---------------- owner: standing behind the desk at origin, facing -Y
P0 = Vector((0.0, 0.0, 0.0))
def o_root(f, dz=0.0, back=0.0, yaw=0.0, side=0.0, pos=None):
    p = (pos if pos is not None else P0) + Vector((0, back, HO.root_head.z + dz + SOLE))
    HO.key_root(f, p, yaw=yaw, flex=0.0, side=side)
def o_feet(f, pos=None, yaw=0.0):
    for s in "LR":
        HO.key_foot(s, f, HO.foot_xy(s, pos if pos is not None else P0, yaw), yaw)

# hand target helper: W = wrist world pos, fingers-up direction d, palm normal n (world; tuned below)
def o_hand(s, f, W, d, n, pole):
    HO.key_hand(s, f, Vector(W), Vector(d), Vector(n), pole=Vector(pole))

PALM_SIGN = {"L": 1.0, "R": 1.0}   # flipped after a numeric check if needed
def palm(s, v): return Vector(v) * PALM_SIGN[s]

# ---- timeline of the owner's acting (frames)
# rest-ish start: hands low in front, startled; flinch builds
FIRE = 30
o_feet(1)
for f, dz, back, side in ((1, -0.01, 0.0, 0), (20, -0.015, 0.01, 1), (FIRE, -0.02, 0.02, 0), (120, -0.035, 0.04, -1), (300, -0.05, 0.06, -2),
                          (541, -0.055, 0.065, -2), (556, -0.06, 0.085, -3), (700, -0.06, 0.08, -2), (890, -0.07, 0.07, 1), (930, -0.075, 0.06, 2),
                          (1000, -0.07, 0.07, -3), (1075, -0.05, 0.05, -1), (1150, -0.04, 0.04, 0), (1240, -0.03, 0.02, 0)):
    o_root(f, dz, back, side=side)
for f, flex, tw, sd, hd in ((1, 0, 0, 0, (-4, 0)), (FIRE, -4, 0, 0, (-8, 0)), (120, -8, -4, 0, (-5, 6)), (300, -10, -8, 2, (-6, 14)),
                            (541, -10, -8, 2, (-6, 16)), (556, -14, -10, 3, (-10, 20)), (700, -12, -8, 2, (-7, 16)),
                            (880, -10, -6, 0, (-4, 12)), (900, -2, 4, -4, (6, 4)), (960, -4, 2, -2, (2, 0)),
                            (990, -8, -6, 4, (-6, -18)), (1020, -6, -8, 6, (-4, -22)), (1075, 6, 0, 0, (18, -4)),
                            (1150, 8, 4, 0, (24, 6)), (1200, 6, -2, 0, (16, -8)), (1240, 2, 0, 0, (4, 0))):
    HO.key_spine(f, flex=flex, twist=tw, side=sd, head=hd)

# hands: (frame, L(W,d,n,pole), R(...)); world coords, owner faces -Y; his left hand is +X
def hands_low(f, jitter=0.0):
    o_hand("L", f, (0.22 + jitter, -0.22, 1.02), (0.05, -0.6, 0.8), palm("L", (0.3, -0.9, -0.3)), (0.5, 0.3, 0.9))
    o_hand("R", f, (-0.22 - jitter, -0.22, 1.02), (-0.05, -0.6, 0.8), palm("R", (-0.3, -0.9, -0.3)), (-0.5, 0.3, 0.9))
hands_low(1); hands_low(18, 0.015); hands_low(FIRE, 0.03)   # small startle before the shot
# the snap up (slow motion): f163 -> f390
def hands_up(f, k=1.0, jl=(0, 0, 0), rl=(0, 0, 0), right=True):
    o_hand("L", f, Vector((0.12, -0.29, 1.36)) + Vector(jl), (0.04, -0.1, 1.0), palm("L", (-0.15, 1.0, 0.0)), (0.45, -0.1, 1.1))
    if right: o_hand("R", f, Vector((-0.2, -0.28, 1.35)) + Vector(rl), (0.0, -0.1, 1.0), palm("R", (0.15, 1.0, 0.0)), (-0.45, -0.1, 1.1))
o_hand("L", 70, (0.27, -0.32, 1.12), (0.0, -0.7, 0.7), palm("L", (0.2, -1.0, 0.0)), (0.5, 0.2, 0.95))
o_hand("R", 70, (-0.25, -0.3, 1.12), (0.0, -0.7, 0.7), palm("R", (-0.2, -1.0, 0.0)), (-0.5, 0.2, 0.95))
o_hand("L", 200, (0.25, -0.44, 1.33), (-0.1, -0.3, 1.0), palm("L", (-0.3, 0.9, -0.2)), (0.5, 0.0, 1.0))
o_hand("R", 200, (-0.18, -0.32, 1.3), (0.1, -0.3, 1.0), palm("R", (0.3, 0.9, -0.2)), (-0.5, 0.0, 1.0))
hands_up(262); hands_up(400, jl=(0.0, 0.004, 0.003)); hands_up(541, jl=(0.0, 0.006, 0.004), rl=(-0.07, 0.0, 0))
# impact jolt (hand knocked back toward his face, then eases forward again in slow motion)
hands_up(550, jl=(0.015, 0.02, 0.02), rl=(-0.075, 0.0, 0)); hands_up(620, jl=(0.02, 0.025, 0.015), rl=(-0.075, 0.0, 0))
hands_up(760, jl=(0.015, 0.02, 0.01), rl=(-0.07, 0.0, 0)); hands_up(880, jl=(0.01, 0.015, 0.0), rl=(0, 0.01, 0))
# wince: left hand flinches away (finger hit) f890-930
# wince (v006): the hit hand jerks back and down to the chest, curling; the other hand comes up open beside it (no contact)
o_hand("L", 906, (0.2, -0.46, 1.25), (-0.15, -0.6, 0.75), palm("L", (-0.2, 0.8, 0.5)), (0.5, -0.05, 1.0))
o_hand("L", 936, (0.09, -0.3, 1.24), (-0.15, -0.15, 1.0), palm("L", (0.05, 1.0, 0.1)), (0.5, 0.0, 0.95))
o_hand("L", 975, (0.09, -0.3, 1.245), (-0.15, -0.15, 1.0), palm("L", (0.05, 1.0, 0.1)), (0.5, 0.0, 0.95))
o_hand("R", 906, (-0.14, -0.33, 1.36), (0.3, -0.2, 0.9), palm("R", (0.3, -0.9, 0.1)), (-0.45, -0.1, 1.05))
o_hand("R", 936, (-0.15, -0.42, 1.25), (0.1, -0.5, 0.85), palm("R", (0.6, -0.3, 0.2)), (-0.45, -0.2, 1.0))
o_hand("R", 975, (-0.15, -0.42, 1.26), (0.1, -0.5, 0.85), palm("R", (0.6, -0.3, 0.2)), (-0.45, -0.2, 1.0))
# right hand flies to the right side of his neck f990-1010, left hand stays up and drops a bit
o_hand("R", 990, (-0.27, -0.2, 1.46), (0.2, 0.6, 0.6), palm("R", (0.95, 0.0, -0.1)), (-0.55, -0.2, 1.0))
o_hand("R", 1030, (-0.208, -0.07, 1.442), (0.2, 0.8, 0.35), palm("R", (0.95, -0.1, -0.2)), (-0.55, -0.1, 1.0))
o_hand("R", 1004, (-0.205, -0.068, 1.437), (0.2, 0.8, 0.35), palm("R", (0.95, -0.1, -0.2)), (-0.5, -0.2, 1.0))
o_hand("R", 1046, (-0.21, -0.072, 1.448), (0.2, 0.8, 0.35), palm("R", (0.95, -0.1, -0.2)), (-0.55, -0.1, 1.0))
o_hand("R", 1060, (-0.207, -0.068, 1.44), (0.2, 0.8, 0.35), palm("R", (0.95, -0.1, -0.2)), (-0.5, -0.2, 1.0))
o_hand("L", 1004, (0.1, -0.3, 1.25), (-0.15, -0.15, 1.0), palm("L", (0.05, 1.0, 0.1)), (0.5, 0.0, 0.95))
# look at the ring: left hand lowered to chest in front, palm toward him, back of hand up so the ring faces camera
o_hand("L", 1075, (0.12, -0.32, 1.28), (-0.6, -0.4, 0.5), palm("L", (0.0, 0.6, 0.6)), (0.5, 0.0, 0.9))
o_hand("L", 1150, (0.10, -0.34, 1.27), (-0.6, -0.45, 0.45), palm("L", (0.0, 0.6, 0.6)), (0.5, 0.0, 0.9))
o_hand("L", 1235, (0.13, -0.33, 1.25), (-0.55, -0.45, 0.5), palm("L", (0.05, 0.6, 0.6)), (0.5, 0.0, 0.9))
o_hand("L", 1262, (0.33, -0.32, 1.1), (-0.4, -0.6, 0.4), palm("L", (0.1, 0.6, 0.7)), (0.5, 0.1, 0.9))
o_hand("R", 1072, (-0.3, -0.15, 1.44), (0.1, 0.4, 0.8), palm("R", (0.9, 0.0, -0.2)), (-0.55, -0.1, 1.0))
o_hand("R", 1083, (-0.31, -0.25, 1.35), (-0.15, -0.9, 0.2), palm("R", (-0.3, 0.1, -0.9)), (-0.55, 0.0, 1.0))   # fingers lead forward-out while the hand comes down
o_hand("R", 1095, (-0.29, -0.3, 1.26), (0.1, -0.3, -0.9), palm("R", (-0.6, -0.3, 0.0)), (-0.5, 0.1, 1.0))
o_hand("R", 1130, (-0.25, -0.1, 1.0), (0.0, -0.2, -1.0), palm("R", (-0.9, 0.0, 0.0)), (-0.5, 0.3, 1.0))
o_hand("R", 1240, (-0.25, -0.11, 0.99), (0.0, -0.25, -1.0), palm("R", (-0.9, 0.0, 0.0)), (-0.5, 0.3, 1.0))
# fingers
for s in "LR":
    key_fingers(ROW, s, 1, curl=25, spread=4, thumb=10); key_fingers(ROW, s, FIRE, curl=18, spread=8, thumb=5)
    key_fingers(ROW, s, 200, curl=5, spread=18, thumb=-5); key_fingers(ROW, s, 262, curl=6, spread=8, thumb=0)
    key_fingers(ROW, s, 541, curl=6, spread=8, thumb=0)
key_fingers(ROW, "L", 550, curl=4, spread=14, thumb=-5); key_fingers(ROW, "L", 700, curl=6, spread=8, thumb=0)
key_fingers(ROW, "L", 890, curl=6, spread=8, thumb=0); key_fingers(ROW, "L", 905, curl=14, spread=4, thumb=5)
key_fingers(ROW, "L", 1000, curl=18, spread=2, thumb=8); key_fingers(ROW, "R", 1080, curl=12, spread=4, thumb=12); key_fingers(ROW, "R", 936, curl=15, spread=6, thumb=10); key_fingers(ROW, "R", 975, curl=15, spread=6, thumb=10); key_fingers(ROW, "R", 1000, curl=18, spread=2, thumb=40); key_fingers(ROW, "R", 1110, curl=22, spread=2, thumb=10)
key_fingers(ROW, "L", 1075, curl=4, spread=10, thumb=0); key_fingers(ROW, "L", 1150, curl=2, spread=12, thumb=0)
key_fingers(ROW, "L", 1235, curl=20, spread=4, thumb=10); key_fingers(ROW, "R", 1240, curl=25, spread=2, thumb=10)

# ---------------- face: terror -> brace -> wince -> pain -> disbelief -> relief
def key_face(f, jaw=0.0, brow=0.0, wide=0.0, squint=0.0, grim=0.0):
    spec = {"jaw": (jaw, 0, 0)}
    for sd in ".L", ".R":
        spec["oculi01" + sd] = (-brow, 0, 0); spec["oculi02" + sd] = (-brow, 0, 0)
        spec["orbicularis03" + sd] = (wide, 0, 0); spec["orbicularis04" + sd] = (squint, 0, 0)
        spec["risorius02" + sd] = (0, 0, grim); spec["risorius03" + sd] = (0, 0, grim)
    for n, r in spec.items():
        pb = ROW.PB[n]; pb.rotation_quaternion = Euler([math.radians(v) for v in r], 'XYZ').to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
for f, jw, br, wd, sq, gr in ((1, 6, 14, 14, 0, 0), (FIRE, 8, 18, 18, 0, 0), (45, 13, 22, 12, 0, 6), (200, 12, 20, 6, 16, 12), (541, 12, 18, 2, 22, 14),
                              (560, 15, 10, 0, 30, 20), (700, 12, 14, 4, 22, 14), (890, 10, 14, 6, 18, 12), (905, 6, -8, 0, 34, 24),
                              (990, 5, -6, 0, 30, 20), (1004, 14, -4, 0, 32, 24), (1060, 8, 4, 4, 16, 12), (1100, 5, 18, 16, 0, 0),
                              (1160, 7, 22, 12, 0, 0), (1176, 7, 22, 4, 30, 0), (1186, 7, 22, 4, 30, 0), (1200, 7, 20, 10, 0, 0), (1230, 4, 12, 6, 0, 4), (1300, 2, 4, 2, 0, 6), (1410, 1, 2, 0, 0, 8)):
    key_face(f, jw, br, wd, sq, gr)

# eyes: look down at the ring during the disbelief beat, back up as he leaves
for f, pitch in ((1, 0), (45, 6), (560, 6), (880, 4), (1000, 0), (1075, 0), (1100, -14), (1230, -12), (1265, 0)):   # v006: eyes keep looking at the gun while the head tilts back (no white roll-up)
    for sd in ".L", ".R":
        pb = ROW.PB["eye" + sd]; pb.rotation_quaternion = Euler((math.radians(pitch), 0, 0), 'XYZ').to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=f, group="eye" + sd)

# ---------------- walk out f1249 -> 1410 toward the door
XR, DY0, DY1 = sc["door"]
DOORC = Vector((XR, (DY0 + DY1) / 2, 0))
WP = [(1249, Vector((0.0, 0.0, 0))), (1275, Vector((0.25, 0.08, 0))), (1330, Vector((1.2, 0.32, 0))), (1390, Vector((2.35, 0.53, 0))), (1440, Vector((3.2, 0.55, 0)))]
wpath = catmull(WP)
def wyaw(f):
    a = wpath(min(f + 6, 1440)); b = wpath(max(f - 6, 1249)); d = a - b
    if d.length < 1e-4: return 0.0
    yw = math.degrees(math.atan2(d.x, -d.y))  # -Y forward
    return yw * smooth((f - 1249) / 30.0)
HO.walk(lambda f: wpath(f), wyaw, 1252, 1410, stride=0.62, lift=0.07, lean=4.0, step=2)
# arms swing during the walk (IK hands relative to the root)
for f in range(1252, 1411, 6):
    p = wpath(f); yw = math.radians(wyaw(f)); Rz = Matrix.Rotation(yw, 3, 'Z')
    dist = (p - WP[0][1]).length; ph = math.sin(2 * math.pi * dist / 0.62 / 2 * 2)
    for s, sx in (("L", 1), ("R", -1)):
        if s == "L" and f < 1263: continue
        sw = ph * 0.12 * (1 if s == "L" else -1)
        loc = p + Rz @ Vector((0.29 * sx, -sw - 0.06, 0.94))
        if s == "L" and f < 1270: loc = p + Rz @ Vector((0.37 * sx, -0.22, 1.04))   # swing out around the hip while turning into the walk
        HO.key_hand(s, f, loc, Rz @ Vector((0.0, -0.1, -1.0)), Rz @ Vector((-0.9 * sx, 0.0, 0.0)), pole=p + Rz @ Vector((0.4 * sx, 0.4, 1.1)))
for s in "LR": key_fingers(ROW, s, 1260, curl=38, spread=0, thumb=20)

# ---------------- robber: behind the camera side, at (0.32,-2.45), facing +Y, right arm extended with the gun
RP = Vector((0.32, -2.45, 0))
def r_root(f, dz=0.0, back=0.0, side=0.0):
    HR.key_root(f, RP + Vector((0, -back, HR.root_head.z + dz + SOLE)), yaw=180.0, flex=0.0, side=side)
for s in "LR": HR.key_foot(s, 1, HR.foot_xy(s, RP + Vector((0, 0, 0)), 180.0) + (Vector((0.0, 0.12)) if s == "L" else Vector((0, -0.1))), 180.0)
r_root(1, -0.03); r_root(FIRE, -0.035); r_root(FIRE + 6, -0.04, 0.02); r_root(160, -0.035, 0.01)
HR.key_spine(1, flex=4, twist=-12, head=(2, -6)); HR.key_spine(FIRE + 6, flex=2, twist=-12, head=(0, -6)); HR.key_spine(160, flex=4, twist=-12, head=(2, -6))
HEAD_T = Vector((0.0, -0.08, 1.64))
def r_arm(f, kick=0.0, drop=0.0):
    sh = Vector((0.32 + 0.17, -2.43, 1.42))
    d = (HEAD_T - sh).normalized()
    W = sh + d * 0.56 + Vector((0, 0, kick * 0.03 - drop))
    up = Vector((0, 0, 1)) + d * (-kick * 0.5)
    HR.key_hand("R", f, W, (d + Vector((0, 0, kick * 0.4))).normalized(), Vector((-1, 0, 0)), pole=sh + Vector((0.35, 0.1, -0.35)))
    return W, d
for f, k in ((1, 0.0), (FIRE - 1, 0.0), (FIRE + 3, 0.35), (FIRE + 14, 0.12), (160, 0.03)):
    r_arm(f, k)
HR.key_hand("L", 1, Vector((0.32 - 0.25, -2.47, 0.95)), Vector((0, 0.2, -1)), Vector((1, 0, 0)), pole=Vector((0.32 - 0.5, -2.2, 1.0)))
key_fingers(RRB, "R", 1, curl=55, spread=0, thumb=25)
key_fingers(RRB, "L", 1, curl=40, spread=2, thumb=10)

# ---------------- officer outside the door: backlit silhouette, beckons him out
OFF = O["Officer"]; ROF = make_human_ctrl(OFF); HF = Human(ROF)
bpy.ops.object.mode_set(mode='OBJECT')
OP = Vector((XR + 1.3, 1.45, 0)); OY = -115.0; Rz_ = Matrix.Rotation(math.radians(OY), 3, 'Z')
for s_ in "LR": HF.key_foot(s_, 1, HF.foot_xy(s_, OP, OY), OY)
for f, dz, sd in ((1, -0.01, 0), (1200, -0.012, 2), (1300, -0.01, -2), (1410, -0.012, 1)):
    HF.key_root(f, OP + Vector((0, 0, HF.root_head.z + dz + SOLE)), yaw=OY, side=sd)
for f, hd in ((1, (0, 0)), (1260, (4, -10)), (1330, (-2, 8)), (1410, (2, 4))):
    HF.key_spine(f, flex=2, head=hd)
def of_hand(s_, f, local, d, n, pole):
    HF.key_hand(s_, f, OP + Rz_ @ Vector(local), Rz_ @ Vector(d), Rz_ @ Vector(n), pole=OP + Rz_ @ Vector(pole))
for f in (1, 1300, 1410):     # left hand resting on the belt
    of_hand("L", f, (0.2, -0.08, 1.0), (-0.3, -0.2, -0.9), (-0.9, 0, 0.2), (0.5, 0.3, 1.1))
of_hand("R", 1, (-0.22, -0.02, 0.86), (0, -0.1, -1), (0.9, 0, 0), (-0.5, 0.3, 1.1))
of_hand("R", 1300, (-0.22, -0.02, 0.86), (0, -0.1, -1), (0.9, 0, 0), (-0.5, 0.3, 1.1))
for f, z in ((1325, 1.3), (1340, 1.42), (1355, 1.3), (1370, 1.42), (1385, 1.32)):   # beckoning wave
    of_hand("R", f, (-0.28, -0.3, z), (0.0, -0.4, 1.0), (0.0, 1.0, 0.0), (-0.5, 0.1, 1.0))
key_fingers(ROF, "L", 1, curl=40, spread=2, thumb=10); key_fingers(ROF, "R", 1, curl=20, spread=4, thumb=10)

# ---------------- hand rule: Limit Rotation (local) on fingers, thumbs, wrists of every character
def add_hand_limits(R):
    for pb in R.PB:
        n = pb.name
        if n.startswith("finger") and n[-2:] in (".L", ".R"):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
            c.use_limit_x = c.use_limit_y = c.use_limit_z = True
            if n.startswith("finger1"):           # thumb: natural cone
                c.min_x, c.max_x = math.radians(-20), math.radians(50); c.min_y, c.max_y = math.radians(-30), math.radians(30); c.min_z, c.max_z = math.radians(-35), math.radians(35)
            else:                                 # fingers: 0..90 forward, no backward bend, +-10 spread
                c.min_x, c.max_x = 0.0, math.radians(90); c.min_y, c.max_y = math.radians(-5), math.radians(5); c.min_z, c.max_z = math.radians(-10), math.radians(10)
        elif n.startswith("wrist."):
            c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "HandLimit"
            c.use_limit_x = c.use_limit_z = True; c.min_x, c.max_x = math.radians(-70), math.radians(70); c.min_z, c.max_z = math.radians(-45), math.radians(45)
for R_ in (ROW, RRB, ROF): add_hand_limits(R_)

# =============================================================== attach props to bones
def bone_world(R, n, f=None):
    if f is not None: sc.frame_set(f)
    return R.o.matrix_world @ R.PB[n].matrix

def parent_bone(o, arm, bone, Mworld):
    """parent o to bone keeping the given world matrix (evaluated at the current frame)"""
    o.parent = arm; o.parent_type = 'BONE'; o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = Mworld

# gun into the robber's right palm, at the pose of frame 1
sc.frame_set(1)
Mw = bone_world(RRB, "wrist.R"); f3 = (RB.matrix_world @ RRB.PB["finger3-1.R"].head); wr = RB.matrix_world @ RRB.PB["wrist.R"].head
palmc = wr.lerp(f3, 0.55)
aim = (HEAD_T - palmc).normalized()
side = aim.cross(Vector((0, 0, 1))).normalized(); up = side.cross(aim).normalized()
G = O["Gun"]
Mg = Matrix((aim, -side, up)).transposed().to_4x4()    # gun +X along aim
Mg.translation = palmc + up * 0.045 - aim * 0.01
parent_bone(G, RB, "wrist.R", Mg)
MUZZLE_LOCAL = Vector((0.19, 0, 0.0))

# owner's body mesh (evaluated) BVH for surface placement
def body_bvh(f, cage=False):
    sc.frame_set(f)
    sub = [m for m in O["Owner.body"].modifiers if m.type in ('SUBSURF', 'MASK')]
    if cage:
        for m in sub: m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    ob = O["Owner.body"].evaluated_get(dg); me = ob.to_mesh()
    verts = [ob.matrix_world @ v.co for v in me.vertices]; polys = [tuple(p.vertices) for p in me.polygons]
    ob.to_mesh_clear()
    for m in sub: m.show_viewport = True
    return BVHTree.FromPolygons(verts, polys), verts

VG = {g.index: g.name for g in O["Owner.body"].vertex_groups}
def group_verts(names, wmin=0.3):
    out = set()
    for v in O["Owner.body"].data.vertices:
        for g in v.groups:
            if VG.get(g.group) in names and g.weight >= wmin: out.add(v.index)
    return out

def finger_radius(verts, a, b, t, group=None):
    """fit a circle to the finger skin (cage verts of this finger's group) in a slab at parameter t along the bone"""
    ax = (b - a); L = ax.length; ax.normalize(); c = a + ax * (L * t)
    idx = [i for i in (group if group is not None else range(len(verts))) if abs((verts[i] - c).dot(ax)) < 0.003]
    if not idx: return 0.009, c, ax
    cen = sum((verts[i] for i in idx), Vector()) / len(idx); cen = cen - ax * (cen - c).dot(ax)
    rs = [((verts[i] - cen) - ax * (verts[i] - cen).dot(ax)).length for i in idx]
    return max(rs), cen, ax

bvh0, V0 = body_bvh(1)
_, VC = body_bvh(1, cage=True)
def bone_seg(R, n):
    pb = R.PB[n]; Mw_ = R.o.matrix_world
    return Mw_ @ pb.head, Mw_ @ pb.tail
a, b = bone_seg(ROW, "finger4-1.L")
rr, rc, rax = finger_radius(VC, a, b, 0.6, group_verts({"finger4-1.L"}))
ring = O["WeddingRing"]; s_ = (rr + 0.0003) / 0.0095
ring.scale = (s_, s_, 1.0)
zr = rax; xr = zr.cross(Vector((0, 0, 1))).normalized(); yr = zr.cross(xr)
Mr = Matrix((xr, yr, zr)).transposed().to_4x4(); Mr.translation = rc
# orient the ring so its dent side (+Y local) faces the incoming bullet later; rotate about the finger axis
parent_bone(ring, OW, "finger4-1.L", Mr @ Matrix.Scale(1, 4))
ring.scale = (s_, s_, 1.0)
# ring seat: press the skin under the band in by ~2 mm (vertex-group displace right after the armature)
body = O["Owner.body"]; seat = body.vertex_groups.new(name="RingSeat")
g4 = group_verts({"finger4-1.L", "finger4-2.L"}, 0.1)
for i in g4:
    h = abs((VC[i] - rc).dot(rax))
    if h < 0.006: seat.add([i], 1.0 - smooth(h / 0.006), 'REPLACE')
dm = body.modifiers.new("RingSeat", 'DISPLACE'); dm.vertex_group = "RingSeat"; dm.strength = -0.0024; dm.mid_level = 0.0
dm.direction = 'NORMAL'
with bpy.context.temp_override(object=body):
    while body.modifiers.find("RingSeat") > 1: bpy.ops.object.modifier_move_up(modifier="RingSeat")
print("RING radius finger %.4f scale %.3f" % (rr, s_))
# bandage on the middle finger (finger3-1.L), nick under it
a3, b3 = bone_seg(ROW, "finger3-1.L"); r3, c3, ax3 = finger_radius(VC, a3, b3, 0.55, group_verts({"finger3-1.L"}))
band = O["FingerBandage"]; s3 = (r3 + 0.0012) / 0.0098
x3 = ax3.cross(Vector((0, 0, 1))).normalized(); y3 = ax3.cross(x3)
Mb = Matrix((x3, y3, ax3)).transposed().to_4x4(); Mb.translation = c3
parent_bone(band, OW, "finger3-1.L", Mb); band.scale = (s3, s3, 0.75)
# nick: ray toward the finger axis from the ring-finger side
hit = bvh0.ray_cast(c3 + x3 * 0.03, -x3)
nick = O["FingerNick"]
if hit[0] is not None:
    loc, nrm = hit[0], hit[1]
    Mn = nrm.to_track_quat('Y', 'Z').to_matrix().to_4x4(); Mn.translation = loc - nrm * 0.0003
    parent_bone(nick, OW, "finger3-1.L", Mn); nick.scale = (0.0016, 0.0008, 0.0045)
# neck mark + plaster: his right side of neck (world -X)
nk = (OW.matrix_world @ ROW.PB["neck02"].head).lerp(OW.matrix_world @ ROW.PB["neck03"].head, 0.6)
hitn = bvh0.ray_cast(nk + Vector((-0.12, -0.03, 0)), Vector((1, 0.25, 0)).normalized())
NECK_PT, NECK_N = (hitn[0], hitn[1]) if hitn[0] is not None else (nk + Vector((-0.055, 0, 0)), Vector((-1, 0, 0)))
for nm, sc_, off in (("NeckMark", (0.005, 0.0012, 0.0025), 0.0002), ("NeckPlaster", (1, 1, 1), 0.0012)):
    o = O[nm]; Mm = NECK_N.to_track_quat('Y', 'Z').to_matrix().to_4x4(); Mm.translation = NECK_PT + NECK_N * off
    parent_bone(o, OW, "neck02", Mm); o.scale = sc_
for o, f0, f1 in ((nick, 1, 896), (O["NeckMark"], 1, 1003), (band, 1, 1244), (O["NeckPlaster"], 1, 1244)):
    hide_key(o, f0, True); hide_key(o, f1, False); const_interp(o)
hide_key(nick, 1244, True); hide_key(O["NeckMark"], 1244, True); const_interp(nick); const_interp(O["NeckMark"])

sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED stage1")
