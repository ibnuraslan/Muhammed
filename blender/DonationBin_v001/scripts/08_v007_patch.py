"""DonationBin v007 patch, applied to the packed v006 file (director review of 40a3660). It changes the camera and two hands only.
blender -b DonationBin_v006_60fps.blend --python 08_v007_patch.py -- out.blend
1. One continuous camera: each of the three v006 hard cuts becomes a covered wall push. The camera dollies into the bin
   wall until the surface fills the frame (3+ frames), the jump happens between two covered frames, and it pulls out on the far side.
2. f961 (beat 6) and the scream: the camera is at the front three-quarters of her face, about 0.6 m off.
3. 19.5 s: the camera stays at least 30 cm from her hands.
4. 35.5 s: the camera is at her face height as she climbs out.
5. f445 / f628: the hand over the clothes is flat on the clothes (place_hand + flat_palm), or relaxed."""
import sys, json, math
import bpy
from mathutils import Vector, Matrix
exec(open("/home/user/Muhammed/blender/pipeline/anim_lib.py").read())
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera; cd = cam.data
WO = bpy.data.objects["Woman"]; HB = WO.pose.bones["head"]
FWDH = WO.data.bones["head"].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
WMESH = set(c.name for c in WO.children_recursive)
def dg(): return bpy.context.evaluated_depsgraph_get()
def face(f):
    sc.frame_set(f); M = WO.matrix_world
    hd = M @ HB.head; up = (M @ HB.tail - hd).normalized()
    fw = (M.to_3x3() @ (HB.matrix.to_3x3() @ FWDH)).normalized()
    return hd - up * 0.03 + fw * 0.05, fw
def ray(o, d, L=5.0):
    h = sc.ray_cast(dg(), Vector(o), Vector(d).normalized(), distance=L)
    return h if h[0] else None
