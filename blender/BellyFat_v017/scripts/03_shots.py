"""BellyFat v014: built straight to the VO frames (v010 timing, 1-1273), short shots with hard cuts on ONE camera.
blender -b scene.blend --python 03_shots.py -- <out.blend>
Director fix lists (Nov 21 18 items, v011 13 items, v012 12 items, v013 10 items) + RECURRING_FAULTS + batch-2 rules. Beat frames: 1, 73, 181, 451, 715, 829, 1147; end 1273."""
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
# shots (first frame, last frame, name). Hard cuts between store shots; the cross-section is ONE continuous push.
SHOTS = [(1, 30, "W_window"), (31, 58, "F_face"), (59, 140, "H_hit"), (141, 180, "L_look"), (181, 330, "M_cut"),
         (331, 520, "R1_medium"), (521, 760, "R2_close"), (761, 960, "R3_help"), (961, 1100, "R4_hole"), (1101, 1185, "P_wince"), (1186, 1216, "P_bullet"), (1217, 1273, "P_face")]
REAL_RANGES = [(1, 180), (331, 1273)]
def is_real(f): return any(a <= f <= b for a, b in REAL_RANGES)
def kq(obj, bone, f, axis, deg):
    """key a bone's LOCAL rotation (eye X = look down, orbicularis03 X<0 = close upper lid, orbicularis04 X>0 = raise lower lid,
    oris07 Z (L +, R -) = mouth corners down, (L -, R +) = corners up, jaw X = open)"""
    pb = obj.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(Vector(axis), math.radians(deg))
    pb.keyframe_insert("rotation_quaternion", frame=f, group=bone)

# ================================================================== woman
W = bpy.data.objects["Woman"]
WR = make_human_ctrl(W); WH = Human(WR); add_hand_limits(W)
POS = Vector((0.0, 0.45, 0.0)); YAW = 90.0
def wpt(x, y, z): return Vector((POS.x + x, POS.y + y, z))
IMPACT = 72                        # the bullet hits her shirt ("right in the stomach" at 73)
for s in "LR":
    xy = WH.foot_xy(s, POS, YAW); fy = YAW + (8 if s == "L" else -8)
    if s == "R":
        for f in (1, FEND): WH.key_foot(s, f, xy, fy)
    else:                          # the hit makes her stagger: her left foot steps back
        back = Vector((xy.x - 0.12, xy.y + 0.02))
        WH.key_foot(s, 1, xy, fy); WH.key_foot(s, IMPACT + 4, xy, fy)
        WH.key_foot(s, IMPACT + 9, xy.lerp(back, 0.55), fy - 4, lift=0.05); WH.key_foot(s, IMPACT + 14, back, fy - 6); WH.key_foot(s, FEND, back, fy - 6)
rh = WH.root_head.z
# (frame, dx, dz, flex, twist, side, head pitch, head yaw)
BODY = [(1, 0.0, 0.0, 6, 10, 2, 14, 22), (8, 0.004, 0.0, 6, 11, 1, 15, 21),
        (12, -0.014, 0.008, 1, 6, 0, -2, 6), (20, -0.016, 0.008, 0, 4, 0, -4, 4), (60, -0.008, 0.004, 3, 6, 0, 0, 6),      # startled by the glass breaking
        (IMPACT, -0.008, 0.004, 3, 6, 0, 0, 6), (IMPACT + 2, -0.04, -0.004, 10, 5, -1, 8, 4), (IMPACT + 5, -0.065, -0.012, 18, 3, -3, 20, 2),   # the jolt
        (IMPACT + 14, -0.08, -0.03, 24, 0, -3, 30, 0), (110, -0.07, -0.035, 22, -2, -1, 32, -2), (180, -0.06, -0.035, 22, -2, 0, 32, -2),
        (331, -0.06, -0.035, 22, -2, 0, 24, -2), (520, -0.06, -0.035, 21, -2, 0, 22, 0), (760, -0.06, -0.03, 20, -2, 0, 20, -6),
        (830, -0.06, -0.03, 19, -2, 0, 14, -24), (900, -0.06, -0.03, 20, -2, 0, 22, -10), (990, -0.06, -0.035, 21, -2, 0, 30, -4), (1146, -0.05, -0.03, 18, -2, 0, 28, -6),
        (1147, -0.05, -0.03, 18, -2, 0, 28, -6), (1165, -0.05, -0.03, 17, -2, 0, 30, -4), (1185, -0.04, -0.025, 12, 0, 1, 26, -8), (1205, -0.03, -0.02, 9, 0, 1, 24, -8),
        (1225, -0.02, -0.01, 5, 0, 1, 0, -18), (1238, -0.018, -0.022, 2, 0, 1, -9, -20), (1256, -0.015, -0.012, 4, 0, 1, -3, -22), (1273, -0.015, -0.01, 4, 0, 1, -2, -22)]   # long exhale: shoulders drop, head back, then settles
for f, dx, dz, fl, tw, sd, hp, hy in BODY:
    WH.key_root(f, Vector((POS.x + dx, POS.y, rh + dz)), yaw=YAW, flex=fl * 0.25, side=sd)
    WH.key_spine(f, flex=fl, twist=tw, side=sd, head=(hp, hy))
def nod(f): return sum(a * math.exp(-((f - c) / 4.0) ** 2) for c, a in ((1232, 7), (1242, 5)))
for a, b in ((1, 180), (331, 1273)):
    for f in range(a, b + 1, 6):
        if IMPACT - 2 <= f <= IMPACT + 8: continue          # leave the jolt keys clean
        base = [k for k in BODY if k[0] <= f][-1]; nxt = [k for k in BODY if k[0] >= f][0]
        u = 0 if nxt[0] == base[0] else (f - base[0]) / (nxt[0] - base[0])
        lerp = lambda i: base[i] + (nxt[i] - base[i]) * u
        amp = 1.0 if f < IMPACT else (2.4 if f < 1185 else (1.4 if f < 1250 else 0.5))
        b_ = math.sin(2 * math.pi * T(f) / (1.4 if f < IMPACT else (0.85 if f < 1185 else 1.8))) * amp
        WH.key_spine(f, flex=lerp(3) + b_, twist=lerp(4), side=lerp(5), head=(lerp(6) + 0.5 * b_ + nod(f), lerp(7)))
# ---- face: reading -> startled -> pain -> looks at the bullet -> clear relief
GAZE = [(1, 14), (8, 14), (12, -8), (40, -4), (IMPACT, 0), (IMPACT + 6, 14), (110, 18), (180, 18), (331, 14), (760, 12), (830, 2),
        (900, 12), (990, 20), (1146, 18), (1165, 20), (1185, 14), (1205, 12), (1225, -2), (1273, -2)]
for f, g in GAZE:
    for s_ in "LR": kq(W, "eye." + s_, f, (1, 0, 0), g)
