"""ShoeBomber character + prop animation. blender -b scene.blend --python 03_animate.py -- <out_anim.blend>
Uses blender/pipeline/anim_lib.py (MPFB IK control rig, Human helpers)."""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "../../pipeline/anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1:][0]
def ground_z(x, y):          # MPFB shoe soles sit ~2.5 cm below the rest foot: lift every foot target
    return 0.024
V = Vector
random.seed(3)
sc = bpy.context.scene
ROW = lambda i: (i - 3) * 0.86                     # row index -> seat y (row 3 = bomber, y = 0)
SX = {"A": -1.42, "B": -0.94, "C": -0.46, "D": 0.46, "E": 0.94, "F": 1.42}
AX = V((400, 0, 0))                                # airport origin
FWD = 180                                          # yaw for facing +Y (towards the cockpit)

# beat start frames (target times; retime later)
B = {1: 1, 2: 199, 3: 373, 4: 481, 5: 655, 6: 769, 7: 1069, 8: 1249, 9: 1393}
END = 1620

def setup(name):
    o = bpy.data.objects[name]
    R = make_human_ctrl(o)
    h = Human(R); h.name = name
    return h
HN = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Traveller", "Officer", "Sleeper1", "Sleeper2", "Sleeper3", "Sleeper4"]
HS = {n: setup(n) for n in HN}
print("RIGS_READY")

# ------------------------------------------------------------------ pose helpers
FINGERS = [("finger%d-%d" % (k, j)) for k in range(2, 6) for j in range(1, 4)]
def curl(h, s, f, amt, thumb=None):
    """amt 0 open .. 1 fist (local X bend); never flatter than a relaxed curl"""
    amt = max(amt, 0.25)
    thumb = amt * 0.6 if thumb is None else thumb
    for k in range(1, 6):
        for j in range(1, 4):
            n = "finger%d-%d.%s" % (k, j, s)
            a = (thumb if k == 1 else amt) * (55 if j == 1 else 70 if j == 2 else 45)
            q = Quaternion((1, 0, 0), math.radians(a)) if k != 1 else Quaternion((0, 0, 1), math.radians(-a * 0.5 if s == "L" else a * 0.5))
            h.r.key_q(n, f, q)

def seat_feet(h, f, x, y, spread=0.12, fwd=0.42, yaw=FWD, lift=(0, 0)):
    for s, sg, lf in (("L", -1, lift[0]), ("R", 1, lift[1])):
        # facing +Y: character's left is -X
        h.key_foot(s, f, V((x + sg * spread, y + fwd)), yaw, lf, 0)

def sit(h, f, x, y, flex=8.0, spine=(5, 0, 0), head=(0, 0), yaw=FWD, z=0.56, side=0.0, fwd=0.42, spread=0.12, lift=(0, 0)):
    h.key_root(f, V((x, y - 0.02, z)), yaw=yaw, flex=flex, side=side)
    h.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    seat_feet(h, f, x, y, spread, fwd, yaw, lift)

def hand(h, s, f, W, d, n, pole=None, grip=0.0):
    h.key_hand(s, f, V(W), V(d), V(n), pole=V(pole) if pole else None)
    curl(h, s, f, grip)

def rest_arm(h, s, f, root, yaw=FWD, out=0.26, fwd=0.28, z=0.17, grip=0.3):
    """hand resting on the thigh/armrest, relative to the root position"""
    sg = -1 if s == "L" else 1
    if yaw == FWD:
        W = V((root.x + sg * out, root.y + fwd, root.z + z)); d = V((0, 1, -0.3)); n = V((0, 0, -1))
    else:
        W = V((root.x - sg * out, root.y - fwd, root.z + z)); d = V((0, -1, -0.3)); n = V((0, 0, -1))
    hand(h, s, f, W, d, n, grip=grip)

def stand(h, f, pos, yaw, flex=0.0, spine=(0, 0, 0), head=(0, 0), crouch=0.0, side=0.0, feet=True, stance=0.0):
    p = V(pos)
    h.key_root(f, V((p.x, p.y, h.root_head.z - 0.02 - crouch)), yaw=yaw, flex=flex, side=side)
    h.key_spine(f, flex=spine[0], twist=spine[1], side=spine[2], head=head)
    if feet:
        for s in "LR":
            xy = h.foot_xy(s, p, yaw)
            fw = Matrix.Rotation(math.radians(yaw), 3, 'Z') @ V((0, -1, 0))
            off = (stance if s == "L" else -stance) * fw
            h.key_foot(s, f, V((xy.x + off.x, xy.y + off.y)), yaw)

def breathe(h, f0, f1, base_flex=5, amp=1.5, period=70, head=(0, 0), twist=0.0, side=0.0):
    """keeps seated/standing extras alive: spine + head micro motion (keys every 20 f)"""
    ph = random.uniform(0, 6.28)
    for f in range(f0, f1 + 1, 20):
        t = (f - f0) / period * 2 * math.pi + ph
        h.key_spine(f, flex=base_flex + amp * math.sin(t), twist=twist + 2 * math.sin(0.6 * t), side=side,
                    head=(head[0] + 3 * math.sin(0.7 * t + 1), head[1] + 5 * math.sin(0.4 * t)))

def wpos(h, bone, f):
    ev(f); return (h.r.o.matrix_world @ h.r.PB[bone].matrix).translation.copy()
def wmat(h, bone, f):
    ev(f); return h.r.o.matrix_world @ h.r.PB[bone].matrix

def all_keys_bezier():
    pass

# ================================================================== CABIN
bom, att, stw = HS["Bomber"], HS["Attendant"], HS["Steward"]
pa, pb, pc, pd = HS["PaxA"], HS["PaxB"], HS["PaxC"], HS["PaxD"]
trav, off = HS["Traveller"], HS["Officer"]
BX, BY = SX["A"], ROW(3)

# ---------------------------------------------------------------- BOMBER
# beat 1: hunched, right foot pulled up onto the seat edge, shoe in left hand, right hand strikes + holds match
def set_pole(h, s, f, P):
    n = "Pole_knee." + s; pb_ = h.r.PB[n]
    pb_.location = h.r.rest(n).to_3x3().inverted() @ (V(P) - h.r.BN[n].head_local)
    pb_.keyframe_insert("location", frame=f, group=n)
def bomber_hunch(f, lean=38, head=(28, 0), foot_up=0.42, twist=-8, hx=0.0):
    """v006: right heel up on the seat edge, knee out to his right, foot well clear of his body; a shallower lean
    (head stays off the seat in front)"""
    lean = lean * 0.3
    bom.key_root(f, V((BX + 0.02, BY - 0.08, 0.56)), yaw=FWD, flex=6, side=-3)
    bom.key_spine(f, flex=lean, twist=twist * 0.7, side=3, head=(head[0] * 0.9, head[1]))
    bom.key_foot("L", f, V((BX - 0.12, BY + 0.44)), FWD, 0, 0)
    bom.key_foot("R", f, V((BX + 0.22, BY + 0.32)), FWD + 15, foot_up, 15)
    set_pole(bom, "R", f, (BX + 0.75, BY + 0.55, 0.85))     # knee out to his right, away from his arms

