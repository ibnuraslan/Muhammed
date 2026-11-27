"""DwarfGiant v009 stage B: acting, growth, x-ray beats, hormone stream, seasons, dusk, the ONE camera, VO.
blender -b a.blend --python 02_animate.py -- <vo.mp3> <out.blend>
Built to the client's VO (v008 recording) from the start. Beat frames = 1 + round(seconds x 60) of the words:
  1 'He was way too short' / 145 'but a tumor' / 335 'It flooded his body' / 463 'and suddenly' (grows 519-680)
  679 'His hands, his feet' / 872 'and he shot up' / 1073 'But his spine' / 1196 'His vision blurred'
  1281 'Then his hearing' / 1415 'Doctors removed the tumor' / 1496 'which slowed his growth' / 1629 'By the time he died'
  1829 'the only man in history' / end 2083.
The hero never moves his feet: he grows by the rig object's scale about the floor point under him (feet planted)."""
import bpy, sys, math, random, os
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
PIPE = "/home/user/Muhammed/blender/pipeline"
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(PIPE + "/anim_lib.py").read())
exec(open(PIPE + "/hand_poses.py").read())
exec(open(HERE + "/lib_anim.py").read())
args = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = args[0], args[1]
random.seed(26)
END = 2083
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); LOG.append(s); print("LOG", s)
O = bpy.data.objects
HR, HB, OR_, OBD = O["Hero"], O["Hero.body"], O["Officer"], O["Officer.body"]
HCL = [c for c in HR.children if c.type == 'MESH' and "suit" in c.name][0]
OCL = [c for c in OR_.children if c.type == 'MESH' and "suit" in c.name][0]
BRAIN = [o for o in O if o.name.startswith("Brain")][0]; TUM = O["Tumour"]
VERTS = [o for o in O if o.name.startswith("Vert_")]
REST_H = HR["rest_height"]; OREST = OR_["rest_height"]

for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
# ================================================================== rigs
CH = make_human_ctrl(HR); CO = make_human_ctrl(OR_)
for rig in (HR, OR_):
    add_hand_limits(rig)
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s in "LR":
        lo = rig.pose.bones["lowerarm01." + s]; lo.use_ik_limit_x = True; lo.ik_min_x = math.radians(-40); lo.ik_max_x = math.radians(140)
        kn = rig.pose.bones["lowerleg01." + s]; kn.use_ik_limit_x = True; kn.ik_min_x = math.radians(-2); kn.ik_max_x = math.radians(120)
HH, HO = Human(CH), Human(CO)

# ---- the hero's height (m) over the film -> rig scale (about the floor point under his feet)
HEIGHT = pchip([(1, 1.37), (519, 1.37), (600, 1.56), (680, 1.72), (872, 1.76), (930, 1.86), (1000, 1.98), (1073, 2.07),
                (1415, 2.10), (1496, 2.12), (1560, 2.17), (1629, 2.22), (1700, 2.29), (1790, 2.34), (END, 2.34)])
def hscale(f): return HEIGHT(f) / REST_H
for f in list(range(1, END + 1, 3)) + [END]:
    HR.scale = (hscale(f),) * 3; HR.keyframe_insert("scale", frame=f)
set_interp(HR, 'LINEAR', "scale")
OSC = 1.80 / OREST
OR_.scale = (OSC,) * 3
OPOS = Vector((0.95, -0.30)); OYAW = -58.0
log("hero rest", round(REST_H, 3), "officer scale", round(OSC, 3))

def to_arm(rig, f, v):
    fs(f); return rig.matrix_world.inverted() @ Vector(v)

# ---- stance: IK feet planted on the floor (armature space; the floor is z=0 there for both rigs)
def key_pole(C, s, f, target, kind="elbow"):
    n = ("Pole_elbow." if kind == "elbow" else "Pole_knee.") + s; pb = C.PB[n]
    pb.location = C.rest(n).to_3x3().inverted() @ (Vector(target) - C.BN[n].head_local)
    pb.keyframe_insert("location", frame=f, group=n)

def stand(Hm, C, f, pos2, yaw, flex=2.0, side=0.0, dz=0.0, stance=0.11):
    pos = Vector((pos2[0], pos2[1], Hm.root_head.z - 0.014 + dz))
    Hm.key_root(f, pos, yaw=yaw, flex=flex, side=side)
    Ry = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    for s, sg in (("L", 1), ("R", -1)):
        a = C.BN["foot." + s].head_local
        off = Ry @ Vector((sg * stance, a.y - Hm.root_head.y, 0))
        tgt = Vector((pos2[0] + off.x, pos2[1] + off.y, a.z))
        M = Matrix.Translation(tgt) @ Matrix.Rotation(math.radians(yaw + sg * 6), 4, 'Z') @ Matrix.Translation(-a) @ C.rest("IK_foot." + s)
        C.key_world("IK_foot." + s, f, M)
        key_pole(C, s, f, tgt + Ry @ Vector((sg * 0.06, -0.8, 0.45)), kind="knee")

def key_spine(C, f, flex=0.0, twist=0.0, side=0.0, scol=0.0):
    """scol: scoliosis S-curve amount (deg) on top of the side bend"""
    S_CURVE = {"spine05": 0.6, "spine04": 1.0, "spine03": 0.2, "spine02": -1.0, "spine01": -0.8}
    for n, w in Human.SPINE_W.items():
        C.key_rot(n, f, [("X", flex * w), ("Y", side * w + scol * S_CURVE[n]), ("Z", twist * w)])