def air(c, r=0.14):
    for d in (Vector((1, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
        if ray(c, d, r): return False
    return True
def sees(c, p):
    v = p - c; h = ray(c, v, v.length)
    return h is None or (h[1] - c).length > v.length - 0.12 or h[4].name in WMESH
def front34(f, dists=(0.62, 0.56, 0.50, 0.45, 0.40), angs=(35, -35, 28, -28, 42, -42, 20, -20, 50, -50), ylo=-0.47, ra=0.14):
    fc, fw = face(f); fh = Vector((fw.x, fw.y, 0)).normalized()
    for d in dists:
        for a in angs:
            for up in (-0.05, 0.03, -0.12, 0.10):
                c = fc + (Matrix.Rotation(math.radians(a), 3, 'Z') @ fh) * d + Vector((0, 0, up))
                if -0.62 < c.x < 0.62 and ylo < c.y < 0.48 and 0.8 < c.z < 2.25 and air(c, ra) and sees(c, fc):
                    return [f, list(c), list(fc - Vector((0, 0, 0.02))), 22]
    print("NO34", f); return None

CAMK = json.loads(sc["cam_keys"])
DROP = {1402, 1404, 1560, 1862, 1868, 950, 1322, 1350, 1384}
CAMK = [k for k in CAMK if k[0] not in DROP]
NEW = []
# 2. beat 6 and the scream: front three-quarters of her face
for f in (950, 965):
    k = front34(f)
    if k: NEW.append(k)
for f in (1322, 1336, 1350, 1366, 1384):
    k = front34(f) or front34(f, dists=(0.50, 0.44, 0.38, 0.32), angs=(35, -35, 45, -45, 55, -55, 65, -65, 25, -25))
    if k: NEW.append(k)
# 1. covered wall pushes (inner and outer faces of the front wall, found by ray cast)
def hit(o, d): h = ray(o, d); return h[1] if h else None
X = 0.25
in_hi = hit((X, -0.15, 1.95), (0, -1, 0)); out_hi = hit((X, -1.6, 1.95), (0, 1, 0))
in_lo = hit((X, 0.05, 0.98), (0, -1, 0)); out_lo = hit((X, -1.6, 0.98), (0, 1, 0))
print("WALL", in_hi, out_hi, in_lo, out_lo)
Y = Vector((0, 1, 0))
def push_in(f_app, f_c1, f_c2, w, side):   # side +1: camera on the +y side of the surface looking -y
    NEW.append([f_app, list(w + Y * side * 0.30), list(w), 22])
    NEW.append([f_c1, list(w + Y * side * 0.03), list(w - Y * side * 0.2), 22])
    NEW.append([f_c2, list(w + Y * side * 0.02), list(w - Y * side * 0.2), 22])
def push_out(f_c1, f_c2, w, side):
    NEW.append([f_c1, list(w + Y * side * 0.02), list(w - Y * side * 0.2), 22])
    NEW.append([f_c2, list(w + Y * side * 0.03), list(w - Y * side * 0.2), 22])
# exit after the scream: into the inner wall above the flap, out of the outer wall, pull back to the wide of the bin
push_in(1396, 1399, 1402, in_hi, +1); push_out(1403, 1405, out_hi, -1)
NEW.append([1418, [0.30, -1.70, 1.80], [0.0, -0.6, 1.35], 22])
# back in for the three days: into the outer wall low, out of the inner wall, pan round to her face
push_in(1546, 1552, 1555, out_lo, -1); push_out(1556, 1559, in_lo, +1)
fc, _ = face(1574); NEW.append([1574, [0.40, -0.30, 1.05], list(fc), 22])
# the knock: into the inner wall, out of the outer wall, then the passer-by (key 1880)
push_in(1862, 1865, 1868, in_lo, +1); push_out(1869, 1871, out_lo, -1)
# 4. 35.5 s: her face height as she climbs out
fc, _ = face(2130); NEW.append([2130, [fc.x + 0.30, fc.y - 0.85, fc.z - 0.02], list(fc), 24])
CAMK = sorted([k for k in CAMK if not any(abs(k[0] - n[0]) < 1 for n in NEW)] + NEW, key=lambda k: k[0])
sc["cam_keys"] = json.dumps(CAMK)

# bake: splines split at the covered jumps only
JUMPS = [1, 1403, 1556, 1869, sc.frame_end + 1]
SEG = []
for a_, b_ in zip(JUMPS, JUMPS[1:]):
    ks = [k for k in CAMK if a_ <= k[0] < b_]
    SEG.append((a_, b_, catmull([(k[0], Vector(k[1])) for k in ks]), catmull([(k[0], Vector(k[2])) for k in ks]), pchip([(k[0], float(k[3])) for k in ks])))
def seg(f): return next(s_ for s_ in SEG if s_[0] <= f < s_[1])
POS = {}
for f in range(1, sc.frame_end + 1):
    s_ = seg(f); POS[f] = [s_[2](f), s_[3](f), s_[4](f)]
# covered frames: hold 5 cm off the wall face (near-clip safe), looking straight into it
COVER = [(1399, 1402, in_hi, +1), (1403, 1405, out_hi, -1), (1552, 1555, out_lo, -1), (1556, 1559, in_lo, +1), (1865, 1868, in_lo, +1), (1869, 1871, out_lo, -1)]
for f0, f1, w, side in COVER:
    for f in range(f0, f1 + 1): POS[f] = [w + Y * side * 0.05, w - Y * side * 0.2, 22.0]
print("COVERED", [(a, b) for a, b, _, _ in COVER])
# 3. keep 30 cm from her hands (19-20.5 s), smoothed
off = {}
for f in range(1140, 1200):
    sc.frame_set(f); p = POS[f][0]
    pts = [WO.matrix_world @ WO.pose.bones[b].head for s in "LR" for b in ("wrist." + s, "finger3-1." + s)] + \
          [WO.matrix_world @ WO.pose.bones["finger3-3." + s].tail for s in "LR"]
    q = min(pts, key=lambda x: (x - p).length); d = (q - p).length
    off[f] = (p - q).normalized() * (0.32 - d) if d < 0.32 else Vector()
for f in range(1140, 1200):
    v = sum((off.get(g, Vector()) for g in range(f - 4, f + 5)), Vector()) / 9
    mx = max((off.get(g, Vector()).length for g in range(f - 4, f + 5)), default=0)
    if v.length > 1e-6: v = v.normalized() * max(v.length, mx)
    p = POS[f][0] + v
    POS[f][0] = Vector((max(-0.62, min(0.62, p.x)), max(-0.47, min(0.48, p.y)), min(2.25, p.z)))
for fcv in cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves: fcv.keyframe_points.clear()
for l in cd.animation_data.action.layers:
    for st in l.strips:
        for cb in st.channelbags:
            for fcv in cb.fcurves: fcv.keyframe_points.clear()
QS = {}
qprev = None
for f in range(1, sc.frame_end + 1):
    q = (POS[f][1] - POS[f][0]).to_track_quat('-Z', 'Y')
    if qprev is not None and q.dot(qprev) < 0: q = -q
    QS[f] = q; qprev = q
# pans next to the pushes: slerp the rotation (smoothstep) so the look-at never swings past the lens
for a_, b_ in ((1559, 1582), (1845, 1865), (1871, 1886)):
    qa, qb = QS[a_], QS[b_]
    for f in range(a_ + 1, b_):
        t_ = (f - a_) / (b_ - a_); t_ = t_ * t_ * (3 - 2 * t_); QS[f] = qa.slerp(qb, t_)
qprev = None
for f in range(1, sc.frame_end + 1):
    p, t, ln = POS[f]
    cam.location = p; cam.keyframe_insert("location", frame=f)
    q = QS[f].copy(); cam.rotation_mode = 'QUATERNION'
    if qprev is not None and q.dot(qprev) < 0: q = -q
    qprev = q.copy(); cam.rotation_quaternion = q; cam.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = ln; cd.keyframe_insert("lens", frame=f)
    cd.dof.focus_distance = max(0.05, (t - p).length); cd.dof.keyframe_insert("focus_distance", frame=f)
for fcv in list(cam.animation_data.action.layers[0].strips[0].channelbags[0].fcurves) + [c for l in cd.animation_data.action.layers for st in l.strips for cb in st.channelbags for c in cb.fcurves]:
    for kp in fcv.keyframe_points:
        kp.interpolation = 'CONSTANT' if int(round(kp.co.x)) in (1402, 1555, 1868) else 'LINEAR'

# 5. f445 / f628: palm flat on the clothes (or relaxed when it is high)
CLOTH = [bpy.data.objects[n] for n in sc["pile_colliders"].split(",")]
def cloth_z(x, y):
    z = None
    for o in CLOTH:
        inv = o.matrix_world.inverted()
        h, loc, n, i = o.ray_cast(inv @ Vector((x, y, 3.0)), (inv.to_3x3() @ Vector((0, 0, -1))).normalized())
        if h:
            wz = (o.matrix_world @ loc).z; z = wz if z is None else max(z, wz)
    return z
for s, f0, f1 in (("R", 425, 468),):
    names = ["IK_hand." + s] + _chain(s)
    for g in (f0 - 6, f1 + 6):                       # anchors
        sc.frame_set(g)
        for n in names:
            pb = WO.pose.bones[n]
            if n.startswith("IK"): pb.keyframe_insert("location", frame=g, group=n)
            pb.keyframe_insert("rotation_quaternion", frame=g, group=n)
    for f in range(f0, f1 + 1, 4):
        sc.frame_set(f)
        wr = WO.matrix_world @ WO.pose.bones["wrist." + s].head; md = WO.matrix_world @ WO.pose.bones["finger3-1." + s].head
        palm = wr.lerp(md, 0.6); z = cloth_z(palm.x, palm.y)
        if z is not None and palm.z - z < 0.16:
            fd = md - wr; fd.z = 0
            place_hand(WO, s, f, Vector((palm.x, palm.y, z)), Vector((0, 0, -1)), fd.normalized() if fd.length > 1e-3 else Vector((0, -1, 0)), skin=0.008)
            apply_pose(WO, s, "flat_palm", f)
        else:
            apply_pose(WO, s, "relaxed", f)
for s in "LR":                                         # f628: kneel-to-stand, both hands relaxed (not splayed)
    for f in range(604, 653, 6): apply_pose(WO, s, "relaxed", f)
sc["director_fix"] = "v007: one continuous camera (covered wall pushes), front 3/4 on beat 6 and scream, hands flat on clothes"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007_DONE", len(CAMK))
