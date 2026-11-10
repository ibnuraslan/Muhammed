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
HX = Vector((sc["hosp_x"], 0.0, 0.0))

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

HAND_PT = {   # rest-body coordinates of hand contact points (sx mirrors to the left side)
    "hip": lambda sx: (Vector((sx * 0.19, -0.04, 0.95)), Vector((0, 0, -1)), Vector((-sx, 0, 0))),
    "chest": lambda sx: (Vector((sx * 0.07, -0.19, 1.24)), Vector((-sx * 0.6, 0, -0.8)), Vector((0, 1, 0))),
    "chest_x": lambda sx: (Vector((-sx * 0.10, -0.18, 1.22)), Vector((-sx * 0.9, 0, -0.4)), Vector((0, 1, 0))),
    "forehead": lambda sx: (Vector((sx * 0.02, -0.20, 1.69)), Vector((-sx, 0, 0.1)), Vector((0, 1, 0.2))),
    "ground_hip": lambda sx: (Vector((sx * 0.30, -0.04, 0.92)), Vector((0, -0.4, -1)), Vector((0, 1, 0))),
}

# ------------------------------------------------------------------ pose keying
SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
POSES = []          # (frame, pose dict) collected, keyed in two passes (body then hands)

def P(f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), legs=None, arms=None, jaw=0.0, curl=None):
    POSES.append((f, dict(pos=Vector(pos), yaw=yaw, pitch=pitch, roll=roll, spine=spine, head=head,
                          legs=legs or {}, arms=arms or {}, jaw=jaw, curl=curl)))

REST_AX = {}
def finger_axes(s):
    Rh = REST_HAND[s]
    return Rh.col[0].copy(), Rh.col[1].copy(), Rh.col[2].copy()
JW = (0.8, 1.1, 0.8)
def key_fingers(s, f, curl, thumb=18, spread=0.0):
    d, a, n = finger_axes(s); sign = 1 if s == "R" else -1
    for k in range(2, 6):
        c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
        for j in range(1, 4):
            b = "finger%d-%d.%s" % (k, j, s)
            FR.key_q(b, f, FR.local_q(b, Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a)))
    for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
        b = "finger1-%d.%s" % (j, s)
        FR.key_q(b, f, FR.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a) @ Matrix.Rotation(R_(22 * sign), 3, d)))

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
    cu = p["curl"] or {}
    for s in "LR":
        c = cu.get(s, (24 if f >= 92 else 16, 20))
        key_fingers(s, f, c[0], c[1])

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
        elif kind == "pt":
            W, d, n = HAND_PT[prm](sx)
            FR.key_world("IK_hand." + s, f, hand_matrix(s, M @ W, R3 @ d, R3 @ n))
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
LZ = ground_z(LIE_PELVIS.x, LIE_PELVIS.y) + 0.105 - 0.19      # sunk well into the muck; the body cast is carved below
LIE_POS = Vector((LIE_PELVIS.x, LIE_PELVIS.y, LZ))
LYAW = -90 + math.degrees(LA)            # body yaw so that, lying on the back, the head points along HEAD_DIR
STAND = Vector((-3.05, -0.45, ROOT_HEAD.z - 0.02))
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
        (80, -82, 6, (-8, 0, 2), (6, 4, 0), {"L": (-28, 22, 30, 6), "R": (-24, 22, 32, 6)}, (130, 70)),
        (87, -88, 4, (-2, 0, 0), (10, 2, 0), {"L": (-12, 22, 16, 8), "R": (-10, 20, 14, 8)}, (100, 76))]:
    P(f, flight(f), yaw=-90 + (f - 36) * 0.15, pitch=pit, roll=rl, spine=sp, head=hd, legs=lg,
      arms={"L": ("rest", dict(fwd=am[0], out=am[1], L=0.45)), "R": ("rest", dict(fwd=am[0] - 10, out=am[1] + 5, L=0.45))}, jaw=12)
# impact + bounce + settle (spread-eagle)
SPREAD = dict(legs={"L": (-6, 22, 10, 10), "R": (-4, 18, 8, 10)},
              arms={"L": ("rest", dict(fwd=-4, out=78, L=0.46)), "R": ("rest", dict(fwd=-4, out=72, L=0.46))})
P(92, LIE_POS + Vector((0, 0, -0.025)), yaw=LYAW, pitch=-92, roll=4, spine=(6, 0, 0), head=(18, 0, 0), jaw=8, **{k: v for k, v in SPREAD.items()})
P(100, LIE_POS + Vector((0, 0, 0.035)), yaw=LYAW, pitch=-88, roll=2, spine=(-4, 0, 0), head=(-8, 4, 0), jaw=4,
  legs={"L": (-14, 24, 22, 10), "R": (-10, 20, 18, 10)}, arms={"L": ("rest", dict(fwd=-4, out=85, L=0.46)), "R": ("rest", dict(fwd=-4, out=80, L=0.46))})
