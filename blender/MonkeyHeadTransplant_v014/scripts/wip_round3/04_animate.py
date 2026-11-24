"""v014 animation, built to the v013 VO timing (synced frames 1-1656, 60 fps). One surgeon, one camera, no cuts.
blender -b layout.blend --python 04_animate.py -- film.blend
Beats (synced): 1 removed the head 1 | 2 attached it 205 | 3 joining the tissue 379 | 4 survived 607 | 5 see and hear 817 |
6 spinal cord 949 | 7 couldn't move 1093 | 8 technically a success 1267 | 9 only lived a few more days 1447 | end 1656"""
import bpy, sys, os, math, json, bmesh
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "../../pipeline")
exec(open(os.path.join(PIPE, "anim_lib.py")).read())
exec(open(os.path.join(PIPE, "hand_poses.py")).read())
D = bpy.data; sc = bpy.context.scene
L = json.load(open(os.path.join(os.path.dirname(OUT), "layout.json")))
sc.frame_start, sc.frame_end = 1, 1656; sc.render.fps = 60; sc.render.fps_base = 1.0
V = lambda *a: Vector(a)
def ss(a, b, x):                        # smoothstep between frames a..b
    if x <= a: return 0.0
    if x >= b: return 1.0
    t = (x - a) / (b - a); return t * t * (3 - 2 * t)