for f, lean, hd, tw in ((1, 36, (26, -4), -8), (40, 40, (30, 2), -10), (90, 42, (34, -2), -12), (150, 40, (30, 4), -9), (200, 38, (26, 0), -8)):
    bomber_hunch(f, lean, hd, twist=tw)
# shoe-holding left hand and match hand: placed relative to the right ankle (evaluated after the feet are keyed)
def shoe_pt(f, dx=0.0, dy=0.0, dz=0.0):
    a = wpos(bom, "foot.R", f); return a + V((dx, dy, dz))
for f in (1, 40, 90, 150, 200, 260, 330, 372):
    a = shoe_pt(f)
    hand(bom, "L", f, a + V((-0.03, 0.17, 0.07)), (0.2, 0.8, -0.5), (1, 0, 0), pole=(BX - 0.6, BY - 0.2, 0.6), grip=0.55)   # holds the toe, in front of the shin
# right hand: strike (f10-28 swipe along the box held in the left hand), then hold the match flame to the tongue
strike = [(1, V((0.10, 0.02, 0.16))), (14, V((0.06, 0.06, 0.14))), (22, V((0.13, -0.04, 0.12))), (30, V((0.07, 0.10, 0.13))),
          (60, V((0.03, 0.07, 0.20))), (90, V((0.02, 0.08, 0.18))), (120, V((0.04, 0.06, 0.19))), (150, V((0.02, 0.09, 0.18))),
          (200, V((0.03, 0.07, 0.19))), (260, V((0.03, 0.08, 0.18))), (330, V((0.02, 0.08, 0.19))), (372, V((0.03, 0.07, 0.18))),
          (400, V((0.06, 0.02, 0.20)))]
for f, o in strike:
    a = shoe_pt(f)
    hand(bom, "R", f, a + o, (-0.5, 0.5, -0.4), (0, 0, -1), pole=(BX + 0.6, BY - 0.3, 0.7), grip=0.8)
# beat 2 (199-372): keeps trying, glances up once (~300), back down
for f, lean, hd, tw in ((260, 40, (32, -5), -10), (300, 34, (12, 10), -6), (330, 40, (30, 0), -10), (372, 39, (28, 2), -9)):
    bomber_hunch(f, lean, hd, twist=tw)
# beat 3 (373-480): caught: freezes, head snaps up toward the attendant in the aisle (to his right, +X)
bomber_hunch(395, 22, (-8, 35), twist=10)
bomber_hunch(420, 18, (-10, 40), twist=14)
hand(bom, "R", 420, shoe_pt(420) + V((0.08, 0.0, 0.25)), (0, 0.4, 0.6), (0, -1, 0), pole=(BX + 0.6, BY - 0.3, 0.7), grip=0.8)
hand(bom, "L", 420, shoe_pt(420) + V((-0.03, 0.17, 0.07)), (0.2, 0.8, -0.5), (1, 0, 0), pole=(BX - 0.6, BY - 0.2, 0.6), grip=0.55)
# beat 4 (481-654): lunges up, grabbed, dragged out into the aisle, pinned face-down (head toward +Y)
bom.key_root(450, V((BX + 0.05, BY - 0.02, 0.57)), yaw=FWD, flex=8, side=0); bom.key_spine(450, flex=20, twist=15, head=(-5, 30))
bom.key_foot("R", 450, V((BX + 0.13, BY + 0.42)), FWD, 0, 0); bom.key_foot("L", 450, V((BX - 0.12, BY + 0.44)), FWD, 0, 0)
hand(bom, "R", 450, V((BX + 0.25, BY + 0.30, 0.95)), (0.5, 0.5, 0.2), (0, 0, -1), grip=0.8)
hand(bom, "L", 450, V((BX - 0.2, BY + 0.35, 0.75)), (0, 1, 0), (0, 0, -1), grip=0.5)
# 490: rises, hunched under the bins, attendant has his right wrist
bom.key_root(495, V((BX + 0.25, BY + 0.12, 0.92)), yaw=FWD - 40, flex=30, side=-5); bom.key_spine(495, flex=30, twist=-10, head=(10, -10))
bom.key_foot("L", 495, V((BX - 0.05, BY + 0.40)), FWD - 30, 0, 0); bom.key_foot("R", 495, V((BX + 0.35, BY + 0.38)), FWD - 40, 0.0, 0)
# 520: hauled sideways across row (B/C), feet stumbling
bom.key_root(525, V((-0.75, BY + 0.20, 0.85)), yaw=FWD - 70, flex=40, side=10); bom.key_spine(525, flex=35, twist=-20, head=(15, -15))
bom.key_foot("L", 525, V((-1.0, BY + 0.38)), FWD - 60, 0.12, 0); bom.key_foot("R", 525, V((-0.55, BY + 0.40)), FWD - 80, 0, 0)
# 555: falling into the aisle, body pitching forward toward +Y
bom.key_root(555, V((-0.15, BY + 0.55, 0.55)), yaw=FWD - 10, flex=65, side=15); bom.key_spine(555, flex=20, twist=10, head=(-20, 10))
bom.key_foot("L", 555, V((-0.30, BY + 0.10)), FWD, 0.15, -30); bom.key_foot("R", 555, V((-0.05, BY + 0.05)), FWD, 0.25, -40)
for f, hr_, hl_ in ((495, (BX + 0.62, BY + 0.38, 1.02), (BX + 0.05, BY + 0.58, 0.92)),
                  (525, (-0.22, BY + 0.72, 0.98), (-0.52, BY + 0.82, 0.72)),
                  (555, (0.10, BY + 1.30, 0.50), (-0.26, BY + 1.22, 0.32))):
    hand(bom, "R", f, hr_, (0.3, 1, -0.2), (0, 0, -1), grip=0.4)
    hand(bom, "L", f, hl_, (0, 1, -0.6), (0, 0, -1), grip=0.25)
# 580: hits the floor (impact, slight bounce at 590), pinned at 600+
for f, z, fl in ((578, 0.27, 92), (586, 0.31, 90), (596, 0.27, 91), (654, 0.27, 91), (700, 0.265, 91), (768, 0.265, 91)):
    bom.key_root(f, V((0.0, BY + 0.75, z)), yaw=FWD, flex=fl, side=0)
    bom.key_spine(f, flex=-2, twist=-5, head=(-18, 32) if f < 700 else ((-18, 34) if f == 700 else (-15, 38)))
    bom.key_foot("L", f, V((-0.11, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.11, BY - 0.27)), FWD, 0.03, -75)
