"""BellyFat v012: built straight to the VO frames (v010 timing, 1-1273), short shots with hard cuts on ONE camera.
blender -b scene.blend --python 03_shots.py -- <out.blend>
Director fix lists (Nov 21 18 items, Nov 23 v011 13 items) + RECURRING_FAULTS + batch-2 rules. Beat frames: 1, 73, 181, 451, 715, 829, 1147; end 1273."""
import sys, os, math, random, json
import bpy, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE = os.path.join(HERE, "..", "..", "pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
out = sys.argv[sys.argv.index("--") + 1]
random.seed(11)
sc = bpy.context.scene
FPS = 60; FEND = 1273
sc.frame_start, sc.frame_end = 1, FEND
def T(f): return (f - 1) / FPS
S = 0.025
YB_ = 3.2
BEATS = [(1, 1, "A stray bullet struck her"), (2, 73, "right in the stomach"), (3, 181, "It pierced her skin"), (4, 451, "Layer by layer"),
         (5, 715, "And by the time it reached deeper tissue"), (6, 829, "the bullet had lost most of its force"), (7, 1147, "saving her life")]
# shots (first frame, last frame, name). Hard cuts between them.
SHOTS = [(1, 40, "A_shop"), (41, 52, "W_window"), (53, 100, "B_track"),
         (101, 200, "E1_skin"), (201, 330, "E2_fat"), (331, 450, "F_fat"), (451, 580, "G1_layers"), (581, 714, "G2_fascia"),
         (715, 828, "H_muscle"), (829, 950, "I_slow"), (951, 1005, "J_stop"),
         (1006, 1146, "D_react"), (1147, 1273, "OP_relief")]
REAL_RANGES = [(1, 100), (1006, 1273)]
def is_real(f): return any(a <= f <= b for a, b in REAL_RANGES)
def kq(obj, bone, f, axis, deg):
    """key a bone's LOCAL rotation (face bones: eye X = look down, orbicularis03 X<0 = close lid, jaw X = open)"""
    pb = obj.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(Vector(axis), math.radians(deg))
    pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)

# ================================================================== woman
W = bpy.data.objects["Woman"]
WR = make_human_ctrl(W); WH = Human(WR); add_hand_limits(W)
POS = Vector((0.0, 0.45, 0.0)); YAW = 90.0
def wpt(x, y, z): return Vector((POS.x + x, POS.y + y, z))
for s in "LR":
    xy = WH.foot_xy(s, POS, YAW)
    for f in (1, FEND): WH.key_foot(s, f, xy, YAW + (8 if s == "L" else -8))
rh = WH.root_head.z
IMPACT = 92                        # bullet touches the shirt (end of shot B)
# (frame, dx, dz, flex, twist, side, head pitch, head yaw)  - she reads the box, flinches at the hit, folds, then straightens relieved
BODY = [(1, 0.0, 0.0, 6, 10, 2, 14, 22), (20, 0.014, 0.0, 6, 11, -1.5, 15, 20), (40, -0.006, 0.0, 7, 10, 2, 16, 18), (70, 0.012, 0.0, 6, 10, -1, 15, 20),
        (IMPACT, 0.0, 0.0, 6, 10, 1, 15, 20), (IMPACT + 5, -0.035, -0.012, 18, 6, -1, 26, 8), (IMPACT + 14, -0.05, -0.03, 26, 2, -3, 28, 0),
        (1006, -0.03, -0.035, 22, -2, 0, 22, -2), (1146, -0.03, -0.035, 21, -2, 0, 24, -4),
        (1147, -0.03, -0.035, 21, -2, 0, 24, -4), (1172, -0.03, -0.03, 18, -2, 0, 14, -6), (1192, -0.03, -0.035, 21, -2, 0, 30, -4),
        (1212, -0.02, -0.025, 14, 0, 1, 14, -8), (1232, -0.01, -0.01, 7, 0, 1, -2, -12), (1273, -0.01, -0.006, 6, 0, 1, 0, -14)]
for f, dx, dz, fl, tw, sd, hp, hy in BODY:
    WH.key_root(f, Vector((POS.x + dx, POS.y, rh + dz)), yaw=YAW, flex=fl * 0.25, side=sd)
    WH.key_spine(f, flex=fl, twist=tw, side=sd, head=(hp, hy))
# breathing on every visible frame range (never a frozen hold), relief nods at the end
def nod(f): return sum(a * math.exp(-((f - c) / 4.0) ** 2) for c, a in ((1248, 7), (1260, 5)))
for a, b in ((1, 100), (1006, 1273)):
    for f in range(a, b + 1, 6):
        base = [k for k in BODY if k[0] <= f][-1]; nxt = [k for k in BODY if k[0] >= f][0]
        u = 0 if nxt[0] == base[0] else (f - base[0]) / (nxt[0] - base[0])
        lerp = lambda i: base[i] + (nxt[i] - base[i]) * u
        amp = 1.0 if f < 100 else (2.2 if f < 1215 else 1.2)
        b_ = math.sin(2 * math.pi * T(f) / (1.4 if f < 100 else (0.9 if f < 1215 else 1.6))) * amp
        WH.key_spine(f, flex=lerp(3) + b_, twist=lerp(4), side=lerp(5), head=(lerp(6) + 0.5 * b_ + nod(f), lerp(7)))
# face: lids softened (no stare), blinks, eyes follow what she looks at, mouth closed or slightly parted
GAZE = [(1, 14), (40, 12), (92, 10), (1006, 12), (1146, 10), (1172, 14), (1192, 18), (1215, 2), (1232, -4), (1273, -2)]
for f, g in GAZE:
    for s_ in "LR": kq(W, "eye." + s_, f, (1, 0, 0), g)
for f in (1, 92, 1006, 1215, 1240, 1273):
    for s_ in "LR": kq(W, "orbicularis03." + s_, f, (1, 0, 0), {1215: -10, 1240: -9}.get(f, -6))
def blink(obj, f, base=-6):
    for s_ in "LR":
        b_ = "orbicularis03." + s_
        if b_ not in obj.pose.bones: continue
        for ff, ang in ((f - 3, base), (f, -27), (f + 1, -27), (f + 4, base)): kq(obj, b_, ff, (1, 0, 0), ang)
for f in (26, 1030, 1098, 1180, 1226, 1266): blink(W, f)
for f, a in ((1, 0), (IMPACT, 0), (IMPACT + 4, 3), (1006, 2.5), (1146, 2.5), (1212, 2), (1228, 4), (1242, 1.5), (1273, 0.5)):
    kq(W, "jaw", f, (1, 0, 0), a)

# hands ---------------------------------------------------------------
def hand(s, f, p, d, n, pole): WH.key_hand(s, f, wpt(*p), Vector(d), Vector(n), wpt(*pole))
# left: holds the box palm-up in front of her chest (cup), lets go at the hit, then presses flat on the wound, lifts to look, rests
LH = [(1, (0.30, 0.17, 1.08), (0.35, 0.45, 0.2), (0, 0, 1), (-0.2, 0.9, 0.7)), (88, (0.30, 0.17, 1.08), (0.35, 0.45, 0.2), (0, 0, 1), (-0.2, 0.9, 0.7)),
      (IMPACT + 6, (0.31, 0.32, 1.06), (0.4, 0.3, -0.2), (0, 0, 1), (-0.15, 0.95, 0.95)),
      (IMPACT + 18, (0.42, 0.20, 1.02), (0.1, -0.9, 0.3), (-1, 0, 0), (0.05, 0.95, 1.05)),
      (125, (0.34, 0.12, 0.98), (0.1, -0.9, 0.3), (-1, 0, 0), (0.05, 0.95, 1.05))]
