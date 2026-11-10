"""Blocking animation for the whole 39 s goat rescue film (60 fps, frames 1-2340).

blender -b gr_scene.blend --python 03_animate.py -- <out.blend>
"""
import sys, os, math
import bpy
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "03_anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
HX = Vector((60.0, 0.0, 0.0))

# =============================================================== FARMER control rig
F = bpy.data.objects["Farmer"]
F.location = (0, 0, 0); F.rotation_euler = (0, 0, 0)
bpy.context.view_layer.objects.active = F
for o in bpy.context.selected_objects: o.select_set(False)
F.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = F.data.edit_bones
for s in "LR":
    src = eb["wrist." + s]; b = eb.new("IK_hand." + s)
    b.head, b.tail, b.roll = src.head.copy(), src.tail.copy(), src.roll; b.use_deform = False; b.parent = None
    el = eb["lowerarm01." + s].head.copy(); sx = 1 if s == "L" else -1
    p = eb.new("Pole_elbow." + s); p.head = el + Vector((0.25 * sx, 0.55, -0.1)); p.tail = p.head + Vector((0, 0, 0.08))
    p.use_deform = False; p.parent = None
bpy.ops.object.mode_set(mode='POSE')
FR = Rig(F)
for pb in F.pose.bones: pb.rotation_mode = 'QUATERNION'
IKC = {}
for s in "LR":
    c = FR.PB["lowerarm02." + s].constraints.new('IK')
    c.target, c.subtarget = F, "IK_hand." + s
    c.pole_target, c.pole_subtarget = F, "Pole_elbow." + s
    c.chain_count = 4; c.iterations = 300
    IKC[s] = c
    for tw in ("upperarm02.", "lowerarm02."):
        p = FR.PB[tw + s]; p.lock_ik_x = p.lock_ik_y = p.lock_ik_z = True
    cr = FR.PB["wrist." + s].constraints.new('COPY_ROTATION'); cr.target, cr.subtarget = F, "IK_hand." + s
for s in "LR":
    c = IKC[s]; ref = FR.BN["lowerarm01." + s].head_local.copy(); best = (0, 9)
    for d in range(-180, 180, 4):
        c.pole_angle = R_(d); ev()
        e = (FR.PB["lowerarm01." + s].head - ref).length
        if e < best[1]: best = (d, e)
    for d10 in range((best[0] - 4) * 10, (best[0] + 4) * 10):
        c.pole_angle = R_(d10 / 10); ev()
        e = (FR.PB["lowerarm01." + s].head - ref).length
        if e < best[1]: best = (d10 / 10, e)
    c.pole_angle = R_(best[0])
print("FARMER poles", IKC["L"].pole_angle, IKC["R"].pole_angle)

ROOT_HEAD = FR.BN["root"].head_local.copy()
SH = {s: FR.BN["upperarm01." + s].head_local.copy() for s in "LR"}

def hand_basis(s, d, n):
    d = d.normalized(); n = (n - d * n.dot(d)).normalized()
    a = d.cross(n) if s == "R" else n.cross(d)
    return Matrix((d, a, n)).transposed()
REST_HAND = {}
for s in "LR":
    wv = FR.BN["wrist." + s].head_local
    d = FR.BN["finger3-1." + s].head_local - wv
    a = FR.BN["finger2-1." + s].head_local - FR.BN["finger5-1." + s].head_local
    n = d.cross(a) if s == "L" else a.cross(d)
    REST_HAND[s] = hand_basis(s, d, n)

def hand_matrix(s, W, d, n):
    Rm = hand_basis(s, d, n) @ REST_HAND[s].transposed()
    wr = FR.BN["wrist." + s].head_local
    return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ FR.rest("IK_hand." + s)

def arm_rest(s, fwd=0.0, out=8.0, L=0.47, twist=0.0):
    """hand target in rest-body coords: arm hangs, then abducts by 'out' and swings forward by 'fwd' (deg)"""
    sx = 1 if s == "L" else -1
    R = Matrix.Rotation(R_(-fwd), 3, 'X') @ Matrix.Rotation(R_(sx * out), 3, 'Y')
    W = SH[s] + Vector((sx * 0.04, -0.02, 0)) + R @ Vector((0, 0, -L))
    d = R @ Vector((sx * 0.05, -0.15, -1.0))
    n = Matrix.Rotation(R_(twist * sx), 3, 'Z') @ (R @ Vector((-sx * 0.9, 0.35, 0.0)))
    return W, d, n

