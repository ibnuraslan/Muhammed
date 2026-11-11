"""Animate everything + bake the one camera.  blender -b scene.blend --python 03_animate.py -- <out.blend>"""
import sys, os, math, random
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "..", "..", "pipeline", "anim_lib.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(7)
sc = bpy.context.scene
FPS = 60
def F(t): return 1 + round(t * FPS)
def T(f): return (f - 1) / FPS
SWAP_IN, SWAP_OUT = F(2.55), F(20.4)      # first macro frame, first real frame again
FEND = 1290
S = 0.025                                  # macro units -> metres

# ================================================================== woman
W = bpy.data.objects["Woman"]
WR = make_human_ctrl(W); WH = Human(WR)
POS = Vector((0.0, 0.45, 0.0)); YAW = 90.0
def wpt(x, y, z):
    """point in her body frame (x = her right..left? no: x = forward, y = to her left, z = up) -> world"""
    return Vector((POS.x + x, POS.y + y, z))
for s in "LR":
    xy = WH.foot_xy(s, POS, YAW)
    for f in (1, FEND):
        WH.key_foot(s, f, xy, YAW + (8 if s == "L" else -8))
rh = WH.root_head.z
# root / spine keys: (t, dx, dz, flex, twist, side, head pitch, head yaw)
BODY = [(0.0, 0.0, 0.0, 4, 14, 2, 4, 28), (0.9, 0.0, 0.0, 6, 18, 3, 8, 34), (1.95, 0.01, 0.0, 6, 18, 3, 10, 34),
        (2.05, -0.035, -0.015, 20, 8, -2, 24, 10), (2.25, -0.05, -0.03, 26, 2, -4, 30, 0), (2.55, -0.03, -0.02, 22, 0, -2, 26, 0),
        (4.0, -0.02, -0.04, 22, -4, 0, 28, -4), (19.9, -0.02, -0.04, 24, -4, 0, 32, -6), (20.5, -0.02, -0.045, 20, -2, 0, 20, -4),
        (20.9, -0.02, -0.04, 16, 0, 1, 6, 4), (21.5, -0.02, -0.035, 14, 0, 1, 2, 6)]
for i, (t, dx, dz, fl, tw, sd, hp, hy) in enumerate(BODY):
    f = F(t)
    WH.key_root(f, Vector((POS.x + dx, POS.y, rh + dz)), yaw=YAW, flex=fl * 0.25, side=sd)
    WH.key_spine(f, flex=fl, twist=tw, side=sd, head=(hp, hy))
# breathing in the visible ending (heavy, shocked)
for f in range(F(20.0), FEND + 1, 6):
    t = T(f); b = math.sin(2 * math.pi * (t - 20.0) / 0.9)
    WH.key_spine(f, flex=16 + 3 * b - 2.0 * min(1, (t - 20.0) / 1.5), twist=0, side=1, head=(8 - 6 * min(1, (t - 20.2) / 1.0) + 2 * b, 5))
jaw = WR.PB["jaw"]
for t, a in ((0, 0), (2.0, 0), (2.15, 14), (2.5, 10), (20.4, 12), (20.9, 16), (21.5, 13)):
    WR.key_rot("jaw", F(t), [("X", a)])
# hands. Left: reaching to the shelf, jerks to her flank at the hit, holds her side. Right: basket, then to her mouth.
def hand(s, t, p, d, n, pole):
    WH.key_hand(s, F(t), wpt(*p), Vector(d), Vector(n), wpt(*pole))
shelf_item = (0.32, 0.53, 1.30)          # front face of a box on the 4th shelf (y = 1.0 shelf front, she is at y 0.45)
hand("L", 0.0, (0.18, 0.40, 1.12), (0.4, 0.6, 0.2), (0, 0, 1), (-0.2, 0.7, 1.0))
hand("L", 0.9, (0.30, 0.50, 1.28), (0.2, 1.0, 0.0), (0, 0, 1), (-0.2, 0.7, 1.1))
hand("L", 1.95, (0.31, 0.51, 1.29), (0.2, 1.0, 0.0), (0, 0, 1), (-0.2, 0.7, 1.1))
hand("L", 2.15, (0.22, 0.42, 1.18), (0.3, 0.6, -0.4), (0, 0, 1), (-0.2, 0.8, 1.0))
hand("L", 2.55, (0.14, 0.30, 1.0), (0.4, -0.4, -0.5), (0, 1, 0), (-0.2, 0.7, 1.0))
hand("L", 4.0, (0.05, 0.28, 0.98), (0.6, -0.3, -0.6), (0, -1, 0), (-0.25, 0.7, 1.0))
hand("L", 20.4, (0.05, 0.28, 0.98), (0.6, -0.3, -0.6), (0, -1, 0), (-0.25, 0.7, 1.0))
hand("L", 20.75, (0.07, 0.26, 0.98), (0.6, -0.4, -0.5), (0, -1, 0), (-0.25, 0.7, 1.0))
hand("L", 21.05, (0.31, 0.11, 0.93), (0.05, -1.0, 0.35), (-1, 0, 0), (0.1, 0.75, 1.0))
hand("L", 21.5, (0.31, 0.115, 0.935), (0.05, -1.0, 0.35), (-1, 0, 0), (0.1, 0.75, 1.0))
hand("R", 0.0, (0.06, -0.24, 0.80), (0.1, 0, -1), (0, -1, 0), (-0.3, -0.6, 1.0))
hand("R", 1.95, (0.07, -0.24, 0.80), (0.1, 0, -1), (0, -1, 0), (-0.3, -0.6, 1.0))
hand("R", 2.2, (0.16, -0.22, 0.92), (0.4, 0, -0.8), (0, -1, 0), (-0.3, -0.6, 1.0))
hand("R", 2.55, (0.20, -0.16, 1.05), (0.5, 0.3, -0.5), (0, -1, 0), (-0.3, -0.6, 1.0))
hand("R", 4.0, (0.36, -0.07, 1.06), (0.3, 0.3, 1.0), (1, 0, 0), (0.0, -0.6, 0.9))
hand("R", 20.4, (0.36, -0.07, 1.06), (0.3, 0.3, 1.0), (1, 0, 0), (0.0, -0.6, 0.9))
hand("R", 21.0, (0.35, -0.06, 1.10), (0.3, 0.3, 1.0), (1, 0, 0), (0.0, -0.6, 0.9))
hand("R", 21.5, (0.35, -0.06, 1.09), (0.3, 0.3, 1.0), (1, 0, 0), (0.0, -0.6, 0.9))

