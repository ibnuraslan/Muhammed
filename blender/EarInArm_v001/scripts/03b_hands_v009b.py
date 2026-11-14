# v009b hand pass (director review of v009). Runs on work/anim.blend after 03_animate.py, before 04_camera_fx.py.
# Every hand contact goes through pipeline/hand_poses.py: grip_object (tools, cartilage), place_hand (flat palms on skin,
# tray, armrest) and apply_pose. A final unclip pass keeps every visible hand vertex >= 1 cm off the bodies it nears.
import bpy, sys, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; OB = bpy.data.objects
SUR, PAT, NUR = OB["Surgeon"], OB["Patient"], OB["Nurse"]
BODY = {r: OB[r.name + ".body"] for r in (SUR, PAT, NUR)}
TEE = OB["Patient.male_casualsuit06"]; FORC = OB["Forceps"]; EAR_TRAY = OB["Ear_Cartilage"]; EAR_NEW = OB["Ear_New"]
def mesh_of(o):
    if o.type == 'MESH': return o
    return max((c for c in o.children_recursive if c.type == 'MESH'), key=lambda c: len(c.data.vertices))
TRAY = mesh_of(OB["Tray"]); ARMREST = OB["Chair_Arm0"]
FAST = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        for m in o.modifiers:
            if m.type in ('SUBSURF', 'SHRINKWRAP', 'DISPLACE', 'BEVEL', 'SOLIDIFY', 'MASK', 'MULTIRES'):
                FAST.append((m, m.show_viewport)); m.show_viewport = False

def bvh(obj):
    dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me = ev.to_mesh(); mw = obj.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); ev.to_mesh_clear(); return t
def surf(obj, guess):
    loc, nrm, _, _ = bvh(obj).find_nearest(Vector(guess), 2.0); return loc, nrm.normalized()
def ikloc(rig, s):
    return rig.matrix_world @ rig.pose.bones["IK_hand." + s].matrix.translation
