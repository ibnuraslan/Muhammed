"""ShoeBomber character + prop animation. blender -b scene.blend --python 03_animate.py -- <out_anim.blend>
Uses blender/pipeline/anim_lib.py (MPFB IK control rig, Human helpers)."""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "../../pipeline/anim_lib.py")).read())
exec(open(os.path.join(HERE, "../../pipeline/hand_poses.py")).read())   # shared hand-pose library (director, Nov 12)
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
END = 1730

def setup(name):
    o = bpy.data.objects[name]
    R = make_human_ctrl(o)
    h = Human(R); h.name = name
    return h
HN = ["Bomber", "Attendant", "Steward", "PaxA", "PaxB", "PaxC", "PaxD", "Traveller", "Officer", "Sleeper1", "Sleeper2", "Sleeper3", "Sleeper4", "AirPaxA", "AirPaxB"]
HS = {n: setup(n) for n in HN}
print("RIGS_READY")

# ------------------------------------------------------------------ pose helpers
FINGERS = [("finger%d-%d" % (k, j)) for k in range(2, 6) for j in range(1, 4)]
_POSE_CACHE = {}
def curl(h, s, f, amt, thumb=None, pose=None):
    """fingers from the shared hand_poses library: grip amount -> pose (relaxed / cup_hold / wrap_grip), or an explicit pose"""
    if pose is None:
        pose = "relaxed" if amt <= 0.32 else "cup_hold" if amt < 0.5 else "wrap_grip"
    k = (h.r.o.name, s, pose)
    if k not in _POSE_CACHE: _POSE_CACHE[k] = _pose_rots(h.r.o, s, pose)
    _key(h.r.o, s, _POSE_CACHE[k], f, 1.0)
    return
def _old_curl(h, s, f, amt, thumb=None):
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

def hand(h, s, f, W, d, n, pole=None, grip=0.0, pose=None):
    h.key_hand(s, f, V(W), V(d), V(n), pole=V(pole) if pole else None)
    curl(h, s, f, grip, pose=pose)

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
exec(open(os.path.join(HERE, "cabin_v010.py")).read())   # v010: whole cabin choreography (aisle staging)

# ---------------------------------------------------------------- PAX C (3D across the aisle) and PAX D (4A in front, reading)
for f in range(1, 1069, 20):
    if f < 380:
        sit(pc, f, SX["D"], BY, spine=(3, 0, 0), head=(5 + 3 * math.sin(f * 0.03), 0))
    elif f < 470:
        sit(pc, f, SX["D"], BY, spine=(0, 25, 3), head=(0, 30))            # turns to look across
    elif f < 600:
        sit(pc, f, SX["D"], BY, spine=(6, 25, 0), head=(12, 35 + 5 * math.sin(f * 0.1)))   # v010: watches from her seat (aisle kept clear)
    elif f < 770:
        sit(pc, f, SX["D"], BY, spine=(4, 20, 0), head=(12, 30 + 5 * math.sin(f * 0.05)))          # v006d: sits back to watch (out of the aisle)
    elif f < 940:
        sit(pc, f, SX["D"], BY, spine=(4, 20, 0), head=(12, 30 + 5 * math.sin(f * 0.05)))          # sits back, still watching
    else:
        sit(pc, f, SX["D"], BY, spine=(-2, -8, 0), head=(8, 12))          # v006d: settles back against her seat (clear of the raised shoe)
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

exec(open(os.path.join(HERE, "airport_v010.py")).read())   # v010: airport re-staged (shoes carried by the collar)
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
# v010: tray table stays stowed (the tackle is in the aisle)
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
    reach_fix(h, a_, b_, maxd=0.12)      # v010: small slides only (aisle staging; never into a seat)
reach_fix(stw, 540, 1068, maxd=0.15)
reach_fix(off, 1393, END, feet=False, maxd=0.2)
reach_fix(trav, 1393, END, feet=False, maxd=0.08)
for h_ in (HS["AirPaxA"], HS["AirPaxB"]): reach_fix(h_, 1393, END, feet=False, maxd=0.08)
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

# ================================================================== hand limits: shared library (STYLE_ANIMATED limits)
for h in HS.values():
    add_hand_limits(h.r.o)
print("HAND_LIMITS")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("ANIM_SAVED", OUT)
