"""DonationBin blocking/polish animation: woman, shover, passer-by, firefighters, flap mechanism, camera.
blender -b scene.blend --python 03_animate.py -- <out.blend>
Runs 03b_fx_camera.py at the end (lights, x-ray, sparks, camera spline)."""
import sys, os, math, json
import bpy
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
FY = sc["bin_front_y"]
PILE = bpy.data.objects["Pile"]

def ground_z(x, y):            # override: asphalt at 0, inside the bin the clothes pile surface
    if -0.73 < x < 0.73 and -0.58 < y < 0.58:
        hit, loc, nrm, idx = PILE.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
        if hit: return loc.z
    return 0.0
PZ = lambda x, y: ground_z(x, y)

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
        M = self.Mb(pos, yaw, flex, side); R3 = M.to_3x3()
        for s in "LR":
            sx = 1 if s == "L" else -1
            spec = (feet or {}).get(s, ("r", (0, 0, 0)))
            if spec[0] == "g":                          # planted on the ground / pile: ("g", (x, y), yaw, lift, pitch)
                self.key_foot(s, f, Vector(spec[1]), spec[2], spec[3] if len(spec) > 3 else 0.0, spec[4] if len(spec) > 4 else 0.0)
            else:                                       # body-relative: ("r", delta_local, pitch)
                d = Vector(spec[1]); a = self.ankle[s]; pt = spec[2] if len(spec) > 2 else 0.0
                T = M @ Matrix.Translation(a + d) @ Matrix.Rotation(R_(pt), 4, 'X') @ Matrix.Translation(-a) @ self.r.rest("IK_foot." + s)
                self.r.key_world("IK_foot." + s, f, T)
                self.key_pole("Pole_knee." + s, f, M @ (self.knee[s] + Vector((0, -0.6, 0)) + d * 0.5))
            hs = (hands or {}).get(s, ("r", (0, 0, 0)))
            pole = M @ (self.elbow[s] + Vector((0.25 * sx, 0.55, -0.1)))
            if hs[0] == "w":                            # world: ("w", W, dir, normal[, pole_world])
                W, d_, n_ = Vector(hs[1]), Vector(hs[2]), Vector(hs[3])
                if len(hs) > 4: pole = Vector(hs[4])
                self.key_hand(s, f, W, d_, n_, pole=pole)
            else:                                       # body-relative: ("r", delta, (rx, ry, rz) deg)
                d = Vector(hs[1]); rot = hs[2] if len(hs) > 2 else (0, 0, 0); w = self.wrist[s]
                Rl = (Matrix.Rotation(R_(rot[2]), 4, 'Z') @ Matrix.Rotation(R_(rot[1]), 4, 'Y') @ Matrix.Rotation(R_(rot[0]), 4, 'X'))
                T = M @ Matrix.Translation(w + d) @ Rl @ Matrix.Translation(-w) @ self.r.rest("IK_hand." + s)
                self.r.key_world("IK_hand." + s, f, T)
                pb = self.r.PB["Pole_elbow." + s]
                self.key_pole("Pole_elbow." + s, f, M @ (self.elbow[s] + Vector((0.25 * sx, 0.55, -0.1)) + d * 0.5))
        if "jaw" in self.r.PB:
            self.r.key_rot("jaw", f, [("X", jaw)])
        c = curl if curl is not None else {"L": 0.25, "R": 0.25}
        for s in "LR":
            for i in range(1, 6):
                for j in (1, 2, 3):
                    n = "finger%d-%d.%s" % (i, j, s)
                    if n in self.r.PB:
                        self.r.key_rot(n, f, [("X", 0)]) if False else self.curl_bone(n, f, c[s] * (55 if i > 1 else 25))
    def curl_bone(self, n, f, deg):
        pb = self.r.PB[n]; pb.rotation_quaternion = Quaternion((1, 0, 0), R_(deg)); pb.keyframe_insert("rotation_quaternion", frame=f, group=n)

def hide_keys(rig_name, ranges):
    """ranges: list of (frame, hidden)"""
    o = bpy.data.objects[rig_name]
    for ob in [o] + list(o.children):
        for f_, h_ in ranges:
            ob.hide_render = h_; ob.keyframe_insert("hide_render", frame=f_)
            ob.hide_viewport = h_; ob.keyframe_insert("hide_viewport", frame=f_)