def fc_all(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    a = ad.action
    try: return list(a.fcurves)
    except Exception: return [fc for l in a.layers for s_ in l.strips for cb in s_.channelbags for fc in cb.fcurves]
def interp(idb, kind='BEZIER'):
    for fc in fc_all(idb):
        for k in fc.keyframe_points: k.interpolation = kind
def key_vis(o, f, visible):
    o.hide_render = o.hide_viewport = not visible
    o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
# ======================================================================== the head (donor A -> recipient B)
head = D.objects["MK_Head"]; head.rotation_mode = 'QUATERNION'
MA = D.objects["MonkeyRootA"].matrix_world.copy(); MB = D.objects["MonkeyRootB"].matrix_world.copy()
F_GRIP, F_LIFT0, F_LIFT1, F_LAND0, F_SEAT, F_REL = 85, 120, 175, 290, 330, 352
def head_M(f):
    """world matrix of the donor head at frame f: on A, lifted, carried in an arc, lowered onto B's neck"""
    pA, pB = MA.translation, MB.translation
    q = MA.to_quaternion()
    if f <= F_LIFT0: return MA.copy()
    if f >= F_SEAT: return MB.copy()
    if f <= F_LIFT1:                                  # straight up off the neck (7 cm), tiny forward tilt
        u = ss(F_LIFT0, F_LIFT1, f); p = pA + V(0, 0, 0.03 * u); tilt = 2 * u
    elif f <= F_LAND0:                                # carried across in an arc (peak +12 cm)
        u = ss(F_LIFT1, F_LAND0, f)
        p = pA.lerp(pB, u) + V(0, 0, 0.03 + 0.015 * math.sin(math.pi * u)); tilt = 2 - 1.0 * math.sin(math.pi * u)
    else:                                             # lowered straight down onto the neck, settles
        u = ss(F_LAND0, F_SEAT, f); p = pB + V(0, 0, 0.03 * (1 - u)); tilt = 2 * (1 - u)
    R_ = Quaternion((1, 0, 0), math.radians(tilt)) @ q
    return Matrix.Translation(p) @ R_.to_matrix().to_4x4()
for f in range(1, 1657):
    if f in (1,) or F_LIFT0 - 1 <= f <= F_SEAT + 1 or f == 1656:
        head.matrix_world = head_M(f)
        head.keyframe_insert("location", frame=f); head.keyframe_insert("rotation_quaternion", frame=f)
interp(head, 'LINEAR')
# neck caps hidden on A's body / the head stump only reads while it is separated (no gore: clean pink cap, gauze ring)
# ======================================================================== surgeon
rig = D.objects["Surgeon"]; R = Rig(rig); Hm = Human(R)
FOOT_Y = 0.80; ROOT_Y = 0.77
for _s in "LR":                       # wrist range: flex +-75, twist +-50, side +-45 (anatomical; the +-60/35 clamp flipped the carry grip)
    _c = rig.pose.bones["wrist." + _s].constraints.get("HandLimit")
    if _c: _c.min_x, _c.max_x, _c.min_z, _c.max_z = math.radians(-75), math.radians(75), math.radians(-45), math.radians(45)
TZ = 0.0
dg = bpy.context.evaluated_depsgraph_get()
def ray_down_z(x, y, objs):
    best = None
    for o in objs:
        inv = o.matrix_world.inverted(); oe = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ok, loc, n, i = oe.ray_cast(inv @ V(x, y, 3), (inv.to_3x3() @ V(0, 0, -1)).normalized())
        if ok:
            z = (o.matrix_world @ loc).z; best = z if best is None else max(best, z)
    return best
TABLES = [D.objects["T1_Pad"], D.objects["T2_Pad"]]
BACK_TOP = L["B"]["back_top"]; BACK_Y = L["B"]["back_y"] + 0.025; TOWEL_Z = L["towel_z"]
EDGE_Z = TOWEL_Z
print("TABLE EDGE z", EDGE_Z)
# body keys: frame -> (hip x, root flex, spine flex, twist, head pitch, head yaw, knee dip)
BODY = [
    (1,    -0.07, 12, 8, -10, 22, -12, 0.02),
    (85,   -0.08, 17, 10, -12, 18, -10, 0.03),
    (150,  -0.06, 21, 12, -9, 12, -8, 0.045),
    (245,   0.02, 21, 12, 0, 12, 0, 0.045),
    (315,   0.10, 17, 10, 9, 18, 8, 0.03),
    (370,   0.11, 15, 9, 11, 20, 10, 0.03),
    (425,   0.13, 18, 11, 16, 20, 14, 0.04),
    (470,   0.145, 19, 11, 15, 12, 12, 0.04),
    (540,   0.15, 20, 12, 15, 10, 9, 0.045),
    (600,   0.155, 21, 12, 16, 12, 12, 0.045),
    (640,   0.13, 18, 11, 16, 20, 14, 0.04),
    (720,   0.09, 10, 6, 8, 14, 8, 0.02),
    (817,   0.10, 14, 8, 7, 9, 5, 0.025),
    (900,   0.11, 15, 9, 9, 11, 8, 0.025),
    (960,   0.07, 7, 4, 5, 12, 6, 0.015),
    (1080,  0.07, 7, 4, 5, 12, 6, 0.015),
    (1130, -0.080, 13, 8, 9, 17, 8, 0.025),
    (1240, -0.080, 13, 8, 9, 18, 6, 0.025),
    (1300, -0.080, 11, 7, 14, 6, 34, 0.02),
    (1400, -0.080, 11, 7, 15, 5, 36, 0.02),
    (1470, -0.090, 12, 7, 10, 16, 10, 0.02),
    (1560, -0.090, 13, 8, 9, 22, 7, 0.025),
    (1656, -0.090, 14, 8, 8, 26, 5, 0.03),
]
rest_z = Hm.root_head.z
for (f, hx, rf, sf, tw, hp, hy, dip) in BODY:
    breath = 0.004 * math.sin(f * 2 * math.pi / 230.0)
    Hm.key_root(f, V(hx, ROOT_Y, rest_z - dip + breath), yaw=tw * 0.35, flex=rf, side=-hx * 20)
    Hm.key_spine(f, flex=sf, twist=tw * 0.65, side=hx * 8, head=(hp, hy))
for s, x in (("L", 0.13), ("R", -0.13)):
    Hm.key_foot(s, 1, Vector((x, FOOT_Y)), 6 if s == "L" else -6)
# elbows: poles out to the sides and a little back, so forearms come in from the sides, never across the monkey
def key_pole(s, f, P):
    n = "Pole_elbow." + s; pb = R.PB[n]
    pb.location = R.rest(n).to_3x3().inverted() @ (P - R.BN[n].head_local); pb.keyframe_insert("location", frame=f, group=n)
for f, hx in ((1, -0.07), (245, 0.02), (330, 0.1), (1080, 0.08), (1130, -0.08), (1656, -0.09)):
    key_pole("L", f, V(hx + 0.85, 0.95, 1.05)); key_pole("R", f, V(hx - 0.85, 0.95, 1.05))
for f, P in ((432, V(0.95, 0.95, 1.05)), (452, V(1.00, 0.75, 0.85)), (612, V(1.00, 0.75, 0.85)), (640, V(0.95, 0.95, 1.05))):
    key_pole("L", f, P)            # stitching: elbow high and back, forearm comes over the shoulder from behind
sc.frame_set(1)
# ---------------------------------------------------------------- hand helpers
def ikM(s):          # current IK_hand armature-space matrix
    return R.PB["IK_hand." + s].matrix.copy()
def key_ik(s, f, M):
    R.key_world("IK_hand." + s, f, M)
def rest_hand(s, f, dx=0.0, dy=0.0):
    """idle contacts on flat tops: right palm on B's backrest rail (fingers along it), left palm on the instrument towel"""
    if s == "R":
        hx = body_hx(f)       # right arm hangs relaxed at his side, elbow slightly bent, palm toward the thigh
        place_hand(rig, s, f, V(hx - 0.27 - dx, ROOT_Y - 0.06 + dy, 0.86), V(1, 0.15, 0).normalized(), V(-0.05, -0.25, -1).normalized(), skin=0.0)
        apply_pose(rig, s, "relaxed", f); return
    else:
        hx = body_hx(f)       # left arm hangs relaxed at his side, elbow slightly bent, palm toward the thigh
        place_hand(rig, s, f, V(hx + 0.27 + dx, ROOT_Y - 0.06 + dy, 0.86), V(-1, 0.15, 0).normalized(), V(0.05, -0.25, -1).normalized(), skin=0.0)
        apply_pose(rig, s, "relaxed", f); return
def body_hx(f):
    ks = [b for b in BODY]
    for a_, b_ in zip(ks, ks[1:]):
        if a_[0] <= f <= b_[0]:
            u = (f - a_[0]) / (b_[0] - a_[0]); return a_[1] + (b_[1] - a_[1]) * u
    return ks[-1][1]
# ---------------------------------------------------------------- grip points on the donor head (head-local), from ray casts
hd_bvh_local = BVHTree.FromObject(head, bpy.context.evaluated_depsgraph_get())
HC_local = sum((V(*c) for c in head.bound_box), Vector()) / 8
def head_contact(sx):
    d = (V(1.0, 0.25, 0.15) if sx > 0 else V(-1.0, 0.25, 0.15)).normalized()
    # direction expressed in head-local axes (head-local == world rotation of root A)
    Rinv = MA.to_3x3().inverted(); dl = (Rinv @ d).normalized()
    hit = hd_bvh_local.ray_cast(HC_local + dl * 0.3, -dl, 0.5)
    return hit[0], hit[1].normalized()
GRIP = {}
for s, sx in (("L", 1), ("R", -1)):
    p, n = head_contact(sx)
    GRIP[s] = (p, n)
    print("GRIP", s, tuple(round(v, 3) for v in (MA @ p)), tuple(round(v, 2) for v in (MA.to_3x3() @ n)))
def grip_world(s, f, out=0.0, up=0.0):
    M = head_M(f); p, n = GRIP[s]
    pw = M @ p; nw = (M.to_3x3() @ n).normalized()
    fd = V(0, 0.05, 1.0); fd = (fd - nw * fd.dot(nw)).normalized()
    return pw + nw * out + V(0, 0, up), -nw, fd
def place_grip(s, f, out=0.0, up=0.0, skin=0.013):
    pw, pn, fd = grip_world(s, f, out, up)
    place_hand(rig, s, f, pw, pn, fd, skin=skin)
# ---- beat 1-2: approach, grip, lift, carry, seat, release
HBV_W = None
def head_pen(s, f):
    """deepest finger/hand bone point inside the head (m) at frame f"""
    sc.frame_set(f); M = head.matrix_world; inv = M.inverted(); worst = 0.0
    for bn in [b.name for b in rig.data.bones if b.name.endswith("." + s) and b.name.startswith(("finger", "metacarpal", "wrist"))]:
        pb = rig.pose.bones[bn]
        for u in (0.0, 0.5, 1.0):
            p = inv @ (rig.matrix_world @ pb.head.lerp(pb.tail, u))
            loc, nrm, idx, dist = hd_bvh_local.find_nearest(p)
            if loc is None or dist > 0.06: continue
            if (p - loc).dot(nrm) < 0 and hd_bvh_local.ray_cast(p, nrm, 0.08)[0] is not None:
                if dist > worst: WORST_BONE[s] = (bn, round(dist * 1000, 1))
                worst = max(worst, dist)
            if bn.startswith("finger") and (p - loc).dot(nrm) >= 0 and dist < 0.004: worst = max(worst, 0.004 - dist)
    return worst
GSKIN = {}
WORST_BONE = {}
for s in "LR":
    sk = 0.013
    for it in range(20):
        place_grip(s, F_GRIP, skin=sk); apply_pose(rig, s, "shield", F_GRIP)
        pen = head_pen(s, F_GRIP)
        if pen < 0.0015: break
        sk += max(0.002, pen * 0.7)
    sk = min(sk, 0.03); print("WORST", s, WORST_BONE.get(s)); GSKIN[s] = sk + 0.008; print("GRIP SKIN", s, round(sk, 3), "pen mm", round(pen * 1000, 1))
for s in "LR":
    sk = GSKIN[s]
    place_grip(s, 1, out=0.15, up=0.0, skin=sk); apply_pose(rig, s, "relaxed", 1)
    place_grip(s, 45, out=0.07, up=0.01, skin=sk); apply_pose(rig, s, "open_alarm", 45, amount=0.6)
    place_grip(s, F_GRIP, skin=sk); apply_pose(rig, s, "shield", F_GRIP)
    for f in range(F_GRIP + 2, F_REL, 2):
        sc.frame_set(f); place_grip(s, f, skin=sk)
    place_grip(s, F_REL, skin=sk); apply_pose(rig, s, "shield", F_REL)
    place_grip(s, F_REL + 20, out=0.07, up=0.02, skin=sk); apply_pose(rig, s, "open_alarm", F_REL + 20, amount=0.6)
    place_grip(s, F_REL + 34, out=0.12, up=0.10, skin=sk); apply_pose(rig, s, "relaxed", F_REL + 34)
# ---- right hand: down to the table edge and stays there (idle shifts)
place_hand(rig, "R", 400, V(-0.30, 0.64, 1.18), V(1, 0, 0), V(0, -0.3, -1).normalized(), skin=0.0); apply_pose(rig, "R", "relaxed", 400)
for f, dx in ((418, 0.0), (470, 0.0), (540, 0.005), (600, 0.0), (700, 0.01), (950, 0.0), (1250, 0.015), (1656, 0.0)):
    rest_hand("R", f, dx=dx)
# ======================================================================== needle holder: pick up, stitch, put down
nh = D.objects["NeedleHolder"]; NH_REST = Matrix(L["nh_rest"])
shank = D.objects["NH_Shank1"]
F_NHG, F_NHR = 430, 700
grip_pt = NH_REST @ V(0.0, -0.066, 0.0)
sc.frame_set(397)
place_hand(rig, "L", 397, grip_pt + V(-0.02, 0.06, 0.20), V(0, 0, -1), (NH_REST.to_3x3() @ V(0, 1, 0)).normalized(), skin=0.03)
def key_fingers(f, rots):
    for n, q in rots.items():
        pb = R.PB[n]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
# ---- hand-posed instrument grip: thumb and ring finger in the rings, index along the shaft, middle and little curled
_P = {k: _pose_rots(rig, "L", k) for k in ("relaxed", "point", "wrap_grip", "power_fist", "pinch")}
GRIP_FINGERS = dict(_P["relaxed"])
for j in (1, 2, 3):
    GRIP_FINGERS["finger2-%d.L" % j] = _P["point"]["finger2-%d.L" % j].slerp(_P["relaxed"]["finger2-%d.L" % j], 0.3)
    GRIP_FINGERS["finger3-%d.L" % j] = _P["wrap_grip"]["finger3-%d.L" % j]
    GRIP_FINGERS["finger4-%d.L" % j] = _P["wrap_grip"]["finger4-%d.L" % j]
    GRIP_FINGERS["finger5-%d.L" % j] = _P["power_fist"]["finger5-%d.L" % j]
    GRIP_FINGERS["finger1-%d.L" % j] = _P["pinch"]["finger1-%d.L" % j]
key_fingers(F_NHG, GRIP_FINGERS); sc.frame_set(F_NHG)
W0 = rig.matrix_world @ R.PB["wrist.L"].matrix
def _bp(n, u):
    pb = R.PB[n]; return rig.matrix_world @ pb.head.lerp(pb.tail, u)
th = _bp("finger1-3.L", 0.5); rf = _bp("finger4-3.L", 0.45)
idx_d = (_bp("finger2-3.L", 1.0) - _bp("finger2-1.L", 0.0)).normalized()
X = (rf - th).normalized(); Y = (idx_d - X * idx_d.dot(X)).normalized(); Z = X.cross(Y)
Hh = _Hand(rig, "L"); _wr, _d, _n, _a = Hh.frame(); nW = (rig.matrix_world.to_3x3() @ _n).normalized()
if Z.dot(nW) > 0: X, Z = -X, -Z                       # tool's up side faces the back of the hand (palm on top of it)
Mt = Matrix((X, Y, Z)).transposed().to_4x4(); Mt.translation = (th + rf) / 2 + Y * 0.086
TOOL_IN_WRIST = W0.inverted() @ Mt
print("RING GRIP thumb-ring finger gap mm", round((rf - th).length * 1000, 1))
WR_DES = NH_REST @ TOOL_IN_WRIST.inverted()
M_ = rig.matrix_world.inverted() @ WR_DES
for it in range(8):
    key_ik("L", F_NHG, M_); sc.frame_set(F_NHG)
    err = WR_DES.translation - (rig.matrix_world @ R.PB["wrist.L"].matrix).translation
    if err.length < 0.0005: break
    M_ = Matrix.Translation(err) @ M_
print("NH pick-up wrist error mm", round(err.length * 1000, 2))
key_ik("L", 408, Matrix.Translation(V(0, 0, 0.08)) @ M_); key_fingers(408, GRIP_FINGERS)
sc.frame_set(F_NHG)
GRIP_IK = ikM("L")
def key_fingers(f, rots):
    for n, q in rots.items():
        pb = R.PB[n]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
co = nh.constraints.new('CHILD_OF'); co.name = "HeldBy"; co.target = rig; co.subtarget = "wrist.L"
sc.frame_set(F_NHG); bpy.context.view_layer.update()
WR_G = rig.matrix_world @ R.PB["wrist.L"].matrix
co.inverse_matrix = WR_G.inverted()
nh.matrix_world = NH_REST
co.influence = 0.0; co.keyframe_insert("influence", frame=F_NHG - 1)
co.influence = 1.0; co.keyframe_insert("influence", frame=F_NHG)
co.influence = 1.0; co.keyframe_insert("influence", frame=F_NHR - 1)
co.influence = 0.0; co.keyframe_insert("influence", frame=F_NHR)
for fc in fc_all(nh):
    for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
TIP_L = V(0.0, 0.041, -0.006)                         # needle point in holder space (jaw tip + needle)
HOLD_IN_WRIST = WR_G.inverted() @ NH_REST            # holder pose in wrist space while held
# seam ring on B (world), stitch points on the +x side (seen from the camera at front-right)
bodyB = D.objects["MK_BodyB"]
def bvh_world(o):
    dg_ = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg_); me_ = oe.to_mesh()
    b = BVHTree.FromPolygons([o.matrix_world @ v.co for v in me_.vertices], [p.vertices[:] for p in me_.polygons]); oe.to_mesh_clear(); return b
