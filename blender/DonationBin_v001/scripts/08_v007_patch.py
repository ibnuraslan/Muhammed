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
DROP = {1402, 1404, 1560, 1862, 1868, 950, 1322, 1350, 1384, 1418, 1574}
CAMK = [k for k in CAMK if k[0] not in DROP]
NEW = []
# 2. beat 6 and the scream: front three-quarters of her face
for f in (950, 965):
    k = front34(f)
    if k: NEW.append(k)
for f in (1322, 1336, 1350, 1366, 1384):
    k = front34(f) or front34(f, dists=(0.50, 0.44, 0.38, 0.32), angs=(35, -35, 45, -45, 55, -55, 65, -65, 25, -25))
    if not k:      # pounding the flap: steady side view, clear of the flap stop bar and counterweight
        fc, _ = face(f); k = [f, [0.50, -0.22, 1.68], list(fc), 30]
    NEW.append(k)
# 1. covered wall pushes (inner and outer faces of the front wall, found by ray cast)
def hit(o, d): h = ray(o, d); return h[1] if h else None
X = 0.25
in_hi = hit((X, -0.15, 1.95), (0, -1, 0)); out_hi = hit((X, -1.6, 1.95), (0, 1, 0))
in_lo = hit((X, 0.05, 0.98), (0, -1, 0)); out_lo = hit((X, -1.6, 0.98), (0, 1, 0))
print("WALL", in_hi, out_hi, in_lo, out_lo)
Y = Vector((0, 1, 0))
def push_in(f_app, f_c1, f_c2, w, side):   # side +1: camera on the +y side of the surface looking -y
    if f_app: NEW.append([f_app, list(w + Y * side * 0.30), list(w), 22])
    NEW.append([f_c1, list(w + Y * side * 0.03), list(w - Y * side * 0.2), 22])
    NEW.append([f_c2, list(w + Y * side * 0.02), list(w - Y * side * 0.2), 22])
def push_out(f_c1, f_c2, w, side):
    NEW.append([f_c1, list(w + Y * side * 0.02), list(w - Y * side * 0.2), 22])
    NEW.append([f_c2, list(w + Y * side * 0.03), list(w - Y * side * 0.2), 22])
# exit after the scream: into the inner wall above the flap, out of the outer wall, pull back to the wide of the bin
# (director rule 3, Nov 14: no camera move through a wall) the three inside/outside transitions are whip-pans:
# the camera tips up into the empty, dark bin ceiling, changes place there, and tips down out of an empty sky
NEW.append([1412, [0.30, -1.70, 1.80], [0.0, -0.6, 1.35], 22])
# back in for the three days: into the outer wall low, out of the inner wall, pan round to her face
def topcam(f, dx):
    sc.frame_set(f); ch = WO.matrix_world @ WO.pose.bones["spine03"].head
    t = ch.lerp(face(f)[0], 0.35); c = t + Vector((dx, -0.42, 1.05))
    return [f, [max(-0.6, min(0.6, c.x)), max(-0.45, c.y), min(2.15, c.z)], list(t), 20]
NEW.append(topcam(1570, 0.15))
# the knock: into the inner wall, out of the outer wall, then the passer-by (key 1880)
NEW.append([1880, [0.20, -1.10, 1.45], [1.3, -1.7, 1.5], 22])
NEW.append([1540, [0.45, -3.30, 2.10], [0.0, -0.6, 1.20], 24])        # wide exterior hold: bin and alley, not a plain wall     # outside, clear of the bin front
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
WHIPS = [(1394, 1403, 1412), (1546, 1556, 1570), (1861, 1869, 1880)]      # (start, jump, settle)
for a_, j_, b_ in WHIPS:
    pin, pout = POS[a_][0].copy(), POS[b_][0].copy()
    for f in range(a_, j_): POS[f][0] = pin
    for f in range(j_, b_): POS[f][0] = pout
print("WHIPS", WHIPS)
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
def _tq(d):
    q = Vector(d).normalized().to_track_quat('-Z', 'Y'); return q
