"""DonationBin v006 acting + camera re-stage (director). Runs on the v004 timeline (frames 1-2490), before the VO retime.
blender -b 09.blend --python fix09.py -- out.blend
Replaces the woman's performance from the shove to the rescue sit-up (old frames 158-2094), the shover's hand
placement, and the camera inside the bin. Story beats and their frames are unchanged, so the same VO anchors apply."""
import sys, math, json
import bpy
from mathutils import Vector, Matrix, Quaternion
exec(open("/home/user/Muhammed/blender/pipeline/anim_lib.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
FY = sc["bin_front_y"]
COLL = [bpy.data.objects[n] for n in sc["pile_colliders"].split(",")]
def ground_z(x, y):
    if -0.73 < x < 0.73 and -0.58 < y < 0.58:
        z = 0.0
        for o in COLL:
            inv = o.matrix_world.inverted()
            hit, loc, nrm, idx = o.ray_cast(inv @ Vector((x, y, 3.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
            if hit: z = max(z, (o.matrix_world @ loc).z)
        return z
    return 0.0
PZ = ground_z

class Body(Human):
    def __init__(self, rig, obj):
        super().__init__(rig); self.obj = obj; B = rig.BN
        self.knee = {s: B["lowerleg01." + s].head_local.copy() for s in "LR"}
        self.elbow = {s: B["lowerarm01." + s].head_local.copy() for s in "LR"}
        self.wrist = {s: B["wrist." + s].head_local.copy() for s in "LR"}
    def Mb(self, pos, yaw, flex, side):
        Rw = Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(flex), 3, 'X') @ Matrix.Rotation(R_(side), 3, 'Y')
        return Matrix.Translation(pos) @ Rw.to_4x4() @ Matrix.Translation(-self.root_head)
    def key_pole(self, n, f, P):
        pb = self.r.PB[n]
        pb.location = self.r.rest(n).to_3x3().inverted() @ (P - self.r.BN[n].head_local)
        pb.keyframe_insert("location", frame=f, group=n)
    def pose(self, f, pos, yaw=0.0, flex=0.0, side=0.0, sp=(0, 0, 0), head=(0, 0), hands=None, feet=None, jaw=0.0, curl=None):
        pos = Vector(pos)
        self.key_root(f, pos, yaw=yaw, flex=flex, side=side)
        self.key_spine(f, flex=sp[0], twist=sp[1], side=sp[2], head=head)
        M = self.Mb(pos, yaw, flex, side)
        for s in "LR":
            sx = 1 if s == "L" else -1
            spec = (feet or {}).get(s, ("r", (0, 0, 0)))
            if spec[0] == "g":
                self.key_foot(s, f, Vector(spec[1]), spec[2], spec[3] if len(spec) > 3 else 0.0, spec[4] if len(spec) > 4 else 0.0)
                if len(spec) > 5:     # explicit knee direction (world) for bent-knee lying / kneeling
                    self.key_pole("Pole_knee." + s, f, Vector(spec[5]))
            else:
                d = Vector(spec[1]); a = self.ankle[s]; pt = spec[2] if len(spec) > 2 else 0.0
                T = M @ Matrix.Translation(a + d) @ Matrix.Rotation(R_(pt), 4, 'X') @ Matrix.Translation(-a) @ self.r.rest("IK_foot." + s)
                self.r.key_world("IK_foot." + s, f, T)
                self.key_pole("Pole_knee." + s, f, M @ (self.knee[s] + Vector((0, -0.6, 0)) + d * 0.5))
            hs = (hands or {}).get(s, ("r", (0, 0, 0)))
            pole = M @ (self.elbow[s] + Vector((0.25 * sx, 0.55, -0.1)))
            if hs[0] == "w":
                W, d_, n_ = Vector(hs[1]), Vector(hs[2]), Vector(hs[3])
                if len(hs) > 4: pole = Vector(hs[4])
                self.key_hand(s, f, W, d_, n_, pole=pole)
            else:
                d = Vector(hs[1]); rot = hs[2] if len(hs) > 2 else (0, 0, 0); w = self.wrist[s]
                Rl = (Matrix.Rotation(R_(rot[2]), 4, 'Z') @ Matrix.Rotation(R_(rot[1]), 4, 'Y') @ Matrix.Rotation(R_(rot[0]), 4, 'X'))
                T = M @ Matrix.Translation(w + d) @ Rl @ Matrix.Translation(-w) @ self.r.rest("IK_hand." + s)
                self.r.key_world("IK_hand." + s, f, T)
                self.key_pole("Pole_elbow." + s, f, M @ (self.elbow[s] + Vector((0.25 * sx, 0.55, -0.1)) + d * 0.5))
        if "jaw" in self.r.PB:
            self.r.key_rot("jaw", f, [("X", jaw)])
        c = curl if curl is not None else {"L": 0.3, "R": 0.3}
        for s in "LR":
            for i in range(1, 6):
                for j in (1, 2, 3):
                    n = "finger%d-%d.%s" % (i, j, s)
                    if n in self.r.PB:
                        pb = self.r.PB[n]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(c[s] * (55 if i > 1 else 25)))
                        pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

def clear_keys(obj, f0, f1, bones_only=True):
    ad = obj.animation_data
    for l in ad.action.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if bones_only and not fc.data_path.startswith("pose.bones"): continue
                    for k in [k for k in fc.keyframe_points if f0 <= k.co.x <= f1][::-1]:
                        fc.keyframe_points.remove(k, fast=True)
                    fc.update()

WOo = bpy.data.objects["Woman"]; SHo = bpy.data.objects["Shover"]
for o in (WOo, SHo):
    for pb in o.pose.bones: pb.rotation_mode = 'QUATERNION'
WO = Body(Rig(WOo), WOo); SH = Body(Rig(SHo), SHo)
RH = WO.root_head.z
def fwd(yaw):  return Vector((math.sin(R_(yaw)), -math.cos(R_(yaw)), 0))     # facing direction
def lat(yaw):  return Vector((math.cos(R_(yaw)), math.sin(R_(yaw)), 0))      # her left
def stand_feet(x, y, yaw, lift=0.0, pitch=0.0):
    out = {}
    fw = fwd(yaw) * 0.14
    for s in "LR":
        p = WO.foot_xy(s, Vector((x, y, 0)), yaw)
        h = ground_z(p.x, p.y); t = ground_z(p.x + fw.x, p.y + fw.y)
        out[s] = ("g", (p.x, p.y), yaw, lift + max(0.0, t - h), pitch)
    return out
PALM_DOWN = Vector((0, 0, -1))

clear_keys(WOo, 158, 2094)

# ---------------------------------------------------------------- 151-294 shoved, tips over the sill, falls in, rolls onto her back
FALL = [  # f, pos, yaw, flex, side, spine, feet-delta, hand-delta L, R      (the v004 dive, unchanged to 238)
    (166, (0.0, -0.98, RH + 0.10), 180, 40, 0, (25, 0, 0), (0, 0.05, 0.10), (-0.05, -0.25, 0.45), (0.05, -0.25, 0.45)),
    (182, (0.0, -0.86, RH + 0.42), 180, 72, 5, (20, 0, 0), (0, 0.10, 0.25), (0.05, -0.35, 0.65), (-0.05, -0.35, 0.65)),
    (200, (0.0, -0.66, 1.30), 180, 100, 8, (10, 8, 0), (0, 0.05, 0.25), (0.10, -0.30, 0.70), (-0.10, -0.30, 0.70)),
    (218, (0.02, -0.42, 1.36), 175, 135, 10, (-10, 10, 0), (0, 0.10, 0.20), (0.25, -0.20, 0.55), (-0.25, -0.10, 0.60)),
    (238, (0.04, -0.20, 1.18), 165, 170, 12, (-5, 0, 0), (0, 0.0, 0.15), (0.35, -0.20, 0.35), (-0.30, 0.10, 0.40)),
]
for f, pos, yaw, fl, sd, spn, fd, hl, hr in FALL:
    WO.pose(f, pos, yaw=yaw, flex=fl, side=sd, sp=spn, head=(-15, 0), hands={"L": ("r", hl), "R": ("r", hr)},
            feet={"L": ("r", fd, -20), "R": ("r", (fd[0], fd[1] - 0.08, fd[2] - 0.1), -10)}, curl={"L": 0.15, "R": 0.15})
# hands meet the clothes, she tucks her head and rolls over onto her back (head ends toward the flap, legs to the back wall)
LAND = Vector((0.08, 0.04, 0)); LY = 130.0
HD = -fwd(LY)            # on her back, her head points this way (front-left)
LG = fwd(LY)             # legs / facing when she sits up (back-right)
def back_lie(f, dz=0.0, sit=0.0, sp=(8, 0, 0), head=(10, 0), hands=None, knee=1.0, jaw=0.0, curl=0.3, yaw=LY, side=4):
    """on her back on the clothes, knees bent, feet flat on the clothes; sit=0..1 rolls the torso up to sitting"""
    flex = -90 + 80 * sit
    zp = PZ(LAND.x, LAND.y) + 0.12 + 0.02 * sit + dz
    feet = {}
    for s in "LR":
        sx = 1 if s == "L" else -1
        p = LAND + LG * (0.50 + 0.08 * (1 - knee)) + lat(yaw) * (0.11 * sx)
        kp = LAND + LG * 0.35 + lat(yaw) * (0.16 * sx) + Vector((0, 0, PZ(p.x, p.y) + 0.9))
        feet[s] = ("g", (p.x, p.y), yaw, 0.0, 0.0, tuple(kp))
    if hands is None:
        hands = {}
        for s in "LR":
            sx = 1 if s == "L" else -1
            hp = LAND + lat(yaw) * (0.30 * sx) + HD * (0.10 - 0.25 * sit)
            hands[s] = ("w", (hp.x, hp.y, PZ(hp.x, hp.y) + 0.035), tuple(LG * 0.3 + Vector((0, 0, 0)) + lat(yaw) * 0.2 * sx), tuple(PALM_DOWN))
    WO.pose(f, (LAND.x, LAND.y, zp), yaw=yaw, flex=flex, side=side * (1 - sit), sp=sp, head=head, hands=hands, feet=feet, jaw=jaw,
            curl={"L": curl, "R": curl})
WO.pose(252, (0.06, -0.06, 0.90), yaw=150, flex=205, side=8, sp=(30, 0, 0), head=(35, 0),
        hands={"L": ("r", (0.30, 0.05, 0.25)), "R": ("r", (-0.30, 0.05, 0.25))},
        feet={"L": ("r", (0, -0.25, 0.40), -10), "R": ("r", (0, -0.20, 0.32), -10)}, curl={"L": 0.2, "R": 0.2})
WO.pose(266, (0.07, 0.0, 0.62), yaw=138, flex=245, side=5, sp=(30, 0, 0), head=(30, 0),
        hands={"L": ("r", (0.30, 0.10, 0.15)), "R": ("r", (-0.30, 0.10, 0.15))},
        feet={"L": ("r", (0, -0.35, 0.45), -10), "R": ("r", (0, -0.30, 0.38), -10)}, curl={"L": 0.2, "R": 0.2})
back_lie(280, dz=0.06, knee=0.6, sp=(20, 0, 0), head=(25, 0))
back_lie(290, dz=-0.03, sp=(0, 0, 0), head=(5, 0))        # bounce on the clothes
back_lie(300, dz=0.01, sp=(6, 0, 0), head=(8, 0))
# --- 295-504: dazed, lifts her head, props up on her elbows, sits up facing the back wall, then looks round at the flap
back_lie(330, head=(15, 10), curl=0.35)
back_lie(360, head=(30, -15), jaw=5)
back_lie(390, sit=0.25, head=(25, 10), sp=(15, 0, 0))
back_lie(420, sit=0.55, head=(15, 0), sp=(20, 0, 0))
back_lie(445, sit=0.85, head=(10, -10), sp=(18, 0, 0))
def sit_back(f, look=(0, 0), lean=14, twist=0, jaw=0.0, hands=None, yaw=LY):
    back_lie(f, sit=1.0, head=look, sp=(lean, twist, 0), jaw=jaw, hands=hands, yaw=yaw)
sit_back(470, look=(-5, 20), lean=12)
sit_back(500, look=(-15, 40), lean=8, twist=15)           # turns her head and shoulders back toward the flap
sit_back(560, look=(-25, 45), lean=5, twist=25, jaw=6)
sit_back(600, look=(-20, 35), lean=10, twist=20)
# --- 600-720: rolls onto one hip, knees under her, stands up facing the flap
KN = Vector((0.04, -0.02, 0))
WO.pose(628, (KN.x, KN.y, PZ(KN.x, KN.y) + 0.32), yaw=40, flex=35, sp=(25, 0, 0), head=(-20, 0),
        hands={"L": ("w", (KN.x + 0.22, KN.y - 0.30, PZ(KN.x + 0.22, KN.y - 0.30) + 0.035), (0.2, -1, 0), tuple(PALM_DOWN)),
               "R": ("w", (KN.x - 0.12, KN.y - 0.36, PZ(KN.x - 0.12, KN.y - 0.36) + 0.035), (-0.1, -1, 0), tuple(PALM_DOWN))},
        feet={"L": ("g", (KN.x + 0.14, KN.y + 0.30), 40, 0.0, -60, (KN.x + 0.2, KN.y - 0.5, 0.35)),
              "R": ("g", (KN.x - 0.10, KN.y + 0.26), 40, 0.0, -60, (KN.x - 0.05, KN.y - 0.5, 0.35))}, curl={"L": 0.15, "R": 0.15})
WO.pose(650, (KN.x, KN.y - 0.04, PZ(KN.x, KN.y) + 0.48), yaw=15, flex=30, sp=(25, 0, 0), head=(-25, 0),
        hands={"L": ("r", (0.02, -0.25, 0.35)), "R": ("r", (-0.02, -0.25, 0.30))},
        feet={"L": ("g", (KN.x + 0.12, KN.y - 0.18), 15, 0.0, 0.0), "R": ("g", (KN.x - 0.12, KN.y + 0.22), 15, 0.0, -50, (KN.x - 0.1, KN.y - 0.6, 0.6))},
        curl={"L": 0.3, "R": 0.3})
STAND = Vector((0.02, -0.18, 0))
WO.pose(676, (STAND.x, STAND.y + 0.02, PZ(STAND.x, STAND.y) + RH - 0.10), yaw=5, flex=10, sp=(8, 0, 0), head=(-20, 0),
        hands={"L": ("r", (0.0, -0.12, 0.25)), "R": ("r", (0.0, -0.12, 0.25))}, feet=stand_feet(STAND.x, STAND.y + 0.08, 0), curl={"L": 0.3, "R": 0.3})
def at_flap(f, push, look=(-10, 0), wob=0.0, jaw=0.0):
    z = PZ(STAND.x, STAND.y)
    ph = 1.50 + 0.03 * wob
    WO.pose(f, (STAND.x, STAND.y - 0.05 * push, z + RH - 0.04), yaw=0, flex=3 + 5 * push, sp=(2 + 4 * push, 0, 0), head=look,
            hands={"L": ("w", (0.16, FY + 0.07 - 0.006 * push, ph), (0, 0, 1), (0, -1, 0)), "R": ("w", (-0.16, FY + 0.07 - 0.006 * push, ph + 0.04), (0, 0, 1), (0, -1, 0))},
            feet=stand_feet(STAND.x, STAND.y + 0.08, 0), jaw=jaw, curl={"L": 0.1, "R": 0.1})
at_flap(720, 0.0, look=(-15, 10)); at_flap(780, 0.2); at_flap(805, 1.0, jaw=8); at_flap(818, 0.3); at_flap(835, 1.0, jaw=10); at_flap(850, 0.2)
at_flap(880, 0.6, look=(-5, -15)); at_flap(930, 0.0, look=(0, 25))
# --- 961-1320: runs her hands over the left wall (smooth, nothing to hold), looks up, searches the flap edge, jumps at the back wall
LW = -0.735
def at_wall(f, a, b, look=(0, 0)):
    p = Vector((-0.20, 0.0, 0)); z = PZ(p.x, p.y)
    WO.pose(f, (p.x, p.y, z + RH - 0.04), yaw=-90, flex=4, sp=(2, 0, 0), head=look,
            hands={"L": ("w", (LW + 0.012, -0.20 + 0.08 * a, 1.55 + 0.10 * a), (0, 0.2, 1), (-1, 0, 0)), "R": ("w", (LW + 0.012, 0.18 - 0.08 * b, 1.45 + 0.10 * b), (0, -0.2, 1), (-1, 0, 0))},
            feet=stand_feet(p.x + 0.05, p.y, -90), curl={"L": 0.08, "R": 0.08})
for i, f in enumerate(range(975, 1090, 14)):
    at_wall(f, (i % 2) * 1.0, ((i + 1) % 2) * 1.0, look=(-25 + 6 * (i % 3), 12 * math.sin(i)))
def search(f, x, look):
    z = PZ(0.0, -0.02)
    WO.pose(f, (0.0, -0.06, z + RH - 0.04), yaw=0, flex=4, sp=(2, 0, 0), head=look,
            hands={"L": ("w", (x + 0.12, FY + 0.07, 1.55), (0, 0, 1), (0, -1, 0)), "R": ("w", (x - 0.12, FY + 0.07, 1.62), (0, 0, 1), (0, -1, 0))},
            feet=stand_feet(0.0, 0.03, 0), curl={"L": 0.1, "R": 0.1})
search(1110, -0.15, (-15, -20)); search(1135, 0.18, (-15, 20)); search(1160, 0.0, (-25, 0))
JW = Vector((0.0, 0.18, 0)); jz = PZ(JW.x, JW.y)
def jump(f, dz, flex, hz, hands_on=True, crouch=0.0, airborne=False, look=(-30, 0)):
    hy = 0.570
    hands = {"L": ("w", (-0.16, hy - 0.01, hz), (0, 0, 1), (0, 1, 0)), "R": ("w", (0.16, hy - 0.01, hz + 0.03), (0, 0, 1), (0, 1, 0))} if hands_on else \
            {"L": ("r", (0.05, -0.1, 0.1)), "R": ("r", (-0.05, -0.1, 0.1))}
    feet = {"L": ("r", (0, 0.05, 0.12), 30), "R": ("r", (0, -0.05, 0.18), 20)} if airborne else stand_feet(JW.x, JW.y - 0.05, 180)
    WO.pose(f, (JW.x, JW.y, jz + RH - crouch + dz), yaw=180, flex=flex, sp=(flex * 0.5, 0, 0), head=look, hands=hands, feet=feet, curl={"L": 0.3, "R": 0.3})
jump(1178, 0, 3, 1.45, hands_on=False, look=(-35, 0)); jump(1192, 0, 18, 1.2, hands_on=False, crouch=0.20)
jump(1206, 0.20, -3, 2.0, airborne=True, look=(-40, 0)); jump(1216, 0.22, -3, 2.05, airborne=True, look=(-40, 0))
jump(1232, 0.12, 0, 1.86, airborne=True, look=(-30, 0)); jump(1244, 0.03, 4, 1.66, airborne=True)
jump(1252, 0, 10, 1.56, crouch=0.12); jump(1268, 0, 14, 1.58, hands_on=True, crouch=0.10, look=(-10, 0)); jump(1300, 0, 8, 1.3, hands_on=False, crouch=0.04, look=(10, 15))
# --- 1321-1500: screams for help up at the flap, hands cupped, pounds on the flap
def scream(f, jaw, bob=0.0, look=(-28, 0)):
    p = Vector((0.0, 0.05, 0)); z = PZ(p.x, p.y)
    M = WO.Mb(Vector((p.x, p.y, z + RH - 0.04 + 0.02 * bob)), 0, -4, 0)
    WO.pose(f, (p.x, p.y, z + RH - 0.04 + 0.02 * bob), yaw=0, flex=-4, sp=(-8 - 4 * bob, 0, 0), head=look,
            hands={"L": ("w", M @ Vector((0.11, -0.22, 1.30)), (-0.2, -0.5, 0.8), (-1, 0.2, 0)), "R": ("w", M @ Vector((-0.11, -0.22, 1.30)), (0.2, -0.5, 0.8), (1, 0.2, 0))},
            feet=stand_feet(p.x, p.y, 0), jaw=jaw, curl={"L": 0.35, "R": 0.35})
def pound(f, hit):
    p = Vector((0.0, -0.08, 0))
    fx_ = [WO.foot_xy(s_, Vector((p.x, p.y + 0.05, 0)), 0) for s_ in "LR"]
    z = min(PZ(v.x, v.y) for v in fx_) + 0.04
    WO.pose(f, (p.x, p.y - 0.05 * hit, z + RH - 0.05), yaw=0, flex=4 + 6 * hit, sp=(4 + 6 * hit, 0, 0), head=(-15, 0),
            hands={"L": ("w", (0.14, FY + 0.05 + 0.18 * (1 - hit), 1.42 + 0.12 * (1 - hit)), (0, -1, 0.4), (0, 0, 1)),
                   "R": ("w", (-0.14, FY + 0.05 + 0.18 * (1 - hit), 1.46 + 0.12 * (1 - hit)), (0, -1, 0.4), (0, 0, 1))},
            feet=stand_feet(p.x, p.y + 0.05, 0), jaw=18 * hit, curl={"L": 1.0, "R": 1.0})
scream(1322, 2); scream(1336, 22, 1.0); pound(1348, 0); pound(1356, 1); pound(1364, 0.2); pound(1372, 1); pound(1380, 0.1)
scream(1394, 24, 1.0, (-26, -6)); scream(1420, 8, 0.2); scream(1446, 22, 1.0, (-30, 0)); scream(1478, 4, 0.0, (-10, 0))
# --- 1500-1842: three days. She sinks down and lies curled on her side in the middle of the clothes, head on her arm, face to the flap
CUR = Vector((-0.12, -0.02, 0)); CY = 52.0          # side-lying: head toward the back-right corner, front of her body faces the front wall
def curled(f, k, weak, head=(20, 0), breathe=0.0, jaw=0.0):
    z = PZ(CUR.x, CUR.y) + 0.17 - 0.02 * weak + 0.006 * breathe
    M = WO.Mb(Vector((CUR.x, CUR.y, z)), CY, 0, 88)
    hp = M @ (WO.root_head + Vector((0.0, -0.10, 0.62)))        # under her head (pillow arm)
    WO.pose(f, (CUR.x, CUR.y, z), yaw=CY, flex=0, side=88, sp=(28 + 8 * k + 2 * breathe, 0, 0), head=head,
            hands={"L": ("r", (-0.05, -0.26, 0.42), (0, 0, 20)), "R": ("r", (0.10, -0.30, 0.20), (0, 0, -20))},
            feet={"L": ("r", (-0.02, -0.30 * k, 0.40 * k), 15), "R": ("r", (0.04, -0.24 * k, 0.34 * k), 15)},
            jaw=jaw, curl={"L": 0.45, "R": 0.5})
WO.pose(1500, (0.0, 0.02, PZ(0.0, 0.02) + 0.55), yaw=20, flex=25, sp=(30, 0, 0), head=(20, 0),
        hands={"L": ("r", (0, -0.2, 0.2)), "R": ("r", (0, -0.2, 0.2))}, feet=stand_feet(0.0, -0.02, 20))
WO.pose(1515, (-0.05, 0.0, PZ(-0.05, 0.0) + 0.30), yaw=40, flex=30, side=40, sp=(30, 0, 0), head=(20, 0),
        hands={"L": ("w", (-0.30, 0.02, PZ(-0.30, 0.02) + 0.035), (0.3, -0.6, 0), tuple(PALM_DOWN)), "R": ("r", (0.05, -0.25, 0.15))},
        feet={"L": ("g", (0.18, -0.30), 40, 0.0, -40), "R": ("g", (0.02, -0.36), 40, 0.0, -40)})
for f, k, weak, hd, br in ((1532, 0.85, 0.0, (15, 10), 0), (1580, 0.9, 0.1, (18, 0), 1), (1630, 1.0, 0.3, (22, -5), 0), (1690, 0.95, 0.5, (20, 5), 1),
                            (1750, 1.0, 0.7, (24, 0), 0), (1800, 1.0, 0.85, (22, -5), 1), (1840, 1.0, 1.0, (25, 0), 0)):
    curled(f, k, weak, hd, br)
# --- 1843-2094: hears the knock, lifts her head, props up on her arm and sits up toward the light
curled(1910, 1.0, 1.0, (25, 0)); curled(1935, 0.95, 0.9, (0, -20), jaw=8)
WO.pose(1990, (CUR.x + 0.02, CUR.y, PZ(CUR.x, CUR.y) + 0.24), yaw=CY - 20, flex=20, side=55, sp=(20, 0, 0), head=(-5, -20),
        hands={"L": ("w", (CUR.x - 0.10, CUR.y + 0.20, PZ(CUR.x - 0.10, CUR.y + 0.20) + 0.035), (0.6, 0.3, 0), tuple(PALM_DOWN)), "R": ("r", (0.05, -0.25, 0.20))},
        feet={"L": ("r", (-0.02, -0.30, 0.40), 15), "R": ("r", (0.04, -0.24, 0.34), 15)}, jaw=4)
SEAT = Vector((0.05, 0.12, 0))
def seated(f, look=(0, 0), lean=15, jaw=0.0, dy=0.0):
    p = Vector((SEAT.x, SEAT.y + dy, PZ(SEAT.x, SEAT.y + dy) + 0.13))
    fx = {s: Vector((SEAT.x + (0.12 if s == "L" else -0.12), SEAT.y + dy - 0.45)) for s in "LR"}
    hands = {}
    for s in "LR":
        sx = 1 if s == "L" else -1
        hp = Vector((SEAT.x + 0.26 * sx, SEAT.y + dy + 0.10))
        hands[s] = ("w", (hp.x, hp.y, PZ(hp.x, hp.y) + 0.035), (0.3 * sx, -1, 0), tuple(PALM_DOWN))
    WO.pose(f, p, yaw=0, flex=-10, sp=(lean, 0, 0), head=look, hands=hands,
            feet={s: ("g", (fx[s].x, fx[s].y), 0, 0.0, 15) for s in "LR"}, jaw=jaw)
seated(2045, look=(-10, 25), lean=25, dy=0.05); seated(2070, look=(-5, 20), lean=25, dy=0.05); seated(2088, look=(-5, 10), lean=20, dy=0.0)

# ---------------------------------------------------------------- shover: hands on her upper back (not her hips)
clear_keys(SHo, 150, 231)
def back_point(f):
    sc.frame_set(f)
    pb = WOo.pose.bones["spine04"]; c = WOo.matrix_world @ pb.head
    dg = bpy.context.evaluated_depsgraph_get()
    body = next(o for o in WOo.children if o.name.endswith(".body"))
    ev = body.evaluated_get(dg)
    src = c + Vector((0, -0.7, 0.35)); d = (c - src).normalized()
    inv = body.matrix_world.inverted()
    hit, loc, nrm, _ = ev.ray_cast(inv @ src, inv.to_3x3() @ d)
    p = body.matrix_world @ loc if hit else c + Vector((0, -0.13, 0.08))
    return p, d
for f, dz, fl, ext in ((154, 0.0, 8, 0.0), (163, -0.03, 22, 0.6), (172, -0.04, 30, 1.0), (196, -0.02, 18, 0.8), (226, 0.0, 5, 0.0)):
    p = Vector((-0.02, -1.75 + 0.12 * ext, RH + dz))
    if 160 <= f <= 200:
        bp, d = back_point(f)
        hands = {s: ("w", tuple(bp + Vector((0.11 * (1 if s == "L" else -1) * -1, 0, 0)) - d * 0.03), (0, 0.45, 1), tuple(d)) for s in "LR"}
    else:
        hands = {"L": ("r", (0.05, -0.15, 0.25)), "R": ("r", (-0.05, -0.15, 0.25))}
    SH.pose(f, p, yaw=180, flex=fl, sp=(fl * 0.6, 0, 0), head=(5, 0), hands=hands,
            feet={"L": ("g", (-0.14, -1.55 + 0.06 * ext), 180), "R": ("g", (0.12, -1.93 + 0.1 * ext), 175)}, curl={"L": 0.15, "R": 0.15})

# ---------------------------------------------------------------- camera inside the bin: high corners, her face in frame, no wall/hair fills
CAMK = json.loads(sc["cam_keys"])
WR_ = WOo; HB = WR_.pose.bones["head"]
def face(fk):
    sc.frame_set(fk); M = WR_.matrix_world
    return M @ (HB.head + (HB.tail - HB.head) * 0.45)
def chest(fk):
    sc.frame_set(fk); return WR_.matrix_world @ WR_.pose.bones["spine03"].head
def mix(a, b, t): return a.lerp(b, t)
KEEP = lambda f: not (236 <= f <= 500 or 860 <= f <= 1420 or 1600 <= f <= 1870)
CAMK = [k for k in CAMK if KEEP(k[0])]
NEW = []
def K(f, pos, tgt, lens): NEW.append([f, list(pos), list(tgt), lens])
K(240, (0.05, -1.30, 1.78), (0.0, -0.45, 1.20), 20)                      # legs disappear through the chute, no sole in the lens
K(268, (0.0, -0.80, 1.55), (0.05, 0.0, 0.55), 18)
K(288, (0.02, -0.45, 1.55), (0.08, 0.05, 0.45), 17)                      # through the chute, looking down at her landing
for f, cp, ln in ((310, (-0.45, -0.42, 1.75), 18), (360, (-0.52, -0.40, 1.55), 20), (420, (-0.40, -0.45, 1.35), 22), (470, (-0.30, -0.45, 1.25), 24)):
    K(f, cp, mix(face(f), chest(f), 0.35), ln)
K(500, (0.62, -0.15, 1.10), mix(face(500), chest(500), 0.3), 22)
# x-ray section stays outside until 860; comes back in while the walls are still see-through
K(880, (0.62, -0.50, 1.85), mix(face(880), chest(880), 0.3), 20)
for f, cp, ln in ((905, (0.58, -0.46, 1.85), 20), (950, (0.50, -0.46, 1.70), 20), (990, (-0.20, -0.48, 1.70), 20), (1040, (0.10, -0.48, 1.75), 20),
                  (1085, (0.30, -0.46, 1.80), 20), (1125, (0.50, -0.30, 1.60), 20), (1165, (0.55, -0.20, 1.55), 20),
                  (1200, (0.55, -0.40, 1.55), 18), (1245, (0.50, -0.45, 1.65), 18), (1300, (0.45, -0.45, 1.90), 18),
                  (1340, (0.50, -0.40, 2.05), 20), (1384, (0.40, -0.45, 2.10), 20), (1404, (0.10, -0.50, 1.95), 20)):
    tg = mix(face(f), chest(f), 0.25)
    K(f, cp, tg, ln)
K(1620, (0.30, -0.46, 1.65), mix(face(1620), chest(1620), 0.4), 20)
K(1700, (0.45, -0.45, 1.35), mix(face(1700), chest(1700), 0.3), 22)
K(1780, (0.50, -0.40, 1.20), mix(face(1780), chest(1780), 0.2), 24)
K(1840, (0.40, -0.45, 1.30), mix(face(1840), chest(1840), 0.2), 22)
K(1862, (0.10, -0.40, 1.45), mix(face(1862), chest(1862), 0.3), 20)
CAMK = sorted(CAMK + NEW, key=lambda k: k[0])
sc["cam_keys"] = json.dumps(CAMK)
cam = sc.camera; cam_d = cam.data
cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves.clear()
if cam_d.animation_data and cam_d.animation_data.action:
    for l in cam_d.animation_data.action.layers:
        for st in l.strips:
            for cb in st.channelbags: cb.fcurves.clear()
cl = catmull([(k[0], Vector(k[1])) for k in CAMK]); ct = catmull([(k[0], Vector(k[2])) for k in CAMK]); cln = pchip([(k[0], float(k[3])) for k in CAMK])
qprev = None
for f in range(1, sc.frame_end + 1):
    p, t = cl(f), ct(f)
    cam.location = p; cam.keyframe_insert("location", frame=f)
    q = (t - p).to_track_quat('-Z', 'Y'); cam.rotation_mode = 'QUATERNION'
    if qprev is not None and q.dot(qprev) < 0: q = -q
    qprev = q.copy(); cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cam_d.lens = cln(f); cam_d.keyframe_insert("lens", frame=f)
    cam_d.dof.focus_distance = (t - p).length; cam_d.dof.keyframe_insert("focus_distance", frame=f)
sc["director_fix"] = "v006 re-stage: shove on upper back, roll onto back with feet down, sit up, upright at walls, curled on side mid-pile, corner camera"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FIX09_DONE", len(CAMK))
