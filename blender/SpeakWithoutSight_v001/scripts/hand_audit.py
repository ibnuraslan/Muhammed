"""Hand audit (client rule, Nov 11 23:00). Every STEP frames, for each character and hand, count hand-surface vertices deeper
than DEPTH inside: (a) the other hand of the same character, (b) its own torso/head/clothes (surface away from the arms),
(c) any other character (body + clothes). Classification is spatial on the evaluated meshes (MPFB masks change topology):
hand vertices = body vertices nearest the hand bones; torso = polygons whose centre is > 7 cm from every arm bone.
blender -b anim.blend --python hand_audit.py -- <report.txt> [step] [depth_m]"""
import sys
import bpy
from mathutils import Vector
from mathutils.geometry import intersect_point_line
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2; DEPTH = float(a[2]) if len(a) > 2 else 0.005
sc = bpy.context.scene
CH = ["Girl", "Teacher", "Mother", "Father"]
def segs(rig, names):
    out = []
    for n in names:
        pb = rig.pose.bones.get(n)
        if pb: out.append((rig.matrix_world @ pb.head, rig.matrix_world @ pb.tail))
    return out
def dseg(p, sg):
    best = 9.0
    for a_, b_ in sg:
        q, t = intersect_point_line(p, a_, b_); t = max(0.0, min(1.0, t)); best = min(best, (p - (a_ + (b_ - a_) * t)).length)
    return best
HAND = lambda s: ["wrist." + s] + ["finger%d-%d.%s" % (k, j, s) for k in range(1, 6) for j in range(1, 4)] + ["metacarpal%d.%s" % (k, s) for k in range(1, 5)]
ARM = lambda s: ["upperarm01." + s, "upperarm02." + s, "lowerarm01." + s, "lowerarm02." + s]
def evald(ob):
    dg = bpy.context.evaluated_depsgraph_get(); eo = ob.evaluated_get(dg); me = eo.to_mesh()
    vs = [eo.matrix_world @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]
    eo.to_mesh_clear(); return vs, ps
def inside(tr, pts):
    n = 0
    for v in pts:
        loc, nrm, idx, dist = tr.find_nearest(v, 0.04)
        if loc is not None and (v - loc).dot(nrm) < 0 and dist > DEPTH: n += 1
    return n
hits = {}; lines = []
FR = [int(x) for x in a[3].split(',')] if len(a) > 3 else list(range(sc.frame_start, sc.frame_end + 1, STEP))
for f in FR:
    sc.frame_set(f)
    M = {}
    for c in CH:
        rig = bpy.data.objects[c]
        meshes = [o for o in rig.children if o.type == 'MESH' and not o.hide_render and (o.name.endswith(".body") or "suit" in o.name or "skirt" in o.name)]
        allv, allp = [], []
        for o in meshes:
            vs, ps = evald(o); off = len(allv); allv += vs; allp += [tuple(i + off for i in p) for p in ps]
        bv, bp = evald(bpy.data.objects[c + ".body"])
        hs = {s: segs(rig, HAND(s)) for s in "LR"}; arm_s = segs(rig, ARM("L") + ARM("R") + HAND("L") + HAND("R"))
        wr = {s: rig.matrix_world @ rig.pose.bones["wrist." + s].head for s in "LR"}
        hand_pts = {}; hand_polys = {}
        for s in "LR":
            near = [i for i, v in enumerate(bv) if (v - wr[s]).length < 0.22 and dseg(v, hs[s]) < 0.035]
            hand_pts[s] = [bv[i] for i in near]; ns = set(near)
            hand_polys[s] = [p for p in bp if all(i in ns for i in p)]
        torso = [p for p in allp if dseg(sum((allv[i] for i in p), Vector()) / len(p), arm_s) > 0.07]
        M[c] = dict(allv=allv, allp=allp, hand_pts=hand_pts, hand_polys=hand_polys, bv=bv, torso=torso)
    for c in CH:
        D = M[c]
        t_own = BVHTree.FromPolygons(D["allv"], D["torso"]) if D["torso"] else None
        for s in "LR":
            pts = D["hand_pts"][s]
            if not pts: continue
            o = "R" if s == "L" else "L"
            t_hh = BVHTree.FromPolygons(D["bv"], D["hand_polys"][o]) if D["hand_polys"][o] else None
            if len(a) > 3: print("DBG", f, c, s, "pts", len(pts), "otherpolys", len(D["hand_polys"][o]), "wr", tuple(round(x, 2) for x in pts[0]))
            res = {"own_body_or_clothes": inside(t_own, pts) if t_own else 0, "other_hand": inside(t_hh, pts) if t_hh else 0, "other_character": 0}
            for c2 in CH:
                if c2 == c: continue
                if min((v - pts[0]).length for v in M[c2]["allv"][::50]) > 0.5: continue
                res["other_character"] += inside(BVHTree.FromPolygons(M[c2]["allv"], M[c2]["allp"]), pts)
            for k, n in res.items():
                if n > 8:
                    hits.setdefault((c, s, k), []).append(f)
                    lines.append("f%d %s hand.%s %s: %d verts > %.0f mm" % (f, c, s, k, n, DEPTH * 1000))
total = sum(len(v) for v in hits.values())
summ = {"%s hand.%s vs %s" % k: (len(v), "%d-%d" % (min(v), max(v))) for k, v in hits.items()}
open(OUT, "w").write("HAND AUDIT every %d frames, depth %.0f mm (flag = more than 8 hand vertices deeper)\nflagged samples: %d\n%s\n\n%s\n" %
                     (STEP, DEPTH * 1000, total, "\n".join("%s: %d samples, frames %s" % (k, n, r) for k, (n, r) in summ.items()), "\n".join(lines)))
print("HAND_AUDIT", total, summ)