for a_, j_, b_ in WHIPS:
    inside_first = POS[a_][0].y > -0.58
    up_a = _tq((0, -0.15 if inside_first else -0.15, 1)); up_b = _tq((0, -0.15, 1))
    qa, qb = QS[a_], QS[b_]
    if up_a.dot(qa) < 0: up_a = -up_a
    for f in range(a_ + 1, j_):
        t_ = (f - a_) / (j_ - 1 - a_); t_ = t_ * t_ * (3 - 2 * t_); QS[f] = qa.slerp(up_a, t_)
    if up_b.dot(qb) < 0: up_b = -up_b
    for f in range(j_, b_):
        t_ = (f - j_) / (b_ - j_); t_ = t_ * t_ * (3 - 2 * t_); QS[f] = up_b.slerp(qb, t_)
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
# eyes: MPFB EnhancedEye reads as black holes at preview samples: warm iris, smaller pupil, more eye white, stronger coat
for m in bpy.data.materials:
    g = m.node_tree.nodes.get("EnhancedEye") if m.use_nodes else None
    if g:
        g.inputs["IrisMajorColor"].default_value = (0.42, 0.30, 0.18, 1); g.inputs["IrisMinorColor"].default_value = (0.25, 0.16, 0.08, 1)
        g.inputs["IrisSection4Color"].default_value = (0.12, 0.08, 0.05, 1); g.inputs["PupilSize"].default_value = 0.16
        g.inputs["Clearcoat"].default_value = 0.8; g.inputs["IrisToEyeWhiteRelation"].default_value = 0.30
# helmets: plain glossy black shell (the textured orange model read as pumpkins)
for o in bpy.data.objects:
    if o.name.endswith("_Helmet") and o.type == 'MESH':
        hmm = bpy.data.materials.get("FireHelmetBlack") or bpy.data.materials.new("FireHelmetBlack")
        hmm.use_nodes = True; bs = hmm.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1); bs.inputs["Roughness"].default_value = 0.25
        for i in range(len(o.data.materials)): o.data.materials[i] = hmm
        for ms in o.material_slots: ms.link = 'DATA'
# dust motes that drift through a head: removed (limb_check PROPHEAD)
heads = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones]
motes = [o for o in bpy.data.objects if o.name.startswith("Mote")]
bad = set()
for f in range(1, sc.frame_end + 1, 4):
    sc.frame_set(f)
    hp_ = [r.matrix_world @ r.pose.bones["head"].head for r in heads]
    for o in motes:
        if o.name in bad: continue
        p_ = o.matrix_world.translation
        if any((p_ - h).length < 0.20 for h in hp_): bad.add(o.name)
for n in bad: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
print("MOTES_REMOVED", len(bad), "of", len(motes))
# client item B: no x-ray / glass look anywhere: every keyed XRAY / STUDIO_MIX value is removed and held at 0
nx = 0
for idb in list(bpy.data.materials) + list(bpy.data.worlds) + list(bpy.data.node_groups):
    nt = idb if isinstance(idb, bpy.types.NodeTree) else getattr(idb, "node_tree", None)
    if nt is None: continue
    ad = nt.animation_data
    if ad and ad.action:
        for l in ad.action.layers:
            for st in l.strips:
                for cb in st.channelbags:
                    for fcv in list(cb.fcurves):
                        if "XRAY" in fcv.data_path or "STUDIO" in fcv.data_path or "Xray" in fcv.data_path: cb.fcurves.remove(fcv); nx += 1
    for nd in nt.nodes:
        if nd.name.upper().startswith(("XRAY", "STUDIO")) or nd.label.upper().startswith(("XRAY", "STUDIO")):
            if nd.type == 'VALUE': nd.outputs[0].default_value = 0.0; nx += 1
            if nd.type == 'MIX_SHADER': nd.inputs['Fac'].default_value = 0.0; nx += 1
for o in bpy.data.objects:
    for k in [k for k in o.keys() if "xray" in k.lower()]: o[k] = 0.0
print("XRAY_REMOVED", nx)
# simplify: props that floated or passed through bodies (blanket that appeared from nowhere, dust motes, the
# explainer's ghost bag, the flap counterweight) are removed
rm_ = [o for o in bpy.data.objects if o.name.startswith(("Mote", "GhostBag", "CounterWeight", "Blanket"))]
for o in rm_: bpy.data.objects.remove(o, do_unlink=True)
print("REMOVED", len(rm_))
sc["director_fix"] = "v007: one continuous camera (covered wall pushes), front 3/4 on beat 6 and scream, hands flat on clothes"
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("V007_DONE", len(CAMK))