def walk_arms(B, path, yaw_fn, f0, f1, stride=0.75, sides="LR", swing=0.14, step=4):
    d = 0.0; prev = path(f0)
    for f in list(range(f0, f1 + 1, step)) + [f1]:
        p = path(f); d += (p - prev).to_2d().length; prev = p
        ph = math.sin(2 * math.pi * d / stride)
        M = B.Mb(Vector((p.x, p.y, ground_z(p.x, p.y) + B.root_head.z - 0.04)), yaw_fn(f), 3, 0)
        for s in sides:
            sx = 1 if s == "L" else -1
            dl = Vector((-0.24 * sx, 0.10 + swing * ph * sx, -0.20))
            T = M @ Matrix.Translation(dl) @ B.r.rest("IK_hand." + s)
            B.r.key_world("IK_hand." + s, f, T)
            B.key_pole("Pole_elbow." + s, f, M @ (B.elbow[s] + Vector((0.25 * sx, 0.55, -0.1))))
WO = Body(make_human_ctrl(bpy.data.objects["Woman"]), bpy.data.objects["Woman"])
SH = Body(make_human_ctrl(bpy.data.objects["Shover"]), bpy.data.objects["Shover"])
PB_ = Body(make_human_ctrl(bpy.data.objects["Passerby"]), bpy.data.objects["Passerby"])
FA = Body(make_human_ctrl(bpy.data.objects["FireA"]), bpy.data.objects["FireA"])
FB = Body(make_human_ctrl(bpy.data.objects["FireB"]), bpy.data.objects["FireB"])
RH = WO.root_head.z   # 0.82 standing root height
print("ROOT_HEIGHT", RH)

# ============================================================== WOMAN
up = Vector((0, 0, 1))
def stand_feet(x, y, yaw, lift=0.0, pitch=0.0, spread=1.0):
    fx = {s: WO.foot_xy(s, Vector((x, y, 0)), yaw) for s in "LR"}
    return {s: ("g", (fx[s].x, fx[s].y), yaw, lift, pitch) for s in "LR"}
# --- beat 1 (1-150): on tiptoe reaching into the chute, the other hand on the sill
TIP_PITCH = float(os.environ.get("TIP_PITCH", "40"))
SILL = Vector((-0.27, FY - 0.03, sc["chute_z"][0] + 0.02))
def reach(f, depth, tip, wob=0.0):
    y = -1.02 + 0.06 * depth
    WO.pose(f, (0.0, y, RH - 0.02 + 0.07 * tip), yaw=180, flex=18 + 14 * depth, sp=(10 + 10 * depth, 6 * wob, 0), head=(-8, 10 * wob),
            hands={"L": ("w", SILL + Vector((0, 0, 0.0)), (0, 1, -0.2), (0, 0, 1)),
                   "R": ("w", Vector((0.12 + 0.06 * wob, FY + 0.15 + 0.2 * depth, 1.24 + 0.05 * wob)), (0, 1, -0.5), (0, 0, 1))},
            feet=stand_feet(0.0, -1.05, 180, lift=0.075 * tip, pitch=TIP_PITCH * tip), curl={"L": 0.7, "R": 0.3 + 0.4 * depth})
reach(1, 0.0, 0.3, 0.0); reach(35, 0.4, 0.8, 0.5); reach(70, 0.8, 1.0, -0.6); reach(105, 1.0, 1.0, 0.8); reach(135, 0.9, 1.0, -0.4); reach(155, 1.0, 1.0, 0.0)
# --- beat 2 (151-294): shoved, pitches forward head-first through the chute, somersault inside
FALL = [  # f, pos, yaw, flex, side, spine, feet-delta, hand-delta L, R
    (166, (0.0, -0.98, RH + 0.10), 180, 40, 0, (25, 0, 0), (0, 0.05, 0.10), (-0.05, -0.25, 0.45), (0.05, -0.25, 0.45)),
    (182, (0.0, -0.86, RH + 0.42), 180, 72, 5, (20, 0, 0), (0, 0.10, 0.25), (0.05, -0.35, 0.65), (-0.05, -0.35, 0.65)),
    (200, (0.0, -0.66, 1.30), 180, 100, 8, (10, 8, 0), (0, 0.05, 0.35), (0.10, -0.30, 0.70), (-0.10, -0.30, 0.70)),
    (218, (0.02, -0.42, 1.36), 175, 135, 10, (-10, 10, 0), (0, 0.15, 0.30), (0.25, -0.20, 0.55), (-0.25, -0.10, 0.60)),
    (238, (0.04, -0.20, 1.18), 165, 175, 12, (-15, 0, 0), (0, -0.20, 0.30), (0.35, -0.20, 0.35), (-0.30, 0.10, 0.40)),
    (258, (0.06, -0.02, 0.92), 150, 215, 8, (20, -10, 0), (0, -0.30, 0.35), (0.35, 0.10, 0.20), (-0.35, 0.05, 0.25)),
    (276, (0.08, 0.06, 0.62), 138, 248, 4, (25, -10, 0), (0, -0.30, 0.40), (0.30, 0.20, 0.10), (-0.40, 0.10, 0.15)),
]
for f, pos, yaw, fl, sd, spn, fd, hl, hr in FALL:
    WO.pose(f, pos, yaw=yaw, flex=fl, side=sd, sp=spn, head=(-15, 0), hands={"L": ("r", hl), "R": ("r", hr)},
            feet={"L": ("r", fd, -20), "R": ("r", (fd[0], fd[1] - 0.08, fd[2] - 0.1), -10)}, curl={"L": 0.1, "R": 0.1})
