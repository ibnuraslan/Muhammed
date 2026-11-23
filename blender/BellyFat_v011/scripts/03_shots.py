"""BellyFat v011: built straight to the VO frames (v010 timing, 1-1273), short shots with hard cuts on ONE camera.
blender -b scene.blend --python 03_shots.py -- <out.blend>
Director fix list (Nov 21) + RECURRING_FAULTS + batch-2 rules. Beat frames: 1, 73, 181, 451, 715, 829, 1147; end 1273."""
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
BEATS = [(1, 1, "A stray bullet struck her"), (2, 73, "right in the stomach"), (3, 181, "It pierced her skin"), (4, 451, "Layer by layer"),
         (5, 715, "And by the time it reached deeper tissue"), (6, 829, "the bullet had lost most of its force"), (7, 1147, "saving her life")]
# shots (first frame, last frame, name). Hard cuts between them; every shot 0.6-2.5 s.
SHOTS = [(1, 36, "A_shop"), (37, 72, "B_flight"), (73, 120, "C_impact"), (121, 180, "D_react"),
         (181, 300, "E1_pierce"), (301, 450, "E2_fat"), (451, 590, "F1_layers"), (591, 714, "F2_cushion"),
         (715, 828, "G_muscle"), (829, 960, "H1_slow"), (961, 1060, "H2_stop"), (1061, 1146, "H3_organs"),
         (1147, 1206, "O_wound"), (1207, 1273, "P_relief")]
REAL_RANGES = [(1, 180), (1147, 1273)]
def is_real(f): return any(a <= f <= b for a, b in REAL_RANGES)

# ================================================================== woman
W = bpy.data.objects["Woman"]
WR = make_human_ctrl(W); WH = Human(WR); add_hand_limits(W)
POS = Vector((0.0, 0.45, 0.0)); YAW = 90.0
def wpt(x, y, z): return Vector((POS.x + x, POS.y + y, z))
for s in "LR":
    xy = WH.foot_xy(s, POS, YAW)
    for f in (1, FEND): WH.key_foot(s, f, xy, YAW + (8 if s == "L" else -8))
rh = WH.root_head.z
IMPACT = 90                        # bullet touches the shirt (shot C)
# (frame, dx, dz, flex, twist, side, head pitch, head yaw)  - she reads the box, flinches at the hit, folds, then straightens relieved
BODY = [(1, 0.0, 0.0, 6, 10, 2, 16, 22), (36, 0.0, 0.0, 7, 12, 2, 18, 18), (72, 0.0, 0.0, 6, 10, 2, 15, 20), (IMPACT, 0.0, 0.0, 6, 10, 2, 15, 20),
        (IMPACT + 5, -0.035, -0.012, 18, 6, -1, 26, 8), (IMPACT + 14, -0.05, -0.03, 26, 2, -3, 30, 0), (130, -0.04, -0.03, 24, 0, -2, 28, 0),
        (180, -0.03, -0.035, 22, -2, 0, 30, -2), (1147, -0.03, -0.035, 22, -2, 0, 32, -2), (1185, -0.03, -0.035, 21, -2, 0, 34, -4),
        (1215, -0.02, -0.02, 14, 0, 1, 14, -10), (1240, -0.01, -0.01, 8, 0, 1, 2, -16), (1273, -0.01, -0.01, 7, 0, 1, 0, -18)]
for f, dx, dz, fl, tw, sd, hp, hy in BODY:
    WH.key_root(f, Vector((POS.x + dx, POS.y, rh + dz)), yaw=YAW, flex=fl * 0.25, side=sd)
    WH.key_spine(f, flex=fl, twist=tw, side=sd, head=(hp, hy))
# breathing on every visible frame range (never a frozen hold): small flex oscillation layered by extra keys
for a, b in ((1, 88), (131, 180), (1147, 1273)):
    for f in range(a, b + 1, 10):
        base = [k for k in BODY if k[0] <= f][-1]; nxt = [k for k in BODY if k[0] >= f][0]
        u = 0 if nxt[0] == base[0] else (f - base[0]) / (nxt[0] - base[0])
        lerp = lambda i: base[i] + (nxt[i] - base[i]) * u
        amp = 1.0 if f < 100 else (2.5 if f < 1200 else 1.5)
        b_ = math.sin(2 * math.pi * T(f) / (1.4 if f < 100 else 0.9)) * amp
        WH.key_spine(f, flex=lerp(3) + b_, twist=lerp(4), side=lerp(5), head=(lerp(6) + 0.5 * b_, lerp(7)))
