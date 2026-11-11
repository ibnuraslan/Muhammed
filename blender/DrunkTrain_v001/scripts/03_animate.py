"""DrunkTrain animation: Lad (drunk man), bystanders, train. Then runs 03b (fx, x-ray, lights, camera).
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
random.seed(1616)
RAIL_H, GAUGE = sc["rail_h"], sc["gauge"]
STOP_Y = sc["stop_y"]
PLAT = eval(sc["plat"]); RAMP = eval(sc["ramp"])
V = lambda *a: Vector(a)
FPS = 60
def F(t): return 1 + round(t * FPS)

# ------------------------------------------------------------------ walkable surface
def ground_z(x, y):
    """ballast / sleeper top = 0, railheads, platform and its ramp"""
    for tx in (0.0, -4.3):
        for sx in (-1, 1):
            if abs(x - (tx + sx * GAUGE)) < 0.05:
                return RAIL_H
    if PLAT["x0"] <= x <= PLAT["x1"] and PLAT["y0"] <= y <= PLAT["y1"]:
        return PLAT["h"]
    if RAMP["x0"] <= x <= RAMP["x1"] and RAMP["y0"] <= y <= RAMP["y1"]:
        return RAMP["h"] * (1 - (y - RAMP["y0"]) / (RAMP["y1"] - RAMP["y0"]))
    # matches the ballast mesh: sleeper tops 0, ballast -0.03, shoulders sloping to the grass at -0.08
    if x > 3.4 or x < -8.6: return -0.08
    if x > 2.6: return -0.03 - 0.05 * (x - 2.6) / 0.8
    if x < -7.2: return -0.03 - 0.05 * (-7.2 - x) / 1.4
    if abs(x) < 1.3 or abs(x + 4.3) < 1.3: return 0.0
    return -0.03

# ------------------------------------------------------------------ train motion (front = plough tip y)
T_IMP = F(9.0)          # impact frame (beat 4)
V0 = 14.0               # m/s at impact (stops with a wheelset gap over him)
T_STOP = F(15.9)        # halts (beat 6 runs 14.5-17)
DEC = V0 / ((T_STOP - T_IMP) / FPS)
HEAD_Y = 0.0
def train_front(f):
    t = (f - T_IMP) / FPS
    if t <= 0:
        return HEAD_Y - V0 * t          # constant speed approach from +Y
    t = min(t, (T_STOP - T_IMP) / FPS)
    return HEAD_Y - (V0 * t - 0.5 * DEC * t * t)
def train_speed(f):
    t = (f - T_IMP) / FPS
    if t <= 0: return V0
    return max(0.0, V0 - DEC * t)
sc["train_stop_front"] = train_front(T_STOP)
TR = bpy.data.objects["TrainRig"]
plough_off = sc["plough_tip"]           # plough tip y in rig space
WHEEL_R = sc["wheel_r"]
wheels = [o for o in bpy.data.objects if o.parent == TR and o.name.startswith("wheel")]
ang = 0.0; prev = None
for f in range(1, sc.frame_end + 1):
    y = train_front(f) - plough_off
    # rocking at the stop
    rock = 0.0
    if f > T_STOP: rock = 0.012 * math.exp(-(f - T_STOP) / 25) * math.sin((f - T_STOP) / 4.0)
    if f % 2 == 1 or f in (T_IMP, T_STOP):
        TR.location = (0, y, 0); TR.rotation_euler = (rock, 0, 0)
        TR.keyframe_insert("location", frame=f); TR.keyframe_insert("rotation_euler", frame=f)
    if prev is not None:
        lock = f > F(14.5)            # wheels lock and slide in beat 6
        if not lock: ang += (prev - y) / WHEEL_R
    prev = y
    if f % 2 == 1:
        for wo in wheels:
            wo.rotation_euler = (ang, 0, 0); wo.keyframe_insert("rotation_euler", frame=f)
print("TRAIN stops at front y", round(train_front(T_STOP), 2), "decel", round(DEC, 2))

# ------------------------------------------------------------------ rigs
def setup(name):
    o = bpy.data.objects[name]
    r = make_human_ctrl(o)
    return Human(r)
LAD = setup("Lad"); WA = setup("WitA"); WB = setup("WitB"); WK = setup("Worker")

def bone_head(H, n): return H.r.BN[n].head_local.copy()
class Body:
    """body-relative limb keys: local coords = the rig's rest (standing) space"""
    def __init__(self, H):
        self.H = H; r = H.r
        self.RH = H.root_head
        self.sh = {s: bone_head(H, "upperarm01." + s) for s in "LR"}
        self.el = {s: bone_head(H, "lowerarm01." + s) for s in "LR"}
        self.wr = {s: bone_head(H, "wrist." + s) for s in "LR"}
        self.hip = {s: bone_head(H, "upperleg01." + s) for s in "LR"}
        self.kn = {s: bone_head(H, "lowerleg01." + s) for s in "LR"}
        self.an = {s: bone_head(H, "foot." + s) for s in "LR"}
        self.L_arm = {s: (self.el[s] - self.sh[s]).length + (self.wr[s] - self.el[s]).length for s in "LR"}
        self.L_leg = {s: (self.kn[s] - self.hip[s]).length + (self.an[s] - self.kn[s]).length for s in "LR"}
        self.head = bone_head(H, "head")
        self.dd = {}; self.nn = {}
        for s in "LR":
            wv = self.wr[s]; d = r.BN["finger3-1." + s].head_local - wv
            a = r.BN["finger2-1." + s].head_local - r.BN["finger5-1." + s].head_local
            self.dd[s] = d.normalized(); self.nn[s] = (d.cross(a) if s == "L" else a.cross(d)).normalized()
    def B(self, pos, R3):
        return Matrix.Translation(pos) @ R3.to_4x4() @ Matrix.Translation(-self.RH)
    def key_body(self, f, pos, R3, spine=(0, 0, 0), head=(0, 0)):
        self.H.r.key_world("root", f, self.B(pos, R3) @ self.H.r.rest("root"))
        self.H.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    def foot(self, s, f, Bm, p_local, R_local=None, pole_local=None):
        r = self.H.r; a = self.an[s]
        Rl = (R_local or Matrix.Identity(3)).to_4x4()
        M = Bm @ Matrix.Translation(p_local) @ Rl @ Matrix.Translation(-a) @ r.rest("IK_foot." + s)
        r.key_world("IK_foot." + s, f, M)
        pl = pole_local if pole_local is not None else self.kn[s] + V(0, -0.8, 0.05)
        pw = Bm @ pl; n = "Pole_knee." + s; pb = r.PB[n]
        pb.location = r.rest(n).to_3x3().inverted() @ (pw - r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    def foot_world(self, s, f, W, yaw_deg, pitch=0.0, pole_dir=None):
        """ankle at world W (flat foot, heading yaw)"""
        r = self.H.r; a = self.an[s]
        M = Matrix.Translation(W) @ Matrix.Rotation(R_(yaw_deg), 4, 'Z') @ Matrix.Rotation(R_(pitch), 4, 'X') @ Matrix.Translation(-a) @ r.rest("IK_foot." + s)
        r.key_world("IK_foot." + s, f, M)
        pole = W + V(0, 0, 0.45) + Matrix.Rotation(R_(yaw_deg), 3, 'Z') @ (pole_dir or V(0, -0.7, 0))
        n = "Pole_knee." + s; pb = r.PB[n]
        pb.location = r.rest(n).to_3x3().inverted() @ (pole - r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    def hand(self, s, f, Bm, p_local, d_local, n_local, pole_local=None):
        """wrist at body-local p, fingers along d, palm facing n (body-local)"""
        R3 = Bm.to_3x3().normalized()
        W = Bm @ p_local
        self.H.key_hand(s, f, W, R3 @ d_local, R3 @ n_local)
        sx = 1 if s == "L" else -1
        pl = pole_local if pole_local is not None else self.el[s] + V(sx * 0.25, 0.55, -0.1)
        pw = Bm @ pl; n = "Pole_elbow." + s; pb = self.H.r.PB[n]
        pb.location = self.H.r.rest(n).to_3x3().inverted() @ (pw - self.H.r.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
    def arm_dir(self, s, f, Bm, direction, reach=0.97, palm=None, pole_local=None):
        """arm straight-ish from the shoulder along a body-local direction"""
        d = direction.normalized()
        W = self.sh[s] + d * self.L_arm[s] * reach
        sx = 1 if s == "L" else -1
        n = palm if palm is not None else (V(-sx, 0, 0) - d * V(-sx, 0, 0).dot(d)).normalized() if abs(d.x) < 0.9 else V(0, 0, -1)
        self.hand(s, f, Bm, W, d, n, pole_local)
    def leg_dir(self, s, f, Bm, direction, reach=0.98, pole_local=None, toe_pitch=0.0):
        d = direction.normalized()
        W = self.hip[s] + d * self.L_leg[s] * reach
        R = V(0, 0, -1).rotation_difference(d).to_matrix() @ Matrix.Rotation(R_(toe_pitch), 3, 'X')
        self.foot(s, f, Bm, W, R, pole_local)

def Rbody(yaw=0.0, pitch=0.0, roll=0.0, side=0.0):
    """yaw about world Z, pitch about X (-90 = lying on the back), roll about the body's long axis, side lean"""
    return Matrix.Rotation(R_(yaw), 3, 'Z') @ Matrix.Rotation(R_(pitch), 3, 'X') @ Matrix.Rotation(R_(side), 3, 'Y') @ Matrix.Rotation(R_(roll), 3, 'Z')

LB = Body(LAD); RH = LB.RH
print("LAD root", [round(v, 3) for v in RH], "arm", round(LB.L_arm["L"], 3), "leg", round(LB.L_leg["L"], 3))

# ------------------------------------------------------------------ generic gait with drunk sway
RAIL_XS = [tx + sx * GAUGE for tx in (0.0, -4.3) for sx in (-1, 1)]
def off_rail(xy, clear=0.3):
    """never plant a foot across a rail: shift the plant to the nearer side"""
    for rx in RAIL_XS:
        if abs(xy.x - rx) < clear:
            xy = Vector((rx + math.copysign(clear, xy.x - rx if xy.x != rx else 1), xy.y))
    return xy
def gait(H, path, yaw_fn, f0, f1, stride=0.75, duty=0.62, lift=0.08, bob=0.022, crouch=0.03, lean=6.0, step=2,
         side_fn=None, spine_fn=None, arms_fn=None, body=None, foot_hold=None):
    frames = list(range(f0, f1 + 1)); dist = [0.0]
    for a_, b_ in zip(frames, frames[1:]):
        dist.append(dist[-1] + (path(b_) - path(a_)).to_2d().length)
    for s, ph in (("L", 0.0), ("R", 0.5)):
        cyc = [d / stride + ph for d in dist]; per = {}
        for i, c in enumerate(cyc): per.setdefault(int(math.floor(c)), []).append(i)
        plant = {}
        for pid, idx in per.items():
            st = [i for i in idx if (cyc[i] % 1.0) < duty]
            if st:
                im = min(st, key=lambda i: abs((cyc[i] % 1.0) - duty / 2))
                plant[pid] = (off_rail(H.foot_xy(s, path(frames[im]), yaw_fn(frames[im]))), yaw_fn(frames[im]))
        first = (H.foot_xy(s, path(f0), yaw_fn(f0)), yaw_fn(f0)); last = (H.foot_xy(s, path(f1), yaw_fn(f1)), yaw_fn(f1))
        for i, f in enumerate(frames):
            if (i % step) and i != len(frames) - 1: continue
            if foot_hold and s in foot_hold and foot_hold[s][0] <= f <= foot_hold[s][1]:
                continue
            pid = int(math.floor(cyc[i])); fr = cyc[i] % 1.0
            if fr < duty:
                xy, yw = plant.get(pid, first if i < len(frames) / 2 else last); lf = 0.0; pt = 0.0
            else:
                a_ = plant.get(pid, first); b_ = plant.get(pid + 1, last); u = (fr - duty) / (1 - duty)
                xy = a_[0].lerp(b_[0], smooth(u)); yw = a_[1] + (b_[1] - a_[1]) * smooth(u)
                gz_a, gz_b = ground_z(*a_[0]), ground_z(*b_[0])
                lf = lift * math.sin(math.pi * u) + (gz_b - gz_a) * smooth(u) * 0 ; pt = 25 * math.sin(math.pi * u) - 10
            H.key_foot(s, f, xy, yw, lf, pt)
    for i, f in enumerate(frames):
        if (i % step) and i != len(frames) - 1: continue
        p = path(f); cyc = (dist[i] / stride) % 1.0
        gz_ = 0.5 * (ground_z(p.x, p.y) + max(ground_z(*H.foot_xy("L", p, yaw_fn(f))), ground_z(*H.foot_xy("R", p, yaw_fn(f)))))
        gz_ = ground_z(p.x, p.y) if ground_z(p.x, p.y) > 0.3 or gz_ < 0.1 else max(0.0, gz_ * 0.5)
        z = gz_ + H.root_head.z - crouch - bob * (0.5 + 0.5 * math.cos(4 * math.pi * cyc))
        yw = yaw_fn(f)
        sd = side_fn(f, cyc) if side_fn else 3 * math.sin(2 * math.pi * cyc)
        H.key_root(f, Vector((p.x, p.y, z)), yaw=yw, flex=lean * 0.5, side=sd)
        if spine_fn: spine_fn(f, cyc)
        else: H.key_spine(f, flex=lean, twist=-6 * math.sin(2 * math.pi * cyc))
        if arms_fn: arms_fn(f, cyc, Vector((p.x, p.y, z)), yw, sd)
    return dist[-1]

def stand_B(Bd, pos_xy, yaw, z_off=0.0, side=0.0, flex=0.0):
    p = V(pos_xy[0], pos_xy[1], ground_z(pos_xy[0], pos_xy[1]) + Bd.RH.z + z_off)
    return Bd.B(p, Rbody(yaw=yaw, pitch=flex, side=side)), p

def hang_arms(Bd, f, Bm, swing=(0.0, 0.0), out=(0.3, 0.3), bend=(0.1, 0.1)):
    for k, s in enumerate("LR"):
        sx = 1 if s == "L" else -1
        d = V(sx * out[k], -swing[k], -1.0)
        Bd.arm_dir(s, f, Bm, d, reach=0.97 - 0.12 * bend[k])

# ==================================================================== LAD
f_walk0, f_trip = 1, F(1.95)
WP = catmull([(1, V(-2.75, 2.05, 0)), (28, V(-2.25, 1.45, 0)), (55, V(-1.55, 1.85, 0)), (80, V(-0.85, 1.25, 0)),
              (100, V(-0.15, 1.45, 0)), (f_trip, V(0.32, 1.05, 0))])
WY = catmull([(1, 70.0), (25, 115.0), (50, 65.0), (75, 120.0), (95, 75.0), (f_trip, 98.0)])
def lad_side(f, cyc): return 9 * math.sin(2 * math.pi * cyc) + 6 * math.sin(f / 9.0)
def lad_spine(f, cyc):
    LAD.key_spine(f, flex=14 + 6 * math.sin(f / 11.0), twist=-12 * math.sin(2 * math.pi * cyc), side=10 * math.sin(f / 13.0 + 1),
                  head=(-8 + 10 * math.sin(f / 7.0), 14 * math.sin(f / 17.0)))
def lad_arms(f, cyc, p, yw, sd):
    Bm = LB.B(p, Rbody(yaw=yw, pitch=7, side=sd))
    # loose drunk arms: big, out of phase swing, flung out for balance
    sL = 0.45 * math.sin(2 * math.pi * cyc) + 0.2 * math.sin(f / 6.0)
    sR = -0.45 * math.sin(2 * math.pi * cyc) + 0.2 * math.sin(f / 5.0 + 2)
    LB.arm_dir("L", f, Bm, V(0.55 + 0.3 * math.sin(f / 8.0), -sL, -0.8), reach=0.92)
    LB.arm_dir("R", f, Bm, V(-0.5 - 0.3 * math.sin(f / 9.0 + 1), -sR, -0.85), reach=0.92)
gait(LAD, WP, WY, f_walk0, f_trip, stride=0.62, duty=0.6, lift=0.26, bob=0.04, crouch=0.06, lean=14, side_fn=lad_side,
     spine_fn=lad_spine, arms_fn=lad_arms)

# --- trip over the near rail (x = +GAUGE), stumble, turn, sit, lie back with head on the rail
# poses: (frame, root xyz, yaw, pitch(fwd lean +), side, spine flex, head pitch, arms (L dir, R dir), feet: ('w', xy, yaw) world or ('l', local))
HEAD_REST = V(GAUGE + 0.02, HEAD_Y, RAIL_H + 0.095)      # back of the head on the railhead
def foot_w(s, f, xy, yaw, lift=0.0, pitch=0.0):
    LB.foot_world(s, f, V(xy[0], xy[1], ground_z(*xy) + LB.an[s].z + lift), yaw, pitch)
TRIP = [
    # f, root pos, yaw, pitch, side, flex, head, armL, armR
    (f_trip,     V(0.32, 1.05, RH.z - 0.06), 98, 8, 4, 14, -6, V(0.6, -0.2, -0.8), V(-0.6, 0.3, -0.8)),
    (f_trip + 8, V(0.62, 1.02, RH.z - 0.10), 96, 28, -6, 30, -18, V(0.7, -0.9, 0.2), V(-0.6, -0.9, 0.3)),     # toe caught: pitches forward, arms fly out front
    (f_trip + 16, V(1.02, 0.98, RH.z - 0.16), 92, 38, 6, 36, -22, V(0.8, -0.8, 0.5), V(-0.8, -0.7, 0.6)),
    (f_trip + 26, V(1.45, 0.86, RH.z - 0.12), 88, 24, -10, 22, -10, V(0.9, -0.3, 0.1), V(-0.9, -0.1, -0.1)),   # catches himself
    (f_trip + 38, V(1.78, 0.74, RH.z - 0.06), 70, 6, 12, 8, 10, V(0.9, 0.2, -0.4), V(-0.7, 0.5, -0.5)),        # overcorrects backward
    (f_trip + 52, V(1.86, 0.52, RH.z - 0.08), 40, -6, -8, 0, 14, V(0.7, 0.3, -0.6), V(-0.6, 0.2, -0.7)),       # wobbling turn
    (f_trip + 66, V(1.82, 0.28, RH.z - 0.10), 10, -4, 10, 6, -8, V(0.6, -0.1, -0.8), V(-0.6, 0.1, -0.8)),
    (f_trip + 80, V(1.78, 0.10, RH.z - 0.12), -20, 4, -8, 10, -12, V(0.5, -0.2, -0.8), V(-0.6, -0.2, -0.8)),   # facing +x-ish, back to the rail
    (f_trip + 92, V(1.74, 0.02, RH.z - 0.42), -2, 12, 0, 18, -10, V(0.6, -0.6, -0.4), V(-0.6, -0.6, -0.4)),   # knees buckle
]
# yaw here: 0 = facing -Y; +90 = facing +X. He faces +X (away from the rail) when he sits.
for i, (f, p, yw, pi, sd, fl, hd, aL, aR) in enumerate(TRIP):
    TRIP[i] = (f, p, yw + 0, pi, sd, fl, hd, aL, aR)
TRIP_FIX = []
for (f, p, yw, pi, sd, fl, hd, aL, aR) in TRIP:
    yw2 = yw if f <= f_trip + 26 else (88 + (yw - 88) * 0.0 + 0)  # keep facing +X; wobble via side/twist instead
    TRIP_FIX.append((f, p, yw if f <= f_trip + 26 else 90 + 0.35 * (yw - 40), pi, sd, fl, hd, aL, aR))
for (f, p, yw, pi, sd, fl, hd, aL, aR) in TRIP_FIX:
    Bm = LB.B(p, Rbody(yaw=yw, pitch=pi, side=sd))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=fl, twist=8 * math.sin(f / 7.0), side=sd * 0.8, head=(hd, 10 * math.sin(f / 9.0)))
    LB.arm_dir("L", f, Bm, aL, reach=0.93); LB.arm_dir("R", f, Bm, aR, reach=0.93)
# trip feet: R toe snagged against the rail side, L lunges, R frees, small staggers, then both plant for the sit
ft = f_trip
foot_w("R", ft, (0.55, 0.95), 95, 0.0, -10); foot_w("R", ft + 10, (0.6, 0.95), 95, 0.03, -25)      # toe under the railhead lip
foot_w("L", ft, (0.25, 1.18), 98, 0.0); foot_w("L", ft + 6, (0.6, 1.12), 96, 0.22, 20); foot_w("L", ft + 14, (1.18, 1.06), 92, 0.0)
foot_w("R", ft + 16, (0.95, 0.96), 92, 0.26, 25); foot_w("R", ft + 24, (1.62, 0.84), 90, 0.0)
foot_w("L", ft + 26, (1.42, 1.0), 90, 0.18, 20); foot_w("L", ft + 34, (2.05, 0.82), 80, 0.0)          # big recovery step
foot_w("R", ft + 40, (1.95, 0.6), 70, 0.15); foot_w("R", ft + 48, (1.72, 0.48), 60, 0.0)                # staggers back
foot_w("L", ft + 52, (2.0, 0.62), 70, 0.12); foot_w("L", ft + 60, (1.98, 0.2), 80, 0.0)
foot_w("R", ft + 64, (1.75, 0.38), 75, 0.12); foot_w("R", ft + 72, (1.95, -0.18), 90, 0.0)
foot_w("L", ft + 92, (1.98, 0.2), 85, 0.0); foot_w("R", ft + 92, (1.98, -0.16), 92, 0.0)
# --- sit down hard (butt to ballast), sway, flop back: head lands on the rail
f_sit = ft + 104; f_sway = f_sit + 30; f_flop = f_sway + 34; f_land = f_flop + 8
SIT_P = V(1.56, 0.02, 0.13)
LIE_ROOT = None
def lying_B(f_, roll=0.0, z=0.12, x=None, yaw=-90.0):
    xx = x if x is not None else HEAD_REST.x + (LB.head.z + 0.1 - RH.z) * 0.93
    return LB.B(V(xx, HEAD_Y, z), Rbody(yaw=yaw, pitch=-90, roll=roll)), V(xx, HEAD_Y, z)
# yaw for lying: head toward -X. Rbody(yaw=-90, pitch=-90): rest +Z (head) -> world -X
for f, z, pi, fl, hd, arms in ((f_sit - 6, 0.36, 10, 30, -5, "out"), (f_sit, SIT_P.z - 0.02, -8, 34, -14, "down"), (f_sit + 5, SIT_P.z + 0.03, -2, 26, 10, "down"),
                              (f_sit + 12, SIT_P.z, -6, 30, 0, "knees"), (f_sway, SIT_P.z, -14, 22, -20, "knees"), (f_sway + 14, SIT_P.z, -4, 34, 14, "knees")):
    Bm = LB.B(V(SIT_P.x, SIT_P.y, z), Rbody(yaw=90, pitch=pi, side=6 * math.sin(f / 6.0)))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=fl, twist=10 * math.sin(f / 8.0), side=8 * math.sin(f / 10.0), head=(hd, 18 * math.sin(f / 11.0)))
    for s in "LR":
        sx = 1 if s == "L" else -1
        # legs forward, knees up (sitting)
        LB.foot(s, f, Bm, V(sx * 0.17, -0.55, RH.z - 0.07), Matrix.Rotation(R_(-20), 3, 'X'))
        if arms == "out": LB.arm_dir(s, f, Bm, V(sx * 0.6, -0.5, -0.4), 0.93)
        elif arms == "down": LB.arm_dir(s, f, Bm, V(sx * 0.35, 0.35, -0.9), 0.95, palm=V(0, 0, -1))      # hands slap the ballast behind
        else: LB.hand(s, f, Bm, V(sx * 0.16, -0.5, RH.z - 0.28), V(0, -0.3, -1), V(-sx, 0, 0))            # forearms draped on knees
# flop: the torso falls back; root slides to lying; legs straighten out along +X
for f, roll_z, prog in ((f_flop, 0.13, 0.0), (f_flop + 4, 0.13, 0.45), (f_land, 0.12, 1.0), (f_land + 4, 0.14, 1.04), (f_land + 9, 0.12, 1.0)):
    pi = -14 + (-90 + 14) * min(1.0, prog)
    xx = SIT_P.x + (lying_B(f)[1].x - SIT_P.x) * min(1.0, prog) * 0.0 + (lying_B(f)[1].x - SIT_P.x) * min(1, prog)
    Bm = LB.B(V(xx, HEAD_Y * prog + SIT_P.y * (1 - prog), roll_z), Rbody(yaw=90, pitch=pi))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=30 * (1 - prog) + 6 * prog, side=0, head=(6 * prog - 10 * (1 - prog) + (8 if f == f_land + 4 else 0), 25 * prog))
    for s in "LR":
        sx = 1 if s == "L" else -1
        k = min(1.0, prog)
        LB.foot(s, f, Bm, V(sx * (0.17 + 0.07 * k), -0.55 * (1 - k) + (LB.an[s].y + 0.02) * k, (RH.z - 0.07) * (1 - k) + LB.an[s].z * k), Matrix.Rotation(R_(-20 * (1 - k) + 0), 3, 'X') @ Matrix.Rotation(R_(sx * 25 * k), 3, 'Z'))
        LB.arm_dir(s, f, Bm, V(sx * (0.6 + 0.3 * k), 0.35 * (1 - k) + 0.05, -0.9 + 0.5 * k), 0.95, palm=V(0, 0.3, -1))
