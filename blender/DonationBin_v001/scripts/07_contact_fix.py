"""Hand contact pass (director QA "HOVER"): a hand that is within 12 cm of a prop must touch it.
Runs after 05_look_hands. blender -b look.blend --python 07_contact_fix.py -- out.blend
For every frame where a visible-or-not hand's wrist is within 12 cm of a prop (same prop list and order as
pipeline/qa_check.py) but no fingertip is within 1.2 cm, the IK_hand control is keyed so that the closest
fingertip lands 3 mm off the surface. The original IK curve is sampled densely around each fix so nothing
else moves. Her palms on the bin walls and the flap use the shared library (pipeline/hand_poses.py): place_hand plus
the flat_palm pose; everything else (bags, the cutter) gets the IK nudge. Floating dust motes, sparks and the hidden x-ray bag are not props and are skipped."""
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
exec(open("/home/user/Muhammed/blender/pipeline/hand_poses.py").read())
RIGS = [bpy.data.objects[n] for n in ("Woman", "FireA", "FireB", "Passerby", "Shover") if n in bpy.data.objects]
CHAR = set(c.name for r in RIGS for c in r.children_recursive if c.type == 'MESH')
ALLRIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones]
CHAR |= set(c.name for r in ALLRIGS for c in r.children_recursive if c.type == 'MESH')
PROPS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in CHAR and len(o.data.polygons) < 200000
         and not any(k in o.name.lower() for k in ("ground", "floor", "terrain", "sky", "backdrop", "water", "ocean", "pile", "heap"))]
SKIP = ("Mote", "Spark", "GhostBag")
WALLS = ("BinLiner", "BinShell", "Flap", "CutPanel", "StopBar", "HingePin", "Spring")
for r in RIGS: add_hand_limits(r)
GAP = 0.003

def W(r, b, tail=False):
    pb = r.pose.bones[b]; return r.matrix_world @ (pb.tail if tail else pb.head)
def tips(r, s):
    return [W(r, "finger%d-3.%s" % (i, s), True) for i in range(1, 6)] + [W(r, "finger3-1." + s)]
def bvh(o, dg):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); mw = o.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]) if me.polygons else None
    ev.to_mesh_clear(); return t
def need(r, s, dg, cache):
    """world correction for this hand at the current frame, or None"""
    w = W(r, "wrist." + s)
    for o in PROPS:
        if (o.matrix_world.translation - w).length > 3.0: continue
        if o.name not in cache: cache[o.name] = bvh(o, dg)
        t = cache[o.name]
        if t is None or t.find_nearest(w, 0.12)[0] is None: continue
        if o.name.startswith(SKIP): return None              # QA stops at the first prop near the wrist
        best = None
        for p in tips(r, s):
            loc, n, i, d = t.find_nearest(p, 0.3)
            if loc is not None and (best is None or d < best[0]): best = (d, p, loc)
        if best is None or best[0] <= 0.010: return None
        d, p, loc = best
        return ((loc - p) * (1.0 - GAP / d), o.name, t)
    return None

def scan(frames):
    out = {}
    for f in frames:
        sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cache = {}
        for r in RIGS:
            for s in "LR":
                c = need(r, s, dg, cache)
                if c is not None: out[(r.name, s, f)] = c
    return out

STEP = 2
FR = list(range(sc.frame_start, sc.frame_end + 1, STEP))
fix = scan(FR)
print("CONTACT pass1", len(fix))
# group per hand, dense anchors of the original curves (IK_hand + fingers) around every fixed frame
per = {}
for (rn, s, f) in fix: per.setdefault((rn, s), set()).add(f)
for (rn, s), fs in per.items():
    r = bpy.data.objects[rn]; names = ["IK_hand." + s] + _chain(s)
    keyf = set()
    for f in fs:
        for g in range(f - 8, f + 9, STEP):
            if sc.frame_start <= g <= sc.frame_end: keyf.add(g)
    orig = {}
    for g in sorted(keyf):
        sc.frame_set(g); orig[g] = {n: (r.pose.bones[n].location.copy(), r.pose.bones[n].rotation_quaternion.copy()) for n in names}
    for g, d in orig.items():
        for n, (lv, qv) in d.items():
            pb = r.pose.bones[n]; pb.location = lv; pb.rotation_quaternion = qv
            if n.startswith("IK"): pb.keyframe_insert("location", frame=g, group=n)
            pb.keyframe_insert("rotation_quaternion", frame=g, group=n)
# palms on the walls / flap: flat_palm + place_hand from the shared library
nflat = 0
for (rn, s, f), (c, on, t) in list(fix.items()):
    if rn != "Woman" or not on.startswith(WALLS): continue
    r = bpy.data.objects[rn]; sc.frame_set(f)
    wr = W(r, "wrist." + s); mid = W(r, "finger3-1." + s); palm = wr.lerp(mid, 0.6)
    loc, nrm, i_, d_ = t.find_nearest(palm, 0.4)
    if loc is None: continue
    n = (loc - palm).normalized() if (loc - palm).length > 1e-4 else -nrm
    up = Vector((0, 0, 1)); fd = up - n * up.dot(n)
    if fd.length < 0.3: fd = (mid - wr) - n * (mid - wr).dot(n)
    place_hand(r, s, f, loc, n, fd.normalized(), skin=0.006)
    apply_pose(r, s, "flat_palm", f); nflat += 1
print("CONTACT flat_palm keys", nflat)
fix = scan(sorted(set(k[2] for k in fix)))
print("CONTACT after flat", len(fix))
for it in range(3):
    for (rn, s, f), (c, on, t) in fix.items():
        r = bpy.data.objects[rn]; pb = r.pose.bones["IK_hand." + s]
        sc.frame_set(f)
        M = pb.matrix.copy(); M.translation += r.matrix_world.inverted().to_3x3() @ c
        pb.matrix = M; pb.keyframe_insert("location", frame=f, group=pb.name)
    fix = scan(sorted(set(k[2] for k in fix)))
    print("CONTACT iter", it, "left", len(fix))
    if not fix: break
for k in sorted(fix): print("CONTACT_LEFT", k, fix[k][1], round(fix[k][0].length * 100, 1), "cm")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CONTACT_DONE")