# struggle wiggle while pinned (beat 4 end, beat 5 start), then limp (sedated ~ 720)
for f in range(600, 721, 12):
    w = 1.0 if f < 690 else max(0.0, (720 - f) / 30)
    bom.key_root(f, V((0.0 + 0.03 * w * math.sin(f), BY + 0.75, 0.27 + 0.02 * w * abs(math.sin(f * 0.7)))), yaw=FWD + 4 * w * math.sin(f * 0.5), flex=91, side=6 * w * math.sin(f * 0.9))
    bom.key_spine(f, flex=-2 + 4 * w * math.sin(f * 0.3), twist=-5 + 8 * w * math.sin(f * 0.6), head=(-18 + 3 * (1 - w), 32 + 6 * (1 - w)))
# arms when pinned: left arm twisted behind his back (held by PaxB), right arm out forward on the floor (held by attendant / injected)
for f in (582, 654, 720, 768, 830, 1068):
    hand(bom, "L", f, V((-0.30, BY + 0.55, 0.08)), (0, -1, 0), (0, 0, -1), pole=(-0.6, BY + 0.9, 0.4), grip=0.3)
    hand(bom, "R", f, V((0.16, BY + 1.50, 0.34 if f < 720 else 0.30)), (0.05, 0.8, 0.3), (0, 0, -1), pole=(0.6, BY + 1.0, 0.5), grip=0.6 if f < 720 else 0.15)
# after sedation he lies still; tiny breathing
for f in range(780, 1069, 30):
    bom.key_root(f, V((0.0, BY + 0.75, 0.265 + 0.004 * math.sin(f * 0.1))), yaw=FWD, flex=91, side=0)
    bom.key_spine(f, flex=-2, twist=-5, head=(-15, 38))
    bom.key_foot("L", f, V((-0.11, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.11, BY - 0.27)), FWD, 0.03, -75)
print("BOMBER_DONE")

# ---------------------------------------------------------------- ATTENDANT (from the front galley, pushing the trolley toward -Y)
# beat 2: walks behind the trolley (y 7.6 -> 2.3), stops ~ f300, sniffs (head up, turns left toward row 3 at f330)
apath = catmull([(170, V((0.0, 7.9, 0))), (230, V((0.0, 5.6, 0))), (300, V((0.0, 3.0, 0))), (318, V((0.0, 2.85, 0)))])
att.walk(apath, lambda f: 0.0, 170, 318, stride=0.62, lift=0.06, lean=8)
def swing(h, path, f0, f1, facing_y=-1, step=10, amp=0.11, period=36):
    """relaxed arm swing while walking (hands opposite to the legs)"""
    for f in range(f0, f1 + 1, step):
        p = path(f); ph = math.sin((f - f0) / period * 2 * math.pi)
        for s_, sg in (("L", 1), ("R", -1)):
            side = sg * (1 if facing_y < 0 else -1) * 0.24
            hand(h, s_, f, V((p.x + side, p.y + facing_y * sg * ph * amp, 0.86)), (0, facing_y * 0.2, -1), (-side, 0, 0), grip=0.3)
TROLLEY = bpy.data.objects["Trolley"]
TROLLEY.location = V((0, 8.55, 0.52)); TROLLEY.keyframe_insert("location", frame=1)      # parked in the forward galley
swing(att, apath, 170, 318)
# stop + sniff + turn
stand(att, 330, apath(318), 0, spine=(-6, 0, 0), head=(-14, 0))           # nose up, sniff
stand(att, 350, apath(318), 0, spine=(-4, 0, 0), head=(-10, -20))
stand(att, 372, V((0.0, 2.8, 0)), -25, spine=(4, -20, 0), head=(6, -25))   # turns toward row 3 (to her right)
hand(att, "L", 330, V((0.22, 2.85, 0.88)), (0, 0, -1), (-1, 0, 0), grip=0.3)
hand(att, "R", 330, V((-0.24, 2.80, 0.90)), (0, 0, -1), (1, 0, 0), grip=0.3)
hand(att, "R", 350, V((-0.22, 2.85, 0.88)), (0, 0, -1), (1, 0, 0), grip=0.3)
hand(att, "L", 372, V((0.22, 2.8, 0.88)), (0, 0, -1), (-1, 0, 0), grip=0.3)
hand(att, "R", 372, V((-0.22, 2.75, 0.9)), (0, 0, -1), (1, 0, 0), grip=0.3)
# beat 3 (373-480): she steps to row 3, leans over seat C looking at him: "caught"
apath2 = catmull([(376, V((0.0, 2.8, 0))), (400, V((0.05, 1.6, 0))), (424, V((0.1, 0.62, 0)))])
att.walk(apath2, lambda f: -70.0 * smooth((f - 404) / 20.0), 376, 424, stride=0.6, lift=0.06, lean=10)
swing(att, apath2, 376, 412, step=12)
for f, yaw, sp, hd in ((432, -78, (22, -12, 4), (14, -15)), (470, -84, (28, -10, 5), (16, -10))):
    stand(att, f, V((0.1, 0.62, 0)), yaw, spine=sp, head=hd, stance=0.12)
for f in (430, 470):
    hand(att, "L", f, V((-0.30, 0.63, 1.15)), (-1, 0, -0.3), (0, 0, -1), grip=0.5)       # left hand on the seat-back top (row 4)
    hand(att, "R", f, V((-0.05, 0.48, 1.05)), (0, -1, 0.2), (0, 0, -1), grip=0.35)
# beat 4: grabs his right wrist (f490), pulls into the aisle, kneels at his head pinning the right arm
ev(495); wr = wpos(bom, "wrist.R", 495)
hand(att, "R", 492, wr + V((0.03, 0, 0.07)), (-1, 0, -0.2), (0, 0, -1), grip=0.6)
hand(att, "L", 492, wr + V((0.10, 0.04, 0.06)), (-1, 0.2, 0), (0, 0, -1), grip=0.6)
stand(att, 492, V((0.12, 0.55, 0)), -90, spine=(25, 0, 0), head=(10, 0), crouch=0.1, stance=0.18)
stand(att, 525, V((0.12, 0.75, 0)), -60, spine=(30, 15, 0), head=(15, 0), crouch=0.15, stance=0.2)
for f in range(500, 541, 10):
    ev(f); w_ = wpos(bom, "wrist.R", f)
    hand(att, "R", f, w_ + V((0.04, -0.03, 0.10)), (-0.5, 0.5, -0.4), (0, 0, -1), grip=0.5)
    hand(att, "L", f, w_ + V((0.10, -0.10, 0.10)), (-0.5, 0.5, -0.4), (0, 0, -1), grip=0.5)