sc.frame_set(F_SEAT + 5)
BV_B = bvh_world(bodyB); BV_H = bvh_world(head)
NC = V(*L["neck_c"]); NN = V(*L["neck_n"])
u_ = NN.cross(V(0, 0, 1)).normalized() if abs(NN.z) < 0.99 else V(1, 0, 0); v_ = NN.cross(u_).normalized()
def surf(p):
    """closest skin point on head or body, with its outward normal"""
    best = None
    for b in (BV_B, BV_H):
        loc, nrm, idx, dist = b.find_nearest(p)
        if loc is not None and (best is None or dist < best[2]): best = (loc, nrm.normalized(), dist)
    n = best[1]
    if n.dot(best[0] - NC) < 0: n = -n
    return best[0], n
def ring_pt(phi):
    d = (u_ * math.cos(phi) + v_ * math.sin(phi)).normalized()
    best = None
    for b in (BV_B, BV_H):
        hit = b.ray_cast(NC + d * 0.2, -d, 0.25)
        if hit[0] is not None and (hit[0] - NC).length < 0.1 and (best is None or (hit[0] - NC).length < (best[0] - NC).length): best = (hit[0], hit[1].normalized())
    if best and best[1].dot(best[0] - NC) < 0: best = (best[0], -best[1])
    return best
