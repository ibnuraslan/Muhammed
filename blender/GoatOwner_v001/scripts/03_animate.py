"""GoatOwner animation: owner, goat, passer-by, officials, rescuer, props, dust, world light, camera.
blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
random.seed(7)
PX0, PX1, PY0, PY1, PZ = list(sc["porch"])
STEPS = [list(s) for s in sc["steps"]]

# ------------------------------------------------------------------ truck bed height -> ramp
truck = bpy.data.objects["truck"]
dg = bpy.context.evaluated_depsgraph_get()
def ray_down(ob, x, y):
    mi = ob.matrix_world.inverted()
    o_ = mi @ Vector((x, y, 6)); d_ = (mi.to_3x3() @ Vector((0, 0, -1))).normalized()
    hit, loc, nrm, idx = ob.evaluated_get(dg).ray_cast(o_, d_)
    return (ob.matrix_world @ loc).z if hit else None
BED = 1.03
tb = [y / 100 for y in range(1000, 1400) if 0.95 < (ray_down(truck, -1.5, y / 100) or 0) < 1.12]
BED_Y0 = min(tb) if tb else 11.0
RAMP_L = 2.2
ramp = bpy.data.objects["Ramp"]
ang = math.asin(min(0.9, BED / RAMP_L)); run = RAMP_L * math.cos(ang)
ramp.location = (-1.5, BED_Y0 - run / 2, BED / 2); ramp.rotation_euler = (-ang, 0, 0)
RAMP = (BED_Y0 - run, BED_Y0)
print("TRUCK bed", round(BED, 3), "starts y", BED_Y0, "ramp", RAMP)

def ground_z(x, y):
    if PX0 <= x <= PX1 and PY0 <= y <= PY1: return PZ
    for xa, xb, zt in STEPS:
        if xa <= x <= xb and 5.25 <= y <= 6.75: return zt
    if -2.0 <= x <= -1.0 and RAMP[0] <= y <= RAMP[1]: return BED * (y - RAMP[0]) / (RAMP[1] - RAMP[0])
    if -2.4 <= x <= -0.6 and RAMP[1] < y < RAMP[1] + 3.5: return BED
    return 0.0

def yaw_to(a, b):
    d = Vector(b).to_2d() - Vector(a).to_2d(); return math.degrees(math.atan2(d.x, -d.y))
def V(*a): return Vector(a)
def lerp(a, b, t): return a + (b - a) * t

# ================================================================= humans
class H:
    def __init__(self, name):
        self.o = bpy.data.objects[name]
        self.R = make_human_ctrl(self.o)
        self.h = Human(self.R)
        B = self.R.BN
        self.RH = self.h.root_head.copy()
        self.SH = {s: B["upperarm01." + s].head_local.copy() for s in "LR"}
        self.meshes = [c for c in self.o.children if c.type == 'MESH']
    def M(self, pos, yaw, lean=0.0, roll=0.0):
        Rw = Matrix.Rotation(R_(yaw), 4, 'Z') @ Matrix.Rotation(R_(lean), 4, 'X') @ Matrix.Rotation(R_(roll), 4, 'Y')
        return Matrix.Translation(pos) @ Rw @ Matrix.Translation(-self.RH)
    def hand_local(self, s, f, M, W, d, n):
        sx = 1 if s == "L" else -1
        R3 = M.to_3x3()
        pole = M @ (self.SH[s] + Vector((0.35 * sx, 0.45, -0.25)))
        self.h.key_hand(s, f, M @ W, R3 @ d, R3 @ n, pole)
    def arm(self, s, f, M, fwd=10, out=8, L=0.5):
        sx = 1 if s == "L" else -1
        Rr = Matrix.Rotation(R_(-fwd), 3, 'X') @ Matrix.Rotation(R_(-sx * out), 3, 'Y')     # out > 0 = away from the body
        W = self.SH[s] + Vector((sx * 0.04, -0.02, 0)) + Rr @ Vector((0, 0, -L))
        d = Rr @ Vector((sx * 0.05, -0.15, -1.0)); n = Rr @ Vector((-sx * 0.9, 0.35, 0.0))
        self.hand_local(s, f, M, W, d, n)
    def fingers(self, s, f, curl=25, thumb=18):
        sign = 1 if s == "R" else -1
        wr = self.R.BN["wrist." + s].head_local
        dd = (self.R.BN["finger3-1." + s].head_local - wr).normalized()
        aa = (self.R.BN["finger2-1." + s].head_local - self.R.BN["finger5-1." + s].head_local).normalized()
        for k in range(2, 6):
            for j, w in ((1, 0.8), (2, 1.1), (3, 0.8)):
                b = "finger%d-%d.%s" % (k, j, s)
                self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(curl * w * sign), 3, aa)))
        for j, fl in ((1, thumb * 0.4), (2, thumb * 0.8), (3, thumb)):
            b = "finger1-%d.%s" % (j, s)
            self.R.key_q(b, f, self.R.local_q(b, Matrix.Rotation(R_(fl * sign), 3, aa) @ Matrix.Rotation(R_(22 * sign), 3, dd)))
    def face(self, f, jaw=0.0, brow=0.0, lid=0.0, smile=0.0):
        """jaw open (deg); brow >0 raised, <0 furrowed/angry; lid >0 wide, <0 narrowed (-8 = closed); smile >0 corners up, <0 grimace"""
        PB = self.R.PB
        self.R.key_rot("jaw", f, [("X", jaw * 0.6)])
        def mv(b, v):
            if b not in PB: return
            pb = PB[b]; pb.location = self.R.rest(b).to_3x3().inverted() @ v; pb.keyframe_insert("location", frame=f, group=b)
        for s in "LR":
            sx = 1 if s == "L" else -1
            if brow >= 0:
                mv("oculi01." + s, Vector((0, 0, 0.0016 * brow))); mv("oculi02." + s, Vector((0, 0, 0.0012 * brow)))
            else:   # angry / pained: inner brow down and in, outer slightly up
                mv("oculi01." + s, Vector((-sx * 0.0008 * -brow, -0.0004 * -brow, 0.0014 * brow))); mv("oculi02." + s, Vector((0, 0, -0.0003 * brow)))
            up = max(-35.0, min(14.0, -lid * 4.0)); lo = max(-20.0, min(20.0, lid * 2.5))
            self.R.key_rot("orbicularis03." + s, f, [("X", up)]); self.R.key_rot("orbicularis04." + s, f, [("X", lo)])
            if smile >= 0: mv("risorius03." + s, Vector((sx * 0.0006 * smile, 0.0004 * smile, 0.0008 * smile)))
            else: mv("risorius03." + s, Vector((sx * 0.0008 * -smile, 0.0, 0.0004 * smile)))
    def stand(self, f, pos, yaw, lean=0.0, roll=0.0, spine=(0, 0, 0), head=(0, 0), feet=None, crouch=0.0, stance=1.0):
        """pos: ground xy (z = ground); feet planted under the body unless given"""
        gz = ground_z(pos.x, pos.y)
        P = Vector((pos.x, pos.y, gz + self.RH.z - crouch))
        self.h.key_root(f, P, yaw=yaw, flex=lean, side=roll)
        self.h.key_spine(f, flex=spine[0], side=spine[1], twist=spine[2], head=head)
        feet = feet or {}
        for s in "LR":
            if s in feet:
                xy, fy = feet[s][:2]; lift = feet[s][2] if len(feet[s]) > 2 else 0.0; pt = feet[s][3] if len(feet[s]) > 3 else 0.0
            else:
                sx = 1 if s == "L" else -1
                o = Matrix.Rotation(R_(yaw), 3, 'Z') @ Vector((self.h.ankle[s].x * 0.9 * stance, 0.02, 0))
                xy, fy, lift, pt = Vector((pos.x + o.x, pos.y + o.y)), yaw + sx * 6, 0.0, 0.0
            self.h.key_foot(s, f, Vector(xy), fy, lift, pt)
        return self.M(P, yaw, lean, roll)
    def vis(self, f, on):
        for o in [self.o] + self.meshes:
            o.hide_render = not on; o.hide_viewport = not on
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
    def key_foot_world(self, s, f, W, Rm):
        a = self.h.ankle[s]
        M = Matrix.Translation(W) @ Rm.to_4x4() @ Matrix.Translation(-a) @ self.R.rest("IK_foot." + s)
        self.R.key_world("IK_foot." + s, f, M)

OW, PS, OA, OB_, RS = H("Owner"), H("Passer"), H("OffA"), H("OffB"), H("Rescuer")
# ================================================================= HAND JOINT LIMITS (client rule, Nov 11 23:00): local-space Limit Rotation
def limit(pb, x, y, z):
    c = pb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.name = "JointLimit"
    c.use_limit_x = c.use_limit_y = c.use_limit_z = True
    c.min_x, c.max_x = R_(x[0]), R_(x[1]); c.min_y, c.max_y = R_(y[0]), R_(y[1]); c.min_z, c.max_z = R_(z[0]), R_(z[1])
    for pb_ in (pb,): pb_.rotation_mode = 'QUATERNION'
N_LIM = 0
for h_ in (OW, PS, OA, OB_, RS):
    for s in "LR":
        # Finger/thumb Limit Rotation was tried: its local-Euler clamp flattened the keyed MPFB curls (open, splayed hands),
        # so fingers are instead only ever keyed through H.fingers(), which bends forward 0-75 deg about the knuckle axis (never backward).
        limit(h_.R.PB["wrist." + s], (-60, 60), (-40, 40), (-25, 25)); N_LIM += 1
print("LIMITS", N_LIM)

for h_ in (OW, PS, OA, OB_, RS):
    for s in "LR": h_.fingers(s, 1, 18, 16)
    h_.face(1)

# hand contact presets in rest-body coordinates (sx mirrors)
def HP(name, s):
    sx = 1 if s == "L" else -1
    return {"belly": (Vector((sx * 0.14, -0.42, 1.06)), Vector((-sx * 0.7, -0.15, -0.6)), Vector((0, 1, 0))),
            "belly2": (Vector((sx * 0.15, -0.42, 1.2)), Vector((-sx * 0.8, -0.1, -0.4)), Vector((0, 1, 0))),
            "overhead": (Vector((sx * 0.3, -0.16, 1.96)), Vector((0, -0.25, 1.0)), Vector((-sx, 0, 0))),
            "raised": (Vector((sx * 0.32, -0.3, 1.76)), Vector((0, -0.6, 0.8)), Vector((-sx, 0, 0))),
            "front": (Vector((sx * 0.3, -0.45, 1.25)), Vector((0, -1, -0.2)), Vector((-sx, 0, 0))),
            "low": (Vector((sx * 0.3, -0.45, 1.0)), Vector((0, -0.9, -0.5)), Vector((-sx, 0, 0))),
            }[name]

def clutch(f, s, kind):
    ev(f)
    D = OW.o.matrix_world @ OW.R.delta("spine02"); R3 = D.to_3x3()
    W, d, n = HP(kind, s); sx = 1 if s == "L" else -1
    pole = D @ (OW.SH[s] + Vector((0.35 * sx, 0.45, -0.25)))
    OW.h.key_hand(s, f, D @ W, R3 @ d, R3 @ n, pole)


# ================================================================= goat
G = Rig(bpy.data.objects["Goat_rig"])
for pb in G.o.pose.bones: pb.rotation_mode = 'QUATERNION'
def gneck(f, n1=0.0, n2=0.0, hd=0.0, turn=0.0, tail=0.0):
    G.key_rot("neck1", f, [("X", n1), ("Z", turn * 0.5)]); G.key_rot("neck2", f, [("X", n2), ("Z", turn * 0.3)])
    G.key_rot("head", f, [("X", hd), ("Z", turn * 0.2)])
    G.key_rot("tail1", f, [("X", -tail)]); G.key_rot("tail2", f, [("X", -tail * 0.6)])
def gpath(keys):
    fx = catmull([(f, Vector((p[0], p[1], 0))) for f, p in keys]); return lambda f: fx(f)
def ghold(f, p, h_deg, dz=0.0, pitch=0.0, roll=0.0):
    quad_hold(G, f, Vector(p), R_(h_deg), torso_dz=dz, extra_rot=Matrix.Rotation(R_(-pitch), 3, 'X') @ Matrix.Rotation(R_(roll), 3, 'Y'))

# ------------------------------------------------------------------ positions
POST = Vector((-1.2, 2.0))
GA = Vector((-0.35, 1.75))             # goat by the post
OA_ = Vector((0.75, 1.3))             # owner standing over it
B = {1: 1, 2: 187, 3: 463, 4: 631, 5: 817, 6: 1129, 7: 1183, 8: 1417, 9: 1519, 10: 1735, 11: 1909}

# ================================================================= OWNER
yaw_g = yaw_to(OA_, GA)
def owner_menace(f, raise_amt, shake=0.0):
    M = OW.stand(f, OA_, yaw_g + shake * 3, lean=-4 * raise_amt, spine=(-6 * raise_amt + 4, 0, -10 * raise_amt), head=(10, 0),
                 feet={"L": (OA_ + Vector((0.12, -0.08)), yaw_g - 10), "R": (OA_ + Vector((0.05, 0.28)), yaw_g + 20)})
    W, d, n = HP("overhead" if raise_amt > 0.6 else "front", "R")
    if raise_amt <= 0.6:
        W0, d0, n0 = HP("low", "R"); W = W0.lerp(W, raise_amt / 0.6); d = d0.lerp(d, raise_amt / 0.6)
    OW.hand_local("R", f, M, W + Vector((0, 0, shake * 0.03)), d, n)
    OW.arm("L", f, M, fwd=6, out=8, L=0.5)
    OW.fingers("R", f, 70, 40); OW.fingers("L", f, 35, 20)
    OW.face(f, jaw=6 + 6 * raise_amt, brow=-3, lid=-1.5, smile=-1.5)
for f, r, sh in ((1, 0.3, 0), (20, 0.5, 0), (42, 1.0, 1), (70, 1.0, -1), (96, 1.0, 1), (124, 1.0, 0.5), (150, 1.0, -1), (175, 0.8, 0)):
    owner_menace(f, r, sh)
OW.arm("R", 183, OW.M(Vector((OA_.x, OA_.y, OW.RH.z)), yaw_g), fwd=35, out=28, L=0.5)   # lowers the stick out to the side, clear of the body
# beat 2: he turns and walks to the porch steps, stick hanging; beat 3: offscreen in the house
p_ow = catmull([(186, V(OA_.x, OA_.y, 0)), (260, V(2.2, 3.0, 0)), (340, V(3.6, 5.2, 0)), (380, V(4.2, 6.0, 0)), (420, V(5.6, 6.0, 0)), (460, V(6.6, 6.4, 0))])
OW.h.walk(p_ow, lambda f: yaw_to(p_ow(f - 3), p_ow(f + 3)) if f < 455 else 90, 186, 460, stride=0.72, lean=4)
for f in range(186, 461, 12):
    M = OW.M(Vector((p_ow(f).x, p_ow(f).y, ground_z(p_ow(f).x, p_ow(f).y) + OW.RH.z)), yaw_to(p_ow(f - 3), p_ow(f + 3)))
    sw = 18 * math.sin((f - 186) / 22.0)
    OW.arm("R", f, M, fwd=12 + sw, out=10, L=0.5); OW.arm("L", f, M, fwd=12 - sw, out=8, L=0.5)
OW.vis(1, True); OW.vis(461, False)     # inside the house during the time-lapse (the pop-in visits read as snaps)
# beat 4: comes back out, down the steps toward the goat with the stick
OW.vis(600, True)
p_ow2 = catmull([(600, V(6.4, 6.2, 0)), (640, V(5.4, 6.0, 0)), (690, V(4.0, 6.0, 0)), (760, V(2.6, 3.6, 0)), (812, V(1.2, 1.6, 0)), (830, V(1.05, 1.4, 0))])
OW.h.walk(p_ow2, lambda f: yaw_to(p_ow2(f - 3), p_ow2(f + 3)), 600, 830, stride=0.7, lean=6)
for f in range(600, 831, 12):
    M = OW.M(Vector((p_ow2(f).x, p_ow2(f).y, ground_z(p_ow2(f).x, p_ow2(f).y) + OW.RH.z)), yaw_to(p_ow2(f - 3), p_ow2(f + 3)))
    sw = 12 * math.sin((f - 600) / 20.0)
    W, d, n = HP("front", "R") if f > 760 else HP("low", "R")
    OW.hand_local("R", f, M, W, d, n); OW.arm("L", f, M, fwd=10 - sw, out=8, L=0.5)
    OW.fingers("R", f, 70, 40); OW.face(f, jaw=10, brow=-4, lid=-2, smile=-2)
# beat 5: slow motion impact (contact at 960), doubles over, pushed back
IMP1 = 960
OC = Vector((1.05, 1.4)); yaw_c = yaw_to(OC, V(-0.4, 1.8))
def ow_hit(f, pos, lean, spine, head, jaw, hands="belly", brow=4, lid=3, crouch=0.0, roll=0.0, feet=None):
    M = OW.stand(f, pos, yaw_c, lean=lean, roll=roll, spine=(spine, 0, 0), head=(head, 0), crouch=crouch, feet=feet)
    for s in "LR":
        if hands == "belly":
            clutch(f, s, "belly" if s == "L" else "belly2"); OW.fingers(s, f, 30, 20)
        else:
            OW.arm(s, f, M, fwd=hands[0], out=hands[1], L=0.48); OW.fingers(s, f, 10, 8)      # relaxed, no claws
    OW.face(f, jaw=jaw, brow=brow, lid=lid, smile=-3)
ow_hit(850, OC, -6, -4, 6, 8, hands=(15, 10), brow=-4, lid=-1)
OW.hand_local("R", 850, OW.M(Vector((OC.x, OC.y, OW.RH.z)), yaw_c, -6), *HP("raised", "R"))
OW.hand_local("R", 930, OW.M(Vector((OC.x, OC.y, OW.RH.z)), yaw_c, -8), *HP("overhead", "R"))
OW.face(930, jaw=18, brow=6, lid=4, smile=-3)
FEET_C = {"L": (OC + Vector((0.1, -0.12)), yaw_c), "R": (OC + Vector((0.08, 0.2)), yaw_c + 15)}
ow_hit(955, OC, 16, 14, -6, 20, hands=(35, 12), feet=FEET_C, crouch=0.1)
OW.hand_local("R", 955, OW.M(Vector((OC.x, OC.y, OW.RH.z - 0.1)), yaw_c, 16), *HP("raised", "R"))
OC2 = OC + Vector((0.25, -0.1))
ow_hit(985, OC2, 28, 38, 22, 34, hands=(40, 14), crouch=0.12, feet={"L": (OC + Vector((0.32, -0.12)), yaw_c), "R": (OC + Vector((0.22, 0.2)), yaw_c + 15, 0.05)})
ow_hit(1040, OC2 + Vector((0.12, -0.04)), 34, 44, 26, 30, hands=(75, 22), crouch=0.16, feet={"L": (OC + Vector((0.32, -0.12)), yaw_c), "R": (OC + Vector((0.42, 0.18)), yaw_c + 15)})
ow_hit(1100, OC2 + Vector((0.15, -0.05)), 24, 30, 14, 24, hands=(65, 22), crouch=0.10, feet={"L": (OC + Vector((0.32, -0.12)), yaw_c), "R": (OC + Vector((0.42, 0.18)), yaw_c + 15)})
# beat 6: second hit (fast) at 1145
OC3 = OC2 + Vector((0.55, -0.1))
ow_hit(1138, OC2 + Vector((0.15, -0.05)), 14, 18, 6, 20, hands=(50, 25), crouch=0.06, feet={"L": (OC + Vector((0.32, -0.12)), yaw_c), "R": (OC + Vector((0.42, 0.18)), yaw_c + 15)})
ow_hit(1152, OC3, 36, 46, 28, 36, hands=(40, 14), crouch=0.18, roll=-6, feet={"L": (OC3 + Vector((0.05, -0.15)), yaw_c), "R": (OC3 + Vector((0.1, 0.2)), yaw_c + 20)})
ow_hit(1180, OC3 + Vector((0.05, 0.05)), 26, 34, 16, 26, hands=(40, 30), crouch=0.10, feet={"L": (OC3 + Vector((0.05, -0.15)), yaw_c), "R": (OC3 + Vector((0.1, 0.2)), yaw_c + 20)})
# beat 7: staggers to the porch, up the steps, along the deck to the south edge
p_ow3 = catmull([(1182, V(OC3.x + 0.05, OC3.y + 0.05, 0)), (1240, V(2.7, 3.4, 0)), (1300, V(3.7, 5.4, 0)), (1330, V(4.2, 6.0, 0)),
                 (1365, V(5.3, 6.0, 0)), (1395, V(6.0, 5.0, 0)), (1416, V(6.15, 4.1, 0)), (1430, V(6.2, 3.7, 0))])
yaw3 = lambda f: yaw_to(p_ow3(f - 3), p_ow3(f + 3))
OW.h.walk(p_ow3, yaw3, 1182, 1430, stride=0.55, lean=24, bob=0.035, crouch=0.08, lift=0.12)
for f in range(1182, 1431, 8):
    p = p_ow3(f); M = OW.M(Vector((p.x, p.y, ground_z(p.x, p.y) + OW.RH.z)), yaw3(f), 12)
    if 1325 < f < 1370:
        # left hand grips the stair rail post side
        OW.arm("L", f, M, fwd=30, out=35, L=0.45)
    else:
        OW.arm("L", f, M, fwd=38, out=14, L=0.46)      # left arm hangs forward for balance; right hand clutches the stomach
    clutch(f, "R", "belly2")
    OW.fingers("L", f, 35, 20); OW.fingers("R", f, 30, 20)
    OW.face(f, jaw=22 + 8 * math.sin(f / 7.0), brow=5, lid=3, smile=-4)
# beat 8: butted at 1440 off the south edge (y = 3), falls, lands at 1478
EDGE = Vector((6.2, 3.45))
OW.stand(1438, Vector((6.2, 3.65)), 10, lean=10, spine=(20, 0, 0), head=(10, 0), crouch=0.06)
for s in "LR": W, d, n = HP("belly", s); OW.hand_local(s, 1438, OW.M(Vector((6.2, 3.65, PZ + OW.RH.z - 0.06)), 10, 10), W, d, n)
fall = [(1450, Vector((6.2, 3.25, PZ + 0.9)), 25, 10, 0), (1462, Vector((6.25, 2.8, 0.85)), 55, 14, 0), (1474, Vector((6.3, 2.35, 0.24)), 82, 8, 0),
        (1480, Vector((6.32, 2.15, 0.25)), 92, 4, 0), (1488, Vector((6.33, 2.1, 0.31)), 88, 2, 0), (1496, Vector((6.33, 2.08, 0.27)), 90, 0, 0)]
for f, P, lean, roll, yawv in fall:
    # lean = pitch about X (negative: falling backwards over the edge -> ends face down after the roll)
    OW.h.key_root(f, P, yaw=yawv, flex=lean, side=roll)
    OW.h.key_spine(f, flex=8, side=4, twist=6, head=(14, 30))
    M = OW.M(P, yawv, lean, roll)
    for s in "LR":
        sx = 1 if s == "L" else -1
        a = OW.h.ankle[s]; W = M @ Vector((a.x * 1.4, a.y + 0.05, a.z))
        W.z = max(W.z, 0.05)
        OW.key_foot_world(s, f, W, M.to_3x3())
        OW.arm(s, f, M, fwd=(60 + 30 * sx) if f < 1478 else (25 if s == 'L' else 5), out=40 if f < 1478 else (30 if s == 'L' else 12), L=0.5)
    OW.face(f, jaw=30 if f < 1480 else 6, brow=6 if f < 1480 else 0, lid=4 if f < 1480 else -6, smile=-4 if f < 1480 else 0)
# beat 9+: lies still, face down (eyes closed), arms out.  Hold to the end of the farm part.
LIE = Vector((6.33, 2.08, 0.27))
for f in (1500, 1735, 1905):
    OW.h.key_root(f, LIE, yaw=0, flex=90, side=0)
    OW.h.key_spine(f, flex=6, side=4, twist=6, head=(14, 30))
    M = OW.M(LIE, 0, 90, 0)
    for s in "LR":
        sx = 1 if s == "L" else -1
        a = OW.h.ankle[s]; W = M @ Vector((a.x * 1.5, a.y + 0.05, a.z)); W.z = 0.06
        OW.key_foot_world(s, f, W, M.to_3x3())
        OW.arm(s, f, M, fwd=(25 if s == 'L' else 5), out=(30 if s == 'L' else 12), L=0.46)   # arms close to the body, one up near the head
    OW.face(f, jaw=4, lid=-8)
OW.vis(1910, False)

# stick: child of the right wrist, dropped at the first impact
stick = bpy.data.objects["Stick"]
ev(42)
def wrist_frame(h_, s):
    A = h_.o.matrix_world; PB = h_.R.PB
    wr = A @ PB["wrist." + s].head; f3 = A @ PB["finger3-1." + s].head
    a_ = (A @ PB["finger2-1." + s].head) - (A @ PB["finger5-1." + s].head)
    d_ = (f3 - wr).normalized(); a_ = (a_ - d_ * a_.dot(d_)).normalized(); n_ = d_.cross(a_)
    return wr, d_, a_, n_
wr, d_, a_, n_ = wrist_frame(OW, "R")
G0 = (OW.o.matrix_world @ OW.R.PB['finger3-1.R'].head) - d_ * 0.01 - n_ * 0.03
xa = a_; ya = d_; za = xa.cross(ya)
Sm = Matrix((xa, ya, za)).transposed().to_4x4(); Sm.translation = G0 + xa * 0.3
cst = stick.constraints.new('CHILD_OF'); cst.target = OW.o; cst.subtarget = "wrist.R"
cst.inverse_matrix = Matrix.Identity(4)
Mw = OW.o.matrix_world @ OW.R.PB["wrist.R"].matrix
stick.matrix_basis = Mw.inverted() @ Sm
LOCAL = stick.matrix_basis.copy()
cst.influence = 1.0; cst.keyframe_insert("influence", frame=IMP1 - 1)
ev(IMP1 - 1); Mdrop = stick.matrix_world.copy()
cst.influence = 0.0; cst.keyframe_insert("influence", frame=IMP1)
def key_obj(o, f, M):
    loc, q, s_ = M.decompose(); o.rotation_mode = 'QUATERNION'
    o.location = loc; o.rotation_quaternion = q; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_quaternion", frame=f)
key_obj(stick, IMP1 - 1, LOCAL); stick.keyframe_insert("location", frame=IMP1 - 2); stick.keyframe_insert("rotation_quaternion", frame=IMP1 - 2)
key_obj(stick, IMP1, Mdrop)
land = Matrix.Translation(Vector((1.8, 0.7, 0.05))) @ Matrix.Rotation(R_(35), 4, 'Z')
mid = Matrix.Translation((Mdrop.translation + land.translation) / 2 + Vector((0.2, 0, 0.6))) @ Matrix.Rotation(R_(110), 4, 'Y')
key_obj(stick, IMP1 + 20, mid); key_obj(stick, IMP1 + 44, land); key_obj(stick, IMP1 + 50, Matrix.Translation(Vector((1.85, 0.68, 0.05))) @ Matrix.Rotation(R_(40), 4, 'Z'))
# fix: before the impact the stick follows the hand with the constant local offset
key_obj(stick, 1, LOCAL)

# ================================================================= GOAT
# beat 1: tense by the post, flinches away from the raised stick (no contact)
ghold(1, GA, math.degrees(math.atan2((OA_ - GA).x, -(OA_ - GA).y)))
h_face = math.degrees(math.atan2((OA_ - GA).x, -(OA_ - GA).y))
gneck(1, 5, 5, 0, 0, 10)
gp = gpath([(30, GA), (60, GA + Vector((-0.35, 0.12))), (90, GA + Vector((-0.55, 0.15))), (186, GA + Vector((-0.6, 0.2)))])
for f in (30, 44, 52, 60, 72, 90, 110, 130, 150, 170, 186):
    p = gp(f); flinch = 1.0 if 44 <= f <= 130 else 0.4
    ghold(f, p.to_2d(), h_face + (25 if f > 50 else 0), dz=-0.05 * flinch, pitch=-3 * flinch, roll=0)
    gneck(f, -10 * flinch, 18 * flinch, 10 * flinch, turn=(-30 if f % 40 < 20 else -18) * flinch, tail=-20 * flinch)
# quick hoof shuffles while backing (re-key hooves via quad_move over the short back-off)
quad_move(G, lambda f: Vector((gp(f).x, gp(f).y, 0)), 44, 92, stride=0.35, gait="walk", heading_fn=lambda f: R_(h_face + 25))
# beat 2: rigid guard stance facing the passer-by, snorts (head jerks)
GB = GA + Vector((-0.6, 0.2))
for f in (187, 200, 240, 280, 320, 360, 400, 440, 462):
    tgt = Vector((lerp(-6.0, 6.0, (f - 187) / 276), -5.4))
    hh = math.degrees(math.atan2((tgt - GB).x, -(tgt - GB).y))
    ghold(f, GB, hh * 0.5, dz=0.0, pitch=0)
    sn = 1 if (f // 40) % 2 else 0
    gneck(f, -6 + 12 * sn, -8, 4 + 10 * sn, turn=hh * 0.5, tail=25)
# beat 3: time-lapse: the goat jumps between resting spots by the shed (stop-motion feel)
spots = [GB, GB + Vector((-0.4, 0.6)), GB + Vector((0.2, 0.5)), GB + Vector((-0.2, 0.9)), GB + Vector((0.3, -0.2)), GB]
tl = catmull([(463 + i * 33, Vector((p.x, p.y, 0))) for i, p in enumerate(spots)])
quad_move(G, tl, 463, 630, stride=0.42, gait="walk")      # fast-forward walk around the tether post (no teleports)
for i, f in enumerate(range(463, 631, 21)):
    gneck(f, 16 if i % 2 else -4, 8, 10 if i % 2 else 0, turn=(i % 3 - 1) * 18, tail=-10)
# thinner over time: the coat sinks onto the frame (displace inward along normals, before the armature)
gbody = [c for c in G.o.children if c.type == 'MESH'][0]
dm = gbody.modifiers.new("Thin", 'DISPLACE'); dm.mid_level = 0.0; dm.strength = 0.0
while gbody.modifiers.find("Thin") > 0: bpy.ops.object.modifier_move_up({"object": gbody}, modifier="Thin") if False else gbody.modifiers.move(gbody.modifiers.find("Thin"), 0)
for f, s_ in ((463, 0.0), (630, -0.012), (1905, -0.012), (1990, -0.006)):
    dm.strength = s_; dm.keyframe_insert("strength", frame=f)
# beat 4: had enough: head down, horns forward, front hoof stamps
G4 = GB + Vector((0.25, -0.1)); h4 = math.degrees(math.atan2((OC - G4).x, -(OC - G4).y))
for f in (631, 660, 700, 740, 780, 816):
    ghold(f, G4, h4, dz=-0.02, pitch=-2)
    gneck(f, 16, 8, 12, turn=0, tail=-25)
for i, f in enumerate(range(650, 820, 34)):           # FL stamps
    for df, lz in ((0, 0.0), (8, 0.09), (14, 0.0)):
        n = "IK_hoof.FL"; o = Matrix.Rotation(R_(h4), 3, 'Z') @ (G.BN[n].head_local - G.rest("torso").translation)
        M = hoof_matrix(G, n, Vector((G4.x + o.x, G4.y + o.y)), R_(h4), lift=lz); G.key_world(n, f + df, M)
# beat 5: charge in slow motion; contact 960 (horns at his belly), recoil
CH0 = G4; IMPP = OC + (G4 - OC).normalized() * 0.68
cp = gpath([(816, CH0), (850, CH0 + (IMPP - CH0) * 0.08), (930, CH0 + (IMPP - CH0) * 0.75), (958, IMPP), (975, IMPP + (CH0 - IMPP).normalized() * 0.16),
            (1060, IMPP + (CH0 - IMPP).normalized() * 0.35), (1128, IMPP + (CH0 - IMPP).normalized() * 0.45), (1140, IMPP + (CH0 - IMPP).normalized() * 0.1),
            (1148, OC3 + (G4 - OC).normalized() * 0.8), (1166, OC3 + (G4 - OC).normalized() * 1.0), (1182, OC3 + (G4 - OC).normalized() * 1.1)])
quad_move(G, cp, 816, 1182, stride=0.6, gait="trot", heading_fn=lambda f: R_(h4), lift=0.08)
for f, n1, tn in ((1000, 20, 25), (1020, 28, -25), (1045, 18, 20), (1070, 30, -15), (1095, 22, 10)):
    gneck(f, n1, 8, 18, tn, -20)
for f in (950, 956, 962, 968):
    ghold(f, cp(f).to_2d(), h4, dz=0.06, pitch=16)
for f in (1140, 1146, 1152):
    ghold(f, cp(f).to_2d(), h4, dz=0.06, pitch=16)
for f, n1, hd in ((816, 16, 12), (850, 18, 14), (940, 16, 12), (958, -12, -12), (975, -6, -8), (1060, 10, 6), (1128, 16, 12), (1146, -12, -12), (1182, 12, 8)):
    gneck(f, n1, 8, hd, 0, -20)
# beat 7: follows him to the porch and up the steps
gp7 = catmull([(1183, V(*(OC3 + (G4 - OC).normalized() * 0.75), 0)), (1260, V(2.1, 2.9, 0)), (1320, V(3.0, 5.2, 0)), (1355, V(3.9, 6.0, 0)),
               (1395, V(5.2, 6.0, 0)), (1420, V(5.9, 4.9, 0)), (1438, V(6.15, 4.45, 0))])
quad_move(G, gp7, 1183, 1438, stride=0.7, gait="trot")
for f in range(1183, 1439, 30): gneck(f, 14, 6, 10, 0, -15)
# beat 8: the butt at 1440, then watches over the edge
GB8 = Vector((6.18, 4.3))
for f, dz, pt, n1 in ((1436, -0.03, -6, 30), (1442, -0.02, -10, 40), (1452, 0.0, 0, 16), (1500, 0.0, 2, 30), (1560, 0.0, 0, 34), (1600, 0, 0, 20)):
    ghold(f, GB8 + (Vector((0, -0.18)) if f == 1442 else Vector((0, 0))), 0, dz=dz, pitch=pt)
    gneck(f, n1, 10, 20, 0, 10)
# beat 9: walks down the steps into the yard (officials arrive); beat 10: led up the ramp into the truck
gp9 = catmull([(1600, V(6.18, 4.3, 0)), (1630, V(5.6, 5.8, 0)), (1660, V(4.3, 6.0, 0)), (1700, V(2.6, 6.2, 0)), (1735, V(1.2, 6.8, 0)),
               (1790, V(-0.6, 7.4, 0)), (1830, V(-1.5, RAMP[0] - 0.2, 0)), (1880, V(-1.5, RAMP[1] + 0.3, 0)), (1905, V(-1.5, RAMP[1] + 1.2, 0))])
quad_move(G, gp9, 1600, 1905, stride=0.62, gait="walk")
for f in range(1600, 1906, 30): gneck(f, 4 + 10 * ((f // 30) % 2), 4, 6, 0, -5)
# beat 11: at the sanctuary (teleport while the camera is above the trees)
PAST_G = Vector((2.1, 62.4)); h11 = -70
ghold(1906, PAST_G, h11); ghold(2190, PAST_G, h11)
for f in range(1906, 2191, 24):
    k = (f // 24) % 3
    gneck(f, 6 + 3 * k, 4, 6 + 4 * (k == 1), turn=-4 + 4 * k, tail=20 if k == 2 else 5)     # head up, eating from her hand (chewing nods)
# pasture goats grazing
for i, (p, hh) in enumerate(((Vector((-1.5, 64.5)), 30), (Vector((4.8, 66.0)), -120), (Vector((-0.5, 59.0)), 160))):
    R2 = Rig(bpy.data.objects["PGoat_%d_rig" % i])
    for pb in R2.o.pose.bones: pb.rotation_mode = 'QUATERNION'
    path = catmull([(1880, V(p.x, p.y, 0)), (2190, V(p.x + 0.8 * math.sin(R_(hh)), p.y - 0.8 * math.cos(R_(hh)), 0))])
    quad_move(R2, path, 1880, 2190, stride=0.6, gait="walk")
    for f in range(1880, 2191, 40 + 7 * i):
        R2.key_rot("neck1", f, [("X", 40 + 6 * ((f // 40) % 2))]); R2.key_rot("head", f, [("X", 30)])

# ------------------------------------------------------------------ rope (tether), snaps at 832
ropeB = bpy.data.objects["RopeB"]; ropeA = bpy.data.objects["RopeA"]; ropeM = bpy.data.objects["RopeMid"]
ropeA.location = (POST.x, POST.y, 0.62)
cb = ropeB.constraints.new('CHILD_OF'); cb.target = G.o; cb.subtarget = "neck1"; cb.inverse_matrix = Matrix.Identity(4)
ev(1); nb = G.o.matrix_world @ G.PB["neck1"].matrix
ropeB.matrix_basis = nb.inverted() @ Matrix.Translation(nb @ Vector((0, G.BN["neck1"].length * 0.6, 0)))
rope = bpy.data.objects["Rope"]
for f in range(1, 840, 3):
    ev(f); b = ropeB.matrix_world.translation; a = ropeA.location
    L = (b - a).length; sag = max(0.0, 1.35 - L) * 0.5
    m = (a + b) / 2; m.z = max(0.02, m.z - sag)
    ropeM.location = m; ropeM.keyframe_insert("location", frame=f)
rope.hide_render = False; rope.keyframe_insert("hide_render", frame=831); rope.hide_render = True; rope.keyframe_insert("hide_render", frame=832)

# ================================================================= PASSER-BY (beat 1-3 background, walks along the fence)
pp = catmull([(1, V(-9.5, -7.2, 0)), (463, V(9.5, -7.0, 0))])
PS.h.walk(pp, lambda f: 90 - 2 if f < 300 else 90, 1, 463, stride=0.75)
for f in range(1, 464, 14):
    p = pp(f); M = PS.M(Vector((p.x, p.y, PS.RH.z)), 90)
    sw = 15 * math.sin(f / 22.0)
    PS.arm("R", f, M, fwd=10 + sw, out=10); PS.arm("L", f, M, fwd=10 - sw, out=10)
    PS.face(f, jaw=2, brow=3 if 220 < f < 320 else 0, lid=2 if 220 < f < 320 else 0)
for f in (230, 300): PS.h.key_spine(f, flex=0, twist=-10, head=(0, -50))     # looks at the snorting goat
PS.vis(1, True); PS.vis(470, False)

# ================================================================= OFFICIALS (arrive 1640, lead goat 1735-1905)
pole = bpy.data.objects["Stick"].copy(); pole.constraints.clear(); pole.animation_data_clear(); pole.name = "CatchPole"
bpy.data.collections["Props"].objects.link(pole); pole.scale = (1.8, 0.8, 0.8); pole.location = (0, 0, 0)
gpos = lambda f: Vector(gp9(f).to_2d())
gh = lambda f: yaw_to(gp9(f - 3), gp9(f + 3))
def _cl(p):
    p.y = min(p.y, RAMP[0] - 0.4); return p
pa = lambda f: _cl(gpos(f) + Matrix.Rotation(R_(gh(f)), 2) @ Vector((-1.0, -1.55)))        # ahead-left of the goat, pole length
pb_ = lambda f: _cl(gpos(f) + Matrix.Rotation(R_(gh(f)), 2) @ Vector((1.0, 0.5)))           # beside its flank
OFF_PATH = {}
for h_, fn in ((OA, pa), (OB_, pb_)):
    st_ = V(-3.5, 11.0, 0) if h_ is OA else V(-2.3, 11.8, 0)
    path = catmull([(1600, st_), (1700, V(*fn(1700), 0))] + [(f, V(*fn(f), 0)) for f in range(1735, 1906, 20)])
    h_.h.walk(path, lambda f, path=path: yaw_to(path(f - 4), path(f + 4)), 1600, 1905, stride=0.72)
    OFF_PATH[h_.o.name] = path
    h_.vis(1, False); h_.vis(1600, True); h_.vis(1910, False)
for f in range(1600, 1906, 10):
    for h_, fn in ((OA, pa), (OB_, pb_)):
        pth = OFF_PATH[h_.o.name]; p_ = pth(f); M_ = h_.M(Vector((p_.x, p_.y, h_.RH.z)), yaw_to(pth(f - 4), pth(f + 4))); sw = 14 * math.sin(f / 20.0)
        if f < 1700 or (h_ is OB_ and f < 1735):
            h_.arm("R", f, M_, fwd=10 + sw, out=24, L=0.5)
        h_.arm("L", f, M_, fwd=10 - sw, out=24, L=0.5)      # OffA holds the catch pole one-handed
        h_.fingers("L", f, 20, 15); h_.fingers("R", f, 20, 15)
    ev(f)
    # OffA holds the catch pole in both hands, loop end at the goat's neck
    neck = G.o.matrix_world @ G.PB["neck2"].head
    pA = OFF_PATH['OffA'](f).to_2d(); MA = OA.M(Vector((pA.x, pA.y, OA.RH.z)), yaw_to(OFF_PATH['OffA'](f - 4), OFF_PATH['OffA'](f + 4)))
    gripR = MA @ Vector((-0.34, -0.55, 1.02)); dirp = (neck - gripR).normalized(); gripL = gripR
    if f >= 1700:
        OA.h.key_hand("R", f, gripR, dirp.cross(Vector((0, 0, 1))), Vector((0, 0, -1)), MA @ Vector((-0.5, 0.4, 1.1)))
        q = dirp.to_track_quat('X', 'Z'); key_obj(pole, f, Matrix.Translation(gripR + dirp * 0.62) @ q.to_matrix().to_4x4())
        OA.fingers("R", f, 75, 40)
    OA.face(f, jaw=3, brow=-1)
    pB = OFF_PATH['OffB'](f).to_2d(); MB = OB_.M(Vector((pB.x, pB.y, OB_.RH.z)), yaw_to(OFF_PATH['OffB'](f - 4), OFF_PATH['OffB'](f + 4)))
    back = G.o.matrix_world @ G.PB["spine2"].head + Vector((0, 0, 0.12))
    if f >= 1735:
        OB_.h.key_hand("R", f, back, Vector((0, 0, -1)).cross(Vector((1, 0, 0))), Vector((0, 0, -1)), MB @ Vector((0.5, 0.4, 1.1)))
    OB_.face(f, jaw=2, brow=2, smile=-1)
pole.hide_render = True; pole.keyframe_insert("hide_render", frame=1); pole.hide_render = False; pole.keyframe_insert("hide_render", frame=1700)
pole.hide_render = True; pole.keyframe_insert("hide_render", frame=1910)
pole.scale = (1.8, 0.8, 0.8)
key_obj(pole, 1600, Matrix.Translation(Vector((-3.5, 11.0, -3))))

# ================================================================= RESCUER (kneels, strokes the goat, it eats from her palm)
RP = Vector((1.0, 61.95)); ry = yaw_to(RP, PAST_G)
RS.vis(1, False); RS.vis(1906, True)
for i, f in enumerate(range(1906, 2191, 12)):
    st = ((i // 3) % 2)
    M = RS.stand(f, RP, ry, lean=6, spine=(16, 0, -6), head=(22 + 4 * st, 0), crouch=0.42,
                 feet={"L": (RP + Matrix.Rotation(R_(ry), 2) @ Vector((0.14, -0.28)), ry, 0.0, 0.0),
                       "R": (RP + Matrix.Rotation(R_(ry), 2) @ Vector((-0.14, 0.42)), ry, 0.0, 55)})
    ev(f)
    dg_ = bpy.context.evaluated_depsgraph_get(); ge = gbody.evaluated_get(dg_); gm = ge.to_mesh()
    hh_ = G.o.matrix_world @ G.PB["head"].head; fw_ = (G.o.matrix_world @ G.PB["neck1"].head) - (G.o.matrix_world @ G.PB["hips"].head); fw_.z = 0; fw_.normalize()
    pts_ = [gbody.matrix_world @ v.co for v in gm.vertices]; ge.to_mesh_clear()
    near = [p for p in pts_ if (p - hh_).length < 0.4]
    mouth = max(near, key=lambda p: (p - hh_).dot(fw_) - 0.3 * abs(p.z - hh_.z)) if near else G.o.matrix_world @ G.PB["head"].tail
    tw_ = Vector((RP.x - mouth.x, RP.y - mouth.y, 0)).normalized()
    RS.h.key_hand("R", f, mouth + Vector((0.0, 0.0, -0.09)) + tw_ * 0.1,
                  Matrix.Rotation(R_(ry), 3, 'Z') @ Vector((0, -1, 0.1)), Vector((0, 0, 1)), M @ Vector((-0.5, 0.2, 0.9)))
    neck = G.o.matrix_world @ G.PB["neck1"].head.lerp(G.PB["chest"].head, 0.05 + 0.25 * st)
    RS.h.key_hand("L", f, neck + Vector((0, 0, 0.15 + 0.06 * st)), -fw_, Vector((0, 0, -1)), M @ Vector((0.5, 0.2, 0.9)))
    RS.fingers("R", f, 6, 4); RS.fingers("L", f, 4, 2)
    RS.face(f, jaw=3, brow=2, lid=0.5, smile=3)

# ================================================================= DUST + CLODS
PUFFS = [bpy.data.objects["DustPuff_%d" % i] for i in range(18)]; CLODS = [bpy.data.objects["Clod_%02d" % i] for i in range(40)]
_pi = [0]; _ci = [0]
def dust(f, pos, size=0.5, dur=90, rise=0.3, n_clods=6, slow=1.0):
    o = PUFFS[_pi[0] % 18]; _pi[0] += 1
    dens = o.data.materials[0].node_tree.nodes["Dens"].outputs[0]
    o.location = pos + Vector((0, 0, -40)); o.keyframe_insert("location", frame=f - 1)
    o.location = pos; o.scale = (size * 0.2,) * 3; o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)
    dens.default_value = 1.4; dens.keyframe_insert("default_value", frame=f)
    o.scale = (size, size, size * 0.7); o.location = pos + Vector((0, 0, rise * 0.5)); o.keyframe_insert("scale", frame=f + int(dur * 0.3)); o.keyframe_insert("location", frame=f + int(dur * 0.3))
    o.scale = (size * 1.7, size * 1.7, size * 1.1); o.location = pos + Vector((0.3, 0.1, rise)); o.keyframe_insert("scale", frame=f + dur); o.keyframe_insert("location", frame=f + dur)
    dens.default_value = 0.0; dens.keyframe_insert("default_value", frame=f + dur)
    o.location = pos + Vector((0, 0, -40)); o.keyframe_insert("location", frame=f + dur + 1)
    for k in range(n_clods):
        c_ = CLODS[_ci[0] % 40]; _ci[0] += 1
        v = Vector((random.uniform(-1.6, 1.6), random.uniform(-1.6, 1.6), random.uniform(1.5, 3.0)))
        p0 = pos.copy(); p0.z = max(0.03, p0.z)
        c_.location = p0 + Vector((0, 0, -40)); c_.keyframe_insert("location", frame=f - 1)
        T = 2 * v.z / 9.81
        for j in range(7):
            t = T * j / 6; ff = f + int(round(t * 60 * slow))
            c_.location = p0 + Vector((v.x * t, v.y * t, v.z * t - 4.9 * t * t)); c_.location.z = max(0.015, c_.location.z)
            c_.keyframe_insert("location", frame=ff)
        c_.location.z = -40; c_.keyframe_insert("location", frame=f + int(T * 60 * slow) + 30)
dust(IMP1, Vector((OC.x - 0.1, OC.y, 0.9)), 0.45, dur=150, rise=0.2, n_clods=0, slow=5)   # dust off his shirt (slow motion)
dust(IMP1 + 4, Vector((IMPP.x, IMPP.y, 0.05)), 0.7, dur=160, rise=0.2, n_clods=10, slow=5)
dust(1146, Vector((OC3.x, OC3.y, 0.9)), 0.4, dur=60, rise=0.3, n_clods=0)
dust(1148, Vector((OC3.x - 0.3, OC3.y, 0.05)), 0.6, dur=70, rise=0.3, n_clods=8)
dust(1479, Vector((6.3, 2.1, 0.08)), 1.0, dur=200, rise=0.5, n_clods=12)
dust(700, Vector((G4.x, G4.y - 0.2, 0.04)), 0.25, dur=50, rise=0.1, n_clods=3)
dust(770, Vector((G4.x, G4.y - 0.2, 0.04)), 0.25, dur=50, rise=0.1, n_clods=3)
for f in range(1188, 1330, 36): dust(f, Vector((gp7(f).x, gp7(f).y, 0.05)), 0.35, dur=60, rise=0.2, n_clods=0)

# tape wind + visibility (tape only once the body has been found)
for i in range(4):
    e = bpy.data.objects["TapeWind_%d" % i]
    e.location = (0, 0, 0); e.keyframe_insert("location", frame=1)
    e.location = (3.0 + i, 2.0, 1.0); e.keyframe_insert("location", frame=2190)
    for fc in (e.animation_data.action.fcurves if hasattr(e.animation_data.action, "fcurves") else []):
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    t = bpy.data.objects["Tape_%d" % i]
    t.hide_render = True; t.keyframe_insert("hide_render", frame=1); t.hide_render = False; t.keyframe_insert("hide_render", frame=1600)
bpy.data.textures["T_Warp"]  # (static)

# ================================================================= AMBIENT LIFE
def fcurves(o, data=False):
    ad = (o.data if data else o).animation_data; out = []
    if not ad or not ad.action: return out
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in getattr(strip, "channelbags", []): out += list(cb.fcurves)
    return out
# trees sway in the wind
for o in bpy.data.objects:
    if o.name.startswith("Tree_"):
        o.keyframe_insert("rotation_euler", frame=1)
        for fc in fcurves(o):
            if fc.array_index in (0, 1):
                m = fc.modifiers.new('NOISE'); m.scale = random.uniform(40, 70); m.strength = 0.035; m.phase = random.uniform(0, 100)
# drifting dust in the yard (wind), settling dust after the fall
for f, p, sz in ((20, (-1.5, -2.0, 0.25), 1.4), (200, (3.0, -3.0, 0.3), 1.6), (420, (-2.0, 0.5, 0.25), 1.2), (640, (1.5, -0.5, 0.2), 1.3),
                 (1200, (0.0, 3.0, 0.2), 1.3), (1530, (5.0, 0.8, 0.2), 1.8), (1620, (7.5, 1.5, 0.25), 1.6), (1760, (0.5, 4.5, 0.2), 1.4)):
    dust(f, Vector(p), sz, dur=170, rise=0.35, n_clods=0)
# background figure: the passer-by later works the far field edge (beats 4-9)
pp2 = catmull([(600, V(-13.0, -4.0, 0)), (1100, V(-13.5, 8.0, 0)), (1520, V(-12.0, 20.0, 0))])
PS.h.walk(pp2, lambda f: 180, 600, 1520, stride=0.7)
for f in range(600, 1521, 14):
    p = pp2(f); M = PS.M(Vector((p.x, p.y, PS.RH.z)), 180); sw = 15 * math.sin(f / 22.0)
    PS.arm("R", f, M, fwd=10 + sw, out=10); PS.arm("L", f, M, fwd=10 - sw, out=10)
PS.vis(600, True); PS.vis(1525, False)
# ================================================================= WORLD: time-lapse in beat 3, golden pasture in beat 11
sun = bpy.data.objects["Key_Sun"]; wt = sc.world.node_tree
tint = wt.nodes["SkyTint"].inputs['B']; stg = wt.nodes["SkyStrength"].inputs['Strength']; rot = wt.nodes["SkyRot"].inputs['Rotation']
def light(f, el, az, energy, col, tcol, s_, r_):
    sun.rotation_euler = (R_(90 - el), 0, R_(az)); sun.keyframe_insert("rotation_euler", frame=f)
    sun.data.energy = energy; sun.data.keyframe_insert("energy", frame=f); sun.data.color = col; sun.data.keyframe_insert("color", frame=f)
    tint.default_value = tcol + (1,); tint.keyframe_insert("default_value", frame=f)
    stg.default_value = s_; stg.keyframe_insert("default_value", frame=f)
    rot.default_value = (0, 0, R_(r_)); rot.keyframe_insert("default_value", frame=f)
DAY = ((1.0, 0.93, 0.84), (1.0, 0.95, 0.88))
light(1, 38, -35, 3.6, *DAY, 0.9, 246); light(462, 40, -30, 3.6, *DAY, 0.9, 252)
light(490, 22, 40, 2.4, (1.0, 0.75, 0.5), (1.0, 0.8, 0.62), 0.6, 300)        # autumn dusk
light(520, 15, 100, 0.8, (0.8, 0.85, 1.0), (0.7, 0.75, 0.85), 0.45, 340)     # grey winter
light(560, 30, -90, 2.0, (0.9, 0.9, 1.0), (0.8, 0.85, 0.95), 0.6, 30)
light(595, 45, -60, 3.0, (1.0, 0.92, 0.82), (1.0, 0.92, 0.85), 0.8, 200)
light(630, 38, -35, 3.4, (1.0, 0.9, 0.8), (1.0, 0.92, 0.84), 0.85, 244)
light(1500, 34, -30, 3.0, (1.0, 0.88, 0.76), (0.95, 0.9, 0.85), 0.8, 252)    # dust settles, slightly duller
light(1880, 30, -30, 3.0, (1.0, 0.88, 0.76), (0.95, 0.9, 0.85), 0.8, 256)
light(1960, 16, 60, 3.6, (1.0, 0.78, 0.52), (1.05, 0.9, 0.72), 1.0, 300)       # warm golden pasture
light(2190, 14, 62, 3.6, (1.0, 0.76, 0.5), (1.05, 0.9, 0.72), 1.0, 302)

# ================================================================= CAMERA: one continuous spline (pos, target, lens)
def TR(name):
    A = G.o.matrix_world
    if name == "gh": return A @ G.PB["head"].head.lerp(G.PB["head"].tail, 0.5)
    if name == "ge": return A @ G.PB["head"].head.lerp(G.PB["head"].tail, 0.3) + Vector((0, 0, 0.03))
    if name == "gb": return A @ G.PB["torso"].head
    if name == "gf": return A @ G.PB["IK_hoof.FL"].head
    if name == "gn": return A @ G.PB["neck1"].head
    if name == "ob": return OW.o.matrix_world @ OW.R.PB["root"].head
    if name == "oc": return OW.o.matrix_world @ OW.R.PB["spine03"].head
    if name == "oh": return OW.o.matrix_world @ OW.R.PB["head"].head
    if name == "ps": return PS.o.matrix_world @ PS.R.PB["spine03"].head
    if name == "mid": return (TR("gh") + TR("oc")) / 2
    if name == "gp": return TR("gh") * 0.6 + TR("ps") * 0.4
    if name == "fm": return TR("gh") * 0.45 + TR("oh") * 0.55 + Vector((0, 0, -0.1))
    raise KeyError(name)
def GROT():
    A = G.o.matrix_world
    fwd = (A @ G.PB["neck1"].head) - (A @ G.PB["hips"].head); fwd.z = 0; fwd.normalize()
    return Matrix.Rotation(math.atan2(fwd.x, -fwd.y), 3, 'Z')      # local -Y = goat forward, +Z up
def spec(v):
    """absolute tuple | (tracker, world offset) | (tracker, goat-local offset, 'g')"""
    if isinstance(v[0], str):
        p = TR(v[0])
        if len(v) > 2: return p + GROT() @ Vector(v[1])
        return p + Vector(v[1]) if len(v) > 1 else p
    return Vector(v)
CAMK = [
 (1,    (0.5, -6.7, 0.95), (0.2, 1.5, 0.85), 40),     # low behind the broken fence rails
 (60,   (0.9, -5.0, 1.0), ("mid", (0, 0, 0.1)), 42),
 (120,  (1.6, -0.5, 1.7), ("gh", (0, 0, 0)), 32),       # over the shoulder, stick high
 (186,  ("gh", (-1.0, -0.7, 0.1), "g"), ("gh",), 34),     # goat's face
 (250,  ("gb", (1.5, 0.2, 0.1), "g"), ("gh",), 38),      # orbit around
 (320,  (-1.3, 4.2, 1.0), (-0.6, -1.5, 0.55), 26),   # behind the goat, the passer-by beyond the fence    # behind the goat; passer-by beyond the fence
 (390,  (-2.7, 2.7, 0.75), ("gh",), 36),
 (462,  (0.6, 0.4, 0.95), ("gh",), 32),    # tense goat, whole head and neck in frame
 (540,  (0.4, 3.9, 1.3), ("gb",), 26),
 (630,  ("gb", (1.1, -1.3, 0.3), "g"), ("gh",), 32),
 (690,  ("gh", (1.0, -0.55, 0.3), "g"), ("gh", (0, 0, 0.05)), 38),    # eye macro
 (740,  ("gh", (0.8, -0.9, 0.15), "g"), ("gh",), 34),    # horns
 (790,  ("gf", (0.9, -0.9, 0.4), "g"), ("gh", (0, 0, -0.25)), 30),   # stamping hoof, head in frame
 (816,  (OC.x - 1.7, OC.y - 1.7, 0.85), ("mid",), 28),
 (880,  (OC.x - 1.0, OC.y - 2.1, 0.55), ("gh",), 28),     # skimming beside the charge
 (960,  (OC.x - 0.2, OC.y - 1.7, 0.7), ("ob", (0, 0, -0.15)), 30),   # impact, side-on
 (1000, (OC.x - 0.5, OC.y - 1.7, 1.05), ("fm",), 30),        # orbit around the doubled-over man
 (1040, (OC.x - 1.4, OC.y - 1.3, 1.1), ("fm",), 30),
 (1085, (OC.x - 2.0, OC.y - 0.5, 1.2), ("fm",), 30),
 (1128, (OC.x - 1.6, OC.y + 1.0, 1.15), ("fm",), 30),
 (1150, (OC.x - 0.2, OC.y + 1.8, 1.0), ("fm",), 28),        # whip orbit, "twice"
 (1182, (OC.x + 2.4, OC.y + 0.1, 1.3), ("oc",), 28),
 (1250, ("gb", (0.2, 1.7, 0.7), "g"), ("oc",), 26),      # chase cam behind the goat
 (1310, ("gb", (0.4, 1.9, 1.0), "g"), ("oh",), 26),
 (1365, (3.1, 4.4, 2.3), ("oh",), 24),                     # crane up the steps
 (1416, (5.0, 1.4, 2.4), ("oh",), 26),
 (1450, (3.9, 2.3, 1.3), (6.2, 3.1, 1.0), 26),            # profile at porch height: knocked off
 (1482, (4.3, 0.9, 0.9), (6.3, 2.2, 0.3), 28),
 (1519, (4.6, -0.4, 1.5), (6.3, 2.0, 0.2), 28),
 (1560, (6.6, -1.4, 2.3), (6.3, 2.4, 0.4), 26),            # pull away, orbit and rise
 (1600, (8.6, -1.6, 3.6), (6.2, 2.6, 0.4), 24),
 (1690, (5.0, -5.0, 6.5), (4.0, 3.5, 0.4), 22),
 (1735, (0.6, 1.0, 4.0), ("gb",), 24),
 (1800, (1.8, 5.6, 1.5), ("gb",), 28),
 (1860, (1.8, 8.0, 1.9), ("gb",), 28),                     # beside the ramp, clear of the officials
 (1905, (0.5, 9.0, 2.6), ("gb",), 24),
 (1928, (2.2, 56.0, 2.0), (2.0, 62.1, 0.55), 28),           # fast fly-over the tree line onto the goat at the sanctuary
 (1970, (3.2, 58.8, 1.3), (1.9, 62.2, 0.55), 30),
 (2020, (4.6, 58.6, 2.2), (1.9, 62.3, 0.5), 28),           # down into the pasture
 (2080, (2.6, 59.6, 1.3), (1.6, 62.2, 0.55), 32),
 (2140, (1.3, 60.3, 0.9), (1.5, 62.15, 0.5), 40),          # settle in front: goat's face at her palm, her face
 (2190, (1.1, 60.5, 0.85), (1.45, 62.1, 0.5), 44),
]
CK = []
for f, p, t, l in CAMK:
    ev(f); CK.append((f, spec(p), spec(t), l))
CAMK = CK
cam = sc.camera
fp = catmull([(f, p) for f, p, t, l in CAMK]); ft = catmull([(f, t) for f, p, t, l in CAMK]); fl = pchip([(f, float(l)) for f, p, t, l in CAMK])
for f in range(1, 2191):
    p = fp(f); t = ft(f)
    p.z = max(p.z, ground_z(p.x, p.y) + 0.12)
    cam.location = p; cam.rotation_mode = 'XYZ'
    cam.rotation_euler = (t - p).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cam.data.lens = fl(f); cam.data.keyframe_insert("lens", frame=f)
    cam.data.dof.focus_distance = (t - p).length; cam.data.dof.keyframe_insert("focus_distance", frame=f)
for f in range(320, 400):     # rack focus to the passer-by
    w = smooth((f - 320) / 30) * (1 - smooth((f - 370) / 30))
    cam.data.dof.focus_distance = lerp((ft(f) - fp(f)).length, (Vector(pp(f)) + Vector((0, 0, 1.4)) - fp(f)).length, w)
    cam.data.dof.keyframe_insert("focus_distance", frame=f)
sc["beats"] = [B[k] for k in sorted(B)]
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM saved", OUT)