# yaw 90 + pitch -90: rest +Z (head) maps to Rz(90) @ Rx(-90) @ Z = Rz(90) @ (0,1,0) = (-1,0,0): head toward -X. Good.
# --- lying, snoring: chest breathes, right hand flops off the belly, rail tremor shakes the head before impact
f_lie0, f_lie1 = f_land + 10, T_IMP - 1
def lie_B(f):
    return LB.B(V(lying_B(f)[1].x, HEAD_Y, 0.085), Rbody(yaw=90, pitch=-90))
for f in list(range(f_lie0, f_lie1 + 1, 3)) + [f_lie1]:
    Bm = lie_B(f)
    br = math.sin(2 * math.pi * (f - f_lie0) / 150.0)            # 2.5 s snore cycle
    trem = 0.0 if f < F(7.0) else (f - F(7.0)) / (f_lie1 - F(7.0))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=6 - 1.5 * br, side=0, twist=0,
                  head=(5.5 + 0.8 * br + 1.0 * trem * math.sin(f * 2.7), 25 + 2 * math.sin(f / 37.0) + 3 * trem * math.sin(f * 3.1)))
    for s in "LR":
        sx = 1 if s == "L" else -1
        LB.foot(s, f, Bm, V(sx * 0.24, LB.an[s].y + 0.1, LB.an[s].z), Matrix.Rotation(R_(sx * 25), 3, 'Z'))
    LB.arm_dir("L", f, Bm, V(0.85, 0.08, -0.5), 0.95, palm=V(0, 0.3, -1))
    if f < F(4.6):
        LB.hand("R", f, Bm, V(-0.02, -0.16 - 0.012 * br, RH.z + 0.18), V(0.9, -0.1, -0.2), V(0, 1, 0))     # hand resting on his belly
    elif f < F(4.75):
        LB.arm_dir("R", f, Bm, V(-0.55, -0.6, 0.3), 0.9, palm=V(0, 0.4, -1))
    else:
        LB.arm_dir("R", f, Bm, V(-0.42, -0.18, 0.75), 0.86, palm=V(0, -0.2, 1))                     # flopped over the rail beside his head

