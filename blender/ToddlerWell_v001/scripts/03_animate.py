"""ToddlerWell animation: cast, ropes, excavator, time-lapse sky, FX, lights. (Camera in 04_camera.py)
blender -b work/scene.blend --python scripts/03_animate.py -- work/anim.blend"""
import sys, os, math, random, json
import bpy
from mathutils import Vector, Matrix, Euler

OUT = sys.argv[sys.argv.index("--") + 1]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pipeline/anim_lib.py")).read())
random.seed(7)
V = Vector
DEPTH = 15.24; FLOOR_Z = -DEPTH + 0.05
BEAT = {1: 1, 2: 241, 3: 463, 4: 673, 5: 913, 6: 1135, 7: 1297, 8: 1357, 9: 1501, 10: 1627, 11: 1765}
END = 1950

def Rz(d): return Matrix.Rotation(R_(d), 3, 'Z')
def Rx(d): return Matrix.Rotation(R_(d), 3, 'X')
def lerp(a, b, t): return a + (b - a) * t

class Char:
    def __init__(self, name):
        self.name = name; self.o = bpy.data.objects[name]
        self.r = make_human_ctrl(self.o); self.h = Human(self.r)
        B = self.r.BN
        self.root = B["root"].head_local.copy()
        self.sh = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.arm = (B["wrist.L"].head_local - B["upperarm01.L"].head_local).length
        self.ankle = {s: B["foot.L" if s == "L" else "foot.R"].head_local.copy() for s in "LR"}
        self.headtop = B["head"].tail_local.copy()
        self.H = self.headtop.z
        for pb in self.r.PB:
            pb.rotation_mode = 'QUATERNION'
        self.state = {}
        self.elbow_out = 0.35
    # body rotation (yaw about Z, then flex: positive = lean forward)
    def rot(self, yaw, flex, side=0.0):
        return Rz(yaw) @ Rx(flex) @ Matrix.Rotation(R_(side), 3, 'Y')
    def to_world(self, rootpos, yaw, flex, local_rest_pt, side=0.0):
        return rootpos + self.rot(yaw, flex, side) @ (local_rest_pt - self.root)
    def shoulder(self, s, rootpos, yaw, flex_tot, side=0.0):
        return self.to_world(rootpos, yaw, flex_tot, self.sh[s], side)
    def key(self, f, xy, yaw=0.0, z=None, flex=0.0, spine=0.0, twist=0.0, side=0.0, head=(0.0, 0.0), crouch=0.0,
            feet=None, hands=None, root_world=None, upright_feet=True):
        """xy: ground position (Vector2/3) of the pelvis; feet default planted under the body.
        hands: {'L': spec, 'R': spec}; spec = ('rel', (out, fwd, up)) in shoulder-local metres, or ('w', Vector) world,
        optional third element = (dir, normal) for the hand orientation."""
        h = self.h; rr = self.r
        if root_world is not None:
            rp = V(root_world)
        else:
            gz = 0.0 if z is None else z
            rp = V((xy[0], xy[1], gz + self.root.z - crouch))
        h.key_root(f, rp, yaw=yaw, flex=flex, side=side)
        h.key_spine(f, flex=spine, twist=twist, side=0.0, head=head)
        Rb = self.rot(yaw, flex, side)
        tot = self.rot(yaw, flex + spine, side)
        # feet
        for s in "LR":
            spec = (feet or {}).get(s)
            if spec is None:
                W = self.to_world(rp, yaw, 0.0 if upright_feet else flex, self.ankle[s], 0.0 if upright_feet else side)
                if upright_feet: W.z = (0.0 if z is None else z) + self.ankle[s].z
                fr = Rz(yaw) if upright_feet else Rb; lift = 0
            elif spec[0] == "w":
                W = V(spec[1]); fr = spec[2] if len(spec) > 2 else Rz(yaw)
            elif spec[0] == "xy":   # ground position + yaw (+lift, pitch)
                xy2, fy = spec[1], spec[2]; lift = spec[3] if len(spec) > 3 else 0.0; pitch = spec[4] if len(spec) > 4 else 0.0
                W = V((xy2[0], xy2[1], (0.0 if z is None else z) + self.ankle[s].z + lift)); fr = Rz(fy) @ Rx(-pitch)
            a = self.ankle[s]
            M = Matrix.Translation(W) @ fr.to_4x4() @ Matrix.Translation(-a) @ rr.rest("IK_foot." + s)
            rr.key_world("IK_foot." + s, f, M)
            n = "Pole_knee." + s
            pole = W + fr @ V((0, -0.8, 0.5 * self.H / 1.8))
            pb = rr.PB[n]; pb.location = rr.rest(n).to_3x3().inverted() @ (pole - rr.BN[n].head_local)
            pb.keyframe_insert("location", frame=f, group=n)
        # hands
        for s in "LR":
            sx = 1 if s == "L" else -1
            spec = (hands or {}).get(s, ("rel", (0.16, 0.09, -0.86 * self.arm)))
            S = self.shoulder(s, rp, yaw, flex + spine, side)
            if spec[0] == "rel":
                o, fw, up = spec[1]
                W = S + tot @ V((o * sx, -fw, up))
            elif spec[0] == "wg":     # grip a body: the wrist stops short of the contact point by a palm length
                Tg = V(spec[1]); dv = (Tg - S); W = Tg - dv.normalized() * GRIP_BACK if dv.length > 1e-4 else Tg
            else:
                W = V(spec[1])
            if len(spec) > 2 and spec[2]:
                d, nrm = spec[2]
            else:
                d = (W - S).normalized() if (W - S).length > 1e-4 else tot @ V((0, 0, -1))
                nrm = tot @ V((-sx, 0, 0))
                if abs(d.dot(nrm)) > 0.95: nrm = tot @ V((0, 1, 0))
            pole = S + tot @ V((self.elbow_out * sx, 0.6, -0.25))
            h.key_hand(s, f, W, d, nrm, pole=pole)
        self.state[f] = dict(rp=rp, yaw=yaw, flex=flex)
        return rp

    def hand_world(self, s, rp, yaw, flex, spine, rel):
        sx = 1 if s == "L" else -1
        S = self.shoulder(s, rp, yaw, flex + spine)
        return S + self.rot(yaw, flex + spine) @ V((rel[0] * sx, -rel[1], rel[2]))

    def walk(self, pts, f0, f1, stride=0.7, lift=0.08, arm_swing=0.18, hands_fn=None, bob=0.022, lean=5.0, step=2):
        """walk along a Catmull path of ground points; hands swing (or hands_fn(f) -> dict)"""
        n = len(pts); keys = [(f0 + (f1 - f0) * i / (n - 1), V((p[0], p[1], 0))) for i, p in enumerate(pts)]
        # reparametrise by arc length for steady speed with ease in/out
        raw = catmull(keys)
        L = [0.0]; fs = list(range(f0, f1 + 1))
        for a, b in zip(fs, fs[1:]): L.append(L[-1] + (raw(b) - raw(a)).length)
        tot = L[-1]
        def path(f):
            u = (f - f0) / max(1, f1 - f0); u = max(0, min(1, u))
            s_ = tot * (u * u * (3 - 2 * u) * 0.35 + u * 0.65)
            for i in range(1, len(L)):
                if L[i] >= s_:
                    t = (s_ - L[i - 1]) / max(1e-6, L[i] - L[i - 1]); return raw(fs[i - 1]).lerp(raw(fs[i]), t)
            return raw(f1)
        def yaw_fn(f):
            a, b = path(max(f0, f - 3)), path(min(f1, f + 3)); d = (b - a)
            if d.length < 1e-4: a, b = path(f0), path(f1); d = b - a
            return math.degrees(math.atan2(d.x, -d.y))
        self.h.ankle = {s: self.ankle[s] for s in "LR"}
        self.h.walk(path, yaw_fn, f0, f1, stride=stride, lift=lift, bob=bob, lean=lean, step=step,
                    crouch=0.03 * self.H / 1.75)
        dist = [0.0]
        for a, b in zip(fs, fs[1:]): dist.append(dist[-1] + (path(b) - path(a)).to_2d().length)
        for i, f in enumerate(fs):
            if (i % 4) and f != f1: continue
            p = path(f); yw = yaw_fn(f); cyc = (dist[i] / stride) % 1.0
            rp = V((p.x, p.y, self.root.z - 0.03 * self.H / 1.75))
            hs = hands_fn(f) if hands_fn else {}
            for s in "LR":
                sw = arm_swing * math.sin(2 * math.pi * (cyc + (0.0 if s == "L" else 0.5)))
                spec = hs.get(s, ("rel", (0.15, sw * self.H / 1.75, -0.86 * self.arm)))
                sx = 1 if s == "L" else -1
                S = self.shoulder(s, rp, yw, lean * 1.5)
                W = S + self.rot(yw, lean * 1.5) @ V((spec[1][0] * sx, -spec[1][1], spec[1][2])) if spec[0] == "rel" else V(spec[1])
                d = (W - S).normalized(); nrm = self.rot(yw, 0) @ V((-sx, 0, 0))
                self.h.key_hand(s, f, W, d, nrm, pole=S + self.rot(yw, 0) @ V((0.35 * sx, 0.6, -0.25)))
        return path, yaw_fn

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

GRIP_BACK = 0.085
def jaw(c, f, deg):
    c.r.key_rot("jaw", f, [("X", deg)])