P(116, LIE_POS, yaw=LYAW, pitch=-90, roll=0, spine=(2, 0, 0), head=(4, 8, 0), jaw=2, **SPREAD)
P(190, LIE_POS, yaw=LYAW, pitch=-90, roll=0, spine=(3, 0, 0), head=(6, 10, 0), jaw=3, **SPREAD)
# ------------------------------------------------------------------ B02 snapping his hip: pain jolt
P(205, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(14, -4, 0), head=(22, 4, 0), jaw=14,
  legs={"L": (8, 14, 30, 10), "R": (-4, 22, 12, 10)}, arms={"L": ("pt", "hip"), "R": ("rest", dict(fwd=-4, out=62, L=0.46))})
P(240, LIE_POS, yaw=LYAW, pitch=-90, roll=-6, spine=(20, -6, 0), head=(26, 2, 0), jaw=16,
  legs={"L": (12, 12, 36, 10), "R": (-4, 22, 12, 10)}, arms={"L": ("pt", "hip"), "R": ("rest", dict(fwd=-4, out=60, L=0.46))})
P(284, LIE_POS, yaw=LYAW, pitch=-90, roll=-2, spine=(6, -2, 0), head=(10, 4, 0), jaw=6,
  legs={"L": (6, 16, 24, 10), "R": (-6, 22, 10, 10)}, arms={"L": ("rest", dict(fwd=-4, out=70, L=0.46)), "R": ("rest", dict(fwd=-4, out=35, L=0.42))})
# ------------------------------------------------------------------ B03 tries to rise, fails; reaches for help
P(320, LIE_POS, yaw=LYAW, pitch=-90, spine=(26, 0, 0), head=(30, 0, 0), jaw=8,
  legs={"L": (-6, 20, 10, 10), "R": (6, 16, 24, 10)}, arms={"L": ("pt", "ground_hip"), "R": ("pt", "ground_hip")})
P(350, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(4, -6, 0), jaw=4,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=-4, out=68, L=0.46)), "R": ("rest", dict(fwd=-4, out=55, L=0.46))})
P(400, LIE_POS, yaw=LYAW, pitch=-90, spine=(6, 0, 0), head=(2, 10, 0), jaw=6,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=95, out=20, L=0.46)), "R": ("rest", dict(fwd=-4, out=55, L=0.46))})
P(440, LIE_POS, yaw=LYAW, pitch=-90, spine=(8, 0, 0), head=(-4, 12, 0), jaw=10,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=150, out=15, L=0.47)), "R": ("rest", dict(fwd=-4, out=55, L=0.46))})
P(470, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(0, 8, 0), jaw=4,
  legs={"L": (-6, 22, 10, 10), "R": (4, 16, 20, 10)}, arms={"L": ("rest", dict(fwd=110, out=30, L=0.46)), "R": ("rest", dict(fwd=-4, out=55, L=0.46))})
P(496, LIE_POS, yaw=LYAW, pitch=-90, spine=(2, 0, 0), head=(2, 6, 0), jaw=2, **SPREAD)
# ------------------------------------------------------------------ B04 five days (subtle shifts), B05 sun, B06 night shiver
for f, hd in ((560, (6, -12, 0)), (620, (2, 14, 0)), (676, (4, 2, 0))):
    P(f, LIE_POS, yaw=LYAW, pitch=-90, spine=(2, 0, 0), head=hd, jaw=3, **SPREAD)
P(700, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(-4, -6, 0), jaw=8,
  legs=SPREAD["legs"], arms={"L": ("pt", "forehead"), "R": ("rest", dict(fwd=-4, out=60, L=0.46))})
P(752, LIE_POS, yaw=LYAW, pitch=-90, spine=(4, 0, 0), head=(-6, -4, 0), jaw=10,
  legs=SPREAD["legs"], arms={"L": ("pt", "forehead"), "R": ("rest", dict(fwd=-4, out=60, L=0.46))})
SHIVER = dict(legs={"L": (24, 6, 40, 8), "R": (28, 4, 46, 8)},
              arms={"L": ("pt", "chest_x"), "R": ("pt", "chest_x")})
for i, f in enumerate(range(790, 869, 8)):
    P(f, LIE_POS + Vector((0, 0, 0.004 * (i % 2))), yaw=LYAW, pitch=-90, roll=-10 + 2 * (i % 2), spine=(10, 0, 0), head=(12, -8, 0), jaw=1, **SHIVER)