ring = []
for k in range(72):
    r_ = ring_pt(2 * math.pi * k / 72)
    if r_: ring.append((2 * math.pi * k / 72, r_[0], r_[1]))
# stitches on the arc that faces the stitching camera (front-right, above), contiguous, 6 of them
CAM_ST = V(0.80, 0.10, 1.50)
sc_ = [(ph, p, n, n.dot((CAM_ST - p).normalized())) for (ph, p, n) in ring]
bph = max(sc_, key=lambda t: t[3])[0]
def dphi(a, b): return (a - b + math.pi) % (2 * math.pi) - math.pi
win = sorted([t for t in sc_ if abs(dphi(t[0], bph)) < 0.55], key=lambda t: dphi(t[0], bph))
STITCH = [win[int(round(i * (len(win) - 1) / 5))][:3] for i in range(6)]
idx = [sc_.index(next(t for t in sc_ if t[0] == st[0])) for st in STITCH]
print("STITCH facing", [round(sc_[i][3], 2) for i in idx])
# incision line: a thin dark-pink line flat on the skin all round the neck
INC = D.materials.new("V_Incision"); INC.use_nodes = True
pI = INC.node_tree.nodes["Principled BSDF"]; pI.inputs["Base Color"].default_value = (0.42, 0.08, 0.10, 1); pI.inputs["Roughness"].default_value = 0.45
THR = D.materials.new("V_Thread"); THR.use_nodes = True
pT = THR.node_tree.nodes["Principled BSDF"]; pT.inputs["Base Color"].default_value = (0.03, 0.05, 0.16, 1); pT.inputs["Roughness"].default_value = 0.35
col = D.collections["V14"]
cu = D.curves.new("NeckIncision", "CURVE"); cu.dimensions = '3D'; cu.bevel_depth = 0.0009; cu.bevel_resolution = 2
sp = cu.splines.new('POLY'); pts = [surf(p)[0] + surf(p)[1] * 0.0004 for (_, p, n) in ring]; sp.points.add(len(pts) - 1)
for k, q in enumerate(pts): sp.points[k].co = (*q, 1)
sp.use_cyclic_u = True; cu.materials.append(INC)
inc = D.objects.new("NeckIncision", cu); col.objects.link(inc)
key_vis(inc, 1, False); key_vis(inc, F_SEAT, True)
stitch_objs = []
for i, (phi, p, n) in enumerate(STITCH):
    t = NN
    pts = []
    for k in range(9):
        q, nq = surf(p + t * (-0.0065 + 0.013 * k / 8))
        pts.append(q + nq * 0.0008)                      # flat on the skin: 0.8 mm off (thread radius 0.6 mm)
    cu = D.curves.new("Stitch_%02d" % i, "CURVE"); cu.dimensions = '3D'; cu.bevel_depth = 0.0006; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for k, q in enumerate(pts): sp.points[k].co = (*q, 1)
    cu.materials.append(THR); cu.use_fill_caps = True
    o = D.objects.new("Stitch_%02d" % i, cu); col.objects.link(o); stitch_objs.append(o)
# stitching choreography for the left hand
def tool_frame(P, n, yaw=0.0, pitch=0.0):
    """holder pose with its needle point at P, shaft coming in from behind-above (surgeon side); yaw/pitch vary the approach"""
    a = (-(n * 0.7 + V(0.05, 0.45, 0.05))).normalized()           # from behind-side, about level with the seam
    a = (Matrix.Rotation(math.radians(yaw), 3, 'Z') @ a)
    side = a.cross(V(0, 0, 1)).normalized(); a = (Matrix.Rotation(math.radians(pitch), 3, side) @ a).normalized()
    side = a.cross(V(0, 0, 1)).normalized(); up = side.cross(a).normalized()
    Rm = Matrix((side, a, up)).transposed()
    return Matrix.Translation(P) @ Rm.to_4x4() @ Matrix.Translation(-TIP_L)
LAST_ANG = [0.0, 0.0]
def _solve(f, P, n, yaw, pitch, iters=7):
    W = tool_frame(P, n, yaw, pitch) @ HOLD_IN_WRIST.inverted()
    M = rig.matrix_world.inverted() @ W
    for it in range(iters):
        key_ik("L", f, M); key_fingers(f, GRIP_FINGERS)
        sc.frame_set(f)
        err = P - nh.matrix_world @ TIP_L
        if err.length < 0.0008: break
        M = Matrix.Translation(err) @ M
    return (P - nh.matrix_world @ TIP_L).length, M
def shaft_hits():
    M = nh.matrix_world; k = 0
    for i in range(24):
        q = M @ V(0.0, -0.085 + i * 0.005, 0.0)
        for b in (BV_B, BV_H):
            loc, nrm, idx, dist = b.find_nearest(q)
            if loc is not None and dist < 0.004: k += 1
    return k
