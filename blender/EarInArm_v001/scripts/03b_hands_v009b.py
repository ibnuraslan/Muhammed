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
wrist_follow("L", 158, 278); wrist_follow("L", 534, 562); wrist_follow("R", 534, 560); wrist_follow("L", 1390, 1498)

# ---------------------------------------------------------------- tool hand: surgeon R pinches the forceps shafts (grip_object)
def grip_forceps(f):
    sc.frame_set(f); C = FORC.matrix_world @ Vector((0, 0.04, 0))
    rep = grip_object(SUR, "R", f, FORC, C, (C - wrist(SUR, "R")).normalized(), grip="pinch")
    LOG.append(("forceps", f, rep))
FORC_F = sorted(set(list(range(100, 337, 12)) + [336] + list(range(572, 1500, 12)) + [1498]))
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
    p, n = surf(TEE, tip + Vector((0.11, -0.02, 0.07)))
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
lock(SUR, "L", 1380); lock(SUR, "L", 1506)
for f in range(1392, 1500, 12):
    sc.frame_set(f); H = PAT.matrix_world @ PAT.pose.bones["head"].matrix
    up = (H.to_3x3() @ Vector((0, 1, 0))).normalized(); c = PAT.matrix_world @ PAT.pose.bones["head"].tail
    p, n = surf(BODY[PAT], c + up * 0.02 + (wrist(SUR, "L") - c).normalized() * 0.05)
    place_hand(SUR, "L", f, p, -n, up - n * up.dot(n), skin=0.013); apply_pose(SUR, "L", "flat_palm", f)

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
JOBS = [(PAT, "R", range(13, 44, 6), lambda: others(PAT) + [lambda: self_bvh(PAT)], 0.03), (SUR, "L", range(1, 50, 3), lambda: [lambda: bvh(BODY[PAT])], 0.06), (SUR, "R", range(1, 50, 3), lambda: [lambda: bvh(BODY[PAT])], 0.06),
        (SUR, "L", range(265, 300, 3), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(265, 300, 3), lambda: [lambda: self_bvh(SUR)], 0.04),
        (SUR, "L", range(637, 664, 3), lambda: others(SUR)), (SUR, "R", range(637, 664, 3), lambda: others(SUR), 0.04),
        (SUR, "L", range(562, 600, 3), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(562, 600, 3), lambda: [lambda: self_bvh(SUR)]),
        (SUR, "L", range(673, 716, 6), lambda: others(SUR)), (SUR, "R", range(673, 716, 6), lambda: others(SUR)),
        (SUR, "L", range(1357, 1397, 3), lambda: [lambda: self_bvh(SUR)] + others(SUR)), (SUR, "R", range(1357, 1397, 3), lambda: [lambda: self_bvh(SUR)]),
        (SUR, "L", range(1405, 1466, 6), lambda: others(SUR)), (SUR, "R", range(1405, 1466, 6), lambda: others(SUR), 0.035),
        (SUR, "L", range(139, 284, 6), lambda: others(SUR)), (SUR, "R", range(139, 284, 6), lambda: others(SUR), 0.04),
        (PAT, "L", range(1705, 1771, 6), lambda: [lambda: self_bvh(PAT)])]
for job in JOBS:
    rig, s, frs, tg = job[:4]; cap = job[4] if len(job) > 4 else 0.2
    for f in frs:
        m = unclip(rig, s, f, tg(), cap=cap); LOG.append(("unclip", rig.name, s, f, round(m, 3)))
# re-bake the forceps (and what rides in it) from the final hand, so the closed pinch stays on the shafts
from mathutils import Matrix
def R_(d): return math.radians(d)
CARRY = OB.get("Chest_Piece_Carry"); EAR_ARM = OB["Ear_InArm"]
def keymat(o, f, M):
    o.matrix_world = M; o.keyframe_insert("location", frame=f); o.keyframe_insert("rotation_euler", frame=f)
for f in [f for f in range(1, 1501, 2) if f <= 337 or 566 <= f <= 1500]:
    sc.frame_set(f)
    Rw = (SUR.matrix_world @ SUR.pose.bones["wrist.R"].matrix).to_3x3().normalized().to_4x4(); PP = Matrix.Translation(pinch_pt(SUR, "R"))
    keymat(FORC, f, PP @ Rw @ Matrix.Translation((0, -0.04, 0)))
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