for k in LH: hand("L", *k)
# right: carries the basket by its handle (hanging), drops it on the hit, then rests open by her side
for f, dx in ((1, 0.14), (20, 0.17), (40, 0.13), (70, 0.16), (IMPACT, 0.15)):     # relaxed hanging arm, elbow softly bent, small swing with her weight shift
    hand("R", f, (dx, -0.30, 0.93), (0.4, 0.1, -0.9), (0, 1, 0), (-0.3, -0.6, 1.0))
for f, p in ((IMPACT + 6, "open_alarm"), (118, "flat_palm"), (1160, "flat_palm"), (1170, "relaxed"), (1200, "relaxed"), (1245, "flat_palm"), (1273, "flat_palm")):
    apply_pose(W, "L", p, f)
for f, p in ((1, "flat_palm"), (FEND, "flat_palm")):
    apply_pose(W, "R", p, f)

# the box (our logo on its front) stands on her left palm in front of her chest; grip_object closes the fingers on it
_bx = bmesh.new(); bmesh.ops.create_cube(_bx, size=1.0)
for v in _bx.verts: v.co = Vector((v.co.x * 0.15, v.co.y * 0.06, v.co.z * 0.2))
bmesh.ops.bevel(_bx, geom=list(_bx.edges) + list(_bx.verts), offset=0.003, segments=1, affect='EDGES')
pme = bpy.data.meshes.new("PickBox"); _bx.to_mesh(pme); _bx.free()
pme.uv_layers.new(name="UVMap"); pme.materials.append(bpy.data.materials["M_pack08"])
pbox = bpy.data.objects.new("PickBox", pme); bpy.data.collections["REAL"].objects.link(pbox)
BC = wpt(0.39, 0.15, 1.16)
_d = Vector((1.4, -0.3)) - BC.xy; BYAW = math.atan2(_d.x, -_d.y)            # front face (local -y) toward the shot-A camera
BROT = (Matrix.Rotation(BYAW, 3, 'Z') @ Matrix.Rotation(math.radians(-6), 3, 'X') @ Matrix.Rotation(math.radians(28), 3, "Y")).to_euler('XYZ')
for f in (1, 30, 60, 88, IMPACT + 2):
    bob = 0.0
    pbox.location = BC + Vector((0, 0, bob)); pbox.rotation_euler = BROT
    pbox.keyframe_insert("location", frame=f); pbox.keyframe_insert("rotation_euler", frame=f)
for f in (1, 30, 60, 88):
    sc.frame_set(f); Mb_ = pbox.matrix_world; bot = Mb_ @ Vector((0.06, 0, -0.1))
    rep = grip_object(W, "L", f, pbox, bot, (Mb_.to_3x3() @ Vector((0, 0, 1))).normalized(), finger_dir=(Mb_.to_3x3() @ Vector((-1, 0, 0))).normalized())
    print("GRIP_BOX", f, rep)
for f, dp, rr, z in ((IMPACT + 5, (0.06, 0.02, -0.09), (0.15, 0.05, 0.05), None), (IMPACT + 12, (0.12, 0.02, -0.40), (0.6, 0.15, 0.2), None), (IMPACT + 20, (0.16, 0.03, 0), (1.5708, 0.3, 0.3), 0.032),
                     (IMPACT + 24, (0.17, 0.03, 0), (1.5708, 0.32, 0.3), 0.05), (IMPACT + 28, (0.18, 0.03, 0), (1.5708, 0.33, 0.3), 0.032), (FEND, (0.18, 0.03, 0), (1.5708, 0.33, 0.3), 0.032)):
    pbox.location = (BC.x + dp[0], BC.y + dp[1], z if z is not None else BC.z + dp[2]); pbox.rotation_euler = (BROT.x + rr[0], BROT.y + rr[1], BROT.z + rr[2])
    pbox.keyframe_insert("location", frame=f); pbox.keyframe_insert("rotation_euler", frame=f)

# basket with carry handle; its top bar sits in her curled right hand; dropped at the hit
bk = bpy.data.objects["Basket"]
_hb = bmesh.new(); _pts = [Vector((-0.205 + 0.41 * i / 16, 0, 0.095 + 0.175 * math.sin(math.pi * i / 16))) for i in range(17)]
_rings = []
for i, c in enumerate(_pts):
    tng = (_pts[min(i + 1, 16)] - _pts[max(i - 1, 0)]).normalized(); q = tng.to_track_quat('Z', 'Y')
    _rings.append([_hb.verts.new(c + q @ Vector((0.007 * math.cos(2 * math.pi * k / 10), 0.007 * math.sin(2 * math.pi * k / 10), 0))) for k in range(10)])
for r1, r2 in zip(_rings, _rings[1:]):
    for k in range(10): _hb.faces.new((r1[k], r1[(k + 1) % 10], r2[(k + 1) % 10], r2[k])).smooth = True