# ------------------------------------------------------------------ pose keying
SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
POSES = []          # (frame, pose dict) collected, keyed in two passes (body then hands)

def P(f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), legs=None, arms=None, jaw=0.0, curl=None):
    POSES.append((f, dict(pos=Vector(pos), yaw=yaw, pitch=pitch, roll=roll, spine=spine, head=head,
                          legs=legs or {}, arms=arms or {}, jaw=jaw, curl=curl)))

def key_body(f, p):
    Rw = (Matrix.Rotation(R_(p["yaw"]), 3, 'Z') @ Matrix.Rotation(R_(p["pitch"]), 3, 'X') @
          Matrix.Rotation(R_(p["roll"]), 3, 'Y'))
    M = Matrix.Translation(p["pos"]) @ Rw.to_4x4() @ Matrix.Translation(-ROOT_HEAD) @ FR.rest("root")
    FR.key_world("root", f, M)
    fl, sd, tw = p["spine"]
    for n, w in SPINE_W.items():
        FR.key_rot(n, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
    hp, ht, hr = p["head"]
    for n, w in HEAD_W.items():
        FR.key_rot(n, f, [("X", hp * w), ("Y", hr * w), ("Z", ht * w)])
    for s in "LR":
        sx = 1 if s == "L" else -1
        flex, abd, knee, ank = p["legs"].get(s, (0, 4, 4, 0))
        FR.key_rot("upperleg01." + s, f, [("Y", -sx * abd), ("X", -flex)])
        FR.key_rot("lowerleg01." + s, f, [("X", knee)])
        FR.key_rot("foot." + s, f, [("X", -ank)])
    FR.key_rot("jaw", f, [("X", -p["jaw"])])

def key_hands(f, p):
    ev(f)
    M = FR.delta("spine01"); R3 = M.to_3x3()
    for s in "LR":
        sx = 1 if s == "L" else -1
        a = p["arms"].get(s, ("rest", dict()))
        kind, prm = a
        if kind == "world":
            W, d, n = prm["W"], prm["d"], prm["n"]
            FR.key_world("IK_hand." + s, f, hand_matrix(s, W, d, n))
        else:
            W, d, n = arm_rest(s, **prm)
            FR.key_world("IK_hand." + s, f, hand_matrix(s, M @ W, R3 @ d, R3 @ n))
        pole = M @ (SH[s] + Vector((0.35 * sx, 0.45, -0.25)))
        pb = FR.PB["Pole_elbow." + s]
        pb.location = FR.rest("Pole_elbow." + s).to_3x3().inverted() @ (pole - FR.BN["Pole_elbow." + s].head_local)
        pb.keyframe_insert("location", frame=f, group="Pole_elbow." + s)

# ------------------------------------------------------------------ layout
PILE_TOP = sc["pile_top"]
LA = sc["lie_angle"]; LC = Vector(sc["lie_center"])
HEAD_DIR = Vector((math.cos(LA), math.sin(LA)))
LIE_PELVIS = LC - HEAD_DIR * 0.25
LZ = ground_z(LIE_PELVIS.x, LIE_PELVIS.y) + 0.105
LIE_POS = Vector((LIE_PELVIS.x, LIE_PELVIS.y, LZ))
LYAW = -90 + math.degrees(LA)            # body yaw so that, lying on the back, the head points along HEAD_DIR
STAND = Vector((-2.35, -0.45, ROOT_HEAD.z - 0.02))
print("LAYOUT lie pelvis", tuple(round(v, 3) for v in LIE_POS), "yaw", round(LYAW, 1))

# ------------------------------------------------------------------ B01 work, impact, flight, landing
P(1, STAND, yaw=-90, spine=(22, 0, -8), head=(18, 0, 0), legs={"L": (18, 6, 25, 4), "R": (6, 6, 14, 0)},
  arms={"L": ("rest", dict(fwd=40, out=5, L=0.43)), "R": ("rest", dict(fwd=55, out=-8, L=0.40))})
P(14, STAND + Vector((0, 0, -0.03)), yaw=-90, spine=(30, 0, -12), head=(26, 0, 0), legs={"L": (24, 6, 34, 6), "R": (8, 6, 18, 0)},
  arms={"L": ("rest", dict(fwd=30, out=5, L=0.45)), "R": ("rest", dict(fwd=40, out=-8, L=0.44))})
P(22, STAND, yaw=-92, spine=(12, 0, -4), head=(-4, 6, 0), legs={"L": (16, 6, 20, 4), "R": (6, 6, 12, 0)},
  arms={"L": ("rest", dict(fwd=35, out=8, L=0.44)), "R": ("rest", dict(fwd=45, out=-5, L=0.42))})
P(30, STAND + Vector((0.05, 0, 0.0)), yaw=-90, spine=(-6, 0, 0), head=(-12, 0, 0), legs={"L": (10, 8, 12, 0), "R": (4, 8, 8, 0)},
  arms={"L": ("rest", dict(fwd=70, out=20, L=0.42)), "R": ("rest", dict(fwd=75, out=20, L=0.42))}, jaw=6)
P(36, STAND + Vector((0.08, 0, -0.02)), yaw=-90, spine=(28, 0, 0), head=(20, 0, 0), legs={"L": (24, 8, 30, 0), "R": (20, 8, 26, 0)},
  arms={"L": ("rest", dict(fwd=70, out=30, L=0.42)), "R": ("rest", dict(fwd=72, out=30, L=0.42))}, jaw=10)
# ballistic flight 36 -> 92
T0, T1 = 36, 92
z0 = STAND.z + 0.04; z1 = LIE_POS.z + 0.03
TT = (T1 - T0) / 60.0
vz = (z1 - z0 + 4.905 * TT * TT) / TT
def flight(f):
    t = (f - T0) / 60.0; u = (f - T0) / (T1 - T0)
    xy = (STAND.to_2d() + Vector((0.12, 0))).lerp(LIE_POS.to_2d(), u * (1.08 - 0.08 * u))
    return Vector((xy.x, xy.y, z0 + vz * t - 4.905 * t * t))
for f, pit, rl, sp, hd, lg, am in [
        (44, -18, 4, (-14, 0, 0), (-18, 0, 0), {"L": (-30, 14, 40, 10), "R": (-40, 14, 50, 10)}, (95, 35)),
        (54, -42, 8, (-22, 0, 4), (-25, 4, 0), {"L": (-55, 18, 55, 10), "R": (-62, 18, 60, 10)}, (120, 45)),
        (66, -64, 10, (-18, 0, 6), (-10, 6, 0), {"L": (-70, 22, 50, 10), "R": (-60, 22, 70, 10)}, (140, 55)),
        (80, -82, 6, (-8, 0, 2), (6, 4, 0), {"L": (-55, 24, 40, 6), "R": (-50, 24, 50, 6)}, (130, 70))]:
    P(f, flight(f), yaw=-90 + (f - 36) * 0.15, pitch=pit, roll=rl, spine=sp, head=hd, legs=lg,
      arms={"L": ("rest", dict(fwd=am[0], out=am[1], L=0.45)), "R": ("rest", dict(fwd=am[0] - 10, out=am[1] + 5, L=0.45))}, jaw=12)
# impact + bounce + settle (spread-eagle)
SPREAD = dict(legs={"L": (-6, 22, 10, 10), "R": (-4, 18, 8, 10)},
              arms={"L": ("rest", dict(fwd=10, out=78, L=0.46)), "R": ("rest", dict(fwd=6, out=72, L=0.46))})
P(92, LIE_POS + Vector((0, 0, -0.025)), yaw=LYAW, pitch=-92, roll=4, spine=(6, 0, 0), head=(18, 0, 0), jaw=8, **{k: v for k, v in SPREAD.items()})
P(100, LIE_POS + Vector((0, 0, 0.035)), yaw=LYAW, pitch=-88, roll=2, spine=(-4, 0, 0), head=(-8, 4, 0), jaw=4,
  legs={"L": (-14, 24, 22, 10), "R": (-10, 20, 18, 10)}, arms={"L": ("rest", dict(fwd=20, out=85, L=0.46)), "R": ("rest", dict(fwd=16, out=80, L=0.46))})
P(116, LIE_POS, yaw=LYAW, pitch=-90, roll=0, spine=(2, 0, 0), head=(4, 8, 0), jaw=2, **SPREAD)
P(190, LIE_POS, yaw=LYAW, pitch=-90, roll=0, spine=(3, 0, 0), head=(6, 10, 0), jaw=3, **SPREAD)
# ------------------------------------------------------------------ B02 snapping his hip: pain jolt
P(205, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(14, -4, 0), head=(22, 4, 0), jaw=14,
  legs={"L": (8, 14, 30, 10), "R": (-4, 22, 12, 10)}, arms={"L": ("rest", dict(fwd=35, out=60, L=0.44)), "R": ("rest", dict(fwd=40, out=30, L=0.40))})
P(240, LIE_POS, yaw=LYAW, pitch=-90, roll=-6, spine=(20, -6, 0), head=(26, 2, 0), jaw=16,
  legs={"L": (12, 12, 36, 10), "R": (-4, 22, 12, 10)}, arms={"L": ("rest", dict(fwd=40, out=55, L=0.44)), "R": ("rest", dict(fwd=55, out=20, L=0.36))})
P(284, LIE_POS, yaw=LYAW, pitch=-90, roll=-2, spine=(6, -2, 0), head=(10, 4, 0), jaw=6,
  legs={"L": (6, 16, 24, 10), "R": (-6, 22, 10, 10)}, arms={"L": ("rest", dict(fwd=15, out=70, L=0.46)), "R": ("rest", dict(fwd=30, out=35, L=0.42))})
# ------------------------------------------------------------------ B03 tries to rise, fails; reaches for help
P(320, LIE_POS, yaw=LYAW, pitch=-90, spine=(26, 0, 0), head=(30, 0, 0), jaw=8,
  legs={"L": (-6, 20, 10, 10), "R": (6, 16, 24, 10)}, arms={"L": ("rest", dict(fwd=30, out=40, L=0.44)), "R": ("rest", dict(fwd=34, out=36, L=0.44))})
P(350, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(4, -6, 0), jaw=4,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=10, out=68, L=0.46)), "R": ("rest", dict(fwd=12, out=55, L=0.46))})
P(400, LIE_POS, yaw=LYAW, pitch=-90, spine=(6, 0, 0), head=(2, 10, 0), jaw=6,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=95, out=20, L=0.46)), "R": ("rest", dict(fwd=12, out=55, L=0.46))})
P(440, LIE_POS, yaw=LYAW, pitch=-90, spine=(8, 0, 0), head=(-4, 12, 0), jaw=10,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=150, out=15, L=0.47)), "R": ("rest", dict(fwd=12, out=55, L=0.46))})
P(470, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(0, 8, 0), jaw=4,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=110, out=30, L=0.46)), "R": ("rest", dict(fwd=12, out=55, L=0.46))})
P(496, LIE_POS, yaw=LYAW, pitch=-90, spine=(2, 0, 0), head=(2, 6, 0), jaw=2, **SPREAD)
# ------------------------------------------------------------------ B04 five days (subtle shifts), B05 sun, B06 night shiver
for f, hd in ((560, (6, -12, 0)), (620, (2, 14, 0)), (676, (4, 2, 0))):
    P(f, LIE_POS, yaw=LYAW, pitch=-90, spine=(2, 0, 0), head=hd, jaw=3, **SPREAD)