# mouth: slightly parted at most (never a black hole), eyelid blinks
for f, a in ((1, 0), (IMPACT, 0), (IMPACT + 4, 5), (180, 4), (1147, 4), (1230, 2), (1273, 1)):
    WR.key_rot("jaw", f, [("X", a)])
def blink(rig, f):
    for s in "LR":
        bn = "orbicularis03." + s
        if bn not in rig.PB: continue
        for ff, ang in ((f - 3, 0), (f, 1), (f + 4, 0)):
            rig.key_rot(bn, ff, [("X", 22 * ang)])
for f in (20, 160, 1170, 1250): blink(WR, f)

# hands ---------------------------------------------------------------
def hand(s, f, p, d, n, pole): WH.key_hand(s, f, wpt(*p), Vector(d), Vector(n), wpt(*pole))
# left: holds the box palm-up in front of her chest (cup), lets go at the hit, then presses flat on the wound, lifts to look, rests
LH = [(1, (0.30, 0.17, 1.08), (0.35, 0.45, 0.2), (0, 0, 1), (-0.2, 0.9, 0.7)), (88, (0.30, 0.17, 1.08), (0.35, 0.45, 0.2), (0, 0, 1), (-0.2, 0.9, 0.7)),
      (IMPACT + 6, (0.31, 0.32, 1.06), (0.4, 0.3, -0.2), (0, 0, 1), (-0.15, 0.95, 0.95)),
      (IMPACT + 18, (0.42, 0.20, 1.02), (0.1, -0.9, 0.3), (-1, 0, 0), (0.05, 0.95, 1.05)),
      (125, (0.34, 0.12, 0.98), (0.1, -0.9, 0.3), (-1, 0, 0), (0.05, 0.95, 1.05))]
for k in LH: hand("L", *k)
# right: carries the basket by its handle (hanging), drops it on the hit, then rests open by her side
RHK = [(1, (0.10, -0.34, 0.86), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0)), (40, (0.12, -0.345, 0.865), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0)),
       (IMPACT, (0.11, -0.34, 0.86), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0)),
       (IMPACT + 12, (0.16, -0.37, 0.92), (0.3, -0.2, -0.9), (0, -1, 0), (-0.3, -0.85, 1.0)), (180, (0.12, -0.35, 0.86), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0)),
       (1210, (0.12, -0.35, 0.86), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0)), (1273, (0.13, -0.355, 0.87), (0.2, -0.1, -1), (0, -1, 0), (-0.3, -0.85, 1.0))]
for k in RHK: hand("R", *k)
for f, p in ((IMPACT + 6, "open_alarm"), (118, "flat_palm"), (1160, "flat_palm"), (1172, "relaxed"), (1222, "relaxed"), (1245, "flat_palm"), (1273, "flat_palm")):
    apply_pose(W, "L", p, f)
for f, p in ((1, "relaxed"), (IMPACT, "relaxed"), (IMPACT + 10, "open_alarm"), (150, "relaxed"), (1273, "relaxed")):
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
    bob = 0.003 * math.sin(2 * math.pi * T(f) / 1.4)
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
def pathA(f):
    if f <= 180: u = T(f) / 3.0; return Vector((-6.4 + 1.6 * u, -0.35, 0))
    u = min(1.0, (f - 1147) / 126.0); return Vector((-3.4 + 1.6 * u, -0.35, 0))
AH.walk(pathA, lambda f: 90.0, 1, 180, stride=0.62, lift=0.07)
AH.walk(pathA, lambda f: 90.0, 1147, FEND, stride=0.62, lift=0.07)
for f in range(1, FEND + 1, 3):
    if 181 <= f < 1147: continue
    p = pathA(f); cart.location = (p.x + 0.95, p.y, 0.0); cart.rotation_euler = (0, 0, math.pi); cart.keyframe_insert("location", frame=f)
    for s, dy in (("L", 0.2), ("R", -0.2)):
        AH.key_hand(s, f, Vector((p.x + 0.36, p.y + dy, 1.04)), Vector((1, 0, -0.3)), Vector((0, 0, 1)), Vector((p.x - 0.2, p.y + 3 * dy, 1.0)))