# follows him as he goes down: steps up beside him to his head, then kneels (real in-betweens)
apath3 = catmull([(540, V((0.12, 0.78, 0))), (562, V((0.0, 1.45, 0))), (582, V((-0.16, 2.0, 0)))])
att.walk(apath3, lambda f: -60 + 40 * smooth((f - 540) / 42.0), 540, 582, stride=0.45, lift=0.05, lean=18)
swing(att, apath3, 548, 580, facing_y=1, step=8, amp=0.08, period=26)   # lets go of his wrist as he drops and steps up to his head
stand(att, 597, V((-0.17, 2.02, 0)), -20, spine=(45, 10, 0), head=(15, 10), crouch=0.35)
# kneel at his head (y ~ BY+2.0), facing -Y, holding his outstretched right forearm
for f in (612, 654, 720, 760):
    att.key_root(f, V((-0.18, BY + 2.0, 0.47)), yaw=-20, flex=15)
    att.key_spine(f, flex=62, twist=10, head=(12, 10))
    att.key_foot("L", f, V((-0.02, BY + 2.38)), -20, 0.02, -65); att.key_foot("R", f, V((-0.30, BY + 2.30)), -20, 0.02, -65)
    hand(att, "R", f, V((0.15, BY + 1.58, 0.47)), (0, -1, -0.4), (0, 0, -1), grip=0.5)
    hand(att, "L", f, V((0.21, BY + 1.36, 0.46)), (0, -1, -0.4), (0, 0, -1), grip=0.5)
# beat 6 (769-1068): goes to his feet, kneels, pulls both sneakers off and lifts them under the reading light
stand(att, 785, V((-0.1, BY + 2.05, 0)), 0, spine=(20, 0, 0), head=(15, 0), crouch=0.05)
awp = catmull([(790, V((0.18, BY + 2.0, 0))), (812, V((0.21, BY + 1.0, 0))), (835, V((0.19, BY - 0.45, 0))), (848, V((0.14, BY - 1.02, 0)))])
att.walk(awp, lambda f: 0.0, 790, 848, stride=0.6, lift=0.07, lean=10)
swing(att, awp, 790, 845, step=11)
stand(att, 856, V((0.12, BY - 1.0, 0)), 90, spine=(10, 0, 0), head=(20, 20), stance=0.08)            # turns round at his feet
stand(att, 864, V((0.08, BY - 0.96, 0)), 170, spine=(30, 0, 0), head=(25, 0), crouch=0.22, stance=0.1)
for s_, sg in (("L", -1), ("R", 1)):
    hand(att, s_, 856, V((0.12 + sg * 0.25, BY - 1.0, 0.88)), (0, 0, -1), (-sg, 0, 0), grip=0.3)
    hand(att, s_, 866, V((0.08 + sg * 0.18, BY - 0.72, 0.62)), (0, 1, -0.6), (0, 0, -1), grip=0.3)
KN = V((0.05, BY - 0.62, 0))          # kneeling spot behind his feet, facing +Y
for f in (874, 880, 940, 1000, 1068):
    att.key_root(f, V((KN.x, KN.y, 0.47 if f < 900 else 0.58)), yaw=FWD, flex=15 if f < 900 else 5)
    att.key_spine(f, flex=50 if f < 900 else 5, twist=0, head=(20, 0) if f < 900 else (5, 0))
    att.key_foot("L", f, V((KN.x - 0.12, KN.y - 0.35)), FWD, 0.02, -65); att.key_foot("R", f, V((KN.x + 0.14, KN.y - 0.33)), FWD, 0.02, -65)
# grasp the heels (870), pull off (880-900), lift up together (900-960), turn the soles to the light (960-1068)
ev(876); hl = wpos(bom, "foot.L", 876); hr = wpos(bom, "foot.R", 876)
hand(att, "L", 876, hl + V((-0.06, -0.05, 0.10)), (0.2, 1, -0.3), (1, 0, 0), grip=0.7)
hand(att, "R", 876, hr + V((0.06, -0.05, 0.10)), (-0.2, 1, -0.3), (-1, 0, 0), grip=0.7)
hand(att, "L", 900, V((KN.x - 0.2, KN.y + 0.45, 0.35)), (0, 1, 0.2), (1, 0, 0), grip=0.75)
hand(att, "R", 900, V((KN.x + 0.2, KN.y + 0.45, 0.35)), (0, 1, 0.2), (-1, 0, 0), grip=0.75)
for f, z, rot in ((950, 1.05, 0), (1000, 1.15, 25), (1068, 1.2, 35)):
    hand(att, "L", f, V((KN.x - 0.22, KN.y + 0.32, z)), (0.3, 0.5, 0.8), (1, 0, 0), grip=0.75)
    hand(att, "R", f, V((KN.x + 0.22, KN.y + 0.32, z)), (-0.3, 0.5, 0.8), (-1, 0, 0), grip=0.75)
print("ATTENDANT_DONE")

# ---------------------------------------------------------------- PAX A (asleep next to him in 3B, wakes, grabs him, helps pin his shoulders)
for f in range(1, 400, 20):
    sit(pa, f, SX["C"], BY, flex=4, spine=(-2, 0, 6), head=(18 + 6 * math.sin(f * 0.05), -25 + 8 * math.sin(f * 0.03)))
for s in "LR": rest_arm(pa, s, 1, V((SX["C"], BY, 0.56)), grip=0.25)
for s in "LR": rest_arm(pa, s, 400, V((SX["C"], BY, 0.56)), grip=0.25)
sit(pa, 420, SX["C"], BY, flex=4, spine=(4, -20, 0), head=(0, -40))      # wakes, looks at the bomber
sit(pa, 470, SX["C"], BY, flex=4, spine=(12, -30, 0), head=(5, -35))
hand(pa, "R", 470, V((SX["C"] - 0.50, BY + 0.20, 1.04)), (-1, 0, 0), (0, 0, -1), grip=0.5)    # grabs the top of the bomber's shoulder
hand(pa, "L", 470, V((SX["C"] - 0.42, BY + 0.05, 0.86)), (-1, 0, -0.2), (0, 0, -1), grip=0.5)
# stands half up, pushes him into the aisle (follows the bomber's back)
stand(pa, 525, V((-0.25, BY + 0.30, 0)), FWD - 40, flex=10, spine=(35, -10, 0), head=(20, -10), crouch=0.35)
hand(pa, "R", 525, V((-0.65, BY + 0.30, 1.0)), (1, 0.4, 0), (0, 0, -1), grip=0.8)
hand(pa, "L", 525, V((-0.80, BY + 0.10, 0.9)), (1, 0.2, 0), (0, 0, -1), grip=0.8)
# kneels in the aisle by the bomber's left side, both hands on his shoulder blades
for f in (585, 654, 720, 768):
    pa.key_root(f, V((-0.05, BY + 0.05, 0.58)), yaw=FWD + 20, flex=10)
    pa.key_spine(f, flex=60 if f < 720 else 45, twist=5, head=(20, 0) if f < 720 else (10, 20))
    pa.key_foot("L", f, V((-0.25, BY - 0.35)), FWD + 20, 0.02, -65); pa.key_foot("R", f, V((0.12, BY - 0.40)), FWD + 20, 0.02, -65)
    hand(pa, "L", f, V((-0.10, BY + 1.05, 0.55)), (0.1, 1, -0.4), (0, 0, -1), grip=0.25)
    hand(pa, "R", f, V((0.12, BY + 1.0, 0.55)), (-0.1, 1, -0.4), (0, 0, -1), grip=0.25)

