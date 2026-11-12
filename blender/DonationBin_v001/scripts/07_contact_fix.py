"""Hand contact pass (director QA "HOVER"): a hand that is within 12 cm of a prop must touch it.
Runs after 05_look_hands. blender -b look.blend --python 07_contact_fix.py -- out.blend
For every frame where a visible-or-not hand's wrist is within 12 cm of a prop (same prop list and order as
pipeline/qa_check.py) but no fingertip is within 1.2 cm, the IK_hand control is keyed so that the closest
fingertip lands 3 mm off the surface. The original IK curve is sampled densely around each fix so nothing
else moves. Floating dust motes, sparks and the hidden x-ray bag are not props and are skipped."""
import sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
RIGS = [bpy.data.objects[n] for n in ("Woman", "FireA", "FireB", "Passerby", "Shover") if n in bpy.data.objects]
CHAR = set(c.name for r in RIGS for c in r.children_recursive if c.type == 'MESH')
ALLRIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE' and "head" in o.pose.bones and "finger2-1.L" in o.pose.bones]
CHAR |= set(c.name for r in ALLRIGS for c in r.children_recursive if c.type == 'MESH')
PROPS = [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in CHAR and len(o.data.polygons) < 200000
         and not any(k in o.name.lower() for k in ("ground", "floor", "terrain", "sky", "backdrop", "water", "ocean", "pile", "heap"))]
SKIP = ("Mote", "Spark", "GhostBag")
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
        return (loc - p) * (1.0 - GAP / d)
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
# group per hand, dense anchors of the original curve around every fixed frame
per = {}
for (rn, s, f) in fix: per.setdefault((rn, s), set()).add(f)
for (rn, s), fs in per.items():
    r = bpy.data.objects[rn]; pb = r.pose.bones["IK_hand." + s]
    keyf = set()
    for f in fs:
        for g in range(f - 8, f + 9, STEP):
            if sc.frame_start <= g <= sc.frame_end: keyf.add(g)
    orig = {}
    for g in sorted(keyf):
        sc.frame_set(g); orig[g] = pb.location.copy()
    for g, v in orig.items():
        pb.location = v; pb.keyframe_insert("location", frame=g, group=pb.name)
for it in range(3):
    for (rn, s, f), c in fix.items():
        r = bpy.data.objects[rn]; pb = r.pose.bones["IK_hand." + s]
        sc.frame_set(f)
        M = pb.matrix.copy(); M.translation += r.matrix_world.inverted().to_3x3() @ c
        pb.matrix = M; pb.keyframe_insert("location", frame=f, group=pb.name)
    fix = scan(sorted(set(k[2] for k in fix)))
    print("CONTACT iter", it, "left", len(fix))
    if not fix: break
for k in sorted(fix): print("CONTACT_LEFT", k, round(fix[k].length * 100, 1), "cm")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("CONTACT_DONE")