_HS = {}
def head_signs(rig):
    if rig.name in _HS: return _HS[rig.name]
    pb = rig.pose.bones["head"]; q0 = pb.rotation_quaternion.copy(); upd()
    e0 = rig.matrix_world.inverted() @ Wh(rig, "eye.L"); out = {}
    for ax, i in (("X", 0), ("Z", 2)):
        pb.rotation_quaternion = Quaternion(Vector([1 if k == i else 0 for k in range(3)]), math.radians(10)); upd()
        out[ax] = rig.matrix_world.inverted() @ Wh(rig, "eye.L") - e0; pb.rotation_quaternion = q0; upd()
    _HS[rig.name] = (1 if out["X"].z < 0 else -1, 1 if out["Z"].x > 0 else -1)
    return _HS[rig.name]
def key_head(C, f, yaw, pitch, roll=0.0):
    """yaw +: toward his own left (+X at rest); pitch +: look down; roll +: ear toward his right shoulder"""
    sx, sz = head_signs(C.o)
    for n, w in (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3)):
        C.key_rot(n, f, [("X", sx * pitch * w), ("Y", roll * w), ("Z", sz * yaw * w)])

# ---- surfaces for clearance (evaluated: what renders)
def bvh_eval(obj):
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]); e.to_mesh_clear(); return b
def ray_surface(objs, origin, direction):
    best = None
    for o in objs:
        h = bvh_eval(o).ray_cast(Vector(origin), Vector(direction).normalized(), 5.0)
        if h[0] is not None and (best is None or h[3] < best[3]): best = h
    return best

def hand_world(Hm, rig, s, f, Ww, d, n, pole_w):
    """key IK_hand from WORLD targets (converted into the rig's armature space at frame f)"""
    fs(f); Mi = rig.matrix_world.inverted(); R3 = Mi.to_3x3().normalized()
    Hm.key_hand(s, f, Mi @ Vector(Ww), R3 @ Vector(d), R3 @ Vector(n), pole=Mi @ Vector(pole_w))

ARMP = ("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "clavicle", "shoulder")
_DOM = {}
def hip_bvh(obj, rig):
    """BVH of the evaluated mesh WITHOUT arm/hand polygons (the ray must find the hip, never the arm itself)"""
    if obj.name not in _DOM:
        d = dom_bones(obj, rig); _DOM[obj.name] = [d.get(i) for i in range(len(obj.data.vertices))]
    dl = _DOM[obj.name]; n0 = len(dl)
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = obj.evaluated_get(dg); me = e.to_mesh(); Mw = obj.matrix_world
    ok = lambda i: not (dl[i % n0] or "").startswith(ARMP)
    polys = [p.vertices[:] for p in me.polygons if all(ok(i) for i in p.vertices)]
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], polys); e.to_mesh_clear(); return b
def hang(Hm, rig, body, cloth, s, f, yaw=0.0, fwd=0.05, drop=0.50, out_extra=0.0):
    """hand hanging relaxed beside the hip, 4.5 cm outside the clothes/body surface (ray-cast), elbow bent ~15-20 deg"""
    sx = 1 if s == "L" else -1
    fs(f); sc_ = rig.scale.x
    Ry = Matrix.Rotation(math.radians(yaw), 3, 'Z')
    sh = Wh(rig, "upperarm01." + s)
    side = Ry @ Vector((sx, 0, 0)); front = Ry @ Vector((0, -1, 0))
    p0 = sh + front * fwd * sc_ - Vector((0, 0, drop * sc_))
    hits = [h for h in (hip_bvh(o, rig).ray_cast(p0 + side * 0.8, -side, 5.0) for o in (cloth, body)) if h[0] is not None]
    hit = min(hits, key=lambda h: h[3]) if hits else None
    surf = hit[0] if hit else p0 + side * 0.20 * sc_
    base = Vector((surf.x, surf.y, p0.z)) + side * (0.045 + out_extra) * max(1.0, sc_)
    # never inside the hip width: the wrist stays at least 0.22 (x rig scale) out from the pelvis centre line
    pel = Wh(rig, "spine05"); lat = (base - pel).dot(side)
    if lat < 0.20 * sc_: base += side * (0.20 * sc_ - lat)
    d = (Ry @ Vector((sx * 0.06, -0.22, -1.0))).normalized(); n = -side
    hand_world(Hm, rig, s, f, base, d, n, sh + side * 0.25 * sc_ + front * -0.40 * sc_ + Vector((0, 0, -0.25 * sc_)))
    apply_pose(rig, s, "relaxed", f)

# ================================================================== the hero (stands at the origin, faces the camera)
HKEYS = [(1, 2.0, 0.0, 0.0), (60, 3.0, 0.5, 0.0), (110, 6.0, 0.0, -0.006), (145, 4.0, 0.0, -0.004), (335, 3.0, 0.0, 0.0),
         (463, 2.0, 0.0, 0.0), (520, -2.0, 0.0, 0.004), (679, 1.0, 0.0, 0.0), (872, 2.0, 0.0, 0.0), (1000, -1.0, 0.0, 0.004),
         (1073, 1.0, 0.0, 0.0), (1150, 9.0, 1.5, -0.012), (1196, 8.0, 1.0, -0.010), (1415, 7.0, 0.0, -0.010),
         (1496, 6.0, 0.0, -0.008), (1629, 7.0, 0.0, -0.010), (1829, 6.0, 0.0, -0.008), (END, 6.5, 0.0, -0.009)]