# --- impact + rag-doll spin (beat 4) and drag beneath the train (beat 5), come to rest prone (by 14.3 s)
f_rest = F(14.3)
LIE_X = lying_B(f_lie1)[1].x
def drag_state(f):
    """root position and rotation from impact to rest"""
    t = (f - T_IMP) / (f_rest - T_IMP)
    tf = train_front(f)
    if f <= T_IMP + 120:
        u = (f - T_IMP) / 120.0
        rel = -0.35 + 3.2 * smooth(u)                    # in front of the plough -> pulled under the front bogie side
        y = tf + rel
        x = LIE_X + (0.0 - LIE_X) * smooth(min(1.0, u / 0.35))
        z = 0.14 + (0.3 * math.sin(math.pi * u / 0.2) if u < 0.2 else 0.02 * abs(math.sin(u * 9)))     # thrown up at the hit, then low under the plough
        yaw = 90 + 450 * (1 - (1 - min(1.0, u / 0.6)) ** 2)   # spins around (ends heading -Y before the first wheelset)
        roll = 300 * u + 40 * math.sin(u * 7)
        pitch = -90 + 18 * math.sin(u * 6.5) * (1 - u)
    else:
        u = (f - (T_IMP + 120)) / (f_rest - (T_IMP + 120))
        y0 = train_front(T_IMP + 120) + 2.85
        y = max(y0 + (STOP_Y - y0) * (1 - (1 - min(1, u)) ** 2.2), tf + 2.6)     # never ahead of the plough
        x = 0.0 + 0.04 * math.sin(u * 13)
        z = 0.15 + 0.08 * smooth(min(1, u)) + 0.07 * abs(math.sin(u * 22)) * (1 - u)
        yaw = 540 + 25 * math.sin(u * 8) * (1 - u)
        roll = 300 + 40 * math.sin(7) + 900 * (1 - (1 - min(1, u)) ** 2)     # log-rolls 2.5 turns; ends prone (300+900 = 1200 = 3*360+120 -> fix below)
        pitch = -90
    return V(x, y, z), yaw, roll, pitch