CH = {n: Char(n) for n in ("Toddler", "Teen", "ResA", "ResB", "ResC", "Mother", "Crowd1", "Crowd2", "Crowd3", "Crowd4")}
T, TE, RA, RB, RC, MO = (CH[n] for n in ("Toddler", "Teen", "ResA", "ResB", "ResC", "Mother"))
HANG = lambda c: ("rel", (0.16, 0.09, -0.86 * c.arm))
UP = lambda c, o=0.08, fw=0.05: ("rel", (o, fw, 0.92 * c.arm))

# ================================================================== TODDLER
# beat 1: toddles toward the pipe, slips, falls 15 m, lands, cries with arms up
t0 = V((-1.65, -1.15)); edge = V((-0.42, -0.31))
T.walk([t0, t0.lerp(edge, 0.5) + V((0.05, -0.05)), edge], 1, 84, stride=0.26, lift=0.045, arm_swing=0.12, bob=0.012, lean=3)
yaw_in = math.degrees(math.atan2(edge.x - t0.x, -(edge.y - t0.y)))
# step onto the rim: right foot over the hole, wobble, arms flail
RIMSTEP = edge.normalized() * 0.335     # his right foot goes up ONTO the casing lip, then slips off inward
T.key(90, edge, yaw_in, feet={"L": ("xy", edge + V((0.03, -0.05)), yaw_in), "R": ("xy", RIMSTEP, yaw_in, 0.15)}, head=(15, 0),
      hands={"L": ("rel", (0.15, 0.15, -0.4 * T.arm)), "R": ("rel", (0.15, 0.15, -0.4 * T.arm))})
T.key(98, edge.lerp(V((0, 0)), 0.3), yaw_in, flex=12, side=-10, feet={"L": ("xy", edge + V((0.03, -0.05)), yaw_in, 0.02), "R": ("w", V((-0.05, -0.04, -0.05)), Rz(yaw_in))},
      head=(25, 0), hands={"L": UP(T, 0.25, -0.1), "R": UP(T, 0.3, 0.1)})
# fall: ballistic, keyed every 4 frames, slow tumble, arms up
F0, F1 = 104, 196
for f in range(F0, F1 + 1, 4):
    u = (f - F0) / (F1 - F0)
    zr = 0.32 - (DEPTH - 0.05 + 0.32) * u * u + T.root.z
    xy = V((-0.04, -0.03)).lerp(V((0.0, 0.0)), u)
    T.key(f, xy, yaw_in + 40 * u, root_world=V((xy.x, xy.y, zr)), flex=-8 + 10 * math.sin(u * 7), side=6 * math.sin(u * 9),
          feet={s: ("w", V((xy.x + (0.07 if s == "L" else -0.07), xy.y, zr - T.root.z + T.ankle[s].z + 0.02 * math.sin(u * 20 + (s == "L") * 2))), Rz(yaw_in + 40 * u))
                for s in "LR"},
          hands={"L": UP(T, 0.09 + 0.03 * math.sin(u * 13), 0.04), "R": UP(T, 0.09, 0.04 + 0.02 * math.sin(u * 11))}, head=(-30, 0))
yb = yaw_in + 40
# land: squash, settle, stand and cry with arms up
FZ = FLOOR_Z + 0.03
T.key(200, V((0, 0)), yb, z=FZ, crouch=0.13, flex=25, head=(10, 0), hands={"L": ("rel", (0.1, 0.12, -0.5 * T.arm)), "R": ("rel", (0.1, 0.12, -0.5 * T.arm))})
T.key(206, V((0, 0)), yb, z=FZ, crouch=0.16, flex=30, head=(20, 0), hands={"L": ("rel", (0.12, 0.15, -0.6 * T.arm)), "R": ("rel", (0.12, 0.15, -0.6 * T.arm))})
LOOK = -62; JAW = 16
jaw(T, 1, 0); jaw(T, 206, 0); jaw(T, 214, JAW)
T.key(220, V((0, 0)), yb, z=FZ, crouch=0.04, flex=-8, head=(LOOK, 0), hands={"L": UP(T, 0.1), "R": UP(T, 0.1)})
# bottom idle until the grab: crying, arms pumping, looking up, bouncing
def toddler_idle(f0, f1, reach=1.0, look=LOOK):
    for i, f in enumerate(range(f0, f1, 12)):
        ph = i * 1.3
        jaw(T, f, JAW * (0.75 + 0.25 * math.sin(ph * 2.3)))
        T.key(f, V((0.01 * math.sin(ph), 0.01 * math.cos(ph))), yb + 15 * math.sin(ph * 0.4), z=FZ, crouch=0.02 + 0.02 * math.sin(ph * 2),
              flex=-12 + 4 * math.sin(ph), twist=8 * math.sin(ph * 0.7),
              head=(look + 8 * math.sin(ph * 1.7), 12 * math.sin(ph * 0.9)),
              hands={"L": UP(T, 0.08 + 0.04 * math.sin(ph * 2.0), 0.05 * reach), "R": UP(T, 0.08 + 0.04 * math.cos(ph * 2.0), 0.05 * reach)})
toddler_idle(232, 420)
# beat 2: the loop swings past his arms (f 420-470): he grabs at it and misses
for f, dx in ((424, 0.06), (436, -0.08), (448, 0.07), (460, -0.03)):
    T.key(f, V((0, 0)), yb, z=FZ, crouch=0.0, flex=-10, head=(LOOK, 20 * dx / 0.08),
          hands={"L": ("rel", (0.08 + dx, 0.12, 0.95 * T.arm)), "R": ("rel", (0.08 - dx, 0.12, 0.95 * T.arm))})
toddler_idle(472, 1520)