for s in "LR": apply_pose(A, s, "wrap_grip", 1); apply_pose(A, s, "wrap_grip", FEND)
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
for rig in (AR, SR, CR_, BR_):
    for f in (40, 1200): blink(rig, f + random.randint(0, 30))

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
th.scale = (S, 1e-4, 1e-4); th.keyframe_insert("scale", frame=1); th.keyframe_insert("scale", frame=IMPACT + 9)
th.scale = (S, S * 2.0, S * 2.0); th.keyframe_insert("scale", frame=IMPACT + 12); th.keyframe_insert("scale", frame=FEND)
# the hole decal mesh sits at x = -0.065 macro units; at real scale that is -1.6 mm (just outside the shirt): keep it

from mathutils.bvhtree import BVHTree as _BVH
_body = bpy.data.objects["Woman.body"]; _gi = {g.index: g.name for g in _body.vertex_groups if g.name in W.data.bones}
_HL = [v.index for v in _body.data.vertices
       if any(g.weight > 0.5 and _gi.get(g.group, "").startswith(("finger", "metacarpal")) and _gi[g.group].endswith(".L") for g in v.groups)]
_ARM = {v.index for v in _body.data.vertices
        if max(((g.weight, _gi.get(g.group, "")) for g in v.groups if g.group in _gi), default=(0, ""))[1].startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "shoulder", "clavicle"))}
for _m in _body.modifiers:
    if _m.type != 'ARMATURE': _m.show_viewport = False
def _hits(dg):
    e = _body.evaluated_get(dg); me = e.to_mesh(); mw = _body.matrix_world
    V = [mw @ v.co for v in me.vertices]; Pp = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
    tb = _BVH.FromPolygons(V, [p for p in Pp if not any(i in _ARM for i in p)])
    et = tee.evaluated_get(dg); mt = et.to_mesh(); tv = [tee.matrix_world @ v.co for v in mt.vertices]; tp = [tuple(p.vertices) for p in mt.polygons]; et.to_mesh_clear()
    tt = _BVH.FromPolygons(tv, tp); n = 0
    for i in _HL:
        q = V[i]
        for t in (tb, tt):
            loc, nr, _i, d = t.find_nearest(q, 0.05)
            if loc is not None and d > 0.003 and (q - loc).dot(nr) < 0: n += 1; break
    return n
def settle(f, nrm):
    pb = W.pose.bones["IK_hand.L"]; step = W.data.bones["IK_hand.L"].matrix_local.to_3x3().inverted() @ (W.matrix_world.inverted().to_3x3() @ (nrm * 0.004))
    for it in range(20):
        sc.frame_set(f); h = _hits(bpy.context.evaluated_depsgraph_get())
        if h <= 2: break
        pb.location = pb.location + step; pb.keyframe_insert("location", frame=f, group=pb.name)
    print("SETTLE", f, it, h)