# make the final roll land prone (face down): supine roll 0 -> prone roll 180 (mod 360)
_, _, r_end, _ = drag_state(f_rest)
ROLL_FIX = (180 - (r_end % 360))
def drag_full(f):
    p, yw, rl, pi = drag_state(f)
    if f > T_IMP + 120:
        u = (f - (T_IMP + 120)) / (f_rest - (T_IMP + 120)); rl += ROLL_FIX * smooth(u)
    return p, Rbody(yaw=yw, pitch=pi, roll=rl)
def above_ground(origin, d_w, L, floor=0.07, ceil=None):
    """clamp a limb so its end (plus ~0.18 m of hand/foot) stays above the ballast, between the wheels and under the chassis"""
    d_w = d_w.normalized()
    for _ in range(6):
        e = origin + d_w * L
        if e.z < floor:
            d_w.z += (floor - e.z) / L
        if ceil is not None:
            if abs(e.x) > 0.3:
                d_w.x -= (e.x - math.copysign(0.3, e.x)) / L
            if e.z > ceil - 0.12:
                d_w.z -= (e.z - (ceil - 0.12)) / L
        d_w.normalize()
    return d_w
HIST = {}
for f in range(T_IMP - 12, f_rest + 1):
    HIST[f] = drag_full(f) if f >= T_IMP else (lie_B(f), None)
def Bm_at(f):
    if f < T_IMP: return lie_B(f)
    p, R3 = drag_full(min(f, f_rest)); return LB.B(p, R3)