# ---------------------------------------------------------------- PAX B (2C behind, aisle seat; stands, pins the left arm / legs)
for f in range(1, 470, 20):
    sit(pb, f, SX["C"], ROW(2), spine=(8, 0, 0), head=(20 + 3 * math.sin(f * 0.04), -5))
for s in "LR": rest_arm(pb, s, 1, V((SX["C"], ROW(2), 0.56)), fwd=0.38, z=0.2, grip=0.6)     # phone in hands
for s in "LR": rest_arm(pb, s, 400, V((SX["C"], ROW(2), 0.56)), fwd=0.38, z=0.2, grip=0.6)
sit(pb, 440, SX["C"], ROW(2), spine=(2, 15, 0), head=(-5, 20))      # looks up at the commotion
stand(pb, 470, V((SX["C"] + 0.08, ROW(2) + 0.05, 0)), FWD, spine=(25, 0, 0), head=(10, 0), crouch=0.3)
pbo = catmull([(474, V((SX["C"] + 0.08, ROW(2) + 0.05, 0))), (500, V((0.0, ROW(2) + 0.1, 0)))])
pb.walk(pbo, lambda f: FWD, 474, 500, stride=0.35, lift=0.05, lean=8)
stand(pb, 545, V((0.0, ROW(2) + 0.3, 0)), FWD, spine=(30, 0, 0), head=(20, 0), crouch=0.15, stance=0.15)
for f in (590, 654, 720, 768):     # kneels on his legs side, holds the twisted left arm behind his back
    pb.key_root(f, V((0.10, BY - 0.80, 0.55)), yaw=FWD, flex=12)
    pb.key_spine(f, flex=62 if f < 720 else 50, twist=-8, head=(20, 0) if f < 720 else (10, -10))
    pb.key_foot("L", f, V((-0.02, BY - 1.18)), FWD, 0.02, -65); pb.key_foot("R", f, V((0.22, BY - 1.18)), FWD, 0.02, -65)
    hand(pb, "L", f, V((-0.08, BY - 0.10, 0.49)), (0, 1, -0.5), (0, 0, -1), grip=0.3)     # on the back of his calves
    hand(pb, "R", f, V((0.12, BY - 0.12, 0.49)), (0, 1, -0.5), (0, 0, -1), grip=0.3)

stand(pa, 790, V((-0.12, BY + 0.12, 0)), 70, spine=(30, 0, 0), head=(20, -20), crouch=0.4)
pap = catmull([(796, V((-0.14, BY + 0.14, 0))), (825, V((-0.58, BY + 0.38, 0)))])
pa.walk(pap, lambda f: 70.0, 796, 825, stride=0.4, lift=0.05, lean=6)
for f in (850, 950, 1068):
    stand(pa, f, V((-0.58, BY + 0.38, 0)), 70, spine=(12, 5, 0), head=(18, -10 + 10 * math.sin(f)), crouch=0.25)
for f in (826, 1068):
    hand(pa, "R", f, V((-0.62, BY + 0.64, 1.14)), (0.3, 0, -1), (0, 1, 0), grip=0.6)   # hand on the seat-back top (row 4)
    hand(pa, "L", f, V((-0.80, BY + 0.10, 0.88)), (0, 0, -1), (1, 0, 0), grip=0.3)
stand(pb, 790, V((0.08, BY - 1.0, 0)), FWD, spine=(15, 0, 0), head=(20, 0), crouch=0.1)
pbp = catmull([(795, V((0.08, BY - 1.0, 0))), (860, V((0.05, BY - 2.6, 0)))])
pb.walk(pbp, lambda f: FWD, 795, 860, stride=0.5, lean=-4)
for f in (900, 1068):
    stand(pb, f, V((0.05, BY - 2.6, 0)), FWD, spine=(5, 0, 0), head=(10, 5))
for f in (800, 860, 1068):
    for s_ in "LR":
        sg = -1 if s_ == "L" else 1
        hand(pb, s_, f, V((sg * 0.27, (BY - 1.0) if f == 800 else (BY - 2.6), 0.98)), (0, 0, -1), (-sg, 0, 0), grip=0.3)
# ---------------------------------------------------------------- STEWARD (runs up the aisle from the aft galley, pins, injects)
spath = catmull([(440, V((0.05, 8.0, 0))), (480, V((0.05, 5.4, 0))), (520, V((0.08, 3.0, 0))), (532, V((0.10, 2.80, 0)))])
stw.walk(spath, lambda f: 0.0, 440, 532, stride=0.95, lift=0.1, lean=14, bob=0.035)
swing(stw, spath, 440, 528, step=9, amp=0.16, period=30)
# holds two rows back while the attendant steps up to the bomber's head, then comes round her on the +x side
for f in (540, 560, 582):
    stand(stw, f, V((0.10, 2.80, 0)), 0, spine=(10, 0, 0), head=(15, 8 * math.sin(f * 0.05)), stance=0.14)
    for s_, sg in (("L", 1), ("R", -1)):
        hand(stw, s_, f, V((0.10 + sg * 0.26, 2.74, 0.90)), (0, -0.3, -1), (-sg, 0, 0), grip=0.3)
spath2 = catmull([(586, V((0.10, 2.80, 0))), (600, V((0.42, 2.15, 0))), (616, V((0.66, 1.62, 0)))])
stw.walk(spath2, lambda f: -80.0 * smooth((f - 590) / 26.0), 586, 616, stride=0.5, lift=0.06, lean=12)
swing(stw, spath2, 586, 612, step=8, amp=0.10, period=28)
for f in range(1, 441, 40):
    stand(stw, f, V((0.05, 8.0, 0)), 0, spine=(5, 0, 0), head=(5, 10 * math.sin(f * 0.02)))
    for s_, sg in (("L", 1), ("R", -1)):
        hand(stw, s_, f, V((0.05 + sg * 0.24, 8.0, 0.86)), (0, -0.2, -1), (-sg, 0, 0), grip=0.3)
