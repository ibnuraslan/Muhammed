"""Hand audit (client rule, Nov 11 23:00): BVH overlap of each hand vs the other hand, vs its own torso/head
(body + clothes), and vs other characters. blender -b final.blend --python 07_hand_audit.py -- <report> [step]"""
import sys, collections, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
HAND = {s: ("wrist." + s, "finger", "metacarpal") for s in "LR"}
TORSO = ("spine", "clavicle", "neck", "head", "pelvis", "root", "breast", "jaw", "eye", "orbicularis", "levator", "oris", "temporalis", "special", "tongue")
RIGS = [o for o in bpy.data.objects if o.type == 'ARMATURE']
for r in RIGS:
    for ch in r.children:
        for m in ch.modifiers:
            if m.type == 'SUBSURF': m.show_viewport = False
def tree(o, dg, pref=None, side=None):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); M = o.matrix_world
    keep = None
    if pref:
        gi = set()
        for g in o.vertex_groups:
            nm = g.name
            if any(nm.startswith(p) for p in pref) and (side is None or nm.endswith("." + side) or not (nm.endswith(".L") or nm.endswith(".R")) or nm.startswith("wrist")):
                if side and nm.startswith("finger") and not nm.endswith("." + side): continue
                gi.add(g.index)
        keep = {v.index for v in me.vertices if any(g.group in gi and g.weight > 0.5 for g in v.groups)}
    vs = [M @ v.co for v in me.vertices]
    ps = [tuple(p.vertices) for p in me.polygons if keep is None or all(i in keep for i in p.vertices)]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps) if ps else None
hits = collections.Counter(); first = {}; n_frames = 0
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); n_frames += 1
    live = [r for r in RIGS if (r.matrix_world @ r.pose.bones["root"].head).z > -40 and bpy.data.objects.get(r.name + ".body")]
    T = {}
    for r in live:
        body = bpy.data.objects[r.name + ".body"]
        clothes = [c for c in r.children if c.type == 'MESH' and any(k in c.name for k in ("suit", "worksuit"))]
        T[r.name] = dict(L=tree(body, dg, HAND["L"], "L"), R=tree(body, dg, HAND["R"], "R"), torso=tree(body, dg, TORSO),
                         clothes=[tree(c, dg, TORSO) for c in clothes], whole=tree(body, dg))
    for n, t in T.items():
        tests = []
        if t["L"] and t["R"]: tests.append(("hand L vs hand R", t["L"], t["R"]))
        for s in "LR":
            if not t[s]: continue
            if t["torso"]: tests.append(("hand %s vs own torso/head" % s, t[s], t["torso"]))
            for ct in t["clothes"]:
                if ct: tests.append(("hand %s vs own clothes (torso)" % s, t[s], ct))
            for m, u in T.items():
                if m != n and u["whole"]: tests.append(("hand %s vs %s" % (s, m), t[s], u["whole"]))
        for lab, x, y in tests:
            k = len(x.overlap(y))
            if k:
                key = (n, lab); hits[key] += 1; first.setdefault(key, f)
lines = ["Hand audit: %d frames (every %d), overlapping-frame counts" % (n_frames, STEP), "TOTAL flagged frame-events: %d" % sum(hits.values())]
lines += ["  %4d  %s %s (first f%d)" % (v, k[0], k[1], first[k]) for k, v in hits.most_common()]
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines[:30])); print("HAND_AUDIT_DONE")