for f, fl, sd, dz in HKEYS:
    stand(HH, CH, f, (0.0, 0.0), 0.0, flex=fl, side=sd, dz=dz)
def h_flex(f):
    return pchip([(1, 2), (60, 3), (110, 9), (145, 6), (335, 4), (463, 2), (520, -3), (679, 4), (872, 2), (1000, -3), (1073, 2),
                  (1150, 18), (1196, 16), (1415, 13), (1496, 11), (1629, 12), (1829, 9), (END, 9)])(f)
def h_scol(f):
    return pchip([(1, 0), (1073, 0), (1150, 9), (1415, 8), (1496, 6), (END, 6)])(f)
def breath(f, per=210, amp=1.0): return amp * math.sin(2 * math.pi * f / per)
for f in list(range(1, END + 1, 20)) + [END]:
    key_spine(CH, f, flex=h_flex(f) + breath(f), scol=h_scol(f), twist=pchip([(1, 0), (60, 4), (145, 0), (1829, 0), (1900, -6), (END, -3)])(f))
# head: yaw + = toward his left (the officer), pitch - = up
HEADK = [(1, 18, -12), (40, 22, -16), (100, 20, -10), (130, 8, 4), (145, 0, 6), (240, -4, 4), (335, 0, 12), (420, 0, 22),
         (463, 0, 18), (540, 0, 25), (620, 6, -4), (679, 2, 18), (700, 0, 34), (860, 4, 30), (900, 10, 4), (960, -12, -6),
         (1020, 14, 6), (1073, 8, 12), (1150, 2, 22), (1196, 0, 14), (1240, -4, 12), (1281, 6, 10), (1315, -30, 8), (1360, -26, 10), (1400, -32, 8),
         (1415, 4, 14), (1496, 12, 18), (1560, 20, 24), (1629, 24, 26), (1760, 22, 24), (1829, 14, 18), (1900, -22, 14),
         (1975, -18, 12), (2030, -4, 10), (END, 0, 10)]
ROLLK = [(1, 0), (1281, 0), (1315, -14), (1400, -13), (1430, 0), (END, 0)]
hy = pchip([(f, y) for f, y, p in HEADK]); hp = pchip([(f, p) for f, y, p in HEADK]); hr = pchip(ROLLK)
for f in list(range(1, END + 1, 5)) + [END]:
    key_head(CH, f, hy(f) + 1.2 * math.sin(f / 37.0), hp(f) + 0.8 * math.sin(f / 23.0), hr(f))
# face: hopeful -> crushed (army says no) -> puzzled -> astonished -> worried (spine) -> squint (vision) -> strain (hearing)
#       -> calm -> gentle smile at the end
for f, sm, br, jaw, sq in ((1, 0.25, 0.4, 0.0, 0.0), (60, 0.1, 0.2, 0.0, 0.0), (100, -0.35, -0.5, 0.05, 0.0), (145, -0.3, -0.3, 0.0, 0.0),
                           (300, -0.1, 0.3, 0.05, 0.0), (463, 0.0, 0.5, 0.1, 0.0), (540, 0.0, 1.0, 0.35, 0.0), (679, 0.15, 0.8, 0.2, 0.0),
                           (800, 0.3, 0.9, 0.25, 0.0), (900, 0.4, 0.7, 0.1, 0.0), (1073, 0.1, 0.2, 0.0, 0.0), (1150, -0.35, -0.6, 0.1, 0.2),
                           (1196, -0.2, -0.5, 0.0, 0.4), (1240, -0.3, -0.7, 0.05, 0.85), (1281, -0.2, 0.6, 0.1, 0.2),
                           (1380, -0.25, 0.7, 0.15, 0.1), (1415, -0.1, 0.0, 0.0, 0.0), (1550, 0.0, 0.1, 0.0, 0.0),
                           (1700, 0.3, 0.2, 0.0, 0.0), (1829, 0.4, 0.2, 0.0, 0.05), (1950, 0.6, 0.3, 0.0, 0.1), (END, 0.65, 0.3, 0.0, 0.1)):
    key_face(HR, f, smile=sm, brow=br, jaw=jaw, squint=sq)
blinks(HR, [30, 170, 290, 400, 590, 760, 950, 1110, 1215, 1250, 1330, 1460, 1600, 1760, 1880, 2010])
saccades(CH, 1, END, every=38, amp=(1.2, 2.0), seed=7)

# ---- arms: hanging (idle) except: hands up in front of the chest (690-850), right hand cupped behind the right ear (1300-1395)
fs(1)
HANG_F = [1, 60, 110, 145, 240, 335, 463, 560, 660, 679, 872, 940, 1010, 1073, 1150, 1196, 1281, 1415, 1496, 1560, 1629, 1700,
          1760, 1829, 1900, 1980, END]
for i, f in enumerate(HANG_F):
    if 690 <= f <= 860: continue
    fw = 0.05 + 0.015 * math.sin(i * 1.7); dr = 0.50 + 0.01 * math.sin(i * 2.3)
    hang(HH, HR, HB, HCL, "L", f, fwd=fw, drop=dr)
    hang(HH, HR, HB, HCL, "R", f, fwd=fw + 0.01, drop=dr)
# hands up: palms up, ~30 cm in front of the chest, at lower-chest height, looking at them
def chest_point(f):
    fs(f); return (Wh(HR, "spine01") + Wh(HR, "spine02")) / 2