# --- beat 3 (295-504): lands on her back on the clothes (diagonal), bounce, settle, dazed, sits up
LZ = lambda x, y: PZ(x, y)
LAND = Vector((0.08, 0.06, 0))
def lying(f, dz, flex=270, yaw=130, sp=(10, 0, 0), head=(10, 0), hl=(0.15, 0.1, 0.1), hr=(-0.2, 0.05, 0.05), knees=0.25, side=4, jaw=0.0):
    z = LZ(LAND.x, LAND.y) + 0.13 + dz
    WO.pose(f, (LAND.x, LAND.y, z), yaw=yaw, flex=flex, side=side, sp=sp, head=head,
            hands={"L": ("r", hl), "R": ("r", hr)}, feet={"L": ("r", (0, -knees, knees * 1.1), -10), "R": ("r", (0, -knees * 0.6, knees * 0.7), -5)}, jaw=jaw)
lying(294, 0.05, flex=262); lying(300, -0.05, sp=(-5, 0, 0)); lying(312, 0.03, sp=(15, 0, 0), knees=0.3); lying(326, -0.01); lying(345, 0.0, knees=0.35, head=(25, 15))
lying(380, 0.0, knees=0.4, head=(30, -20), hl=(0.1, -0.2, 0.3), jaw=6); lying(420, 0.02, flex=285, knees=0.45, head=(35, 10), hl=(0.05, -0.35, 0.5))
# sit up (440-505): seated facing the flap (yaw 0 faces -y)
SEAT = Vector((0.05, 0.12, 0))
def seated(f, look=(0, 0), lean=15, hands=None, jaw=0.0, dy=0.0):
    p = Vector((SEAT.x, SEAT.y + dy, PZ(SEAT.x, SEAT.y + dy) + 0.13))
    fx = {s: Vector((SEAT.x + (0.12 if s == "L" else -0.12), SEAT.y + dy - 0.45)) for s in "LR"}
    WO.pose(f, p, yaw=0, flex=-10, sp=(lean, 0, 0), head=look,
            hands=hands or {"L": ("w", (SEAT.x + 0.3, SEAT.y + dy + 0.05, PZ(SEAT.x + 0.3, SEAT.y + 0.05) + 0.01), (0.3, 0.2, -1), (1, 0, 0)),
                            "R": ("w", (SEAT.x - 0.3, SEAT.y + dy + 0.05, PZ(SEAT.x - 0.3, SEAT.y + 0.05) + 0.01), (-0.3, 0.2, -1), (-1, 0, 0))},
            feet={s: ("g", (fx[s].x, fx[s].y), 0, 0.0, 15) for s in "LR"}, jaw=jaw)
seated(462, look=(20, 15), lean=30); seated(485, look=(-15, -10), lean=10); seated(505, look=(-25, 0), lean=5)
# --- beats 4-5 (505-960): looks up at the flap, rises, pushes it outward: it clacks against the stop bar
seated(560, look=(-30, 20), lean=0); seated(610, look=(-20, -15), lean=10)
STAND = Vector((0.02, -0.18, 0))
def at_flap(f, push, look=(-10, 0), wob=0.0, jaw=0.0):
    z = PZ(STAND.x, STAND.y)
    ph = 1.30 + 0.03 * wob
    WO.pose(f, (STAND.x, STAND.y - 0.05 * push, z + RH - 0.04), yaw=0, flex=5 + 5 * push, sp=(3 + 4 * push, 0, 0), head=look,
            hands={"L": ("w", (0.16, FY + 0.048 - 0.006 * push, ph), (0, 0, 1), (0, 1, 0)), "R": ("w", (-0.16, FY + 0.048 - 0.006 * push, ph + 0.04), (0, 0, 1), (0, 1, 0))},
            feet=stand_feet(STAND.x, STAND.y + 0.08, 0, 0, 0), jaw=jaw, curl={"L": 0.1, "R": 0.1})
WO.pose(660, (0.04, 0.02, PZ(0.04, 0.02) + 0.45), yaw=0, flex=20, sp=(35, 0, 0), head=(-20, 0),
        hands={"L": ("r", (0.0, -0.2, 0.1)), "R": ("r", (0.0, -0.2, 0.1))}, feet=stand_feet(0.04, -0.02, 0))