# (frame, upper lid, lower lid, mouth corners (+ down / - up), jaw)
FACE = [(1, -6, 0, 0, 0), (8, -6, 0, 0, 0), (12, 7, 0, 2, 5), (30, 4, 0, 4, 3), (IMPACT, 2, 0, 4, 2),
        (IMPACT + 4, -12, 14, 26, 5), (110, -10, 12, 24, 3), (180, -10, 12, 22, 3), (331, -11, 13, 24, 3), (520, -9, 11, 20, 2.5),
        (760, -10, 12, 22, 3), (830, -6, 6, 12, 2.5), (990, -8, 8, 12, 2), (1146, -8, 8, 10, 2), (1160, -14, 14, 26, 3), (1172, -12, 12, 20, 2.5), (1180, -6, 6, 6, 2.5),   # wince as she pulls it out
        (1195, 0, 2, 0, 3), (1212, -3, 4, -22, 2), (1230, -2, 5, -44, 1), (1236, -2, 5, -46, 0.5), (1239, -27, 2, -50, 0.2), (1248, -27, 2, -54, 0.2), (1256, -2, 5, -62, 0), (1273, -2, 6, -62, 0)]   # relief: eyes close on the breath out, then a smile
for f, ul, ll, mc, jw in FACE:
    for s_, sg in (("L", 1), ("R", -1)):
        kq(W, "orbicularis03." + s_, f, (1, 0, 0), ul); kq(W, "orbicularis04." + s_, f, (1, 0, 0), ll); kq(W, "oris07." + s_, f, (0, 0, 1), mc * sg)
    kq(W, "jaw", f, (1, 0, 0), jw)
def ulid(f):
    k = [x for x in FACE if x[0] <= f][-1]; n_ = [x for x in FACE if x[0] >= f][0]
    u = 0 if n_[0] == k[0] else (f - k[0]) / (n_[0] - k[0]); return k[1] + (n_[1] - k[1]) * u
def blink(obj, f, base=None):
    base = ulid(f) if (base is None and obj is W) else (base or 0)
    for s_ in "LR":
        b_ = "orbicularis03." + s_
        if b_ not in obj.pose.bones: continue
        for ff, ang in ((f - 3, base), (f, -27), (f + 1, -27), (f + 4, base)): kq(obj, b_, ff, (1, 0, 0), ang)
for f in (4, 50, 128, 160, 380, 455, 540, 610, 690, 750, 815, 880, 945, 1010, 1080, 1140, 1180, 1218): blink(W, f)