def lock(rig, s, f):
    """key IK hand + fingers at f with their current values (keeps the original motion outside an edited range)"""
    sc.frame_set(f); pb = rig.pose.bones["IK_hand." + s]
    pb.keyframe_insert("location", frame=f, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
    for k in range(1, 6):
        for j in (1, 2, 3):
            b = rig.pose.bones["finger%d-%d.%s" % (k, j, s)]; b.keyframe_insert("rotation_quaternion", frame=f, group=b.name)
def wrist(rig, s): return rig.matrix_world @ rig.pose.bones["wrist." + s].head
def pinch_pt(rig, s):
    P = rig.pose.bones; return rig.matrix_world @ ((P["finger1-3." + s].tail + P["finger2-3." + s].tail) / 2)
LOG = []
# the surgeon's wrists normally follow the forearm (v006 glove fix); for flat-palm contacts the hand orientation must follow
# place_hand, so the wrist copy-rotation is faded in only inside those windows
def wrist_follow(s, f0, f1, ramp=8):
    c = SUR.pose.bones["wrist." + s].constraints[0]
    for f, v in ((f0 - ramp, 0.0), (f0, 1.0), (f1, 1.0), (f1 + ramp, 0.0)):
        c.influence = v; c.keyframe_insert("influence", frame=f)
wrist_follow("L", 158, 278); wrist_follow("L", 534, 562); wrist_follow("R", 534, 560); wrist_follow("L", 1390, 1650)

# ---------------------------------------------------------------- tool hand: surgeon R pinches the forceps shafts (grip_object)
def grip_forceps(f):
    sc.frame_set(f); C = FORC.matrix_world @ Vector((0, 0.04, 0))
    rep = grip_object(SUR, "R", f, FORC, C, (C - wrist(SUR, "R")).normalized(), grip="pinch")
    LOG.append(("forceps", f, rep))
FORC_F = sorted(set(list(range(100, 337, 12)) + [336] + [f for f in range(572, 1500, 12) if not 784 <= f <= 1062] + [1498]))   # v009d: not while he waits with the hand at his side
lock(SUR, "R", 90)
for f in FORC_F: grip_forceps(f)
# grip_object places the hand on the shafts; in the chest and head beats the fingers are then set to the full pinch
# (the forceps is re-baked to this pinch point at the end, so thumb and index close on it)
for f in FORC_F:
    if f <= 337: apply_pose(SUR, "R", "pinch", f)
    elif f >= 1300: apply_pose(SUR, "R", "pinch", f, amount=0.8)

# ---------------------------------------------------------------- 1. chest x-ray: L flat on the chest beside the forceps
for f in (146, 290): lock(SUR, "L", f)
for f in range(158, 280, 12):
    sc.frame_set(f); tip = FORC.matrix_world @ Vector((0, 0.13, 0))
    p, n = surf(TEE, tip + Vector((0.17, -0.01, 0.11)))   # v009d: further onto his upper-left chest, clear of the forceps hand
    place_hand(SUR, "L", f, p, -n, Vector((0, 0, 1)) - n * n.z, skin=0.014); apply_pose(SUR, "L", "flat_palm", f)
apply_pose(SUR, "L", "relaxed", 290)

# ---------------------------------------------------------------- 2. over the tray (9.0-9.5 s): L pinches the carved ear, R flat on the tray edge
for f in (528, 570): lock(SUR, "L", f)
lock(SUR, "R", 528)
for f in range(536, 566, 6):
    sc.frame_set(f); pp = pinch_pt(SUR, "L"); p, n = surf(EAR_TRAY, pp)
    rep = grip_object(SUR, "L", f, EAR_TRAY, p, (p - wrist(SUR, "L")).normalized(), grip="pinch"); LOG.append(("ear", f, rep))
    sc.frame_set(f); p, n = surf(TRAY, wrist(SUR, "R") + Vector((0, 0, -0.08)))
    sh_ = SUR.matrix_world @ SUR.pose.bones["upperarm01.R"].head; fd = p - sh_; fd.z = 0
    place_hand(SUR, "R", f, p, Vector((0, 0, -1)), fd.normalized(), skin=0.012)
    apply_pose(SUR, "R", "flat_palm", f)
apply_pose(SUR, "L", "relaxed", 576)

# ---------------------------------------------------------------- 5. ear placement: L flat on the scalp above the ear
lock(SUR, "L", 1380); lock(SUR, "L", 1662)
for f in range(1392, 1652, 12):
    sc.frame_set(f); H = PAT.matrix_world @ PAT.pose.bones["head"].matrix
    up = (H.to_3x3() @ Vector((0, 1, 0))).normalized(); c = PAT.matrix_world @ PAT.pose.bones["head"].tail
    p, n = surf(BODY[PAT], c + up * 0.02 + (wrist(SUR, "L") - c).normalized() * 0.05)
    place_hand(SUR, "L", f, p, -n, up - n * up.dot(n), skin=0.013); apply_pose(SUR, "L", "flat_palm", f)

# ---------------------------------------------------------------- v009d: during the growing beat the surgeon's free left hand
# hangs relaxed at his side (it floated palm-up by the arm for ~5 s, and later filled the x-ray macro)
lock(SUR, "L", 784); lock(SUR, "L", 1062); lock(SUR, "R", 784); lock(SUR, "R", 1062)
def hang(s_, f, side_sign):
    sc.frame_set(f); shL = SUR.matrix_world @ SUR.pose.bones["upperarm01.L"].head; shR = SUR.matrix_world @ SUR.pose.bones["upperarm01.R"].head
    right = shR - shL; right.z = 0; right.normalize(); fwd = Vector((0, 0, 1)).cross(right)
    sh_ = shR if s_ == "R" else shL
    W = sh_ + right * (0.06 * side_sign) + fwd * 0.1 + Vector((0, 0, -0.56))
    pb = SUR.pose.bones["IK_hand." + s_]; d_ = SUR.matrix_world.inverted() @ W - (SUR.matrix_world.inverted() @ (SUR.matrix_world @ pb.head))
    pb.location = pb.location + SUR.data.bones["IK_hand." + s_].matrix_local.to_3x3().inverted() @ d_
    pb.keyframe_insert("location", frame=f, group=pb.name)
for f in range(796, 1052, 32): hang("R", f, 1.0)   # the forceps hand waits at his side too (it rose into the x-ray camera)
for f in range(796, 1052, 32):
    sc.frame_set(f); shL = SUR.matrix_world @ SUR.pose.bones["upperarm01.L"].head; shR = SUR.matrix_world @ SUR.pose.bones["upperarm01.R"].head
    right = shR - shL; right.z = 0; right.normalize(); fwd = Vector((0, 0, 1)).cross(right)
    W = shL - right * 0.06 + fwd * 0.08 + Vector((0, 0, -0.58))
    pb = SUR.pose.bones["IK_hand.L"]; d_ = SUR.matrix_world.inverted() @ W - (SUR.matrix_world.inverted() @ (SUR.matrix_world @ pb.head))
    pb.location = pb.location + SUR.data.bones["IK_hand.L"].matrix_local.to_3x3().inverted() @ d_
    pb.keyframe_insert("location", frame=f, group=pb.name)
# ---------------------------------------------------------------- 6. patient's free (right) hand relaxed on the armrest while reclined
lock(PAT, "R", 468)
for f in list(range(480, 1640, 40)) + [1640]:
    sc.frame_set(f); p, n = surf(ARMREST, wrist(PAT, "R") + Vector((0, 0, -0.05)))
    top = ARMREST.matrix_world.to_3x3() @ Vector((0, 0, 1))
    fd = (ARMREST.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
    place_hand(PAT, "R", f, p, -top.normalized(), fd, skin=0.014); apply_pose(PAT, "R", "relaxed", f)
lock(PAT, "R", 1660)

# ---------------------------------------------------------------- 4. nurse: relaxed at her sides (the dish rides on her forearms; no finger contact claimed)
for s in "LR":
    for f in (700, 1000, 1308): apply_pose(NUR, s, "relaxed", f)

# ---------------------------------------------------------------- v009c: no starfish gloves
# finger limits back to the table in hand_poses.py (z = side +-10), then every surgeon / nurse finger key is replaced by a clean
# schedule of hand_poses with spread = 0 (pinch on the forceps, relaxed on the tray, flat_palm on chest / scalp)
for rig in (SUR, PAT, NUR):
    for pb in rig.pose.bones:
        c = pb.constraints.get("HandLimit")
        if not c: continue
        lim = LIMITS["wrist"] if pb.name.startswith("wrist") else LIMITS["thumb"] if pb.name.startswith("finger1") else LIMITS["finger"]
        for ax, (lo, hi) in zip("xyz", lim): setattr(c, "min_" + ax, math.radians(lo)); setattr(c, "max_" + ax, math.radians(hi))
def fcurves_of(obj):
    ad = obj.animation_data; act = ad.action
    if hasattr(act, "fcurves"): return act.fcurves
    from bpy_extras import anim_utils
    return anim_utils.action_get_channelbag_for_slot(act, ad.action_slot).fcurves
def clear_fingers(rig):
    fcs = fcurves_of(rig)
    for fc in [fc for fc in fcs if fc.data_path.startswith('pose.bones["finger')]: fcs.remove(fc)
# EarInArm-local pose variants in the hand_poses table: the three back fingers tucked evenly under a pinch, and an even relaxed
# curl, so the gloved fingers lie together instead of pointing in different directions
POSES["pinch_tuck"] = dict(curl={2: (40, 45, 25), 3: (45, 55, 30), 4: (52, 62, 36), 5: (58, 68, 40)}, spread=0.0, thumb=("index_tip", 0.004))
POSES["relaxed_even"] = dict(curl={2: (24, 30, 16), 3: (26, 32, 17), 4: (28, 34, 18), 5: (30, 36, 19)}, spread=0.0, thumb=("beside_index", 0.012))
# v009c-2: the "starfish" gloves were the GloveThin displace (hand surface pulled in 3.2 mm along its normals): on the subdivided
# glove it thinned every finger and opened gaps between them. Removed; the bones and skinning were correct.
for rig in (SUR,):
    gm = BODY[rig].modifiers.get("GloveThin")
    if gm: BODY[rig].modifiers.remove(gm)
SCHED = {(SUR, "R"): [(1, "pinch_tuck"), (339, "pinch_tuck"), (343, "cup_hold"), (464, "cup_hold"), (472, "relaxed_even"), (560, "relaxed_even"), (566, "pinch_tuck"),
                      (1500, "pinch_tuck"), (1502, "pinch_tuck"), (1685, "pinch_tuck"), (1715, "relaxed_even"), (1770, "relaxed_even")],
         (SUR, "L"): [(1, "relaxed_even"), (96, "relaxed_even"), (106, "flat_palm"), (278, "flat_palm"), (290, "relaxed_even"), (337, "relaxed_even"), (343, "pinch_tuck"),
                      (464, "pinch_tuck"), (476, "relaxed_even"), (1385, "relaxed_even"), (1392, "flat_palm"), (1498, "flat_palm"), (1508, "relaxed_even"), (1770, "relaxed_even")],
         (NUR, "L"): [(1, "relaxed_even"), (1770, "relaxed_even")], (NUR, "R"): [(1, "relaxed_even"), (1770, "relaxed_even")]}
for rig in (SUR, NUR): clear_fingers(rig)
for (rig, s_), sch in SCHED.items():
    for i, (f, pose) in enumerate(sch):
        apply_pose(rig, s_, pose, f, spread=0)
        if i + 1 < len(sch) and sch[i + 1][1] == pose:          # same pose held: extra keys so the thumb solve follows the hand frame
            for g in range(f + 60, sch[i + 1][0] - 20, 60): apply_pose(rig, s_, pose, g, spread=0)
# f1-45: the surgeon stands 10 cm further back from the patient's knee (his hip met the patient's resting left hand)
sc.frame_set(52); rb = SUR.pose.bones["root"]; rb.keyframe_insert("location", frame=52, group="root")
for f in range(1, 46, 4):
    sc.frame_set(f); rb.location = rb.location + SUR.data.bones["root"].matrix_local.to_3x3().inverted() @ (SUR.matrix_world.inverted().to_3x3() @ (Vector((0.63, -0.78, 0)).normalized() * 0.10))
    rb.keyframe_insert("location", frame=f, group="root")
# (the patient's own hand path is unchanged)
# v009d: the patient's hand on the new ear is relaxed (cup_hold read as a claw)
for f in (1715, 1745, 1770): apply_pose(PAT, "L", "relaxed_even", f, spread=0)
lock(PAT, "L", 1); lock(PAT, "L", 42)
for f, w in ((5, 0.5), (11, 1.0), (18, 1.0), (24, 1.0), (30, 1.0), (36, 0.5)):
    sc.frame_set(f); pb = PAT.pose.bones["IK_hand.L"]; off = Vector((0, 0, 0))
    pb.location = pb.location + PAT.data.bones["IK_hand.L"].matrix_local.to_3x3().inverted() @ (PAT.matrix_world.inverted().to_3x3() @ off)
    pb.keyframe_insert("location", frame=f, group=pb.name)

# ---------------------------------------------------------------- 7/8. unclip: every hand vertex >= 1 cm off skin it nears (bodies + clothes)
ARMK = ("hand", "finger", "metacarpal", "thumb", "palm")
def hand_verts(rig, s):
    body = BODY[rig]; gi = {g.index: g.name for g in body.vertex_groups}; bones = {b.name for b in rig.data.bones}; out = []
    for v in body.data.vertices:
        gs = [g for g in v.groups if gi.get(g.group) in bones]
        if not gs: continue
        n = gi[max(gs, key=lambda g: g.weight).group].lower()
        if n.endswith("." + s.lower()) and any(k in n for k in ARMK): out.append(v.index)
    return out
HV = {(r, s): hand_verts(r, s) for r in (SUR, PAT) for s in "LR"}
SELF_T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "thigh", "calf", "foot", "toe", "root", "eye", "ear", "nose", "lip", "oris", "brow", "cheek", "temporal", "tongue", "levator", "risorius", "special", "orbicularis", "glute")
SKIPK = ("lowerarm", "wrist", "upperarm", "clavicle", "shoulder", "deltoid", "breast", "pectoral", "scapula")
_SELFK = {}
def self_keep(rig):          # same classes as pipeline/clip_scan.py (dominant bone group, helpers excluded)
    if rig in _SELFK: return _SELFK[rig]
    body = BODY[rig]; bones = {b.name for b in rig.data.bones}; gi = {g.index: g.name for g in body.vertex_groups}
    helper = {i for i, n in gi.items() if n.lower().startswith(("helper", "joint")) or n in ("HelperGeometry", "JointCubes")}
    keep = set()
    for v in body.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): continue
        gs = [g for g in v.groups if gi.get(g.group) in bones]
        if not gs: continue
        n = gi[max(gs, key=lambda g: g.weight).group].lower()
        if any(k in n for k in SKIPK) or any(k in n for k in ("hand", "finger", "metacarpal", "thumb", "palm")): continue
        if any(k in n for k in SELF_T): keep.add(v.index)
    _SELFK[rig] = keep; return keep