sc.frame_set(470)
SHL = rig.matrix_world @ R.PB["upperarm01.L"].head
PMID = sum((st[1] for st in STITCH), Vector()) / len(STITCH)
NAV = sum((st[2] for st in STITCH), Vector()).normalized()
A_DES = (PMID - SHL); A_DES.z = min(A_DES.z, 0.0) - 0.12 * A_DES.length; A_DES.normalize()   # from the shoulder side, sloping slightly down onto the seam
T_IN_W = HOLD_IN_WRIST @ TIP_L
t0 = (WR_G.to_3x3() @ HOLD_IN_WRIST.to_3x3()) @ V(0, 1, 0)
ROT_W = t0.rotation_difference(A_DES).to_matrix() @ WR_G.to_3x3()
def _solve_r(f, P, Rw, iters=8):
    W = Rw.to_4x4(); W.translation = P - Rw @ T_IN_W
    M = rig.matrix_world.inverted() @ W
    for it in range(iters):
        key_ik("L", f, M); key_fingers(f, GRIP_FINGERS)
        sc.frame_set(f)
        err = P - nh.matrix_world @ TIP_L
        if err.length < 0.0008: break
        M = Matrix.Translation(err) @ M
    return (P - nh.matrix_world @ TIP_L).length, M
LASTC = [(0, 0)]
def key_tool(f, P, n):
    best = None
    for p_ in (0, -8, 8):
        side = A_DES.cross(V(0, 0, 1)).normalized()
        Rw = Matrix.Rotation(math.radians(p_), 3, side) @ ROT_W
        e, M = _solve_r(f, P, Rw)
        if best is None or e < best[0]: best = (e, M)
        if e < 0.002: break
    key_ik("L", f, best[1]); key_fingers(f, GRIP_FINGERS); sc.frame_set(f)
    return (P - nh.matrix_world @ TIP_L).length
# keep only seam points the hand reaches with this one orientation (no wrist flips), 4 of them, contiguous
ok_pts = []
for t in sorted(win, key=lambda t: dphi(t[0], bph)):
    e, M = _solve_r(470, t[1] + t[2] * 0.0015, ROT_W)
    sc.frame_set(470)
    if e < 0.003: ok_pts.append(t[:3])
print("REACHABLE seam points", len(ok_pts), "of", len(win))
if len(ok_pts) >= 4:
    STITCH[:] = [ok_pts[int(round(i * (len(ok_pts) - 1) / 3))] for i in range(4)]
for i, (phi, p, n) in enumerate(STITCH):        # rebuild the kept stitches at the chosen seam points (flat on the skin)
    sp = stitch_objs[i].data.splines[0]
    for k in range(9):
        q, nq = surf(p + NN * (-0.0065 + 0.013 * k / 8)); q = q + nq * 0.0008
        sp.points[k].co = (*q, 1)
for o in stitch_objs[len(STITCH):]:
    o.hide_render = o.hide_viewport = True
    D.objects.remove(o, do_unlink=True)
stitch_objs = stitch_objs[:len(STITCH)]
F_ST0 = 470; STEP = 30
key_ik("L", F_NHG + 16, Matrix.Translation(V(0, 0, 0.09)) @ GRIP_IK); key_fingers(F_NHG + 16, GRIP_FINGERS)
errs = []
p0, n0 = STITCH[0][1], STITCH[0][2]
WP = [(F_ST0 - 18, p0 + n0 * 0.08 + V(0, 0, 0.03), n0)]
for i, (phi, p, n) in enumerate(STITCH):
    f0 = F_ST0 + i * STEP
    WP += [(f0, p + n * 0.012, n), (f0 + 6, p + n * 0.0015, n), (f0 + 12, p + n * 0.016 + NN * 0.008, n)]
    o = stitch_objs[i]
    o.data.bevel_factor_end = 0.0; o.data.keyframe_insert("bevel_factor_end", frame=f0 + 6)
    o.data.bevel_factor_end = 1.0; o.data.keyframe_insert("bevel_factor_end", frame=f0 + 13)
    key_vis(o, 1, False); key_vis(o, f0 + 6, True)
pl, nl = STITCH[-1][1], STITCH[-1][2]
WP.append((F_ST0 + len(STITCH) * STEP + 8, pl + nl * 0.05 + V(0, 0.03, 0.02), nl))
WP.append((F_ST0 + len(STITCH) * STEP + 22, pl + nl * 0.09 + V(0, 0.10, 0.08), nl))
for (fa, pa, na), (fb, pb_, nb) in zip(WP, WP[1:]):
    for f in range(fa, fb, 2):
        u = (f - fa) / (fb - fa)
        # path bows outward along the skin normal between points (never cuts through the neck)
        P = pa.lerp(pb_, u) + na.lerp(nb, u).normalized() * (0.01 * math.sin(math.pi * u))
        errs.append(key_tool(f, P, na.lerp(nb, u).normalized()))
errs.append(key_tool(WP[-1][0], WP[-1][1], WP[-1][2]))
print("TOOL tip errors mm max", round(max(errs) * 1000, 1), "n", len(errs), [round(e*1000) for e in errs])
# put the holder back exactly where it was picked up
key_ik("L", F_NHR - 18, Matrix.Translation(V(0, 0, 0.08)) @ GRIP_IK); key_fingers(F_NHR - 18, GRIP_FINGERS)
key_ik("L", F_NHR - 1, GRIP_IK); key_fingers(F_NHR - 1, GRIP_FINGERS)
key_ik("L", F_NHR, GRIP_IK); key_fingers(F_NHR, GRIP_FINGERS)
sc.frame_set(F_NHR + 18)
place_hand(rig, "L", F_NHR + 18, grip_pt + V(0, 0.02, 0.08), V(0, 0, -1), (NH_REST.to_3x3() @ V(0, 1, 0)).normalized(), skin=0.03)
apply_pose(rig, "L", "relaxed", F_NHR + 18)
rest_hand("L", 745)
# body pose must match at pick-up and put-down (identical wrist => holder lands exactly on its rest pose)
# ---- beat 5: left index finger moves beside the monkey's face (no contact); the eyes follow it
FACE = MB.translation + (MB.to_3x3() @ (HC_local - V(0, 0, 0)))
sc.frame_set(1)
print("FACE centre", tuple(round(v, 3) for v in FACE))
def hand_wp(f, P):        # a high waypoint above the backrest/shoulder line so the arm never sweeps through them
    place_hand(rig, "L", f, P, V(0, 0, -1), V(0.2, -1, 0).normalized(), skin=0.02); apply_pose(rig, "L", "relaxed", f)
hand_wp(800, V(0.47, 0.44, 1.50)); hand_wp(965, V(0.47, 0.44, 1.50)); hand_wp(1098, V(0.45, 0.36, 1.58)); hand_wp(1338, V(0.45, 0.36, 1.58))
for f, off in ((835, V(0.17, 0.05, 0.04)), (870, V(0.15, -0.02, 0.02)), (905, V(0.17, 0.04, 0.06)), (935, V(0.19, 0.08, 0.03))):
    place_hand(rig, "L", f, FACE + off, V(-1, 0, 0), V(0, -0.6, 0.8).normalized(), skin=0.012)
    apply_pose(rig, "L", "point", f)