# hands ---------------------------------------------------------------
def hand(s, f, p, d, n, pole): WH.key_hand(s, f, wpt(*p), Vector(d), Vector(n), wpt(*pole))
# the box (our logo on its front) held in her left hand: palm under it, fingers wrapping up its far side (grip_object)
_bx = bmesh.new(); bmesh.ops.create_cube(_bx, size=1.0)
for v in _bx.verts: v.co = Vector((v.co.x * 0.11, v.co.y * 0.05, v.co.z * 0.17))
bmesh.ops.bevel(_bx, geom=list(_bx.edges) + list(_bx.verts), offset=0.003, segments=1, affect='EDGES')
pme = bpy.data.meshes.new("PickBox"); _bx.to_mesh(pme); _bx.free()
pme.uv_layers.new(name="UVMap"); pme.materials.append(bpy.data.materials["M_pack08"])
pbox = bpy.data.objects.new("PickBox", pme); bpy.data.collections["REAL"].objects.link(pbox)
# her left hand palm-up in front of her (cup preset), the box stands ON the posed palm, logo toward the hit-shot camera
place_hand(W, "L", 1, wpt(0.30, 0.20, 1.04), Vector((0, 0, 1)), Vector((0.35, -0.9, 0.15)).normalized(), skin=0.0)
apply_pose(W, "L", "cup_hold", 1, amount=0.35, spread=0)
sc.frame_set(1); _pb = W.pose.bones; _Mw = W.matrix_world
_wr = _Mw @ _pb["wrist.L"].head; _k3 = _Mw @ _pb["finger3-1.L"].head; _k2 = _Mw @ _pb["finger2-1.L"].head; _k5 = _Mw @ _pb["finger5-1.L"].head
_dd = (_k3 - _wr).normalized(); _aa = (_k2 - _k5).normalized(); _nn = _dd.cross(_aa)
if _nn.z < 0: _nn = -_nn
_nn = (_nn - _dd * _nn.dot(_dd)).normalized(); _cc = _wr.lerp(_k3, 0.75)
_cd = Vector((1.25, -0.45, 1.25)) - _cc; _yb = -(_cd - _nn * _cd.dot(_nn)).normalized(); _xb = _yb.cross(_nn).normalized(); _yb = _nn.cross(_xb)
_BM = Matrix((_xb, _yb, _nn)).transposed().to_4x4(); _BM.translation = _cc + _nn * (0.012 + 0.085) + _xb * 0.035 + _nn * 0.012   # clear of the wrist/forearm
BC = _BM.translation.copy(); BYAW = math.atan2(_xb.y, _xb.x)
pbox.matrix_world = _BM
for f in (1, 20): pbox.keyframe_insert("location", frame=f); pbox.keyframe_insert("rotation_euler", frame=f)
print("BOXONPALM", _cc, _nn)
_ikL = W.pose.bones["IK_hand.L"]; _l0, _q0 = _ikL.location.copy(), _ikL.rotation_quaternion.copy()
_toIK = W.data.bones["IK_hand.L"].matrix_local.to_3x3().inverted() @ W.matrix_world.inverted().to_3x3()
def chestM(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["spine05"].matrix
_ikL.keyframe_insert("location", frame=20, group=_ikL.name); _ikL.keyframe_insert("rotation_quaternion", frame=20, group=_ikL.name)
sc.frame_set(20); _ikW20 = W.matrix_world @ _ikL.matrix; _c20 = chestM(20).inverted()
_EXTRA = {11: (0, 0, 0.025), 21: (0, 0, 0.015), 31: (0, 0, 0.008)}
for f in list(range(21, 120, 2)) + [119]:          # the box hand rides with her chest: the arm keeps its shape (no forearm through the box)
    ex = Vector(_EXTRA.get(f, (0, 0, 0))) + Vector((0.02, 0.05, -0.015)) * max(0.0, min(1.0, (f - IMPACT) / 12.0))   # as she folds, the box hand moves out and down, clear of her chest
    Mt = Matrix.Translation(ex) @ chestM(f) @ _c20 @ _ikW20
    _ikL.matrix = W.matrix_world.inverted() @ Mt
    _ikL.keyframe_insert("location", frame=f, group=_ikL.name); _ikL.keyframe_insert("rotation_quaternion", frame=f, group=_ikL.name)
# the box stays in her grip through the startle and the hit (baked from her wrist every frame), then lies on the floor after the cutaway
def wristL(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["wrist.L"].matrix
OFFL = wristL(20).inverted() @ pbox.matrix_world.copy()
REL = IMPACT + 2     # the jolt shakes it out of her hand
for f in range(21, REL + 1):
    M_ = wristL(f) @ OFFL; pbox.matrix_world = M_
    pbox.keyframe_insert("location", frame=f); pbox.keyframe_insert("rotation_euler", frame=f)
# she lets go (her hand opens) and the box drops to the floor, tumbling; it lies there for the rest of the film
_l120 = pbox.location.copy(); _r120 = pbox.rotation_euler.copy(); _floor = wpt(0.40, 0.34, 0.026)
for f, u, rx, z in ((REL + 5, 0.06, 0.15, None), (REL + 10, 0.2, 0.45, None), (REL + 16, 0.5, 0.9, None), (REL + 21, 0.8, 1.3, None), (REL + 25, 1.0, 1.5708, 0.026), (REL + 28, 1.0, 1.5708, 0.045), (REL + 31, 1.0, 1.5708, 0.026), (FEND, 1.0, 1.5708, 0.026)):
    p_ = _l120.lerp(_floor, u); p_.z = z if z is not None else _l120.z + (_floor.z - _l120.z) * u * u
    pbox.location = p_; pbox.rotation_euler = (_r120.x + (math.radians(90) - _r120.x) * min(1, rx / 1.5708), _r120.y * (1 - min(1, u)), _r120.z + 0.6 * u)
    pbox.keyframe_insert("location", frame=f); pbox.keyframe_insert("rotation_euler", frame=f)
# right arm: relaxed with a bent elbow, startles, then her hand goes to the wound
for f, p in ((1, (0.22, -0.25, 1.0)), (8, (0.22, -0.25, 1.0)), (12, (0.26, -0.27, 1.06)), (60, (0.24, -0.26, 1.02)), (IMPACT, (0.24, -0.26, 1.02))):
    hand("R", f, p, (0.6, 0.15, -0.75), (0, 1, 0), (-0.3, -0.7, 1.0))
hand("R", IMPACT + 6, (0.22, -0.42, 1.02), (0.45, -0.3, -0.5), (0, 1, 0), (-0.3, -0.8, 1.0)); hand("R", 98, (0.25, -0.38, 1.0), (0.5, -0.2, -0.6), (0, 1, 0), (-0.3, -0.8, 1.0))   # R10: arm flung out to her side, away from her body
for f, p, a in ((1, "relaxed", 0.8), (IMPACT, "relaxed", 0.8), (IMPACT + 6, "open_alarm", 0.7)): apply_pose(W, "R", p, f, amount=a, spread=0)

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
    bk.location = (POS.x - 1.7, POS.y + 0.33, 0.101); bk.rotation_euler = (0, 0, 0.15); bk.keyframe_insert("location", frame=f); bk.keyframe_insert("rotation_euler", frame=f)
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

# ================================================================== background people (A strolls, hears it, comes to help; B and C idle and react)
A = bpy.data.objects["ShopperA"]; AR = make_human_ctrl(A); AH = Human(AR); A.location.z = 0.015; add_hand_limits(A)
cart = bpy.data.objects["Cart"]
APOS = Vector((-0.95, -0.45, 0)); AYAW_END = 90.0    # stops just behind her right shoulder, still facing up the aisle (no pivot)
def pathA(f):
    if f <= 600: return Vector((-8.0 + 3.8 * (f - 1) / 599, -0.55, 0))
    u = sm_((min(f, 900) - 600) / 300.0); return Vector((-4.2, -0.55, 0)).lerp(APOS, u)
def sm_(u): return u * u * (3 - 2 * u)
AH.walk(pathA, lambda f: 90.0, 1, 900, stride=0.55, lift=0.06)
for f, fl, hp, tw, hy in ((912, 8, 14, 18, 22), (1000, 12, 20, 24, 26), (1146, 9, 16, 22, 24), (1210, 6, 8, 20, 20), (FEND, 6, 8, 20, 20)):
    AH.key_root(f, Vector((APOS.x, APOS.y, AH.root_head.z - 0.015)), yaw=AYAW_END, flex=fl * 0.3); AH.key_spine(f, flex=fl, twist=tw, head=(hp, hy))
cart.location = (-9.0, -3.6, 0.0); cart.keyframe_insert("location", frame=1)          # parked out of the way
for f in range(1, 901, 6):
    p = pathA(f); ph = math.sin(2 * math.pi * f / (96.0 if f < 600 else 60.0))
    for s, dy, sg in (("L", 0.26, 1), ("R", -0.26, -1)):       # arms swing with bent elbows
        AH.key_hand(s, f, Vector((p.x + 0.14 * ph * sg + 0.10, p.y + dy, 0.97)), Vector((0.6, 0.1 * sg, -0.75)), Vector((0, -sg, 0)), Vector((p.x - 0.4, p.y + 2.2 * dy, 1.05)))
_fw = Vector((math.sin(math.radians(AYAW_END)), -math.cos(math.radians(AYAW_END)), 0)); _sd = Vector((_fw.y, -_fw.x, 0))    # facing / his right
for f in (912, 1000, 1146, FEND):
    for s, sg in (("L", -1), ("R", 1)):
        c_ = APOS + _sd * (0.22 * sg) + _fw * (0.16 if s == "L" else 0.12); zz = 1.0 if s == "L" else 0.97
        if s == "L" and f in (1000, 1146): c_ = APOS + _sd * (-0.05) + _fw * 0.30; zz = 1.12      # his left hand reaches toward her (concern), elbow bent
        AH.key_hand(s, f, Vector((c_.x, c_.y, zz)), Vector((_fw.x * 0.6, _fw.y * 0.6, -0.7)), -_sd * sg, APOS + _sd * (0.6 * sg) - _fw * 0.3 + Vector((0, 0, 1.05)))
for s in "LR": apply_pose(A, s, "relaxed", 1); apply_pose(A, s, "relaxed", FEND)
STK = bpy.data.objects["Stocker"]
SCo = bpy.data.objects["ShopperC"]; CR_ = make_human_ctrl(SCo); CH = Human(CR_); add_hand_limits(SCo)
cpos = Vector((-3.0, 0.72, 0))
for s_ in "LR":
    for f in (1, FEND): CH.key_foot(s_, f, CH.foot_xy(s_, cpos, 0.0), 0.0)
random.seed(5)
for f in list(range(1, FEND + 1, 45)) + [FEND]:
    tw = 4 + 6 * math.sin(f * 0.013); hy = -10 + 25 * math.sin(f * 0.009 + 1); hp = 10 + 6 * math.sin(f * 0.017)
    if 24 <= f <= 80: hy, tw = 60, 18                     # turns to the noise
    if f > 80: hy = 50 + 8 * math.sin(f * 0.02); tw = 22  # then watches her
    CH.key_root(f, Vector((cpos.x, cpos.y, CH.root_head.z - 0.01 + 0.004 * math.sin(f * 0.05))), yaw=0.0); CH.key_spine(f, flex=4 + 1.5 * math.sin(f * 0.07), twist=tw, head=(hp, hy))
for s, sx in (("L", -1), ("R", 1)):        # elbows bent; at the noise her right hand goes up to her mouth, then to her chest
    for f in (1, 20, 400, 800, FEND):
        CH.key_hand(s, f, Vector((cpos.x + 0.21 * -sx, cpos.y - 0.12, 0.96 + 0.01 * math.sin(f))), Vector((0.1, -0.6, -0.75)), Vector((sx, 0, 0)), Vector((cpos.x - 0.5 * sx, cpos.y + 0.4, 1.1)))
    apply_pose(SCo, s, "relaxed", 1)
pass   # R6/R10: no hand-to-mouth or hand-to-body; she reacts with head turns, hands down
Bp = bpy.data.objects["ShopperB"]; BR_ = make_human_ctrl(Bp); BH = Human(BR_); add_hand_limits(Bp)
def pathB(f):
    t = min(T(f), 2.3); return Vector((-9.75, -3.2 + 1.25 * t, 0))
BH.walk(pathB, lambda f: 180.0, 1, 139, stride=0.7)
bpos = pathB(139)
for s in "LR":
    for f in (139, FEND): BH.key_foot(s, f, BH.foot_xy(s, bpos, 180.0), 180.0)
for f in list(range(139, FEND + 1, 50)) + [FEND]:
    hy = 55 + 10 * math.sin(f * 0.011); tw = 28 + 4 * math.sin(f * 0.02)
    BH.key_root(f, Vector((bpos.x, bpos.y, BH.root_head.z - 0.02 + 0.004 * math.sin(f * 0.05))), yaw=180.0); BH.key_spine(f, flex=3 + math.sin(f * 0.06), twist=tw, head=(4 * math.sin(f * 0.03), hy))
for s, sx in (("L", -1), ("R", 1)):        # elbows bent; startled hands up at the noise, then one hand to her chest
    for f in (1, 30, 139, 600, FEND):
        p = pathB(f); up = 0.0
        BH.key_hand(s, f, Vector((p.x + 0.23 * sx, p.y + 0.14 + 1.2 * up, 0.97 + up)), Vector((0, 0.6, -0.75)), Vector((-sx, 0, 0)), Vector((p.x + 0.5 * sx, p.y - 0.4, 1.1)))
    apply_pose(Bp, s, "relaxed", 1)
for rig in (A, SCo, Bp):
    for f in (40, 300, 560, 780, 1030, 1200): blink(rig, f + random.randint(0, 30), 0)

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
for f, dd in ((IMPACT - 1, 0.0), (IMPACT, 0.0), (IMPACT + 2, 0.08), (IMPACT + 4, 0.11), (IMPACT + 7, 0.09), (IMPACT + 12, 0.03), (IMPACT + 18, 0.0)):   # R5: one clear dent over the beat
    we_to.location = (dd, 0, 0); we_to.keyframe_insert("location", frame=f)
wm = tee.modifiers.new("Dimple", 'WARP'); wm.object_from = imp; wm.object_to = we_to; wm.falloff_radius = 0.12; wm.falloff_type = 'SMOOTH'
wv = tee.modifiers.new("Ripple", 'WAVE'); wv.start_position_object = imp; wv.use_normal = True; wv.use_x = wv.use_y = True
wv.height = 0.009; wv.width = 0.03; wv.narrowness = 1.2; wv.speed = 0.006; wv.time_offset = IMPACT; wv.lifetime = 50; wv.damping_time = 35; wv.falloff_radius = 0.2
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
th.scale = (S, 1e-4, 1e-4); th.keyframe_insert("scale", frame=1); th.keyframe_insert("scale", frame=IMPACT)
th.scale = (S, S * 2.0, S * 2.0); th.keyframe_insert("scale", frame=IMPACT + 3); th.keyframe_insert("scale", frame=FEND)
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
def surf_trees(f):
    sc.frame_set(f); dg_ = bpy.context.evaluated_depsgraph_get()
    e = _body.evaluated_get(dg_); me = e.to_mesh(); mw = _body.matrix_world
    V = [mw @ v.co for v in me.vertices]; Pp = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear()
    tb = _BVH.FromPolygons(V, [p for p in Pp if not any(i in _ARM for i in p)])
    et = tee.evaluated_get(dg_); mt = et.to_mesh(); tv = [tee.matrix_world @ v.co for v in mt.vertices]; tp = [tuple(p.vertices) for p in mt.polygons]; et.to_mesh_clear()
    return tb, _BVH.FromPolygons(tv, tp)
def sdist(trees, q):
    best = 9.0
    for t in trees[:1]:            # body only (the shirt rides 0-8 mm above it)
        loc, nr, _i, d = t.find_nearest(q, 0.08)
        if loc is None: continue
        sd_ = d if (q - loc).dot(nr) >= 0 else -d
        if abs(sd_) < abs(best): best = sd_
    return best
def fingers_to_shirt(sd, f):
    """ray-fit: curl each finger (from its current pose toward a fist) until its tip rests ON the shirt (0-4 mm), never in it"""
    trees = surf_trees(f); H = _Hand(W, sd); Mw = W.matrix_world
    cur = {bn: W.pose.bones[bn].rotation_quaternion.copy() for bn in _chain(sd)}; fist = _pose_rots(W, sd, "power_fist"); out = {}
    for k in FING:
        chain = [_b(k, j, sd) for j in (1, 2, 3)]; pick = 0.0
        for t in [i * 0.06 for i in range(0, 7)]:      # never past a soft curl: the hand stays a flat palm on her belly
            trial = dict(cur)
            for bn in chain: trial[bn] = cur[bn].slerp(fist[bn], t)
            F = H.fk(trial); tip = Mw @ F[chain[-1]][1]; mids = [Mw @ F[bn][1] for bn in chain[:2]]
            dtip = sdist(trees, tip)
            if min(sdist(trees, m) for m in mids) < 0.007 or dtip < 0.006: break
            pick = t
            if dtip <= 0.010: break
        for bn in chain:
            q = cur[bn].slerp(fist[bn], pick); pb = W.pose.bones[bn]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=bn)
        out[k] = round(pick, 2)
    print("FINGERFIT", sd, f, out)
def onbelly(sd, f, dy, dz, fdir, air=0.004, pose="flat_palm"):
    apply_pose(W, sd, pose, f, amount=1.0, spread=0.25)     # R2: open flat palm, relaxed slight spread, resting ON the shirt
    sc.frame_set(f); c = imp.matrix_world.translation.copy(); n = (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
    place_hand(W, sd, f, c + Vector((0, dy, dz)), -n, Vector(fdir).normalized(), skin=0.02); settle(f, n, sd, extra=air)
RB = (-0.075, 0.0, (0.0, 0.85, 0.5))         # right hand beside the hole (lower, her right): the hole stays visible
LB_ = (0.10, 0.01, (0.0, -0.75, 0.6))         # left hand above-left of it
hand("R", 106, (0.38, -0.27, 1.02), (0.4, 0.5, -0.2), (0, 1, 0), (-0.3, -0.8, 1.0))   # swings round in front, clear of her body
hand("R", 112, (0.41, -0.22, 1.02), (0.3, 0.6, -0.2), (0, 1, 0), (-0.3, -0.8, 1.0))   # eased 3 cm forward of her body (f110-118)
for f in [118, 140, 155, 168, 180] + list(range(331, 961, 30)) + [960]: onbelly("R", f, *RB)
# left hand: holds the box, opens (drop at 120), comes to her belly
apply_pose(W, "L", "cup_hold", REL, amount=0.35, spread=0); apply_pose(W, "L", "open_alarm", REL + 6, amount=0.7, spread=0); apply_pose(W, "L", "open_alarm", 123, amount=0.6, spread=0)
_pn = "Pole_elbow.L"; _ppb = WH.r.PB[_pn]; _ppb.location = WH.r.rest(_pn).to_3x3().inverted() @ (wpt(0.0, 0.95, 1.05) - WH.r.BN[_pn].head_local); _ppb.keyframe_insert("location", frame=136, group=_pn)   # elbow pole for the belly hold
for f in (138, 400, 800, 1273): hand("L", f, (0.25, 0.26, 0.98), (0.62, -0.15, -0.72), (0, -1, 0), (-0.3, 0.7, 1.0))   # ONE hand on the belly: her left hangs relaxed at her side
apply_pose(W, "L", "relaxed", 140, amount=1.0, spread=0)
pass
# R4: she takes her right hand off and looks at the hole; the arm hangs relaxed with a bent elbow, fingers together
hand("R", 978, (0.36, -0.22, 1.02), (0.5, 0.2, -0.3), (0, 1, 0), (-0.3, -0.7, 1.0))
for f in (992, 1040):
    hand("R", f, (0.25, -0.24, 1.0), (0.62, 0.15, -0.72), (0, 1, 0), (-0.3, -0.7, 1.0))
for f, p_, a in ((978, "relaxed", 0.6), (992, "relaxed", 1.0), (1040, "relaxed", 1.0)): apply_pose(W, "R", p_, f, amount=a, spread=0)
# P: she pinches the bullet out of the hole, lifts it to her face and looks at it (relief)
def pinch_at(f, target):
    apply_pose(W, "R", "pinch", f, amount=0.6)
    for _ in range(3):
        sc.frame_set(f); pb_ = W.pose.bones; Mw = W.matrix_world
        pp = (Mw @ pb_["finger1-3.R"].tail + Mw @ pb_["finger2-3.R"].tail) / 2
        ik = pb_["IK_hand.R"]; ik.location = ik.location + W.data.bones["IK_hand.R"].matrix_local.to_3x3().inverted() @ (Mw.inverted().to_3x3() @ (target - pp))
        ik.keyframe_insert("location", frame=f, group=ik.name)
def hole(f):
    sc.frame_set(f); return imp.matrix_world.translation.copy(), (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
for f, out_ in ((1075, 0.10), (1095, 0.035), (1115, 0.02), (1135, 0.03), (1154, 0.03), (1164, 0.02), (1170, 0.022), (1178, 0.07)):   # she reaches to the hole, feels it, then pinches the bullet out
    c, n = hole(f); place_hand(W, "R", f, c + n * (out_ + 0.03) + Vector((0, -0.02, -0.02)), -n, Vector((0, 0.3, -1)).normalized(), skin=0.0)
    pinch_at(f, c + n * out_)
pass   # no up-turn key: wrist stays neutral
for f, pp_ in ((1187, wpt(0.36, -0.10, 1.04)), (1196, wpt(0.34, -0.10, 1.09)), (1238, wpt(0.34, -0.10, 1.10)), (1273, wpt(0.33, -0.11, 1.08))):
    # palm up at chest height, fingertips toward the camera side: the bullet sits on top of her pinch, in view, and she looks down at it
    place_hand(W, "R", f, pp_, Vector((0.15, 0, 1)).normalized(), Vector((0.75, -0.6, 0.15)).normalized(), skin=0.0); pinch_at(f, pp_ + Vector((0.05, -0.04, 0.035)))
for _m in _body.modifiers: _m.show_viewport = True
for _m in _body.modifiers: _m.show_viewport = True
# relief smile: two shape keys, mouth corners sculpted up (R5: one continuous shape-key move)
_bme = _body.data
if _bme.shape_keys is None: _body.shape_key_add(name="Basis", from_mix=False)
_vg = {g.name: g.index for g in _body.vertex_groups}
_upL = (_body.matrix_world.inverted().to_3x3() @ Vector((0, 0, 1))).normalized()
_cen = {}
for s_ in ("L", "R"):
    gi = _vg.get("oris07." + s_); ws = []
    for v in _bme.vertices:
        for g in v.groups:
            if g.group == gi and g.weight > 0.05: ws.append((v.index, g.weight, v.co.copy()))
    _cen[s_] = ws
_mid = sum((c for s_ in _cen for _, _, c in _cen[s_]), Vector()) / max(1, sum(len(_cen[s_]) for s_ in _cen))
for s_ in ("L", "R"):
    kb = _body.shape_key_add(name="Smile" + s_, from_mix=False); ws = _cen[s_]
    if ws:
        cc = sum((c for _, _, c in ws), Vector()) / len(ws); out_ = (cc - _mid); out_ = (out_ - _upL * out_.dot(_upL)).normalized()
        for vi, w, c in ws: kb.data[vi].co = c + (_upL * 0.0035 + out_ * 0.0015) * w
    for f, v in ((1, 0.0), (1236, 0.0), (1258, 1.0), (FEND, 1.0)): kb.value = v; kb.keyframe_insert("value", frame=f)
    print("SMILE", s_, len(ws))
# ================================================================== bullet: through the shop window, down the aisle, into her shirt
bul = bpy.data.objects["Bullet"]; bul.rotation_mode = 'QUATERNION'
XWIN = 12.0
def bullet_store(f):
    """tip position (world): bursts through the window (f8) toward the camera side, then the last half metre into her shirt (f64-72)"""
    if f <= 30: x = XWIN + 0.4 - (f - 6) * 0.2
    else: x = P.x + 1.2 * max(0, (IMPACT - f)) / 8.0
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
for f, hv in ((1, True), (5, False), (17, True), (63, False), (IMPACT + 1, True)):
    bul.hide_render = hv; bul.hide_viewport = hv; bul.keyframe_insert("hide_render", frame=f); bul.keyframe_insert("hide_viewport", frame=f)
# motion streak behind the bullet (thin, tapering, warm glow) so its flight reads at speed
_st = bmesh.new(); _sr = []
for i in range(13):
    x = -20.0 * i / 12; r = 0.17 * (1 - i / 12) ** 0.8 + 0.004
    _sr.append([_st.verts.new((x, r * math.cos(2 * math.pi * k / 12), r * math.sin(2 * math.pi * k / 12))) for k in range(12)])
for r1, r2 in zip(_sr, _sr[1:]):
    for k in range(12): _st.faces.new((r1[k], r1[(k + 1) % 12], r2[(k + 1) % 12], r2[k]))
stme = bpy.data.meshes.new("Streak"); _st.to_mesh(stme); _st.free()
stm = bpy.data.materials.new("M_streak"); stm.use_nodes = True; _N = stm.node_tree.nodes; _L = stm.node_tree.links; _N.remove(_N["Principled BSDF"])
_em = _N.new("ShaderNodeEmission"); _em.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1); _em.inputs["Strength"].default_value = 6.0
_L.new(_em.outputs[0], _N["Material Output"].inputs["Surface"]); stme.materials.append(stm)
streak = bpy.data.objects.new("BulletStreak", stme); bpy.data.collections["REAL"].objects.link(streak); streak.parent = bul

# the street outside the shop window reads as daylit facades (not a dark empty glass frame)
for m_ in [m for m in bpy.data.materials if m.name.startswith("M_bld")]:
    b_ = m_.node_tree.nodes.get("Principled BSDF")
    if b_:
        col = b_.inputs["Base Color"].default_value
        b_.inputs["Emission Color"].default_value = (col[0], col[1], col[2], 1) if not b_.inputs["Base Color"].is_linked else (0.8, 0.75, 0.65, 1)
        b_.inputs["Emission Strength"].default_value = 0.55
# shop window: entry hole + crack star appear as the bullet punches through (keyed scale, no Scene Time)
cm = bpy.data.materials.new("M_crack"); cm.use_nodes = True; nt = cm.node_tree; N = nt.nodes; L = nt.links
N.remove(N["Principled BSDF"]); mo = N["Material Output"]
tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs["Scale"].default_value = 30.0
L.new(tc.outputs["Object"], vo.inputs["Vector"])
gr = N.new("ShaderNodeMath"); gr.operation = 'LESS_THAN'; gr.inputs[1].default_value = 0.03; L.new(vo.outputs["Distance"], gr.inputs[0])
rad = N.new("ShaderNodeVectorMath"); rad.operation = 'LENGTH'; L.new(tc.outputs["Object"], rad.inputs[0])
fall = N.new("ShaderNodeMapRange"); fall.inputs["From Min"].default_value = 0.0; fall.inputs["From Max"].default_value = 0.42
fall.inputs["To Min"].default_value = 1.0; fall.inputs["To Max"].default_value = 0.0; L.new(rad.outputs["Value"], fall.inputs["Value"])
mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; L.new(gr.outputs[0], mul.inputs[0]); L.new(fall.outputs["Result"], mul.inputs[1])
core = N.new("ShaderNodeMath"); core.operation = 'LESS_THAN'; core.inputs[1].default_value = 0.012; L.new(rad.outputs["Value"], core.inputs[0])
mx_ = N.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; L.new(mul.outputs[0], mx_.inputs[0]); L.new(core.outputs[0], mx_.inputs[1])
em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 1, 1, 1); em.inputs["Strength"].default_value = 3.0
tr = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader"); L.new(mx_.outputs[0], ms.inputs[0]); L.new(tr.outputs[0], ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2])
L.new(ms.outputs[0], mo.inputs["Surface"])
_c = bmesh.new(); bmesh.ops.create_circle(_c, cap_ends=True, segments=48, radius=0.5)
cme2 = bpy.data.meshes.new("Crack"); _c.to_mesh(cme2); _c.free(); cme2.materials.append(cm)
crack = bpy.data.objects.new("WindowCrack", cme2); bpy.data.collections["REAL"].objects.link(crack)
crack.location = (XWIN - 0.012, P.y, P.z); crack.rotation_euler = (0, math.radians(-90), 0)
for f, s_ in ((1, 0.001), (7, 0.001), (8, 0.5), (11, 0.85), (18, 1.0), (FEND, 1.0)):
    crack.scale = (s_, s_, s_); crack.keyframe_insert("scale", frame=f)
# glass sparkle: a few tiny shards that fly off the hole, keyed
shm = bpy.data.materials.new("M_shard"); shm.use_nodes = True; shm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
shm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.05
for i in range(14):
    _s = bmesh.new(); bmesh.ops.create_icosphere(_s, subdivisions=0, radius=0.006); sme = bpy.data.meshes.new("Shard"); _s.to_mesh(sme); _s.free(); sme.materials.append(shm)
    o = bpy.data.objects.new("Shard%02d" % i, sme); bpy.data.collections["REAL"].objects.link(o)
    v = Vector((-random.uniform(0.4, 1.2), random.uniform(-0.6, 0.6), random.uniform(-0.3, 0.7)))
    for f in (1, 7, 8, 30, 31):
        k = max(0, f - 8) / 60.0
        o.location = Vector((XWIN - 0.02, P.y, P.z)) + v * 2 * k + Vector((0, 0, -4.9 * k * k)); o.scale = (2, 2, 2) if 8 <= f <= 30 else (0, 0, 0)
        o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f)