# ================================================================== CROWD / MOTHER idles (behind the tape)
CROWD_POS = {"Mother": (-1.3, 6.15), "Crowd1": (-1.85, 6.75), "Crowd2": (1.4, 6.7), "Crowd3": (3.3, 7.2), "Crowd4": (-0.2, 7.6)}
def crowd_idle(c, f0, f1, xy, yaw, mood):
    for i, f in enumerate(range(f0, f1, 18)):
        ph = i * 0.9 + hash(c.name) % 10
        if mood == "worry":
            hands = {"L": ("rel", (0.02, 0.22, 0.12 * c.arm)), "R": ("rel", (0.02, 0.2, 0.1 * c.arm))} if (i // 3) % 2 == 0 else \
                    {"L": ("rel", (0.0, 0.2, -0.35 * c.arm)), "R": ("rel", (-0.02, 0.22, -0.3 * c.arm))}
        elif mood == "plead":     # leaning on the tape, reaching toward the well, hands to face, sobbing
            hands = ({"L": ("rel", (0.05, 0.22, 0.14 * c.arm)), "R": ("rel", (0.02, 0.22, 0.12 * c.arm))} if (i % 4) < 2 else
                     {"L": ("rel", (0.12, 0.6 * c.arm, -0.15 * c.arm)), "R": ("rel", (0.1, 0.65 * c.arm, -0.05 * c.arm))})
        elif mood == "restrain":   # from behind: one hand between the mother's shoulder blades, the other on her lower back
            mp_ = V(CROWD_POS["Mother"]); my_ = math.degrees(math.atan2(-mp_.x, mp_.y))
            mb = MO.rot(my_, 14)
            base = V((mp_.x, mp_.y, MO.root.z))
            hands = {"R": ("wg", base + mb @ V((0.0, 0.13, 0.45))), "L": ("wg", base + mb @ V((-0.08, 0.13, 0.22)))}
        elif mood == "point":
            hands = {"R": ("rel", (0.05, 0.75 * c.arm, 0.1 * c.arm))} if (i % 4) < 2 else {}
        elif mood == "cheer":
            hands = {"L": ("rel", (0.2 + 0.06 * math.sin(ph * 3), 0.2, 0.96 * c.arm), (V((0, 0, 1)), V((-1, 0, 0)))), "R": ("rel", (0.2 + 0.06 * math.cos(ph * 3), 0.2, 0.96 * c.arm), (V((0, 0, 1)), V((1, 0, 0))))}   # above and in front of the head, clear of the hair
        else:
            hands = {"L": ("rel", (0.14, 0.1 + 0.05 * math.sin(ph), -0.82 * c.arm))}
        c.key(f, V((xy[0] + 0.03 * math.sin(ph * 0.7), xy[1])), yaw + 6 * math.sin(ph * 0.5), flex=(14 + 6 * math.sin(ph * 1.7)) if mood == "plead" else 3 + 3 * math.sin(ph),
              twist=8 * math.sin(ph * 0.6), head=(5 * math.sin(ph * 1.3) + (20 if mood == "worry" else 0), 15 * math.sin(ph * 0.8)),
              hands=hands, crouch=(0.05 * abs(math.sin(ph * 2)) if mood == "cheer" else 0.0))
for n, xy in CROWD_POS.items():
    c = CH[n]; yaw = math.degrees(math.atan2(0 - xy[0], -(0 - xy[1])))
    if n != "Mother":
        crowd_idle(c, 1, 470, xy, yaw, "idle")
        crowd_idle(c, 470, 1760, xy, yaw, "restrain" if n == "Crowd1" else ("point" if n in ("Crowd2", "Crowd4") else "worry"))
        crowd_idle(c, 1776, END + 20, xy, yaw, "cheer")
    else:
        crowd_idle(c, 1, 241, xy, yaw, "idle"); crowd_idle(c, 241, 1800, xy, yaw, "plead")

# ================================================================== RESCUERS
# rope/hand helpers
PULLEY_TOP = V((0, 0.05, 3.33)); PULLEY_OUT = V((0, 0.16, 3.22)); PULLEY_IN = V((0, 0.0, 3.11))
RA_P = V((-0.62, 0.52)); RB_P = V((0.62, 0.5)); RC_P = V((-2.2, 1.6))
def yaw_to(p, q): return math.degrees(math.atan2(q[0] - p[0], -(q[1] - p[1])))
# beat 1: rescuers not on scene yet (they are off to the side at the trucks) -> keep them away
for c, p in ((RA, V((-14, 12))), (RB, V((-15, 13))), (RC, V((-13, 14)))):
    c.key(1, p, 0); c.key(236, p, 0)     # off-stage until the camera is down the shaft
# beat 2 (241-462): ResA feeds the loop rope hand over hand over the hole; ResB kneels at the rim; ResC behind, calling
loop_depth = {}
for f in range(241, 471, 2):
    u = (f - 262) / (420 - 262)
    loop_depth[f] = -0.3 - (DEPTH - 1.0) * ease(u) if f < 420 else -(DEPTH - 0.75) - 0.0
for i, f in enumerate(range(241, 470, 10)):
    ph = i * 0.6
    yA = yaw_to(RA_P, (0, 0))
    hy = 0.15 * math.sin(i * math.pi / 2)
    # hand over hand: hands alternate on the rope, just above the opening
    hl = V((-0.26, 0.2, 1.05 + 0.18 * math.sin(i * math.pi / 2))); hr = V((-0.22, 0.15, 1.05 - 0.18 * math.sin(i * math.pi / 2)))
    RA.key(f, RA_P, yA, flex=14, spine=8, head=(35, 0), crouch=0.05, hands={"L": ("w", hl), "R": ("w", hr)})
    RB.key(f, RB_P, yaw_to(RB_P, (0, 0)), crouch=0.42, flex=35, spine=10, head=(40, 0),
           feet={"L": ("xy", RB_P + V((0.15, 0.05)), yaw_to(RB_P, (0, 0))), "R": ("xy", RB_P + V((-0.12, 0.25)), yaw_to(RB_P, (0, 0)))},
           hands={"L": ("w", V((0.31, 0.09, 0.16))), "R": ("rel", (0.05, 0.45 * RB.arm, -0.35 * RB.arm))})
    RC.key(f, RC_P, yaw_to(RC_P, (0, 0)) + 20 * math.sin(ph), head=(0, 10 * math.sin(ph)),
           hands={"R": ("rel", (0.02, 0.12, 0.18 * RC.arm)), "L": ("rel", (0.2, 0.25, -0.3 * RC.arm)) if i % 4 < 2 else HANG(RC)})
# beat 3 (463-672): step back as the excavator rolls in; ResC waves it in
for i, f in enumerate(range(470, 680, 12)):
    ph = i * 0.8
    RA.key(f, V((-1.12, 0.92)), yaw_to(RA_P, (4, 1)), head=(5, 0), hands={"L": ("rel", (0.05, 0.25, -0.2 * RA.arm)), "R": HANG(RA)})
    RB.key(f, V((1.6, -2.2)), yaw_to((1.6, -2.2), (5, 1)), head=(5, 0), hands={"R": ("rel", (0.05, 0.3, 0.1 * RB.arm))})
    if f >= 562: RC.key(f, V((1.9, -2.8)), yaw_to((1.9, -2.8), (6, 1)), hands={"L": UP(RC, 0.35, 0.1 + 0.25 * math.sin(ph * 2.2)), "R": ("rel", (0.4, 0.2 + 0.2 * math.sin(ph * 2.2 + 1), 0.4 * RC.arm))})
# beat 4 (673-912): time-lapse exhaustion: fast pose changes
TL = [("bent", "wipe", "sit"), ("sit", "bent", "point"), ("wipe", "sit", "bent"), ("bent", "wipe", "sit"), ("sit", "point", "bent"), ("bent", "sit", "wipe")]
def tired(c, f, p, yaw, kind):
    if kind == "bent":
        c.key(f, p, yaw, flex=35, crouch=0.12, head=(10, 0), hands={"L": ("rel", (0.06, 0.5, -0.58 * c.arm)), "R": ("rel", (0.06, 0.5, -0.58 * c.arm))})
    elif kind == "wipe":
        c.key(f, p, yaw, flex=-5, head=(-15, 0), hands={"R": ("rel", (-0.12, 0.12, 0.18 * c.arm)), "L": ("rel", (0.08, 0.1, -0.5 * c.arm))})
    elif kind == "drink":
        c.key(f, p, yaw, flex=-8, head=(-30, 0), hands={"R": ("rel", (-0.1, 0.12, 0.1 * c.arm))})
    elif kind == "sit":      # sit on the ground, knees up, forearms on the knees, head down for a breath then up
        fwd = Rz(yaw) @ V((0, -1, 0)); side = Rz(yaw) @ V((1, 0, 0))
        c.key(f, p, yaw, flex=18, crouch=c.root.z - 0.16, head=(12, 0),
              feet={"L": ("xy", (p.to_3d() + fwd * 0.5 + side * 0.14).to_2d(), yaw), "R": ("xy", (p.to_3d() + fwd * 0.5 - side * 0.14).to_2d(), yaw)},
              hands={"L": ("rel", (0.05, 0.42, -0.42 * c.arm)), "R": ("rel", (0.05, 0.42, -0.42 * c.arm))})
    else:
        c.key(f, p, yaw, hands={"R": ("rel", (0.05, 0.75 * c.arm, 0.1))})
TLP = {RA: V((-1.1, 1.5)), RB: V((0.4, 2.6)), RC: V((-2.4, 1.2))}
for k, f in enumerate(range(704, 905, 36)):
    for j, c in enumerate((RA, RB, RC)):
        tired(c, f, TLP[c], yaw_to(TLP[c], (1.5, 0.5)) + 25 * math.sin(k + j), TL[k][j])
        tired(c, f + 24, TLP[c], yaw_to(TLP[c], (1.5, 0.5)) + 25 * math.sin(k + j), TL[k][j])
# beat 5 (913-1134): they turn to the teen, listen, gesture at the hole
for i, f in enumerate(range(920, 1140, 14)):
    ph = i * 0.9
    tgt = V((-1.0, 2.0)) if f > 1000 else V((-2.2, 4.8))
    RA.key(f, V((-0.9, 0.9)), yaw_to((-0.9, 0.9), tgt), head=(0, 8 * math.sin(ph)), twist=6 * math.sin(ph),
           hands={"R": ("rel", (0.25, 0.35, -0.05 * RA.arm + 0.08 * math.sin(ph * 2))) if i % 3 else HANG(RA), "L": ("rel", (0.12, 0.25, -0.35 * RA.arm))})
    RB.key(f, V((0.1, 1.9)), yaw_to((0.1, 1.9), tgt), head=(5, 0),
           hands={"L": ("rel", (0.3, 0.55 * RB.arm, -0.3 * RB.arm)) if (i % 4) < 2 else HANG(RB)})
    RC.key(f, V((-1.9, 0.2)), yaw_to((-1.9, 0.2), tgt), hands={"L": ("rel", (0.02, 0.15, -0.1 * RC.arm)), "R": ("rel", (0.02, 0.18, -0.1 * RC.arm))}, flex=-3)

# ================================================================== TEEN
TEEN_START = V((-2.6, 7.4))
crowd_idle(TE, 1, 905, TEEN_START, yaw_to(TEEN_START, (0, 0)), "idle")     # a passer-by watching at the back of the crowd
# beat 5: pushes through the crowd, ducks under the tape, walks up with a raised hand, talks
path, yfn = TE.walk([TEEN_START, V((-2.45, 6.2)), V((-2.1, 4.6)), V((-1.6, 3.1)), V((-1.15, 2.05))], 913, 1010, stride=0.72,
                    hands_fn=lambda f: {"R": UP(TE, 0.12, 0.12)} if 925 < f < 990 else {})
# duck under the tape around f 940-955 (tape at y~5.6)
for f, d in ((936, 0.0), (946, 1.0), (956, 0.0)):
    p = path(f); yw = yfn(f)
    TE.h.key_spine(f, flex=40 * d, head=(-20 * d, 0))
TE.key(1016, V((-1.12, 2.0)), yaw_to((-1.12, 2.0), (-0.9, 0.9)), head=(-5, 0))
for i, f in enumerate(range(1028, 1130, 14)):
    ph = i * 1.1
    who = "self" if 1070 < f < 1100 else "talk"
    hands = {"R": ("rel", (-0.12, 0.24, -0.06)), "L": HANG(TE)} if who == "self" else \
            {"R": ("rel", (0.2, 0.35, -0.2 * TE.arm + 0.1 * math.sin(ph * 2))), "L": ("rel", (0.15, 0.3, -0.35 * TE.arm))}
    TE.key(f, V((-1.12, 2.0)), yaw_to((-1.12, 2.0), (-0.9, 0.9)) + 6 * math.sin(ph), head=(-4 + 6 * math.sin(ph * 2), 6 * math.sin(ph)), twist=5 * math.sin(ph), hands=hands)
# beat 6 (1135-1296): rope tied around his waist by ResB; arms lifted out of the way; ResA checks the line
TPOS = V((-1.45, 1.25)); TYAW = yaw_to(TPOS, (-0.9, 0.42))
TE.walk([V((-1.12, 2.0)), V((-1.3, 1.6)), TPOS], 1130, 1160, stride=0.5)
WAIST = TPOS.to_3d() + V((0, 0, TE.root.z + 0.08))
for i, f in enumerate(range(1166, 1300, 8)):
    ph = i * 0.9
    TE.key(f, TPOS, TYAW, head=(25 if f < 1240 else -5, 0), flex=-3,
           hands={"L": ("rel", (0.36, 0.04, 0.6 * TE.arm)), "R": ("rel", (0.36, 0.04, 0.6 * TE.arm))} if f < 1250 else
                 {"L": ("rel", (0.1, 0.25, -0.5 * TE.arm)), "R": ("rel", (0.1, 0.25, -0.5 * TE.arm))})
# ResB in front of the teen, knotting at the waist
RBT = TPOS + (Rz(TYAW) @ V((0, -0.74, 0))).to_2d()
fwd_t = (Rz(TYAW) @ V((0, -1, 0)))
knot = WAIST + fwd_t * 0.25      # in front of the belly, on the rope loop
for i, f in enumerate(range(1164, 1263, 6)):
    ph = i * 1.2; u = (f - 1140) / 160
    circ = V((0.07 * math.cos(ph), 0, 0.05 * math.sin(ph)))
    if f < 1170:
        hl = knot + Rz(TYAW) @ V((0.12, -0.08, 0)); hr = knot + Rz(TYAW) @ V((-0.12, -0.08, 0))
    elif f < 1244:
        hl = knot + Rz(TYAW) @ (circ * 0.5 + V((0.08, -0.06, 0))); hr = knot + Rz(TYAW) @ (-circ * 0.5 + V((-0.08, -0.06, 0)))
    else:   # pull the knot tight: hands apart and back
        k = ease((f - 1244) / 16); hl = knot + Rz(TYAW) @ V((0.06 + 0.1 * k, -0.08 - 0.08 * k, 0)); hr = knot + Rz(TYAW) @ V((-0.06 - 0.1 * k, -0.08 - 0.08 * k, 0))
    RB.key(f, RBT, yaw_to(RBT, TPOS), flex=22, crouch=0.28, head=(25, 0), hands={"L": ("wg", hl), "R": ("wg", hr)})
for i, f in enumerate(range(1140, 1300, 10)):
    RA.key(f, V((0.75, -0.3)) if f > 1180 else V((-0.9, 0.9)), yaw_to((0.75, -0.3), (0.42, -0.7)), head=(-25, 0),
           hands={"L": ("w", V((0.47, -0.57, 1.82 - 0.04 * math.sin(i)))), "R": ("w", V((0.55, -0.68, 1.5)))} if f > 1190 else {})   # checks the tripod leg   # checks the tripod leg
    RC.key(f, V((-0.2, 2.6)), yaw_to((-0.2, 2.6), (0, 0)), hands={"L": ("w", V((-0.14, 2.1, 1.08))), "R": ("w", V((-0.1, 1.9, 1.1)))}, flex=10)

# ================================================================== HEAD-FIRST LOWERING (1297-1500), GRAB (1501-1626), RISE (1627-1764)
# teen stands at the rim on the +y side facing -y (yaw 0) then pitches forward into the pipe; ResA/ResB hold his legs.
RIM = V((0.0, 0.55))
TE.walk([TPOS, V((0.0, 1.25)), RIM], 1290, 1312, stride=0.6)     # straight in between the two holders
TOP_Y = 0.0
def teen_ank(rp, Rb, s, flex=180.0):
    """ankle target for the head-down teen: feet together, toes pointed up the pipe (narrow, like a dive)"""
    k = max(0.0, min(1.0, (flex - 90.0) / 90.0))
    l = TE.ankle[s] - TE.root; l = V((l.x * (1 - 0.65 * k), l.y, l.z))
    return rp + Rb @ l
def teen_foot(rp, Rb, s, flex=180.0):
    k = max(0.0, min(1.0, (flex - 90.0) / 90.0))
    fr = Rb.to_quaternion().slerp((Rx(-90)).to_quaternion(), k).to_matrix()
    return ("w", teen_ank(rp, Rb, s, flex), fr)
def teen_inverted(f, zr, flex, wob=0.0, arms="reach", grip=None, xy=None):
    """zr = pelvis height; flex 180 = fully head-down. Body centred over/in the pipe."""
    u = flex / 180.0
    if xy is None: xy = RIM.lerp(V((0.0, 0.0)), min(1.0, u * 1.3))
    rp = V((xy.x, xy.y, zr))
    Rb = Rz(0) @ Rx(flex)
    feet = {s: teen_foot(rp, Rb, s, flex) for s in "LR"}
    if grip:
        hands = {"L": ("w", grip["L"], grip.get("dn")), "R": ("w", grip["R"], grip.get("dn"))}
    elif arms == "reach":
        hands = {"L": ("rel", (-0.03, 0.0, 0.93 * TE.arm)), "R": ("rel", (-0.03, 0.0, 0.93 * TE.arm))}
    else:
        hands = {"L": ("rel", (0.05, 0.25, 0.75 * TE.arm)), "R": ("rel", (0.05, 0.25, 0.75 * TE.arm))}
    TE.key(f, xy, 0, root_world=rp, flex=flex, spine=0 if u > 0.9 else 20 * u, side=wob, head=(-25 * u, 0), feet=feet, hands=hands)
    return rp, Rb
TE.elbow_out = 0.05     # elbows tucked inside the pipe
# 1314-1326: standing at the rim he bends forward at the hips, hands reaching down into the pipe, feet planted
for f in range(1314, 1327, 4):
    k = ease((f - 1314) / 12)
    TE.key(f, RIM, 0, flex=80 * k, spine=8 * k, crouch=0.05 * k, head=(-25 * k, 0),
           hands={"L": ("rel", (-0.02, 0.05, 0.9 * TE.arm)), "R": ("rel", (-0.02, 0.05, 0.9 * TE.arm))})
LOWER = []   # (frame, pelvis z, flex, xy)
for f in range(1330, 1500, 4):
    u = (f - 1314) / (1500 - 1314)
    if f < 1342:      # 1326-1342: the holders lift his legs up over the pipe
        k = ease((f - 1326) / 16); zr = lerp(TE.root.z - 0.05, 1.25, k); flex = 80 + 100 * k
    else:
        k = (f - 1342) / (1500 - 1342); zr = lerp(1.25, FLOOR_Z + 2.0, ease(k) * 0.6 + k * 0.4); flex = 180
    LOWER.append((f, zr, flex, RIM.lerp(V((0, 0)), ease((f - 1326) / 16))))
for f, zr, flex, xy_ in LOWER:
    teen_inverted(f, zr, flex, wob=1.5 * math.sin(f * 0.15), xy=xy_)
# beat 9: at the bottom: reach, grip the toddler's upper arms (toddler arms up)
BOT = LOWER[-1][1]
TD_ROOT = V((0, 0, FZ + T.root.z))
grip_pts = {"L": TD_ROOT + V((0.07, 0.0, 0.44)), "R": TD_ROOT + V((-0.07, 0.0, 0.44))}     # where his reach (root - 0.97) meets the toddler's forearms
for f, k in ((1504, 0.0), (1520, 0.5), (1536, 1.0), (1552, 1.0), (1580, 1.0), (1610, 1.0), (1626, 1.0)):
    zr = BOT - 0.27 * ease(k)
    rp = V((0, 0, zr)); Rb = Rx(180)
    hl = (rp + Rb @ V((0.12, 0.05, 0.75))).lerp(grip_pts["L"] + V((0, 0, 0.02)), ease(k))
    hr = (rp + Rb @ V((-0.12, 0.05, 0.75))).lerp(grip_pts["R"] + V((0, 0, 0.02)), ease(k))
    TE.key(f, V((0, 0)), 0, root_world=rp, flex=180, head=(-35, 0),
           feet={s: teen_foot(rp, Rb, s) for s in "LR"},
           hands={"L": ("w", hl, (V((0, 0, -1)), V((-1, 0, 0)))), "R": ("w", hr, (V((0, 0, -1)), V((1, 0, 0))))})
# toddler: looks up, reaches, then clings to the teen's wrists (1500-1626)
for f in range(1500, 1628, 8):
    k = ease((f - 1500) / 40)
    jaw(T, f, JAW)
    T.key(f, V((0, 0)), yb, z=FZ, flex=-12, head=(LOOK, 0),
          hands={"L": ("w", (TD_ROOT + V((0.1, -0.02, 0.38))).lerp(grip_pts["L"] + V((0.0, -0.03, 0.12)), k)),
                 "R": ("w", (TD_ROOT + V((-0.1, -0.02, 0.38))).lerp(grip_pts["R"] + V((0.0, -0.03, 0.12)), k))})
# beat 10 (1627-1764): rise together; the toddler hangs from the teen's grip
RISE0, RISE1 = 1630, 1772
rise_z = {}
for f in range(RISE0, RISE1 + 1, 2):
    u = (f - RISE0) / (RISE1 - RISE0)
    rise_z[f] = (BOT - 0.27) + ((0.5 + TE.root.z * 0.0 + 1.0) - (BOT - 0.27)) * (0.15 * u + 0.85 * ease(u))
for f in range(RISE0, RISE1 + 1, 4):
    zr = rise_z[f]; rp = V((0, 0, zr)); Rb = Rx(180)
    dz = zr - (BOT - 0.27)
    gl = grip_pts["L"] + V((0, 0, 0.02 + dz)); gr = grip_pts["R"] + V((0, 0, 0.02 + dz))
    TE.key(f, V((0, 0)), 0, root_world=rp, flex=180, head=(-35, 0), side=3 * math.sin(f * 0.2),
           feet={s: teen_foot(rp, Rb, s) for s in "LR"},
           hands={"L": ("w", gl, (V((0, 0, -1)), V((-1, 0, 0)))), "R": ("w", gr, (V((0, 0, -1)), V((1, 0, 0))))})
    # toddler hangs: root under the grip, arms up, legs dangling and kicking slightly
    tr = TD_ROOT + V((0, 0, dz))
    T.key(f, V((0, 0)), yb, root_world=tr, flex=-4, head=(-35, 10 * math.sin(f * 0.1)),
          feet={s: ("w", tr + V((0.05 if s == "L" else -0.05, -0.02, -T.root.z + T.ankle[s].z + 0.03 * math.sin(f * 0.2 + (s == "L") * 3))), Rz(yb)) for s in "LR"},
          hands={"L": ("w", gl + V((0.0, -0.03, 0.10))), "R": ("w", gr + V((0.0, -0.03, 0.10)))})   # on his forearms, above his hands
HOLD = {RB: V((-0.55, 0.45)), RA: V((0.55, 0.45))}     # beside the rim, close enough to reach his shins
# rescuers: hold his legs while he goes in (1312-1400), then haul line; haul hand over hand in beat 10
for f in range(1314, 1420, 4):
    st = TE.state.get(f) or TE.state.get(f - 2) or TE.state.get(f + 2)
    if st is None:
        continue
    rp, flex = st["rp"], st["flex"]
    Rb = Rx(flex)
    for c, s_, pos in ((RB, "R", HOLD[RB]), (RA, "L", HOLD[RA])):     # each holds the leg on his own side
        sx = -1 if c is RB else 1
        if f <= 1326:      # legs still planted: the leg is a vertical segment at the rim
            ax_ = TE.ankle[s_].x
            hipw, ank = V((ax_, RIM.y, TE.root.z * 0.9)), V((ax_, RIM.y, 0.1))
        else:
            hipw = rp + Rb @ (V((TE.ankle[s_].x * 0.6, 0.0, 0.0)) + V((0, 0, -0.08)))
            ank = teen_ank(rp, Rb, s_, flex)
        if f > 1350 and ank.z < 0.55: break
        sh = V((pos.x, pos.y, 1.38)) - V((sx * 0.15, 0, 0))          # his shoulder on the pipe side
        axis = ank - hipw; t = max(0.45, min(0.9, (sh - hipw).dot(axis) / max(1e-4, axis.length_squared)))
        if f <= 1326: t = 0.0      # his belt at the back of the hips
        leg = hipw + axis * t; adir = axis.normalized()
        leg = leg + (sh - leg).normalized() * (0.12 if f > 1326 else 0.1)     # on the surface of his leg, not its axis
        hy = yaw_to(pos, (0, 0.25))
        low = 0.0 if f <= 1326 else max(0.0, min(1.0, (1.25 - leg.z) / 0.8))                 # crouch only as far as the leg is low
        c.key(f, pos, hy, flex=10 + 25 * low, crouch=0.08 * low, head=(20, 0),
              hands={"L": ("wg", leg + adir * 0.07), "R": ("wg", leg - adir * 0.07)})
for c, pos in ((RB, HOLD[RB]), (RA, HOLD[RA])):     # waiting beside the rim, hands ready, before he bends
    for f in (1296, 1306):
        c.key(f, pos, yaw_to(pos, (0, 0.25)), flex=12, head=(10, 0), hands={"L": ("rel", (0.12, 0.14, -0.55 * c.arm)), "R": ("rel", (0.12, 0.14, -0.55 * c.arm))})
HAUL = {RA: V((-0.24, 1.6)), RB: V((-0.21, 2.6)), RC: V((-0.18, 3.6))}     # rope runs past their right side
HAUL_FROM = {RA: 1502, RB: 1492, RC: 1324}
def rope_haul_line(f):
    """haul line from the pulley out to +y, through the three haulers' hands"""
    return [PULLEY_OUT + V((0, 0.0, 0)), V((0.0, 1.2, 1.5)), V((0.03, 2.0, 1.3)), V((0.06, 2.8, 1.1)), V((0.1, 3.6, 0.9)), V((0.4, 4.2, 0.05))]
def on_line(y):
    pts = rope_haul_line(0)
    for a, b in zip(pts, pts[1:]):
        if a.y <= y <= b.y: return a.lerp(b, (y - a.y) / (b.y - a.y))
    return pts[-1]
for c in (RA, RB, RC):
    for f in range(HAUL_FROM[c], 1630, 10):     # paying out: hands slide along the rope
        p = HAUL[c]; ph = (f - 1420) / 10
        c.key(f, p, 0, flex=-8, head=(10, 0), feet={"L": ("xy", p + V((0.15, -0.25)), -10), "R": ("xy", p + V((-0.15, 0.15)), 10)},
              hands={"L": ("w", on_line(p.y - 0.55 + 0.04 * math.sin(ph))), "R": ("w", on_line(p.y - 0.36 + 0.04 * math.sin(ph)))})
    for k, f in enumerate(range(1630, 1770 if c is not RA else 1740, 8)):     # haul: lean back, hand over hand
        p = HAUL[c]; a = (k % 2)
        hl = on_line(p.y - 0.56 + 0.15 * a); hr = on_line(p.y - 0.36 - 0.15 * a)
        c.key(f, p + V((0, 0.08 * math.sin(k * math.pi / 2))), 0, flex=-18 + 6 * a, crouch=0.12, head=(15, 0),
              feet={"L": ("xy", p + V((0.15, -0.25)), -10), "R": ("xy", p + V((-0.15, 0.15)), 10)},
              hands={"L": ("w", hl), "R": ("w", hr)})
for f, sx in ((1, 1.0), (1330, 1.0), (1345, 0.9), (1770, 0.9), (1790, 1.0)):
    TE.o.scale = (sx, sx, 1.0); TE.o.keyframe_insert("scale", frame=f)
# ================================================================== BEAT 11: emerge, lift, mother, cheers
# teen comes out (feet, body), swung upright onto the +y side, holding the toddler; lifts him up; mother takes him
TE.elbow_out = 0.35
OUTP = V((-0.3, 0.95))
for f in range(1772, 1812, 4):
    k = ease((f - 1772) / 40)
    # pulled out legs first and swung down sideways onto his feet: a single rotation about Y (no root spin),
    # head-down (Rx 180) -> upright facing the crowd (Rz 180)
    zr = lerp(rise_z[RISE1], TE.root.z, k)
    xy = V((0, 0)).lerp(OUTP, k)
    rp = V((xy.x, xy.y, zr)); Rb = Rx(180) @ Matrix.Rotation(R_(-180 * k), 3, "Y")
    if k < 0.85:
        feet = {s: teen_foot(rp, Rb, s, 180 * (1 - k)) for s in "LR"}
    else:
        feet = {s: ("xy", OUTP + V((0.12 if s == "R" else -0.12, 0.0)), 180) for s in "LR"}
    gl = rp + Rb @ V((0.28, -0.45, 0.55 - 0.35 * k)); gr = rp + Rb @ V((-0.28, -0.45, 0.55 - 0.35 * k))
    TE.key(f, xy, 0, root_world=rp if k < 0.85 else None, flex=180, side=-180 * k, head=(-20, 0), feet=feet,
           hands={"L": ("wg", gl), "R": ("wg", gr)})
    # ResA, behind him on the +y side, grips his hips and guides him out and down onto his feet
    RAP = V((-0.6, -0.15))      # behind-left of him: clear of his swinging head, legs and the toddler in front
    d_ = (RAP - xy).normalized().to_3d(); pp_ = V((-d_.y, d_.x, 0))     # toward ResA, and across
    RA.key(f, RAP, yaw_to(RAP, xy), flex=22, crouch=0.06, head=(15, 0),
           hands={"L": ("wg", rp + V((0.02, -0.21, 0.08))), "R": ("wg", rp + V((-0.1, -0.19, -0.06)))})
    tr = (gl + gr) / 2 + V((0, 0, -0.52))
    T.key(f, V((0, 0)), yb + 160 * k, root_world=tr, flex=0, head=(-25, 0),
          feet={s: ("w", tr + V((0.05 if s == "L" else -0.05, 0, -T.root.z + T.ankle[s].z + 0.04)), Rz(yb)) for s in "LR"},
          hands={"L": ("w", gl + Rb @ V((0.0, 0.09, 0.0))), "R": ("w", gr + Rb @ V((0.0, 0.09, 0.0)))})
# hold up (1816-1870) then hand to the mother (1870-1950)
for i, f in enumerate(range(1816, 1872, 8)):
    k = ease((f - 1816) / 30)
    yawT = 180 - 30 * k
    rp = V((OUTP.x, OUTP.y, TE.root.z))
    gl = rp + Rz(yawT) @ V((0.25, -0.3, 0.25 + 0.75 * k)); gr = rp + Rz(yawT) @ V((-0.25, -0.3, 0.25 + 0.75 * k))
    TE.key(f, OUTP, yawT, flex=-8 * k, head=(-20 * k, 0), hands={"L": ("wg", gl), "R": ("wg", gr)})
    tr = (gl + gr) / 2 + V((0, 0, -0.18))
    T.key(f, V((0, 0)), yawT + 180 - 180, root_world=tr, flex=0, head=(-10, 8 * math.sin(i)),
          feet={s: ("w", tr + V((0.05 if s == "L" else -0.05, 0, -T.root.z + T.ankle[s].z + 0.02)), Rz(yawT)) for s in "LR"},
          hands={"L": ("wg", gl + Rz(yawT) @ V((0.0, 0.16, 0.08))), "R": ("wg", gr + Rz(yawT) @ V((0.0, 0.16, 0.08)))})
# mother: ducks the tape, runs in, takes him in a hug
MO.walk([V(CROWD_POS["Mother"]), V((-1.0, 5.2)), V((-0.8, 3.2)), V((-0.6, 1.9))], 1800, 1866, stride=1.0, lift=0.11, arm_swing=0.3, lean=10)
MP = V((-0.6, 1.9)); myaw = yaw_to(MP, OUTP)
HELD0 = OUTP.to_3d() + V((0, 0, TE.root.z + 1.0 - 0.08)) + Rz(150) @ V((0, -0.3, 0))     # where the hold-up left him
for i, f in enumerate(range(1872, END + 10, 4)):
    k = ease((f - 1872) / 34)
    cr_ = 0.42 * MO.root.z * ease((f - 1896) / 34)
    hug = MP.to_3d() + V((0, 0, MO.root.z + 0.44 - cr_)) + Rz(myaw) @ V((0, -0.3, 0))
    held = HELD0.lerp(hug, k)
    jaw(T, f, JAW * max(0.0, 1 - ease((f - 1890) / 40)))
    MO.key(f, MP, myaw + 4 * math.sin(i * 0.7), flex=8 + 10 * (cr_ > 0.05), crouch=cr_, head=(10, 0), twist=10 * math.sin(i * 0.5),
           feet={"L": ("xy", MP + (Rz(myaw) @ V((0.12, 0.12, 0))).to_2d(), myaw), "R": ("xy", MP + (Rz(myaw) @ V((-0.12, -0.05, 0))).to_2d(), myaw, 0.0, 0.0)},
           hands={"L": ("w", held + Rz(lerp(150, myaw + 180, k) - 180) @ V((0.27, 0.1, -0.02))), "R": ("w", held + Rz(lerp(150, myaw + 180, k) - 180) @ V((-0.23, 0.05, 0.02)))} if k >= 0.3 else
                 {"L": ("rel", (0.1, 0.45, 0.3 * MO.arm)), "R": ("rel", (0.1, 0.45, 0.3 * MO.arm))})   # reaching up for him until he is in reach   # both arms: under him and across his back
    T.key(f, V((0, 0)), lerp(150, myaw + 180, k), root_world=held + V((0, 0, -0.1)), flex=10, head=(5 + 10 * k, 25 * k),
          feet={s: ("w", held + V((0.05 if s == "L" else -0.05, 0, -0.1 - T.root.z + T.ankle[s].z + 0.05)), Rz(myaw + 180)) for s in "LR"},
          hands={"L": ("wg", held + Rz(myaw) @ V((0.17, 0.2, 0.34))), "R": ("wg", held + Rz(myaw) @ V((-0.17, 0.2, 0.34)))})
    TE.key(f, OUTP, 150 - 20 * k, flex=-5, head=(-15, 0),
           hands={"L": UP(TE, 0.25, 0.1), "R": UP(TE, 0.25, 0.1)} if k > 0.55 else {"L": ("wg", held + Rz(lerp(150, myaw + 180, k)) @ V((0.25, 0.0, 0.08))), "R": ("wg", held + Rz(lerp(150, myaw + 180, k)) @ V((-0.25, 0.0, 0.08)))})
for c, p in ((RA, V((0.95, 1.75))), (RB, V((-1.75, 1.3))), (RC, V((1.0, 3.3)))):
    for i, f in enumerate(range(1836, END + 10, 10)):
        ph = i * 1.4
        c.key(f, p, yaw_to(p, OUTP), crouch=0.04 * abs(math.sin(ph)), head=(-10, 0),
              hands={"L": UP(c, 0.2 + 0.1 * math.sin(ph * 2), 0.05), "R": UP(c, 0.2 + 0.1 * math.cos(ph * 2), 0.05)} if i % 6 < 4 else
                    {"L": ("rel", (-0.04, 0.35, -0.05 + 0.08 * (i % 2))), "R": ("rel", (-0.04, 0.35, -0.05 + 0.08 * (i % 2)))})


# ================================================================== WALKS between standing spots (no sliding feet)
def clear_keys(c, f0, f1):
    ad = c.o.animation_data
    if not ad or not ad.action: return
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    kill = [i for i, kp in enumerate(fc.keyframe_points) if f0 < kp.co.x < f1]
                    for i in reversed(kill): fc.keyframe_points.remove(fc.keyframe_points[i])
MOVES = [
 (RA, 470, 520, [RA_P, (-0.9, 0.75), (-1.12, 0.92)]), (RA, 674, 690, [(-1.12, 0.92), (-1.1, 1.5)]), (RA, 905, 925, [(-1.1, 1.5), (-0.9, 0.9)]),
 (RA, 1140, 1188, [(-0.9, 0.9), (-0.15, 0.72), (0.55, 0.1), (0.75, -0.3)]), (RA, 1290, 1312, [(0.75, -0.3), (0.95, 0.3), (0.55, 0.45)]),
 (RA, 1430, 1500, [(0.55, 0.45), (0.85, -0.2), (0.0, -0.6), (-0.3, -0.5), (-0.8, -0.2), (-0.85, 0.9), (-0.24, 1.6)]), (RA, 1742, 1766, [(-0.24, 1.6), (-0.95, 0.9), (-0.9, -0.1), (-0.6, -0.15)]), (RA, 1812, 1836, [(-0.6, -0.15), (0.4, -0.7), (1.2, 0.2), (0.95, 1.75)]),
 (RB, 470, 525, [RB_P, (1.0, -0.6), (1.6, -2.2)]), (RB, 674, 702, [(1.6, -2.2), (0.2, -0.6), (-0.45, 0.6), (-0.2, 1.8), (0.4, 2.6)]),
 (RB, 905, 925, [(0.4, 2.6), (0.1, 1.9)]), (RB, 1130, 1162, [(0.1, 1.9), (-0.3, 0.55), tuple(RBT)]),
 (RB, 1262, 1288, [tuple(RBT), (-0.95, 0.9), (-0.55, 0.45)]), (RB, 1430, 1490, [(-0.55, 0.45), (-0.85, 0.5), (-0.45, 1.6), (-0.21, 2.6)]),
 (RB, 1770, 1830, [(-0.21, 2.6), (-1.2, 2.4), (-2.1, 1.7), (-1.75, 1.3)]),
 (RC, 463, 560, [RC_P, (-1.4, -0.9), (0.3, -2.4), (1.9, -2.8)]), (RC, 674, 702, [(1.9, -2.8), (0.5, -2.4), (-1.7, -1.2), (-2.4, 1.2)]),
 (RC, 905, 920, [(-2.4, 1.2), (-1.9, 0.2)]), (RC, 1130, 1170, [(-1.9, 0.2), (-2.3, 1.4), (-1.6, 2.7), (-0.2, 2.6)]),
 (RC, 1300, 1322, [(-0.2, 2.6), (-0.18, 3.6)]), (RC, 1770, 1795, [(-0.18, 3.6), (1.0, 3.3)]),
]
for c, f0, f1, pts in MOVES:
    clear_keys(c, f0, f1)
    c.walk([V(p) for p in pts], f0, f1, stride=0.75 if (f1 - f0) > 30 else 0.95, lift=0.09)
# ================================================================== PROPS / FX
def key_vis(o, frames_on):
    """frames_on: list of (start, end) where visible"""
    o.hide_render = True; o.keyframe_insert("hide_render", frame=1)
    for a, b in frames_on:
        o.hide_render = False; o.keyframe_insert("hide_render", frame=a)
        o.hide_render = True; o.keyframe_insert("hide_render", frame=b)
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
tripod = [o for o in bpy.data.objects if o.name.startswith(("Tripod", "Pulley"))]
for o in tripod: key_vis(o, [(230, END + 10)])     # appears while the camera is down the shaft
# ropes
def set_curve(ob, f, pts):
    sp = ob.data.splines[0]; n = len(sp.points)
    # resample the polyline to n points
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (b - a).length)
    for i in range(n):
        s_ = L[-1] * i / (n - 1)
        for j in range(1, len(L)):
            if L[j] >= s_ - 1e-9:
                t = (s_ - L[j - 1]) / max(1e-9, L[j] - L[j - 1]); p = pts[j - 1].lerp(pts[j], t); break
        sp.points[i].co = (p.x, p.y, p.z, 1); sp.points[i].keyframe_insert("co", frame=f)