hme = bpy.data.meshes.new("BasketHandle"); _hb.to_mesh(hme); _hb.free(); hme.materials.append(bpy.data.materials["M_basket"])
handle = bpy.data.objects.new("BasketHandle", hme); bpy.data.collections["REAL"].objects.link(handle); handle.parent = bk
def wristM(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["wrist.R"].matrix
sc.frame_set(1); _pb = W.pose.bones; _mw = W.matrix_world
_wr = _mw @ _pb["wrist.R"].head; _k3 = _mw @ _pb["finger3-1.R"].head
_kax = (_mw @ _pb["finger5-1.R"].head) - (_mw @ _pb["finger2-1.R"].head)
_nrm = (_k3 - _wr).cross(_kax).normalized()
if _nrm.dot((_mw @ _pb["finger1-3.R"].tail) - _wr) < 0: _nrm = -_nrm
_hook = [_mw @ _pb['finger%d-%d.R' % (k, j)].head for k in (2, 3, 4, 5) for j in (1, 2, 3)] + [_mw @ _pb['finger%d-3.R' % k].tail for k in (2, 3, 4, 5)]
_grip = sum(_hook, Vector()) / len(_hook)
# fine-tune: the bar (7 mm radius, along the knuckle axis) sits where the curled finger bones clear it best (finger ~8 mm thick)
_ax = _kax.normalized(); _fs = []
for k in (2, 3, 4, 5):
    for j in (1, 2, 3):
        _h = _mw @ _pb['finger%d-%d.R' % (k, j)].head; _t = _mw @ _pb['finger%d-%d.R' % (k, j)].tail
        _fs += [_h.lerp(_t, u) for u in (0.0, 0.5, 1.0)]
_pal = [_mw @ _pb['metacarpal%d.R' % k].tail for k in (1, 2, 3, 4) if 'metacarpal%d.R' % k in _pb]
def _pen(c):
    e = 0.0
    for q in _fs + _pal:
        d = q - c; d = d - _ax * d.dot(_ax); e += max(0.0, 0.0155 - d.length) ** 2
    return e
_best = (_pen(_grip), _grip)
for i in range(-6, 7):
    for j in range(-6, 7):
        for k in range(-6, 7):
            c = _grip + Vector((i, j, k)) * 0.003; c = c - _ax * (c - _grip).dot(_ax); v = _pen(c)
            if v < _best[0] - 1e-12 or (abs(v - _best[0]) < 1e-12 and (c - _grip).length < (_best[1] - _grip).length): _best = (v, c)
print("BAR", _pen(_grip), _best[0], (_best[1] - _grip).length); _grip = _best[1]
_bkM = Matrix.Translation(_grip) @ Matrix.Rotation(math.atan2(_kax.y, _kax.x), 4, 'Z') @ Matrix.Translation((0, 0, -0.27))
OFF = wristM(1).inverted() @ _bkM
for f in (1, FEND):
    bk.location = (POS.x + 0.30, POS.y - 0.47, 0.101); bk.rotation_euler = (0, 0, 0.15); bk.keyframe_insert("location", frame=f); bk.keyframe_insert("rotation_euler", frame=f)
# our logo: white on the basket's long sides, dark on the box front (in-scene, flat to camera in shot A)
def logo_decal(name, img, parent, loc, rot, width):
    im = bpy.data.images.load(os.path.join(HERE, "..", "assets", "tex", img)); im.pack()
    m = bpy.data.materials.new("M_" + name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N["Principled BSDF"]; tx = N.new("ShaderNodeTexImage"); tx.image = im; tx.extension = 'CLIP'
    L.new(tx.outputs["Color"], b.inputs["Base Color"]); L.new(tx.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.5
    bm_ = bmesh.new(); h = width * 414 / 967
    vs = [bm_.verts.new((x * width / 2, 0, z * h / 2)) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f_ = bm_.faces.new(vs); uv = bm_.loops.layers.uv.new("UVMap")
    for l, (u, v) in zip(f_.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = (u, v)
    me = bpy.data.meshes.new(name); bm_.to_mesh(me); bm_.free(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); bpy.data.collections["REAL"].objects.link(o); o.parent = parent; o.location = loc; o.rotation_euler = rot
    return o
logo_decal("LogoBasketA", "DaKrasFilms_logo_white.png", bk, (0, -0.1415, 0.0), (0, 0, 0), 0.3)
logo_decal("LogoBasketB", "DaKrasFilms_logo_white.png", bk, (0, 0.1415, 0.0), (0, 0, math.pi), 0.3)
logo_decal("LogoBox", "DaKrasFilms_logo_dark.png", pbox, (0, -0.0315, 0.02), (0, 0, 0), 0.13)

# ================================================================== background people (A walks in with his cart, C browses, stocker, B crosses)
A = bpy.data.objects["ShopperA"]; AR = make_human_ctrl(A); AH = Human(AR); A.location.z = 0.015; add_hand_limits(A)
cart = bpy.data.objects["Cart"]
def pathA(f): return Vector((-6.4 + 4.4 * (f - 1) / (FEND - 1), -0.35, 0))
AH.walk(pathA, lambda f: 90.0, 1, FEND, stride=0.45, lift=0.06)
cart.location = (-9.0, -3.6, 0.0); cart.keyframe_insert("location", frame=1)          # parked out of the way
for f in range(1, FEND + 1, 6):
    p = pathA(f); ph = math.sin(2 * math.pi * f / 96.0)
    for s, dy, sg in (("L", 0.33, 1), ("R", -0.33, -1)):
        AH.key_hand(s, f, Vector((p.x + 0.10 * ph * sg + 0.05, p.y + dy, 0.93)), Vector((0.25, 0.1 * sg, -1)), Vector((0, -sg, 0)), Vector((p.x - 0.4, p.y + 2.2 * dy, 1.05)))
for s in "LR": apply_pose(A, s, "relaxed", 1); apply_pose(A, s, "relaxed", FEND)
STK = bpy.data.objects["Stocker"]; SR = make_human_ctrl(STK); SH = Human(SR); STK.location.z = 0.015; add_hand_limits(STK)
spos = Vector((-7.4, -0.55, 0))
for s_ in "LR":
    for f in (1, FEND): SH.key_foot(s_, f, SH.foot_xy(s_, spos, 0.0), 0.0)
_bx = bmesh.new(); bmesh.ops.create_cube(_bx, size=1.0)
for v in _bx.verts: v.co = Vector((v.co.x * 0.34, v.co.y * 0.22, v.co.z * 0.24))
cme = bpy.data.meshes.new("Carton"); _bx.to_mesh(cme); _bx.free(); cme.materials.append(bpy.data.materials["M_pack05"])
carton = bpy.data.objects.new("Carton", cme); bpy.data.collections["REAL"].objects.link(carton)
for f, fl, tw, hy, cz in ((1, 8, 0, -10, 1.02), (60, 12, -4, -14, 1.08), (120, 6, 10, 30, 1.0), (1147, 4, 14, 40, 0.98), (FEND, 3, 16, 44, 0.98)):
    SH.key_root(f, Vector((spos.x, spos.y, SH.root_head.z - 0.015)), yaw=0.0, flex=fl * 0.3); SH.key_spine(f, flex=fl, twist=tw, head=(-6 + fl * 0.5, hy))
    c = Vector((spos.x, -0.86, cz)); carton.location = c; carton.keyframe_insert("location", frame=f)
    for s_, sx in (("L", 1), ("R", -1)):
        SH.key_hand(s_, f, c + Vector((sx * 0.2, 0.02, -0.02)), Vector((-sx * 0.3, -1, 0.1)), Vector((-sx, 0, 0)), Vector((spos.x + sx * 0.5, spos.y + 0.3, 1.0)))
for s in "LR": apply_pose(STK, s, "flat_palm", 1); apply_pose(STK, s, "flat_palm", FEND)
SCo = bpy.data.objects["ShopperC"]; CR_ = make_human_ctrl(SCo); CH = Human(CR_); add_hand_limits(SCo)
cpos = Vector((-2.1, 0.62, 0))
for s_ in "LR":
    for f in (1, FEND): CH.key_foot(s_, f, CH.foot_xy(s_, cpos, 0.0), 0.0)
for f, tw, hy, hp in ((1, 0, -10, 12), (60, 4, -4, 16), (110, 22, 45, 0), (1147, 28, 55, -2), (FEND, 30, 58, -2)):
    CH.key_root(f, Vector((cpos.x, cpos.y, CH.root_head.z - 0.01)), yaw=0.0); CH.key_spine(f, flex=4, twist=tw, head=(hp, hy))
for s, sx in (("L", -1), ("R", 1)):
    for f in (1, FEND):
        CH.key_hand(s, f, Vector((cpos.x + 0.27 * -sx, cpos.y - 0.03, 0.84)), Vector((0, -0.15, -1)), Vector((sx, 0, 0)), Vector((cpos.x - 0.5 * sx, cpos.y + 0.4, 1.1)))
    apply_pose(SCo, s, "relaxed", 1)
Bp = bpy.data.objects["ShopperB"]; BR_ = make_human_ctrl(Bp); BH = Human(BR_); add_hand_limits(Bp)
def pathB(f):
    t = min(T(f), 2.3) if f <= 180 else 2.3; return Vector((-9.75, -3.2 + 1.25 * t, 0))
BH.walk(pathB, lambda f: 180.0, 1, 139, stride=0.7)
bpos = pathB(139)
for s in "LR":
    for f in (139, FEND): BH.key_foot(s, f, BH.foot_xy(s, bpos, 180.0), 180.0)
for f, hy in ((139, 0), (175, 55), (FEND, 60)):
    BH.key_root(f, Vector((bpos.x, bpos.y, BH.root_head.z - 0.02)), yaw=180.0); BH.key_spine(f, twist=30 if f > 139 else 0, head=(0, hy))
for s, sx in (("L", -1), ("R", 1)):
    for f in (1, 139, FEND):
        p = pathB(f); BH.key_hand(s, f, Vector((p.x + 0.27 * sx, p.y + 0.03, 0.84)), Vector((0, 0.15, -1)), Vector((-sx, 0, 0)), Vector((p.x + 0.5 * sx, p.y - 0.4, 1.1)))
    apply_pose(Bp, s, "relaxed", 1)
for rig in (A, STK, SCo, Bp):
    for f in (40, 1030, 1200): blink(rig, f + random.randint(0, 30), 0)

# ================================================================== impact point on her shirt (at the impact frame), wound mark, dimple, ripple
tee = bpy.data.objects["Woman.female_casualsuit01"]
sc.frame_set(IMPACT); dg = bpy.context.evaluated_depsgraph_get(); te = tee.evaluated_get(dg)
o_ = tee.matrix_world.inverted() @ Vector((3.0, POS.y - 0.02, 1.0)); d_ = tee.matrix_world.inverted().to_3x3() @ Vector((-1, 0, 0))
hit, loc, nrm, idx = te.ray_cast(o_, d_)
P = tee.matrix_world @ loc; PN = (tee.matrix_world.to_3x3() @ nrm).normalized()
print("IMPACT", P, PN)
# impact helpers ride on her belly bone so the dimple, ripple and wound mark move with her
imp = bpy.data.objects.new("ImpactCtl", None); sc.collection.objects.link(imp); imp.parent = W; imp.parent_type = 'BONE'; imp.parent_bone = "spine03"
bpy.context.view_layer.update(); imp.matrix_world = Matrix.Translation(P) @ Matrix.Rotation(math.pi, 4, 'Z')
we_to = bpy.data.objects.new("WarpTo", None); sc.collection.objects.link(we_to); we_to.parent = imp
for f, dd in ((IMPACT - 1, 0.0), (IMPACT, 0.0), (IMPACT + 5, 0.012), (IMPACT + 9, 0.016), (IMPACT + 14, 0.003), (IMPACT + 20, 0.0)):
    we_to.location = (dd, 0, 0); we_to.keyframe_insert("location", frame=f)
wm = tee.modifiers.new("Dimple", 'WARP'); wm.object_from = imp; wm.object_to = we_to; wm.falloff_radius = 0.035; wm.falloff_type = 'SMOOTH'
wv = tee.modifiers.new("Ripple", 'WAVE'); wv.start_position_object = imp; wv.use_normal = True; wv.use_x = wv.use_y = True
wv.height = 0.003; wv.width = 0.03; wv.narrowness = 1.2; wv.speed = 0.006; wv.time_offset = IMPACT; wv.lifetime = 50; wv.damping_time = 35; wv.falloff_radius = 0.2
th = bpy.data.objects["TeeHole"]
# shirt hole that reads on navy fabric: near-black core, pale frayed fibre ring (no blood)
thm = bpy.data.materials.new("M_TeeHole"); thm.use_nodes = True; tn = thm.node_tree; TN = tn.nodes; TL = tn.links
tb_ = TN["Principled BSDF"]; tco = TN.new("ShaderNodeTexCoord"); tln = TN.new("ShaderNodeVectorMath"); tln.operation = 'LENGTH'
TL.new(tco.outputs["Object"], tln.inputs[0])
tnz = TN.new("ShaderNodeTexNoise"); tnz.inputs["Scale"].default_value = 60.0; TL.new(tco.outputs["Object"], tnz.inputs["Vector"])
tad = TN.new("ShaderNodeMath"); tad.operation = 'MULTIPLY_ADD'; tad.inputs[1].default_value = 0.06; tad.inputs[2].default_value = -0.03
TL.new(tnz.outputs["Fac"], tad.inputs[0]); tsum = TN.new("ShaderNodeMath"); tsum.operation = 'ADD'; TL.new(tln.outputs["Value"], tsum.inputs[0]); TL.new(tad.outputs[0], tsum.inputs[1])
trp = TN.new("ShaderNodeValToRGB"); TL.new(tsum.outputs[0], trp.inputs["Fac"]); cr_ = trp.color_ramp
cr_.elements[0].position = 0.0; cr_.elements[0].color = (0.01, 0.008, 0.008, 1); cr_.elements[1].position = 0.2; cr_.elements[1].color = (0.0, 0.0, 0.0, 0)
e1 = cr_.elements.new(0.095); e1.color = (0.015, 0.01, 0.01, 1); e2 = cr_.elements.new(0.11); e2.color = (0.55, 0.58, 0.68, 1); e3 = cr_.elements.new(0.17); e3.color = (0.42, 0.46, 0.58, 1)
TL.new(trp.outputs["Color"], tb_.inputs["Base Color"]); TL.new(trp.outputs["Alpha"], tb_.inputs["Alpha"]); tb_.inputs["Roughness"].default_value = 0.9
th.data = th.data.copy(); th.data.materials.clear(); th.data.materials.append(thm)
th.parent = imp; th.matrix_parent_inverse = Matrix.Identity(4)
th.location = (-0.0015 / S * 0 - 0.001, 0, 0); th.rotation_euler = (0, 0, 0)
th.scale = (S, 1e-4, 1e-4); th.keyframe_insert("scale", frame=1); th.keyframe_insert("scale", frame=IMPACT + 2)
th.scale = (S, S * 2.0, S * 2.0); th.keyframe_insert("scale", frame=IMPACT + 10); th.keyframe_insert("scale", frame=FEND)
# the hole decal mesh sits at x = -0.065 macro units; at real scale that is -1.6 mm (just outside the shirt): keep it

from mathutils.bvhtree import BVHTree as _BVH
_body = bpy.data.objects["Woman.body"]; _gi = {g.index: g.name for g in _body.vertex_groups if g.name in W.data.bones}
_HAND = {sd: [v.index for v in _body.data.vertices
              if any(g.weight > 0.5 and _gi.get(g.group, "").startswith(("finger", "metacarpal")) and _gi[g.group].endswith("." + sd) for g in v.groups)] for sd in "LR"}
_ARM = {v.index for v in _body.data.vertices
        if max(((g.weight, _gi.get(g.group, "")) for g in v.groups if g.group in _gi), default=(0, ""))[1].startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "shoulder", "clavicle"))}
for _m in _body.modifiers:
    if _m.type != 'ARMATURE': _m.show_viewport = False
def _hits(dg, sd="L"):
    e = _body.evaluated_get(dg); me = e.to_mesh(); mw = _body.matrix_world
    V = [mw @ v.co for v in me.vertices]; Pp = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
    tb = _BVH.FromPolygons(V, [p for p in Pp if not any(i in _ARM for i in p)])
    et = tee.evaluated_get(dg); mt = et.to_mesh(); tv = [tee.matrix_world @ v.co for v in mt.vertices]; tp = [tuple(p.vertices) for p in mt.polygons]; et.to_mesh_clear()
    tt = _BVH.FromPolygons(tv, tp); n = 0
    for i in _HAND[sd]:
        q = V[i]
        for t in (tb, tt):
            loc, nr, _i, d = t.find_nearest(q, 0.05)
            if loc is not None and d > 0.003 and (q - loc).dot(nr) < 0: n += 1; break
    return n
def settle(f, nrm, sd="L", extra=0.004):
    pb = W.pose.bones["IK_hand." + sd]; step = W.data.bones["IK_hand." + sd].matrix_local.to_3x3().inverted() @ (W.matrix_world.inverted().to_3x3() @ (nrm * 0.003))
    loc0 = pb.location.copy()
    for it in range(30 if sd == "L" else 14):
        sc.frame_set(f); h = _hits(bpy.context.evaluated_depsgraph_get(), sd)
        if h <= 1: break
        pb.location = pb.location + step; pb.keyframe_insert("location", frame=f, group=pb.name)
    if h > 300:     # the whole hand flagged = a false 'inside' at a cloth fold, not a real overlap: keep the placed hand, just a little air
        pb.location = loc0 + step * 2; pb.keyframe_insert("location", frame=f, group=pb.name)
    pb.location = pb.location + step * (extra / 0.003); pb.keyframe_insert("location", frame=f, group=pb.name)   # a hair of air: reads ON, never IN
    print("SETTLE", sd, f, it, h)
def hip(f):
    sc.frame_set(f); dg_ = bpy.context.evaluated_depsgraph_get(); te_ = tee.evaluated_get(dg_); mi = tee.matrix_world.inverted()
    o_ = wpt(0.03, -0.7, 0.97); ok, lc, nr, _i = te_.ray_cast(mi @ o_, mi.to_3x3() @ Vector((0, 1, 0)))
    c = tee.matrix_world @ lc; n = (tee.matrix_world.to_3x3() @ nr).normalized()
    if n.y > 0: n = -n
    place_hand(W, "R", f, c, -n, Vector((0.45, 0, -1)).normalized(), skin=0.015); settle(f, n, "R")
def rbelly(f):
    sc.frame_set(f); c = imp.matrix_world.translation.copy(); n = (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
    place_hand(W, "R", f, c + Vector((0, -0.115, -0.09)), -n, Vector((0.0, 0.5, -0.85)).normalized(), skin=0.02); settle(f, n, "R")
apply_pose(W, "R", "relaxed", 1); apply_pose(W, "R", "relaxed", IMPACT)
hand("R", IMPACT + 5, (0.42, -0.27, 1.08), (0.4, -0.2, 0.3), (0, 1, 0), (-0.35, -0.9, 1.05)); apply_pose(W, "R", "open_alarm", IMPACT + 5)
apply_pose(W, "R", "flat_palm", 1006)
for f in (1006, 1040, 1080, 1120, 1146, 1180, 1215, 1245, 1273): rbelly(f)
def wound(f, lift=0.0, dz=0.0, dy=0.0):
    sc.frame_set(f); c = imp.matrix_world.translation.copy(); n = (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
    place_hand(W, "L", f, c + n * lift + Vector((0, 0.015 + dy, dz)), -n, Vector((0, -1, 0.35)).normalized(), skin=0.02)
    settle(f, n)
for f, lift, dz, dy in ((1006, 0.0, 0.0, 0), (1030, 0.0, 0.0, 0), (1060, 0.0, 0.0, 0), (1090, 0.0, 0.0, 0), (1120, 0.0, 0.0, 0), (1146, 0.0, 0.0, 0),
                        (1160, 0.0, 0.0, 0), (1167, 0.12, 0.06, 0.03), (1197, 0.10, -0.02, 0.10), (1243, 0.06, 0.03, 0.04), (1250, 0.0, 0.02, 0), (1256, 0.012, 0.02, 0), (1262, 0.0, 0.02, 0), (1268, 0.012, 0.02, 0), (1273, 0.012, 0.02, 0)):
    wound(f, lift, dz, dy)
# she lifts her hand and checks her palm (nothing on it), then lowers it to her side while she looks at the hole
for f in (1176, 1190):
    sc.frame_set(f); fc_ = W.matrix_world @ W.pose.bones["head"].head; pp = wpt(0.38, 0.06, 1.12)
    place_hand(W, "L", f, pp, (fc_ - pp).normalized(), Vector((0.25, -0.35, 0.9)).normalized(), skin=0.0)
for f in (1206, 1234):      # hand away from the hole, hanging relaxed clear of her hip while she looks at the hole
    hand("L", f, (0.12, 0.36, 0.88), (0.2, 0.05, -1), (0, -1, 0), (0.0, 0.95, 1.05))
for _m in _body.modifiers: _m.show_viewport = True
# ================================================================== bullet: through the shop window, down the aisle, into her shirt
bul = bpy.data.objects["Bullet"]; bul.rotation_mode = 'QUATERNION'
XWIN = 12.0
def bullet_store(f):
    """tip position (world) for the store shots"""
    if f <= 52: x = XWIN + 0.3 - (f - 41) * 0.075                          # punches through the glass at f45 (slow motion)
    else:
        u = (f - 53) / (IMPACT - 53); x = (XWIN + 0.3 - 11 * 0.075) + (P.x - (XWIN + 0.3 - 11 * 0.075)) * min(1.0, u ** 0.85)
    return Vector((x, P.y, P.z))
spin = 0.0
for f in range(1, FEND + 1):
    spin += 0.08
    if is_real(f):
        tip = bullet_store(f)
        Mb = Matrix.Translation(tip) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Translation((-0.6 * S, 0, 0)) @ Matrix.Rotation(spin, 4, 'X') @ Matrix.Diagonal((S, S, S, 1))
    else:
        Mb = None
    if Mb is not None:
        lo, ro, scl = Mb.decompose()
        if bul.rotation_quaternion.dot(ro) < 0: ro = -ro
        bul.location = lo; bul.rotation_quaternion = ro; bul.scale = scl
        for p_ in ("location", "rotation_quaternion", "scale"): bul.keyframe_insert(p_, frame=f)
# store bullet is only on screen in B and C (until it is in the dimple); macro bullet is a separate copy on the macro root
bul.hide_render = True; bul.keyframe_insert("hide_render", frame=1)
bul.hide_render = False; bul.keyframe_insert("hide_render", frame=41)
bul.hide_render = True; bul.keyframe_insert("hide_render", frame=IMPACT + 7)
bpy.data.objects.remove(bpy.data.objects["Trail"], do_unlink=True)          # the white stub at the base is gone
# shop window: entry hole + crack star appear as the bullet punches through (keyed scale, no Scene Time)
cm = bpy.data.materials.new("M_crack"); cm.use_nodes = True; nt = cm.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 30.0
L.new(tc.outputs["Object"], vo.inputs["Vector"])
gr = N.new("ShaderNodeMath"); gr.operation = 'LESS_THAN'; gr.inputs[1].default_value = 0.022; L.new(vo.outputs["Distance"], gr.inputs[0])
rad = N.new("ShaderNodeVectorMath"); rad.operation = 'LENGTH'; L.new(tc.outputs["Object"], rad.inputs[0])
fall = N.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = 0.2
fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0; L.new(rad.outputs["Value"], fall.inputs["Value"])
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(gr.outputs[0], mul.inputs[0]); L.new(fall.outputs["Result"], mul.inputs[1])
core = N.new("ShaderNodeMath"); core.operation = 'LESS_THAN'; core.inputs[1].default_value = 0.012; L.new(rad.outputs["Value"], core.inputs[0])
mx_ = N.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; L.new(mul.outputs[0], mx_.inputs[0]); L.new(core.outputs[0], mx_.inputs[1])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1); em.inputs["Strength"].default_value = 1.5
tr = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader"); L.new(mx_.outputs[0], ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
L.new(ms.outputs[0], mo.inputs["Surface"])
_c = bmesh.new(); bmesh.ops.create_circle(_c, cap_ends=True, segments=48, radius=0.5)
cme2 = bpy.data.meshes.new("Crack"); _c.to_mesh(cme2); _c.free(); cme2.materials.append(cm)
crack = bpy.data.objects.new("WindowCrack", cme2); bpy.data.collections["REAL"].objects.link(crack)
crack.location = (XWIN - 0.012, P.y, P.z); crack.rotation_euler = (0, math.radians(-90), 0)
for f, s_ in ((1, 0.001), (44, 0.001), (46, 0.55), (51, 1.0), (FEND, 1.0)):
    crack.scale = (s_, s_, s_); crack.keyframe_insert("scale", frame=f)
# glass sparkle: a few tiny shards that fly off the hole, keyed
shm = bpy.data.materials.new("M_shard"); shm.use_nodes = True; shm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
shm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.05
for i in range(14):
    _s = bmesh.new(); bmesh.ops.create_icosphere(_s, subdivisions=0, radius=0.006); sme = bpy.data.meshes.new("Shard"); _s.to_mesh(sme); _s.free(); sme.materials.append(shm)
    o = bpy.data.objects.new("Shard%02d" % i, sme); bpy.data.collections["REAL"].objects.link(o)
    v = Vector((-random.uniform(0.4, 1.2), random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.7)))
    for f in (1, 44, 45, 52, 53):
        k = max(0, f - 45) / 60.0
        o.location = Vector((XWIN - 0.02, P.y, P.z)) + v * k + Vector((0, 0, -4.9 * k * k)); o.scale = (1, 1, 1) if 45 <= f <= 52 else (0, 0, 0)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)

# ================================================================== macro cross-section: its own static set (hard cuts, no in-body scale trick)
root = bpy.data.objects["MacroRoot"]; root.parent = None
MR = Matrix.Translation((0.0, 60.0, 5.0)) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((S, S, S, 1))
root.matrix_world = MR; bpy.context.view_layer.update()
# macro bullet: its own copy on the macro root
bm2 = bul.copy(); bm2.data = bul.data; bm2.animation_data_clear(); bm2.name = "BulletMacro"
bpy.data.collections["MACRO"].objects.link(bm2); bm2.parent = root; bm2.matrix_parent_inverse = Matrix.Identity(4)
bm2.rotation_mode = 'XYZ'; bm2.scale = (1, 1, 1)
# tip depth (macro units) per VO frame: touches the shirt 130, dimple, pierces 183, fast through fat (2 s), slows through fascia and muscle, stops 945
DK = [(101, -0.9), (130, 0.0), (183, 0.28), (200, 0.5), (330, 1.5), (450, 3.2), (580, 4.0), (714, 4.5), (828, 5.0), (900, 5.22), (945, 5.3), (1273, 5.3)]
Dfn = pchip(DK)
def D(f): return Dfn(f)
for f in range(95, 1010):
    moving = D(f + 1) - D(f) > 1e-4
    bm2.location = (D(f) - 0.6, 0, 0); bm2.rotation_euler = (0.035 * min(f, 945), 0, 0)
    bm2.keyframe_insert("location", frame=f); bm2.keyframe_insert("rotation_euler", frame=f)
# flush layers (no recessed pale band), tissue-tinted fascia, and a backing plane so no void shows between layers
for nm in ("M_Fascia",):
    o = bpy.data.objects.get(nm)
    if o: o.location.y = -YB_ / 2
fm = bpy.data.materials.get("M_fascia")
if fm: fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.72, 0.42, 0.38, 1)
for on_, col_ in (("M_Dermis", (0.86, 0.48, 0.44, 1)), ("M_Epidermis", (0.93, 0.72, 0.6, 1))):      # skin layers read as distinct bands
    o_ = bpy.data.objects.get(on_)
    if o_ and o_.active_material:
        m_ = o_.active_material.copy(); o_.data.materials[0] = m_
        bs_ = m_.node_tree.nodes.get("Principled BSDF")
        mx_ = bs_.inputs["Base Color"].links[0].from_node if bs_.inputs["Base Color"].is_linked else None
        if mx_ is not None and mx_.bl_idname == "ShaderNodeMix":
            for i_ in mx_.inputs:
                if i_.name == "A" and i_.type == 'RGBA': i_.default_value = col_
                if i_.name == "Factor" and i_.type == 'VALUE' and not i_.is_linked: i_.default_value = 0.2
        elif bs_: bs_.inputs["Base Color"].default_value = col_
        print("SKINCOL", on_, bs_.inputs["Base Color"].is_linked if bs_ else None)
_bk = bmesh.new(); bmesh.ops.create_grid(_bk, x_segments=1, y_segments=1, size=1.0)
for v in _bk.verts: v.co = Vector(((v.co.x + 1) / 2 * 7.4 - 0.2, -YB_ - 0.05, v.co.y * 12.0))
bkme = bpy.data.meshes.new("M_Backing"); _bk.to_mesh(bkme); _bk.free()
bkm = bpy.data.materials.new("M_backing"); bkm.use_nodes = True; bkm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.3, 0.26, 1)
bkme.materials.append(bkm); bko = bpy.data.objects.new("M_Backing", bkme); bpy.data.collections["MACRO"].objects.link(bko); bko.parent = root
# tissue response
def dimple_val(f):
    if f < 130: return 0.0
    if f < 186: return D(f)
    u = (f - 186) / 60.0; return 0.28 * math.exp(-u * 3.0) * math.cos(u * 14.0)