rest_hand("L", 1000); rest_hand("L", 1070, dx=0.01)
# ---- beat 7: left palm resting on the monkey's left shoulder (ray cast onto the fur), eyes look at it
hit = BV_B.ray_cast(MB.translation + V(0.12, -0.07, 0.75), V(0, 0, -1), 1.0) if False else None
sc.frame_set(1100)
BVB = bvh_world(bodyB)
cands = []
for xx in (0.33, 0.35, 0.37, 0.39):
    for yy in (0.12, 0.16, 0.20, 0.24):
        h_ = BVB.ray_cast(V(xx, yy, 1.8), V(0, 0, -1), 1.5)
        if h_[0] is not None and h_[1].normalized().z > 0.6: cands.append((h_[0].z, h_[0], h_[1].normalized()))
cands.sort(key=lambda c: -c[0]); SH_P, SH_N = cands[0][1], cands[0][2]
print("SHOULDER contact", tuple(round(v, 3) for v in SH_P), tuple(round(v, 2) for v in SH_N))
place_hand(rig, "L", 1110, SH_P + SH_N * 0.06, -SH_N, V(0.1, -1, -0.1).normalized(), skin=0.014); apply_pose(rig, "L", "relaxed", 1110)
place_hand(rig, "L", 1135, SH_P, -SH_N, V(0.1, -1, -0.1).normalized(), skin=0.024); apply_pose(rig, "L", "shield", 1135)
place_hand(rig, "L", 1290, SH_P, -SH_N, V(0.1, -1, -0.1).normalized(), skin=0.024); apply_pose(rig, "L", "shield", 1290)
place_hand(rig, "L", 1315, SH_P + SH_N * 0.06, -SH_N, V(0.1, -1, -0.1).normalized(), skin=0.014)
rest_hand("L", 1375); rest_hand("L", 1500, dx=-0.01); rest_hand("L", 1656)
# ======================================================================== monkey face: lids, gaze, ears
LU = [D.objects["LidUp_L"], D.objects["LidUp_R"]]; LO = [D.objects["LidLo_L"], D.objects["LidLo_R"]]
UP_C, UP_O, LO_C, LO_O = 0.07, -1.309, 0.017, 0.716
def lids(f, openness):
    for o in LU: o.rotation_euler.x = UP_C + (UP_O - UP_C) * openness; o.keyframe_insert("rotation_euler", index=0, frame=f)
    for o in LO: o.rotation_euler.x = LO_C + (LO_O - LO_C) * openness; o.keyframe_insert("rotation_euler", index=0, frame=f)
for f, op in ((1, 0), (690, 0), (697, 0.35), (704, 0.05), (716, 0.55), (724, 0.2), (742, 0.85), (760, 1.0),
              (798, 1.0), (803, 0.0), (809, 1.0), (1000, 1.0), (1005, 0.0), (1011, 1.0), (1196, 1.0), (1201, 0.0), (1207, 1.0),
              (1380, 1.0), (1385, 0.0), (1391, 1.0), (1500, 1.0), (1508, 0.1), (1520, 0.8), (1580, 0.75), (1640, 0.45), (1656, 0.42)):
    lids(f, op)
mh = D.materials["M_MonkeyHead"].node_tree.nodes
def gaze(f, x, z=0.0):
    mh["GazeX"].outputs[0].default_value = x; mh["GazeX"].outputs[0].keyframe_insert("default_value", frame=f)
    mh["GazeZ"].outputs[0].default_value = z; mh["GazeZ"].outputs[0].keyframe_insert("default_value", frame=f)
for f, x, z in ((1, 0, 0), (760, 0, 0), (790, -0.0012, 0.0004), (830, -0.0004, 0.0), (850, 0.0016, 0.0004), (875, 0.0012, 0.0),
                (905, 0.0019, 0.0006), (935, 0.0020, 0.0003), (990, 0.0, 0.0), (1140, 0.0016, -0.0008), (1165, -0.0012, 0.0),
                (1195, 0.0015, -0.0006), (1230, -0.0008, 0.0002), (1290, 0.0018, -0.0002), (1420, 0.0017, -0.0003),
                (1480, 0.0, 0.0), (1560, -0.0004, -0.0006), (1656, -0.0002, -0.0008)):
    gaze(f, x, z)
kb = head.data.shape_keys.key_blocks
kb["Ears_Round"].value = 0.75
def ear(name, f, v):
    kb[name].value = v; kb[name].keyframe_insert("value", frame=f)
for name, f0 in (("Ear_L", 905), ("Ear_R", 922), ("Ear_L", 1215)):
    ear(name, f0, 0.0); ear(name, f0 + 6, 0.8); ear(name, f0 + 16, 0.15); ear(name, f0 + 24, 0.0)
# ======================================================================== x-ray (beat 6, synced 949-1093)
F_X0, F_X1, F_X2, F_X3 = 958, 990, 1060, 1092
def key_val(nodes, name, f, v):
    nodes[name].outputs[0].default_value = v; nodes[name].outputs[0].keyframe_insert("default_value", frame=f)
XRMATS = ["M_MonkeyGinger", "M_MonkeyHead", "M_NeckCap", "M_MonkeyPale"]
for mn in XRMATS:
    nt = D.materials[mn].node_tree.nodes
    for f, v in ((1, 0.0), (F_X0, 0.0), (F_X1, 1.0), (F_X2, 1.0), (F_X3, 0.0)): key_val(nt, "XRay", f, v)