RL = bpy.data.objects["RopeLoop"]; RM = bpy.data.objects["RopeMain"]; RW = bpy.data.objects["RopeWaist"]
key_vis(RL, [(241, 480)]); key_vis(RM, [(1180, END + 10)]); key_vis(RW, [(1150, END + 10)])
for f in range(241, 481, 2):
    d = loop_depth.get(f, loop_depth[max(k for k in loop_depth if k <= f)] if f > 241 else -0.3)
    top = V((-0.24, 0.17, 1.0))
    sw = 0.08 * math.sin(f * 0.22) if f > 400 else 0.02 * math.sin(f * 0.3)
    bottom = V((sw, 0.02 * math.cos(f * 0.2), d))
    pts = [top + V((-0.15, 0.25, -0.4)), top, V((-0.03, 0.02, 0.1)), V((sw * 0.3, 0, max(d + 1.0, -0.4))), bottom + V((0, 0, 0.25))]
    loop = [bottom + V((0.13 * math.cos(a), 0.13 * math.sin(a), 0.03 * math.sin(2 * a))) for a in [i * math.pi / 6 for i in range(13)]]
    set_curve(RL, f, pts + loop)
for f in range(1150, END + 10, 2):
    # waist loop follows the teen's pelvis
    st = None
    keys = sorted(TE.state)
    kk = max([k for k in keys if k <= f] or [keys[0]]); st = TE.state[kk]
    rp, yaw, flex = st["rp"], st["yaw"], st["flex"]
    Rb = Rz(yaw) @ Rx(flex)
    c_ = rp + Rb @ V((0, -0.05, 0.12))
    rx, ry = 0.175, 0.135
    ring = [c_ + Rb @ V((rx * math.cos(a), ry * math.sin(a), 0)) for a in [i * 2 * math.pi / 20 for i in range(21)]]
    if f < 1250:   # loose ends in ResB's hands before the knot is tight
        ring = ring[:14]
    set_curve(RW, f, ring)
    if f >= 1180:
        knot_w = c_ + Rb @ V((0, -0.14, 0))
        line = rope_haul_line(f)
        if f < 1300:
            pts = [knot_w, knot_w + V((0.1, 0.25, -0.8)), V((0.2, 1.4, 0.03)), V((0.4, 2.6, 0.03)), V((0.4, 4.2, 0.03))]
        else:
            pts = [knot_w, PULLEY_IN + V((0, 0.0, 0.0)), PULLEY_TOP, ] + line
        set_curve(RM, f, pts)
