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
            if m.type in ('SUBSURF', 'SHRINKWRAP', 'DISPLACE', 'BEVEL', 'SOLIDIFY', 'MASK'):
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
wrist_follow("L", 108, 278); wrist_follow("L", 534, 562); wrist_follow("R", 534, 560); wrist_follow("L", 1390, 1498)

# ---------------------------------------------------------------- tool hand: surgeon R pinches the forceps shafts (grip_object)
def grip_forceps(f):
    sc.frame_set(f); C = FORC.matrix_world @ Vector((0, 0.04, 0))
    rep = grip_object(SUR, "R", f, FORC, C, (C - wrist(SUR, "R")).normalized(), grip="pinch")
    LOG.append(("forceps", f, rep))
FORC_F = sorted(set(list(range(100, 337, 12)) + [336] + list(range(572, 1500, 12)) + [1498]))
lock(SUR, "R", 90)
for f in FORC_F: grip_forceps(f)

# ---------------------------------------------------------------- 1. chest x-ray: L flat on the chest beside the forceps
for f in (90, 290): lock(SUR, "L", f)
for f in range(110, 280, 12):
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
def self_bvh(rig):
    body = BODY[rig]; gi = {g.index: g.name for g in body.vertex_groups}
    keep = set(); T = ("head", "neck", "jaw", "spine", "pelvis", "upperleg", "lowerleg", "foot", "root", "eye", "ear", "nose", "lip", "oris", "brow", "cheek", "temporal", "glute")
    for v in body.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda g: g.weight); n = gi.get(g.group, "").lower()
            if any(k in n for k in T) and not n.startswith(("helper", "joint")): keep.add(v.index)
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh(); mw = body.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons if all(i in keep for i in p.vertices)]); ev.to_mesh_clear(); return t
def unclip(rig, s, f, targets, margin=0.01, it=6):
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
        if worst <= 0.0005: break
        d_ = rig.data.bones["IK_hand." + s].matrix_local.to_3x3().inverted() @ (rig.matrix_world.inverted().to_3x3() @ push)
        pb.location = pb.location + d_; pb.keyframe_insert("location", frame=f, group=pb.name); moved += push.length
    return moved
def others(rig): return [lambda o=o: bvh(o) for o in (SUR, PAT, NUR) if o is not rig for o in (BODY[o],)]
JOBS = [(PAT, "R", range(13, 44, 6), lambda: others(PAT)),
        (SUR, "L", range(565, 596, 6), lambda: [lambda: self_bvh(SUR)]), (SUR, "R", range(565, 596, 6), lambda: [lambda: self_bvh(SUR)]),
        (SUR, "L", range(673, 716, 6), lambda: others(SUR)), (SUR, "R", range(673, 716, 6), lambda: others(SUR)),
        (SUR, "L", range(1357, 1394, 6), lambda: [lambda: self_bvh(SUR)] + others(SUR)), (SUR, "R", range(1357, 1394, 6), lambda: [lambda: self_bvh(SUR)] + others(SUR)),
        (SUR, "L", range(1405, 1466, 6), lambda: others(SUR)), (SUR, "R", range(1405, 1466, 6), lambda: others(SUR)),
        (PAT, "L", range(1705, 1771, 6), lambda: [lambda: self_bvh(PAT)])]
for rig, s, frs, tg in JOBS:
    for f in frs:
        m = unclip(rig, s, f, tg()); LOG.append(("unclip", rig.name, s, f, round(m, 3)))
for m, v in FAST: m.show_viewport = v
for l in LOG: print("HANDS", l)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("HANDS_DONE")