LIMB_POSE = []   # rag-doll limb directions, re-randomised every ~10 frames, smoothed by lag
for k in range(0, 40):
    LIMB_POSE.append(dict(aL=V(random.uniform(0.3, 1.0), random.uniform(-0.8, 0.8), random.uniform(-0.6, 0.9)),
                          aR=V(random.uniform(-1.0, -0.3), random.uniform(-0.8, 0.8), random.uniform(-0.6, 0.9)),
                          lL=V(random.uniform(0.05, 0.6), random.uniform(-0.9, 0.5), -1.0),
                          lR=V(random.uniform(-0.6, -0.05), random.uniform(-0.9, 0.5), -1.0)))
def limb_dir(key, f):
    seg = 10.0 if f < T_IMP + 140 else 16.0
    x = (f - T_IMP) / seg; i = int(x); u = smooth(x - i)
    a, b = LIMB_POSE[min(i, 39)][key], LIMB_POSE[min(i + 1, 39)][key]
    calm = max(0.0, min(1.0, (f - (f_rest - 70)) / 70.0))      # limbs settle as he stops
    rest = {"aL": V(0.5, 0.1, -0.85), "aR": V(-0.45, -0.1, -0.88), "lL": V(0.12, 0.05, -1), "lR": V(-0.1, 0.1, -1)}[key]
    return (a.lerp(b, u)).lerp(rest, calm)
for f in list(range(T_IMP, f_rest + 1, 2)) + [f_rest]:
    p, R3 = drag_full(f)
    Bm = LB.B(p, R3)
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    u = min(1.0, (f - T_IMP) / 120.0); calm = max(0.0, min(1.0, (f - (f_rest - 70)) / 70.0))
    LAD.key_spine(f, flex=(25 * math.sin(f / 5.0)) * (1 - calm) + 4 * calm, twist=30 * math.sin(f / 7.0) * (1 - calm),
                  side=25 * math.sin(f / 6.0 + 1) * (1 - calm), head=((30 if f < T_IMP + 60 else 10) * math.sin(f / 4.0 + 2) * (1 - calm), (35 * math.sin(f / 5.0)) * (1 - calm) - 40 * calm))
    lag_B = Bm_at(f - 5); lag_B2 = Bm_at(f - 8)
    # limbs trail the torso: directions expressed in the torso frame of a few frames ago
    for s, key, LBm in (("L", "aL", lag_B), ("R", "aR", lag_B)):
        d_w = LBm.to_3x3() @ limb_dir(key, f)
        if f > T_IMP + 40 and d_w.x < -0.15:                  # keep the flung arms clear of the wheels (wheels are on his -X side)
            d_w.x = -0.15; d_w.z = max(d_w.z, -0.2); d_w.normalize()
        d_w = above_ground(Bm @ LB.sh[s], d_w, LB.L_arm[s] * 0.98, ceil=(0.36 if p.y - train_front(f) < 1.3 else 0.4) if f > T_IMP + 10 else None)
        d_l = Bm.to_3x3().inverted() @ d_w
        sxx = 1 if s == "L" else -1
        if sxx * d_l.x < 0.3: d_l.x = sxx * 0.3; d_l.normalize()       # flung arms never cross his own body
        LB.arm_dir(s, f, Bm, d_l, 0.98 if f > T_IMP + 10 else 0.92)
    for s, key, LBm in (("L", "lL", lag_B2), ("R", "lR", lag_B2)):
        d_w = LBm.to_3x3() @ limb_dir(key, f)
        if f > T_IMP + 40 and d_w.x < -0.15:
            d_w.x = -0.15; d_w.normalize()
        d_w = above_ground(Bm @ LB.hip[s], d_w, LB.L_leg[s] * 0.97, floor=0.17, ceil=(0.36 if p.y - train_front(f) < 1.3 else 0.4) if f > T_IMP + 10 else None)
        d_l = Bm.to_3x3().inverted() @ d_w
        LB.leg_dir(s, f, Bm, d_l, 0.97)
REST_P, REST_R = drag_full(f_rest)
sc["lad_rest"] = str(tuple(REST_P))
# --- lies still (prone) while the train stops and witnesses arrive; faint breathing only
f_stir = F(19.2)
REST_B = LB.B(REST_P, REST_R)
for f in list(range(f_rest + 4, f_stir + 1, 10)) + [f_stir]:
    LAD.r.key_world("root", f, REST_B @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=4 + 0.8 * math.sin(f / 30.0), head=(0, -40))
    for s, key in (("L", "aL"), ("R", "aR")):
        LB.arm_dir(s, f, REST_B, {"aL": V(0.5, 0.1, -0.85), "aR": V(-0.45, -0.1, -0.88)}[key], 0.92)
    for s, key in (("L", "lL"), ("R", "lR")):
        LB.leg_dir(s, f, REST_B, {"lL": V(0.12, 0.05, -1), "lR": V(-0.1, 0.1, -1)}[key], 0.97)

# --- stirs, crawls out sideways (+X) on hands and knees, stands up wobbling (beat 8)
STAND_XY = V(2.45, STOP_Y - 0.1, 0)
f_crawl0, f_crawl1, f_up0, f_up1 = f_stir + 12, F(20.4), F(20.4) + 2, F(20.95)
# stir: head lifts, hands push under shoulders (prone push-up)
for f, push in ((f_stir + 4, 0.0), (f_stir + 10, 0.35), (f_crawl0, 1.0)):
    p = REST_P + V(0, 0, 0.06 * push); Bm = LB.B(p, REST_R @ Matrix.Rotation(R_(-0 * push), 3, 'X'))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=4 - 18 * push, head=(-25 * push, -40 * (1 - push)))
    for s in "LR":
        sx = 1 if s == "L" else -1
        LB.hand(s, f, Bm, LB.sh[s] + V(sx * 0.2, -0.35 * push, -0.05), V(0, -1, -0.2).normalized(), V(0, 1, 0))
    for s, key in (("L", "lL"), ("R", "lR")):
        LB.leg_dir(s, f, Bm, {"lL": V(0.12, 0.05, -1), "lR": V(-0.1, 0.1, -1)}[key], 0.97)
# crawl: on all fours, torso horizontal facing +X, hands and knees alternate (planted in world)
CR0 = V(REST_P.x + 0.2, REST_P.y, 0.0); CR1 = V(STAND_XY.x - 0.45, STAND_XY.y, 0.0)
def crawl_root(f):
    u = (f - f_crawl0) / (f_crawl1 - f_crawl0)
    return CR0.lerp(CR1, smooth(u))
for f in list(range(f_crawl0, f_crawl1 + 1, 2)) + [f_crawl1]:
    u = (f - f_crawl0) / (f_crawl1 - f_crawl0)
    c = crawl_root(f); yaw_c = 0 + 90 * smooth(min(1, u * 2.5))           # turns from heading -Y to facing +X
    cz = 0.4 + 0.15 * smooth((c.x - 1.4) / 0.4)           # low commando crawl until he clears the loco side
    Bm = LB.B(V(c.x, c.y, cz + 0.03 * math.sin(u * 12)), Rbody(yaw=yaw_c, pitch=84, side=6 * math.sin(u * 12)))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=-8, twist=8 * math.sin(u * 12), head=(-45, 10 * math.sin(u * 7)))
    ph = u * 4.0
    for k, s in enumerate("LR"):
        sx = 1 if s == "L" else -1
        q = (ph + 0.5 * k) % 1.0; lift = 0.08 * math.sin(math.pi * q) if q > 0.6 else 0.0
        fwd = 0.35 * (q if q <= 0.6 else 0.6 - (q - 0.6) * 1.5)
        # hand under the shoulder (world: down), knee under the hip: hands planted with palms flat
        Wh = Bm @ (LB.sh[s] + V(sx * 0.04, -0.06 - fwd * 0.4, -0.0))
        Wh = V(Wh.x, Wh.y, ground_z(Wh.x, Wh.y) + 0.05 + lift)
        LAD.key_hand(s, f, Wh, Bm.to_3x3() @ V(0, -1, 0), V(0, 0, -1))
        hw = Bm @ LB.hip[s]; fwd_ = V(math.sin(R_(yaw_c)), -math.cos(R_(yaw_c)), 0)
        kq = (ph + 0.5 * k + 0.5) % 1.0; kf = 0.25 * (kq if kq <= 0.6 else 0.6 - (kq - 0.6) * 1.5); klift = 0.06 * math.sin(math.pi * kq) if kq > 0.6 else 0.0
        Wa = hw - fwd_ * (0.44 - kf) ; Wa = V(Wa.x, Wa.y, ground_z(Wa.x, Wa.y) + 0.085 + klift)
        LB.foot_world(s, f, Wa, yaw_c, pitch=165, pole_dir=V(0, -0.9, -0.6))