P(700, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(-4, -6, 0), jaw=8,
  legs=SPREAD["legs"], arms={"L": ("rest", dict(fwd=140, out=-30, L=0.30)), "R": ("rest", dict(fwd=10, out=60, L=0.46))})
P(752, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(-6, -4, 0), jaw=10,
  legs=SPREAD["legs"], arms={"L": ("rest", dict(fwd=145, out=-35, L=0.29)), "R": ("rest", dict(fwd=10, out=60, L=0.46))})
SHIVER = dict(legs={"L": (24, 6, 40, 8), "R": (28, 4, 46, 8)},
              arms={"L": ("rest", dict(fwd=60, out=-40, L=0.30)), "R": ("rest", dict(fwd=62, out=-42, L=0.30))})
for i, f in enumerate(range(790, 869, 8)):
    P(f, LIE_POS + Vector((0, 0, 0.004 * (i % 2))), yaw=LYAW, pitch=-90, roll=-10 + 2 * (i % 2), spine=(10, 0, 0), head=(12, -8, 0), jaw=1, **SHIVER)
# ------------------------------------------------------------------ B07 not alone: head turns to the ridge
P(900, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(8, 0, 0), head=(6, -26, 0), jaw=2, legs=SHIVER["legs"],
  arms={"L": ("rest", dict(fwd=30, out=30, L=0.42)), "R": ("rest", dict(fwd=30, out=30, L=0.42))})