def self_bvh(rig):
    keep = self_keep(rig); body = BODY[rig]
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons if all(i in keep for i in p.vertices)]); ev.to_mesh_clear(); return t
def unclip(rig, s, f, targets, margin=0.01, it=6, cap=0.2):
    pb = rig.pose.bones["IK_hand." + s]; moved = 0.0
    for _ in range(it):
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); ev = BODY[rig].evaluated_get(dg); me = ev.to_mesh()
        mw = BODY[rig].matrix_world; P = [mw @ me.vertices[i].co for i in HV[(rig, s)]]; ev.to_mesh_clear()
        T = [t() if callable(t) else t for t in targets]; push = Vector(); worst = 0.0
        for t in T:
            for p in P:
                loc, nrm, _, d = t.find_nearest(p, 0.1)
                if loc is None: continue
                sd = d if (p - loc).dot(nrm) >= 0 else -d
                if sd < margin and margin - sd > worst: worst = margin - sd; push = nrm.normalized() * (margin - sd + 0.002)
        if worst <= 0.0005 or moved >= cap: break
        d_ = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ (rig.matrix_world.inverted().to_3x3() @ push)
        pb.location = pb.location + d_; pb.keyframe_insert("location", frame=f, group=pb.name); moved += push.length
    return moved
def others(rig): return [lambda o=o: bvh(o) for o in (SUR, PAT, NUR) if o is not rig for o in (BODY[o],)]
JOBS = [(PAT, "L", range(120, 200, 4), lambda: [lambda: self_bvh(PAT)], 0.08), (PAT, "R", range(120, 200, 4), lambda: [lambda: self_bvh(PAT)], 0.08),
        (SUR, "L", range(268, 340, 3), lambda: [lambda: self_bvh(SUR)], 0.06), (SUR, "R", range(268, 340, 3), lambda: [lambda: self_bvh(SUR)], 0.06),
        (SUR, "L", range(566, 664, 3), lambda: [lambda: self_bvh(SUR)], 0.06), (SUR, "R", range(566, 664, 3), lambda: [lambda: self_bvh(SUR)], 0.06),
        (SUR, "L", range(478, 520, 3), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(478, 520, 3), lambda: [lambda: self_bvh(SUR)]),
        (PAT, "R", range(13, 44, 6), lambda: others(PAT) + [lambda: self_bvh(PAT)], 0.03), (SUR, "L", range(1, 50, 3), lambda: [lambda: bvh(BODY[PAT])], 0.06), (SUR, "R", range(1, 50, 3), lambda: [lambda: bvh(BODY[PAT])], 0.06),
        (SUR, "L", range(265, 300, 3), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(265, 300, 3), lambda: [lambda: self_bvh(SUR)], 0.04),
        (SUR, "L", range(637, 664, 3), lambda: others(SUR)), (SUR, "R", range(637, 664, 3), lambda: others(SUR), 0.04),
        (SUR, "L", range(562, 600, 3), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(562, 600, 3), lambda: [lambda: self_bvh(SUR)]),
        (SUR, "L", range(673, 716, 6), lambda: others(SUR)), (SUR, "R", range(673, 716, 6), lambda: others(SUR)),
        (SUR, "L", range(1357, 1397, 3), lambda: [lambda: self_bvh(SUR)] + others(SUR)), (SUR, "R", range(1357, 1397, 3), lambda: [lambda: self_bvh(SUR)]),
        (SUR, "L", range(1405, 1494, 6), lambda: others(SUR)), (SUR, "R", range(1405, 1494, 3), lambda: others(SUR), 0.035),
        (SUR, "L", range(139, 284, 6), lambda: others(SUR)), (SUR, "R", range(139, 284, 6), lambda: others(SUR), 0.04),
        (PAT, "L", range(1705, 1771, 6), lambda: [lambda: self_bvh(PAT)])]