# stand up: push back onto the feet, rise, wobble
for f, z_k, pi, fl in ((f_up0, 0.55, 75, -8), (f_up0 + 10, 0.65, 45, 30), (f_up0 + 20, RH.z - 0.35, 25, 35), (f_up0 + 32, RH.z - 0.06, 6, 10), (f_up1, RH.z - 0.03, -4, 6)):
    Bm = LB.B(V(STAND_XY.x - 0.15 * (1 - (z_k - 0.55) / (RH.z - 0.58)), STAND_XY.y, z_k), Rbody(yaw=90, pitch=pi, side=8 * math.sin(f / 5.0)))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=fl, twist=10 * math.sin(f / 6.0), side=6 * math.sin(f / 7.0), head=(-15 + 10 * math.sin(f / 5.0), 20 * math.sin(f / 9.0)))
    for s in "LR":
        sx = 1 if s == "L" else -1
        if f <= f_up0 + 10:
            LB.hand(s, f, Bm, LB.sh[s] + V(sx * 0.05, -0.2, -0.45), V(0, -0.6, -1).normalized(), V(0, 0, -1))
        else:
            LB.arm_dir(s, f, Bm, V(sx * 0.55, -0.2 + 0.3 * math.sin(f / 6.0 + sx), -0.7), 0.93)
for s in "LR":
    sx = 1 if s == "L" else -1
    for f in (f_up0, f_up1):
        foot_w(s, f, (STAND_XY.x - 0.05, STAND_XY.y + sx * 0.16), 90 + sx * 8)

# --- beat 9 (21.0-23.5): flash-back swig from the bottle, standing, swaying
f_fb0, f_fb1 = F(21.0), F(23.5)
SWIG_UP, SWIG_HOLD, SWIG_DOWN = f_fb0 + 22, f_fb0 + 60, f_fb0 + 100
for f in list(range(f_up1 + 2, f_fb1 + 1, 3)) + [f_fb1]:
    sw = math.sin(f / 13.0)
    Bm = LB.B(V(STAND_XY.x + 0.03 * sw, STAND_XY.y + 0.04 * math.sin(f / 9.0), RH.z - 0.03), Rbody(yaw=90 + 6 * math.sin(f / 17.0), pitch=2, side=7 * sw))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    tilt = 0.0
    if f >= f_fb0:
        if f < SWIG_UP: tilt = smooth((f - f_fb0) / (SWIG_UP - f_fb0))
        elif f < SWIG_HOLD: tilt = 1.0
        elif f < SWIG_DOWN: tilt = 1 - smooth((f - SWIG_HOLD) / (SWIG_DOWN - SWIG_HOLD))
    LAD.key_spine(f, flex=6 - 14 * tilt, twist=6 * math.sin(f / 8.0), side=6 * sw, head=(-6 - 38 * tilt, 10 * math.sin(f / 11.0) * (1 - tilt)))
    LB.arm_dir("L", f, Bm, V(0.35, 0.1 * sw, -0.9), 0.95)
    if f >= f_fb0 - 6:
        # right hand brings the bottle to the mouth
        mouth = LB.head + V(0, -0.11, 0.02)
        rest_p = LB.sh["R"] + V(-0.22, -0.2, -0.45)
        up_p = mouth + V(-0.03, -0.02, -0.04)
        W = rest_p.lerp(up_p, tilt)
        d = V(0.1, -0.35, 1.0).lerp(V(0.3, -0.2, 1.0), tilt).normalized()
        LB.hand("R", f, Bm, W, d, V(1, 0, 0))
    else:
        LB.arm_dir("R", f, Bm, V(-0.35, -0.1 * sw, -0.9), 0.95)
    if f % 9 == 0:
        for s in "LR":
            sx = 1 if s == "L" else -1
            foot_w(s, f, (STAND_XY.x - 0.05, STAND_XY.y + sx * 0.16), 90 + sx * 8)
sc["swig"] = str((f_fb0, SWIG_UP, SWIG_HOLD, SWIG_DOWN, f_fb1))

# --- beat 10 (23.5-26.5): x-ray, loose limbs swaying like rope (arms dangle and swing, one leg shaken out)
f_x0, f_x1 = f_fb1, F(26.5)
for f in list(range(f_x0 + 3, f_x1 + 1, 2)) + [f_x1]:
    t = (f - f_x0) / FPS
    sw = math.sin(t * 2.2)
    Bm = LB.B(V(STAND_XY.x + 0.04 * sw, STAND_XY.y, RH.z - 0.04 - 0.015 * abs(math.sin(t * 2.2))), Rbody(yaw=90 + 10 * math.sin(t * 1.1), pitch=4, side=9 * sw))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=10 + 4 * math.sin(t * 1.7), twist=14 * math.sin(t * 2.2 - 0.6), side=9 * sw, head=(12 + 8 * math.sin(t * 2.2 - 1.2), 16 * math.sin(t * 1.1 - 0.8)))
    # pendulum arms lagging the body sway (loose)
    LB.arm_dir("L", f, Bm, V(0.25 + 0.35 * math.sin(t * 2.2 - 1.4), 0.45 * math.sin(t * 2.2 - 1.9), -1.0), 0.95)
    LB.arm_dir("R", f, Bm, V(-0.25 + 0.35 * math.sin(t * 2.2 - 1.4), -0.45 * math.sin(t * 2.2 - 2.1), -1.0), 0.95)
    foot_w("L", f, (STAND_XY.x - 0.05, STAND_XY.y + 0.16), 98)
    if t > 1.3:
        sh = min(1.0, (t - 1.3) / 0.3) * (1 - max(0.0, (t - 2.7) / 0.3))
        LB.leg_dir("R", f, Bm, V(-0.15 + 0.25 * math.sin(t * 9) * sh, -0.45 * sh + 0.15 * math.sin(t * 9 + 1) * sh, -1.0), 0.97 - 0.06 * sh, toe_pitch=20 * math.sin(t * 9 - 1) * sh)
    else:
        foot_w("R", f, (STAND_XY.x - 0.05, STAND_XY.y - 0.16), 82)
# keep the planted (left) foot truly planted: world key overrides at the end of the segment
for f in (f_x0 + 3, f_x1):
    foot_w("L", f, (STAND_XY.x - 0.05, STAND_XY.y + 0.16), 98)