P(968, LIE_POS, yaw=LYAW, pitch=-90, roll=-2, spine=(14, 0, 0), head=(18, -32, 0), jaw=4, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=25, out=35, L=0.44)), "R": ("rest", dict(fwd=20, out=40, L=0.44))})
# B08 goat arrives at his head; he lifts his right hand to her
P(1060, LIE_POS, yaw=LYAW, pitch=-90, spine=(10, 0, 0), head=(12, -30, 0), jaw=2, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=20, out=40, L=0.44)), "R": ("rest", dict(fwd=20, out=40, L=0.44))})
P(1120, LIE_POS, yaw=LYAW, pitch=-90, spine=(12, 0, -6), head=(14, -38, 0), jaw=4, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=20, out=40, L=0.44)), "R": ("rest", dict(fwd=150, out=-10, L=0.44))})
P(1175, LIE_POS, yaw=LYAW, pitch=-90, spine=(10, 0, -4), head=(10, -36, 0), jaw=2, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=20, out=40, L=0.44)), "R": ("rest", dict(fwd=120, out=10, L=0.44))})
# B09 night: she lies along his right side; he rolls slightly toward her, arm over her
P(1260, LIE_POS, yaw=LYAW, pitch=-90, roll=-12, spine=(10, 0, -8), head=(8, -30, 0), jaw=1, legs={"L": (14, 6, 34, 8), "R": (12, 4, 30, 8)},
  arms={"L": ("rest", dict(fwd=60, out=-30, L=0.34)), "R": ("rest", dict(fwd=40, out=30, L=0.44))})