for nm, gain in (("M_Fabric", 1.0), ("M_Epidermis", 1.0), ("M_Dermis", 0.85)):
    o = bpy.data.objects[nm]; o.shape_key_add(name="Basis"); k = o.shape_key_add(name="dimple")
    for i, v in enumerate(o.data.vertices):
        r2 = v.co.y ** 2 + v.co.z ** 2; k.data[i].co = v.co + Vector((gain * math.exp(-r2 / 0.6), 0, 0))
    k.slider_min = -1
    for f in range(101, 330, 2):
        dv = dimple_val(f) + (0.07 if nm == "M_Fabric" and 130 <= f < 186 else 0.0)
        k.value = max(-0.5, min(1.0, dv)); k.keyframe_insert("value", frame=f)
    h = o.shape_key_add(name="hole", from_mix=False)
    for i, v in enumerate(o.data.vertices):
        rr = math.hypot(v.co.y, v.co.z)
        if rr < 0.5:
            dd = Vector((0, v.co.y, v.co.z)).normalized() if rr > 1e-4 else Vector((0, 0, 1))
            h.data[i].co = v.co + dd * (0.23 + (rr / 0.5) * 0.27 - rr) + Vector((0.06 * (1 - rr / 0.5), 0, 0))
    for f, hv in ((182, 0.0), (190, 1.0), (FEND, 1.0)): h.value = hv; h.keyframe_insert("value", frame=f)