# --- beat 11 (26.5-31.0): slow-motion x-ray replay. Lies with head on a ghost rail, ghost train pushes, body flows with it
f_r0, f_r1 = f_x1, F(31.0) - 4          # beat 12 starts 4 frames early so the 31 s still is the real scene
R_HEAD = V(STAND_XY.x - 1.25, STOP_Y + 1.5, RAIL_H + 0.095)    # ghost rail runs along Y at x = R_HEAD.x - 0.02
sc["replay_head"] = str(tuple(R_HEAD))
R_IMP = f_r0 + 40; SLOW = 5.0
R_LIEX = R_HEAD.x + (LIE_X - HEAD_REST.x)
for f in list(range(f_r0 + 2, f_r1 + 1, 2)) + [f_r1]:
    if f <= R_IMP:
        Bm = LB.B(V(R_LIEX, R_HEAD.y, 0.12), Rbody(yaw=90, pitch=-90))
        LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
        LAD.key_spine(f, flex=6, head=(20, 25))
        for s in "LR":
            sx = 1 if s == "L" else -1
            LB.foot(s, f, Bm, V(sx * 0.24, LB.an[s].y + 0.02, LB.an[s].z), Matrix.Rotation(R_(sx * 25), 3, 'Z'))
            LB.arm_dir(s, f, Bm, V(sx * 0.85, 0.08, -0.5), 0.95, palm=V(0, 0.3, -1))
        continue
    # replay the real spin at 1/SLOW speed, relative to the ghost train front
    fr = T_IMP + (f - R_IMP) / SLOW
    p, R3 = drag_full(int(fr))
    p = p + (V(R_HEAD.x, R_HEAD.y, 0) - V(HEAD_REST.x, HEAD_Y, 0))
    p.x += 0.0
    Bm = LB.B(p, R3)
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=12 * math.sin(fr / 5.0), twist=16 * math.sin(fr / 7.0), side=14 * math.sin(fr / 6.0 + 1), head=(18 * math.sin(fr / 4.0 + 2), 20 * math.sin(fr / 5.0)))
    lag = Bm_at(int(fr) - 4)
    lagW = lag.copy(); lagW.translation = Bm.translation
    for s, key in (("L", "aL"), ("R", "aR")):
        d_l = Bm.to_3x3().inverted() @ (lag.to_3x3() @ limb_dir(key, int(fr)))
        LB.arm_dir(s, f, Bm, d_l, 0.93)
    for s, key in (("L", "lL"), ("R", "lR")):
        d_l = Bm.to_3x3().inverted() @ (lag.to_3x3() @ limb_dir(key, int(fr)))
        LB.leg_dir(s, f, Bm, d_l, 0.97)
sc["replay"] = str((f_r0, R_IMP, SLOW, f_r1))

# --- beat 12 (31.0-34.5): walks off along the platform, looks at his palm, dazed grin
f_w0 = f_r1 + 1; f_w1 = F(33.0); f_palm0, f_palm1 = f_w1 + 4, F(34.5)
WK_P = catmull([(f_w0, V(STAND_XY.x - 0.05, STAND_XY.y - 0.2, 0)), (f_w0 + 40, V(STAND_XY.x + 0.05, STAND_XY.y - 1.05, 0)),
                (f_w0 + 80, V(STAND_XY.x - 0.05, STAND_XY.y - 1.9, 0)), (f_w1, V(STAND_XY.x, STAND_XY.y - 2.55, 0))])
WK_Y = catmull([(f_w0, 4.0), (f_w0 + 40, -6.0), (f_w0 + 80, 6.0), (f_w1, 0.0)])
def lad_side2(f, cyc): return 7 * math.sin(2 * math.pi * cyc) + 4 * math.sin(f / 10.0)
def lad_spine2(f, cyc):
    LAD.key_spine(f, flex=8, twist=-8 * math.sin(2 * math.pi * cyc), side=6 * math.sin(f / 14.0), head=(-4 + 5 * math.sin(f / 9.0), 8 * math.sin(f / 15.0)))
def lad_arms2(f, cyc, p, yw, sd):
    Bm = LB.B(p, Rbody(yaw=yw, pitch=4, side=sd))
    LB.arm_dir("L", f, Bm, V(0.2, -0.35 * math.sin(2 * math.pi * cyc), -1.0), 0.95)
    LB.arm_dir("R", f, Bm, V(-0.2, 0.35 * math.sin(2 * math.pi * cyc), -1.0), 0.95)
gait(LAD, WK_P, WK_Y, f_w0, f_w1, stride=0.55, duty=0.62, lift=0.09, bob=0.03, crouch=0.04, lean=6, side_fn=lad_side2,
     spine_fn=lad_spine2, arms_fn=lad_arms2)
END_P = WK_P(f_w1); END_YAW = 0.0
for f in list(range(f_palm0, f_palm1 + 1, 3)) + [f_palm1]:
    u = smooth((f - f_palm0) / 25.0); g = smooth((f - (f_palm0 + 38)) / 22.0)
    Bm = LB.B(V(END_P.x, END_P.y, RH.z - 0.035), Rbody(yaw=END_YAW + 6 * math.sin(f / 15.0), pitch=3, side=4 * math.sin(f / 11.0)))
    LAD.r.key_world("root", f, Bm @ LAD.r.rest("root"))
    LAD.key_spine(f, flex=10 - 4 * g, twist=-6 * u, head=(30 * u * (1 - g) - 6 * g, -12 * u * (1 - g) + 18 * g))
    # left palm turned up in front of his face
    W = (LB.sh["L"] + V(0.18, -0.1, -0.55)).lerp(LB.head + V(0.12, -0.38, -0.32), u * (1 - 0.35 * g))
    LB.hand("L", f, Bm, W, V(0.15, -0.85, 0.35).normalized(), V(0, 0.5, 0.85).normalized())
    LB.arm_dir("R", f, Bm, V(-0.2, 0.05, -1.0), 0.95)
    for s in "LR":
        if f in (f_palm0, f_palm1):
            sx = 1 if s == "L" else -1
            foot_w(s, f, LAD.foot_xy(s, END_P, END_YAW), END_YAW)
sc["palm"] = str((f_palm0, f_palm1))

# ==================================================================== BYSTANDERS
BYS = {"WitA": WA, "WitB": WB, "Worker": WK}
BODY = {k: Body(h) for k, h in BYS.items()}
LAD_REST_XY = V(REST_P.x, REST_P.y, 0)
def face(frm, to):
    d = (to - frm).to_2d(); return math.degrees(math.atan2(d.x, -d.y))
def alerp(a, b, u):
    d = ((b - a + 180) % 360) - 180; return a + d * u
START = {"WitA": (V(5.2, -50.5, 0), -70.0), "WitB": (V(6.0, -52.0, 0), -100.0), "Worker": (V(4.4, -48.5, 0), -95.0)}
GOAL = {}
for k, g_ in (("WitA", V(3.75, STOP_Y + 2.4, 0)), ("WitB", V(4.55, STOP_Y + 0.9, 0)), ("Worker", V(3.15, STOP_Y - 1.9, 0))):
    GOAL[k] = (g_, face(g_, LAD_REST_XY))
BACK = {k: (GOAL[k][0] + (GOAL[k][0] - LAD_REST_XY).normalized() * 0.55, GOAL[k][1]) for k in GOAL}
f_run0 = {"WitA": F(14.6), "WitB": F(14.8), "Worker": F(14.5)}
f_run1 = {"WitA": F(17.2), "WitB": F(17.5), "Worker": F(17.0)}
f_back0, f_back1 = F(20.3), F(20.8)
def idle(name, f0, f1, pos, yaw, react=None):
    H = BYS[name]; Bd = BODY[name]
    for f in list(range(f0, f1 + 1, 6)) + [f1]:
        rk = 0.0
        if react and f >= react: rk = math.exp(-(f - react) / 40.0)
        look = 0.0
        Bm, p = stand_B(Bd, pos, yaw + 8 * math.sin(f / 50.0 + len(name)), side=2 * math.sin(f / 40.0), flex=-8 * rk)
        H.r.key_world("root", f, Bm @ H.r.rest("root"))
        H.key_spine(f, flex=4 - 12 * rk, twist=6 * math.sin(f / 60.0), head=(-4 * rk, 40 * rk + 15 * math.sin(f / 70.0 + 1)))
        hang_arms(Bd, f, Bm, swing=(0.05 * math.sin(f / 30.0) + 0.4 * rk, 0.05 * math.sin(f / 33.0) + 0.4 * rk))
        if f in (f0, f1):
            for s in "LR":
                xy = H.foot_xy(s, pos, yaw)
                Bd.foot_world(s, f, V(xy.x, xy.y, ground_z(xy.x, xy.y) + Bd.an[s].z), yaw)