def wound(f, lift=0.0, dz=0.0, dy=0.0):
    sc.frame_set(f); c = imp.matrix_world.translation.copy(); n = (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
    place_hand(W, "L", f, c + n * lift + Vector((0, 0.015 + dy, dz)), -n, Vector((0, -1, 0.35)).normalized(), skin=0.02)
    settle(f, n)
for f, lift, dz, dy in ((125, 0.0, 0.0, 0), (135, 0.0, 0.0, 0), (150, 0.0, 0.0, 0), (165, 0.0, 0.0, 0), (172, 0.0, 0.0, 0), (180, 0.0, 0.0, 0), (1147, 0.0, 0.0, 0), (1158, 0.0, 0.0, 0),
                        (1172, 0.07, -0.08, 0.06), (1205, 0.07, -0.09, 0.06), (1222, 0.06, -0.10, 0.07), (1245, 0.0, 0.03, 0), (1273, 0.0, 0.03, 0)):
    wound(f, lift, dz, dy)
for _m in _body.modifiers: _m.show_viewport = True
# ================================================================== bullet: through the shop window, down the aisle, into her shirt
bul = bpy.data.objects["Bullet"]; bul.rotation_mode = 'QUATERNION'
XWIN = 12.0
def bullet_store(f):
    """tip position (world) for the store shots"""
    if f <= 72: x = XWIN + 0.25 - (f - 37) * 0.20           # through the glass at f38, flying down the aisle (12 m/s, slowed for the eye)
    else:
        u = min(1.0, (f - 73) / (IMPACT - 73)); x = P.x + 0.16 * (1 - u)  # slow-motion close-up approach
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
bul.hide_render = False; bul.keyframe_insert("hide_render", frame=37)
bul.hide_render = True; bul.keyframe_insert("hide_render", frame=IMPACT + 8)
trail = bpy.data.objects["Trail"]; trail.scale = (3.0, 0.45, 0.45)
for f, a in ((1, 0.0), (37, 0.0), (39, 0.8), (72, 0.7), (73, 0.35), (IMPACT - 2, 0.1), (IMPACT, 0.0)):
    trail.color = (1, 1, 1, a); trail.keyframe_insert("color", frame=f)
# shop window: entry hole + crack star appear as the bullet punches through (keyed scale, no Scene Time)
cm = bpy.data.materials.new("M_crack"); cm.use_nodes = True; nt = cm.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 9.0
L.new(tc.outputs["Object"], vo.inputs["Vector"])
gr = N.new("ShaderNodeMath"); gr.operation = 'LESS_THAN'; gr.inputs[1].default_value = 0.035; L.new(vo.outputs["Distance"], gr.inputs[0])
rad = N.new("ShaderNodeVectorMath"); rad.operation = 'LENGTH'; L.new(tc.outputs["Object"], rad.inputs[0])
fall = N.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = 0.5
fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0; L.new(rad.outputs["Value"], fall.inputs["Value"])
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(gr.outputs[0], mul.inputs[0]); L.new(fall.outputs["Result"], mul.inputs[1])
core = N.new("ShaderNodeMath"); core.operation = 'LESS_THAN'; core.inputs[1].default_value = 0.035; L.new(rad.outputs["Value"], core.inputs[0])
mx_ = N.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; L.new(mul.outputs[0], mx_.inputs[0]); L.new(core.outputs[0], mx_.inputs[1])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1); em.inputs["Strength"].default_value = 1.5
tr = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader"); L.new(mx_.outputs[0], ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
L.new(ms.outputs[0], mo.inputs["Surface"])
_c = bmesh.new(); bmesh.ops.create_circle(_c, cap_ends=True, segments=48, radius=0.5)
cme2 = bpy.data.meshes.new("Crack"); _c.to_mesh(cme2); _c.free(); cme2.materials.append(cm)
crack = bpy.data.objects.new("WindowCrack", cme2); bpy.data.collections["REAL"].objects.link(crack)
crack.location = (XWIN - 0.012, P.y, P.z); crack.rotation_euler = (0, math.radians(90), 0)
for f, s_ in ((1, 0.001), (37, 0.001), (39, 0.6), (44, 1.0), (FEND, 1.0)):
    crack.scale = (s_, s_, s_); crack.keyframe_insert("scale", frame=f)
# glass sparkle: a few tiny shards that fly off the hole, keyed
shm = bpy.data.materials.new("M_shard"); shm.use_nodes = True; shm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
shm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.05
for i in range(14):
    _s = bmesh.new(); bmesh.ops.create_icosphere(_s, subdivisions=0, radius=0.006); sme = bpy.data.meshes.new("Shard"); _s.to_mesh(sme); _s.free(); sme.materials.append(shm)
    o = bpy.data.objects.new("Shard%02d" % i, sme); bpy.data.collections["REAL"].objects.link(o)
    v = Vector((-random.uniform(0.4, 1.2), random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.7)))
    for f in (1, 37, 38, 72):
        k = max(0, f - 38) / 60.0
        o.location = Vector((XWIN - 0.02, P.y, P.z)) + v * k + Vector((0, 0, -4.9 * k * k)); o.scale = (1, 1, 1) if f >= 38 else (0, 0, 0)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)

