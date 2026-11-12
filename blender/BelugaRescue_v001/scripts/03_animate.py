"""BelugaRescue animation: diver, beluga, spectators, keeper, props.  (03b adds FX, lights and the camera.)
blender -b work/scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, json
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
V = lambda *a: Vector(a)
WATER_Z, DECK_Z = 6.0, 6.25
BEAT = {1: 1, 2: 169, 3: 265, 4: 523, 5: 661, 6: 775, 7: 925, 8: 1213, 9: 1375, 10: 1699, 11: 1885, 12: 2053}
END = 2190
GROUND = [0.0]
def ground_z(x, y):            # anim_lib walkers use this; set GROUND[0] per character
    return GROUND[0]

# =============================================================== human control (FK legs/spine, IK arms) — pattern from goat_rescue2
SPINE_W = {"spine05": 0.12, "spine04": 0.18, "spine03": 0.22, "spine02": 0.26, "spine01": 0.22}
HEAD_W = {"neck01": 0.25, "neck02": 0.25, "neck03": 0.2, "head": 0.3}
JW = (0.8, 1.1, 0.8)

class H:
    def __init__(self, name):
        o = bpy.data.objects[name]; self.o = o
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.selected_objects: x.select_set(False)
        o.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        eb = o.data.edit_bones
        for s in "LR":
            src = eb["wrist." + s]; b = eb.new("IK_hand." + s)
            b.head, b.tail, b.roll = src.head.copy(), src.tail.copy(), src.roll; b.use_deform = False; b.parent = None
            el = eb["lowerarm01." + s].head.copy(); sx = 1 if s == "L" else -1
            p = eb.new("Pole_elbow." + s); p.head = el + Vector((0.25 * sx, 0.55, -0.1)); p.tail = p.head + Vector((0, 0, 0.08))
            p.use_deform = False; p.parent = None
        bpy.ops.object.mode_set(mode='POSE')
        self.R = R = Rig(o)
        for pb in o.pose.bones: pb.rotation_mode = 'QUATERNION'
        self.IKC = {}
        for s in "LR":
            c = R.PB["lowerarm02." + s].constraints.new('IK')
            c.target, c.subtarget = o, "IK_hand." + s
            c.pole_target, c.pole_subtarget = o, "Pole_elbow." + s
            c.chain_count = 4; c.iterations = 200
            self.IKC[s] = c
            for tw in ("upperarm02.", "lowerarm02."):
                p = R.PB[tw + s]; p.lock_ik_x = p.lock_ik_y = p.lock_ik_z = True
            cr = R.PB["wrist." + s].constraints.new('COPY_ROTATION'); cr.target, cr.subtarget = o, "IK_hand." + s
        for s in "LR":
            c = self.IKC[s]; ref = R.BN["lowerarm01." + s].head_local.copy(); best = (0, 9)
            for d in range(-180, 180, 6):
                c.pole_angle = R_(d); ev(); e = (R.PB["lowerarm01." + s].head - ref).length
                if e < best[1]: best = (d, e)
            for d10 in range((best[0] - 6) * 5, (best[0] + 6) * 5):
                c.pole_angle = R_(d10 / 5); ev(); e = (R.PB["lowerarm01." + s].head - ref).length
                if e < best[1]: best = (d10 / 5, e)
            c.pole_angle = R_(best[0])
        bpy.ops.object.mode_set(mode='OBJECT')
        self.ROOT = R.BN["root"].head_local.copy()
        self.SH = {s: R.BN["upperarm01." + s].head_local.copy() for s in "LR"}
        self.ARM = sum(R.BN[b + ".L"].length for b in ("upperarm01", "upperarm02", "lowerarm01", "lowerarm02"))
        self.REST_HAND = {}
        for s in "LR":
            wv = R.BN["wrist." + s].head_local
            d = R.BN["finger3-1." + s].head_local - wv
            a = R.BN["finger2-1." + s].head_local - R.BN["finger5-1." + s].head_local
            n = d.cross(a) if s == "L" else a.cross(d)
            self.REST_HAND[s] = self.hand_basis(s, d, n)
        self.keys = []
    @staticmethod
    def hand_basis(s, d, n):
        d = d.normalized(); n = (n - d * n.dot(d)).normalized()
        a = d.cross(n) if s == "R" else n.cross(d)
        return Matrix((d, a, n)).transposed()
    def hand_matrix(self, s, W, d, n):
        Rm = self.hand_basis(s, d, n) @ self.REST_HAND[s].transposed()
        wr = self.R.BN["wrist." + s].head_local
        return Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-wr) @ self.R.rest("IK_hand." + s)
    def arm_rest(self, s, fwd=0.0, out=8.0, L=None, twist=0.0):
        sx = 1 if s == "L" else -1
        L = 0.9 * self.ARM if L is None else min(L, 0.97 * self.ARM)
        Rr = Matrix.Rotation(R_(-fwd), 3, 'X') @ Matrix.Rotation(R_(-sx * out), 3, 'Y')     # +out = away from the body
        W = self.SH[s] + Vector((sx * 0.04, -0.02, 0)) + Rr @ Vector((0, 0, -L))
        d = Rr @ Vector((sx * 0.05, -0.15, -1.0))
        n = Matrix.Rotation(R_(twist * sx), 3, 'Z') @ (Rr @ Vector((-sx * 0.9, 0.35, 0.0)))
        return W, d, n
    def P(self, f, pos, yaw=0.0, pitch=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0, 0), legs=None, arms=None, jaw=0.0, curl=None):
        self.keys.append((f, dict(pos=Vector(pos), yaw=yaw, pitch=pitch, roll=roll, spine=spine, head=head,
                                  legs=legs or {}, arms=arms or {}, jaw=jaw, curl=curl or {})))
    def key_fingers(self, s, f, curl, thumb=18):
        Rh = self.REST_HAND[s]; d, a = Rh.col[0].copy(), Rh.col[1].copy(); sign = 1 if s == "R" else -1
        for k in range(2, 6):
            c = curl[k - 2] if isinstance(curl, (list, tuple)) else curl
            for j in range(1, 4):
                b = "finger%d-%d.%s" % (k, j, s)
                self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(c * JW[j - 1] * sign), 3, a)))
        for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
            b = "finger1-%d.%s" % (j, s)
            self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(fl * sign), 3, a) @ Matrix.Rotation(R_(22 * sign), 3, d)))
    def body_matrix(self, p):
        Rw = (Matrix.Rotation(R_(p["yaw"]), 3, 'Z') @ Matrix.Rotation(R_(p["pitch"]), 3, 'X') @ Matrix.Rotation(R_(p["roll"]), 3, 'Y'))
        return Matrix.Translation(p["pos"]) @ Rw.to_4x4() @ Matrix.Translation(-self.ROOT)
    def key_body(self, f, p):
        R = self.R
        R.key_world("root", f, self.body_matrix(p) @ R.rest("root"))
        fl, sd, tw = p["spine"]
        for n, w in SPINE_W.items():
            R.key_rot(n, f, [("X", fl * w), ("Y", sd * w), ("Z", tw * w)])
        hp, ht, hr = p["head"]
        for n, w in HEAD_W.items():
            R.key_rot(n, f, [("X", hp * w), ("Y", hr * w), ("Z", ht * w)])
        for s in "LR":
            sx = 1 if s == "L" else -1
            flex, abd, knee, ank = p["legs"].get(s, (0, 4, 4, 0))
            R.key_rot("upperleg01." + s, f, [("Y", -sx * abd), ("X", -flex)])
            R.key_rot("lowerleg01." + s, f, [("X", knee)])
            R.key_rot("foot." + s, f, [("X", -ank)])
        R.key_rot("jaw", f, [("X", -p["jaw"])])
        for s in "LR":
            c = p["curl"].get(s, (22, 18))
            self.key_fingers(s, f, c[0], c[1])
    def key_hands(self, f, p):
        ev(f)
        R = self.R
        M = R.delta("spine01"); R3 = M.to_3x3()
        for s in "LR":
            sx = 1 if s == "L" else -1
            kind, prm = p["arms"].get(s, ("rest", dict()))
            if kind == "body":
                W, d, n = prm["W"], prm["d"], prm["n"]
                R.key_world("IK_hand." + s, f, self.hand_matrix(s, M @ W, R3 @ d, R3 @ n))
                pole = M @ (self.SH[s] + Vector((0.45 * sx, 0.35, -0.3)))
            elif kind == "world":
                W, d, n = prm["W"], prm["d"], prm["n"]
                R.key_world("IK_hand." + s, f, self.hand_matrix(s, W, d, n))
                pole = prm.get("pole", M @ (self.SH[s] + Vector((0.35 * sx, 0.45, -0.25))))
            else:
                W, d, n = self.arm_rest(s, **prm)
                R.key_world("IK_hand." + s, f, self.hand_matrix(s, M @ W, R3 @ d, R3 @ n))
                pole = M @ (self.SH[s] + Vector((0.35 * sx, 0.45, -0.25)))
            nme = "Pole_elbow." + s; pb = R.PB[nme]
            pb.location = R.rest(nme).to_3x3().inverted() @ (pole - R.BN[nme].head_local)
            pb.keyframe_insert("location", frame=f, group=nme)
    def bake(self, world_hands_fn=None):
        self.keys.sort(key=lambda k: k[0])
        for f, p in self.keys: self.key_body(f, p)
        for f, p in self.keys: self.key_hands(f, p)
    def world(self, bone, f, which="head"):
        ev(f); pb = self.o.pose.bones[bone]
        return self.o.matrix_world @ (pb.head if which == "head" else pb.tail)

def arms(l=None, r=None, **both):
    both = dict(both)
    a = {}
    if both: a["L"] = ("rest", dict(both)); a["R"] = ("rest", dict(both))
    if l is not None: a["L"] = ("rest", l) if isinstance(l, dict) else l
    if r is not None: a["R"] = ("rest", r) if isinstance(r, dict) else r
    return a
def legs(l=(0, 4, 4, 0), r=None):
    return {"L": l, "R": r if r is not None else l}

# =============================================================== DIVER
DV = H("Diver"); RZ = DV.ROOT.z         # root height above the soles when standing (≈1.0)
EDGE_Y = -5.0                            # coping inner face
X0 = 0.6
STREAM = arms(fwd=174, out=10, L=0.52)                 # streamline: arms overhead
DOLPH = lambda k: legs((8 + 10 * math.sin(k), 3, 8 + 14 * max(0, math.sin(k + 0.8)), -55), (8 + 10 * math.sin(k), 3, 8 + 14 * max(0, math.sin(k + 0.8)), -55))
# --- beat 1: on the coping, crouch, spring, arc, entry, glide down
DV.P(1, (X0, EDGE_Y + 0.03, DECK_Z + RZ - 0.02), yaw=180, pitch=8, spine=(10, 0, 0), head=(-8, 0, 0), legs=legs((10, 5, 18, 0)), arms=arms(fwd=70, out=12), curl={"L": (10, 10), "R": (10, 10)})
DV.P(22, (X0, EDGE_Y + 0.01, DECK_Z + RZ - 0.18), yaw=180, pitch=30, spine=(28, 0, 0), head=(-15, 0, 0), legs=legs((52, 6, 70, 22)), arms=arms(fwd=-35, out=15), curl={"L": (8, 10), "R": (8, 10)})
DV.P(40, (X0, EDGE_Y + 0.03, DECK_Z + RZ - 0.26), yaw=180, pitch=38, spine=(30, 0, 0), head=(-10, 0, 0), legs=legs((62, 6, 88, 25)), arms=arms(fwd=-45, out=12))
DV.P(54, (X0, EDGE_Y + 0.15, DECK_Z + RZ + 0.25), yaw=180, pitch=55, spine=(5, 0, 0), head=(20, 0, 0), legs=legs((-5, 3, 5, -40)), arms=arms(fwd=150, out=6))
DV.P(66, (X0, EDGE_Y + 0.85, DECK_Z + 1.0), yaw=180, pitch=105, spine=(12, 0, 0), head=(25, 0, 0), legs=legs((6, 3, 10, -50)), arms=STREAM)
DV.P(78, (X0, EDGE_Y + 1.30, WATER_Z - 0.35), yaw=180, pitch=140, spine=(8, 0, 0), head=(20, 0, 0), legs=legs((10, 3, 12, -55)), arms=STREAM)
for i, f in enumerate(range(92, 169, 12)):
    t = (f - 78) / 90.0
    DV.P(f, (X0 + 0.05 * t, EDGE_Y + 1.30 + 1.8 * t, WATER_Z - 0.35 - 2.4 * t), yaw=180, pitch=140 - 6 * t, spine=(6 * math.sin(i), 0, 0), head=(18, 0, 0),
         legs=DOLPH(i * 1.7), arms=STREAM if i < 4 else arms(fwd=150 - 40 * (i % 2), out=20 + 40 * (i % 2)))
# --- beat 2: kicks down, rotates feet-down, settles kneeling on the tiles
DV.P(190, (X0 + 0.1, EDGE_Y + 3.35, 2.9), yaw=180, pitch=128, spine=(5, 0, 0), head=(15, 0, 0), legs=DOLPH(1.0), arms=arms(fwd=100, out=60))
DV.P(212, (X0 + 0.1, EDGE_Y + 3.6, 1.95), yaw=180, pitch=60, spine=(10, 0, 0), head=(5, 0, 0), legs=legs((55, 6, 40, -60)), arms=arms(fwd=60, out=70))
DV.P(232, (X0 + 0.1, EDGE_Y + 3.7, 1.05), yaw=180, pitch=-14, spine=(14, 0, 0), head=(-10, 0, 0), legs=legs((84, 8, 14, -72)), arms=arms(fwd=40, out=60))
SIT_Y = EDGE_Y + 3.75
SIT = (X0 + 0.1, SIT_Y, 0.13)
DV.P(252, (X0 + 0.1, SIT_Y, 0.38), yaw=180, pitch=-8, spine=(12, 0, 0), head=(5, 0, 0), legs=legs((84, 8, 12, -72)), arms=arms(fwd=35, out=50))
DV.P(264, SIT, yaw=180, pitch=-10, spine=(18, 0, 0), head=(10, 0, 0), legs=legs((86, 8, 8, -72)), arms=arms(fwd=30, out=40))
# --- beat 3: cramps — knees jerk, toes lock, hands clutch the right calf
CALF_HOLD = lambda f: None
for k, f in enumerate(range(276, 520, 16)):
    j = (k % 2)
    kn_r = 22 if j else 4; kn_l = 14 if (k % 3 == 0) else 4
    DV.P(f, (SIT[0], SIT[1] + 0.02 * j, SIT[2] + 0.01 * j), yaw=180, pitch=-6 + 6 * j, roll=3 * (j * 2 - 1), spine=(34 + 10 * j, 4 * (j * 2 - 1), 0),
         head=(18, 6 * (j * 2 - 1), 0), legs=legs((92 + 0.5 * kn_l, 8, kn_l, -82), (92 + 0.6 * kn_r, 10, kn_r, -84)), jaw=4 + 4 * j,
         arms={"L": ("calf", dict(s="L", t=0.45)), "R": ("calf", dict(s="R", t=0.6))}, curl={"L": (62, 40), "R": (62, 40)})
# --- beat 4: claws upward, legs locked, rises, sinks back
DV.P(523, SIT, yaw=180, pitch=-8, spine=(30, 0, 0), head=(-10, 0, 0), legs=legs((86, 8, 10, -72)), arms=arms(fwd=120, out=30))
for k, f in enumerate(range(535, 610, 15)):
    up = k / 5.0
    DV.P(f, (SIT[0], SIT[1] - 0.15 * up, SIT[2] + 0.75 * up), yaw=180, pitch=-28 * up - 8, spine=(-8, 0, 0), head=(-35, 0, 0),
         legs=legs((60 - 30 * up, 6, 4, -74)), arms=arms(fwd=175 if k % 2 == 0 else 95, out=8 if k % 2 == 0 else 80), jaw=10, curl={"L": (45, 30), "R": (45, 30)})
for k, f in enumerate(range(620, 661, 10)):
    dn = (k + 1) / 4.0
    DV.P(f, (SIT[0], SIT[1] - 0.15 + 0.12 * dn, SIT[2] + 0.75 * (1 - dn)), yaw=180, pitch=-36 + 26 * dn, spine=(-5 + 20 * dn, 0, 0), head=(-40 + 20 * dn, 0, 0),
         legs=legs((40 + 46 * dn, 6, 6, -72)), arms=arms(fwd=150 - 60 * dn, out=40 + 20 * dn), jaw=8)
# --- beat 5: drowning — head back toward the light, chest heaving, last bubbles
for k, f in enumerate(range(672, 775, 17)):
    j = k % 2
    DV.P(f, (SIT[0], SIT[1] - 0.03, SIT[2] + 0.02 * j), yaw=180, pitch=-14 - 4 * j, spine=(-6 + 10 * j, 0, 0), head=(-38 + 8 * j, 8 * (j - 0.5), 0),
         legs=legs((84, 8, 12, -70), (84, 9, 18, -70)), arms=arms(l=dict(fwd=110 + 30 * j, out=70), r=dict(fwd=50 + 40 * j, out=75)), jaw=12 - 6 * j)
# --- beats 6–8: weakening, drifting up off the tiles, limp (legs trail forward-down)
FLOAT = lambda f, t: (SIT[0], SIT[1] - 0.05 - 0.15 * t, SIT[2] + 0.95 * t)
for k, f in enumerate(range(790, 1380, 30)):
    t = min(1.0, (f - 790) / 520.0)
    DV.P(f, FLOAT(f, t), yaw=180 + 8 * math.sin(k * 0.5), pitch=-14 + 30 * t, roll=4 * math.sin(k * 0.7), spine=(-4 + 14 * t, 0, 3 * math.sin(k)),
         head=(-30 + 50 * t, 6 * math.sin(k * 0.6), 0), legs=legs((84 - 30 * t, 8, 12 + 20 * t, -60), (84 - 50 * t, 10, 18 + 72 * t, -40)),
         arms=arms(l=dict(fwd=70 + 20 * math.sin(k), out=55 + 15 * t), r=dict(fwd=60 + 20 * math.cos(k), out=60 + 10 * t)), jaw=6,
         curl={"L": (30, 20), "R": (30, 20)})
# --- beats 9–11: held by the ankle (right knee bent, shin across the mouth), pushed up, breaks the surface
RISE = [(1380, FLOAT(0, 1.0)[2]), (1440, FLOAT(0, 1.0)[2] + 0.05), (1500, 1.6), (1600, 2.6), (1699, 3.4), (1800, 4.6), (1884, 5.0), (1915, 5.55), (1950, 5.6), (1990, 5.3)]
RZF = pchip([(f, z) for f, z in RISE])
XY0 = Vector(FLOAT(0, 1.0)[:2]); XY1 = Vector((X0 + 0.25, EDGE_Y + 1.2))
for k, f in enumerate(range(1380, 2000, 20)):
    t = smooth((f - 1380) / 560.0)
    xy = XY0.lerp(XY1, t)
    limp = 1.0 if f < 1915 else max(0.0, 1 - (f - 1915) / 40.0)
    DV.P(f, (xy.x, xy.y, RZF(f)), yaw=180 + 10 * math.sin(k * 0.3), pitch=6 + 10 * limp, roll=6 * math.sin(k * 0.4), spine=(10 * limp - 12 * (1 - limp), 0, 0),
         head=(25 * limp - 30 * (1 - limp), 0, 0), legs=legs((62 + 8 * math.sin(k * 0.8), 22, 100 + 10 * math.sin(k * 0.8), -45), (35, 14, 95, -20)),
         arms=arms(l=dict(fwd=50 + 30 * limp * math.sin(k * 0.9), out=70 - 20 * (1 - limp)), r=dict(fwd=40 + 30 * limp * math.cos(k * 0.9), out=75 - 20 * (1 - limp))),
         jaw=4 if limp > 0.5 else 22)
# --- beat 12: gasps, swims to the coping, clings with both hands
COP_Z = DECK_Z + 0.06; COP_Y = EDGE_Y + 0.0
for k, f in enumerate(range(2000, 2191, 15)):
    t = min(1.0, (f - 2000) / 80.0)
    y = XY1.y - 0.86 * smooth(t)
    gasp = k % 2
    DV.P(f, (XY1.x, y, 5.52 + 0.16 * smooth(t) - 0.03 * gasp + 0.1 * (1 - t)), yaw=180, pitch=-4 - 14 * t, spine=(4 + 10 * t + 6 * gasp, 0, 0), head=(-18 + 12 * gasp, 6 * math.sin(k), 0),
         legs=legs((25 + 15 * math.sin(k), 8, 40 + 20 * math.sin(k), -40), (30 - 15 * math.sin(k), 8, 45 - 20 * math.sin(k), -40)),
         arms=({"L": ("coping", dict(s="L")), "R": ("coping", dict(s="R"))} if t >= 1.0 else arms(fwd=110 - 40 * gasp, out=40)),
         jaw=26 if gasp else 12, curl={"L": (35, 25), "R": (35, 25)} if t >= 1.0 else {})
# resolve special arm kinds after body keys exist
_key_hands_base = DV.key_hands
def diver_hands(f, p):
    a = dict(p["arms"]); p = dict(p); p["arms"] = a
    for s, (kind, prm) in list(a.items()):
        if kind == "calf":
            ev(f)
            k0 = DV.world("lowerleg01.R", f); k1 = DV.world("foot.R", f)
            c = k0.lerp(k1, prm["t"])
            sx = 1 if s == "L" else -1
            out = (k1 - k0).cross(Vector((0, 0, 1))).normalized() * sx
            W = c + out * 0.16 + Vector((0, 0, 0.1))
            a[s] = ("world", dict(W=W, d=(k1 - k0).normalized() * 0.85 + Vector((0, 0, -1)) * 0.15, n=-out * 0.6 + Vector((0, 0, -0.8)), pole=W + Vector((sx * 0.3, 0, 0.5))))
        elif kind == "coping":
            sx = 1 if s == "L" else -1
            W = Vector((XY1.x + sx * 0.24, COP_Y + 0.1, COP_Z + 0.062))
            a[s] = ("world", dict(W=W, d=Vector((0, -1, -0.15)), n=Vector((0, 0, -1)), pole=W + Vector((sx * 0.6, 0.45, -0.3))))
    _key_hands_base(f, p)
DV.key_hands = diver_hands
DV.bake()
# floor solver: near the tiles, lift/lower each key so the lowest point of body + fins rests on the floor (2–5 mm)
def lowest(f):
    ev(f); dg = bpy.context.evaluated_depsgraph_get(); z = 9.0
    for o in [bpy.data.objects["Diver.body"]] + [o for o in bpy.data.objects if o.name.startswith(("Diver.FootPocket", "Diver.FinBlade")) and not o.name.endswith("loose") and not (o.name.endswith("_R") and "Fin" in o.name and f >= 589)]:
        if o.hide_render: continue
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
        z = min(z, min((mw @ v.co).z for v in list(me.vertices)[::3])); e.to_mesh_clear()
    return z
SEAT = (240, 522)
for it in range(2):
    adj = 0
    for f, p in DV.keys:
        if f <= 45:                       # standing / crouching on the deck
            lo = lowest(f); p["pos"].z += DECK_Z + 0.063 - lo; adj += 1; continue
        if p["pos"].z > 1.6: continue
        lo = lowest(f)
        if (SEAT[0] <= f <= SEAT[1]) or (f < 1600 and lo < 0.01):
            p["pos"].z += (0.004 if (SEAT[0] <= f <= SEAT[1]) else 0.02) - lo; adj += 1
    D_ = DV.o
    D_.animation_data_clear()
    DV.bake()
    print("FLOOR pass", it, "adjusted", adj)
print("DIVER keyed", len(DV.keys))

# right fin comes off during the struggle (beat 4) and sinks to the tiles; the left stays on
finR = bpy.data.objects["Diver.FinBlade_R"]
ev(588)
mw = finR.matrix_world.copy()
# rebuild as a separate world-space duplicate that takes over at frame 589
finR2 = finR.copy(); finR2.data = finR.data; finR2.name = "Diver.FinBlade_R_loose"; sc.collection.objects.link(finR2)
finR2.parent = None; finR2.matrix_world = mw
for f_, h in ((1, True), (589, False)):
    finR2.hide_render = h; finR2.hide_viewport = h; finR2.keyframe_insert("hide_render", frame=f_); finR2.keyframe_insert("hide_viewport", frame=f_)
for f_, h in ((1, False), (589, True)):
    finR.hide_render = h; finR.keyframe_insert("hide_render", frame=f_)
loc0 = mw.translation.copy(); q0 = mw.to_quaternion()
for f_, dz, ang in ((589, 0, 0), (610, -0.25, 25), (640, -0.55, 60), (680, -0.85, 85)):
    q = Quaternion(Vector((1, 0.3, 0)).normalized(), R_(ang)) @ q0
    finR2.location = loc0 + Vector((0.12 * ang / 85, 0.25 * ang / 85, dz)); finR2.rotation_mode = 'QUATERNION'; finR2.rotation_quaternion = q
    finR2.keyframe_insert("location", frame=f_); finR2.keyframe_insert("rotation_quaternion", frame=f_)
    ev(f_); mz_ = min((finR2.matrix_world @ v.co).z for v in finR2.data.vertices)
    if mz_ < 0.004:
        finR2.location.z += 0.004 - mz_; finR2.keyframe_insert("location", frame=f_)
# settle exactly on the floor: lowest vertex at z = 0.003
ev(680)
mz = min((finR2.matrix_world @ v.co).z for v in finR2.data.vertices)
finR2.location.z -= mz - 0.004; finR2.keyframe_insert("location", frame=680)
for f_ in (681, END): finR2.keyframe_insert("location", frame=f_); finR2.keyframe_insert("rotation_quaternion", frame=f_)

# =============================================================== BELUGA
BR = bpy.data.objects["Beluga_Rig"]; BRR = Rig(BR)
for pb in BR.pose.bones: pb.rotation_mode = 'XYZ'
BEL = bpy.data.objects["Beluga"]
JAWO = bpy.data.objects["Beluga_Jaw"]
def _jaw_tip_z(sign):
    BR.pose.bones["jaw"].rotation_euler = (sign * R_(10), 0, 0); ev()
    z = min((JAWO.matrix_world @ v.co).y for v in JAWO.data.vertices)   # tip = most forward (-Y) vertex
    tip = min(JAWO.data.vertices, key=lambda v: v.co.y); zz = (JAWO.matrix_world @ tip.co).z
    BR.pose.bones["jaw"].rotation_euler = (0, 0, 0); ev(); return zz
JSIGN = 1 if _jaw_tip_z(1) < _jaw_tip_z(-1) else -1
def jaw(f, v):
    b = BR.pose.bones["jaw"]; b.rotation_euler = (JSIGN * R_(17) * v, 0, 0); b.keyframe_insert("rotation_euler", frame=f)
L_W = 4.3
SOCK_LOCAL = Vector((0, -L_W * 0.42 + 0.035 * L_W * 0.94, -0.075))      # in rig rest space (mouth front, on the slit)
def whale_matrix(pos, yaw, climb, roll):
    return Matrix.Translation(pos) @ Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(-climb), 4, 'X') @ Matrix.Rotation(R_(roll), 4, 'Y')
PHASE = {"p": 0.0, "f": 1}
def tail_wave(f, freq, amp=1.0, turn=0.0, neck=(0, 0), head=(0, 0)):
    """vertical fluke beats (travelling wave) + lateral bend 'turn' (deg spread over the body) + neck/head pitch,yaw"""
    PHASE["p"] += 2 * math.pi * freq * (f - PHASE["f"]) / 60.0; PHASE["f"] = f
    ph = PHASE["p"]
    A = (2.0, 3.5, 6.0, 9.0, 13.0, 16.0)
    for k in range(6):
        b = BR.pose.bones["tail%d" % k]
        b.rotation_euler = (R_(amp * A[k] * math.sin(ph - 0.75 * k)), 0, R_(turn * (0.10 + 0.04 * k)))
        b.keyframe_insert("rotation_euler", frame=f)
    mb = BR.pose.bones["melon"]; mw_ = 0.035 * math.sin(ph * 1.0 + 1.3) + 0.02 * math.sin(f * 0.21)
    mb.scale = (1 + mw_, 1 - mw_ * 0.6, 1 + mw_); mb.keyframe_insert("scale", frame=f)
    for nme, (pp, yy) in (("neck", neck), ("head", head)):
        b = BR.pose.bones[nme]; b.rotation_euler = (R_(pp), 0, R_(yy)); b.keyframe_insert("rotation_euler", frame=f)
# free-swim path (before the grab and after the release): (frame, pos, roll, freq, amp, turn, neck, head)
WP = [(1, V(-3.5, 3.2, 3.2), 0, 0.8, 0.6, 0, (0, 0), (0, 0)),
      (300, V(-4.6, -0.5, 3.6), 0, 0.8, 0.6, 8, (0, 0), (0, 0)),
      (600, V(-1.0, 3.8, 4.4), 0, 0.8, 0.6, 8, (0, 0), (0, 0)),
      (775, V(2.6, 3.0, 2.4), -10, 0.9, 0.7, 10, (0, 0), (0, 0)),
      (860, V(2.0, 0.6, 1.8), -15, 1.0, 0.8, 14, (0, 15), (-5, 20)),       # head turns toward her
      (925, V(0.0, -0.9, 2.2), -20, 1.1, 0.8, 18, (0, 10), (0, 15)),
      (1000, V(-1.7, -1.9, 2.25), 10, 0.9, 0.7, 10, (5, -10), (8, -8)),     # bats the ring
      (1060, V(-2.6, -1.6, 2.0), 180, 1.3, 0.9, -10, (0, 0), (0, 0)),       # playful barrel roll
      (1130, V(-2.6, -2.75, 1.65), 0, 0.6, 0.5, 0, (10, 0), (12, 0)),        # nods at the keeper
      (1170, V(-2.5, -2.75, 1.65), 0, 0.6, 0.5, 0, (-8, 0), (-10, 0)),
      (1213, V(-2.2, -2.6, 1.7), 0, 0.7, 0.5, 0, (6, 0), (8, 0)),
      (1260, V(-1.6, -2.6, 1.5), 0, 0.8, 0.6, 20, (0, 25), (0, 25)),        # eye macro, head snaps toward her
      (1330, V(-0.6, -0.6, 0.9), 0, 2.2, 1.4, 0, (0, 0), (0, 0)),           # surges
      (1375, V(-0.2, -0.3, 0.8), 0, 1.6, 1.0, 0, (0, 0), (0, 0))]
fp = catmull([(w[0], w[1]) for w in WP])
froll = pchip([(w[0], float(w[2])) for w in WP])
def wp_at(f, idx):
    for (a, b) in zip(WP, WP[1:]):
        if a[0] <= f <= b[0]:
            t = (f - a[0]) / (b[0] - a[0]); va, vb = a[idx], b[idx]
            if isinstance(va, tuple): return tuple(x + (y - x) * smooth(t) for x, y in zip(va, vb))
            return va + (vb - va) * smooth(t)
    return WP[-1][idx]
F_GRAB0, F_GRAB = 1376, 1440
F_REL = 1975
for f in range(1, F_GRAB0, 2):
    p = fp(f); d = (fp(min(f + 3, F_GRAB0)) - fp(max(1, f - 3)))
    if d.length < 1e-4: d = Vector((0, -1, 0))
    d.normalize()
    yaw = math.degrees(math.atan2(d.x, -d.y)); climb = math.degrees(math.asin(max(-1, min(1, d.z))))
    BR.matrix_world = whale_matrix(p, yaw, climb, froll(f))
    BR.keyframe_insert("location", frame=f); BR.rotation_mode = 'QUATERNION'; BR.keyframe_insert("rotation_quaternion", frame=f)
    tail_wave(f, wp_at(f, 3), wp_at(f, 4), wp_at(f, 5), wp_at(f, 6), wp_at(f, 7))
# grab + push: rig solved from her right ankle; whale local X along her shin, nose climbs as height allows
def solve_whale(f, blend_from=None, tb=0.0):
    ev(f)
    an = DV.world("foot.R", f); kn = DV.world("lowerleg01.R", f)
    shin = (an - kn).normalized()
    h = Vector((0, 0, 1)).cross(shin); h.z = 0
    if h.length < 1e-3: h = Vector((1, 0, 0))
    h.normalize()
    pel = DV.world("root", f)
    if (pel - an).to_2d().dot(h.to_2d()) > 0: h = -h          # whale body away from her body
    clim = math.asin(max(0.0, min(0.97, (an.z - 0.6) / 3.9)))
    fwd = (-h * math.cos(clim) + Vector((0, 0, 1)) * math.sin(clim)).normalized()    # nose direction
    fwd = (fwd - shin * fwd.dot(shin)).normalized()
    X = shin; Yl = -fwd; Z = X.cross(Yl).normalized(); X = Yl.cross(Z).normalized()
    Rm = Matrix((X, Yl, Z)).transposed().to_4x4()
    return Matrix.Translation(an) @ Rm @ Matrix.Translation(-SOCK_LOCAL)
jaw(1, 0.0); jaw(1380, 0.0); jaw(1405, 1.0); jaw(1436, 0.6); jaw(F_REL - 10, 0.6); jaw(F_REL + 10, 1.0); jaw(F_REL + 40, 0.1)
for f, v in ((1000, 0.0), (1012, 0.3), (1030, 0.0)):
    jaw(f, v)
from mathutils.bvhtree import BVHTree
ev(1440); _dg = bpy.context.evaluated_depsgraph_get()
def _rig_space_bvh(objs):
    vs, ps = [], []
    Mi = BR.matrix_world.inverted()
    for o in objs:
        e = o.evaluated_get(_dg); me = e.to_mesh(); M = Mi @ o.matrix_world; base = len(vs)
        vs += [M @ v.co for v in me.vertices]; ps += [[base + i for i in p.vertices] for p in me.polygons]
        e.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps)
WLOC = _rig_space_bvh([BEL, bpy.data.objects["Beluga_Jaw"]])      # whale head + jaw in rig space, jaw as held
SOCK = SOCK_LOCAL
def diver_pts(f):
    ev(f); dg = bpy.context.evaluated_depsgraph_get(); an = DV.world("foot.R", f)
    pts, ank = [], []
    for o in [bpy.data.objects["Diver.body"], bpy.data.objects["Diver.FinBlade_L"], bpy.data.objects["Diver.FootPocket_L"], bpy.data.objects["Diver.FootPocket_R"]]:
        e = o.evaluated_get(dg); me = e.to_mesh(); mw = o.matrix_world
        for v in list(me.vertices)[::11]:
            p = mw @ v.co
            (ank if (p - an).length < 0.075 else pts).append(p)
        e.to_mesh_clear()
    return pts, ank
def pen(M, pts, eps=0.005):
    Mi = M.inverted(); c = 0
    for p in pts:
        q = Mi @ p; loc, n, i, d = WLOC.find_nearest(q, 0.6)
        if loc is not None and (q - loc).dot(n) < -eps: c += 1
    return c
ANG = (0, 15, -15, 30, -30, 45, -45, 60, -60, 80, -80, 100, -100, 130, -130, 160, -160, 180)
def rot_about_sock(M, a, phi=0.0):
    return M @ Matrix.Translation(SOCK) @ Matrix.Rotation(R_(a), 4, 'X') @ Matrix.Rotation(R_(phi), 4, 'Z') @ Matrix.Translation(-SOCK)
PHI = (0, 35, -35, 60, -60)
_wl = [v.co.copy() for v in BEL.data.vertices][::25]          # rig-space sample of the body for the floor test
def floor_bad(Mc):
    ps_ = [Mc @ p for p in _wl]
    return max(0.0, 0.5 - min(p.z for p in ps_)) + max(0.0, -4.55 - min(p.y for p in ps_))      # floor (fluke margin) and the window wall
SOL = []; SOLP = []; prev = (0.0, 0.0)
def _app_cost(dv):
    c = 0
    for f_ in (F_GRAB0 + 16, F_GRAB0 + 32, F_GRAB0 + 48):
        t_ = (f_ - F_GRAB0) / (F_GRAB - F_GRAB0)
        Mg = rot_about_sock(solve_whale(F_GRAB), 0, 0); Mt = Matrix.Translation(dv * 2.2 * (1 - smooth(t_))) @ Mg
        pts_, _ = diver_pts(f_); c += pen(Mt, pts_[::3])
        c += 50 * sum(1 for p in _wl if (Mt @ p).y < -4.85 or (Mt @ p).z < 0.1)
    return c
_cands = [Vector((math.cos(R_(a)), math.sin(R_(a)), 0)) for a in range(0, 360, 45)]
APP_DIR = min(_cands, key=_app_cost)
print("HOLD approach dir", tuple(round(x, 2) for x in APP_DIR))
for f in range(F_GRAB, F_REL + 1, 8):
    M = solve_whale(f); pts, ank = diver_pts(f); pts = pts[::2]
    def cost(c):
        a, ph = c; Mc = rot_about_sock(M, a, ph)
        down = (Mc.to_3x3() @ Vector((0, 1, 0))).z
        fb = floor_bad(Mc)
        return (round(fb, 2), 0 if down < -0.25 else 1, pen(Mc, pts), abs(((a - prev[0] + 180) % 360) - 180) + abs(ph - prev[1]))
    best = min([(a, ph) for a in ANG for ph in PHI], key=cost)
    prev = best; SOL.append((f, best[0])); SOLP.append((f, float(best[1])))
# unwrap (no 340-degree spins), then smooth the chosen roll angle about the shin and key the hold
for i in range(1, len(SOL)):
    a = SOL[i][1]
    while a - SOL[i - 1][1] > 180: a -= 360
    while a - SOL[i - 1][1] < -180: a += 360
    SOL[i] = (SOL[i][0], a)
fa_ = pchip([(f, float(a)) for f, a in SOL]); fp_ = pchip(SOLP)
M0 = None
STATS = []
for f in range(F_GRAB0, F_REL + 1, 2):
    a_i, p_i = fa_(max(F_GRAB, f)), fp_(max(F_GRAB, f)); Mb = solve_whale(f)
    M = rot_about_sock(Mb, a_i, p_i)
    if floor_bad(M) > 0:          # interpolation dipped the body into the tiles: nearest roll that clears the floor
        for da in sorted(range(-90, 91, 10), key=abs):
            Mt = rot_about_sock(Mb, a_i + da, p_i)
            if floor_bad(Mt) == 0 and (Mt.to_3x3() @ Vector((0, 1, 0))).z < 0: M = Mt; break
    if f < F_GRAB:      # swims straight in along its own axis, blending off the free path over the first 20 frames
        t = (f - F_GRAB0) / (F_GRAB - F_GRAB0)
        back = APP_DIR
        M = Matrix.Translation(back * 2.2 * (1 - smooth(t))) @ M
        if M0 is None: M0 = BR.matrix_world.copy()
        u = smooth(min(1.0, (f - F_GRAB0) / 20.0))
        loc = M0.translation.lerp(M.translation, u); q = M0.to_quaternion().slerp(M.to_quaternion(), u)
        M = Matrix.Translation(loc) @ q.to_matrix().to_4x4()
    BR.matrix_world = M
    BR.keyframe_insert("location", frame=f); BR.keyframe_insert("rotation_quaternion", frame=f)
    push = 2.0 if 1460 < f < 1930 else 1.0
    tail_wave(f, push, 1.3 if push > 1.5 else 0.8, 0, (0, 0), (0, 0))
    if f >= F_GRAB and f % 40 == 0:
        pts, ank = diver_pts(f); Mi = M.inverted(); ds = []
        for p in ank:
            q = Mi @ p; loc, n, i, d = WLOC.find_nearest(q, 0.5)
            if loc is not None: ds.append((q - loc).dot(n))
        STATS.append((f, pen(M, pts), round(min(ds) * 100, 1) if ds else None, round(sorted(ds)[len(ds) // 2] * 100, 1) if ds else None))
print("HOLD angles", SOL, SOLP)
print("HOLD stats (frame, body pts inside, deepest ankle cm, median ankle cm)", STATS)
# release: swims a circle beside her on the surface (back out of the water, spout)
M_rel = BR.matrix_world.copy()
CIRC_C = Vector((XY1.x - 1.2, XY1.y + 3.0, WATER_Z - 0.22))
for k, f in enumerate(range(F_REL + 2, END + 1, 2)):
    t = (f - F_REL) / (END - F_REL)
    a = R_(200 + 200 * t)
    p = CIRC_C + Vector((math.cos(a) * 1.6, math.sin(a) * 1.4, 0))
    tang = Vector((-math.sin(a) * 1.6, math.cos(a) * 1.4, 0)).normalized()
    yaw = math.degrees(math.atan2(tang.x, -tang.y))
    Mc = whale_matrix(p, yaw, 0, -12)
    if t < 0.25:
        u = smooth(t / 0.25)
        Mc = Matrix.Translation(M_rel.translation.lerp(Mc.translation, u)) @ M_rel.to_quaternion().slerp(Mc.to_quaternion(), u).to_matrix().to_4x4()
    BR.matrix_world = Mc
    BR.keyframe_insert("location", frame=f); BR.keyframe_insert("rotation_quaternion", frame=f)
    tail_wave(f, 0.9, 0.7, 25, (0, 0), (-6, 10))

# ring toy: floats near the window; batted at 1000, flips at 1060
ring = bpy.data.objects["RingToy"]; ring.rotation_mode = 'XYZ'
RK = [(1, V(-2.6, -3.0, 2.2), (80, 0, 0)), (990, V(-2.55, -3.0, 2.25), (80, 0, 30)), (1004, V(-2.5, -3.05, 2.3), (80, 0, 30)),
      (1030, V(-2.9, -3.3, 2.9), (150, 20, 120)), (1070, V(-3.0, -3.4, 2.6), (220, 40, 200)), (1150, V(-3.2, -3.6, 2.1), (260, 30, 260)), (END, V(-3.5, -3.8, 1.5), (300, 30, 300))]
for f, p, r in RK:
    ring.location = p; ring.rotation_euler = tuple(R_(x) for x in r)
    ring.keyframe_insert("location", frame=f); ring.keyframe_insert("rotation_euler", frame=f)

# =============================================================== spectators + keeper
PEOPLE = {}
SOLE = {}
def sole_offset(h):
    if h.o.name not in SOLE:
        z = 0.0
        for ch in h.o.children:
            if ch.type == 'MESH' and "shoes" in ch.name:
                z = min(z, min(v.co.z for v in ch.data.vertices))
        SOLE[h.o.name] = -z
    return SOLE[h.o.name]
def stand(h, f, pos, yaw, spine=(0, 0, 0), head=(0, 0, 0), arms_=None, knee=4, gz=0.0, curl=None):
    if arms_:      # hands at the sides never inside the thighs
        for k_, v_ in list(arms_.items()):
            if v_[0] == "rest" and v_[1].get("fwd", 0) < 40: arms_[k_] = ("rest", dict(v_[1], out=max(v_[1].get("out", 8), 15)))
    gz = gz + sole_offset(h)
    drop = h.R.BN["upperleg02.L"].length * (1 - math.cos(R_(knee))) * 2.0 * 0.5
    h.P(f, (pos[0], pos[1], gz + h.ROOT.z - drop), yaw=yaw, spine=spine, head=head, legs=legs((knee * 0.5, 4, knee, -knee * 0.5)), arms=arms_ or arms(fwd=6, out=10), curl=curl)
GLASS_Y = -5.35 - 0.005
def glass_hand(h, s, x, z):
    sx = 1 if s == "L" else -1
    W = Vector((x, GLASS_Y - 0.035, z))
    return ("world", dict(W=W, d=Vector((0, 0.15, 1)), n=Vector((0, 1, 0)), pole=W + Vector((sx * 0.4, -0.5, -0.5))))
GAL = [("Keeper", -2.6, -5.85), ("SpecA", 1.4, -5.7), ("SpecB", 2.5, -6.3), ("SpecC", -0.6, -5.75), ("SpecD", -1.5, -6.6)]
DECK = [("SpecE", -0.5, -6.0), ("SpecG", 0.4, -6.9)]
for nm, x, y in GAL + DECK:
    PEOPLE[nm] = H(nm)
def clap(h, open_):
    a = {}
    for s_, sx in (("L", 1), ("R", -1)):
        W = Vector((sx * (0.09 + 0.1 * open_), -0.38, h.SH[s_].z - 0.14))
        a[s_] = ("body", dict(W=W, d=Vector((0, -0.35, 1.0)), n=Vector((-sx, 0, 0))))
    return a
def mouth_hand(h, s_="R"):
    e = h.R.BN["eye.L"].head_local; sx = 1 if s_ == "L" else -1
    return ("body", dict(W=Vector((sx * 0.01, e.y - 0.17, e.z - 0.09)), d=Vector((-sx * 0.6, 0, 1.0)), n=Vector((0, 1, 0))))
POINT = (0, 88, 88, 85)
for nm, x, y in GAL:
    h = PEOPLE[nm]
    for k, f in enumerate(range(1, END + 1, 30)):
        j = k % 2
        alarmed = BEAT[4] <= f < BEAT[11] + 40; happy = f >= BEAT[11] + 40
        if nm == "Keeper":
            if 1090 <= f <= 1210:          # nods to the beluga, palm on the glass, other hand signals
                stand(h, f, (x, y), 180, spine=(8, 0, 0), head=(18 * j, 0, 0), arms_={"L": glass_hand(h, "L", x - 0.25, 1.55), "R": ("rest", dict(fwd=60 + 40 * j, out=25))})
            elif alarmed and f > 1210:      # radios the deck, points up
                stand(h, f, (x, y), 180, spine=(4, 0, 0), head=(-25, 0, 0), arms_={"L": mouth_hand(h, "L"), "R": ("rest", dict(fwd=150, out=15))}, curl={"R": (POINT, 40)})
            elif happy:
                stand(h, f, (x, y), 180, spine=(0, 0, 0), head=(-15, 0, 0), arms_=clap(h, j))
            else:
                stand(h, f, (x, y), 180 + 5 * math.sin(k), spine=(4, 0, 2 * j), head=(5, 10 * math.sin(k * 0.7), 0), arms_=arms(fwd=12, out=10))
            continue
        if happy:
            stand(h, f, (x, y), 180, spine=(-4, 0, 0), head=(-12, 6 * math.sin(k), 0), knee=4 + 3 * j, arms_=clap(h, j), curl={"L": (12, 15), "R": (12, 15)})
        elif alarmed and nm in ("SpecA", "SpecC"):
            stand(h, f, (x, y), 180, spine=(10, 0, 0), head=(12, 8 * math.sin(k), 0),
                  arms_={"L": glass_hand(h, "L", x - 0.24, 1.5 + 0.05 * j), "R": glass_hand(h, "R", x + 0.24, 1.45)}, curl={"L": (8, 10), "R": (8, 10)})
        elif alarmed and nm == "SpecB":
            stand(h, f, (x, y), 180 - 12, spine=(8, 0, 0), head=(5, 10, 0), arms_=arms(l=dict(fwd=100 + 8 * j, out=12), r=dict(fwd=15, out=12)), curl={"L": (POINT, 45)})
        elif alarmed and nm == "SpecD":
            stand(h, f, (x, y), 180, spine=(12, 0, 0), head=(8, 0, 0), arms_={"R": mouth_hand(h, "R"), "L": ("rest", dict(fwd=40 + 15 * j, out=15))})
        else:
            stand(h, f, (x, y), 180 + 8 * math.sin(k + x), spine=(3, 0, 0), head=(4 * j, 12 * math.sin(k * 0.5 + x), 0), arms_=arms(fwd=10 + 20 * j, out=12))
for nm, x, y in DECK:
    h = PEOPLE[nm]
    for k, f in enumerate(range(1, END + 1, 12)):
        j = k % 2
        if f >= BEAT[11] + 30:       # clap, and one fist pump
            if nm == "SpecE" and (k // 3) % 2:
                stand(h, f, (x, y), 180 - 6 * x, spine=(-4, 0, 0), head=(-8, 0, 0), knee=4, gz=DECK_Z,
                      arms_=arms(l=dict(fwd=160 - 25 * j, out=20), r=dict(fwd=20, out=15)), curl={"L": (85, 50), "R": (25, 20)})
            else:
                stand(h, f, (x, y), 180 - 6 * x, spine=(6, 0, 0), head=(20, 0, 0), knee=4, gz=DECK_Z, arms_=clap(h, j), curl={"L": (12, 15), "R": (12, 15)})
        elif f >= BEAT[4]:           # lean over the rail, point down into the tank
            stand(h, f, (x, y), 180 - 6 * x, spine=(28, 0, 0), head=(35, 6 * math.sin(k * 0.3), 0), gz=DECK_Z,
                  arms_=arms(l=dict(fwd=60 + 6 * j, out=15), r=dict(fwd=20, out=15)), curl={"L": (POINT, 45)})
        elif k % 5 == 0 or f == 1:
            stand(h, f, (x, y), 180 - 6 * x, spine=(10, 0, 0), head=(20, 6 * math.sin(k * 0.6), 0), gz=DECK_Z, arms_=arms(fwd=15 + 15 * j, out=12))
# deck keeper (SpecF in a navy staff top) runs to the edge with a ring buoy and holds it out to her
K2 = bpy.data.objects["SpecF"]
for ch in K2.children:
    if ch.type == 'MESH' and "casualsuit" in ch.name:
        for m in ch.data.materials:
            for nd in m.node_tree.nodes:
                if nd.type == 'MIX' and nd.data_type == 'RGBA' and nd.blend_type == 'MULTIPLY': nd.inputs['B'].default_value = (0.16, 0.22, 0.4, 1)
K2R = make_human_ctrl(K2); K2H = Human(K2R)
K2F = H.__new__(H); K2F.R = K2R; K2F.REST_HAND = {}
for s_ in "LR":
    wv_ = K2R.BN["wrist." + s_].head_local; d_ = K2R.BN["finger3-1." + s_].head_local - wv_
    a_ = K2R.BN["finger2-1." + s_].head_local - K2R.BN["finger5-1." + s_].head_local
    K2F.REST_HAND[s_] = H.hand_basis(s_, d_, d_.cross(a_) if s_ == "L" else a_.cross(d_))
SOLE_K2 = -min((min(v.co.z for v in ch.data.vertices) for ch in K2.children if ch.type == 'MESH' and "shoes" in ch.name), default=0.0)
GROUND[0] = DECK_Z + SOLE_K2
P0 = Vector((3.6, -7.6, 0)); P1 = Vector((XY1.x + 0.75, -5.42, 0))
RUN0, RUN1 = 1840, 1985
def k2_path(f):
    t = smooth(max(0.0, min(1.0, (f - RUN0) / (RUN1 - RUN0)))); return P0.lerp(P1, t)
d_ = (P1 - P0); YAW_RUN = math.degrees(math.atan2(d_.x, -d_.y))
def k2_yaw(f):
    return YAW_RUN if f < RUN1 else YAW_RUN + (180 - YAW_RUN) * smooth(min(1.0, (f - RUN1) / 25.0))
for f in (1, 900, RUN0):
    p = k2_path(f)
    K2H.key_root(f, Vector((p.x, p.y, GROUND[0] + K2H.root_head.z - 0.02)), yaw=k2_yaw(f))
    K2H.key_spine(f, flex=6, head=(10, -20 if f < 900 else 0))
    for s_ in "LR": K2H.key_foot(s_, f, K2H.foot_xy(s_, p, k2_yaw(f)), k2_yaw(f))
K2H.walk(k2_path, k2_yaw, RUN0, RUN1, stride=1.05, lift=0.1, bob=0.03, crouch=0.06, lean=14)
for f in (RUN1 + 30, END):
    p = k2_path(f)
    K2H.key_root(f, Vector((p.x, p.y, GROUND[0] + K2H.root_head.z - 0.12)), yaw=k2_yaw(f), flex=12)
    K2H.key_spine(f, flex=34, head=(25, 0))
    for s_ in "LR": K2H.key_foot(s_, f, K2H.foot_xy(s_, p, k2_yaw(f)), k2_yaw(f))
# the buoy: a real ring life-buoy (orange/white bands), held in both hands
bpy.ops.mesh.primitive_torus_add(major_radius=0.24, minor_radius=0.055, major_segments=48, minor_segments=16)
buoy = bpy.context.active_object; buoy.name = "RingBuoy"
bm_m = bpy.data.materials.new("M_RingBuoy"); bm_m.use_nodes = True
bnn, bll = bm_m.node_tree.nodes, bm_m.node_tree.links; bpb = bnn["Principled BSDF"]; bpb.inputs['Roughness'].default_value = 0.55
btc_ = bnn.new('ShaderNodeTexCoord'); bsep_ = bnn.new('ShaderNodeSeparateXYZ'); bll.new(btc_.outputs['Object'], bsep_.inputs['Vector'])
bat = bnn.new('ShaderNodeMath'); bat.operation = 'ARCTAN2'; bll.new(bsep_.outputs['Y'], bat.inputs[0]); bll.new(bsep_.outputs['X'], bat.inputs[1])
bsn = bnn.new('ShaderNodeMath'); bsn.operation = 'SINE'; bmu = bnn.new('ShaderNodeMath'); bmu.operation = 'MULTIPLY'; bmu.inputs[1].default_value = 2.0
bll.new(bat.outputs[0], bmu.inputs[0]); bll.new(bmu.outputs[0], bsn.inputs[0])
bgt = bnn.new('ShaderNodeMath'); bgt.operation = 'GREATER_THAN'; bgt.inputs[1].default_value = 0.0; bll.new(bsn.outputs[0], bgt.inputs[0])
bcm = bnn.new('ShaderNodeMix'); bcm.data_type = 'RGBA'; bcm.inputs['A'].default_value = (0.9, 0.22, 0.03, 1); bcm.inputs['B'].default_value = (0.92, 0.92, 0.9, 1)
bll.new(bgt.outputs[0], bcm.inputs['Factor']); bll.new(bcm.outputs['Result'], bpb.inputs['Base Color'])
bnz_ = bnn.new('ShaderNodeTexNoise'); bnz_.inputs['Scale'].default_value = 120; bbp = bnn.new('ShaderNodeBump'); bbp.inputs['Strength'].default_value = 0.15
bll.new(bnz_.outputs['Fac'], bbp.inputs['Height']); bll.new(bbp.outputs['Normal'], bpb.inputs['Normal'])
buoy.data.materials.append(bm_m); [setattr(f_, 'use_smooth', True) for f_ in buoy.data.polygons]
buoy.rotation_mode = 'QUATERNION'
for f in list(range(1, END + 1, 6)) + [END]:
    ev(f)
    sp = K2.matrix_world @ K2R.PB["spine02"].head
    yw = R_(k2_yaw(f)); fwd = Vector((math.sin(yw), -math.cos(yw), 0)); side = Vector((math.cos(yw), math.sin(yw), 0))
    reach = 0.0 if f < RUN1 else smooth(min(1.0, (f - RUN1) / 40.0))
    c = sp + fwd * (0.42 + 0.35 * reach) + Vector((0, 0, -0.18 - 0.35 * reach))
    q = Vector((0, 0, 1)).rotation_difference(fwd)
    buoy.location = c; buoy.rotation_quaternion = q
    buoy.keyframe_insert("location", frame=f); buoy.keyframe_insert("rotation_quaternion", frame=f)
    for s_, sx in (("L", 1), ("R", -1)):
        W = c + side * sx * 0.37                     # grip on the outer edge of the ring, each side (palm outside the tube)
        K2H.key_hand(s_, f, W + Vector((0, 0, 0.03)), Vector((0, 0, -1)), -side * sx, pole=W + side * sx * 0.4 - fwd * 0.4 + Vector((0, 0, -0.3)))
        K2F.key_fingers(s_, f, 45, 40)
# the buoy follows the hands the IK actually reached: rim between the two palms
for f in list(range(1, END + 1, 6)) + [END]:
    ev(f)
    wl = K2.matrix_world @ K2R.PB["wrist.L"].head; wr = K2.matrix_world @ K2R.PB["wrist.R"].head
    yw = R_(k2_yaw(f)); fwd = Vector((math.sin(yw), -math.cos(yw), 0))
    c = (wl + wr) / 2 + fwd * 0.05 + Vector((0, 0, -0.07))
    axis = (wr - wl).normalized().cross(Vector((0, 0, 1))).normalized()
    if axis.dot(fwd) < 0: axis = -axis
    buoy.location = c; buoy.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
    buoy.keyframe_insert("location", frame=f); buoy.keyframe_insert("rotation_quaternion", frame=f)
print("DECK KEEPER keyed")
for nm, h in PEOPLE.items():
    h.bake()
print("PEOPLE keyed")

# bake JSON of beat frames for the VO retime
FIRST = {1: "She dove into an Arctic whale tank", 2: "as she sank to the bottom", 3: "the freezing water sent her legs into crippling cramps",
         4: "impossible to swim back up", 5: "as she started to drown", 6: "a beluga whale noticed her panicking",
         7: "known for being intelligent and playful", 8: "it could tell something was wrong", 9: "gently took her leg in its mouth",
         10: "just as she was about to run out of breath", 11: "lifted her above the surface", 12: "she could finally gasp for air"}
json.dump([{"beat": b, "frame": f, "first_words": FIRST[b]} for b, f in BEAT.items()], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc["beats"] = json.dumps(BEAT)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE", OUT)