at_flap(720, 0.0, look=(-20, 10)); at_flap(780, 0.2); at_flap(805, 1.0, jaw=8); at_flap(818, 0.3); at_flap(835, 1.0, jaw=10); at_flap(850, 0.2)
at_flap(880, 0.6, look=(-5, -15)); at_flap(930, 0.0, look=(10, 25))
# --- beat 6 (961-1320): pats the left wall, searches the flap for a handle, jumps, slips down
LW = -0.735
def at_wall(f, a, b, look=(0, 0)):
    p = Vector((-0.30, 0.0, 0)); z = PZ(p.x, p.y)
    WO.pose(f, (p.x, p.y, z + RH - 0.05), yaw=-90, flex=8, sp=(6, 0, 0), head=look,
            hands={"L": ("w", (LW + 0.004 + 0.06 * a, -0.18, 1.45), (0, 0, 1), (1, 0, 0)), "R": ("w", (LW + 0.004 + 0.06 * b, 0.17, 1.30), (0, 0, 1), (1, 0, 0))},
            feet=stand_feet(p.x + 0.05, p.y, -90), curl={"L": 0.05, "R": 0.05})
for i, f in enumerate(range(975, 1090, 12)):
    at_wall(f, (i % 2) * 1.0, ((i + 1) % 2) * 1.0, look=(-10 + 4 * (i % 3), 15 * math.sin(i)))
def search(f, x, look):
    z = PZ(0.0, -0.15)
    WO.pose(f, (0.0, -0.17, z + RH - 0.06), yaw=0, flex=12, sp=(10, 0, 0), head=look,
            hands={"L": ("w", (x + 0.12, FY + 0.048, 1.22), (0, 0, 1), (0, 1, 0)), "R": ("w", (x - 0.12, FY + 0.048, 1.38), (0, 0, 1), (0, 1, 0))},
            feet=stand_feet(0.0, -0.08, 0), curl={"L": 0.1, "R": 0.1})
search(1110, -0.15, (10, -20)); search(1135, 0.18, (15, 20)); search(1160, 0.0, (-10, 0))
# jump at the back wall (facing +y = yaw 180)
JW = Vector((0.0, 0.18, 0)); jz = PZ(JW.x, JW.y)
def jump(f, dz, flex, hz, hands_on=True, crouch=0.0, airborne=False, look=(-30, 0)):
    hy = 0.570
    hands = {"L": ("w", (-0.16, hy, hz), (0, 0, 1), (0, -1, 0)), "R": ("w", (0.16, hy, hz + 0.03), (0, 0, 1), (0, -1, 0))} if hands_on else \
            {"L": ("r", (0.05, -0.1, 0.1)), "R": ("r", (-0.05, -0.1, 0.1))}
    feet = {"L": ("r", (0, 0.05, 0.15), 30), "R": ("r", (0, -0.05, 0.25), 20)} if airborne else stand_feet(JW.x, JW.y - 0.05, 180)
    WO.pose(f, (JW.x, JW.y, jz + RH - crouch + dz), yaw=180, flex=flex, sp=(flex * 0.5, 0, 0), head=look, hands=hands, feet=feet, curl={"L": 0.3, "R": 0.3})
jump(1178, 0, 5, 1.45, hands_on=False, look=(-35, 0)); jump(1192, 0, 20, 1.2, hands_on=False, crouch=0.22)
jump(1206, 0.32, -5, 2.0, airborne=True, look=(-40, 0)); jump(1216, 0.36, -5, 2.02, airborne=True, look=(-40, 0))
jump(1232, 0.20, 0, 1.86, airborne=True, look=(-30, 0)); jump(1244, 0.04, 4, 1.66, airborne=True)
jump(1252, 0, 10, 1.56, crouch=0.15); jump(1268, 0, 30, 1.40, hands_on=True, crouch=0.30, look=(10, 0)); jump(1300, 0, 20, 1.3, hands_on=False, crouch=0.12, look=(20, 15))
# --- beat 7 (1321-1500): screams for help, hands cupped at her mouth, face up to the chute
def scream(f, jaw, bob=0.0, look=(-28, 0)):
    p = Vector((0.0, 0.05, 0)); z = PZ(p.x, p.y)
    M = WO.Mb(Vector((p.x, p.y, z + RH - 0.04 + 0.02 * bob)), 0, -4, 0)
    WO.pose(f, (p.x, p.y, z + RH - 0.04 + 0.02 * bob), yaw=0, flex=-4, sp=(-8 - 4 * bob, 0, 0), head=look,
            hands={"L": ("w", M @ Vector((0.075, -0.22, 1.30)), (-0.5, -0.5, 0.5), (-1, 0.2, 0)), "R": ("w", M @ Vector((-0.075, -0.22, 1.30)), (0.5, -0.5, 0.5), (1, 0.2, 0))},
            feet=stand_feet(p.x, p.y, 0), jaw=jaw, curl={"L": 0.35, "R": 0.35})