for job in JOBS:
    rig, s, frs, tg = job[:4]; cap = job[4] if len(job) > 4 else 0.2
    for f in frs:
        m = unclip(rig, s, f, tg(), cap=cap); LOG.append(("unclip", rig.name, s, f, round(m, 3)))
# v009d: stitching, solved on the final pose: at every stitch key the pinch sits 10.8 cm back from the stitch along his reach,
# so the needle holder (re-baked below along shoulder -> pinch) puts its needle on the stitch; between stitches it lifts 3 cm
NH = OB["NeedleHolder"]
def sh_pt(): return SUR.matrix_world @ SUR.pose.bones["upperarm01.R"].head
def stitch_w(i):   # hidden objects are not evaluated: build the world point from the head bone (bone parent, identity inverse)
    o = OB["Stitch%d" % i]; hb = PAT.pose.bones["head"]
    return (PAT.matrix_world @ hb.matrix @ Matrix.Translation((0, hb.length, 0)) @ o.matrix_basis).translation
for i in range(9):
    for f, lift in ((1505 + i * 15, 0.0), (1513 + i * 15, 0.03)):
        for _ in range(14):
            sc.frame_set(f - 1); sc.frame_set(f); st = stitch_w(i) + Vector((0, 0, lift))
            dsp = (st - sh_pt()).normalized(); want = st - dsp * 0.108; err = want - pinch_pt(SUR, "R")
            if err.length < 0.003: break
            pb = SUR.pose.bones["IK_hand.R"]
            pb.location = pb.location + SUR.data.bones["IK_hand.R"].matrix_local.to_3x3().inverted() @ (SUR.matrix_world.inverted().to_3x3() @ (err * 0.5))   # damped: the pinch swings with the forearm
            pb.keyframe_insert("location", frame=f, group=pb.name); sc.frame_set(f - 1); sc.frame_set(f); bpy.context.view_layer.update()
        LOG.append(("stitch", i, f, round(err.length, 3)))
