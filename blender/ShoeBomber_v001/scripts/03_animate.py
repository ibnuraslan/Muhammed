"""ShoeBomber character + prop animation. blender -b scene.blend --python 03_animate.py -- <out_anim.blend>
Uses blender/pipeline/anim_lib.py (MPFB IK control rig, Human helpers)."""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "../../pipeline/anim_lib.py")).read())
OUT = sys.argv[sys.argv.index("--") + 1:][0]
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
HN = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Traveller", "Officer"]
HS = {n: setup(n) for n in HN}
print("RIGS_READY")

# ------------------------------------------------------------------ pose helpers
FINGERS = [("finger%d-%d" % (k, j)) for k in range(2, 6) for j in range(1, 4)]
def curl(h, s, f, amt, thumb=None):
    """amt 0 open .. 1 fist (local X bend)"""
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

def rest_arm(h, s, f, root, yaw=FWD, out=0.22, fwd=0.28, z=0.12, grip=0.3):
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
def bomber_hunch(f, lean=38, head=(28, 0), foot_up=0.30, twist=-8, hx=0.0):
    bom.key_root(f, V((BX + 0.02, BY - 0.03, 0.56)), yaw=FWD, flex=10, side=-3)
    bom.key_spine(f, flex=lean, twist=twist, side=4, head=head)
    bom.key_foot("L", f, V((BX - 0.12, BY + 0.44)), FWD, 0, 0)
    bom.key_foot("R", f, V((BX + 0.13, BY + 0.30)), FWD + 10, foot_up, 15)   # heel up near the cushion edge

for f, lean, hd, tw in ((1, 36, (26, -4), -8), (40, 40, (30, 2), -10), (90, 42, (34, -2), -12), (150, 40, (30, 4), -9), (200, 38, (26, 0), -8)):
    bomber_hunch(f, lean, hd, twist=tw)
# shoe-holding left hand and match hand: placed relative to the right ankle (evaluated after the feet are keyed)
def shoe_pt(f, dx=0.0, dy=0.0, dz=0.0):
    a = wpos(bom, "foot.R", f); return a + V((dx, dy, dz))
for f in (1, 40, 90, 150, 200, 260, 330, 372):
    a = shoe_pt(f)
    hand(bom, "L", f, a + V((-0.09, 0.08, 0.05)), (0.3, 0.6, -0.6), (1, 0, 0), pole=(BX - 0.6, BY - 0.2, 0.6), grip=0.65)