# ================================================================== macro cross-section: its own static set (hard cuts, no in-body scale trick)
root = bpy.data.objects["MacroRoot"]; root.parent = None
MR = Matrix.Translation((0.0, 60.0, 5.0)) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((S, S, S, 1))
root.matrix_world = MR; bpy.context.view_layer.update()
# macro bullet: its own copy on the macro root
bm2 = bul.copy(); bm2.data = bul.data; bm2.animation_data_clear(); bm2.name = "BulletMacro"
bpy.data.collections["MACRO"].objects.link(bm2); bm2.parent = root; bm2.matrix_parent_inverse = Matrix.Identity(4)
bm2.rotation_mode = 'XYZ'; bm2.scale = (1, 1, 1)
# tip depth (macro units) per VO frame: shirt 181-200, skin dimple then pierce ~230, steady through fat, muscle at 715, stop at ~960
DK = [(181, -0.45), (200, 0.0), (215, 0.12), (232, 0.28), (260, 0.62), (330, 1.15), (450, 2.0), (590, 2.75), (714, 3.55), (790, 4.25),
      (828, 4.62), (900, 5.05), (960, 5.3), (1000, 5.36), (1273, 5.36)]
Dfn = pchip(DK)
def D(f): return Dfn(f)
for f in range(170, 1160):
    bm2.location = (D(f) - 0.6, 0, 0); bm2.rotation_euler = (0.04 * f if D(f + 1) - D(f) > 1e-4 else 0.04 * 960, 0, 0)
    bm2.keyframe_insert("location", frame=f); bm2.keyframe_insert("rotation_euler", frame=f)
# a soft glow halo on the macro bullet so it reads in every framing (and a warm rim light that follows it)
glow = bpy.data.materials.new("M_bullet_glow"); glow.use_nodes = True; gnt = glow.node_tree; GN_ = gnt.nodes; GL_ = gnt.links
GN_.remove(GN_["Principled BSDF"]); gmo = GN_["Material Output"]
lw = GN_.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.4
em2 = GN_.new("ShaderNodeEmission"); em2.inputs["Color"].default_value = (1.0, 0.85, 0.45, 1); em2.inputs["Strength"].default_value = 2.5
tr2 = GN_.new("ShaderNodeBsdfTransparent"); ms2 = GN_.new("ShaderNodeMixShader")
inv = GN_.new("ShaderNodeMath"); inv.operation = 'MULTIPLY'; inv.inputs[1].default_value = 0.6; GL_.new(lw.outputs["Facing"], inv.inputs[0])
GL_.new(inv.outputs[0], ms2.inputs[0]); GL_.new(tr2.outputs[0], ms2.inputs[1]); GL_.new(em2.outputs[0], ms2.inputs[2]); GL_.new(ms2.outputs[0], gmo.inputs["Surface"])
halo = bm2.copy(); halo.data = bm2.data.copy(); halo.data.materials.clear(); halo.data.materials.append(glow); halo.name = "BulletHalo"
bpy.data.collections["MACRO"].objects.link(halo); halo.parent = bm2; halo.matrix_parent_inverse = Matrix.Identity(4); halo.animation_data_clear()
halo.location = (-0.03, 0, 0); halo.rotation_euler = (0, 0, 0); halo.scale = (1.1, 1.18, 1.18)
for m_ in halo.modifiers: pass
# tissue response
def dimple_val(f):
    if f < 200: return 0.0
    if f < 232: return D(f)
    u = (f - 232) / 60.0; return 0.28 * math.exp(-u * 3.0) * math.cos(u * 14.0)