# basket: rides on the right wrist until the hit (baked), then drops to the floor
bk = bpy.data.objects["Basket"]
sc.frame_set(1); bpy.context.view_layer.update()
def wristM(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["wrist.R"].matrix
OFF = wristM(1).inverted() @ (Matrix.Translation(wpt(0.07, -0.26, 0.66)) @ Matrix.Rotation(math.radians(90), 4, 'Z'))
for f in list(range(1, F(2.25) + 1, 2)) + [F(2.25)]:
    M = wristM(f) @ OFF; bk.location = M.translation; bk.rotation_euler = M.to_euler()
    bk.keyframe_insert("location", frame=f); bk.keyframe_insert("rotation_euler", frame=f)
for t, p, r in ((2.6, (0.25, -0.35, 0.16), (0.4, 0.2, 1.8)), (2.68, (0.27, -0.37, 0.101), (0.0, 0.0, 1.82)), (2.78, (0.28, -0.38, 0.115), (0.06, 0.0, 1.85)), (2.88, (0.28, -0.38, 0.101), (0.0, 0.0, 1.85)), (21.5, (0.28, -0.38, 0.101), (0.0, 0.0, 1.85))):
    bk.location = wpt(*p); bk.rotation_euler = r
    bk.keyframe_insert("location", frame=F(t)); bk.keyframe_insert("rotation_euler", frame=F(t))
# falling cans knocked from the shelf by her flailing left hand at the hit
for i in range(3):
    c = bpy.data.objects["FallCan%d" % i]
    x0 = 0.28 + 0.08 * i; y0 = 1.05; z0 = 1.26 + 0.06
    keys = [(0, (x0, y0, z0), (0, 0, 0)), (2.12 + 0.05 * i, (x0, y0, z0), (0, 0, 0)),
            (2.4 + 0.05 * i, (x0 + 0.05, 0.92 - 0.05 * i, 0.85), (1.2, 0.3, 0)), (2.62 + 0.05 * i, (x0 + 0.1, 0.80 - 0.07 * i, 0.035), (1.57, 0, 0.6 * i)),
            (2.9 + 0.05 * i, (x0 + 0.18, 0.72 - 0.1 * i, 0.035), (1.57, 0, 1.4 + i)), (21.5, (x0 + 0.18, 0.72 - 0.1 * i, 0.035), (1.57, 0, 1.4 + i))]
    for t, p, r in keys:
        c.location = p; c.rotation_euler = r; c.keyframe_insert("location", frame=F(t)); c.keyframe_insert("rotation_euler", frame=F(t))

# ================================================================== background shoppers
A = bpy.data.objects["ShopperA"]; AR = make_human_ctrl(A); AH = Human(AR); A.location.z = 0.015
cart = bpy.data.objects["Cart"]
def pathA(f):
    t = min(T(f), 2.6); u = t / 2.6
    return Vector((-6.4 + 2.9 * (1.6 * u - 0.6 * u * u), -0.35, 0))
AH.walk(pathA, lambda f: 90.0, 1, F(2.6), stride=0.62, lift=0.07)
apos = pathA(F(2.6))
# planted until the end, then (beat 7) he turns to her and takes a step toward her: right foot, then left
STEPV = Vector((0.1, 0.36, 0))
for s_ in "LR":
    for f in (F(2.6), F(20.5)):
        AH.key_foot(s_, f, AH.foot_xy(s_, apos, 90.0), 90.0)
AH.key_foot("R", F(20.68), AH.foot_xy("R", apos + STEPV * 0.5, 90.0), 90.0, lift=0.07, pitch=15)
for f in (F(20.86), FEND): AH.key_foot("R", f, AH.foot_xy("R", apos + STEPV, 90.0), 90.0)
AH.key_foot("L", F(21.0), AH.foot_xy("L", apos, 90.0), 90.0)
AH.key_foot("L", F(21.17), AH.foot_xy("L", apos + STEPV * 0.5, 90.0), 90.0, lift=0.07, pitch=15)
for f in (F(21.34), FEND): AH.key_foot("L", f, AH.foot_xy("L", apos + STEPV, 90.0), 90.0)
for t, fl, tw, hy, k in ((2.6, 6, 0, 0, 0), (3.2, 2, -10, 30, 0), (20.4, 0, -12, 35, 0), (20.55, 8, -4, 20, 0.05), (20.86, 10, 0, 8, 0.55),
                         (21.17, 9, 0, 4, 0.75), (21.34, 8, 0, 2, 1.0), (21.5, 8, 0, 2, 1.0)):
    pr = apos + STEPV * k
    AH.key_root(F(t), Vector((pr.x, pr.y, AH.root_head.z - 0.01 - 0.02 * math.sin(math.pi * min(1, k * 2) ))), yaw=90.0, flex=fl * 0.3)
    AH.key_spine(F(t), flex=fl, twist=tw, head=(-4, hy))
for f in range(1, FEND + 1, 4):
    p = pathA(min(f, F(2.6)))
    cart.location = (p.x + 0.95, p.y, 0.0); cart.rotation_euler = (0, 0, math.pi)
    cart.keyframe_insert("location", frame=f)
    for s, dy in (("L", 0.2), ("R", -0.2)):
        if f <= F(2.7):
            AH.key_hand(s, f, Vector((p.x + 0.36, p.y + dy, 1.04)), Vector((1, 0, -0.3)), Vector((0, 0, 1)), Vector((p.x - 0.2, p.y + 3 * dy, 1.0)))
# shopper A: after the bang he lets go and raises his hands, frozen in surprise
AH.key_hand("L", F(3.4), Vector((apos.x + 0.25, apos.y + 0.22, 1.32)), Vector((0.2, 0.2, 1)), Vector((1, 0, 0)), Vector((apos.x - 0.2, apos.y + 0.6, 1.0)))
AH.key_hand("R", F(3.4), Vector((apos.x + 0.25, apos.y - 0.22, 1.32)), Vector((0.2, -0.2, 1)), Vector((1, 0, 0)), Vector((apos.x - 0.2, apos.y - 0.6, 1.0)))
AH.key_hand("L", F(20.5), Vector((apos.x + 0.27, apos.y + 0.23, 1.34)), Vector((0.2, 0.2, 1)), Vector((1, 0, 0)), Vector((apos.x - 0.2, apos.y + 0.6, 1.0)))
AH.key_hand("R", F(20.5), Vector((apos.x + 0.27, apos.y - 0.23, 1.34)), Vector((0.2, -0.2, 1)), Vector((1, 0, 0)), Vector((apos.x - 0.2, apos.y - 0.6, 1.0)))
ap2 = apos + STEPV   # reaching toward her as he steps in
AH.key_hand("L", FEND, Vector((ap2.x + 0.42, ap2.y + 0.2, 1.18)), Vector((1, 0.1, 0.2)), Vector((0, 0, -1)), Vector((ap2.x - 0.1, ap2.y + 0.6, 1.0)))
AH.key_hand("R", FEND, Vector((ap2.x + 0.35, ap2.y - 0.22, 1.12)), Vector((1, -0.1, 0.1)), Vector((0, 0, -1)), Vector((ap2.x - 0.1, ap2.y - 0.6, 1.0)))

# stocker restocking down the aisle: holds a carton in both hands (grasp), then turns toward the bang
import bmesh as _bm2
STK = bpy.data.objects["Stocker"]; SR = make_human_ctrl(STK); SH = Human(SR); STK.location.z = 0.015
spos = Vector((-7.4, -0.55, 0)); syaw = 0.0
for s_ in "LR":
    for f in (1, FEND): SH.key_foot(s_, f, SH.foot_xy(s_, spos, syaw), syaw)
_b = _bm2.new(); _bm2.ops.create_cube(_b, size=1.0)
for v in _b.verts: v.co = Vector((v.co.x * 0.34, v.co.y * 0.22, v.co.z * 0.24))
cme = bpy.data.meshes.new("Carton"); _b.to_mesh(cme); _b.free(); cme.materials.append(bpy.data.materials["M_pack05"])
carton = bpy.data.objects.new("Carton", cme); bpy.data.collections["REAL"].objects.link(carton)
for t, fl, tw, hy, cz, cy in ((0.0, 8, 0, -10, 1.02, -0.86), (1.0, 14, -4, -16, 1.12, -0.88), (2.0, 6, 0, -6, 1.06, -0.85), (2.6, 4, 10, 30, 1.0, -0.84),
                              (20.4, 2, 18, 45, 0.98, -0.83), (21.5, 2, 20, 48, 0.98, -0.83)):
    f = F(t)
    SH.key_root(f, Vector((spos.x, spos.y, SH.root_head.z - 0.015)), yaw=syaw, flex=fl * 0.3)
    SH.key_spine(f, flex=fl, twist=tw, head=(-6 + fl * 0.5, hy))
    c = Vector((spos.x + 0.02 * math.sin(t), cy, cz))
    carton.location = c; carton.rotation_euler = (0, 0, math.radians(tw * 0.6)); carton.keyframe_insert("location", frame=f); carton.keyframe_insert("rotation_euler", frame=f)
    for s_, sx in (("L", 1), ("R", -1)):
        SH.key_hand(s_, f, c + Vector((sx * 0.2, 0.02, -0.02)), Vector((-sx * 0.3, -1, 0.1)), Vector((-sx, 0, 0)), Vector((spos.x + sx * 0.5, spos.y + 0.3, 1.0)))
# shopper C browsing the shelf, then turns to look, hand to her chest
SC = bpy.data.objects["ShopperC"]; CR_ = make_human_ctrl(SC); CH = Human(CR_)
cpos = Vector((-2.1, -0.5, 0)); cyaw = 0.0
for s_ in "LR":
    for f in (1, FEND): CH.key_foot(s_, f, CH.foot_xy(s_, cpos, cyaw), cyaw)
for t, tw, hy, hp in ((0.0, 0, -10, 12), (1.2, 4, -4, 18), (2.3, 6, 0, 14), (2.9, 25, 50, 0), (20.4, 30, 58, -2), (21.5, 32, 60, -2)):
    f = F(t); CH.key_root(f, Vector((cpos.x, cpos.y, CH.root_head.z - 0.01)), yaw=cyaw)
    CH.key_spine(f, flex=4, twist=tw, head=(hp, hy))
for t, p in ((0.0, (-2.15, -0.86, 1.18)), (1.2, (-2.2, -0.9, 1.22)), (2.3, (-2.2, -0.9, 1.22)), (2.9, (-2.1, -0.68, 1.28)), (21.5, (-2.08, -0.67, 1.29))):
    CH.key_hand("R", F(t), Vector(p), Vector((0, -1, 0.4)) if t < 2.5 else Vector((0.3, 0.2, 1.0)), Vector((1, 0, 0)), Vector((cpos.x - 0.45, cpos.y + 0.2, 1.0)))
for t in (0.0, 21.5):
    CH.key_hand("L", F(t), Vector((cpos.x + 0.22, cpos.y - 0.02, 0.8)), Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((cpos.x + 0.5, cpos.y + 0.3, 1.0)))
B_ = bpy.data.objects["ShopperB"]; BR_ = make_human_ctrl(B_); BH = Human(BR_)
def pathB(f):
    t = min(T(f), 2.3); return Vector((-9.75, -3.2 + 1.25 * t, 0))
BH.walk(pathB, lambda f: 0.0 + 180.0, 1, F(2.3), stride=0.7)
bpos = pathB(F(2.3))
for s in "LR":
    for f in (F(2.3), FEND): BH.key_foot(s, f, BH.foot_xy(s, bpos, 180.0), 180.0)
for t, hy, tw in ((2.3, 0, 0), (2.9, 55, 30), (21.5, 60, 35)):
    BH.key_root(F(t), Vector((bpos.x, bpos.y, BH.root_head.z - 0.02)), yaw=180.0)
    BH.key_spine(F(t), twist=tw, head=(0, hy))
for s, sx in (("L", 1), ("R", -1)):
    for t in (2.9, 21.5):
        BH.key_hand(s, F(t), Vector((bpos.x - 0.15 * sx * -1, bpos.y + 0.1, 1.05)), Vector((0, 1, 0.5)), Vector((sx, 0, 0)), Vector((bpos.x + 0.5 * sx, bpos.y - 0.4, 1.0)))

# ================================================================== impact point + macro root (child of her spine03)
sc.frame_set(F(2.0)); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
tee = bpy.data.objects["Woman.female_casualsuit01"]
te = tee.evaluated_get(dg)
ZB = 1.0
best = None
for zz in (0.98, 1.0, 1.02):
    o_ = tee.matrix_world.inverted() @ Vector((3.0, POS.y - 0.02, zz))
    d_ = tee.matrix_world.inverted().to_3x3() @ Vector((-1, 0, 0))
    hit, loc, nrm, idx = te.ray_cast(o_, d_)
    if hit:
        wl = tee.matrix_world @ loc; print("HIT", zz, wl, (tee.matrix_world.to_3x3() @ nrm).normalized())
        if best is None or abs(zz - ZB) < abs(best[0] - ZB): best = (zz, wl)
P = best[1]
root = bpy.data.objects["MacroRoot"]
root.parent = W; root.parent_type = 'BONE'; root.parent_bone = "spine03"
bpy.context.view_layer.update()
M121 = Matrix.Translation(P) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((S, S, S, 1))
root.matrix_world = M121
bpy.context.view_layer.update()
print("ROOT", root.matrix_world.translation, P)
def rootM(f):
    sc.frame_set(f); return root.matrix_world.copy()
RM = {}; ANC = {}
for f in range(1, FEND + 1):
    sc.frame_set(f); RM[f] = M121 if f <= F(2.0) else root.matrix_world.copy()
    Mi = RM[f].inverted()
    ANC[f] = {"torso": Mi @ (W.matrix_world @ W.pose.bones["spine01"].head), "face": Mi @ (W.matrix_world @ W.pose.bones["head"].head)}

# ================================================================== bullet: tip depth in macro units (negative = outside her)
DK = [(0.0, -184), (0.45, -156), (0.8, -108), (1.2, -60), (1.6, -20), (1.85, -4), (2.0, 0.0), (2.6, 0.10), (3.2, 0.26),
      (3.6, 0.7), (5.0, 1.7), (7.8, 2.85), (10.2, 3.6), (12.6, 4.2), (14.8, 4.85), (16.2, 5.2), (17.2, 5.36), (21.5, 5.36)]
Dfn = pchip(DK)
def D(t): return Dfn(t)
bul = bpy.data.objects["Bullet"]; bul.rotation_mode = 'QUATERNION'
spin = 0.0; prevD = D(0)
for f in range(1, FEND + 1):
    t = T(f); d = D(t); v = (d - prevD) * FPS; prevD = d
    spin += 0.25 * min(1.0, abs(v) / 20.0) + (0.06 if t < 17.2 else 0.0) * min(1, abs(v) * 2)
    mush = min(1.0, max(0.0, (d - 0.3) / 4.0))     # slight nose flattening as it slows
    Mb = RM[f] @ Matrix.Translation((d - 0.6, 0, 0)) @ Matrix.Rotation(spin, 4, 'X') @ Matrix.Diagonal((1 - 0.12 * mush, 1 + 0.08 * mush, 1 + 0.08 * mush, 1))
    loc, rot, scl = Mb.decompose()
    if f > 1 and bul.rotation_quaternion.dot(rot) < 0: rot = -rot
    bul.location = loc; bul.rotation_quaternion = rot; bul.scale = scl
    for p in ("location", "rotation_quaternion", "scale"): bul.keyframe_insert(p, frame=f)
trail = bpy.data.objects["Trail"]; trail.scale = (3.0, 0.45, 0.45)
for t, a in ((0, 0.9), (1.5, 0.7), (1.9, 0.15), (2.0, 0.0), (21.5, 0.0)):
    trail.color = (1, 1, 1, a); trail.keyframe_insert("color", frame=F(t))

# ================================================================== tissue: dimple shape keys, hole decal, lobules, rings, muscle, guts
def dimple_val(t):
    if t < 2.0: return 0.0
    if t < 3.2: return D(t)
    u = t - 3.2; return 0.26 * math.exp(-u * 3.0) * math.cos(u * 14.0)     # pierce: snaps back and wobbles
for nm, gain in (("M_Fabric", 1.0), ("M_Epidermis", 1.0), ("M_Dermis", 0.85)):
    o = bpy.data.objects[nm]; o.shape_key_add(name="Basis")
    k = o.shape_key_add(name="dimple")
    for i, v in enumerate(o.data.vertices):
        r2 = v.co.y ** 2 + v.co.z ** 2
        k.data[i].co = v.co + Vector((gain * math.exp(-r2 / 0.6), 0, 0))
    for f in range(F(1.95), F(4.5), 2):
        dv = dimple_val(T(f)) + (0.07 if nm == "M_Fabric" and 2.0 <= T(f) < 3.2 else 0.0)   # the fabric sits 0.06 u above the skin the tip touches
        k.value = max(-0.5, min(1.0, dv)); k.slider_min = -1; k.keyframe_insert("value", frame=f)
    # after the pierce the layer stays parted round the bullet: open a clean round hole (radial push to r >= 0.23)
    h = o.shape_key_add(name="hole", from_mix=False)
    for i, v in enumerate(o.data.vertices):
        rr = math.hypot(v.co.y, v.co.z)
        if rr < 0.5:
            d_ = Vector((0, v.co.y, v.co.z)).normalized() if rr > 1e-4 else Vector((0, 0, 1))
            nr = 0.23 + (rr / 0.5) * 0.27
            h.data[i].co = v.co + d_ * (nr - rr) + Vector((0.06 * (1 - rr / 0.5), 0, 0))
    for t_, hv in ((3.1, 0.0), (3.22, 1.0), (21.5, 1.0)):
        h.value = hv; h.keyframe_insert("value", frame=F(t_))
# real tee dimple: Warp from the impact point toward the inside
we_from = bpy.data.objects.new("WarpFrom", None); sc.collection.objects.link(we_from); we_from.parent = root; we_from.location = (0, 0, 0)
we_to = bpy.data.objects.new("WarpTo", None); sc.collection.objects.link(we_to); we_to.parent = root
for f in range(F(1.95), F(2.6), 2):
    we_to.location = (dimple_val(T(f)), 0, 0); we_to.keyframe_insert("location", frame=f)
wm = tee.modifiers.new("Dimple", 'WARP'); wm.object_from = we_from; wm.object_to = we_to; wm.falloff_radius = 0.035; wm.falloff_type = 'SMOOTH'
wv = tee.modifiers.new("Ripple", 'WAVE'); wv.start_position_object = we_from; wv.use_normal = True; wv.use_x = wv.use_y = True
wv.height = 0.004; wv.width = 0.03; wv.narrowness = 1.2; wv.speed = 0.006; wv.time_offset = F(2.0); wv.lifetime = 60; wv.damping_time = 40
wv.falloff_radius = 0.22
for hn in ("M_HoleDecal", "TeeHole"):
    hole = bpy.data.objects[hn]
    for t, s_ in ((0, 0.0), (3.15, 0.0), (3.3, 1.0), (21.5, 1.0)):
        hole.scale = (1, s_ * 0.8, s_ * 0.8); hole.keyframe_insert("scale", frame=F(t))

def vel(t): return (D(t + 0.02) - D(t - 0.02)) / 0.04
# fat lobules are geometry-node instances (02_build_scene); their push / squash / ripple / settle come from TipCtl:
#   x = tip depth, y = energy being absorbed (ripple strength), z = settle-wobble amplitude after the stop
tipctl = bpy.data.objects["TipCtl"]
for f in range(SWAP_IN - 4, SWAP_OUT + 6, 2):
    t = T(f)
    e = min(1.0, max(0.0, vel(t) / 1.2)) if t > 3.15 else 0.0
    wob = (math.exp(-(t - 17.2) / 1.6) if t > 17.2 else 0.0) + (0.35 * math.exp(-(t - 3.2) / 0.8) if t > 3.2 else 0.0)
    tipctl.location = (D(t), e, wob); tipctl.keyframe_insert("location", frame=f)
# energy rings bloom behind the bullet
RINGS = sorted([o for o in bpy.data.objects if o.name.startswith("M_Ring")], key=lambda o: o.name)
EMIT = [3.35, 4.0, 4.8, 5.7, 6.7, 7.85, 8.6, 9.4, 10.3, 11.2, 12.3, 13.6]
for o, te_ in zip(RINGS, EMIT):
    x = D(te_) - 0.05; e = max(0.2, min(1.0, vel(te_) / 1.0))
    for t, rr, a in ((te_ - 0.02, 0.2, 0.0), (te_, 0.25, 0.9 * e), (te_ + 0.5, 1.2 + 0.8 * e, 0.45 * e), (te_ + 1.4, 2.4 + 1.0 * e, 0.0)):
        o.location = (x, 0, 0); o.scale = (1, rr, rr); o.color = (1, 1, 1, a)
        for p in ("location", "scale", "color"): o.keyframe_insert(p, frame=F(t))
# muscle fibres: the front rows bow back out of the bullet's way (shape key), all shiver when it arrives
for o in [o for o in bpy.data.objects if o.name.startswith("M_MuscleFib")]:
    ph = random.uniform(0, 6.28); x = o.location.x; yrow = o.location.y
    o.shape_key_add(name="Basis"); k = o.shape_key_add(name="part")
    for i, v in enumerate(o.data.vertices):
        k.data[i].co = v.co + Vector((0, -0.34 * math.exp(-(v.co.z / 0.32) ** 2) * (1.0 if yrow > -0.3 else 0.5), 0))
    k.slider_max = 1.0
    for f in range(F(11.5), SWAP_OUT + 4, 4):
        t = T(f); d = D(t)
        k.value = max(0.0, min(1.0, (d - (x - 0.45)) / 0.3)); k.keyframe_insert("value", frame=f)
        near = math.exp(-((d - x) / 0.5) ** 2)
        s_ = 1 + 0.08 * near * math.sin(t * 9 + ph) + 0.015 * math.sin(t * 2.2 + ph)
        o.scale = (s_, s_, 1); o.keyframe_insert("scale", frame=f)
# bring a bowel loop right up behind the peritoneum at the bullet's height (shift in y/z only, so nothing crosses the muscle)
gr = bpy.data.objects.get("M_GutReal")
if gr:
    cand = [v.co for v in gr.data.vertices if 5.66 < v.co.x < 6.1 and abs(v.co.z) < 4.0]
    best_v = max(cand, key=lambda c: c.y - 0.15 * abs(c.z))          # the frontmost loop near the bullet's height
    gr.location = (0.0, 0.0, -best_v.z)
    print("GUT shift", tuple(gr.location), tuple(best_v))
# intestines glisten and slide (displace noise drifting)
tex = bpy.data.textures.new("GutNoise", 'CLOUDS'); tex.noise_scale = 1.2
gn = bpy.data.objects.new("GutNoiseCtl", None); sc.collection.objects.link(gn); gn.parent = root
for t in (0, 21.5):
    gn.location = (t * 0.25, t * 0.1, t * 0.18); gn.keyframe_insert("location", frame=F(t))
for o in [o for o in bpy.data.objects if o.name.startswith("M_Gut") and o.type == 'MESH' and "Bed" not in o.name]:
    dm = o.modifiers.new("peristalsis", 'DISPLACE'); dm.texture = tex; dm.texture_coords = 'OBJECT'; dm.texture_coords_object = gn; dm.strength = 0.25

# fat droplets shed from the channel wall as the bullet ploughs through (secondary motion), drifting out and settling
import bmesh as _bm
_b = _bm.new(); _bm.ops.create_icosphere(_b, subdivisions=2, radius=1.0); dme = bpy.data.meshes.new("Droplet"); _b.to_mesh(dme); _b.free()
for p_ in dme.polygons: p_.use_smooth = True
dme.materials.append(bpy.data.materials["M_fat_lobule"])
MC = bpy.data.collections["MACRO"]
for i in range(48):
    te_ = 3.3 + i * 0.22
    if te_ > 15.0: break
    o = bpy.data.objects.new("M_Drop%02d" % i, dme); MC.objects.link(o); o.parent = root
    x0 = D(te_) - 0.15; ang = random.uniform(0.2, 2.9); r0 = 0.2
    dirv = Vector((random.uniform(-0.3, 0.1), math.cos(ang), math.sin(ang) * random.choice((-1, 1))))
    sz = random.uniform(0.035, 0.07) * max(0.4, min(1.0, vel(te_) / 0.8))
    for t_, k_, s_ in ((te_ - 0.02, 0.0, 0.0), (te_, 0.0, 1.0), (te_ + 0.6, 0.5, 1.0), (te_ + 2.0, 0.8, 0.8), (te_ + 3.5, 0.85, 0.0)):
        o.location = Vector((x0, 0, 0)) + dirv.normalized() * (r0 + k_ * random.uniform(0.6, 1.0)); o.scale = (sz * s_,) * 3
        o.keyframe_insert("location", frame=F(t_)); o.keyframe_insert("scale", frame=F(t_))
# vessels pulse with the heartbeat (~80 bpm)
for o in [o for o in bpy.data.objects if o.name.startswith("M_Vessel")]:
    for f in range(SWAP_IN - 2, SWAP_OUT + 4, 6):
        t_ = T(f); b_ = max(0.0, math.sin(2 * math.pi * t_ * 1.33)) ** 3
        o.scale = (1.0, 1.0 + 0.03 * b_, 1.0 + 0.03 * b_); o.keyframe_insert("scale", frame=f)
# ================================================================== visibility swap (one camera; the store and the macro set trade places while fabric fills the frame)
MACO = [o for o in bpy.data.collections["MACRO"].all_objects]
_ms = set(MACO)
REALO = [o for o in sc.objects if o not in _ms and o.type in ('MESH', 'LIGHT', 'CURVE') and o.name != "Bullet"]
def key_vis(o, on_ranges):
    for f, v in on_ranges:
        o.hide_render = v; o.keyframe_insert("hide_render", frame=f)
        o.hide_viewport = False
    if o.animation_data and o.animation_data.action:
        pass
for o in REALO: key_vis(o, [(1, False), (SWAP_IN, True), (SWAP_OUT, False)])
for o in MACO: key_vis(o, [(1, True), (SWAP_IN, False), (SWAP_OUT, True)])
for a in bpy.data.actions:
    for lay in a.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path == "hide_render":
                        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

# ================================================================== camera: target + spherical offset in the macro root frame (units), pchip on log distance
def anchor(name, f):
    Mi = RM[f].inverted()
    if name == "tip": return Vector((D(T(f)), 0, 0))
    if name == "hole": return Vector((0, 0, 0))
    if name in ("torso", "face"):
        return ANC[f][name]
    raise KeyError(name)
# (t, anchor, offset(local units), az, el, dist(units), lens)
CK = [(0.0, "torso", (0, 0, -6), 176, -6, 172, 26),
      (0.75, "tip", (0.3, 0, 0), 165, 5, 6.0, 30),
      (1.05, "tip", (0.3, 0, 0.1), 148, 4, 4.0, 30),
      (1.35, "tip", (0.2, 0, 0.1), 105, 6, 3.4, 30),
      (1.65, "tip", (0.3, 0, 0.1), 152, 6, 4.0, 30),
      (1.9, "hole", (-1.2, 0, 0), 110, 3, 3.5, 40),
      (2.05, "hole", (0.0, 0, 0), 95, 2, 2.4, 50),
      (2.3, "hole", (0, -0.2, 0.05), 135, 8, 1.5, 50),
      (2.55, "hole", (0, -0.55, 0.1), 160, 5, 0.72, 50),
      (2.8, "hole", (0.4, -0.3, 0), 125, 30, 2.6, 45),
      (3.1, "tip", (0.3, 0, 0), 96, 10, 4.0, 40),
      (4.0, "tip", (0.3, 0, -0.2), 70, -12, 3.2, 40),
      (5.0, "tip", (0.0, 0, 0), 80, 5, 1.7, 50),
      (6.0, "tip", (0.6, 0, 0), 95, 6, 8.5, 30),
      (7.0, "tip", (0.0, 0, 0), 112, 40, 3.6, 40),
      (8.0, "tip", (0.2, 0, 0), 88, 12, 2.8, 40),
      (9.0, "tip", (-0.6, 0, 0), 145, 10, 3.2, 40),
      (9.5, "tip", (-0.2, 0, 0), 105, 62, 3.4, 35),
      (10.0, "tip", (0.0, 0, 0), 62, 15, 3.4, 38),
      (11.0, "tip", (-0.3, -0.2, 0.5), 95, -5, 1.8, 45),
      (11.5, "tip", (0.2, 0, -0.3), 75, -40, 2.6, 38),
      (12.0, "tip", (0.3, 0, 0), 100, 18, 7.0, 30),
      (13.0, "tip", (0.1, 0, 0), 78, 5, 2.4, 45),
      (14.0, "tip", (0.1, 0, 0), 95, -35, 2.3, 45),
      (15.0, "tip", (0.3, 0, 0), 45, 10, 3.6, 35),
      (16.0, "tip", (0.3, 0, 0), 66, 42, 3.0, 35),
      (16.6, "tip", (0.2, 0, 0), 48, 14, 2.4, 40),
      (17.8, "tip", (0.3, 0, 0), 150, -8, 3.0, 38),
      (18.4, "tip", (0.3, 0, 0), 138, -22, 3.4, 35),
      (19.0, "tip", (0.3, 0, 0), 110, -35, 3.8, 35),
      (19.8, "tip", (-0.8, 0, 0), 98, 8, 6.0, 32),
      (20.1, "hole", (1.2, -0.2, 0), 105, 15, 4.2, 40),
      (20.27, "hole", (0.0, -0.35, 0.1), 132, 28, 1.7, 48),
      (20.4, "hole", (0, -0.55, 0.1), 160, 5, 0.72, 50),
      (20.6, "hole", (-3.0, 0, 2.0), 158, 6, 6.0, 45),
      (20.8, "face", (-2, 0, -6), 152, 6, 28, 40),
      (21.5, "face", (-2, 0, -8), 138, 9, 48, 35)]
kt = [k[0] for k in CK]
def DS(t, w=0.1):
    """bullet tip smoothed over +-w s (C1 through the impact kink): the camera's moving reference"""
    n = 9; acc = 0.0; ws = 0.0
    for j in range(n):
        u = -w + 2 * w * j / (n - 1); g = math.exp(-(u / (0.5 * w)) ** 2); acc += g * D(t + u); ws += g
    return acc / ws
class CamSolve:
    """target = ref(t) + catmull offsets (anchor values at key time, relative to ref); camera = target + spherical (az, el, log dist)"""
    def __init__(self, keys, ref):
        self.ref = ref
        rel = [anchor(k[1], max(1, min(FEND, F(k[0])))) + Vector(k[2]) - Vector((ref(k[0]), 0, 0)) for k in keys]
        self.rx = catmull([(k[0], v.x) for k, v in zip(keys, rel)]); self.ry = catmull([(k[0], v.y) for k, v in zip(keys, rel)])
        self.rz = catmull([(k[0], v.z) for k, v in zip(keys, rel)])
        self.az = catmull([(k[0], k[3]) for k in keys]); self.el = catmull([(k[0], k[4]) for k in keys])
        self.ld = catmull([(k[0], math.log(k[5])) for k in keys]); self.ln = pchip([(k[0], k[6]) for k in keys])
    def __call__(self, t):
        tgt = Vector((self.ref(t), 0, 0)) + Vector((self.rx(t), self.ry(t), self.rz(t)))
        az = math.radians(self.az(t)); el = math.radians(self.el(t)); dist = math.exp(self.ld(t))
        return tgt, tgt + dist * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))), self.ln(t), dist