stand(stw, 624, V((0.68, 1.45, 0)), -90, spine=(25, 0, 0), head=(20, 0), crouch=0.3, stance=0.14)   # stops beside his arm and lowers to a kneel
# kneels at the bomber's right side by his upper arm (beat 5) and injects
SK = V((0.68, BY + 1.28, 0))
for f in (640, 700, 768, 900, 1068):
    stw.key_root(f, V((SK.x, SK.y, 0.56)), yaw=-90, flex=10)
    stw.key_spine(f, flex=55, twist=0, head=(15, 0))
    stw.key_foot("L", f, V((SK.x + 0.38, SK.y + 0.14)), -90, 0.02, -65); stw.key_foot("R", f, V((SK.x + 0.40, SK.y - 0.16)), -90, 0.02, -65)
# upper-arm injection: left hand steadies the arm, right hand holds the syringe (thumb on plunger)
ev(700); UA = (bom.r.o.matrix_world @ bom.r.PB['upperarm02.R'].matrix).translation.copy() + V((0.0, 0.0, 0.05))   # bomber's right upper arm (evaluated)
print('UA', UA)
for f, dz in ((640, 0.25), (652, 0.18), (664, 0.09), (690, 0.07), (720, 0.07), (745, 0.2), (768, 0.3)):
    hand(stw, "R", f, UA + V((0.05, 0.0, dz + 0.10)), (-0.6, 0, -0.8), (0, 1, 0), grip=0.6)
    hand(stw, "L", f, UA + V((0.02, 0.22, 0.13)), (-1, 0, -0.3), (0, 0, -1), grip=0.45)
for f in (900, 1068):
    hand(stw, "R", f, V((SK.x - 0.12, SK.y + 0.22, 0.92)), (-0.2, 0, -1), (0, 1, 0), grip=0.4)
    hand(stw, "L", f, V((SK.x - 0.30, SK.y - 0.18, 0.62)), (-1, 0, -0.5), (0, 0, -1), grip=0.4)

# ---------------------------------------------------------------- PAX C (3D across the aisle) and PAX D (4A in front, reading)
for f in range(1, 1069, 20):
    if f < 380:
        sit(pc, f, SX["D"], BY, spine=(3, 0, 0), head=(5 + 3 * math.sin(f * 0.03), 0))
    elif f < 470:
        sit(pc, f, SX["D"], BY, spine=(0, 25, 3), head=(0, 30))            # turns to look across
    elif f < 770:
        sit(pc, f, SX["D"], BY, z=0.58, spine=(25, 35, 0), head=(20, 25 + 5 * math.sin(f * 0.1)))   # leans out to watch
    else:
        sit(pc, f, SX["D"], BY, spine=(4, 20, 0), head=(12, 30 + 5 * math.sin(f * 0.05)))          # sits back, still watching
for f in (1, 380):
    for s in "LR": rest_arm(pc, s, f, V((SX["D"], BY, 0.56)), grip=0.3)