# sand trickles + time-lapse sky/sun + clouds
for o in bpy.data.objects:
    if o.name.startswith("SandTrickle"):
        mp = o.material_slots[0].material.node_tree.nodes["TrickleMap"]
        mp.inputs["Location"].default_value = (0, 0, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=1)
        mp.inputs["Location"].default_value = (0, -120, 0); mp.inputs["Location"].keyframe_insert("default_value", frame=END)
        break
sky = bpy.context.scene.world.node_tree.nodes["Sky"]; sun = bpy.data.objects["Sun"]
def key_sun(f, elev, rot, energy, col):
    sky.sun_elevation = R_(elev); sky.sun_rotation = R_(rot)
    sky.keyframe_insert("sun_elevation", frame=f); sky.keyframe_insert("sun_rotation", frame=f)
    sun.rotation_euler = (R_(90 - elev), 0, R_(rot - 90)); sun.keyframe_insert("rotation_euler", frame=f)
    sun.data.energy = energy; sun.data.color = col; sun.data.keyframe_insert("energy", frame=f); sun.data.keyframe_insert("color", frame=f)
key_sun(1, 52, 130, 3.2, (1.0, 0.96, 0.9)); key_sun(680, 56, 145, 3.2, (1.0, 0.96, 0.9))
key_sun(790, 42, 215, 3.0, (1.0, 0.93, 0.84)); key_sun(905, 24, 262, 2.8, (1.0, 0.86, 0.7)); key_sun(END, 22, 266, 2.8, (1.0, 0.85, 0.7))
cm = bpy.data.materials["M_Clouds"].node_tree.nodes["CloudMap"]
for f, x in ((1, 0), (673, 40), (905, 900), (END, 1000)):
    cm.inputs["Location"].default_value = (x, x * 0.3, 0); cm.inputs["Location"].keyframe_insert("default_value", frame=f)