# void: camera-parented sphere with the cyan->white explainer gradient (camera rays only, lights pass through)
cam = sc.camera
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.25, segments=48, ring_count=24, location=(0, 0, 0))
vo = bpy.context.active_object; vo.name = "XR_Void"
for c in vo.users_collection: c.objects.unlink(vo)
col.objects.link(vo); vo.parent = cam; vo.matrix_parent_inverse = Matrix.Identity(4); vo.location = (0, 0, 0)
for p in vo.data.polygons: p.use_smooth = True
vo.visible_diffuse = vo.visible_glossy = vo.visible_transmission = vo.visible_volume_scatter = vo.visible_shadow = False
vm = D.materials.new("M_XR_Void2"); vm.use_nodes = True; nt = vm.node_tree; nt.nodes.clear()
o_ = nt.nodes.new("ShaderNodeOutputMaterial"); mix = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent")
em = nt.nodes.new("ShaderNodeEmission"); ramp = nt.nodes.new("ShaderNodeValToRGB"); tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); val = nt.nodes.new("ShaderNodeValue"); val.name = "VoidOn"
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.91, 0.97, 1.0, 1)
ramp.color_ramp.elements[1].position = 1.0; ramp.color_ramp.elements[1].color = (0.31, 0.76, 0.97, 1)
nt.links.new(tc.outputs["Window"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], ramp.inputs[0]); nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
em.inputs["Strength"].default_value = 1.0
nt.links.new(val.outputs[0], mix.inputs[0]); nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], o_.inputs["Surface"])
vo.data.materials.append(vm)
for f, v in ((F_X0, 0.0), (F_X1, 1.0), (F_X2, 1.0), (F_X3, 0.0)): key_val(nt.nodes, "VoidOn", f, v)
key_vis(vo, 1, False); key_vis(vo, F_X0, True); key_vis(vo, F_X3 + 1, False)
# props inside the void radius fade with it (tables, seats, towel, holder, donor body A, monitor cart)
def add_fade(m, tag="VoidFade"):
    nt = m.node_tree
    if nt is None or tag in nt.nodes: return
    outn = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None) or next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if outn is None or not outn.inputs["Surface"].links: return
    src = outn.inputs["Surface"].links[0].from_socket
    mx = nt.nodes.new("ShaderNodeMixShader"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); v = nt.nodes.new("ShaderNodeValue"); v.name = tag
    v.outputs[0].default_value = 1.0
    nt.links.new(v.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(src, mx.inputs[2]); nt.links.new(mx.outputs[0], outn.inputs["Surface"])
    for f, val_ in ((F_X0, 1.0), (F_X1, 0.0), (F_X2, 0.0), (F_X3, 1.0)): key_val(nt.nodes, tag, f, val_)
KEEP_EXACT = {"M_MonkeyGinger", "M_MonkeyHead", "M_NeckCap", "M_MonkeyPale", "V_Thread", "V_Incision", "M_XR_Void2"}
class _K(tuple):
    pass
def _keep(n): return n in KEEP_EXACT or n.startswith(("M_XR", "V_XR"))
B_GROUP = {"MK_BodyB", "MK_Head", "LidUp_L", "LidUp_R", "LidLo_L", "LidLo_R", "NeckIncision", "XR_Void"}
FADE_OBJS = [o for o in D.objects if o.type in ('MESH', 'CURVE') and o.name not in B_GROUP and not o.name.startswith(("Stitch_", "XR_"))]
done = set()
for o in FADE_OBJS:
    for m in [sl.material for sl in o.material_slots]:
        if m and m.name not in done and not _keep(m.name):
            add_fade(m); done.add(m.name)
for o in FADE_OBJS:
    for m in [sl.material for sl in o.material_slots]:
        if m and _keep(m.name) and o.name not in B_GROUP:
            print("WARN shared keep-material on faded object", o.name, m.name)
for o in stitch_objs + [inc]:
    pass
print("FADED materials", len(done))
# x-ray anatomy: brain in the cranium, spinal cord down the back, a visible GAP at the neck seam
XRM = D.materials.new("V_XR_Cord"); XRM.use_nodes = True; p_ = XRM.node_tree.nodes["Principled BSDF"]
p_.inputs["Base Color"].default_value = (1.0, 0.86, 0.55, 1); p_.inputs["Emission Color"].default_value = (1.0, 0.75, 0.35, 1); p_.inputs["Emission Strength"].default_value = 2.5
BON = D.materials.new("V_XR_Vert"); BON.use_nodes = True; p_ = BON.node_tree.nodes["Principled BSDF"]
p_.inputs["Base Color"].default_value = (0.95, 0.92, 0.82, 1); p_.inputs["Emission Color"].default_value = (0.95, 0.92, 0.85, 1); p_.inputs["Emission Strength"].default_value = 0.8
GLW = D.materials.new("V_XR_Gap"); GLW.use_nodes = True; p_ = GLW.node_tree.nodes["Principled BSDF"]
p_.inputs["Base Color"].default_value = (1.0, 0.25, 0.12, 1); p_.inputs["Emission Color"].default_value = (1.0, 0.22, 0.08, 1); p_.inputs["Emission Strength"].default_value = 6.0
sc.frame_set(1000)
hv = [head.matrix_world @ v.co for v in head.data.vertices]
hmin = V(*[min(v[i] for v in hv) for i in range(3)]); hmax = V(*[max(v[i] for v in hv) for i in range(3)])
hc = (hmin + hmax) / 2
brain = D.objects["XR_Brain"]; brain.hide_viewport = False; brain.hide_render = False; brain.parent = None; brain.matrix_parent_inverse = Matrix.Identity(4)
brain.constraints.clear(); brain.animation_data_clear()
bvs = brain.data.vertices; lo_ = V(*[min(v.co[i] for v in bvs) for i in range(3)]); hi_ = V(*[max(v.co[i] for v in bvs) for i in range(3)])
cl = (lo_ + hi_) / 2; s_ = 0.07 / max(hi_ - lo_)
brain.rotation_mode = 'XYZ'; brain.rotation_euler = (math.radians(-8), 0, 0); brain.scale = (s_, s_, s_)
Rb = brain.rotation_euler.to_matrix()
brain.location = hc + V(0, 0.02, 0.02) - Rb @ (cl * s_)
bpy.context.view_layer.update()
print("BRAIN dims", tuple(round(v, 3) for v in brain.dimensions))
mw = brain.matrix_world.copy(); brain.parent = head; brain.matrix_world = mw
for i, m in enumerate(brain.data.materials):
    pass
# spinal cord centre line: slices of body B, 3 cm in from the back surface
bv_ = [bodyB.matrix_world @ v.co for v in bodyB.data.vertices]
seam_z = NC.z
cord = []
for k in range(12):
    z = seam_z - 0.02 - k * 0.035
    sl = [v for v in bv_ if abs(v.z - z) < 0.012 and abs(v.x - MB.translation.x) < 0.09]
    if len(sl) < 10: continue
    yb = max(v.y for v in sl); x = sum(v.x for v in sl) / len(sl)
    cord.append(V(x, yb - 0.035, z))
gap_b = NC - NN * 0.006 + V(0, 0.015, 0)
cord = [gap_b] + cord
stem_top = hc + V(0, 0.025, -0.01)
gap_h = NC + NN * 0.006 + V(0, 0.015, 0)
def tube(name, pts, r, m, parent):
    cu = D.curves.new(name, "CURVE"); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for k, q in enumerate(pts):
        bp = sp.bezier_points[k]; bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.materials.append(m); o = D.objects.new(name, cu); col.objects.link(o)
    mw = o.matrix_world.copy(); o.parent = parent; o.matrix_parent_inverse = parent.matrix_world.inverted(); return o
xr_objs = [brain]
xr_objs.append(tube("XR_CordHead", [stem_top, stem_top.lerp(gap_h, 0.5) + V(0, 0.006, 0), gap_h], 0.0045, XRM, head))
xr_objs.append(tube("XR_CordBody", cord, 0.0045, XRM, bodyB))
for k in range(1, len(cord) - 1):
    for t in (0.0, 0.5):
        q = cord[k].lerp(cord[k + 1], t)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8, location=q)
        vb = bpy.context.active_object; vb.name = "XR_Vert_%02d" % len(xr_objs)
        for c in vb.users_collection: c.objects.unlink(vb)
        col.objects.link(vb); vb.scale = (0.016, 0.013, 0.006)
        tan = (cord[k + 1] - cord[k]).normalized(); vb.rotation_mode = 'QUATERNION'; vb.rotation_quaternion = tan.to_track_quat('Z', 'Y')
        vb.data.materials.append(BON)
        for p in vb.data.polygons: p.use_smooth = True
        bpy.context.view_layer.update(); mw = vb.matrix_world.copy(); vb.parent = bodyB; vb.matrix_world = mw
        xr_objs.append(vb)