scream(1322, 2); scream(1340, 22, 1.0); scream(1368, 10, 0.0, (-32, 8)); scream(1392, 24, 1.0, (-26, -6)); scream(1420, 8, 0.2); scream(1446, 22, 1.0, (-30, 0)); scream(1478, 4, 0.0, (-10, 0))
# --- beat 8 (1501-1842): three days curled on the clothes, shifting, weaker
CUR = Vector((0.05, 0.05, 0))
def curled(f, yaw, side, k, weak, head=(25, 0)):
    z = PZ(CUR.x, CUR.y) + 0.16 - 0.03 * weak
    WO.pose(f, (CUR.x, CUR.y, z), yaw=yaw, flex=5, side=side, sp=(35 + 10 * k, 0, 0), head=head,
            hands={"L": ("r", (-0.30, -0.12, 0.22)), "R": ("r", (0.30, -0.14, 0.20))},
            feet={"L": ("r", (-0.05, -0.18 * k, 0.42 * k), 10), "R": ("r", (0.05, -0.12 * k, 0.36 * k), 10)}, curl={"L": 0.6, "R": 0.6})
WO.pose(1500, (0.05, 0.05, PZ(0.05, 0.05) + 0.4), yaw=-30, flex=30, sp=(40, 0, 0), head=(20, 0), hands={"L": ("r", (0, -0.2, 0.2)), "R": ("r", (0, -0.2, 0.2))},
        feet=stand_feet(0.05, 0.0, -30))
for f, yaw, side, k, weak, hd in ((1530, 60, 88, 0.9, 0.0, (25, 10)), (1600, 75, 86, 1.0, 0.2, (30, -5)), (1650, 60, 92, 0.8, 0.4, (20, 0)),
                                   (1720, 50, 90, 1.0, 0.6, (35, 5)), (1790, 65, 88, 0.95, 0.8, (25, -10)), (1840, 62, 90, 1.0, 1.0, (30, 0))):
    curled(f, yaw, side, k, weak, hd)
# --- beats 9-10 (1843-2094): lifts her head at the knock, pushes up on an elbow, then sits toward the light
curled(1920, 62, 90, 1.0, 1.0, (30, 0)); curled(1945, 62, 84, 0.9, 0.9, (-5, -25))
curled(2010, 62, 70, 0.7, 0.7, (-10, -30))
seated(2070, look=(-5, 20), lean=25, dy=0.05); seated(2088, look=(-5, 10), lean=20, dy=0.0)
# --- beat 11 (2095-2490): crouches out through the cut opening, steps down, walks off wrapped in a blanket
WO.pose(2110, (0.0, -0.42, PZ(0.0, -0.42) + 0.50), yaw=0, flex=35, sp=(30, 0, 0), head=(-15, 0),
        hands={"L": ("w", (0.55, FY - 0.005, 0.75), (0, 0, 1), (0, 1, 0)), "R": ("r", (0, -0.25, 0.1))}, feet=stand_feet(0.0, -0.30, 0))
WO.pose(2140, (-0.05, -0.85, RH - 0.25), yaw=10, flex=25, sp=(20, 0, 0), head=(-5, 0),
        hands={"L": ("r", (-0.05, -0.15, 0.25)), "R": ("r", (0.05, -0.15, 0.25))},
        feet={"L": ("g", (0.05, -0.95), 10), "R": ("g", (-0.15, -0.70), 10)})
WO.pose(2165, (-0.12, -1.15, RH - 0.06), yaw=15, flex=12, sp=(12, 0, 0), head=(5, 0),
        hands={"L": ("r", (-0.10, -0.25, 0.35)), "R": ("r", (0.10, -0.25, 0.35))}, feet=stand_feet(-0.12, -1.15, 15))
path_w = catmull([(2166, Vector((-0.12, -1.15, 0))), (2250, Vector((-0.55, -1.75, 0))), (2340, Vector((-0.95, -2.35, 0)))])
WO.walk(path_w, lambda f: 25.0, 2166, 2340, stride=0.55, lift=0.05, bob=0.012, crouch=0.06, lean=10)
for f in range(2166, 2341, 12):
    WO.r.key_rot("head", f, [("X", 8), ("Z", 0)])
for f in range(2170, 2490, 20):
    M = WO.Mb(path_w(min(f, 2340)) + Vector((0, 0, RH - 0.06)), 25, 5, 0)
    for s in "LR":
        sx = 1 if s == "L" else -1
        T = M @ Matrix.Translation(WO.wrist[s] + Vector((-sx * 0.34, -0.12, 0.26))) @ Matrix.Translation(-WO.wrist[s]) @ WO.r.rest("IK_hand." + s)
        WO.r.key_world("IK_hand." + s, f, T)