bpy.data.objects.remove(bpy.data.objects["M_HoleDecal"], do_unlink=True)   # no floating disc
def vel(f): return (D(f + 2) - D(f - 2)) / 4 * FPS
tipctl = bpy.data.objects["TipCtl"]
for f in range(95, 1012, 2):
    e = min(1.0, max(0.0, vel(f) / 1.0)) if f > 186 else 0.0
    wob = (math.exp(-(f - 945) / 90.0) if f > 945 else 0.0) + (0.35 * math.exp(-(f - 186) / 50.0) if f > 186 else 0.0)
    tipctl.location = (D(f), e, wob); tipctl.keyframe_insert("location", frame=f)
# no rings at all (director): delete every ring object
for o in [o for o in bpy.data.objects if o.name.startswith("M_Ring")]: bpy.data.objects.remove(o, do_unlink=True)
# fat 'ahead of the tip' push switches on as the tip pierces into the fat (f183 = 3.03 s)
for nd in bpy.data.node_groups["FatLobulesGN"].nodes if "FatLobulesGN" in bpy.data.node_groups else []:
    if nd.bl_idname == "ShaderNodeMath" and nd.operation == 'GREATER_THAN' and abs(nd.inputs[1].default_value - 3.15) < 1e-6: nd.inputs[1].default_value = 3.0