# ================================================================== macro cross-section: its own static set (hard cuts, no in-body scale trick)
root = bpy.data.objects["MacroRoot"]; root.parent = None
MR = Matrix.Translation((0.0, 60.0, 5.0)) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Diagonal((S, S, S, 1))
root.matrix_world = MR; bpy.context.view_layer.update()
# macro bullet: its own copy on the macro root
_og = bmesh.new(); _prof = []
for i in range(25):            # profile along x (0 = flat base with a rim groove, 0.6 = pointed ogive nose)
    x = 0.6 * i / 24
    if x < 0.30: r = 0.18 - (0.012 if 0.04 < x < 0.07 else 0.0)
    else: u = (x - 0.30) / 0.30; r = 0.18 * max(0.0, 1 - u ** 1.7) ** 0.62
    _prof.append((x, max(r, 0.004)))
_rings = []
for x, r in _prof:
    _rings.append([_og.verts.new((x, r * math.cos(2 * math.pi * k / 32), r * math.sin(2 * math.pi * k / 32))) for k in range(32)])
for r1, r2 in zip(_rings, _rings[1:]):
    for k in range(32): _og.faces.new((r1[k], r1[(k + 1) % 32], r2[(k + 1) % 32], r2[k])).smooth = True
_og.faces.new(list(reversed(_rings[0])))
ogme = bpy.data.meshes.new("BulletOgive"); _og.to_mesh(ogme); _og.free()
for m_ in bul.data.materials: ogme.materials.append(m_)
bm2 = bpy.data.objects.new("BulletMacro", ogme)
bpy.data.collections["MACRO"].objects.link(bm2); bm2.parent = root; bm2.matrix_parent_inverse = Matrix.Identity(4)
for o in [o for o in bpy.data.objects if o.name.startswith("M_Vessel")]: bpy.data.objects.remove(o, do_unlink=True)   # no thin line artefacts
hb = bpy.data.objects.new("BulletInHand", ogme); bpy.data.collections["REAL"].objects.link(hb); hb.rotation_mode = 'XYZ'
def wristR(f):
    sc.frame_set(f); return W.matrix_world @ W.pose.bones["wrist.R"].matrix