for f in (705, 730, 755, 780, 805, 830, 850, 862):
    fs(f); sc_ = HR.scale.x; c = chest_point(f)
    for s, sx in (("L", 1), ("R", -1)):
        k_ = (f - 705) / 30.0
        w = c + Vector((sx * (0.18 + 0.025 * math.sin(k_ * 2.1)) * sc_, -(0.30 + (0.08 if f == 862 else 0.0)) * sc_, (0.05 + 0.03 * math.sin(k_ * 1.7 + sx)) * sc_))
        d = Vector((-sx * 0.35, -1.0, 0.10)).normalized(); n = Vector((sx * (0.25 + 0.5 * math.sin(k_ * 1.9)), -0.15, 1.0))
        hand_world(HH, HR, s, f, w, d, n, w + Vector((sx * 0.30 * sc_, 0.35 * sc_, -0.30 * sc_)))
        apply_pose(HR, s, "open_alarm" if f in (730, 780, 830) else "relaxed", f)
# bigger hands (acromegaly): wrist bone scale 1 -> 1.22 while he looks at them
for s in "LR":
    pb = HR.pose.bones["wrist." + s]
    for f, k in ((1, 1.0), (710, 1.0), (850, 1.22), (END, 1.22)):
        pb.scale = (k,) * 3; pb.keyframe_insert("scale", frame=f, group=pb.name)
# cupped right hand behind the right ear (his right = -X), palm forward, >=1.5 cm from head and hair
fs(1)
idx = {g.index: g.name for g in HB.vertex_groups}
ear_rest = None
eyez = HR.data.bones["eye.R"].head_local.z
sv_ = [(m, m.show_viewport) for m in HB.modifiers]
for m, _ in sv_: m.show_viewport = False
upd(); dg_ = bpy.context.evaluated_depsgraph_get(); e_ = HB.evaluated_get(dg_); me_ = e_.to_mesh()
A_ = HR.matrix_world.inverted() @ HB.matrix_world
RCO = [A_ @ v.co for v in me_.vertices]; e_.to_mesh_clear()
for m, v_ in sv_: m.show_viewport = v_
upd()
cand = []
for v in HB.data.vertices:
    gw = {idx.get(g.group): g.weight for g in v.groups}
    if gw.get("head", 0) > 0.8 and abs(RCO[v.index].z - eyez) < 0.03: cand.append(RCO[v.index].copy())
RSIGN = 1 if HR.data.bones["upperarm01.R"].head_local.x > 0 else -1
ear_rest = max(cand, key=lambda c: c.x * RSIGN)     # outermost point on his right side at eye height
log("right side sign", RSIGN, "ear rest", tuple(round(x, 3) for x in ear_rest))
HEAD_REST_INV = HR.data.bones["head"].matrix_local.inverted()
EAR_L = HEAD_REST_INV @ ear_rest
def ear_w(f): fs(f); return W(HR, "head") @ EAR_L
HAIR = [c for c in HR.children if c.type == 'MESH' and "short02" in c.name][0]
HEADP = ("head", "neck", "jaw", "eye", "orbic", "oris", "levator", "risor", "temporal", "tongue", "special")
def head_bvh(f):
    fs(f)
    if "hb" not in _DOM:
        d = dom_bones(HB, HR); _DOM["hb"] = [d.get(i) for i in range(len(HB.data.vertices))]
    dl = _DOM["hb"]; n0 = len(dl)
    upd(); dg = bpy.context.evaluated_depsgraph_get(); e = HB.evaluated_get(dg); me = e.to_mesh(); Mw = HB.matrix_world
    polys = [p.vertices[:] for p in me.polygons if all((dl[i % n0] or "").startswith(HEADP) for i in p.vertices)]
    b = BVHTree.FromPolygons([Mw @ v.co for v in me.vertices], polys); e.to_mesh_clear(); return b
def finger_clear(f, objs):
    fs(f); bvs = [head_bvh(f)] + [bvh_eval(o) for o in objs if o is not HB]; best = 9.0
    for b in HR.pose.bones:
        if b.name.startswith(("finger", "metacarpal")) and b.name.endswith(".R"):
            p = HR.matrix_world @ b.tail
            for bv in bvs:
                h = bv.find_nearest(p)
                if h[0] is not None: best = min(best, h[3])
    return best
# ================================================================== the officer (stands, turned toward the hero)
OP = Vector((OPOS.x / OSC, OPOS.y / OSC))
for f, fl, dz in ((1, 2.0, 0.0), (120, 3.0, 0.0), (463, 2.0, 0.0), (620, -3.0, 0.004), (872, -2.0, 0.003), (1073, -5.0, 0.006),
                  (1415, -4.0, 0.005), (1629, -4.0, 0.005), (1829, -2.0, 0.002), (END, -2.0, 0.002)):
    stand(HO, CO, f, OP, OYAW, flex=fl, dz=dz)
for f in list(range(1, END + 1, 20)) + [END]:
    key_spine(CO, f, flex=pchip([(1, 3), (463, 3), (680, -4), (1073, -7), (1600, -6), (END, -4)])(f) + breath(f + 60, 240, 0.9))
# head: looks at the hero's face (computed), with a 'no' head shake at f40-115
def officer_aim(f):
    fs(f); eo = (Wh(OR_, "eye.L") + Wh(OR_, "eye.R")) / 2; eh = (Wh(HR, "eye.L") + Wh(HR, "eye.R")) / 2
    d = eh - eo; yaw_w = math.degrees(math.atan2(d.x, -d.y)); pitch = -math.degrees(math.atan2(d.z, d.to_2d().length))
    rel = yaw_w - OYAW
    while rel > 180: rel -= 360
    while rel < -180: rel += 360
    return rel, pitch