P(1388, LIE_POS, yaw=LYAW, pitch=-90, roll=-14, spine=(10, 0, -8), head=(8, -34, 0), jaw=1, legs={"L": (16, 6, 36, 8), "R": (14, 4, 32, 8)},
  arms={"L": ("rest", dict(fwd=70, out=-35, L=0.32)), "R": ("rest", dict(fwd=46, out=24, L=0.44))})
# B10 days pass, grows weak (sinks, still)
P(1500, LIE_POS + Vector((0, 0, -0.01)), yaw=LYAW, pitch=-90, roll=-6, spine=(2, 0, -2), head=(0, -14, 0), jaw=6, **SPREAD)
P(1604, LIE_POS + Vector((0, 0, -0.012)), yaw=LYAW, pitch=-90, roll=-4, spine=(2, 0, 0), head=(4, -20, 0), jaw=8, **SPREAD)
# B11 milking: roll toward the goat (+Y side = his right), right hand milks, left holds the bottle
MILK = dict(legs={"L": (10, 8, 26, 8), "R": (8, 6, 20, 8)})
P(1640, LIE_POS, yaw=LYAW, pitch=-90, roll=-22, spine=(18, 0, -10), head=(16, -40, 0), jaw=4, **MILK,
  arms={"L": ("rest", dict(fwd=70, out=-40, L=0.40)), "R": ("rest", dict(fwd=80, out=-10, L=0.42))})
for i, f in enumerate(range(1670, 1831, 15)):
    P(f, LIE_POS, yaw=LYAW, pitch=-90, roll=-24, spine=(20, 0, -12), head=(18, -42 + 2 * (i % 2), 0), jaw=4, **MILK,
      arms={"L": ("rest", dict(fwd=88, out=-48, L=0.40)), "R": ("rest", dict(fwd=95 + 6 * (i % 2), out=-18, L=0.40 - 0.02 * (i % 2)))})
# B12 drinks: lifts head, bottle to lips (left hand)
P(1870, LIE_POS, yaw=LYAW, pitch=-90, roll=-10, spine=(22, 0, -4), head=(26, -10, 0), jaw=8, **MILK,
  arms={"L": ("rest", dict(fwd=110, out=-62, L=0.27)), "R": ("rest", dict(fwd=30, out=30, L=0.44))})
P(1940, LIE_POS, yaw=LYAW, pitch=-90, roll=-8, spine=(24, 0, -4), head=(14, -8, 0), jaw=10, **MILK,
  arms={"L": ("rest", dict(fwd=125, out=-66, L=0.25)), "R": ("rest", dict(fwd=30, out=30, L=0.44))})
P(1973, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(8, 0, 0), head=(6, -10, 0), jaw=4, **MILK,
  arms={"L": ("rest", dict(fwd=60, out=-20, L=0.40)), "R": ("rest", dict(fwd=25, out=35, L=0.44))})
