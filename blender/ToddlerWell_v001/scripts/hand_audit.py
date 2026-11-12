"""Hand audit (client rule, Nov 11): BVH overlap every <step> frames of
  hand vs other hand, hand vs own torso/head/clothes, hand vs other characters.
Hands = body faces whose verts are weighted mostly to finger/metacarpal bones (the wrist cuff is excluded).
blender -b film.blend --python hand_audit.py -- out.json [step] [f0] [f1]"""
import sys, json
import bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
F0 = int(a[2]) if len(a) > 2 else sc.frame_start; F1 = int(a[3]) if len(a) > 3 else sc.frame_end
CH = ["Toddler", "Teen", "ResA", "ResB", "ResC", "Mother", "Crowd1", "Operator"]
for n in CH:          # audit on the base cage (subdivision off) for speed
    for ch in bpy.data.objects[n].children:
        for m in ch.modifiers:
            if m.type in ("SUBSURF", "MASK"): m.show_viewport = False
def groups(body):
    bones = set(b.name for b in body.parent.data.bones)
    gi = {g.index: g.name for g in body.vertex_groups if g.name in bones}
    hand = {"L": set(), "R": set()}; arm = set()
    for v in body.data.vertices:
        best = max((g for g in v.groups if g.group in gi), key=lambda g: g.weight, default=None)
        if best is None: continue
        nm = gi.get(best.group, "")
        if nm.startswith(("finger", "metacarpal")) and best.weight > 0.4: hand[nm[-1]].add(v.index)
        if nm.startswith(("upperarm", "lowerarm", "wrist", "finger", "metacarpal", "shoulder", "clavicle")): arm.add(v.index)
    return hand, arm
INFO = {}
for n in CH:
    body = [c for c in bpy.data.objects[n].children if c.name.endswith(".body")][0]
    INFO[n] = (body,) + groups(body)
def bvh_of(o, dg, keep=None, drop=None):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    if (keep or drop) and len(me.vertices) != len(o.data.vertices):
        e.to_mesh_clear(); return None
    co = [M @ v.co for v in me.vertices]
    polys = [p.vertices[:] for p in me.polygons
             if (keep is None or all(i in keep for i in p.vertices)) and (drop is None or not any(i in drop for i in p.vertices))]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(co, polys) if polys else None
CLOTH_KEYS = ("suit", "vest", "short0", "long0", "bob0", "ponytail")
hits = []; counts = {"hand_hand": 0, "hand_self": 0, "hand_other": 0}
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    H = {}; SELF = {}; FULL = {}
    for n in CH:
        rig = bpy.data.objects[n]
        if (rig.matrix_world @ rig.pose.bones["root"].head).length > 14 and n != "Operator": continue
        body, hand, arm = INFO[n]
        H[n] = {s: bvh_of(body, dg, keep=hand[s]) for s in "LR"}
        cl = [bvh_of(c, dg) for c in rig.children if c.type == "MESH" and not c.hide_render and any(k in c.name for k in CLOTH_KEYS)]
        SELF[n] = [bvh_of(body, dg, drop=arm)] + cl
        FULL[n] = [bvh_of(body, dg)] + cl
    for n, hs in H.items():
        if hs["L"] and hs["R"] and hs["L"].overlap(hs["R"]):
            hits.append([f, n, "L-R", "hand-hand"]); counts["hand_hand"] += 1
        for s, hb in hs.items():
            if not hb: continue
            if any(t and hb.overlap(t) for t in SELF[n]):
                hits.append([f, n, s, "self"]); counts["hand_self"] += 1
            for m, ts in FULL.items():
                if m != n and any(t and hb.overlap(t) for t in ts):
                    hits.append([f, n, s, "other:" + m]); counts["hand_other"] += 1
json.dump({"step": STEP, "frames": [F0, F1], "counts": counts, "hits": hits}, open(OUT, "w"), indent=0)
print("HANDAUDIT", counts, len(hits))