# opening dolly on her (static reference) and the bullet-locked solution for everything after; cross-blended 0.3 -> 0.75 s = the whip
CA = [(-1.0, "torso", (0, 0, -6), 176, -6, 185, 26), (0.0, "torso", (0, 0, -6), 176, -6, 172, 26), (0.75, "torso", (0, 0, -3), 175, -4, 150, 27),
      (1.5, "torso", (0, 0, -2), 175, -3, 130, 28)]
CB = CK[1:]
solA = CamSolve(CA, lambda t: 0.0); solB = CamSolve(CB, DS)
def cam_at(t):
    if t >= 0.75: return solB(t)
    ta, ca, la, da = solA(t)
    if t <= 0.3: return ta, ca, la, da
    tb, cb, lb, db = solB(t); w = smooth((t - 0.3) / 0.45)
    return ta.lerp(tb, w), ca.lerp(cb, w), la + (lb - la) * w, math.exp(math.log(da) + (math.log(db) - math.log(da)) * w)
cam = bpy.data.objects["CAM_Film"]; cd = cam.data; cam.rotation_mode = 'QUATERNION'
CAMLOG = []
prevq = None
for f in range(1, FEND + 1):
    t = T(f)
    tgt, cp, lens_, dist = cam_at(t)
    M = RM[f]
    cw = M @ cp; tw_ = M @ tgt
    up = (M.to_3x3() @ Vector((0, 0, 1))).normalized()
    fwd = (tw_ - cw).normalized(); right = fwd.cross(up).normalized(); up2 = right.cross(fwd)
    R3 = Matrix((right, up2, -fwd)).transposed()
    q = R3.to_quaternion()
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = cw; cam.rotation_quaternion = q
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = lens_; cd.keyframe_insert("lens", frame=f)
    dw = dist * S
    cd.clip_start = max(0.0002, min(0.05, 0.04 * dw)); cd.keyframe_insert("clip_start", frame=f)
    fdist = (tw_ - cw).length
    fl_ = (tgt - cp).normalized()
    if cp.x < -0.01 and fl_.x > 0.3 and dw < 0.25:      # close to the shirt and facing it: focus on the fabric plane
        fdist = min(fdist, (-cp.x / fl_.x) * S)
    cd.dof.use_dof = True; cd.dof.focus_distance = fdist; cd.dof.keyframe_insert("focus_distance", frame=f)
    cd.dof.aperture_fstop = 2.8 + 8.2 * smooth((0.4 - dw) / 0.3); cd.dof.keyframe_insert("aperture_fstop", frame=f)
    CAMLOG.append((f, tuple(cw), tuple(cp), dw))
import json
json.dump(CAMLOG, open(os.path.join(HERE, "..", "camlog.json"), "w"))
BEATS = [(1, 0.0, "A stray bullet struck her"), (2, 2.0, "right in the stomach"), (3, 3.0, "It pierced her skin"),
         (4, 7.8, "Layer by layer"), (5, 12.6, "And by the time it reached deeper tissue"), (6, 14.8, "the bullet had lost most of its force"),
         (7, 20.1, "saving her life")]
json.dump([{"beat": b, "frame": F(t), "first_words": w} for b, t, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("DONE")