for name in BYS:
    H = BYS[name]; Bd = BODY[name]
    p0, y0 = START[name]; p1, y1 = GOAL[name]
    idle(name, 1, f_run0[name] - 1, p0, y0, react=T_IMP + (6 if name == "Worker" else 12))
    # run: along the platform, down the ramp, along the ballast to the train
    lane = {"Worker": -0.9, "WitA": 0.5, "WitB": 1.3}[name]
    mid = V((RAMP["x0"] + RAMP["x1"]) / 2 - 0.6 + lane, RAMP["y0"] + 1.0, 0); mid2 = V(RAMP["x0"] + 0.4 + lane * 0.5, RAMP["y1"] + 0.5, 0)
    path = catmull([(f_run0[name], p0), (f_run0[name] + 35, mid), (f_run0[name] + 70, mid2), (f_run1[name], p1)])
    def yawf(f, path=path, f0=f_run0[name], f1=f_run1[name], y0=y0, y1=y1):
        a, b = path(max(f0, f - 3)), path(min(f1, f + 3))
        d = (b - a).to_2d()
        hy = math.degrees(math.atan2(d.x, -d.y)) if d.length > 1e-3 else y1
        if f < f0 + 14: hy = alerp(y0, hy, smooth((f - f0) / 14))
        if f > f1 - 15: hy = alerp(hy, y1, smooth((f - (f1 - 15)) / 15))
        return hy
    # unwrap the yaw so it never spins the long way round
    def run_arms(f, cyc, p, yw, sd, Bd=Bd):
        Bm = Bd.B(p, Rbody(yaw=yw, pitch=14, side=sd))
        s_ = math.sin(2 * math.pi * cyc)
        ow = 0.8 if Bd is BODY.get("WitB") else 0.55          # her jacket flares: swing wider
        Bd.arm_dir("L", f, Bm, V(ow, -0.9 * s_ - 0.15, -0.6), 0.85, pole_local=Bd.el["L"] + V(0.35, 0.6, -0.1))
        Bd.arm_dir("R", f, Bm, V(-ow, 0.9 * s_ - 0.15, -0.6), 0.85, pole_local=Bd.el["R"] + V(-0.35, 0.6, -0.1))
    gait(H, path, yawf, f_run0[name], f_run1[name], stride=1.45, duty=0.42, lift=0.16, bob=0.05, crouch=0.08, lean=16, arms_fn=run_arms)
    # react pose at the goal: WitA hands to mouth, WitB hands on head, Worker crouches and peers under the train
    for f in list(range(f_run1[name] + 2, f_back0 + 1, 4)) + [f_back0]:
        u = smooth((f - f_run1[name]) / 14.0)
        if name == "Worker":
            Bm, p = stand_B(Bd, p1, y1 + 5 * math.sin(f / 20.0), z_off=-0.42 * u, flex=30 * u)
            H.r.key_world("root", f, Bm @ H.r.rest("root"))
            H.key_spine(f, flex=30 * u, head=(-25 * u, 10 * math.sin(f / 25.0)))
            Bd.arm_dir("L", f, Bm, V(0.65, -0.55, -0.35), 0.92)        # steadying arm out to the side
            Bd.arm_dir("R", f, Bm, V(-0.5, -0.8, -0.1), 0.9)          # one arm out, steadying, reaching toward him
        else:
            Bm, p = stand_B(Bd, p1, y1 + 4 * math.sin(f / 23.0), flex=-6 * u)
            H.r.key_world("root", f, Bm @ H.r.rest("root"))
            H.key_spine(f, flex=10 * u, twist=4 * math.sin(f / 17.0), head=(10 * u, 6 * math.sin(f / 19.0)))
            mouth = Bd.head + V(0, -0.11, 0.0)
            for s in "LR":
                sx = 1 if s == "L" else -1
                if name == "WitA":
                    if s == "L":      # one hand over the mouth
                        Wt = mouth + V(0.05, -0.13, -0.15)
                        Bd.hand(s, f, Bm, (Bd.sh[s] + V(sx * 0.28, -0.25, -0.38)).lerp(Wt, u), V(-0.3, -0.15, 1).normalized(), V(0, 1, 0))
                    else:             # the other held just off her chest
                        Wt = Bd.sh["R"] + V(0.1, -0.24, -0.2)
                        Bd.hand(s, f, Bm, (Bd.sh[s] + V(sx * 0.28, -0.25, -0.38)).lerp(Wt, u), V(0.6, -0.2, 0.75).normalized(), V(0, 1, 0))
                else:
                    Wt = Bd.head + V(sx * 0.19, 0.02, 0.02)
                    Bd.hand(s, f, Bm, (Bd.sh[s] + V(sx * 0.28, -0.25, -0.38)).lerp(Wt, u), V(-sx * 0.25, 0.1, 1.0).normalized(), V(-sx, 0, 0))
        if f in (f_run1[name] + 2, f_back0):
            for s in "LR":
                xy = H.foot_xy(s, p1, y1)
                Bd.foot_world(s, f, V(xy.x, xy.y, ground_z(xy.x, xy.y) + Bd.an[s].z), y1)
    # stagger back when he stands up (beat 8), then stay and stare (beat 12)
    pb_, yb = BACK[name]
    for f in (f_back1, F(21.0)):
        Bm, p = stand_B(Bd, pb_, yb, flex=-10)
        H.r.key_world("root", f, Bm @ H.r.rest("root"))
        H.key_spine(f, flex=-6, head=(-10, 0))
        hang_arms(Bd, f, Bm, swing=(0.6, 0.5), out=(0.4, 0.4), bend=(0.6, 0.6))
    for s in "LR":
        xy = H.foot_xy(s, pb_, yb)
        Bd.foot_world(s, f_back0 + 6, V(xy.x, xy.y, ground_z(xy.x, xy.y) + Bd.an[s].z + 0.1), yb)
        Bd.foot_world(s, f_back1, V(xy.x, xy.y, ground_z(xy.x, xy.y) + Bd.an[s].z), yb)
    for f in list(range(F(31.0), sc.frame_end + 1, 5)) + [sc.frame_end]:
        tgt = WK_P(min(f, f_w1)); here = pb_
        look = face(here, tgt)
        Bm, p = stand_B(Bd, pb_, yb + 0.4 * (((look - yb) + 180) % 360 - 180))
        H.r.key_world("root", f, Bm @ H.r.rest("root"))
        H.key_spine(f, flex=4, head=(0, 0.5 * (((look - yb) + 180) % 360 - 180)))
        if name == "Worker" and f > F(32.5):
            Bd.hand("R", f, Bm, Bd.head + V(-0.17, 0.03, 0.2), V(0.6, 0.1, 0.6).normalized(), V(1, 0, 0))     # scratches his hard hat
            Bd.arm_dir("L", f, Bm, V(0.15, 0.0, -1), 0.95)
        elif name == "WitA":
            Bd.hand("L", f, Bm, Bd.head + V(0.07, -0.22, -0.15), V(-0.25, -0.15, 1).normalized(), V(0, 1, 0))
            Bd.arm_dir("R", f, Bm, V(-0.42, -0.1, -1), 0.95)
        else:
            hang_arms(Bd, f, Bm)
    for s in "LR":
        xy = H.foot_xy(s, pb_, yb)
        for f in (F(31.0), sc.frame_end):
            Bd.foot_world(s, f, V(xy.x, xy.y, ground_z(xy.x, xy.y) + Bd.an[s].z), yb)

sc["T_IMP"] = T_IMP; sc["f_rest"] = f_rest; sc["f_stir"] = f_stir; sc["stand_xy"] = str(tuple(STAND_XY))
sc["walk_end"] = str(tuple(END_P)); sc["lie_x"] = LIE_X; sc["head_rest"] = str(tuple(HEAD_REST))
print("ANIM_DONE")
exec(open(os.path.join(HERE, "03b_fx_camera.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