hand(pc, "R", 470, V((SX["D"] - 0.15, BY + 0.6, 0.95)), (0, 0, 1), (0, -1, 0), grip=0.9)   # hand over her mouth-ish reaction
hand(pc, "L", 470, V((SX["D"] - 0.20, BY + 0.2, 0.66)), (-1, 0, -0.2), (0, 0, -1), grip=0.6)  # grips the armrest
for f in (770,):
    hand(pc, "R", f, V((SX["D"] + 0.08, BY + 0.30, 0.74)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
    hand(pc, "L", f, V((SX["D"] - 0.10, BY + 0.30, 0.74)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
for f in (500, 520):   # PaxC: right hand braced on her armrest while she leans out to watch
    hand(pc, "R", f, V((SX["D"] + 0.26, BY + 0.30, 0.80)), (0, 1, -0.3), (0, 0, -1), grip=0.35)
for f in range(1, 1069, 20):
    if f < 420:
        sit(pd, f, SX["A"], ROW(4), spine=(12, 0, 0), head=(25, 0))
    else:
        sit(pd, f, SX["A"], ROW(4), z=0.6, spine=(5, 60, 0), head=(5, 60))      # twists round over her shoulder
for f in (1, 420):
    hand(pd, "L", f, V((SX["A"] - 0.13, ROW(4) + 0.38, 0.86)), (0, 0.3, 1), (1, 0, 0), grip=0.5)   # holding a book
    hand(pd, "R", f, V((SX["A"] + 0.13, ROW(4) + 0.38, 0.86)), (0, 0.3, 1), (-1, 0, 0), grip=0.5)
for f in (446, 1068):   # book lowered to her lap as she twists round to look
    hand(pd, "L", f, V((SX["A"] - 0.12, ROW(4) + 0.24, 0.70)), (0, 1, -0.3), (0, 0, -1), grip=0.4)
    hand(pd, "R", f, V((SX["A"] + 0.06, ROW(4) + 0.26, 0.70)), (0, 1, -0.3), (0, 0, -1), grip=0.4)
for f in (1068, 1380):
    hand(pc, "R", f, V((SX["D"] + 0.08, BY + 0.30, 0.74)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
    hand(pc, "L", f, V((SX["D"] - 0.10, BY + 0.30, 0.74)), (0, 1, -0.3), (0, 0, -1), grip=0.3)
    sit(pd, f, SX["A"], ROW(4), z=0.6, spine=(5, 60, 0), head=(5, 60))
    hand(pd, "L", f, V((SX["A"] - 0.12, ROW(4) + 0.24, 0.70)), (0, 1, -0.3), (0, 0, -1), grip=0.4)
    hand(pd, "R", f, V((SX["A"] + 0.06, ROW(4) + 0.26, 0.70)), (0, 1, -0.3), (0, 0, -1), grip=0.4)
print("PAX_DONE")

# ================================================================== AIRPORT (beat 9). Traveller + officer + walkers
# traveller stands at the belt (side of the belt, -Y side, facing +Y), takes off sneakers, puts them in the tray
TP = AX + V((-1.2, -0.75, 0))
for f in range(1, 1380, 60):
    stand(trav, f, TP, FWD, spine=(5, 0, 0))
for f, flex, sp, crouch, hd in ((1393, 0, 10, 0.0, (25, 0)), (1420, 0, 18, 0.03, (35, 5)), (1440, 0, 20, 0.04, (35, 0)), (1455, 5, 30, 0.15, (30, 0)),
                               (1468, 15, 46, 0.50, (-35, 0)), (1480, 15, 48, 0.52, (-38, 5)), (1500, 5, 20, 0.12, (20, 0))):
    trav.key_root(f, V((TP.x, TP.y + (0.05 if f >= 1455 else 0), trav.root_head.z - 0.02 - crouch)), yaw=FWD, flex=flex)
    trav.key_spine(f, flex=sp, head=hd)
    trav.key_foot("L", f, trav.foot_xy("L", TP, FWD), FWD)
# right foot: steps back out of the sneaker (1425-1445; the sneaker stays on the floor), then plants beside it
RF0 = trav.foot_xy("R", TP, FWD)
for f, dy, lift, pitch in ((1393, 0, 0, 0), (1425, 0, 0, 0), (1435, -0.10, 0.04, 20), (1445, -0.22, 0.0, 0), (1520, -0.22, 0.0, 0)):
    trav.key_foot("R", f, RF0 + V((0.06 if f >= 1445 else 0, dy)), FWD, lift, pitch)
# right hand: down to the sneaker heel on the floor (1478), lifts it over the tray (1500-1515), lets go (1520)
TRAY = bpy.data.objects["Tray_1"]
ev(1430); trf = wpos(trav, "foot.R", 1430)
SHOE_PICK = V((trf.x + 0.02, trf.y - 0.04, 0.19))
hand(trav, "R", 1393, TP + V((0.29, 0.10, 0.95)), (0, 0.3, -1), (-1, 0, 0), grip=0.3)
hand(trav, "L", 1393, TP + V((-0.29, 0.10, 0.95)), (0, 0.3, -1), (1, 0, 0), grip=0.3)
hand(trav, "L", 1440, TP + V((-0.12, 0.42, 0.82)), (0, 1, -0.5), (0, 0, -1), grip=0.3)          # steadies on the belt edge
hand(trav, "L", 1480, TP + V((-0.22, 0.30, 0.55)), (0, 1, -0.5), (0, 0, -1), grip=0.3)         # on his knee in the squat
hand(trav, "R", 1455, SHOE_PICK + V((0, 0, 0.18)), (0, 0.3, -1), (-1, 0, 0), grip=0.3)
hand(trav, "R", 1478, SHOE_PICK, (0, 0.3, -1), (-1, 0, 0), grip=0.8)
hand(trav, "R", 1500, V((TP.x + 0.15, TP.y + 0.45, 0.95)), (0, 0.6, -0.8), (-1, 0, 0), grip=0.8)
hand(trav, "R", 1515, V((TP.x + 0.35, TP.y + 0.70, 0.98)), (0, 0.6, -0.8), (-1, 0, 0), grip=0.8)
hand(trav, "R", 1520, V((TP.x + 0.36, TP.y + 0.72, 0.99)), (0, 0.6, -0.8), (-1, 0, 0), grip=0.2)
print("SHOE_PICK", SHOE_PICK)
# straightens in socks, watches the tray roll into the X-ray, small shrug (1560-1620)
for f, sp, hd in ((1560, 5, (5, 10)), (1590, 0, (0, 30)), (1620, -2, (-3, 35))):
    stand(trav, f, TP, FWD, spine=(sp, 0, 0), head=hd)
    hand(trav, "R", f, TP + V((0.29, 0.10, 0.95)), (0, 0.2, -1), (-1, 0, 0), grip=0.3)
    hand(trav, "L", f, TP + V((-0.29, 0.10, 0.95)), (0, 0.2, -1), (1, 0, 0), grip=0.3)
# tray rides the belt into the tunnel
for f, x in ((1, -0.85), (1500, -0.85), (1530, -0.85), (1620, 1.4)):
    TRAY.location = AX + V((x, 0.0, 0.80)); TRAY.keyframe_insert("location", frame=f)
for o in bpy.data.objects:
    if o.name.startswith("Tray_") and o.name != "Tray_1":
        x0 = o.location.x
        for f in (1, 1393): o.location.x = x0; o.keyframe_insert("location", frame=f)
        o.location.x = x0 + 1.8; o.keyframe_insert("location", frame=END)
# officer at the monitor, leaning, head moving
for f in range(1, END + 1, 40):
    stand(off, f, AX + V((4.5, 2.05, 0)), 0, spine=(18 + 3 * math.sin(f * 0.05), 0, 0), head=(15, 8 * math.sin(f * 0.03)))
    hand(off, "R", f, AX + V((4.72, 1.66, 0.85)), (0, -1, -0.3), (0, 0, -1), grip=0.4)
    hand(off, "L", f, AX + V((4.22, 1.66, 0.85)), (0, -1, -0.3), (0, 0, -1), grip=0.4)
# PaxC and PaxD become airport extras after the cabin is gone: queue + walk-by (teleport at 1380, hidden by the cloud dive)
def teleport_keys(h, f):
    """make every key on this rig at f constant so the jump at f+1 is instant"""
    ad = h.r.o.animation_data
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:
                        if int(round(kp.co.x)) == f: kp.interpolation = 'CONSTANT'
for h in (pc, pd):
    for f in (1068,): pass
wpath = catmull([(1381, AX + V((-6.0, -3.2, 0))), (1500, AX + V((-1.5, -3.0, 0))), (1620, AX + V((3.0, -2.9, 0)))])
sit(pc, 1380, SX["D"], BY, z=0.58, spine=(25, 35, 0), head=(20, 25))
pc.walk(wpath, lambda f: -90.0, 1381, END, stride=0.7)
for f in range(1381, END + 1, 20):
    p = wpath(f)
    for s in "LR":
        sg = -1 if s == "L" else 1
        hand(pc, s, f, V((p.x - 0.0, p.y + sg * 0.22 * (1 if True else 1), 0.82)), (0, 0, -1), (sg, 0, 0), grip=0.3)
sit(pd, 1380, SX["A"], ROW(4), z=0.6, spine=(5, 60, 0), head=(5, 60))
QP = AX + V((-3.0, -1.3, 0))
for f in range(1381, END + 1, 40):
    stand(pd, f, QP, FWD - 90 + 10 * math.sin(f * 0.02), spine=(3, 0, 0), head=(5, 20 * math.sin(f * 0.03)))
    hand(pd, "R", f, QP + V((0.0, -0.31, 0.86)), (0, 0, -1), (1, 0, 0), grip=0.3)
    hand(pd, "L", f, QP + V((0.0, 0.31, 0.86)), (0, 0, -1), (-1, 0, 0), grip=0.3)
for h in (pa, pb, stw, att):
    for b_ in ("root", "IK_foot.L", "IK_foot.R", "IK_hand.L", "IK_hand.R", "Pole_knee.L", "Pole_knee.R"):
        pass
for h in (pc, pd):
    teleport_keys(h, 1380)
print("AIRPORT_DONE")


# ================================================================== sleepers under blankets (cabin background life)
SLEEP = (("Sleeper1", 6, "E", "Blanket_6F", 1), ("Sleeper2", 1, "F", "Blanket_1E", -1), ("Sleeper3", 7, "B", "Blanket_8D", 1), ("Sleeper4", 2, "A", "Blanket_5A", 1))
for nm, ri, k, bl, lean in SLEEP:
    h = HS[nm]; x, y = SX[k], ROW(ri)
    ph = random.uniform(0, 6)
    for f in range(1, END + 1, 30):
        t = f / 60.0
        sit(h, f, x, y, flex=-4, spine=(-4 + 1.2 * math.sin(t * 1.3 + ph), 0, 6 * lean), head=(25 + 3 * math.sin(t * 0.9 + ph), 25 * lean))
    for f in (1, END):
        for s_ in "LR": rest_arm(h, s_, f, V((x, y, 0.56)), out=0.18, fwd=0.32, z=0.24, grip=0.25)
    b = bpy.data.objects[bl]; b.location = V((x, y + 0.22, 0.66)); b.rotation_euler = (math.radians(-6), 0, math.radians(random.uniform(-8, 8)))
    b.scale = (1.0, 1.25, 1.0)
bpy.data.objects["Blanket_2C"].location = V((SX["C"], ROW(9) + 0.05, 0.52))
# tray table knocked loose in the tackle: flies into the aisle, tumbles, lands
tt = bpy.data.objects["TrayTable"]; t0 = tt.location.copy()
for f, p_, r in ((1, t0, (0, 0, 0)), (512, t0, (0, 0, 0)), (522, t0 + V((0.25, 0.25, 0.25)), (40, 30, 60)), (532, V((0.15, 0.95, 0.5)), (120, 70, 140)),
                 (540, V((0.22, 1.25, 0.03)), (180, 85, 200)), (548, V((0.26, 1.32, 0.012)), (180, 90, 215))):
    tt.location = p_; tt.rotation_euler = [math.radians(v) for v in r]; tt.keyframe_insert("location", frame=f); tt.keyframe_insert("rotation_euler", frame=f)
# airport queue: four cabin cast members become travellers in line once the cabin is gone (switch hidden in the cloud dive)
QUEUE = ((pa, AX + V((-3.6, -2.1, 0)), 90), (pb, AX + V((-4.4, -2.15, 0)), 95), (stw, AX + V((-5.4, -2.0, 0)), 85), (att, AX + V((-6.2, -2.1, 0)), 92))
for h, qp, yaw in QUEUE:
    ev(1380)
    for f in range(1381, END + 1, 30):
        stand(h, f, qp + V(((f - 1381) * 0.0012, 0, 0)), yaw + 6 * math.sin(f * 0.02), spine=(4, 0, 0), head=(5, 25 * math.sin(f * 0.015 + qp.x)))
        for s_ in "LR":
            sg = -1 if s_ == "L" else 1
            hand(h, s_, f, qp + V((sg * 0.05, sg * -0.31, 0.88)), (0, 0, -1), (0, sg, 0), grip=0.35)
# ================================================================== reach fix: slide bodies so keyed hand targets are actually reached
def key_frames(h, bone):
    ad = h.r.o.animation_data; out = set()
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    if ('"%s"' % bone) in fc.data_path: out |= {int(round(k.co.x)) for k in fc.keyframe_points}
    return sorted(out)
def shift(h, f, d, feet=True):
    names = ["root"] + (["IK_foot.L", "IK_foot.R", "Pole_knee.L", "Pole_knee.R"] if feet else [])
    for n in names:
        pb = h.r.PB[n]; ks = key_frames(h, n)
        if f not in ks: continue
        ev(f)
        pb.location = pb.location + h.r.rest(n).to_3x3().inverted() @ d
        pb.keyframe_insert("location", frame=f, group=n)
def reach_fix(h, f0, f1, feet=True, maxd=0.4, tol=0.02):
    fr = [f for f in key_frames(h, "IK_hand.L") + key_frames(h, "IK_hand.R") if f0 <= f <= f1]
    for f in sorted(set(fr)):
        if f not in key_frames(h, "root"): continue
        tot = V((0, 0, 0))
        for it in range(4):
            ev(f); M = h.r.o.matrix_world; ds = []
            for s in "LR":
                t = (M @ h.r.PB["IK_hand." + s].matrix).translation; w = (M @ h.r.PB["wrist." + s].matrix).translation
                e = t - w
                if e.length > tol: ds.append(e)
            if not ds: break
            d = sum(ds, V((0, 0, 0))) / len(ds); d.z = 0.0
            if (tot + d).length > maxd: d = d.normalized() * max(0.0, maxd - tot.length)
            if d.length < 0.005: break
            shift(h, f, d, feet); tot += d
for h, a_, b_ in ((att, 420, 1068), (pa, 440, 1068), (pb, 440, 1068)):
    reach_fix(h, a_, b_)
reach_fix(stw, 540, 1068, maxd=0.15)
reach_fix(off, 1393, END, feet=False, maxd=0.2)
reach_fix(trav, 1393, END, feet=False, maxd=0.25)
for h in (pa, pb, stw, att):
    # hold the last cabin pose until 1380, then jump (constant)
    ad = h.r.o.animation_data
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    ks = [k for k in fc.keyframe_points if k.co.x <= 1068]
                    if ks:
                        last = max(ks, key=lambda k: k.co.x)
                        fc.keyframe_points.insert(1380, last.co.y).interpolation = 'CONSTANT'
                    fc.update()
print("REACH_FIXED")

# ================================================================== hand limits (client, Nov 11 23:00): no backward or over-range bends
import math as _m
for h in HS.values():
    for s_ in "LR":
        for k in range(1, 6):
            for j in range(1, 4):
                pbn = h.r.PB["finger%d-%d.%s" % (k, j, s_)]
                c = pbn.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'
                c.use_limit_x = c.use_limit_y = c.use_limit_z = True
                if k == 1:
                    c.min_x, c.max_x = _m.radians(-30), _m.radians(60); c.min_y, c.max_y = _m.radians(-40), _m.radians(40); c.min_z, c.max_z = _m.radians(-60), _m.radians(60)
                else:
                    c.min_x, c.max_x = 0.0, _m.radians(100); c.min_y, c.max_y = _m.radians(-10), _m.radians(10); c.min_z, c.max_z = _m.radians(-10), _m.radians(10)
        wb = h.r.PB["wrist." + s_]
        c = wb.constraints.new('LIMIT_ROTATION'); c.owner_space = 'LOCAL'; c.use_limit_x = c.use_limit_z = True
        c.min_x, c.max_x = _m.radians(-60), _m.radians(60); c.min_z, c.max_z = _m.radians(-25), _m.radians(25)
print("HAND_LIMITS")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_SAVED", OUT)
