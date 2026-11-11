"""Hand audit (client rule, Nov 11 23:00): BVH overlap every N frames of
hand vs other hand, hand vs own torso/head, hand vs other character. Depth > 4 mm counts.
blender -b film.blend --python hand_audit.py -- report.txt [step]"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; DEPTH = 0.004
SEEN = {"Inventor": [(1, 1150), (1160, 1700), (1720, 2100)], "Mentor": [(1160, 1700), (1880, 2100)]}
def groups(body, me, prefixes):
    idx = {g.index for g in body.vertex_groups if g.name.startswith(prefixes)}
    out = set()
    for v in me.vertices:
        w = sum(g.weight for g in v.groups if g.group in idx)
        if w > 0.5: out.add(v.index)
    return out
INFO = {}
sc.frame_set(1); dg0 = bpy.context.evaluated_depsgraph_get()
for hn in ("Inventor", "Mentor"):
    body = bpy.data.objects[hn + ".body"]
    me = body.evaluated_get(dg0).to_mesh()
    hand = {s: groups(body, me, tuple(["wrist." + s] + ["finger%d-%d.%s" % (k, j, s) for k in range(1, 6) for j in range(1, 4)])) for s in "LR"}
    torso = groups(body, me, ("spine", "neck", "head", "breast", "clavicle", "pelvis", "root", "jaw", "special", "oris", "levator", "risorius", "orbicularis", "oculi", "temporalis", "eye"))
    tf = [tuple(p.vertices) for p in me.polygons if all(v in torso for v in p.vertices)]
    hf = {s: [tuple(p.vertices) for p in me.polygons if all(v in hand[s] for v in p.vertices)] for s in "LR"}
    allf = [tuple(p.vertices) for p in me.polygons]
    body.evaluated_get(dg0).to_mesh_clear()
    INFO[hn] = (body, hand, tf, hf, allf)
    print("GROUPS", hn, {s: len(hand[s]) for s in "LR"}, len(tf))
def inside(tree, p):
    # open sub-meshes (hand / torso cut out of the body): only a short, plausible depth counts as penetration
    loc, nrm, i, d = tree.find_nearest(p, 0.015)
    return loc is not None and (p - loc).dot(nrm) < 0 and d > DEPTH, d
counts = {}; frames = {}
def hit(k, f, d):
    counts[k] = counts.get(k, 0) + 1; frames.setdefault(k, []).append(f)
for f in range(1, 2101, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    cur = {}
    for hn, (body, hand, tf, hf, allf) in INFO.items():
        if not any(x <= f <= y for x, y in SEEN[hn]): continue
        be = body.evaluated_get(dg); me = be.to_mesh(); mw = be.matrix_world
        co = [mw @ v.co for v in me.vertices]; be.to_mesh_clear()
        cur[hn] = (co, BVHTree.FromPolygons(co, tf), {s: BVHTree.FromPolygons(co, hf[s]) for s in "LR"}, hand,
                   BVHTree.FromPolygons(co, allf))
    for hn, (co, tt, ht, hand, whole) in cur.items():
        for s in "LR":
            o = "R" if s == "L" else "L"
            pts = [co[i] for i in list(hand[s])[::3]]
            # skip fingertips touching the wrist area of the same hand
            if any(inside(tt, p)[0] for p in pts): hit("%s hand.%s inside own torso/head" % (hn, s), f, 0)
            if s == "L" and any(inside(ht[o], p)[0] for p in pts): hit("%s hand.L inside hand.R" % hn, f, 0)
            for on, oc in cur.items():
                if on != hn and any(inside(oc[4], p)[0] for p in pts): hit("%s hand.%s inside %s" % (hn, s, on), f, 0)
lines = ["Hand audit every %d frames (penetration %.0f-15 mm; open sub-mesh test)" % (STEP, DEPTH * 1000)]
for k in sorted(counts): lines.append("%-46s %4d frames: %s" % (k, counts[k], " ".join(map(str, frames[k][:30]))))
lines.append("TOTAL flagged samples: %d" % sum(counts.values()))
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