for f in list(range(1, END + 1, 6)) + [END]:
    ry, rp = officer_aim(f)
    shake = 14 * math.sin((f - 40) * 2 * math.pi / 26) * (1.0 if 40 <= f <= 118 else 0.0) * min(1, (f - 40) / 8, (118 - f) / 8 if f <= 118 else 0)
    k_ = 0.75 if not (1829 <= f) else 0.6
    key_head(CO, f, -(ry * k_) + shake, rp * 0.8 + 0.6 * math.sin(f / 29.0))
for f, sm, br, jaw, sq in ((1, 0.0, -0.3, 0.0, 0.1), (60, -0.2, -0.7, 0.0, 0.2), (130, -0.1, -0.3, 0.0, 0.1), (463, 0.0, 0.2, 0.0, 0.0),
                           (560, -0.1, 1.0, 0.35, 0.0), (700, 0.0, 0.9, 0.25, 0.0), (960, -0.1, 1.0, 0.40, 0.0), (1073, 0.0, 0.6, 0.1, 0.0),
                           (1200, -0.2, -0.2, 0.0, 0.0), (1415, 0.0, 0.1, 0.0, 0.0), (1700, 0.2, 0.3, 0.0, 0.0), (1900, 0.45, 0.3, 0.0, 0.1),
                           (END, 0.5, 0.3, 0.0, 0.1)):
    key_face(OR_, f, smile=sm, brow=br, jaw=jaw, squint=sq)
for i, f in enumerate(range(1290, 1405, 8)):     # the officer speaks to him (jaw moves), he can't hear well
    key_face(OR_, f, smile=-0.05, brow=0.35, jaw=(0.55 if i % 2 == 0 else 0.10) + 0.05 * math.sin(i), squint=0.0)
key_face(OR_, 1412, smile=0.0, brow=0.2, jaw=0.0, squint=0.0)
blinks(OR_, [80, 230, 410, 620, 800, 1010, 1180, 1390, 1580, 1740, 1920, 2050])
saccades(CO, 1, END, every=44, amp=(1.0, 1.6), seed=11)
for i, f in enumerate([1, 70, 150, 300, 463, 600, 760, 900, 1073, 1250, 1415, 1600, 1750, 1900, END]):
    for s in "LR":
        hang(HO, OR_, OBD, OCL, s, f, yaw=OYAW, fwd=0.05 + 0.015 * math.sin(i * 1.3 + (s == "L")), drop=0.50)

# ================================================================== x-ray, tumour, hormone stream, vertebrae
XR = [(1, 0.0), (172, 0.0), (210, 1.0), (432, 1.0), (472, 0.0), (1076, 0.0), (1104, 1.0), (1178, 1.0), (1204, 0.0),
      (1402, 0.0), (1428, 1.0), (1478, 1.0), (1504, 0.0), (END, 0.0)]
for mname in HR["xr_mats"]:
    m = bpy.data.materials[mname]; v = m.node_tree.nodes["XR"].outputs[0]
    for f, x in XR:
        v.default_value = x; v.keyframe_insert("default_value", frame=f)
def vis(obj, f, show):
    obj.hide_render = not show; obj.hide_viewport = not show
    obj.keyframe_insert("hide_render", frame=f); obj.keyframe_insert("hide_viewport", frame=f)
    set_interp(obj, 'CONSTANT', "hide")
for o in (BRAIN, TUM):
    vis(o, 1, False); vis(o, 176, True); vis(o, 470, False); vis(o, 1406, True); vis(o, 1502, False)
for o in VERTS:
    vis(o, 1, False); vis(o, 1086, True); vis(o, 1180, False)
# tumour: a small pituitary that swells into a lumpy glowing tumour; removed (shrinks, dims to pink) at 1428-1478
for f, r_ in ((1, 0.35), (200, 0.35), (320, 1.0), (1430, 1.0), (1475, 0.30), (END, 0.30)):
    TUM.scale = (TUM.scale.x if f == 1 else TUM.scale.x,) * 3
TS0 = TUM.scale.x
for f, r_ in ((1, 0.35), (200, 0.35), (320, 1.0), (1400, 1.0), (1425, 1.7), (1445, 1.7), (1480, 0.25), (END, 0.25)):
    TUM.scale = (TS0 * r_,) * 3; TUM.keyframe_insert("scale", frame=f)
pt = TUM.data.materials[0].node_tree.nodes["Principled BSDF"]
for f, e_, col in ((1, 0.5, (1.0, 0.5, 0.6)), (200, 0.5, (1.0, 0.5, 0.6)), (300, 4.0, (1.0, 0.25, 0.02)), (330, 2.5, (1.0, 0.25, 0.02)),
                   (360, 4.5, (1.0, 0.25, 0.02)), (400, 2.5, (1.0, 0.25, 0.02)), (440, 4.0, (1.0, 0.25, 0.02)),
                   (1430, 7.0, (1.0, 0.25, 0.02)), (1448, 7.0, (1.0, 0.25, 0.02)), (1480, 0.4, (1.0, 0.5, 0.6)), (END, 0.4, (1.0, 0.5, 0.6))):
    pt.inputs["Emission Strength"].default_value = e_; pt.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    pt.inputs["Emission Color"].default_value = (*col, 1); pt.inputs["Emission Color"].keyframe_insert("default_value", frame=f)
    pt.inputs["Base Color"].default_value = (*col, 1); pt.inputs["Base Color"].keyframe_insert("default_value", frame=f)