# ------------------------------------------------------------------ B07 not alone: head turns to the ridge
P(900, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(8, 0, 0), head=(6, -26, 0), jaw=2, legs=SHIVER["legs"],
  arms={"L": ("rest", dict(fwd=-4, out=30, L=0.42)), "R": ("rest", dict(fwd=-4, out=30, L=0.42))})
P(968, LIE_POS, yaw=LYAW, pitch=-90, roll=-2, spine=(14, 0, 0), head=(18, -32, 0), jaw=4, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=-4, out=35, L=0.44)), "R": ("rest", dict(fwd=-4, out=40, L=0.44))})
# B08 goat arrives at his head; he lifts his right hand to her
P(1060, LIE_POS, yaw=LYAW, pitch=-90, spine=(10, 0, 0), head=(12, -30, 0), jaw=2, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=-4, out=40, L=0.44)), "R": ("rest", dict(fwd=-4, out=40, L=0.44))})
P(1120, LIE_POS, yaw=LYAW, pitch=-90, spine=(12, 0, -6), head=(14, -38, 0), jaw=4, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=-4, out=40, L=0.44)), "R": ("rest", dict(fwd=150, out=-10, L=0.44))})
P(1175, LIE_POS, yaw=LYAW, pitch=-90, spine=(10, 0, -4), head=(10, -36, 0), jaw=2, legs={"L": (6, 14, 20, 8), "R": (8, 12, 26, 8)},
  arms={"L": ("rest", dict(fwd=-4, out=40, L=0.44)), "R": ("rest", dict(fwd=120, out=10, L=0.44))})
# B09 night: she lies along his right side; he rolls slightly toward her, arm over her
P(1260, LIE_POS, yaw=LYAW, pitch=-90, roll=-12, spine=(10, 0, -8), head=(8, -30, 0), jaw=1, legs={"L": (14, 6, 34, 8), "R": (12, 4, 30, 8)},
  arms={"L": ("pt", "chest"), "R": ("rest", dict(fwd=-4, out=30, L=0.44))})
P(1388, LIE_POS, yaw=LYAW, pitch=-90, roll=-14, spine=(10, 0, -8), head=(8, -34, 0), jaw=1, legs={"L": (16, 6, 36, 8), "R": (14, 4, 32, 8)},
  arms={"L": ("pt", "chest"), "R": ("rest", dict(fwd=-4, out=30, L=0.44))})
# B10 days pass, grows weak (sinks, still)
P(1500, LIE_POS + Vector((0, 0, -0.01)), yaw=LYAW, pitch=-90, roll=-6, spine=(2, 0, -2), head=(0, -14, 0), jaw=6, **SPREAD)
P(1604, LIE_POS + Vector((0, 0, -0.012)), yaw=LYAW, pitch=-90, roll=-4, spine=(2, 0, 0), head=(4, -20, 0), jaw=8, **SPREAD)
# B11 milking: roll toward the goat (+Y side = his right), right hand milks, left holds the bottle
MILK = dict(legs={"L": (10, 8, 26, 8), "R": (8, 6, 20, 8)})
P(1640, LIE_POS, yaw=LYAW, pitch=-90, roll=-22, spine=(18, 0, -10), head=(16, -40, 0), jaw=4, **MILK,
  arms={"L": ("rest", dict(fwd=70, out=-40, L=0.40)), "R": ("rest", dict(fwd=80, out=-10, L=0.42))})
for i, f in enumerate(range(1670, 1831, 15)):
    P(f, LIE_POS + Vector((0, 0, 0.03)), yaw=LYAW, pitch=-90, roll=-36, spine=(16, 0, -16), head=(14, -44 + 2 * (i % 2), 0), jaw=4, **MILK,
      arms={"L": ("rest", dict(fwd=88, out=-48, L=0.40)), "R": ("rest", dict(fwd=95 + 6 * (i % 2), out=-18, L=0.40 - 0.02 * (i % 2)))})
# B12 drinks: lifts head, bottle to lips (left hand)
P(1870, LIE_POS, yaw=LYAW, pitch=-90, roll=-10, spine=(22, 0, -4), head=(26, -10, 0), jaw=8, **MILK,
  arms={"L": ("rest", dict(fwd=110, out=-62, L=0.27)), "R": ("rest", dict(fwd=-4, out=30, L=0.44))})
P(1940, LIE_POS, yaw=LYAW, pitch=-90, roll=-8, spine=(24, 0, -4), head=(14, -8, 0), jaw=10, **MILK,
  arms={"L": ("rest", dict(fwd=125, out=-66, L=0.25)), "R": ("rest", dict(fwd=-4, out=30, L=0.44))})
P(1973, LIE_POS, yaw=LYAW, pitch=-90, roll=-4, spine=(8, 0, 0), head=(6, -10, 0), jaw=4, **MILK,
  arms={"L": ("rest", dict(fwd=60, out=-20, L=0.40)), "R": ("rest", dict(fwd=-4, out=35, L=0.44))})