WO.pose(2380, (-0.95, -2.35, RH - 0.06), yaw=-20, flex=8, sp=(10, -20, 0), head=(5, -35),
        hands={"L": ("r", (-0.34, -0.12, 0.26)), "R": ("r", (0.34, -0.12, 0.26))}, feet=stand_feet(-0.95, -2.35, 25))
WO.pose(2460, (-0.95, -2.35, RH - 0.07), yaw=-25, flex=10, sp=(14, -25, 0), head=(15, -40),
        hands={"L": ("r", (-0.33, -0.12, 0.28)), "R": ("r", (0.33, -0.12, 0.28))}, feet=stand_feet(-0.95, -2.35, 25))

# ============================================================== SHOVER (hood up, face away)
hide_keys("Shover", [(1, False), (320, True)])
pS = catmull([(40, Vector((-2.6, -2.4, 0))), (100, Vector((-1.1, -2.0, 0))), (148, Vector((-0.02, -1.62, 0)))])
SH.walk(pS, lambda f: 180 - 30 * max(0, (148 - f)) / 108.0, 40, 148, stride=0.7, lift=0.08, bob=0.02, crouch=0.04, lean=8)
walk_arms(SH, pS, lambda f: 180 - 30 * max(0, (148 - f)) / 108.0, 40, 144, 0.7)
for f, dz, fl, hy, ext in ((154, 0.0, 8, -1.30, 0.0), (163, -0.03, 20, -1.12, 0.6), (172, -0.04, 28, -0.98, 1.0), (196, -0.02, 18, -1.05, 0.8), (226, 0.0, 5, -1.25, 0.0)):
    p = Vector((-0.02, -1.62 + 0.12 * ext, RH + dz))
    hands = {"L": ("w", (-0.12, hy, 1.08), (0, 0, 1), (0, -1, 0)), "R": ("w", (0.12, hy, 1.10), (0, 0, 1), (0, -1, 0))}
    SH.pose(f, p, yaw=180, flex=fl, sp=(fl * 0.6, 0, 0), head=(5, 0), hands=hands,
            feet={"L": ("g", (-0.14, -1.42 + 0.06 * ext), 180), "R": ("g", (0.12, -1.80 + 0.1 * ext), 175)}, curl={"L": 0.1, "R": 0.1})
pS2 = catmull([(232, Vector((-0.02, -1.62, 0))), (280, Vector((-1.5, -2.9, 0))), (320, Vector((-2.6, -4.3, 0)))])
SH.walk(pS2, lambda f: 35.0 if f > 240 else 180 - (f - 226) * 10, 232, 320, stride=1.1, lift=0.12, bob=0.03, crouch=0.08, lean=14)
walk_arms(SH, pS2, lambda f: 35.0 if f > 240 else 180 - (f - 226) * 10, 236, 320, 1.1, swing=0.22)

# ============================================================== PASSER-BY (beat 9)
hide_keys("Passerby", [(1, True), (1780, False)])
pP = catmull([(1780, Vector((3.2, -2.9, 0))), (1860, Vector((1.6, -1.8, 0))), (1905, Vector((0.78, -1.32, 0)))])
yawP = lambda f: 237.0 + 33.0 * smooth((f - 1860) / 45.0)
PB_.walk(pP, yawP, 1780, 1905, stride=0.72, lift=0.08, bob=0.02, crouch=0.04, lean=5)
walk_arms(PB_, pP, yawP, 1780, 1905, 0.72)
P0 = Vector((0.78, -1.32, 0))
# stops facing along the wall (-x), right ear turned to the bin; knocks with the right hand
for f, sd, hd, knock in ((1915, 4, (0, -20), 0), (1932, 12, (5, -35), 1), (1940, 12, (5, -35), 0), (1948, 12, (5, -35), 1), (1960, 6, (0, -15), 0), (1985, 0, (-5, -5), 0)):
    PB_.pose(f, (P0.x, P0.y, RH + 0.1), yaw=270, flex=3, side=0, sp=(6, 0, sd), head=hd,
             hands={"R": ("w", (0.55, FY - 0.03 - 0.04 * (1 - knock), 1.28), (0, 0, 1), (1, 0, 0)) if f < 1960 else ("r", (0.24, 0.05, -0.18)), "L": ("r", (-0.24, 0.08, -0.18))},
             feet=stand_feet(P0.x, P0.y, 270), curl={"L": 0.3, "R": 0.9})