for nm_, q, par in (("XR_GapHead", gap_h, head), ("XR_GapBody", gap_b, bodyB)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0065, segments=16, ring_count=8, location=q)
    g = bpy.context.active_object; g.name = nm_
    for c in g.users_collection: c.objects.unlink(g)
    col.objects.link(g); g.data.materials.append(GLW); bpy.context.view_layer.update(); mw = g.matrix_world.copy(); g.parent = par; g.matrix_world = mw
    xr_objs.append(g)
# a pulse runs down from the brain and stops at the gap
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.006, segments=16, ring_count=8, location=stem_top)
pu = bpy.context.active_object; pu.name = "XR_Pulse"
for c in pu.users_collection: c.objects.unlink(pu)
col.objects.link(pu); pu.data.materials.append(GLW); xr_objs.append(pu)
for f, q in ((1000, stem_top), (1030, gap_h), (1035, stem_top), (1062, gap_h)):
    pu.location = q; pu.keyframe_insert("location", frame=f)
for o in xr_objs:
    key_vis(o, 1, False); key_vis(o, F_X0 + 4, True); key_vis(o, F_X3 - 2, False)
# ======================================================================== ECG: steady beat, then it slows and fades toward flat
ecg = D.materials.get("M_ECG")
if ecg:
    en = ecg.node_tree.nodes
    t = 0.0; last = 1
    keys = [(1, 0.0)]
    for f in range(31, 1657, 30):
        rate = 1.0 if f < 1460 else max(0.25, 1.0 - (f - 1460) / 260.0)
        t += 0.5 * rate; keys.append((f, t))
    for f, v in keys: key_val(en, "ECGTime", f, v)
    for f, v in ((1, 1.0), (1460, 1.0), (1600, 0.35), (1656, 0.2)): key_val(en, "ECGAmp", f, v)
    for fc in fc_all(ecg.node_tree):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# ======================================================================== light dims at the end
sc.view_settings.exposure = -0.25; sc.view_settings.keyframe_insert("exposure", frame=1)
sc.view_settings.keyframe_insert("exposure", frame=1470)
sc.view_settings.exposure = -0.75; sc.view_settings.keyframe_insert("exposure", frame=1656)
# ======================================================================== camera: one move, keyed framings, monotone spline
CAMK = json.load(open(os.path.join(HERE, "camera_keys.json")))
def pchip1(xs, ys):
    n = len(xs); h = [xs[i + 1] - xs[i] for i in range(n - 1)]; d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n; m[0] = d[0]; m[-1] = d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0: m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    # keep the camera moving through framings: never a full stop at an interior key
    for i in range(1, n - 1):
        if m[i] == 0.0: m[i] = 0.25 * (d[i - 1] + d[i])
    def f(x):
        if x <= xs[0]: return ys[0] + m[0] * (x - xs[0])
        if x >= xs[-1]: return ys[-1] + m[-1] * (x - xs[-1])
        i = max(j for j in range(n - 1) if xs[j] <= x); t = (x - xs[i]) / h[i]
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1; h10 = t ** 3 - 2 * t ** 2 + t; h01 = -2 * t ** 3 + 3 * t ** 2; h11 = t ** 3 - t ** 2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f
fr = [k["f"] for k in CAMK]
CP = [pchip1(fr, [k["pos"][i] for k in CAMK]) for i in range(3)]
CT = [pchip1(fr, [k["tgt"][i] for k in CAMK]) for i in range(3)]
CL = pchip1(fr, [k["lens"] for k in CAMK])
cam.animation_data_clear(); cam.data.animation_data_clear() if cam.data.animation_data else None
cam.rotation_mode = 'QUATERNION'; cam.constraints.clear()
cd = cam.data; cd.sensor_fit = 'AUTO'; cd.sensor_width = 36; cd.clip_start = 0.02; cd.clip_end = 60
cd.dof.use_dof = True; cd.dof.aperture_fstop = 8.0
for f in range(1, 1657):
    p = V(*[c(f) for c in CP]); t = V(*[c(f) for c in CT])
    cam.location = p; cam.rotation_quaternion = (t - p).to_track_quat('-Z', 'Y')
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = CL(f); cd.keyframe_insert("lens", frame=f)
    cd.dof.focus_distance = (t - p).length; cd.dof.keyframe_insert("focus_distance", frame=f)
interp(cam, 'LINEAR'); interp(cd, 'LINEAR')
# ======================================================================== VO
vo_path = os.path.join(os.path.dirname(OUT), "MonkeyHeadTransplant_v014_VO.mp3")
if not sc.sequence_editor: sc.sequence_editor_create()
for s_ in list(sc.sequence_editor.strips_all if hasattr(sc.sequence_editor, "strips_all") else sc.sequence_editor.sequences_all):
    try: sc.sequence_editor.strips.remove(s_)
    except Exception: pass
if os.path.exists(vo_path):
    strips = sc.sequence_editor.strips if hasattr(sc.sequence_editor, "strips") else sc.sequence_editor.sequences
    snd = strips.new_sound("VO", vo_path, 1, 1)
sc.cycles.transparent_max_bounces = 48; sc.cycles.max_bounces = 12
for mn in ("M_NeckCap", "M_NeckCap_A"):          # neck disc: skin tone, blends into the fur edge
    m = D.materials.get(mn)
    if not m: continue
    pbsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if pbsdf:
        for l in list(pbsdf.inputs["Base Color"].links): m.node_tree.links.remove(l)
        pbsdf.inputs["Base Color"].default_value = (0.72, 0.50, 0.38, 1); pbsdf.inputs["Roughness"].default_value = 0.75
print("ANIM DONE")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