# B13 found: two paramedics shift him onto a spine board, lift it and hurry it down to the ambulance
HD2 = HEAD_DIR.copy(); LEFT = -Vector((-HEAD_DIR.y, HEAD_DIR.x))
AMB_REAR = Vector(sc["amb_rear"]).to_2d(); AMB_DIR = Vector(sc["amb_dir"]).to_2d()
BC0 = LIE_POS.to_2d() + LEFT * 0.58 + HD2 * 0.05
BC1 = AMB_REAR + AMB_DIR * 1.7
ang0, ang1 = math.atan2(HD2.y, HD2.x), math.atan2(AMB_DIR.y, AMB_DIR.x)
board_xy = catmull([(1996, BC0.to_3d()), (2018, BC0.to_3d()), (2080, BC0.to_3d().lerp(BC1.to_3d(), 0.5) + Vector((-0.15, 0.1, 0))), (2140, BC1.to_3d()), (2149, BC1.to_3d())])
board_ang = pchip([(1996, ang0), (2030, ang0), (2120, ang1), (2149, ang1)])
def board_hd(f):
    a_ = board_ang(f); return Vector((math.cos(a_), math.sin(a_)))
def board_lift(f):
    return smooth((f - 1998) / 22.0)
CARRY_H = 0.82
def board_matrix(f):
    c = board_xy(f).to_2d(); hd = board_hd(f)
    ga, gb = ground_z(*(c + hd * 1.35)), ground_z(*(c - hd * 1.35))
    lie_z = ground_z(c.x, c.y) + 0.035
    car_z = (ga + gb) / 2 + CARRY_H
    z = lie_z + (car_z - lie_z) * board_lift(f)
    raw = math.atan2((ga - gb) * board_lift(f), 2.7) if board_lift(f) > 0 else math.atan2(ground_z(*(c + hd * 0.8)) - ground_z(*(c - hd * 0.8)), 1.6)
    pitch = max(-R_(8), min(R_(8), raw))       # carriers keep it nearly level; their arms take up the difference
    R = Matrix.Rotation(math.atan2(hd.y, hd.x) - math.pi / 2, 3, 'Z') @ Matrix.Rotation(pitch, 3, 'X')
    return Matrix.Translation(Vector((c.x, c.y, z))) @ R.to_4x4()
BOARD = bpy.data.objects["SpineBoard"]
BOARD.rotation_mode = 'XYZ'
for f in [1] + list(range(1996, 2150, 4)) + [2149]:
    ff = max(f, 1996)
    M = board_matrix(ff)
    BOARD.matrix_world = M
    BOARD.keyframe_insert("location", frame=f); BOARD.keyframe_insert("rotation_euler", frame=f)
for f_, h_ in ((1, True), (1972, False), (2150, True)):
    BOARD.hide_render = h_; BOARD.keyframe_insert("hide_render", frame=f_)
# farmer: shifted out of the crater onto the board, then carried lying on it, arms across his chest
P(1980, LIE_POS, yaw=LYAW, pitch=-90, roll=6, spine=(6, 0, 0), head=(8, -6, 0), jaw=2, **SPREAD)
def on_board(f, extra=None):
    M = board_matrix(f); hd = board_hd(f).to_3d()
    pel = M.translation + Vector((0, 0, 0.028 + 0.10)) - hd * 0.12
    yaw = math.degrees(math.atan2(hd.y, hd.x)) - 90
    tilt = math.degrees(math.asin(max(-1, min(1, (M.to_3x3() @ Vector((0, 1, 0))).z))))
    P(f, pel, yaw=yaw, pitch=-90 + tilt, spine=(8, 0, 0), head=(10, 0, 0), jaw=2,
      legs={"L": (0, 3, 4, 8), "R": (2, 3, 6, 8)}, arms={"L": ("pt", "chest_x"), "R": ("pt", "chest_x")})
P(1988, (LIE_POS + Vector((BC0.x - HD2.x * 0.12, BC0.y - HD2.y * 0.12, LIE_POS.z + 0.12))) / 2 + Vector((0, 0, 0.06)),
  yaw=math.degrees(ang0) - 90, pitch=-90, roll=10, spine=(8, 0, 0), head=(10, 0, 0), jaw=4,
  legs={"L": (0, 6, 8, 8), "R": (2, 6, 10, 8)}, arms={"L": ("pt", "chest_x"), "R": ("rest", dict(fwd=-4, out=20, L=0.46))})
for f in (1996, 2006, 2018, 2034, 2050, 2066, 2082, 2098, 2114, 2130, 2149):
    on_board(f)