# moves aside for the firefighters (1992-2058), then watches
pP2 = catmull([(1992, P0), (2030, Vector((1.4, -1.6, 0))), (2060, Vector((1.75, -1.9, 0)))])
yawP2 = lambda f: 270.0 + 156.0 * smooth((f - 1992) / 30.0) if f < 2040 else 426.0 - 66.0 * smooth((f - 2040) / 20.0)
PB_.walk(pP2, yawP2, 1992, 2058, stride=0.55, lift=0.06, bob=0.015)
walk_arms(PB_, pP2, yawP2, 1996, 2058, 0.55, swing=0.06)
for f, hd in ((2066, (-5, 15)), (2200, (0, -20)), (2400, (0, -40))):
    PB_.pose(f, (1.75, -1.9, RH - 0.02), yaw=360, flex=3, sp=(4, 0, 0), head=hd, hands={"L": ("r", (-0.24, 0.08, -0.18)), "R": ("r", (0.24, 0.08, -0.18))},
             feet=stand_feet(1.75, -1.9, 360))

# ============================================================== FIREFIGHTERS (beats 10-11)
hide_keys("FireA", [(1, True), (1975, False)]); hide_keys("FireB", [(1, True), (1975, False)])
CUT_Z = sc["chute_z"][0] - 0.12
def cutter_pos(f):     # cutting along the top edge of the front panel, then down the right edge
    t = max(0.0, min(1.0, (f - 1985) / 70.0))
    if t < 0.7:
        return Vector((-0.66 + 1.32 * (t / 0.7), FY - 0.06, CUT_Z))
    return Vector((0.66, FY - 0.06, CUT_Z - 0.9 * (t - 0.7) / 0.3))
sc["cut_z"] = CUT_Z
for f in list(range(1976, 2062, 6)) + [2060]:
    c = cutter_pos(f)
    kx = c.x - 0.25
    FA.pose(f, (kx, FY - 0.78, RH - 0.10), yaw=170, flex=14, sp=(14, 0, 0), head=(15, -10),
            hands={"L": ("w", c + Vector((-0.12, -0.25, 0.10)), (0.3, 1, 0), (0, 0, 1)), "R": ("w", c + Vector((0.05, -0.30, -0.02)), (0, 1, 0), (-1, 0, 0))},
            feet={"L": ("g", (kx + 0.12, FY - 0.62), 170), "R": ("g", (kx - 0.18, FY - 1.02), 175)}, curl={"L": 0.85, "R": 0.85})
PH = sc["chute_z"][0] - 0.15
def panel_edge(th):
    return Vector((0.5, FY + 0.006 - PH * math.sin(R_(th)), 0.06 + PH * math.cos(R_(th))))
for f, th, fy, fl in ((1976, 0, -1.0, 10), (2040, 0, -1.0, 12), (2060, 0, -1.0, 18), (2072, 15, -1.08, 25), (2085, 60, -1.3, 45)):
    e = panel_edge(th)
    FB.pose(f, (0.98, fy, RH - 0.05 - 0.2 * (fl > 30)), yaw=140, flex=fl * 0.6, sp=(fl, 0, 0), head=(15, 10),
            hands={"L": ("w", e + Vector((0.12, 0, 0.0)), (-0.3, 1, -0.6), (0, 0, 1)), "R": ("w", e + Vector((-0.12, 0, 0.0)), (-0.3, 1, -0.6), (0, 0, 1))},
            feet=stand_feet(0.98, fy, 140), curl={"L": 0.8, "R": 0.8})
FB.pose(2100, (0.95, -1.35, RH - 0.05), yaw=150, flex=8, sp=(8, 0, 0), head=(10, 20), hands={"L": ("r", (-0.2, 0.05, -0.15)), "R": ("r", (0.2, 0.05, -0.15))}, feet=stand_feet(0.95, -1.35, 150))
# FireB helps her out: hand on her arm, walks beside her
pFB = catmull([(2120, Vector((0.65, -1.45, 0))), (2200, Vector((0.05, -1.6, 0))), (2340, Vector((-0.45, -2.55, 0)))])
FB.walk(pFB, lambda f: 25.0, 2120, 2340, stride=0.6, lift=0.06, bob=0.015)
walk_arms(FB, pFB, lambda f: 25.0, 2120, 2340, 0.6, sides="L", swing=0.08)
for f in range(2140, 2341, 10):
    wp = path_w(min(max(f, 2166), 2340)) + Vector((0.18, 0.05, 1.10))
    FB.key_hand("R", f, wp, Vector((-1, 0.3, 0)), Vector((0, 0, 1)))