def nh_held():
    pp_ = pinch_pt(SUR, "R"); dsp = (pp_ - sh_pt()).normalized()
    Y = -dsp; X = Y.cross(Vector((0, 0, 1))); X = X.normalized() if X.length > 1e-4 else Vector((1, 0, 0)); Z = X.cross(Y)
    M = Matrix((X, Y, Z)).transposed().to_4x4(); M.translation = pp_ + dsp * 0.03
    return M
for f in range(1501, 1687, 2):   # same (odd) frames as the bake in 03_animate.py, so the keys replace it
    sc.frame_set(f); NH.matrix_world = nh_held(); NH.keyframe_insert("location", frame=f); NH.keyframe_insert("rotation_euler", frame=f)
# re-bake the forceps (and what rides in it) from the final hand, so the closed pinch stays on the shafts
from mathutils import Matrix
def R_(d): return math.radians(d)
CARRY = OB.get("Chest_Piece_Carry"); EAR_ARM = OB["Ear_InArm"]
def keymat(o, f, M):
    o.matrix_world = M; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
for f in [f for f in range(1, 1501, 2) if f <= 331 or 566 <= f <= 1500]:
    sc.frame_set(f)
    Rw = (SUR.matrix_world @ SUR.pose.bones["wrist.R"].matrix).to_3x3().normalized().to_4x4(); PP = Matrix.Translation(pinch_pt(SUR, "R"))
    keymat(FORC, f, PP @ Rw @ Matrix.Rotation(math.radians(FORC.get("tilt_deg", 0.0)), 4, 'X') @ Matrix.Translation((0, -0.04, 0)))
    tip = FORC.matrix_world @ Vector((0, 0.13, 0)); Rf = FORC.matrix_world.to_quaternion().to_matrix().to_4x4()
    if CARRY and 255 <= f <= 335:
        sc_ = CARRY.matrix_world.to_scale()[0]; keymat(CARRY, f, Matrix.Translation(tip) @ FORC.matrix_world.to_3x3().normalized().to_4x4() @ Matrix.Scale(sc_, 4))
    if 566 <= f < 712:
        keymat(EAR_ARM, f, Matrix.Translation(tip) @ Rf @ Matrix.Translation((0, 0.03, 0)) @ Matrix.Rotation(R_(-90), 4, 'X') @ Matrix.Scale(0.85, 4))
    if 1150 <= f < 1440:
        keymat(EAR_NEW, f, Matrix.Translation(tip) @ Rf @ Matrix.Translation((0, 0.03, 0)) @ Matrix.Rotation(R_(-90), 4, 'X') @ Matrix.Scale(1.0, 4))
for m, v in FAST: m.show_viewport = v
for l in LOG: print("HANDS", l)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HANDS_DONE")