# lights: cross-section fill, shaft fill, head torch, lens glow
XL = bpy.data.lights["XsecFill"]; SFL = bpy.data.lights["ShaftFill"]; HT = bpy.data.lights["HeadTorch"]
def key_light(l, pts):
    for f, e in pts: l.energy = e; l.keyframe_insert("energy", frame=f)
key_light(XL, [(1, 0), (455, 0), (470, 11000), (545, 11000), (560, 0), (770, 0), (785, 11000), (860, 11000), (875, 0), (1342, 0), (1350, 9000), (1745, 11000), (1765, 0)])
key_light(SFL, [(1, 0), (110, 0), (140, 300), (250, 300), (258, 60), (292, 60), (300, 300), (1300, 300), (1340, 40), (1770, 40)])
_sd = bpy.data.materials["M_ShaftDust"].node_tree.nodes["Principled Volume"].inputs["Density"]     # no glowing dust in front of the lens on the rise up the shaft
for f_, v_ in ((1, 0.06), (250, 0.06), (256, 0.0), (292, 0.0), (298, 0.06)):
    _sd.default_value = v_; _sd.keyframe_insert("default_value", frame=f_)
key_light(HT, [(1, 0), (1320, 0), (1335, 90), (1780, 90), (1800, 0)])
for n_ in ("Teen.torch_strap", "Teen.torch_lamp", "Teen.torch_lens"): key_vis(bpy.data.objects[n_], [(1240, END + 10)])
lens = bpy.data.materials["M_TorchLens"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
for f, e in ((1, 0), (1320, 0), (1335, 30), (1780, 30), (1800, 0)): lens.default_value = e; lens.keyframe_insert("default_value", frame=f)

# ================================================================== EXCAVATOR: roll in, dig cycles, pit + spoil heap grow
EX = bpy.data.objects["Excavator"]; body = bpy.data.objects["Body_GEO"]; boom = bpy.data.objects["arm_01_GEO1"]; stick = bpy.data.objects["Arm_2_GEO"]
shovel = bpy.data.objects["shovel_GEO"]
base = {o.name: o.rotation_euler.copy() for o in (body, boom, stick, shovel)}
def key_ex(f, x, y, swing, b, s, sh):
    EX.location = (x, y, 0); EX.keyframe_insert("location", frame=f)
    body.rotation_euler = base["Body_GEO"].copy(); body.rotation_euler.z += R_(swing); body.keyframe_insert("rotation_euler", frame=f)
    boom.rotation_euler = base["arm_01_GEO1"].copy(); boom.rotation_euler.x += R_(b); boom.keyframe_insert("rotation_euler", frame=f)
    stick.rotation_euler = base["Arm_2_GEO"].copy(); stick.rotation_euler.x += R_(s); stick.keyframe_insert("rotation_euler", frame=f)
    shovel.rotation_euler = base["shovel_GEO"].copy(); shovel.rotation_euler.x += R_(sh); shovel.keyframe_insert("rotation_euler", frame=f)
key_ex(1, 22, 1.0, 0, -20, 30, 20); key_ex(478, 22, 1.0, 0, -20, 30, 20)
key_ex(582, 7.0, 1.0, 0, -20, 30, 20)
# dig cycle: reach (boom down, stick out), curl, lift, swing to the heap, dump, swing back
def dig(f0, period, n):
    for i in range(n):
        f = f0 + i * period; p = period
        key_ex(int(f), 7.0, 1.0, 0, -5, 55, -10)                  # reach out over the pit
        key_ex(int(f + p * 0.25), 7.0, 1.0, 0, 15, 35, 30)          # bite down
        key_ex(int(f + p * 0.45), 7.0, 1.0, 0, -15, 15, 70)         # curl + lift
        key_ex(int(f + p * 0.7), 7.0, 1.0, -55, -25, 25, 60)         # swing to the heap
        key_ex(int(f + p * 0.85), 7.0, 1.0, -55, -20, 45, -20)       # dump
dig(588, 44, 2); dig(676, 26, 9)
key_ex(913, 7.0, 1.0, -20, -30, 20, 30); key_ex(END, 7.0, 1.0, -25, -32, 18, 32)
# operator seated in the cab (MPFB), parented to the swinging cab
OP = Char("Operator")
for i, f in enumerate(range(1, END + 10, 22)):
    ph = i * 1.7
    OP.key(f, V((0, 0)), 0, root_world=V((0, 0, 0.45)), flex=-4 + 6 * math.sin(ph), head=(8, 18 * math.sin(ph * 0.6)),
           feet={"L": ("w", V((0.12, -0.42, 0.08)), Rz(0)), "R": ("w", V((-0.12, -0.38, 0.08)), Rz(0))},
           hands={"L": ("w", V((0.26, -0.5, 0.8 + 0.05 * math.sin(ph)))), "R": ("w", V((-0.26, -0.5, 0.8 + 0.05 * math.cos(ph))))})
bpy.context.scene.frame_set(600)
chair = bpy.data.objects["Body_GEO_Chair_MAT_0"]; bb = [chair.matrix_world @ V(c_) for c_ in chair.bound_box]
seat = V((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8, min(v.z for v in bb) + 0.42 * (max(v.z for v in bb) - min(v.z for v in bb))))
body_w = bpy.data.objects["Body_GEO"].matrix_world.copy()
OP.o.matrix_world = Matrix.Translation(V((seat.x, seat.y, min(v.z for v in bb) + 0.02))) @ Matrix.Rotation(R_(-90), 4, "Z")
mw = OP.o.matrix_world.copy(); OP.o.parent = bpy.data.objects["Body_GEO"]; OP.o.matrix_parent_inverse = body_w.inverted(); OP.o.matrix_world = mw
print("OPERATOR seat", seat)
pit = bpy.data.objects["EarthBack"].data.shape_keys.key_blocks["Pit"]
for f, v in ((1, 0), (575, 0), (680, 0.25), (905, 0.95), (END, 0.95)):
    pit.value = v; pit.keyframe_insert("value", frame=f)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(3.6, 2.6, -0.1))