# muscle fibres part exactly where the bullet tip is
for o in [o for o in bpy.data.objects if o.name.startswith("M_MuscleFib")]:
    ph = random.uniform(0, 6.28); x = o.location.x; yrow = o.location.y
    o.shape_key_add(name="Basis"); k = o.shape_key_add(name="part")
    for i, v in enumerate(o.data.vertices):
        k.data[i].co = v.co + Vector((0, -0.34 * math.exp(-(v.co.z / 0.3) ** 2) * (1.0 if yrow > -0.3 else 0.5), 0))
    for f in range(560, 1012, 2):
        d = D(f); k.value = max(0.0, min(1.0, (d - (x - 0.2)) / 0.18)); k.keyframe_insert("value", frame=f)
# bowel: drift (peristalsis) and its nearest loop brought up behind the peritoneum at the bullet's height (z only)
gr_ = bpy.data.objects.get("M_GutReal")
if gr_:
    cand = [v.co for v in gr_.data.vertices if 5.66 < v.co.x < 6.1 and abs(v.co.z) < 4.0]
    best_v = max(cand, key=lambda c: c.y - 0.15 * abs(c.z)); gr_.location = (0.0, 0.0, -best_v.z)
tex = bpy.data.textures.new("GutNoise", 'CLOUDS'); tex.noise_scale = 1.2
gnc = bpy.data.objects.new("GutNoiseCtl", None); sc.collection.objects.link(gnc); gnc.parent = root
for f in (1, FEND): gnc.location = (T(f) * 0.25, T(f) * 0.1, T(f) * 0.18); gnc.keyframe_insert("location", frame=f)
for o in [o for o in bpy.data.objects if o.name.startswith("M_Gut") and o.type == 'MESH' and "Bed" not in o.name]:
    dm = o.modifiers.new("peristalsis", 'DISPLACE'); dm.texture = tex; dm.texture_coords = 'OBJECT'; dm.texture_coords_object = gnc; dm.strength = 0.2