# B14 hospital bed: lying flat on his back, head on the pillow (toward +Y), turning to the window (+X = his left)
BED = bpy.data.objects["Hospital_Bed"]
bpy.context.view_layer.update()
_hit, _loc, _n, _i = BED.ray_cast(BED.matrix_world.inverted() @ Vector((HX.x + 1.0, 0.45, 3.0)), Vector((0, 0, -1)))
MTOP = (BED.matrix_world @ _loc).z if _hit else 0.62
print("BED mattress top", round(MTOP, 3))
BED_PEL = Vector((HX.x + 1.0, 0.56, MTOP + 0.10))
for f, hd, jw, armL in ((2150, (10, 8, 0), 1, (8, 14)), (2230, (10, 30, 0), 2, (8, 14)), (2290, (9, 48, 0), 6, (14, 18)), (2340, (9, 52, 0), 8, (16, 20))):
    P(f, BED_PEL, yaw=0, pitch=-90, spine=(6, 0, 0), head=hd, jaw=jw,
      legs={"L": (0, 4, 3, 8), "R": (0, 4, 3, 8)},
      arms={"L": ("rest", dict(fwd=armL[0], out=armL[1], L=0.46)), "R": ("rest", dict(fwd=6, out=12, L=0.46))})
# pillow on the mattress, blanket draped over him from the feet to the chest
pillow = bpy.data.objects["Hosp_Pillow"]
_pc = sum((pillow.matrix_world @ Vector(c) for c in pillow.bound_box), Vector()) / 8
pillow.location += Vector((HX.x + 1.0, BED_PEL.y + 0.70, MTOP + 0.065)) - _pc       # mesh has its position baked in
blanket = bpy.data.objects["Hosp_Blanket"]
blanket.location = Vector((HX.x + 1.0, BED_PEL.y - 0.42, MTOP))
for v in blanket.data.vertices:
    ax = abs(v.co.x)
    top = 0.27 if v.co.y < 0.45 else 0.27 - (v.co.y - 0.45) * 0.35    # lower over the chest edge
    drop = smooth((ax - 0.27) / 0.24)
    v.co.z = top * (1 - drop) + 0.015 + 0.012 * math.sin(v.co.y * 23) * (1 - drop)
# clothes: overalls on the farm, gown in the hospital
for nm, show_from, hide_from in (("Farmer.male_worksuit01", 1, 2150), ("Farmer.male_casualsuit06", 2150, None)):
    o = bpy.data.objects[nm]
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False; o.keyframe_insert("hide_render", frame=show_from)
    if hide_from:
        o.hide_render = True; o.keyframe_insert("hide_render", frame=hide_from)
POSES.sort(key=lambda x: x[0])
for f, p in POSES:
    key_body(f, p)
# the move into the hospital is a teleport hidden in the sky tilt: hold constant across 2149->2150
for f, p in POSES:
    key_hands(f, p)
print("FARMER keyed poses", len(POSES))

# ------------------------------------------------------------------ body cast in the heap (shape key) + splash
heap = bpy.data.objects["ManureHeap"]
if not heap.data.shape_keys:
    heap.shape_key_add(name="Basis", from_mix=False)
imp = heap.shape_key_add(name="Imprint", from_mix=False)
ev(116)
def seg(a, b, r):
    return (a.copy(), b.copy(), r)
PBf = FR.PB
SEGS = [seg(PBf["spine05"].head, PBf["spine01"].tail, 0.15), seg(PBf["spine05"].head, PBf["upperleg01.L"].head, 0.13),
        seg(PBf["spine05"].head, PBf["upperleg01.R"].head, 0.13), seg(PBf["neck01"].head, PBf["head"].tail, 0.09)]
for s_ in "LR":
    SEGS += [seg(PBf["upperarm01." + s_].head, PBf["lowerarm01." + s_].head, 0.06), seg(PBf["lowerarm01." + s_].head, PBf["wrist." + s_].head, 0.05),
             seg(PBf["wrist." + s_].head, PBf["finger3-3." + s_].tail, 0.045),
             seg(PBf["upperleg01." + s_].head, PBf["lowerleg01." + s_].head, 0.09), seg(PBf["lowerleg01." + s_].head, PBf["foot." + s_].head, 0.065),
             seg(PBf["foot." + s_].head, PBf["foot." + s_].tail + (PBf["foot." + s_].tail - PBf["foot." + s_].head) * 1.6, 0.055)]