for nm, gain in (("M_Fabric", 1.0), ("M_Epidermis", 1.0), ("M_Dermis", 0.85)):
    o = bpy.data.objects[nm]; o.shape_key_add(name="Basis"); k = o.shape_key_add(name="dimple")
    for i, v in enumerate(o.data.vertices):
        r2 = v.co.y ** 2 + v.co.z ** 2; k.data[i].co = v.co + Vector((gain * math.exp(-r2 / 0.6), 0, 0))
    k.slider_min = -1
    for f in range(181, 330, 2):
        dv = dimple_val(f) + (0.07 if nm == "M_Fabric" and 200 <= f < 232 else 0.0)
        k.value = max(-0.5, min(1.0, dv)); k.keyframe_insert("value", frame=f)
    h = o.shape_key_add(name="hole", from_mix=False)
    for i, v in enumerate(o.data.vertices):
        rr = math.hypot(v.co.y, v.co.z)
        if rr < 0.5:
            dd = Vector((0, v.co.y, v.co.z)).normalized() if rr > 1e-4 else Vector((0, 0, 1))
            h.data[i].co = v.co + dd * (0.23 + (rr / 0.5) * 0.27 - rr) + Vector((0.06 * (1 - rr / 0.5), 0, 0))
    for f, hv in ((228, 0.0), (234, 1.0), (FEND, 1.0)): h.value = hv; h.keyframe_insert("value", frame=f)
hd = bpy.data.objects["M_HoleDecal"]
for f, s_ in ((1, 0.0), (228, 0.0), (236, 0.8), (FEND, 0.8)): hd.scale = (1, s_, s_); hd.keyframe_insert("scale", frame=f)
def vel(f): return (D(f + 2) - D(f - 2)) / 4 * FPS
tipctl = bpy.data.objects["TipCtl"]
for f in range(176, 1152, 2):
    e = min(1.0, max(0.0, vel(f) / 1.0)) if f > 232 else 0.0
    wob = (math.exp(-(f - 980) / 90.0) if f > 980 else 0.0) + (0.35 * math.exp(-(f - 232) / 50.0) if f > 232 else 0.0)
    tipctl.location = (D(f), e, wob); tipctl.keyframe_insert("location", frame=f)
# ONE clean shock-wave ring that stays on the bullet (pulses with the energy it is losing), the others are removed
RINGS = sorted([o for o in bpy.data.objects if o.name.startswith("M_Ring")], key=lambda o: o.name)
for o in RINGS[1:]: bpy.data.objects.remove(o, do_unlink=True)
# fat 'ahead of the tip' push switches on as the tip enters the fat (VO timing: f229 = 3.8 s)
for nd in bpy.data.node_groups["FatLobulesGN"].nodes if "FatLobulesGN" in bpy.data.node_groups else []:
    if nd.bl_idname == "ShaderNodeMath" and nd.operation == 'GREATER_THAN' and abs(nd.inputs[1].default_value - 3.15) < 1e-6: nd.inputs[1].default_value = 3.8
ring = RINGS[0]
for f in range(176, 1152, 3):
    e = min(1.0, max(0.0, vel(f) / 1.0)) if f > 232 else 0.0
    ring.location = (D(f) - 0.32, 0, 0); r_ = 0.34 + 0.12 * e * (0.5 + 0.5 * math.sin(f * 0.35))
    ring.scale = (1, r_, r_); ring.color = (1, 1, 1, 0.45 * e)
    for p_ in ("location", "scale", "color"): ring.keyframe_insert(p_, frame=f)