HEAP = bpy.context.object; HEAP.name = "SpoilHeap"; HEAP.data.materials.append(bpy.data.materials["M_Soil"])
_tx = bpy.data.textures.new("HeapLumps", "CLOUDS"); _tx.noise_scale = 0.18; _tx.noise_depth = 3
_d = HEAP.modifiers.new("lumps", "DISPLACE"); _d.texture = _tx; _d.strength = 0.22; _d.texture_coords = "LOCAL"
for v in HEAP.data.vertices:
    v.co.z = max(-0.05, v.co.z) * (0.7 + 0.15 * math.sin(v.co.x * 5) * math.cos(v.co.y * 4))
for p in HEAP.data.polygons: p.use_smooth = True
HEAP.data.uv_layers.new()
for f, s in ((1, 0.01), (575, 0.01), (680, 0.35), (905, 0.85), (END, 0.85)):
    HEAP.scale = (s * 1.1, s * 0.9, s * 0.7); HEAP.keyframe_insert("scale", frame=f)
# dirt clods thrown from the bucket at each dump + into the pit at each bite
M_CLOD = bpy.data.materials["M_Soil"]
clods = []
for i in range(30):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=random.uniform(0.04, 0.11)); o = bpy.context.object; o.name = "Clod%02d" % i
    o.data.materials.append(M_CLOD); clods.append(o)
    _dc = o.modifiers.new("lumps", "DISPLACE"); _dc.texture = _tx; _dc.strength = 0.05; _dc.texture_coords = "LOCAL"