def seg_d(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    q = a + ab * t
    return (Vector((p.x, p.y)) - Vector((q.x, q.y))).length, q
for i, v in enumerate(heap.data.vertices):
    co = imp.data[i].co
    newz = co.z; rim = 0.0
    for a_, b_, r in SEGS:
        d, q = seg_d(co, a_, b_)
        floor_z = q.z - 0.55 * r
        if d < 1.35 * r:
            w = 1.0 if d < r else 1.0 - smooth((d - r) / (0.35 * r))
            newz = min(newz, co.z + (floor_z - co.z) * w) if floor_z < co.z else newz
        elif d < 3.2 * r and co.z > q.z - r * 2.0:
            # displaced muck banked up against his sides
            rim = max(rim, 0.13 * math.sin(math.pi * (d - 1.35 * r) / (1.85 * r)) ** 0.7)
    imp.data[i].co.z = newz + rim
for f, v in ((1, 0.0), (91, 0.0), (95, 1.0)):
    imp.value = v; imp.keyframe_insert("value", frame=f)
print("HEAP imprint carved")
# splash: muck clods thrown out on impact, ballistic, landing on the surface
import random
rnd = random.Random(11)
muck = bpy.data.materials.get("M_Manure_Heap")
clods = bpy.data.collections.new("Splash_Clods"); sc.collection.children.link(clods)
ev(140)
for k in range(44):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.012, 0.035))
    c = bpy.context.active_object; c.name = "Clod_%02d" % k
    c.scale = (1.0, rnd.uniform(0.6, 1.0), rnd.uniform(0.45, 0.8))
    c.data.materials.append(muck)
    for cc in c.users_collection: cc.objects.unlink(c)
    clods.objects.link(c)
    ang = rnd.uniform(0, 2 * math.pi); sp = rnd.uniform(0.8, 2.6); up = rnd.uniform(1.2, 3.0)
    start = LIE_POS + Vector((math.cos(ang) * 0.25 + rnd.uniform(-0.3, 0.3), math.sin(ang) * 0.18, -0.02))
    vel = Vector((math.cos(ang) * sp, math.sin(ang) * sp, up))
    spin = Vector((rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(-12, 12)))
    c.hide_render = True; c.keyframe_insert("hide_render", frame=1)
    c.hide_render = False; c.keyframe_insert("hide_render", frame=92)
    t = 0.0; f = 92; landed = False
    while not landed and f < 150:
        t = (f - 92) / 60.0
        p = start + vel * t + Vector((0, 0, -4.905 * t * t))
        gzc = ground_z(p.x, p.y)
        if p.z <= gzc and f > 94:
            p.z = gzc + 0.008; landed = True
        c.location = p; c.rotation_euler = spin * min(t, 0.4)
        c.keyframe_insert("location", frame=f); c.keyframe_insert("rotation_euler", frame=f)
        f += 2
    for cc_f, h in ((2149, False), (2150, True)):
        c.hide_render = h; c.keyframe_insert("hide_render", frame=cc_f)
ev(116)
for k, (bone, t, off) in enumerate((("lowerleg01.L", 0.4, 0.05), ("lowerleg01.R", 0.6, 0.05), ("upperleg02.L", 0.5, 0.07), ("upperleg02.R", 0.3, 0.07),
                                    ("lowerarm01.L", 0.5, 0.04), ("upperarm02.R", 0.6, 0.05), ("spine03", 0.5, 0.11), ("lowerleg02.R", 0.3, 0.045),
                                    ("upperarm02.L", 0.4, 0.05), ("spine04", 0.3, 0.12))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=rnd.uniform(0.02, 0.04))
    c = bpy.context.active_object; c.name = "Clod_On_%02d" % k; c.scale = (1.3, 1.0, 0.5); c.data.materials.append(muck)
    for cc in c.users_collection: cc.objects.unlink(c)
    clods.objects.link(c)
    pb = FR.PB[bone]; pt = F.matrix_world @ pb.head.lerp(pb.tail, t)
    c.location = pt + Vector((0, 0, off))
    con = c.constraints.new('CHILD_OF'); con.target = F; con.subtarget = bone
    con.inverse_matrix = (F.matrix_world @ pb.matrix).inverted()
    for ff, h in ((1, True), (93, False), (2010, True)):
        c.hide_render = h; c.keyframe_insert("hide_render", frame=ff)
print("SPLASH clods", len(clods.objects))

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
ev(86)
fd = fork.data; pts_ = [v.co for v in fd.vertices]
ext_ = [max(p[i] for p in pts_) - min(p[i] for p in pts_) for i in range(3)]
long_ax = max(range(3), key=lambda i: ext_[i])
fx, fy = fork.location.x, fork.location.y
yaw_f = R_(35)
dirv = Vector((math.cos(yaw_f), math.sin(yaw_f), 0))
ga, gb = ground_z(*(Vector((fx, fy)) + dirv.to_2d() * 0.65)), ground_z(*(Vector((fx, fy)) - dirv.to_2d() * 0.65))
slope = math.atan2(ga - gb, 1.3)
base_rot = {0: Matrix.Identity(3), 1: Matrix.Rotation(R_(-90), 3, 'Z'), 2: Matrix.Rotation(R_(90), 3, 'Y')}[long_ax]
Rf = Matrix.Rotation(yaw_f, 3, 'Z') @ Matrix.Rotation(-slope, 3, 'Y') @ base_rot
fork.rotation_euler = Rf.to_euler(); fork.location = (fx, fy, (ga + gb) / 2 + 0.018)
fork.keyframe_insert("location", frame=86); fork.keyframe_insert("rotation_euler", frame=86)