# vessels pulse
for o in [o for o in bpy.data.objects if o.name.startswith("M_Vessel")]:
    for f in range(95, 1012, 6):
        b_ = max(0.0, math.sin(2 * math.pi * T(f) * 1.33)) ** 3; o.scale = (1.0, 1.0 + 0.03 * b_, 1.0 + 0.03 * b_); o.keyframe_insert("scale", frame=f)

# ================================================================== visibility per shot (hide_render AND hide_viewport keyed together)
MACO = set(bpy.data.collections["MACRO"].all_objects)
REALO = [o for o in sc.objects if o not in MACO and o.type in ('MESH', 'LIGHT', 'CURVE') and o.name not in ("Bullet",)]
def key_vis(o, visible_fn):
    prev = None
    for f in range(1, FEND + 1):
        v = visible_fn(f)
        if v != prev:
            o.hide_render = not v; o.hide_viewport = not v
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f); prev = v
for o in REALO: key_vis(o, (lambda f: False) if (o.name == "Carton" or o.name.startswith("Stocker") or o.name == "Cart") else is_real)
for o in MACO: key_vis(o, lambda f: not is_real(f))
for a in bpy.data.actions:
    for lay in a.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("hide_render", "hide_viewport"):
                        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'

# ================================================================== camera: one camera, hard cuts between shots (constant keys at each cut)
cam = bpy.data.objects["CAM_Film"]; cd = cam.data; cam.rotation_mode = 'QUATERNION'
cd.sensor_fit = 'AUTO'; cd.sensor_width = 36
def look(cp, tg, up=Vector((0, 0, 1))):
    fwd = (tg - cp).normalized(); right = fwd.cross(up).normalized(); up2 = right.cross(fwd)
    return Matrix((right, up2, -fwd)).transposed().to_quaternion()
