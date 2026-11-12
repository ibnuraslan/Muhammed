"""BVH hand audit (STYLE_ANIMATED.md "Hands"): every <step> frames, for each visible character:
  - hand vs other hand (finger/knuckle/wrist points of one hand inside the other hand's skin region)
  - hand vs own torso/head skin and clothes (points inside, depth > 1 cm)
  - hand vs other characters' bodies (points inside, depth > 1 cm)
blender -b look.blend --python hand_audit.py -- <report.txt> [step] [f0] [f1]"""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
F0 = int(a[2]) if len(a) > 2 else 1; F1 = int(a[3]) if len(a) > 3 else sc.frame_end
NAMES = ("Woman", "Shover", "Passerby", "FireA", "FireB")
HANDG = ("wrist", "finger", "metacarpal")
TORSOG = ("spine01", "spine02", "spine03", "spine04", "spine05", "breast", "pelvis", "neck01", "neck02", "neck03", "head", "clavicle", "root")
def hand_pts(rig, s):
    P = rig.pose.bones; M = rig.matrix_world; pts = []
    for i in range(1, 6):
        for j in (1, 2, 3):
            n = "finger%d-%d.%s" % (i, j, s)
            if n in P: pts.append(M @ P[n].tail)
    pts.append(M @ P["wrist." + s].head)
    return pts
def region_bvh(obj, groups, dg):
    """BVH of the evaluated mesh faces whose vertices are all weighted to the given bone groups"""
    ev = obj.evaluated_get(dg); me = ev.to_mesh()
    gi = {g.index for g in obj.vertex_groups if g.name.split(".")[0].startswith(groups)}
    ok = set()
    for v in me.vertices:
        if sum(g.weight for g in v.groups if g.group in gi) > 0.5: ok.add(v.index)
    verts = [obj.matrix_world @ v.co for v in me.vertices]
    polys = [list(p.vertices) for p in me.polygons if all(i in ok for i in p.vertices)]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys) if polys else None
def inside(bvh, p, depth=0.01):
    if bvh is None: return False
    loc, nrm, idx, d = bvh.find_nearest(p)
    return loc is not None and (p - loc).dot(nrm) < 0 and d > depth and d < 0.08
for n in NAMES:      # audit on the base cage so vertex groups map 1:1
    for md in bpy.data.objects[n + '.body'].modifiers:
        if md.type == 'SUBSURF': md.show_viewport = False
hits = []; counts = {}
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    vis = [n for n in NAMES if not bpy.data.objects[n].hide_render]
    torso = {}; full = {}; handb = {}
    for n in vis:
        body = bpy.data.objects[n + ".body"]
        torso[n] = region_bvh(body, TORSOG, dg)
    for n in vis:
        rig = bpy.data.objects[n]
        H = {s: hand_pts(rig, s) for s in "LR"}
        # hand vs hand: any fingertip of one hand within 8 mm of a fingertip/knuckle of the other
        dmin = min((p - q).length for p in H["L"] for q in H["R"])
        if dmin < 0.008:
            hits.append((f, n, "hand-hand", dmin)); counts[(n, "hand-hand")] = counts.get((n, "hand-hand"), 0) + 1
        for s in "LR":
            if any(inside(torso[n], p) for p in H[s]):
                hits.append((f, n, "hand%s-own-torso" % s, 0)); counts[(n, "own-torso")] = counts.get((n, "own-torso"), 0) + 1
            for m in vis:
                if m == n: continue
                if (rig.matrix_world @ rig.pose.bones["root"].head - bpy.data.objects[m].matrix_world @ bpy.data.objects[m].pose.bones["root"].head).length > 1.6: continue
                if any(inside(torso[m], p) for p in H[s]):
                    hits.append((f, n, "hand%s-in-%s" % (s, m), 0)); counts[(n, "other-" + m)] = counts.get((n, "other-" + m), 0) + 1
lines = ["HAND AUDIT step %d frames %d-%d" % (STEP, F0, F1), "TOTAL %d" % len(hits), "BY " + repr(counts)]
lines += ["f%4d %-8s %s %.3f" % h for h in hits]
open(OUT, "w").write("\n".join(lines) + "\n")
print("HANDAUDIT", len(hits), counts)