# =============================================================== COW: charge, impact, stop, turn away
C = bpy.data.objects["cow_rig"]; C.location = (0, 0, 0); CR = Rig(C)
for pb in C.pose.bones: pb.rotation_mode = 'QUATERNION'
cow_path = pchip([(1, -9.3), (34, -4.75), (60, -4.05), (80, -3.95)])
quad_move(CR, lambda f: Vector((cow_path(f), -0.55, 0)), 1, 80, stride=1.6, gait="trot", lift=0.14, body_bob=0.03,
          heading_fn=lambda f: R_(90))
cow_exit = catmull([(81, Vector((-3.95, -0.55, 0))), (150, Vector((-4.15, -1.25, 0))), (230, Vector((-4.6, -2.9, 0)))])
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
ev(400)
G = bpy.data.objects["goat_rig"]; G.location = (0, 0, 0); GR = Rig(G)
for pb in G.pose.bones: pb.rotation_mode = 'QUATERNION'
HEAD_W_POS = LIE_POS.to_2d() + HEAD_DIR * 0.85          # his head (world xy)
RSIDE = Vector((-HEAD_DIR.y, HEAD_DIR.x))                 # his right side (+Y-ish)
gz = lambda v: ground_z(v.x, v.y)
G_RIDGE = Vector((2.5, 3.2)); G_TOP = Vector((1.35, 1.35)); G_HEAD = HEAD_W_POS + RSIDE * 0.62 + HEAD_DIR * 0.25
quad_hold(GR, 1, G_RIDGE.to_3d(), R_(150))
quad_hold(GR, 880, G_RIDGE.to_3d(), R_(150))
# she is not in the story until "his goat found him": hidden until then (comes up over the far side of the heap)
for ob in [G] + list(G.children):
    for f_, h_ in ((1, True), (875, False)):
        ob.hide_render = h_; ob.keyframe_insert("hide_render", frame=f_)
# natural head carriage while walking (neck forward/down, not straight up)
for f, nk in ((1, (30, 0)), (880, (34, 0)), (930, (44, 0)), (975, (40, 0)), (1040, (28, 0)), (1080, (14, 0))):
    for n in ("neck1", "neck2"):
        GR.key_rot(n, f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
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
G_SIDE = LIE_POS.to_2d() + RSIDE * 0.62 + HEAD_DIR * 0.1
gp2 = catmull([(1176, G_HEAD.to_3d()), (1215, (G_HEAD + G_SIDE) .to_3d() / 2 + RSIDE.to_3d() * 0.25), (1250, G_SIDE.to_3d())])
quad_move(GR, gp2, 1176, 1250, stride=0.38, gait="walk", lift=0.05, body_bob=0.006)
h_side = math.atan2(-HEAD_DIR.x, HEAD_DIR.y) + math.pi          # facing along -HEAD_DIR (toward his feet)
quad_hold(GR, 1252, G_SIDE.to_3d(), h_side)
for k in LEGS:
    GR.key_rot("neck1", 1252, [("X", 10)])
# lie down 1252 -> 1300 (front first, then hind), stays down until 1500
TR = GR.rest("torso"); Hg = TR.translation.z
def goat_rigid(f, pos2, h, roll, drop, neck=(0, 0)):
    """move the whole goat rigidly (torso + all hoof targets): lying on her side keeps the legs undeformed"""
    Rh = Matrix.Rotation(h, 3, 'Z')
    fwd = Rh @ Vector((0, -1, 0))
    Rr = Matrix.Rotation(roll, 3, fwd)
    base = gz(pos2.to_3d())
    centre = Vector((pos2.x, pos2.y, base + Hg - drop))
    Mt = Matrix.Translation(centre) @ (Rr @ Rh).to_4x4() @ Matrix.Translation(-TR.translation) @ TR
    GR.key_world("torso", f, Mt)
    for k in LEGS:
        n = "IK_hoof." + k
        GR.key_world(n, f, Mt @ TR.inverted() @ GR.rest(n))
# roll so that her back faces him (he is on the -RSIDE side of her)
_fwd = Matrix.Rotation(h_side, 3, 'Z') @ Vector((0, -1, 0))
ROLL = R_(82) if (Matrix.Rotation(R_(82), 3, _fwd) @ Vector((0, 0, 1))).to_2d().dot(-RSIDE) > 0 else R_(-82)
BELLY_DROP = 0.25
FOLD = {  # FK fold for sternal lying (deg about the world-aligned X axis of each bone, + = tip swings back)
    "F": [("upper", 22, 0), ("lower", -100, 0), ("cannon", 168, 0), ("hoof", 25, 0)],
    "H": [("upper", -58, 12), ("lower", 128, 0), ("cannon", -112, 0), ("hoof", -15, 0)]}
def goat_lying(f, dz, fold):
    """dz: torso drop, fold 0..1: IK legs (standing) -> FK folded legs"""
    goat_rigid(f, G_SIDE, h_side, 0.0, dz)
    for k in LEGS:
        sx = 1 if k.endswith("L") else -1
        for part, ang, splay in FOLD[k[0]]:
            GR.key_rot("%s.%s" % (part, k), f, [("Y", sx * splay * fold), ("X", ang * fold)])
        for cn, bone in (("IK", "cannon." + k), ("Copy Rotation", "hoof." + k)):
            c = GR.PB[bone].constraints[cn]; c.influence = 1.0 - fold; c.keyframe_insert("influence", frame=f)
goat_lying(1262, 0.0, 0.0)
goat_lying(1276, 0.10, 0.45)
goat_lying(1300, BELLY_DROP, 1.0)
goat_lying(1500, BELLY_DROP, 1.0)
for f, nk in ((1262, (14, 0)), (1305, (26, 34)), (1388, (30, 40)), (1500, (28, 36))):
    GR.key_rot("neck1", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)]); GR.key_rot("neck2", f, [("X", nk[0] * 0.5), ("Z", nk[1] * 0.5)])