def face_pt(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["head"].head + Vector((0.05, 0, 0.04))
def macro_cam(f, tgt_off, az, el, dist):
    d = D(f); tg = Vector((d, 0, 0)) + Vector(tgt_off)
    cp = tg + dist * Vector((math.cos(math.radians(el)) * math.cos(math.radians(az)), math.cos(math.radians(el)) * math.sin(math.radians(az)), math.sin(math.radians(el))))
    return MR @ cp, MR @ tg, (MR.to_3x3() @ Vector((-1, 0, 0))).normalized(), dist * S
def lin(a, b, u): return a + (b - a) * u
def sm(u): return u * u * (3 - 2 * u)
MAC_DIST, MAC_LENS = 3.4, 45.0          # same distance and lens in every macro shot: the bullet never changes size
def shot_cam(f):
    for f0, f1, name in SHOTS:
        if f0 <= f <= f1: break
    u = sm((f - f0) / max(1, f1 - f0))
    if name == "A_shop":     # medium-close: her face and the logo box she is reading; slow push
        tg = face_pt(f).lerp(BC, 0.4); cp = lin(Vector((1.05, -0.28, 1.42)), Vector((0.95, -0.22, 1.40)), u); return cp, tg, Vector((0, 0, 1)), 35, 8.0
    if name == "W_window":   # the origin: the bullet punches through the shop window (crack star, shards), coming toward us
        tip = bullet_store(f); cp = Vector((XWIN - 0.85, P.y - 0.2, P.z + 0.04)); tg = Vector((XWIN, P.y, P.z)).lerp(tip, min(1.0, max(0.0, (f - 44) / 4)))
        return cp, tg, Vector((0, 0, 1)), 50, 22.0
    if name == "B_track":    # behind the bullet down the aisle: bullet big in the foreground, she is ahead in frame; it hits her stomach
        tip = bullet_store(f); stop_x = P.x + 0.42
        cx = max(tip.x, stop_x); k = 1.0 + 0.3 * u                               # the camera lags a little: the bullet pulls ahead in frame
        cp = Vector((cx + 0.13 * k, P.y - 0.01 * k, P.z + 0.028 * k))
        tg = Vector((min(cx, tip.x + 0.0) - 0.6, P.y, P.z)) if tip.x > stop_x else P + Vector((0.0, 0, 0.01))
        return cp, tg, Vector((0, 0, 1)), 40, 22.0
    if name == "D_react":    # front three-quarter, slightly low so her lowered face is seen; hand on the wound, other hand on her hip
        tg = face_pt(f).lerp(P, 0.45); cp = lin(Vector((1.25, -0.42, 1.12)), Vector((1.15, -0.36, 1.14)), u); return cp, tg, Vector((0, 0, 1)), 32, 8.0
    if name == "OP_relief":  # one continuous shot (no cut): checks her palm, looks at the hole, straightens, breathes out, nods, pats her belly
        tg = (face_pt(f) + Vector((0, 0, -0.06))).lerp(P, lin(0.45, 0.3, u)); cp = lin(Vector((1.35, -0.36, 1.22)), Vector((1.12, -0.24, 1.34)), u)
        return cp, tg, Vector((0, 0, 1)), 38, 8.0
    # macro: side-on (az 90), level, fixed distance; the camera half-follows so the bullet visibly travels down through each shot
    d0, d1 = D(f0), D(f1); dd = max(0.0, d1 - d0); k = max(0.0, min(0.85, 1.0 - 0.9 / dd)) if dd > 1e-3 else 0.0
    cdep = (d0 - 0.3 + 0.45) + k * (D(f) - d0)
    tg = Vector((cdep, 0, 0)); cpl = tg + MAC_DIST * Vector((0.0, math.cos(math.radians(4)), math.sin(math.radians(4))))
    return MR @ cpl, MR @ tg, (MR.to_3x3() @ Vector((-1, 0, 0))).normalized(), MAC_LENS, 45.0
prevq = None; CAMLOG = []
for f in range(1, FEND + 1):
    cp, tg, up, lens, fstop = shot_cam(f)
    q = look(cp, tg, up)
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = cp; cam.rotation_quaternion = q; cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = lens; cd.keyframe_insert("lens", frame=f)
    dist = (tg - cp).length
    cd.clip_start = dist * 0.55 if not is_real(f) else max(0.0005, min(0.05, dist * 0.05)); cd.keyframe_insert("clip_start", frame=f)   # macro: nothing near the lens can block it
    nm_ = next(n for a_, b_, n in SHOTS if a_ <= f <= b_)
    cd.dof.use_dof = nm_ not in ("W_window", "B_track"); cd.dof.keyframe_insert("use_dof", frame=f)   # bullet chase: everything sharp (bullet AND her)
    cd.dof.focus_distance = dist; cd.dof.aperture_fstop = fstop
    cd.dof.keyframe_insert("focus_distance", frame=f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
    CAMLOG.append((f, tuple(cp), tuple(tg)))
for a in bpy.data.actions:          # hard cuts: no interpolation between frames
    for lay in a.layers:
        for st in lay.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    if fc.data_path in ("location", "rotation_quaternion", "lens", "clip_start", "dof.focus_distance", "dof.aperture_fstop") and a.name.startswith(cam.name):
                        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# catchlight: a small light on the camera that shows only in glossy (eyes), not on the skin
cl = bpy.data.lights.new("Catchlight", 'POINT'); cl.energy = 3.0; cl.shadow_soft_size = 0.02
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = cam; clo.location = (0.05, 0.08, 0)
clo.visible_diffuse = False; clo.visible_transmission = False; clo.visible_volume_scatter = False
sc.frame_set(1240); dg = bpy.context.evaluated_depsgraph_get()
cam_p = cam.matrix_world.translation.copy(); fr = cd.view_frame(scene=sc); Mc = cam.matrix_world
def scr(u, v):   # u, v in 0..1 (0,0 bottom-left)
    tl, bl, br = Mc @ fr[3], Mc @ fr[2], Mc @ fr[1]   # view_frame order: top-right, bottom-right, bottom-left, top-left
    return (bl + (br - bl) * u + (tl - bl) * v - cam_p).normalized()
LB = None
for u, v in ((0.82, 0.78), (0.8, 0.7), (0.85, 0.85), (0.15, 0.78)):
    hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, cam_p, scr(u, v))
    if hit and ob.name.startswith("Shelf") or (hit and abs(nrm.y) > 0.8 and loc.y > 0.9):
        LB = loc; print("LOGOBOX hit", ob.name, loc, (u, v)); break
if LB is not None:
    base = None
    for dy in (-0.05, -0.02, 0.0, 0.03, 0.06):
        h2, l2, n2, *_r = sc.ray_cast(dg, Vector((LB.x, LB.y + dy, LB.z + 0.05)), Vector((0, 0, -1)))
        if h2 and n2.z > 0.8 and LB.z - l2.z < 0.45: base = (l2, dy); break
    if base:
        l2, dy = base; W_, D_, H_ = 0.22, 0.05, 0.27
        _bx = bmesh.new(); bmesh.ops.create_cube(_bx, size=1.0)
        for v in _bx.verts: v.co = Vector((v.co.x * W_, v.co.y * D_, v.co.z * H_ + H_ / 2))
        bmesh.ops.bevel(_bx, geom=list(_bx.edges) + list(_bx.verts), offset=0.003, segments=1, affect='EDGES')
        lme = bpy.data.meshes.new("LogoShelfBox"); _bx.to_mesh(lme); _bx.free(); lme.materials.append(bpy.data.materials["M_pack08"])
        lbox = bpy.data.objects.new("LogoShelfBox", lme); bpy.data.collections["REAL"].objects.link(lbox)
        to_cam = Vector((cam_p.x - l2.x, cam_p.y - l2.y, 0)).normalized(); yaw = math.atan2(to_cam.y, to_cam.x) + math.pi / 2
        lbox.location = (l2.x, l2.y - D_ * 0.9, l2.z + 0.002); lbox.rotation_euler = (0, 0, yaw)
        logo_decal("LogoShelf", "DaKrasFilms_logo_dark.png", lbox, (0, -D_ / 2 - 0.0015, H_ * 0.55), (0, 0, 0), 0.2)
        for o_ in (lbox, bpy.data.objects["LogoShelf"]): key_vis(o_, is_real)
        print("LOGOBOX at", lbox.location, math.degrees(yaw))
json.dump([{"beat": b, "frame": f, "first_words": w} for b, f, w in BEATS], open(os.path.join(HERE, "..", "beats.json"), "w"), indent=1)
json.dump(CAMLOG, open(os.path.join(HERE, "..", "camlog.json"), "w"))
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("DONE")
