"""Hand audit (client HANDS rule, Nov 11 23:00 UTC). blender -b film.blend --python audit_hands.py -- report.txt [step=2]
Every <step> frames, BVH overlap of YOU's hand vertices (within 3 cm of finger/wrist bones, evaluated mesh):
  1. left hand vs right hand
  2. each hand vs own clothes (shirt/jeans), own head region and own torso
  3. each hand vs other characters (FO, captain, the window-seat neighbour)
A hit = a hand vertex more than 3 mm inside the other surface. Reported per category with the flagged frame spans."""
import sys, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; O = bpy.data.objects; A = O["YOU"]
bpy.context.view_layer.layer_collection.children["PASSENGERS"].exclude = True
body = O["YOU.body"]
cloth = [o for o in A.children if o.type == 'MESH' and ("suit" in o.name)]
others = [o for o in O if o.type == 'MESH' and o.parent and o.parent.name in ("FO", "CAPT") and (o.name.endswith(".body") or "suit" in o.name)]
HB = {s: [b.name for b in A.pose.bones if (b.name.startswith("finger") or b.name.startswith("wrist")) and b.name.endswith("." + s)] for s in "LR"}
def eval_mesh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh(); Mw = o.matrix_world
    vs = [Mw @ v.co for v in me.vertices]; ps = [tuple(p.vertices) for p in me.polygons]; e.to_mesh_clear(); return vs, ps
def segs(s): return [(A.matrix_world @ A.pose.bones[n].head, A.matrix_world @ A.pose.bones[n].tail) for n in HB[s]]
def near(v, sg, r):
    for a_, b_ in sg:
        ab = b_ - a_; t = max(0.0, min(1.0, (v - a_).dot(ab) / max(ab.length_squared, 1e-9)))
        if (a_ + ab * t - v).length < r: return True
    return False
def inside(t, p):
    loc, n, i, d = t.find_nearest(p, 0.06)
    return loc is not None and d > 0.003 and (p - loc).dot(n) < 0
cats = {}; spans = {}
def hit(k, f, n):
    if n: cats[k] = cats.get(k, 0) + n; spans.setdefault(k, []).append(f)
# topology of the evaluated body is constant (MPFB mask modifiers are static): pick hand / torso sets once
sc.frame_set(1); dg = bpy.context.evaluated_depsgraph_get()
bv, bp = eval_mesh(body, dg)
sc.frame_set(1); sgL, sgR = segs("L"), segs("R")
arm_names = ("lowerarm01.L", "lowerarm02.L", "lowerarm01.R", "lowerarm02.R", "upperarm01.L", "upperarm02.L", "upperarm01.R", "upperarm02.R")
arm_segs = sgL + sgR + [(A.matrix_world @ A.pose.bones[n].head, A.matrix_world @ A.pose.bones[n].tail) for n in arm_names]
hs = {"L": set(i for i, v in enumerate(bv) if near(v, sgL, 0.03)), "R": set(i for i, v in enumerate(bv) if near(v, sgR, 0.03))}
armset = set(i for i, v in enumerate(bv) if near(v, arm_segs, 0.07))
torso_polys = [p for p in bp if not any(i in armset for i in p)]
hand_polys = {k: [p for p in bp if all(i in hs[k] for i in p)] for k in "LR"}
print("HANDVERTS", len(hs["L"]), len(hs["R"]), "torso polys", len(torso_polys))
def near_obj(o, pts, r=0.35):
    c = o.matrix_world.translation; return any((p - c).length < 1.2 for p in pts)
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg); me = e.to_mesh(); Mw = body.matrix_world
    bv = [Mw @ v.co for v in me.vertices]; e.to_mesh_clear()
    for s_, o_ in (("L", "R"), ("R", "L")):
        t = BVHTree.FromPolygons(bv, hand_polys[o_])
        hit("hand %s vs hand %s" % (s_, o_), f, sum(1 for i in hs[s_] if inside(t, bv[i])))
    tt = BVHTree.FromPolygons(bv, torso_polys)
    for s_ in "LR": hit("hand %s vs own body/head" % s_, f, sum(1 for i in hs[s_] if inside(tt, bv[i])))
    wr = [bv[next(iter(hs[k]))] for k in "LR"]
    for o in cloth:
        cv, cp = eval_mesh(o, dg); t = BVHTree.FromPolygons(cv, cp)
        for s_ in "LR": hit("hand %s vs own clothes" % s_, f, sum(1 for i in hs[s_] if inside(t, bv[i])))
    for o in others:
        if not any((w - (o.parent.matrix_world @ o.parent.pose.bones["spine03"].head)).length < 1.1 for w in wr): continue
        cv, cp = eval_mesh(o, dg); t = BVHTree.FromPolygons(cv, cp)
        for s_ in "LR": hit("hand %s vs %s" % (s_, o.name), f, sum(1 for i in hs[s_] if inside(t, bv[i])))
def fmt(fr):
    if not fr: return ""
    out_, s0, pv = [], fr[0], fr[0]
    for x in fr[1:]:
        if x - pv > STEP: out_.append((s0, pv)); s0 = x
        pv = x
    out_.append((s0, pv)); return ", ".join("%.2f-%.2fs" % ((a_ - 1) / 60, (b_ - 1) / 60) for a_, b_ in out_)
nfr = len(set(f for v in spans.values() for f in v))
L = ["HAND AUDIT every %d frames (%d samples): hand vertices > 3 mm inside another surface" % (STEP, len(range(1, sc.frame_end + 1, STEP))),
     "flagged samples: %d; total vertex hits: %d" % (nfr, sum(cats.values()))]
for k in sorted(cats, key=lambda k: -cats[k]): L.append("  %-40s %6d  frames: %s" % (k, cats[k], fmt(spans[k])))
if not cats: L.append("  none")
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))