FA.pose(2078, (-1.0, FY - 0.75, RH - 0.05), yaw=160, flex=10, sp=(10, 0, 0), head=(5, 15), hands={"L": ("r", (-0.18, 0.0, -0.15)), "R": ("r", (0.18, -0.05, -0.12))}, feet=stand_feet(-1.0, FY - 0.75, 160))
FA.pose(2140, (-1.1, FY - 0.7, RH - 0.05), yaw=200, flex=10, sp=(10, 0, 0), head=(0, -10), hands={"L": ("r", (0, 0, 0.0)), "R": ("r", (0, -0.15, 0.2))}, feet=stand_feet(-1.1, FY - 0.7, 200))
FA.pose(2300, (-1.2, FY - 0.8, RH - 0.05), yaw=170, flex=8, sp=(8, 20, 0), head=(5, 25), hands={"L": ("r", (0, 0, 0.0)), "R": ("r", (0, -0.15, 0.2))}, feet=stand_feet(-1.2, FY - 0.8, 170))

# ============================================================== FLAP mechanism
FL = bpy.data.objects["Flap"]; FL.rotation_mode = 'XYZ'
def flap(f, deg):
    FL.rotation_euler.x = R_(deg); FL.keyframe_insert("rotation_euler", index=0, frame=f)
for f, d in ((1, 30), (40, 45), (80, 52), (150, 55), (180, 80), (215, 88), (250, 85), (290, 60), (318, 18), (330, -1.5), (335, 6), (341, -0.8), (347, 2), (353, 0),
             (575, 0), (605, 72), (640, 70), (668, 10), (676, -1.5), (682, 4), (690, 0),
             (790, 0), (805, -1.6), (812, 0.5), (835, -1.6), (842, 0.3), (850, 0),
             (2000, 0), (2400, 0)):
    flap(f, d)
pw = bpy.data.objects["Pawl"]
for f, d in ((1, 0), (330, 0), (338, -35), (345, -30), (800, -30), (806, -38), (812, -30)):
    pw.rotation_euler.x = R_(d); pw.keyframe_insert("rotation_euler", index=0, frame=f)
# ghost bag for the x-ray demo (575-700): pushed through the flap, drops into the bin
gb = bpy.data.objects["Bag03"].copy(); gb.data = bpy.data.objects["Bag03"].data.copy(); gb.name = "GhostBag"
bpy.data.collections["BIN"].objects.link(gb); gb.data.materials.clear()
gm = bpy.data.materials.new("GhostBagMat"); gm.use_nodes = True
gp = gm.node_tree.nodes["Principled BSDF"]; gp.inputs['Base Color'].default_value = (1, 0.6, 0.2, 1)
gp.inputs['Emission Color'].default_value = (1, 0.55, 0.15, 1); gp.inputs['Emission Strength'].default_value = 1.5
gb.data.materials.append(gm); gb.scale = (0.9, 0.7, 0.5)
for f, loc, h in ((1, (0, FY - 0.6, 1.35), True), (560, (0, FY - 0.6, 1.35), False), (590, (0, FY - 0.25, 1.38), False), (615, (0, FY + 0.15, 1.28), False),
                  (640, (0, FY + 0.45, 0.85), False), (650, (0, FY + 0.5, 0.60), False), (720, (0, FY + 0.5, 0.60), False), (725, (0, FY + 0.5, 0.60), True)):
    gb.location = loc; gb.keyframe_insert("location", frame=f)
    gb.hide_render = h; gb.keyframe_insert("hide_render", frame=f)
# bags squash under her landing
for nm in sc["bags"].split(",")[:26]:
    b = bpy.data.objects[nm]
    if (b.location.to_2d() - LAND.to_2d()).length < 0.65:
        s0 = b.scale.copy()
        for f, k in ((292, 1.0), (300, 0.8), (310, 1.06), (322, 1.0)):
            b.scale = (s0.x * (2 - k) ** 0.5, s0.y * (2 - k) ** 0.5, s0.z * k); b.keyframe_insert("scale", frame=f)
# cut panel (2060-2097): cut free, the firefighter pulls the top edge and it folds down onto the asphalt like a ramp
cp = bpy.data.objects["CutPanel"]
for f, th in ((2060, 0), (2072, 15), (2085, 60), (2094, 86), (2098, 84.5), (2102, 86)):
    cp.rotation_euler.x = R_(th); cp.keyframe_insert("rotation_euler", index=0, frame=f)
json.dump([{"beat": i + 1, "frame": 1 + round(t * 60), "first_words": w} for i, (t, w) in enumerate((
    (0.0, "She was reaching into"), (2.5, "when someone shoved her"), (4.9, "The heavy door slammed"), (8.4, "These bins are built"),
    (12.8, "Once you drop through"), (16.0, "There's no handle"), (22.0, "She screamed for help"), (25.0, "For three days"),
    (30.7, "Finally, someone heard"), (33.0, "and firefighters cut"), (34.9, "But this wasn't the first")))],
    open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
exec(open(os.path.join(HERE, "03b_fx_camera.py")).read())
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_DONE")