# muscle fibres part exactly where the bullet tip is
for o in [o for o in bpy.data.objects if o.name.startswith("M_MuscleFib")]:
    ph = random.uniform(0, 6.28); x = o.location.x; yrow = o.location.y
    o.shape_key_add(name="Basis"); k = o.shape_key_add(name="part")
    for i, v in enumerate(o.data.vertices):
        k.data[i].co = v.co + Vector((0, -0.34 * math.exp(-(v.co.z / 0.3) ** 2) * (1.0 if yrow > -0.3 else 0.5), 0))
    for f in range(700, 1152, 3):
        d = D(f); k.value = max(0.0, min(1.0, (d - (x - 0.2)) / 0.18)); k.keyframe_insert("value", frame=f)
        near = math.exp(-((d - x) / 0.4) ** 2); s_ = 1 + 0.05 * near * math.sin(f * 0.15 + ph) + 0.01 * math.sin(f * 0.037 + ph)
        o.scale = (s_, s_, 1); o.keyframe_insert("scale", frame=f)
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
    for f in range(176, 1152, 6):
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
for o in REALO: key_vis(o, is_real)
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
def shot_cam(f):
    for f0, f1, name in SHOTS:
        if f0 <= f <= f1: break
    u = sm((f - f0) / max(1, f1 - f0))
    if name == "A_shop":     # medium on her, face and the box (logo) readable; slow push
        tg = face_pt(f).lerp(wpt(0.3, 0.17, 1.15), 0.45); cp = lin(Vector((1.55, -0.35, 1.42)), Vector((1.3, -0.22, 1.38)), u); return cp, tg, Vector((0, 0, 1)), 35, 8.0
    if name == "B_flight":   # rides beside the bullet from the cracked window down the aisle; bullet sharp and big
        tip = bullet_store(f); cp = tip + Vector((0.07, -0.10, 0.025)); return cp, tip + Vector((-0.02, 0, 0)), Vector((0, 0, 1)), 40, 22.0
    if name == "C_impact":   # side close of her belly: the bullet arrives and hits the shirt, impact point in frame and sharp
        tg = P + Vector((0.03, 0, 0.015)); cp = lin(P + Vector((0.20, -0.17, -0.02)), P + Vector((0.175, -0.145, -0.015)), u); return cp, tg, Vector((0, 0, 1)), 30, 11.0
    if name == "D_react":    # front three-quarter medium: she folds, drops the basket and box, hand to her stomach, face readable
        tg = face_pt(f).lerp(wpt(0.2, 0.0, 1.0), 0.45); cp = lin(Vector((1.7, -0.55, 1.35)), Vector((1.55, -0.45, 1.3)), u); return cp, tg, Vector((0, 0, 1)), 32, 8.0
    if name == "O_wound":    # front 3/4: she lifts her hand and looks down at the small hole in her shirt (wound and her face in frame)
        tg = face_pt(f).lerp(P, 0.5); cp = lin(Vector((1.25, -0.3, 1.25)), Vector((1.12, -0.25, 1.22)), u); return cp, tg, Vector((0, 0, 1)), 35, 8.0
    if name == "P_relief":   # she straightens, breathes out and looks up: she is fine (shopper A comes to help behind her)
        tg = face_pt(f) + Vector((0, 0, -0.08)); cp = lin(Vector((1.25, -0.2, 1.45)), Vector((1.08, -0.12, 1.47)), u); return cp, tg, Vector((0, 0, 1)), 40, 8.0
    MAC = {"E1_pierce": ((0.15, 0, 0), (98, 92), (8, 6), (4.0, 3.4), 45), "E2_fat": ((0.3, 0, 0), (62, 72), (14, 10), (3.3, 3.0), 45),
           "F1_layers": ((0.3, 0, 0), (105, 98), (-8, -4), (3.2, 3.0), 45), "F2_cushion": ((0.2, 0, 0), (132, 122), (12, 10), (3.4, 3.2), 45),
           "G_muscle": ((0.3, 0, 0), (84, 90), (6, 4), (2.9, 2.7), 45), "H1_slow": ((0.3, 0, 0), (62, 74), (10, 8), (3.3, 3.1), 45),
           "H2_stop": ((0.2, 0, 0), (100, 96), (18, 14), (4.4, 4.1), 42), "H3_organs": ((0.4, 0, 0), (80, 86), (-12, -8), (3.8, 3.3), 45)}
    off, az, el, ds, lens = MAC[name]
    cp, tg, up, dw = macro_cam(f, off, lin(*az, u), lin(*el, u), lin(*ds, u))
    return cp, tg, up, lens, 11.0
prevq = None; CAMLOG = []
for f in range(1, FEND + 1):
    cp, tg, up, lens, fstop = shot_cam(f)
    q = look(cp, tg, up)
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    cam.location = cp; cam.rotation_quaternion = q; cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = lens; cd.keyframe_insert("lens", frame=f)
    dist = (tg - cp).length
    cd.clip_start = max(0.0005, min(0.05, dist * 0.05)); cd.keyframe_insert("clip_start", frame=f)
    cd.dof.use_dof = True; cd.dof.focus_distance = dist; cd.dof.aperture_fstop = fstop
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