# B13 lifted onto the stretcher, wheeled to the ambulance
ST = bpy.data.objects["Stretcher"]
ST_A = Vector((-0.9, -1.55, 0)); ST_B = Vector((-4.6, -3.5, 0)); ST_YAW_A, ST_YAW_B = math.radians(102), math.radians(60)
ST.rotation_mode = 'XYZ'
for f, loc, yw in ((1, Vector((-9, -6, 0)), ST_YAW_A), (1974, Vector((-1.6, -2.0, 0)), ST_YAW_A), (2010, ST_A, ST_YAW_A),
                   (2060, ST_A, ST_YAW_A), (2130, ST_B, ST_YAW_B), (2149, ST_B + Vector((-0.4, -0.25, 0)), ST_YAW_B)):
    ST.location = loc; ST.rotation_euler = (0, 0, yw)
    ST.keyframe_insert("location", frame=f); ST.keyframe_insert("rotation_euler", frame=f)
P(2015, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(6, -16, 0), jaw=2, **SPREAD)
def on_stretcher(f, loc, yw):
    # stretcher local +Y is its long axis; head toward +Y
    d = Matrix.Rotation(yw, 3, 'Z') @ Vector((0, 1, 0))
    pel = loc + Vector((0, 0, 0.66 + 0.11)) - d * 0.15
    yaw = math.degrees(math.atan2(d.y, d.x)) - 90
    P(f, pel, yaw=yaw, pitch=-90, spine=(10, 0, 0), head=(12, 0, 0), jaw=2, legs={"L": (0, 4, 6, 6), "R": (0, 4, 6, 6)},
      arms={"L": ("rest", dict(fwd=20, out=10, L=0.46)), "R": ("rest", dict(fwd=20, out=10, L=0.46))})
P(2035, (LIE_POS + (ST_A + Vector((0, 0, 0.77)))) / 2 + Vector((0, 0, 0.35)), yaw=LYAW + 20, pitch=-86, spine=(10, 0, 0), head=(10, -6, 0), jaw=3,
  legs={"L": (10, 6, 20, 6), "R": (10, 6, 20, 6)}, arms={"L": ("rest", dict(fwd=30, out=30, L=0.44)), "R": ("rest", dict(fwd=30, out=30, L=0.44))})
for f in (2060, 2090, 2130, 2149):
    ev(f); on_stretcher(f, ST.matrix_world.translation.copy(), ST.rotation_euler.z)
# B14 hospital bed
BED = bpy.data.objects["Hospital_Bed"]
bed_pel = BED.location + Vector((-0.15, 0.0, 0.0))
for f, hd, jw, armL in ((2150, (8, 10, 0), 1, (20, 12)), (2220, (6, 40, 0), 2, (20, 12)), (2290, (4, 52, 0), 6, (34, 22)), (2340, (4, 55, 0), 8, (36, 24))):
    P(f, Vector((HX.x + 1.2, 0.35, 0.72)), yaw=0, pitch=-58, spine=(12, 0, 0), head=hd, jaw=jw,
      legs={"L": (56, 4, 8, 10), "R": (56, 4, 8, 10)},
      arms={"L": ("rest", dict(fwd=armL[0], out=armL[1], L=0.44)), "R": ("rest", dict(fwd=24, out=12, L=0.46))})
POSES.sort(key=lambda x: x[0])
for f, p in POSES:
    key_body(f, p)
# the move into the hospital is a teleport hidden in the sky tilt: hold constant across 2149->2150
for f, p in POSES:
    key_hands(f, p)
print("FARMER keyed poses", len(POSES))

# ------------------------------------------------------------------ pitchfork: held, then knocked away
fork = bpy.data.objects["Pitchfork"]
fork.rotation_mode = 'XYZ'
co = fork.constraints.new('CHILD_OF'); co.target = F; co.subtarget = "wrist.R"
ev(1)
co.inverse_matrix = (F.matrix_world @ FR.PB["wrist.R"].matrix).inverted()
# grip pose: shaft along the forearm-forward line
grip = (F.matrix_world @ FR.PB["wrist.R"].matrix) @ Matrix.Translation((0, 0.05, 0))
fork.matrix_world = Matrix.Translation(grip.translation + Vector((0, 0, -0.15))) @ Matrix.Rotation(R_(-60), 4, 'Y') @ Matrix.Rotation(R_(90), 4, 'Z')
for f, v in ((1, 1.0), (37, 1.0), (38, 0.0)):
    co.influence = v; co.keyframe_insert("influence", frame=f)