# hormone stream: glowing beads from the pituitary down the neck and spine into the arms and legs (335-465)
M_HORM = bpy.data.materials.new("M_Hormone"); M_HORM.use_nodes = True
pn = M_HORM.node_tree.nodes["Principled BSDF"]; pn.inputs["Base Color"].default_value = (0.6, 1.0, 0.15, 1)
pn.inputs["Emission Color"].default_value = (0.55, 1.0, 0.12, 1); pn.inputs["Emission Strength"].default_value = 9.0
fs(380)
def wp(b, end="head"): return Wh(HR, b) if end == "head" else Wt(HR, b)
trunk = [TUM.matrix_world.translation.copy(), wp("neck03"), wp("neck02"), wp("neck01"), wp("spine01"), wp("spine02"), wp("spine03")]
paths = []
for s in "LR":
    paths.append(trunk[:5] + [wp("clavicle." + s, "tail"), wp("upperarm01." + s), wp("lowerarm01." + s), wp("wrist." + s), wp("finger3-1." + s)])
    paths.append(trunk + [wp("spine04"), wp("spine05"), wp("upperleg01." + s), wp("lowerleg01." + s), wp("foot." + s)])
paths.append(trunk + [wp("spine04")])
paths.append([TUM.matrix_world.translation.copy(), wp("neck03"), wp("neck01"), wp("spine01"), wp("spine02")])
def path_fn(pts):
    L = [0.0]
    for a_, b_ in zip(pts, pts[1:]): L.append(L[-1] + (b_ - a_).length)
    tot = L[-1]
    def at(u):
        d = u * tot
        for i in range(len(pts) - 1):
            if d <= L[i + 1] or i == len(pts) - 2:
                t = 0 if L[i + 1] == L[i] else (d - L[i]) / (L[i + 1] - L[i]); return pts[i].lerp(pts[i + 1], max(0, min(1, t)))
    return at
HORM = []
k = 0
for pi_, pts in enumerate(paths):
    at = path_fn(pts)
    for j in range(6):
        t0 = 340 + j * 14 + pi_ * 2; t1 = t0 + 78
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0065, segments=12, ring_count=8)
        o = bpy.context.active_object; o.name = "Hormone%02d" % k; k += 1; o.data.materials.append(M_HORM); bpy.ops.object.shade_smooth()
        o.visible_shadow = False
        for f in range(t0, t1 + 1, 2):
            u = smoothstep((f - t0) / (t1 - t0)) * 0.85 + 0.15 * (f - t0) / (t1 - t0)
            o.location = at(u); o.keyframe_insert("location", frame=f)
            sz = min(1.0, (f - t0) / 6.0, max(0.0, (t1 - f) / 10.0)) * (1.0 + 0.25 * math.sin(f / 3.0 + k))
            o.scale = (max(sz, 0.001),) * 3; o.keyframe_insert("scale", frame=f)
        vis(o, 1, False); vis(o, t0, True); vis(o, t1 + 1, False)
        HORM.append(o)
log("hormone beads", len(HORM))
# room lights dim a little while the x-ray glows (the hero's glow reads), back up after
LK, LF, LR_, LW, LS = O["L_Key"], O["L_Fill"], O["L_Rim"], O["L_Window"], O["L_Sun"]
E0 = {o.name: o.data.energy for o in (LK, LF, LR_)}
for o in (LK, LF, LR_):
    for f, x in XR:
        o.data.energy = E0[o.name] * (1.0 - 0.45 * x); o.data.keyframe_insert("energy", frame=f)

# ================================================================== seasons through the window (872-1073), dusk at the end (1629-1829)
LEAF = bpy.data.materials["M_Leaves"].node_tree.nodes["Principled BSDF"].inputs["Base Color"]
for f, c in ((1, (0.10, 0.45, 0.06)), (880, (0.10, 0.45, 0.06)), (930, (0.85, 0.32, 0.02)), (980, (0.85, 0.88, 0.95)),
             (1030, (0.35, 0.65, 0.10)), (1073, (0.12, 0.48, 0.06)), (END, (0.12, 0.48, 0.06))):
    LEAF.default_value = (*c, 1); LEAF.keyframe_insert("default_value", frame=f)
ramp = bpy.data.worlds[0].node_tree.nodes["SkyRamp"].color_ramp
for f, c0, c1 in ((1, (0.65, 0.85, 1.0), (0.10, 0.40, 0.95)), (1640, (0.65, 0.85, 1.0), (0.10, 0.40, 0.95)),
                  (1820, (1.0, 0.50, 0.22), (0.22, 0.12, 0.45)), (END, (1.0, 0.48, 0.20), (0.20, 0.10, 0.42))):
    ramp.elements[0].color = (*c0, 1); ramp.elements[0].keyframe_insert("color", frame=f)
    ramp.elements[1].color = (*c1, 1); ramp.elements[1].keyframe_insert("color", frame=f)
for o, cA, cB in ((LW, (1.0, 0.92, 0.80), (1.0, 0.50, 0.22)), (LS, (1.0, 0.88, 0.70), (1.0, 0.45, 0.20)), (LK, (1.0, 0.90, 0.78), (1.0, 0.72, 0.50))):
    for f, c in ((1, cA), (1640, cA), (1820, cB), (END, cB)):
        o.data.color = c; o.data.keyframe_insert("color", frame=f)

# ================================================================== the photo on the wall appears off-camera (set in the camera pass)
PHOTO = [O["RM_Photo"], O["RM_PhotoFrame"]]