# B10/B11 stand up and present the udder by his chest (facing his feet, hind end at his chest)
goat_lying(1530, 0.12, 0.45)
goat_lying(1552, 0.0, 0.0)
G_MILK = LIE_POS.to_2d() + RSIDE * 0.60 + HEAD_DIR * 0.30
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
G_WIN = Vector((HX.x + 3.86, 0.0, 0))
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
# ------------------------------------------------------------------ udder for the goat (milking), attached to the hips bone
GB = bpy.data.objects["goat_body"]
_hy = G.data.bones["upper.HL"].head_local.y
_cands = [v for v in GB.data.vertices if abs(v.co.x) < 0.035 and _hy - 0.16 < v.co.y < _hy + 0.02]
UDDER_V = min(_cands, key=lambda v: v.co.z).index
ev(1601)
_dg = bpy.context.evaluated_depsgraph_get(); _me = GB.evaluated_get(_dg).to_mesh()
_ub = GB.matrix_world @ _me.vertices[UDDER_V].co
GB.evaluated_get(_dg).to_mesh_clear()
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=1.0)
udder = bpy.context.active_object; udder.name = "Goat_Udder"
udder.scale = (0.055, 0.068, 0.05); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for sx_ in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.016, radius2=0.010, depth=0.05, location=(sx_ * 0.028, -0.01, -0.07))
    t_ = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT'); t_.select_set(True); udder.select_set(True)
    bpy.context.view_layer.objects.active = udder; bpy.ops.object.join()
bpy.ops.object.shade_smooth()
um = bpy.data.materials.new("M_Goat_Udder"); um.use_nodes = True
up_ = um.node_tree.nodes["Principled BSDF"]; up_.inputs['Base Color'].default_value = (0.46, 0.27, 0.19, 1)
up_.inputs['Subsurface Weight'].default_value = 0.3; up_.inputs['Roughness'].default_value = 0.55
udder.data.materials.append(um)
_hdir = Matrix.Rotation(h_side, 3, 'Z')
_fw = _hdir @ Vector((0, -1, 0))
udder.matrix_world = Matrix.Translation(_ub + _fw * 0.09 + Vector((0, 0, -0.01))) @ _hdir.to_4x4()   # under the belly, ahead of the hind legs
uc = udder.constraints.new('CHILD_OF'); uc.target = G; uc.subtarget = "hips"
uc.inverse_matrix = (G.matrix_world @ G.pose.bones["hips"].matrix).inverted()
for ob_, f_, h_ in ((udder, 1, True), (udder, 875, False), (udder, 2150, True)):
    ob_.hide_render = h_; ob_.keyframe_insert("hide_render", frame=f_)
UDDER_TEAT_LOCAL = Vector((-0.028, -0.01, -0.095))
print("UDDER placed")
exec(open(os.path.join(HERE, "03c_medics.py")).read())
for o in (G, F, BOARD):
    stepped(o, {2149})

print("ANIM_DONE")
exec(open(os.path.join(HERE, "03b_effects_lights_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
