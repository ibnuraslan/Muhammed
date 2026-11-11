"""Hand audit (client hands rule): BVH overlaps every 2 frames + joint-range check.
blender -b film.blend --python 08_hand_audit.py -- <report.txt>"""
import sys, math, bpy
from mathutils.bvhtree import BVHTree
OUT = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene
C = bpy.data.objects["Composer"]; body = bpy.data.objects["Composer.body"]; suit = bpy.data.objects["Composer.male_elegantsuit01"]
for o in (body, suit):   # audit on the cage mesh: stable vertex indices, fast
    for m in o.modifiers:
        if m.type in ('SUBSURF', 'MASK'): m.show_viewport = False
BONES = set(b.name for b in C.data.bones)
def dominant(o):
    """dominant BONE group per vertex; helper/joint-cube geometry (masked in render) -> ''"""
    names = {g.index: g.name for g in o.vertex_groups}; dom = []
    helper = {i for i, n in names.items() if n in ("HelperGeometry", "JointCubes")}
    for v in o.data.vertices:
        if any(g.group in helper and g.weight > 0.5 for g in v.groups): dom.append(""); continue
        bg = [g for g in v.groups if names.get(g.group) in BONES]
        best = max(bg, key=lambda g: g.weight, default=None); dom.append(names[best.group] if best else "")
    return dom
HANDB = lambda n, s: n.endswith("." + s) and (n.startswith(("wrist", "finger", "metacarpal")))
ARMB = lambda n: n.startswith(("wrist", "finger", "metacarpal", "lowerarm", "upperarm", "shoulder", "clavicle"))
db, ds = dominant(body), dominant(suit)
def polys(o, dom, pred):
    return [p.index for p in o.data.polygons if all(pred(dom[i]) for i in p.vertices)]
SETS = {"hand.L": (body, polys(body, db, lambda n: HANDB(n, "L"))), "hand.R": (body, polys(body, db, lambda n: HANDB(n, "R"))),
        "torso_head": (body, polys(body, db, lambda n: n and not ARMB(n))), "clothes": (suit, polys(suit, ds, lambda n: n and not ARMB(n)))}
print("SETS", {k: len(v[1]) for k, v in SETS.items()})
def tree(o, idx, dg):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); M = o.matrix_world
    vs = [M @ v.co for v in me.vertices]; ps = [tuple(me.polygons[i].vertices) for i in idx]
    t = BVHTree.FromPolygons(vs, ps); ev.to_mesh_clear(); return t
hits = {}; frames = 0
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); frames += 1
    T = {k: tree(o, idx, dg) for k, (o, idx) in SETS.items()}
    for a, b in (("hand.L", "hand.R"), ("hand.L", "torso_head"), ("hand.R", "torso_head"), ("hand.L", "clothes"), ("hand.R", "clothes")):
        if T[a].overlap(T[b]): hits.setdefault(a + " x " + b, []).append(f)
# joint range: finger local curl must not go backward, no sideways twist beyond 12 deg
def local(pb):
    b = pb.bone; rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
    return ((pb.parent.matrix @ rest_rel).inverted() @ pb.matrix).to_euler('XYZ')
bad = []
for f in range(1, sc.frame_end + 1, 10):
    sc.frame_set(f)
    for s in "LR":
        for k in range(2, 6):
            for j in range(1, 4):
                e = local(C.pose.bones["finger%d-%d.%s" % (k, j, s)])
                if math.degrees(e.x) < -2 or abs(math.degrees(e.z)) > 12: bad.append((f, "finger%d-%d.%s" % (k, j, s), round(math.degrees(e.x)), round(math.degrees(e.z))))
        w = local(C.pose.bones["wrist." + s])
        if abs(math.degrees(w.x)) > 62 or abs(math.degrees(w.z)) > 27: bad.append((f, "wrist." + s, round(math.degrees(w.x)), round(math.degrees(w.z))))
        el = local(C.pose.bones["lowerarm01." + s])
        if math.degrees(el.x) < -2: bad.append((f, "elbow." + s, round(math.degrees(el.x))))
L = ["HAND AUDIT: %d frames checked (every 2nd frame); BVH overlap on the cage mesh" % frames]
L += ["  %s: %d frames %s" % (k, len(v), v[:12]) for k, v in sorted(hits.items())] or ["  overlaps: 0"]
L.append("  total overlap frames: %d" % sum(len(v) for v in hits.values()))
L.append("JOINT RANGE (every 10th frame): %d violations %s" % (len(bad), bad[:10]))
open(OUT, "w").write("\n".join(L) + "\n"); print("\n".join(L)); print("HANDAUDIT_DONE")