ev(37)
mw = fork.matrix_world.copy()
co.influence = 0.0
fork.matrix_world = mw
fork.keyframe_insert("location", frame=38); fork.keyframe_insert("rotation_euler", frame=38)
for f, dl, rot in ((52, (-0.4, -0.9, 0.9), (1.5, 0.4, 2.0)), (66, (-0.7, -1.6, 0.6), (3.2, 0.8, 3.6)), (80, (-0.9, -2.0, -0.55), (4.6, 1.0, 4.4))):
    fork.location = mw.translation + Vector(dl); fork.rotation_euler = Vector(mw.to_euler()) + Vector(rot)
    fork.keyframe_insert("location", frame=f); fork.keyframe_insert("rotation_euler", frame=f)
fork.location.z = 0.04
fork.keyframe_insert("location", frame=86)

# =============================================================== COW: charge, impact, stop, turn away
C = bpy.data.objects["cow_rig"]; C.location = (0, 0, 0); CR = Rig(C)
for pb in C.pose.bones: pb.rotation_mode = 'QUATERNION'
cow_path = pchip([(1, -8.6), (34, -4.05), (60, -3.35), (80, -3.25)])
quad_move(CR, lambda f: Vector((cow_path(f), -0.55, 0)), 1, 80, stride=1.6, gait="trot", lift=0.14, body_bob=0.03,
          heading_fn=lambda f: R_(90))
cow_exit = catmull([(81, Vector((-3.25, -0.55, 0))), (150, Vector((-3.45, -1.25, 0))), (230, Vector((-3.9, -2.9, 0)))])
turn = pchip([(81, 90.0), (140, 150.0), (230, 178.0)])
quad_move(CR, cow_exit, 81, 230, stride=1.1, gait="walk", lift=0.09, body_bob=0.012, heading_fn=lambda f: R_(turn(f)))
for f, nk in ((1, (8, 0)), (26, (22, 0)), (34, (34, 0)), (40, (10, 0)), (70, (-8, 6)), (120, (-4, 14)), (180, (6, 4))):
    CR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); CR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
C.hide_render = False; C.keyframe_insert("hide_render", frame=1)
C.hide_render = True; C.keyframe_insert("hide_render", frame=500)
for ch in C.children:
    ch.hide_render = False; ch.keyframe_insert("hide_render", frame=1)
    ch.hide_render = True; ch.keyframe_insert("hide_render", frame=500)

# =============================================================== GOAT
G = bpy.data.objects["goat_rig"]; G.location = (0, 0, 0); GR = Rig(G)
for pb in G.pose.bones: pb.rotation_mode = 'QUATERNION'
HEAD_W_POS = LIE_POS.to_2d() + HEAD_DIR * 0.85          # his head (world xy)
RSIDE = Vector((-HEAD_DIR.y, HEAD_DIR.x))                 # his right side (+Y-ish)
gz = lambda v: ground_z(v.x, v.y)
G_RIDGE = Vector((1.9, 2.6)); G_TOP = Vector((1.35, 1.35)); G_HEAD = HEAD_W_POS + RSIDE * 0.62 + HEAD_DIR * 0.25
quad_hold(GR, 1, G_RIDGE.to_3d(), R_(150))
quad_hold(GR, 880, G_RIDGE.to_3d(), R_(150))
gp = catmull([(880, G_RIDGE.to_3d()), (960, G_TOP.to_3d()), (1040, G_HEAD.to_3d() + (G_TOP - G_HEAD).to_3d() * 0.35), (1080, G_HEAD.to_3d())])
gh = quad_move(GR, gp, 881, 1080, stride=0.42, gait="walk", lift=0.06, body_bob=0.008)
h_end = gh(1078)
quad_hold(GR, 1081, G_HEAD.to_3d(), h_end)
# nuzzle: head down to his face, ear/nose contact, back up
for f, nk in ((1081, (0, 0)), (1100, (34, -10)), (1120, (46, -14)), (1140, (40, -8)), (1160, (48, -14)), (1175, (30, -6))):
    for n in ("neck1", "neck2"):
        GR.key_rot(n, f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
    GR.key_rot("head", f, [("X", nk[0] * 0.25)])
# B09: walk round to lie along his right side
G_SIDE = LIE_POS.to_2d() + RSIDE * 0.55 + HEAD_DIR * 0.1
gp2 = catmull([(1176, G_HEAD.to_3d()), (1215, (G_HEAD + G_SIDE) .to_3d() / 2 + RSIDE.to_3d() * 0.25), (1250, G_SIDE.to_3d())])
quad_move(GR, gp2, 1176, 1250, stride=0.38, gait="walk", lift=0.05, body_bob=0.006)
h_side = math.atan2(-HEAD_DIR.x, HEAD_DIR.y) + math.pi          # facing along -HEAD_DIR (toward his feet)
quad_hold(GR, 1252, G_SIDE.to_3d(), h_side)
for k in LEGS:
    GR.key_rot("neck1", 1252, [("X", 10)])
# lie down 1252 -> 1300 (front first, then hind), stays down until 1500
TR = GR.rest("torso"); Hg = TR.translation.z
def goat_lying(f, dz, fold):
    pos = G_SIDE.to_3d(); h = h_side
    base = gz(pos)
    Rh = Matrix.Rotation(h, 4, 'Z')
    GR.key_world("torso", f, Matrix.Translation(Vector((pos.x, pos.y, base + Hg - dz))) @ Rh @ Matrix.Translation(-TR.translation) @ TR)
    for k in LEGS:
        n = "IK_hoof." + k
        o = Matrix.Rotation(h, 3, 'Z') @ (GR.BN[n].head_local - TR.translation)
        front = k.startswith("F")
        # folded: hooves pulled under the body (front back, hind forward) and out a little
        tuck = Matrix.Rotation(h, 3, 'Z') @ Vector((0.03 * (1 if k.endswith("L") else -1), (0.16 if front else -0.18) * fold, 0))
        p = Vector((pos.x + o.x + tuck.x, pos.y + o.y + tuck.y, 0))
        p.z = gz(p) + GR.BN[n].head_local.z + 0.05 * fold
        GR.key_world(n, f, Matrix.Translation(p) @ Rh @ Matrix.Rotation(R_(-70 if front else 40) * fold, 4, 'X') @
                     Matrix.Translation(-GR.BN[n].head_local) @ GR.rest(n))
goat_lying(1262, 0.0, 0.0)
goat_lying(1285, 0.17, 0.6)
goat_lying(1305, 0.30, 1.0)
goat_lying(1500, 0.31, 1.0)
for f, nk in ((1262, (14, 0)), (1305, (20, 30)), (1388, (24, 34)), (1500, (22, 30))):
    GR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); GR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