# ================================================================== camera: ONE camera, PCHIP path, level horizon
cam_d = bpy.data.cameras.new("CAM_Film"); CAM = bpy.data.objects.new("CAM_Film", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
AIM = bpy.data.objects.new("CAM_Film_Aim", None); sc.collection.objects.link(AIM)
cam_d.sensor_fit = 'AUTO'; cam_d.sensor_width = 36; cam_d.clip_start = 0.02; cam_d.clip_end = 60
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 16.0
CAM.rotation_mode = 'QUATERNION'
def P(*v): return Vector(v)
def eyes(f): fs(f); return (Wh(HR, "eye.L") + Wh(HR, "eye.R")) / 2
def oeyes(f): fs(f); return (Wh(OR_, "eye.L") + Wh(OR_, "eye.R")) / 2
def headc(f): fs(f); return Wh(HR, "head").lerp(Wt(HR, "head"), 0.35)
def chestc(f): return chest_point(f)
def hands_c(f): fs(f); return (Wh(HR, "wrist.L") + Wh(HR, "wrist.R")) / 2
def side_head(f, dx, dy, dz): fs(f); s_ = HR.scale.x; return headc(f) + Vector((dx, dy, dz)) * s_
KEYS = [
    # 1-145: wide on both men, the rod, door edge and the logo plaque; then down to his eye level
    (1,    lambda: P(0.50, -3.05, 1.50), lambda: P(0.36, 0.20, 1.15), 27),
    (60,   lambda: P(0.42, -2.65, 1.40), lambda: P(0.33, 0.20, 1.12), 28),
    (118,  lambda: P(0.30, -2.05, 1.30), lambda: P(0.30, 0.20, 1.10), 28),
    # 145-335: close on his head from his right-front; the x-ray reveals the brain and the swelling gland
    (175,  lambda: side_head(175, -0.42, -0.95, 0.02), lambda: headc(175), 36),
    (235,  lambda: side_head(235, -0.36, -0.62, 0.03), lambda: headc(235), 42),
    (300,  lambda: side_head(300, -0.30, -0.46, 0.01), lambda: headc(300) + P(0, 0.01, -0.03), 46),
    (335,  lambda: side_head(335, -0.30, -0.52, -0.02), lambda: headc(335) + P(0, 0.01, -0.06), 44),
    # 335-463: pull back down his body with the hormone stream (face stays in frame)
    (385,  lambda: P(-0.30, -1.25, 1.05), lambda: P(0.0, 0.05, 0.86), 33),
    (440,  lambda: P(-0.22, -1.85, 0.95), lambda: P(0.0, 0.05, 0.78), 30),
    # 463-679: wide: he grows next to the rod, the door and the officer
    (520,  lambda: P(-0.30, -2.90, 1.00), lambda: P(0.38, 0.15, 0.98), 26),
    (640,  lambda: P(0.80, -2.55, 1.30), lambda: P(0.42, 0.15, 1.12), 26),
    # 679-872: his hands growing, his face above them
    (700,  lambda: P(0.10, -1.55, 1.20), lambda: hands_c(700).lerp(eyes(700), 0.45), 32),
    (780,  lambda: hands_c(780) + P(0.18, -0.85, 0.42), lambda: hands_c(780).lerp(eyes(780), 0.62), 40),
    (850,  lambda: hands_c(850) + P(0.10, -0.82, 0.45), lambda: hands_c(850).lerp(eyes(850), 0.66), 40),
    # 872-1073: low wide orbit: he shoots up past the door, the officer looks up, seasons in the window
    (920,  lambda: P(-0.55, -2.50, 0.95), lambda: P(0.12, 0.10, 1.25), 25),
    (1000, lambda: P(0.10, -3.05, 0.90), lambda: P(0.25, 0.10, 1.40), 23),
    (1060, lambda: P(0.55, -2.95, 1.05), lambda: P(0.20, 0.10, 1.45), 23),
    # 1073-1196: front medium, x-ray of the curving spine as he stoops
    (1110, lambda: P(0.85, -1.75, 1.50), lambda: P(0.0, 0.05, 1.32), 27),
    (1175, lambda: P(0.80, -1.65, 1.58), lambda: P(0.0, 0.05, 1.38), 28),
    # 1196-1281: close on his face, the focus drifts off (his vision blurs)
    (1215, lambda: eyes(1215) + P(0.05, -0.75, -0.02), lambda: eyes(1215) + P(0, 0, -0.03), 42),
    (1270, lambda: eyes(1270) + P(-0.06, -0.68, -0.03), lambda: eyes(1270) + P(0, 0, -0.04), 44),
    # 1281-1415: round to his right ear, he cups it
    # 1281-1415: the officer talks to him; he turns his ear toward the voice, straining to hear (both faces in frame)
    (1330, lambda: eyes(1330).lerp(oeyes(1330), 0.45) + P(0.05, -2.25, -0.10), lambda: eyes(1330).lerp(oeyes(1330), 0.5) + P(0, 0, -0.16), 27),
    (1400, lambda: eyes(1400).lerp(oeyes(1400), 0.45) + P(-0.05, -2.10, -0.10), lambda: eyes(1400).lerp(oeyes(1400), 0.5) + P(0, 0, -0.16), 28),
    # 1415-1496: x-ray head: the tumour is taken out (shrinks away)
    (1440, lambda: side_head(1440, -0.36, -0.46, 0.08), lambda: headc(1440) + P(0, 0.0, -0.03), 44),
    (1490, lambda: side_head(1490, -0.40, -0.62, 0.08), lambda: headc(1490), 40),
    # 1496-1829: pull back to the wide: still growing, past the door top; officer beside him; dusk
    (1560, lambda: P(-0.40, -2.40, 1.80), lambda: P(-0.15, 0.15, 1.72), 25),
    (1640, lambda: P(-0.90, -3.00, 1.30), lambda: P(0.05, 0.15, 1.35), 23),
    (1740, lambda: P(1.10, -2.75, 1.10), lambda: P(0.40, 0.15, 1.45), 23),
    (1829, lambda: P(0.35, -2.45, 1.55), lambda: P(0.15, 0.20, 1.60), 25),
    # 1829-2083: down to the photo of his short young self, then up beside the giant he became; settle
    (1900, lambda: P(-0.40, -2.40, 1.84), lambda: P(-0.40, 0.40, 1.8), 25),
    (1960, lambda: P(-0.40, -2.32, 1.85), lambda: P(-0.40, 0.40, 1.81), 25),
    (2030, lambda: P(-0.40, -2.25, 1.86), lambda: P(-0.40, 0.40, 1.82), 25),
    (END,  lambda: P(-0.40, -2.22, 1.86), lambda: P(-0.40, 0.40, 1.82), 25),
]
def look_q(p, a, up=Vector((0, 0, 1))):
    zc_ = (p - a).normalized(); yc = (up - zc_ * up.dot(zc_)); yc = yc.normalized() if yc.length > 1e-6 else Vector((0, 1, 0))
    xc = yc.cross(zc_); return Matrix((xc, yc, zc_)).transposed().to_quaternion()
ks = [(f, pf(), af(), l) for f, pf, af, l in KEYS]
fx = [pchip([(k_[0], k_[1][i]) for k_ in ks]) for i in range(3)]
ax = [pchip([(k_[0], k_[2][i]) for k_ in ks]) for i in range(3)]
fl = pchip([(k_[0], k_[3]) for k_ in ks])
FSTOP = pchip([(1, 16), (1205, 16), (1228, 2.4), (1268, 2.4), (1290, 16), (END, 16)])
prev = None
for f in range(1, END + 1):
    p = Vector([fx[i](f) for i in range(3)]); a_ = Vector([ax[i](f) for i in range(3)])
    q = look_q(p, a_)
    if prev is not None and prev.dot(q) < 0: q = -q
    prev = q
    CAM.location = p; CAM.rotation_quaternion = q; AIM.location = a_; cam_d.lens = fl(f)
    CAM.keyframe_insert("location", frame=f); CAM.keyframe_insert("rotation_quaternion", frame=f)
    AIM.keyframe_insert("location", frame=f); cam_d.keyframe_insert("lens", frame=f)
    if f % 3 == 1 or f == END:
        # focus on the hero's face; in the blur beat the focus slides away to 0.25 m
        fd = (p - eyes(f)).length
        if 1205 <= f <= 1290:
            u = pchip([(1205, 0), (1228, 1), (1268, 1), (1290, 0)])(f); fd = fd * (1 - u) + 0.22 * u
        cam_d.dof.focus_distance = fd; cam_d.dof.keyframe_insert("focus_distance", frame=f)
        cam_d.dof.aperture_fstop = FSTOP(f); cam_d.dof.keyframe_insert("aperture_fstop", frame=f)
set_interp(CAM, 'LINEAR'); set_interp(AIM, 'LINEAR'); set_interp(cam_d, 'LINEAR')
# a small catchlight riding with the camera so the eyes never read as black holes
cl = bpy.data.lights.new("Catch", 'AREA'); cl.energy = 3.0; cl.size = 0.25; cl.color = (1, 0.96, 0.92)
clo = bpy.data.objects.new("Catchlight", cl); sc.collection.objects.link(clo); clo.parent = CAM; clo.location = (0.0, 0.10, 0.0)
for f in list(range(1, END + 1, 6)) + [END]:
    fs(f); d_ = (CAM.matrix_world.translation - eyes(f)).length
    cl.energy = max(0.1, min(2.5, 2.5 * (d_ / 0.9) ** 2)); cl.keyframe_insert("energy", frame=f)

# ---- the photo pops in only where the camera cannot see it
def in_view(obj, f):
    fs(f); from bpy_extras.object_utils import world_to_camera_view
    for c in obj.bound_box:
        v = world_to_camera_view(sc, CAM, obj.matrix_world @ Vector(c))
        if -0.05 <= v.x <= 1.05 and -0.05 <= v.y <= 1.05 and v.z > 0: return True
    return False
show_f = None
for f in range(1300, 1820):
    if all(not in_view(o, f) for o in PHOTO) and all(not in_view(o, f + 1) for o in PHOTO):
        show_f = f + 1; break
log("photo appears at", show_f)
for o in PHOTO:
    vis(o, 1, False); vis(o, show_f, True)

# ================================================================== VO, output
sc.frame_start, sc.frame_end = 1, END
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor; strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", VO, 1, 1)
sc.render.filepath = "//render/DwarfGiant_v009_####.png"; sc.render.image_settings.file_format = 'PNG'
for o in O:
    for m in getattr(o, "modifiers", []):
        if m.type == 'SUBSURF': m.show_viewport = False
log("quat flips fixed", quat_continuity(HR), quat_continuity(OR_))
sc.frame_set(1)
open(os.path.join(os.path.dirname(OUT), "animate_log.txt"), "w").write("\n".join(LOG))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("ANIM_DONE", OUT)