sc.frame_set(1164); _pbn = W.pose.bones; _Mw = W.matrix_world
_pp = (_Mw @ _pbn["finger1-3.R"].tail + _Mw @ _pbn["finger2-3.R"].tail) / 2
_c, _n = imp.matrix_world.translation.copy(), (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
_xa = -_n; _ya = _xa.cross(Vector((0, 0, 1))).normalized(); _za = _xa.cross(_ya)
_B0 = Matrix((_xa, _ya, _za)).transposed().to_4x4(); _B0.translation = _pp - _xa * 0.004; _B0 = _B0 @ Matrix.Diagonal((1.3 * S, 1.3 * S, 1.3 * S, 1))   # base in her fingers, nose still in the hole
_OFFB = wristR(1164).inverted() @ _B0
sc.frame_set(1200); _pp2 = (_Mw @ _pbn["finger1-3.R"].tail + _Mw @ _pbn["finger2-3.R"].tail) / 2
_xu = Vector((0.35, -0.2, 1)).normalized(); _yu = _xu.cross(Vector((1, 0, 0))).normalized(); _zu = _xu.cross(_yu)
_B1 = Matrix((_xu, _yu, _zu)).transposed().to_4x4(); _B1.translation = _pp2 + _xu * 0.002; _B1 = _B1 @ Matrix.Diagonal((1.3 * S, 1.3 * S, 1.3 * S, 1))   # nose up out of her pinch (the insert from the cut at 1193)
_OFFB2 = wristR(1200).inverted() @ _B1
for f in range(1164, FEND + 1):
    _M = wristR(f) @ (_OFFB if f < 1193 else _OFFB2); _ix = W.matrix_world @ W.pose.bones["finger2-3.R"].tail; _ax = _M.to_3x3().col[0].normalized()
    _M.translation = _ix + _ax * 0.004   # R4: parented to the index tip, 4 mm gap
    hb.matrix_world = _M; hb.keyframe_insert("location", frame=f); hb.keyframe_insert("rotation_euler", frame=f); hb.keyframe_insert("scale", frame=f)
hb.scale = (0, 0, 0); hb.keyframe_insert("scale", frame=1); hb.keyframe_insert("scale", frame=1163)
bm2.rotation_mode = 'XYZ'; bm2.scale = (1, 1, 1)
# tip depth (macro units) per VO frame: touches the shirt 130, dimple, pierces 183, fast through fat (2 s), slows through fascia and muscle, stops 945
DK = [(181, -1.4), (192, -0.02), (198, 0.18), (203, 0.30), (215, 0.85), (228, 1.4), (242, 1.85), (256, 2.15), (268, 2.32), (278, 2.37), (1273, 2.37)]   # stops in the fat (muscle starts at 4.49)
Dfn = pchip(DK)
def D(f): return Dfn(f)
for f in range(175, 340):
    bm2.location = (D(f) - 0.6, 0, 0); bm2.rotation_euler = (0.05 * min(f, 275), 0, 0)
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
    if f < 192: return 0.0
    if f < 203: return max(0.0, D(f))
    u = (f - 203) / 60.0; return 0.28 * math.exp(-u * 3.0) * math.cos(u * 14.0)
for nm, gain in (("M_Fabric", 1.0), ("M_Epidermis", 1.0), ("M_Dermis", 0.85)):
    o = bpy.data.objects[nm]; o.shape_key_add(name="Basis"); k = o.shape_key_add(name="dimple")
    for i, v in enumerate(o.data.vertices):
        r2 = v.co.y ** 2 + v.co.z ** 2; k.data[i].co = v.co + Vector((gain * math.exp(-r2 / 0.6), 0, 0))
    k.slider_min = -1
    for f in range(175, 340, 2):
        dv = dimple_val(f) + (0.07 if nm == "M_Fabric" and 192 <= f < 203 else 0.0)
        k.value = max(-0.5, min(1.0, dv)); k.keyframe_insert("value", frame=f)
    h = o.shape_key_add(name="hole", from_mix=False)
    for i, v in enumerate(o.data.vertices):
        rr = math.hypot(v.co.y, v.co.z)
        if rr < 0.5:
            dd = Vector((0, v.co.y, v.co.z)).normalized() if rr > 1e-4 else Vector((0, 0, 1))
            h.data[i].co = v.co + dd * (0.23 + (rr / 0.5) * 0.27 - rr) + Vector((0.06 * (1 - rr / 0.5), 0, 0))
    for f, hv in ((201, 0.0), (206, 1.0), (FEND, 1.0)): h.value = hv; h.keyframe_insert("value", frame=f)
bpy.data.objects.remove(bpy.data.objects["M_HoleDecal"], do_unlink=True)   # no floating disc
def vel(f): return (D(f + 2) - D(f - 2)) / 4 * FPS
tipctl = bpy.data.objects["TipCtl"]
for f in range(175, 340, 2):
    e = min(1.0, max(0.0, vel(f) / 1.6)) if f > 203 else 0.0
    wob = (1.6 * math.exp(-(f - 272) / 35.0) if f > 272 else 0.0) + (0.35 * math.exp(-(f - 203) / 50.0) if f > 203 else 0.0)   # the fat compresses and rebounds as it stops the bullet
    tipctl.location = (D(f), e, wob); tipctl.keyframe_insert("location", frame=f)
# no rings at all (director): delete every ring object
for o in [o for o in bpy.data.objects if o.name.startswith("M_Ring")]: bpy.data.objects.remove(o, do_unlink=True)
# fat 'ahead of the tip' push switches on as the tip pierces into the fat (f183 = 3.03 s)
for nd in bpy.data.node_groups["FatLobulesGN"].nodes if "FatLobulesGN" in bpy.data.node_groups else []:
    if nd.bl_idname == "ShaderNodeMath" and nd.operation == 'GREATER_THAN' and abs(nd.inputs[1].default_value - 3.15) < 1e-6: nd.inputs[1].default_value = 3.35
# muscle fibres part exactly where the bullet tip is
for o in [o for o in bpy.data.objects if o.name.startswith("M_MuscleFib")]:
    ph = random.uniform(0, 6.28); x = o.location.x; yrow = o.location.y
    o.shape_key_add(name="Basis"); k = o.shape_key_add(name="part")
    for i, v in enumerate(o.data.vertices):
        k.data[i].co = v.co + Vector((0, -0.34 * math.exp(-(v.co.z / 0.3) ** 2) * (1.0 if yrow > -0.3 else 0.5), 0))
    for f in (175, 340):
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
# vessels removed
for o in []:
    for f in ():
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
_bulvis = lambda f: (5 <= f <= 16) or (63 <= f <= IMPACT)
for o in REALO:
    if o.name in ("BulletStreak", "Trail"): key_vis(o, _bulvis); continue
    key_vis(o, (lambda f: False) if (o.name == "Carton" or o.name.startswith("Stocker") or o.name == "Cart") else is_real)
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
def Dsm(f, w=28):
    return sum(D(f + i) for i in range(-w, w + 1, 4)) / len(range(-w, w + 1, 4))
def head_pt(rig, f):
    sc.frame_set(f); return rig.matrix_world @ rig.pose.bones["head"].head
def shot_cam(f):
    for f0, f1, name in SHOTS:
        if f0 <= f <= f1: break
    u = sm((f - f0) / max(1, f1 - f0))
    if name == "W_window":   # medium on the shop window from inside: it shatters, the bullet streaks through
        cp = lin(Vector((10.1, -0.55, 1.2)), Vector((10.25, -0.5, 1.2)), u); return cp, Vector((12.0, 0.3, 1.1)), Vector((0, 0, 1)), 35, 8.0
    if name == "F_face":     # her face: startled by the crash
        tg = face_pt(f); cp = lin(Vector((0.78, 0.02, 1.62)), Vector((0.72, 0.06, 1.62)), u); return cp, tg, Vector((0, 0, 1)), 45, 8.0
    if name == "H_hit":      # face and belly: the bullet streaks in, the shirt dents, her body jolts, she staggers and drops the box
        tg = face_pt(f).lerp(P, 0.5); cp = lin(Vector((1.3, -0.5, 1.25)), Vector((1.2, -0.45, 1.22)), u); return cp, tg, Vector((0, 0, 1)), 28, 8.0
    if name == "L_look":     # closer: she looks down at her stomach
        tg = face_pt(f).lerp(P, 0.5); cp = lin(Vector((1.02, -0.34, 1.15)), Vector((0.94, -0.3, 1.16)), u); return cp, tg, Vector((0, 0, 1)), 30, 8.0
    if name == "R1_medium":  # medium, sharp: bent in pain, hands on her belly beside the hole; shoppers react behind her
        tg = face_pt(f).lerp(P, 0.4).lerp(Vector((-3.0, 0.3, 1.2)), 0.12); cp = lin(Vector((1.7, -0.45, 1.4)), Vector((1.25, -0.36, 1.36)), u); return cp, tg, Vector((0, 0, 1)), 26, 8.0   # looking down the aisle: shoppers react behind her; slow push
    if name == "R2_close":   # her face and hands: pain, breathing, blinks
        tg = face_pt(f).lerp(P, 0.45); cp = lin(Vector((1.05, -0.45, 1.10)), Vector((0.86, -0.12, 1.16)), u); return cp, tg, Vector((0, 0, 1)), 34, 8.0   # slow arc + push
    if name == "R3_help":    # tighter two-shot: the shopper comes to her side
        tg = face_pt(f).lerp(head_pt(A, f), 0.3) + Vector((0, 0, -0.12)); cp = lin(Vector((1.8, 0.25, 1.42)), Vector((1.62, 0.2, 1.42)), u); return cp, tg, Vector((0, 0, 1)), 30, 8.0
    if name == "R4_hole":    # she takes her hand off and looks at the hole in her shirt
        tg = face_pt(f).lerp(P, 0.55); cp = lin(Vector((1.0, -0.2, 1.12)), Vector((0.92, -0.16, 1.14)), u); return cp, tg, Vector((0, 0, 1)), 30, 8.0
    if name == "P_relief":   # she pulls the bullet out, looks at it, relief, nods to the helper; held end frame
        uu = sm(min(1.0, (f - f0) / 98.0)); tg = face_pt(min(f, 1245)).lerp(wpt(0.3, -0.06, 1.2), 0.35)
        cp = lin(Vector((1.1, -0.35, 1.32)), Vector((0.98, -0.28, 1.38)), uu); return cp, tg, Vector((0, 0, 1)), 32, 8.0
    if name == "R5_feel":    # insert: her fingers find the hole in her shirt; her face looking down above it
        sc.frame_set(f); c_ = imp.matrix_world.translation.copy(); n_ = (imp.matrix_world.to_3x3() @ Vector((-1, 0, 0))).normalized()
        tg = c_.lerp(face_pt(f), 0.4); cp = c_ + n_ * lin(0.62, 0.50, u) + Vector((0.12, -0.1, 0.2)); return cp, tg, Vector((0, 0, 1)), 36, 8.0
    if name == "P_wince":    # her face as she pulls it out (off screen): wince, looks down
        tg = face_pt(f) + Vector((0, 0, -0.04)); cp = lin(Vector((0.68, -0.15, 1.28)), Vector((0.62, -0.14, 1.28)), u); return cp, tg, Vector((0, 0, 1)), 40, 8.0   # below her eye line, looking up at her face
    if name == "P_bullet":   # insert: the bullet between her fingertips, her face looking down at it above
        # one INSERT from her reach to the hole, through the pinch and pull-out, to her looking at the bullet (tracks her index fingertip)
        bp = Vector((0, 0, 0))
        for k_ in (-4, -2, 0, 2, 4): sc.frame_set(max(1186, min(1216, f + k_))); bp += (W.matrix_world @ W.pose.bones["finger2-3.R"].tail) / 5.0
        fp = face_pt(f); w_ = 0.33
        tg = bp.lerp(fp, w_); cp = bp + Vector((0.30, -0.16, 0.06)) + Vector((0.06, -0.03, 0.04)) * (w_ / 0.33); return cp, tg, Vector((0, 0, 1)), 50, 8.0
    if name == "P_face":     # her face: relief, a breath out, a small smile; held to the end
        uu = sm(min(1.0, (f - f0) / 24.0)); tg = face_pt(min(f, 1250)) + Vector((0, 0, -0.06))
        cp = lin(Vector((0.95, -0.25, 1.52)), Vector((0.86, -0.22, 1.53)), uu); return cp, tg, Vector((0, 0, 1)), 58, 8.0
    # cross-section: ONE continuous push, side-on, following the bullet (smoothed) and still pushing in while it stops in the fat
    cdep = Dsm(f) - 0.3 + 0.35; dist = lin(4.4, 2.5, u); az = math.radians(lin(92, 80, u))
    tg = Vector((cdep, 0, 0)); cpl = tg + dist * Vector((math.cos(az) * math.cos(math.radians(4)), math.sin(az) * math.cos(math.radians(4)), math.sin(math.radians(4))))
    return MR @ cpl, MR @ tg, (MR.to_3x3() @ Vector((-1, 0, 0))).normalized(), 45.0, 45.0
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
    cd.dof.use_dof = nm_ not in ("W_window",); cd.dof.keyframe_insert("use_dof", frame=f)   # window shot: deep focus (her and the window both sharp)
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
cl = bpy.data.lights.new("Catchlight", 'POINT'); cl.energy = 8.0; cl.shadow_soft_size = 0.03
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