# right hand: strike (f10-28 swipe along the box held in the left hand), then hold the match flame to the tongue
strike = [(1, V((0.10, 0.02, 0.16))), (14, V((0.06, 0.06, 0.14))), (22, V((0.13, -0.04, 0.12))), (30, V((0.07, 0.10, 0.13))),
          (60, V((0.03, 0.08, 0.10))), (90, V((0.02, 0.09, 0.08))), (120, V((0.04, 0.07, 0.09))), (150, V((0.02, 0.10, 0.08))),
          (200, V((0.03, 0.08, 0.09))), (260, V((0.03, 0.09, 0.08))), (330, V((0.02, 0.09, 0.09))), (372, V((0.03, 0.08, 0.08))),
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
hand(bom, "L", 420, shoe_pt(420) + V((-0.09, 0.08, 0.05)), (0.3, 0.6, -0.6), (1, 0, 0), pole=(BX - 0.6, BY - 0.2, 0.6), grip=0.65)
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
# 580: hits the floor (impact, slight bounce at 590), pinned at 600+
for f, z, fl in ((578, 0.20, 92), (586, 0.24, 90), (596, 0.205, 91), (654, 0.205, 91), (700, 0.2, 91), (768, 0.2, 91)):
    bom.key_root(f, V((0.0, BY + 0.75, z)), yaw=FWD, flex=fl, side=0)
    bom.key_spine(f, flex=-8 if f < 655 else -4, twist=-5, head=(-25, 35) if f < 700 else (-15, 45))
    bom.key_foot("L", f, V((-0.11, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.11, BY - 0.27)), FWD, 0.03, -75)
# struggle wiggle while pinned (beat 4 end, beat 5 start), then limp (sedated ~ 720)
for f in range(600, 721, 12):
    w = 1.0 if f < 690 else max(0.0, (720 - f) / 30)
    bom.key_root(f, V((0.0 + 0.03 * w * math.sin(f), BY + 0.75, 0.205 + 0.02 * w * abs(math.sin(f * 0.7)))), yaw=FWD + 4 * w * math.sin(f * 0.5), flex=91, side=6 * w * math.sin(f * 0.9))
    bom.key_spine(f, flex=-8 + 4 * w * math.sin(f * 0.3), twist=-5 + 8 * w * math.sin(f * 0.6), head=(-25 + 15 * (1 - w), 35 + 10 * (1 - w)))
# arms when pinned: left arm twisted behind his back (held by PaxB), right arm out forward on the floor (held by attendant / injected)
for f in (582, 654, 720, 768, 830, 1068):
    hand(bom, "L", f, V((-0.08, BY + 0.55, 0.42)), (1, 0, 0.1), (0, 0, 1), pole=(-0.6, BY + 0.6, 0.6), grip=0.5)
    hand(bom, "R", f, V((0.12, BY + 1.75, 0.06)), (0.05, 1, -0.1), (0, 0, -1), pole=(0.6, BY + 1.0, 0.4), grip=0.6 if f < 720 else 0.15)
# after sedation he lies still; tiny breathing
for f in range(780, 1069, 30):
    bom.key_root(f, V((0.0, BY + 0.75, 0.2 + 0.004 * math.sin(f * 0.1))), yaw=FWD, flex=91, side=0)
    bom.key_spine(f, flex=-4, twist=-5, head=(-10, 45))
    bom.key_foot("L", f, V((-0.11, BY - 0.25)), FWD, 0.03, -75); bom.key_foot("R", f, V((0.11, BY - 0.27)), FWD, 0.03, -75)
print("BOMBER_DONE")

# ---------------------------------------------------------------- ATTENDANT (from the front galley, pushing the trolley toward -Y)
# beat 2: walks behind the trolley (y 7.6 -> 2.3), stops ~ f300, sniffs (head up, turns left toward row 3 at f330)
apath = catmull([(170, V((0.0, 7.9, 0))), (230, V((0.0, 5.6, 0))), (300, V((0.0, 3.0, 0))), (318, V((0.0, 2.85, 0)))])
att.walk(apath, lambda f: 0.0, 170, 318, stride=0.62, lift=0.06, lean=8)
for s in "LR":    # hands on the trolley handle while walking
    sg = 1 if s == "L" else -1     # facing -Y: her left is +X
    for f in range(170, 319, 10):
        p = apath(f)
        hand(att, s, f, V((p.x + sg * 0.16, p.y - 0.36, 0.98)), (0, -1, -0.2), (0, 0, -1), grip=0.7)
TROLLEY = bpy.data.objects["Trolley"]
for f in range(170, 319, 6):
    p = apath(f); TROLLEY.location = V((0, p.y - 0.75, 0.52)); TROLLEY.keyframe_insert("location", frame=f)
for f in (1,):
    TROLLEY.location = V((0, 7.9 - 0.75, 0.52)); TROLLEY.keyframe_insert("location", frame=f)
for f, y in ((372, 2.10), (470, 2.10), (500, 2.9), (530, 3.35), (560, 3.45)):
    TROLLEY.location = V((0.02 * (f > 470), y, 0.52)); TROLLEY.keyframe_insert("location", frame=f)
# stop + sniff + turn
stand(att, 330, apath(318), 0, spine=(-6, 0, 0), head=(-14, 0))           # nose up, sniff
stand(att, 350, apath(318), 0, spine=(-4, 0, 0), head=(-10, -20))
stand(att, 372, V((0.0, 2.8, 0)), -25, spine=(4, -20, 0), head=(6, -25))   # turns toward row 3 (to her right)
for s in "LR":
    sg = 1 if s == "L" else -1
    hand(att, s, 330, V((sg * 0.16, 2.85 - 0.36, 0.98)), (0, -1, -0.2), (0, 0, -1), grip=0.7)
hand(att, "R", 372, V((-0.25, 2.55, 1.05)), (0, -1, 0), (1, 0, 0), grip=0.3)
hand(att, "L", 372, V((0.2, 2.6, 0.95)), (0, -1, -0.2), (0, 0, -1), grip=0.7)
# beat 3 (373-480): she steps to row 3, leans over seat C looking at him: "caught"
for f, y, yaw, sp, hd in ((400, 1.3, -50, (18, -15, 0), (10, -20)), (430, 0.55, -80, (25, -15, 5), (14, -15)), (470, 0.45, -85, (30, -10, 5), (16, -10))):
    stand(att, f, V((0.1, y, 0)), yaw, spine=sp, head=hd, stance=0.12)
hand(att, "L", 430, V((-0.45, 0.25, 1.1)), (-1, 0, -0.3), (0, 0, -1), grip=0.6)       # left hand on the seat-back top (seat 3C headrest)
hand(att, "R", 430, V((-0.6, 0.5, 1.0)), (-1, 0, 0.2), (0, 0, -1), grip=0.2)
hand(att, "L", 470, V((-0.45, 0.25, 1.1)), (-1, 0, -0.3), (0, 0, -1), grip=0.6)
hand(att, "R", 470, V((-0.7, 0.45, 0.95)), (-1, 0, 0.1), (0, 0, -1), grip=0.2)
# beat 4: grabs his right wrist (f490), pulls into the aisle, kneels at his head pinning the right arm
ev(495); wr = wpos(bom, "wrist.R", 495)
hand(att, "R", 492, wr + V((0.03, 0, 0.03)), (-1, 0, -0.2), (0, 0, -1), grip=0.85)
hand(att, "L", 492, wr + V((0.10, 0.04, 0.02)), (-1, 0.2, 0), (0, 0, -1), grip=0.85)
stand(att, 492, V((0.15, 0.45, 0)), -90, spine=(25, 0, 0), head=(10, 0), crouch=0.1, stance=0.18)
stand(att, 525, V((0.12, 0.75, 0)), -60, spine=(30, 15, 0), head=(15, 0), crouch=0.15, stance=0.2)
# kneel at his head (y ~ BY+2.0), facing -Y, holding his outstretched right forearm
for f in (590, 654, 720, 760):
    att.key_root(f, V((0.15, BY + 2.05, 0.52)), yaw=0, flex=12)
    att.key_spine(f, flex=30, twist=-5, head=(25, 0))
    att.key_foot("L", f, V((0.28, BY + 2.4)), 0, 0.02, -65); att.key_foot("R", f, V((0.02, BY + 2.45)), 0, 0.02, -65)
    hand(att, "R", f, V((0.12, BY + 1.62, 0.12)), (0, -1, -0.4), (0, 0, -1), grip=0.8)
    hand(att, "L", f, V((0.16, BY + 1.35, 0.14)), (0, -1, -0.4), (0, 0, -1), grip=0.8)
# beat 6 (769-1068): goes to his feet, kneels, pulls both sneakers off and lifts them under the reading light
for f, pos, sp in ((800, V((0.25, BY + 0.9, 0)), (20, 40, 0)), (830, V((0.22, BY - 0.15, 0)), (25, 10, 0))):
    stand(att, f, pos, 120 if f == 800 else 160, spine=sp, head=(15, 0), crouch=0.05, stance=0.1)
KN = V((0.05, BY - 0.85, 0))          # kneeling spot behind his feet, facing +Y
for f in (850, 880, 940, 1000, 1068):
    att.key_root(f, V((KN.x, KN.y, 0.55 if f < 900 else 0.62)), yaw=FWD, flex=8)
    att.key_spine(f, flex=25 if f < 900 else 5, twist=0, head=(25, 0) if f < 900 else (5, 0))
    att.key_foot("L", f, V((KN.x - 0.12, KN.y - 0.35)), FWD, 0.02, -65); att.key_foot("R", f, V((KN.x + 0.14, KN.y - 0.33)), FWD, 0.02, -65)
# grasp the heels (870), pull off (880-900), lift up together (900-960), turn the soles to the light (960-1068)
ev(870); hl = wpos(bom, "foot.L", 870); hr = wpos(bom, "foot.R", 870)
hand(att, "L", 870, hl + V((-0.06, -0.05, 0.08)), (0.2, 1, -0.3), (1, 0, 0), grip=0.75)
hand(att, "R", 870, hr + V((0.06, -0.05, 0.08)), (-0.2, 1, -0.3), (-1, 0, 0), grip=0.75)
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
hand(pa, "R", 470, V((SX["C"] - 0.55, BY + 0.25, 0.95)), (-1, 0, 0), (0, 0, -1), grip=0.8)    # grabs the bomber's shoulder/arm
hand(pa, "L", 470, V((SX["C"] - 0.5, BY + 0.10, 0.78)), (-1, 0, -0.2), (0, 0, -1), grip=0.8)
# stands half up, pushes him into the aisle (follows the bomber's back)
stand(pa, 525, V((-0.25, BY + 0.30, 0)), FWD - 40, flex=10, spine=(35, -10, 0), head=(20, -10), crouch=0.35)
hand(pa, "R", 525, V((-0.65, BY + 0.30, 1.0)), (1, 0.4, 0), (0, 0, -1), grip=0.8)
hand(pa, "L", 525, V((-0.80, BY + 0.10, 0.9)), (1, 0.2, 0), (0, 0, -1), grip=0.8)
# kneels in the aisle by the bomber's left side, both hands on his shoulder blades
for f in (585, 654, 720, 768):
    pa.key_root(f, V((-0.05, BY + 0.05, 0.58)), yaw=FWD + 20, flex=10)
    pa.key_spine(f, flex=40 if f < 720 else 20, twist=5, head=(30, 0) if f < 720 else (10, 20))
    pa.key_foot("L", f, V((-0.25, BY - 0.35)), FWD + 20, 0.02, -65); pa.key_foot("R", f, V((0.12, BY - 0.40)), FWD + 20, 0.02, -65)
    hand(pa, "L", f, V((-0.10, BY + 1.05, 0.33)), (0.1, 1, -0.6), (0, 0, -1), grip=0.3)
    hand(pa, "R", f, V((0.12, BY + 1.0, 0.33)), (-0.1, 1, -0.6), (0, 0, -1), grip=0.3)

# ---------------------------------------------------------------- PAX B (2C behind, aisle seat; stands, pins the left arm / legs)
for f in range(1, 470, 20):
    sit(pb, f, SX["C"], ROW(2), spine=(8, 0, 0), head=(20 + 3 * math.sin(f * 0.04), -5))
for s in "LR": rest_arm(pb, s, 1, V((SX["C"], ROW(2), 0.56)), fwd=0.38, z=0.2, grip=0.6)     # phone in hands
for s in "LR": rest_arm(pb, s, 400, V((SX["C"], ROW(2), 0.56)), fwd=0.38, z=0.2, grip=0.6)
sit(pb, 440, SX["C"], ROW(2), spine=(2, 15, 0), head=(-5, 20))      # looks up at the commotion
stand(pb, 500, V((0.0, ROW(2) + 0.1, 0)), FWD, spine=(10, 0, 0), head=(5, 0))
stand(pb, 545, V((0.0, ROW(2) + 0.3, 0)), FWD, spine=(30, 0, 0), head=(20, 0), crouch=0.15, stance=0.15)
for f in (590, 654, 720, 768):     # kneels on his legs side, holds the twisted left arm behind his back
    pb.key_root(f, V((0.14, BY - 0.55, 0.57)), yaw=FWD - 15, flex=10)
    pb.key_spine(f, flex=45 if f < 720 else 25, twist=-8, head=(30, 0) if f < 720 else (10, -10))
    pb.key_foot("L", f, V((0.02, BY - 0.95)), FWD - 15, 0.02, -65); pb.key_foot("R", f, V((0.32, BY - 0.92)), FWD - 15, 0.02, -65)
    hand(pb, "L", f, V((-0.02, BY + 0.5, 0.48)), (0, 1, -0.4), (0, 0, -1), grip=0.85)
    hand(pb, "R", f, V((0.12, BY + 0.2, 0.3)), (0, 1, -0.6), (0, 0, -1), grip=0.85)

stand(pa, 800, V((-0.70, BY + 0.38, 0)), 70, spine=(10, 0, 0), head=(15, -20), crouch=0.25)
for f in (850, 950, 1068):
    stand(pa, f, V((-0.72, BY + 0.38, 0)), 70, spine=(12, 5, 0), head=(18, -10 + 10 * math.sin(f)), crouch=0.25)
for f in (800, 1068):
    hand(pa, "R", f, V((-0.55, BY + 0.62, 1.05)), (0.3, 0, -1), (0, 1, 0), grip=0.7)   # hand on the seat-back top
    hand(pa, "L", f, V((-0.80, BY + 0.10, 0.85)), (0, 0, -1), (1, 0, 0), grip=0.3)
stand(pb, 790, V((0.08, BY - 1.0, 0)), FWD, spine=(15, 0, 0), head=(20, 0), crouch=0.1)
pbp = catmull([(795, V((0.08, BY - 1.0, 0))), (860, V((0.05, BY - 2.6, 0)))])
pb.walk(pbp, lambda f: FWD, 795, 860, stride=0.5, lean=-4)
for f in (900, 1068):
    stand(pb, f, V((0.05, BY - 2.6, 0)), FWD, spine=(5, 0, 0), head=(10, 5))
for f in (800, 860, 1068):
    for s_ in "LR":
        sg = -1 if s_ == "L" else 1
        hand(pb, s_, f, V((sg * 0.22, (BY - 1.0) if f == 800 else (BY - 2.6), 0.85)), (0, 0, -1), (-sg, 0, 0), grip=0.3)
# ---------------------------------------------------------------- STEWARD (runs up the aisle from the aft galley, pins, injects)
spath = catmull([(440, V((0.0, -3.6, 0))), (480, V((0.0, -2.6, 0))), (530, V((0.0, -1.6, 0)))])
stw.walk(spath, lambda f: 180.0, 440, 530, stride=1.0, lift=0.1, lean=14, bob=0.035)
for f in range(1, 441, 40):
    stand(stw, f, V((0.0, -3.6, 0)), 180, spine=(5, 0, 0), head=(5, 10 * math.sin(f * 0.02)))
for s in "LR":
    for f in (1, 440, 530):
        p = spath(f); sg = -1 if s == "L" else 1
        hand(stw, s, f, V((p.x + sg * 0.25, p.y + 0.12, 0.95)), (0, 0.3, -1), (sg, 0, 0), grip=0.4)
# kneels at the bomber's right side by his upper arm (beat 5) and injects
SK = V((0.45, BY + 1.25, 0))
for f in (575, 640, 700, 768, 900, 1068):
    stw.key_root(f, V((SK.x, SK.y, 0.56)), yaw=-90, flex=10)
    stw.key_spine(f, flex=35, twist=0, head=(25, 0))
    stw.key_foot("L", f, V((SK.x + 0.38, SK.y + 0.14)), -90, 0.02, -65); stw.key_foot("R", f, V((SK.x + 0.40, SK.y - 0.16)), -90, 0.02, -65)
# upper-arm injection: left hand steadies the arm, right hand holds the syringe (thumb on plunger)
UA = V((0.22, BY + 1.18, 0.2))                           # bomber's right upper arm (approx, measured in audit)
for f, dz in ((575, 0.25), (640, 0.18), (660, 0.09), (690, 0.07), (720, 0.07), (745, 0.2), (768, 0.3)):
    hand(stw, "R", f, UA + V((0.05, 0.0, dz + 0.06)), (-0.6, 0, -0.8), (0, 1, 0), grip=0.75)
    hand(stw, "L", f, UA + V((0.02, 0.22, 0.08)), (-1, 0, -0.3), (0, 0, -1), grip=0.6)
for f in (900, 1068):
    hand(stw, "R", f, V((SK.x - 0.05, SK.y, 0.75)), (-0.2, 0, -1), (0, 1, 0), grip=0.6)
    hand(stw, "L", f, V((SK.x - 0.25, SK.y - 0.1, 0.32)), (-1, 0, -0.5), (0, 0, -1), grip=0.5)

# ---------------------------------------------------------------- PAX C (3D across the aisle) and PAX D (4A in front, reading)
for f in range(1, 1069, 20):
    if f < 380:
        sit(pc, f, SX["D"], BY, spine=(3, 0, 0), head=(5 + 3 * math.sin(f * 0.03), 0))
    elif f < 470:
        sit(pc, f, SX["D"], BY, spine=(0, 25, 3), head=(0, 30))            # turns to look across
    else:
        sit(pc, f, SX["D"], BY, z=0.58, spine=(25, 35, 0), head=(20, 25 + 5 * math.sin(f * 0.1)))   # leans out to watch
for f in (1, 380):
    for s in "LR": rest_arm(pc, s, f, V((SX["D"], BY, 0.56)), grip=0.3)
hand(pc, "R", 470, V((SX["D"] - 0.15, BY + 0.6, 0.95)), (0, 0, 1), (0, -1, 0), grip=0.9)   # hand over her mouth-ish reaction
hand(pc, "L", 470, V((SX["D"] - 0.30, BY + 0.2, 0.62)), (-1, 0, -0.2), (0, 0, -1), grip=0.8)  # grips the armrest
for f in range(1, 1069, 20):
    if f < 420:
        sit(pd, f, SX["A"], ROW(4), spine=(12, 0, 0), head=(25, 0))
    else:
        sit(pd, f, SX["A"], ROW(4), z=0.6, spine=(5, 60, 0), head=(5, 60))      # twists round over her shoulder
for f in (1, 420):
    hand(pd, "L", f, V((SX["A"] - 0.1, ROW(4) + 0.33, 0.85)), (0, 0.3, 1), (1, 0, 0), grip=0.5)   # holding a book
    hand(pd, "R", f, V((SX["A"] + 0.1, ROW(4) + 0.33, 0.85)), (0, 0.3, 1), (-1, 0, 0), grip=0.5)
print("PAX_DONE")

# ================================================================== AIRPORT (beat 9). Traveller + officer + walkers
# traveller stands at the belt (side of the belt, -Y side, facing +Y), takes off sneakers, puts them in the tray
TP = AX + V((-1.2, -0.75, 0))
for f in range(1, 1380, 60):
    stand(trav, f, TP, FWD, spine=(5, 0, 0))
for f, flex, sp, crouch in ((1393, 0, (10, 0, 0), 0.0), (1420, 0, (25, 0, 0), 0.05), (1450, 0, (55, 0, 0), 0.12), (1480, 0, (60, 0, 0), 0.15)):
    trav.key_root(f, V((TP.x, TP.y, trav.root_head.z - 0.02 - crouch)), yaw=FWD, flex=flex)
    trav.key_spine(f, flex=sp[0], head=(15, 0))
    trav.key_foot("L", f, trav.foot_xy("L", TP, FWD), FWD)
    trav.key_foot("R", f, trav.foot_xy("R", TP, FWD) + V((0, 0.0)), FWD, 0.0 if f < 1440 else 0.08)
# right foot lifts out of the shoe (heel pulled by the right hand), shoe goes into the tray
TRAY = bpy.data.objects["Tray_1"]
ev(1440); trf = wpos(trav, "foot.R", 1440)
hand(trav, "R", 1393, TP + V((0.25, 0.0, 0.95)), (0, 0.3, -1), (-1, 0, 0), grip=0.3)
hand(trav, "L", 1393, TP + V((-0.25, 0.0, 0.95)), (0, 0.3, -1), (1, 0, 0), grip=0.3)
hand(trav, "R", 1440, trf + V((0.03, 0.08, 0.10)), (0, -0.2, -1), (-1, 0, 0), grip=0.75)
hand(trav, "L", 1440, TP + V((-0.12, 0.45, 0.8)), (0, 1, -0.5), (0, 0, -1), grip=0.3)          # steadies on the belt edge
for f, z in ((1470, 0.45), (1500, 0.82), (1520, 0.86)):
    tp = TRAY.matrix_world.translation if f < 1500 else TRAY.matrix_world.translation
    hand(trav, "R", f, V((TP.x + 0.15, TP.y + 0.55, z + 0.1)), (0, 0.5, -0.8), (-1, 0, 0), grip=0.75 if f < 1520 else 0.2)
trav.key_root(1520, V((TP.x, TP.y, trav.root_head.z - 0.1)), yaw=FWD, flex=0); trav.key_spine(1520, flex=35, head=(20, 0))
trav.key_foot("R", 1520, trav.foot_xy("R", TP, FWD), FWD)
# straightens in socks, watches the tray roll into the X-ray, small shrug (1560-1620)
for f, sp, hd in ((1560, 5, (5, 10)), (1590, 0, (0, 30)), (1620, -2, (-3, 35))):
    stand(trav, f, TP, FWD, spine=(sp, 0, 0), head=hd)
    hand(trav, "R", f, TP + V((0.24, 0.05, 0.93)), (0, 0.2, -1), (-1, 0, 0), grip=0.3)
    hand(trav, "L", f, TP + V((-0.24, 0.05, 0.93)), (0, 0.2, -1), (1, 0, 0), grip=0.3)
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
    hand(off, "R", f, AX + V((4.6, 1.75, 0.83)), (0, -1, -0.3), (0, 0, -1), grip=0.4)
    hand(off, "L", f, AX + V((4.3, 1.75, 0.83)), (0, -1, -0.3), (0, 0, -1), grip=0.4)
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
    hand(pd, "R", f, QP + V((0.0, -0.25, 0.82)), (0, 0, -1), (1, 0, 0), grip=0.3)
    hand(pd, "L", f, QP + V((0.0, 0.25, 0.82)), (0, 0, -1), (-1, 0, 0), grip=0.3)
for h in (pc, pd):
    teleport_keys(h, 1380)
print("AIRPORT_DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_SAVED", OUT)