# B10/B11 stand up and present the udder by his chest (facing his feet, hind end at his chest)
goat_lying(1530, 0.18, 0.5)
G_MILK = LIE_POS.to_2d() + RSIDE * 0.42 + HEAD_DIR * 0.30
quad_hold(GR, 1560, G_SIDE.to_3d(), h_side)
gp3 = catmull([(1561, G_SIDE.to_3d()), (1600, G_MILK.to_3d())])
quad_move(GR, gp3, 1561, 1600, stride=0.35, gait="walk", lift=0.05, heading_fn=lambda f: h_side)
quad_hold(GR, 1601, G_MILK.to_3d(), h_side)
quad_hold(GR, 1973, G_MILK.to_3d(), h_side)
for f, nk in ((1601, (6, 0)), (1700, (10, 40)), (1800, (8, 30)), (1900, (4, 10))):
    GR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); GR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
# B13 goat steps up onto the heap top and watches
gp4 = catmull([(1974, G_MILK.to_3d()), (2040, G_TOP.to_3d())])
quad_move(GR, gp4, 1974, 2040, stride=0.4, gait="walk", lift=0.06)
quad_hold(GR, 2041, G_TOP.to_3d(), R_(-150))
quad_hold(GR, 2149, G_TOP.to_3d(), R_(-150))
for f, nk in ((2041, (-6, -20)), (2100, (-8, -30)), (2149, (-6, -34))):
    GR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); GR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
# B14 at the hospital window, looking in (outside, +X of the window)
G_WIN = Vector((HX.x + 3.75, 0.05, 0))
quad_hold(GR, 2150, G_WIN, R_(-90))
quad_hold(GR, 2340, G_WIN, R_(-90))
for f, nk in ((2150, (-20, 0)), (2250, (-24, 8)), (2340, (-22, 4))):
    GR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); GR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
# constant interpolation across the scene jumps (no smear through the world)
def stepped(obj, frames):
    ad = obj.animation_data
    if not ad or not ad.action: return
    for layer in getattr(ad.action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        if int(round(kp.co.x)) in frames:
                            kp.interpolation = 'CONSTANT'
for o in (G, F, ST):
    stepped(o, {2149})

print("ANIM_DONE")
exec(open(os.path.join(HERE, "03b_effects_lights_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