def throw(o, f0, p0, v0, dur=30):
    o.location = p0; o.scale = (0.001,) * 3; o.keyframe_insert("location", frame=f0 - 1); o.keyframe_insert("scale", frame=f0 - 1)
    for k in range(0, dur + 1, 3):
        t = k / 60.0; p = p0 + v0 * t + V((0, 0, -4.9 * t * t))
        if p.z < 0.03: p.z = 0.03
        o.location = p; o.scale = (1, 1, 1); o.keyframe_insert("location", frame=f0 + k); o.keyframe_insert("scale", frame=f0 + k)
        o.rotation_euler = (k * 0.3, k * 0.2, 0); o.keyframe_insert("rotation_euler", frame=f0 + k)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=f0 + dur + 2)
cyc = [(588 + i * 44, 44) for i in range(2)] + [(676 + i * 26, 26) for i in range(9)]
for ci, (f0, p) in enumerate(cyc):
    dump = int(f0 + p * 0.85)
    bpy.context.scene.frame_set(dump)
    sco = bpy.data.objects["shovel_GEO_Scoop_MAT_0"]; bb = [sco.matrix_world @ V(c_) for c_ in sco.bound_box]; bc = sum(bb, V()) / 8
    for j in range(10):
        o = clods[(ci * 10 + j) % len(clods)]
        throw(o, dump + j % 4, bc + V((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), -0.1)), V((random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), random.uniform(-1.0, 0.6))), dur=30)
# dust puffs (soft volumetric balls) at each bite and around the landing in the shaft
M_DUST = bpy.data.materials.new("M_DustPuff"); M_DUST.use_nodes = True; nt = M_DUST.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); pv = nt.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = 1.2; pv.inputs["Color"].default_value = (0.75, 0.62, 0.48, 1)
tc = nt.nodes.new("ShaderNodeTexCoord"); gr = nt.nodes.new("ShaderNodeTexGradient"); gr.gradient_type = "SPHERICAL"; nt.links.new(tc.outputs["Object"], gr.inputs[0])
nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4; nt.links.new(tc.outputs["Object"], nz.inputs[0])
mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; nt.links.new(gr.outputs["Fac"], mm.inputs[0]); nt.links.new(nz.outputs["Fac"], mm.inputs[1])
dn = nt.nodes.new("ShaderNodeMath"); dn.operation = "MULTIPLY"; dn.inputs[1].default_value = 1.2; nt.links.new(mm.outputs[0], dn.inputs[0])
nt.links.new(dn.outputs[0], pv.inputs["Density"]); nt.links.new(pv.outputs[0], o_.inputs["Volume"])
def puff(name, loc, f0, r0, r1, dur):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=loc); o = bpy.context.object; o.name = name
    o.data.materials.append(M_DUST); o.visible_shadow = False
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=f0 - 1)
    o.scale = (r0,) * 3; o.keyframe_insert("scale", frame=f0)
    o.scale = (r1,) * 3; o.location = V(loc) + V((0, 0, r1 * 0.4)); o.keyframe_insert("scale", frame=f0 + dur); o.keyframe_insert("location", frame=f0 + dur)
    o.scale = (0.001,) * 3; o.keyframe_insert("scale", frame=f0 + dur + 1)
    return o
puff("DustLand", (0, 0, FLOOR_Z + 0.1), 199, 0.08, 0.26, 50)
for ci, (f0, p) in enumerate(cyc[::2]):
    puff("DustBite%02d" % ci, (2.0, 0.9, 0.1), int(f0 + p * 0.3), 0.2, 0.9, 40)
puff("DustRoll", (10, 1.0, 0.3), 540, 0.5, 2.0, 90)
# diesel exhaust from the engine deck (rear of the cab), dark puffs every ~0.4 s while it works
M_EXH = M_DUST.copy(); M_EXH.name = "M_Exhaust"; M_EXH.node_tree.nodes["Principled Volume"].inputs["Color"].default_value = (0.18, 0.17, 0.16, 1)
bpy.context.scene.frame_set(600)
eb = [o for o in bpy.data.objects if o.name.startswith("Body_GEO_Body")][0]; bb = [eb.matrix_world @ V(c_) for c_ in eb.bound_box]
EXH = V((max(v.x for v in bb) - 0.3, sum(v.y for v in bb) / 8 + 0.35, max(v.z for v in bb) + 0.1))
for k_, f in enumerate(range(590, 912, 24)):
    o = puff("Exhaust%02d" % k_, EXH, f, 0.08, 0.55, 40); o.data.materials[0] = M_EXH
    o.location = EXH + V((0.3, 0.2, 0.9)); o.keyframe_insert("location", frame=f + 40)
puff("DustToddler", (-0.6, -0.5, 0.05), 20, 0.1, 0.5, 70)

# extra crowd: duplicates of the four villagers with a 0-2 s time offset (NLA), scale and clothes-colour variety
def tinted(mat, rgb):
    m = mat.copy(); m.name = mat.name + "_v"
    for nd in list(m.node_tree.nodes):
        if nd.type == "TEX_IMAGE" and nd.image and "diffuse" in nd.image.name.lower():
            for lk in list(nd.outputs["Color"].links):
                mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1
                mx.inputs["B"].default_value = (*rgb, 1); m.node_tree.links.new(nd.outputs["Color"], mx.inputs["A"]); m.node_tree.links.new(mx.outputs["Result"], lk.to_socket)
    return m
SPOTS = [(5.4, 0.7, -14, 0.0), (-5.0, 0.5, 13, 1.0), (1.7, 2.7, 3, 1.6), (-3.2, 2.1, 9, 0.5), (6.8, 3.4, -12, 1.3)]
COLS = [(0.6, 0.85, 1.1), (1.15, 0.8, 0.6), (0.75, 1.05, 0.7), (1.1, 1.05, 0.8), (0.85, 0.7, 1.05)]
for k, (dx, dy, rz, toff) in enumerate(SPOTS):
    for j, n in enumerate(("Crowd1", "Crowd2", "Crowd3", "Crowd4")):
        src = bpy.data.objects[n]; nr = src.copy(); nr.name = "%s_dup%d" % (n, k); bpy.context.scene.collection.objects.link(nr)
        nr.animation_data_clear(); ad = nr.animation_data_create()
        act = src.animation_data.action; tr = ad.nla_tracks.new()
        off = int(toff * 60 + j * 17)
        st = tr.strips.new("off", 1 - off, act); st.extrapolation = "HOLD"
        try: st.action_slot = src.animation_data.action_slot
        except Exception: pass
        sca = random.uniform(0.93, 1.06)
        nr.matrix_world = Matrix.Translation(V((dx, dy, 0))) @ Matrix.Rotation(R_(rz), 4, "Z") @ Matrix.Scale(sca, 4)
        for ch in src.children:
            cc = ch.copy(); cc.name = ch.name + "_dup%d" % k; bpy.context.scene.collection.objects.link(cc); cc.parent = nr
            for md in cc.modifiers:
                if md.type == "ARMATURE": md.object = nr
            if "suit" in ch.name:
                for slot in cc.material_slots:
                    base = slot.material
                    if base: slot.link = "OBJECT"; slot.material = tinted(base, COLS[(k + j) % len(COLS)])
# ================================================================== HANDS: shared pose library (pipeline/hand_poses.py)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../pipeline/hand_poses.py")).read())
GRIPS = {"ResA": [(241, 470, "wrap_grip"), (1190, 1290, "wrap_grip"), (1314, 1420, "cup_hold"), (1502, 1740, "wrap_grip"), (1776, 1812, "wrap_grip")],
         "ResB": [(1164, 1262, "wrap_grip"), (1314, 1420, "cup_hold"), (1492, 1770, "wrap_grip")],
         "ResC": [(1324, 1770, "wrap_grip")], "Teen": [(1530, 1872, "cup_hold")], "Toddler": [(1530, 1812, "cup_hold")],
         "Mother": [(1872, END + 10, "cup_hold")], "Crowd1": [(470, 1760, "flat_palm")], "Operator": [(1, END + 10, "wrap_grip")]}
for o in [o for o in bpy.data.objects if o.type == "ARMATURE" and "_dup" not in o.name and (o.name in CH or o.name == "Operator")]:
    add_hand_limits(o)
    for sd in "LR": apply_pose(o, sd, "relaxed", 1)
    for a_, b_, pose in GRIPS.get(o.name, []):
        for sd in "LR":
            if a_ > 7: apply_pose(o, sd, "relaxed", a_ - 6)
            apply_pose(o, sd, pose, a_); apply_pose(o, sd, pose, b_)
            if b_ + 6 < END: apply_pose(o, sd, "relaxed", b_ + 6)

# beats.json
first = {1: "The toddler fell", 2: "Rescuers lowered ropes", 3: "They even brought in heavy machinery", 4: "But after 11 hours",
         5: "Finally, a teenager", 6: "A rope was tied", 7: "and he was lowered", 8: "With a flashlight", 9: "he reached out his arms",
         10: "And when they pulled him", 11: "he brought the toddler up alive"}
json.dump([{"beat": b, "frame": f, "first_words": first[b]} for b, f in BEAT.items()], open(os.path.join(os.path.dirname(os.path.abspath(OUT)), "..", "beats.json"), "w"), indent=1)
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM SAVED", OUT)
