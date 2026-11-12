"""BVH hand audit (client, Nov 11 23:00 UTC), every 2 frames:
  hand vs other hand, hand vs own torso/head/neck (+ shirt), hand vs other characters' bodies.
blender -b anim.blend --python hand_audit.py -- report.txt [step] [f0] [f1]
Regions come from the dominant vertex group of each face (vertex groups = bone names on MPFB meshes).
A hit = BVH overlap between triangle sets. Fingertips touching the face/nose on purpose still count (they penetrate if overlapping)."""
import sys, collections, bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene
F0 = int(a[2]) if len(a) > 2 else sc.frame_start; F1 = int(a[3]) if len(a) > 3 else sc.frame_end
HAND = ("wrist", "finger", "metacarpal")
TORSO = ("spine", "neck", "head", "breast", "pelvis", "clavicle", "jaw")
def region_faces(ob, me=None):
    """per face: 'handL', 'handR', 'torso' or None (me: an evaluated mesh, whose vertex groups follow subdivision)"""
    me = me or ob.data
    arm_ = ob.parent if ob.parent and ob.parent.type == "ARMATURE" else next((p for p in [ob.parent, getattr(ob.parent, "parent", None)] if p and p.type == "ARMATURE"), None)
    bones = set(arm_.data.bones.keys()) if arm_ else set()
    vg = {g.index: g.name for g in ob.vertex_groups if g.name in bones}
    dom = []
    for v in me.vertices:
        best = max((g for g in v.groups if g.group in vg), key=lambda g: g.weight, default=None)
        dom.append(vg.get(best.group, "") if best else "")
    reg = []
    for p in me.polygons:
        names = [dom[i] for i in p.vertices]
        if all(n.startswith(HAND) for n in names):
            reg.append("hand" + ("L" if names[0].endswith(".L") else "R"))
        elif all(n.startswith(TORSO) for n in names):
            reg.append("torso")
        else:
            reg.append(None)
    return reg
chars = {}
for nm in ("Boy", "Teen", "Man", "Mom"):
    arm = bpy.data.objects[nm]
    body = bpy.data.objects[nm + "_Body"]
    shirts = [o for o in arm.children_recursive if o.type == "MESH" and ("suit" in o.name)]
    chars[nm] = dict(arm=arm, body=body, breg=region_faces(body), shirts=[(s, region_faces(s)) for s in shirts])
def tris(ob_eval_mesh, Mw, reg, want):
    vs = [Mw @ v.co for v in ob_eval_mesh.vertices]
    polys = [list(p.vertices) for i, p in enumerate(ob_eval_mesh.polygons) if i < len(reg) and reg[i] in want]
    if not polys: return None
    return BVHTree.FromPolygons(vs, polys, epsilon=0.0)
hits = []; kinds = collections.Counter()
for f in range(F0, F1 + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    T = {}
    for nm, c in chars.items():
        if c["arm"].hide_render or c["body"].hide_render: continue
        be = c["body"].evaluated_get(dg); me = be.to_mesh()
        if len(me.polygons) != len(c["breg"]): c["breg"] = region_faces(c["body"], me)
        Mw = be.matrix_world
        T[nm] = dict(L=tris(me, Mw, c["breg"], ("handL",)), R=tris(me, Mw, c["breg"], ("handR",)), torso=tris(me, Mw, c["breg"], ("torso",)), shirts=[])
        be.to_mesh_clear()
        for s, sreg in c["shirts"]:
            if s.hide_render: continue
            se = s.evaluated_get(dg); sm = se.to_mesh()
            if len(sm.polygons) != len(sreg):
                sreg = region_faces(s, sm); c["shirts"] = [(s2, (sreg if s2 is s else r2)) for s2, r2 in c["shirts"]]
            t = tris(sm, se.matrix_world, sreg, ("torso",))
            if t: T[nm]["shirts"].append(t)
            se.to_mesh_clear()
    for nm, t in T.items():
        if t["L"] and t["R"] and t["L"].overlap(t["R"]):
            hits.append((f, nm, "handL-handR")); kinds[(nm, "hand-hand")] += 1
        for s in "LR":
            h = t[s]
            if not h: continue
            if t["torso"] and h.overlap(t["torso"]):
                hits.append((f, nm, "hand" + s + "-ownbody")); kinds[(nm, "hand-ownbody")] += 1
            if any(h.overlap(st) for st in t["shirts"]):
                hits.append((f, nm, "hand" + s + "-ownshirt")); kinds[(nm, "hand-ownshirt")] += 1
            for on, ot in T.items():
                if on == nm: continue
                if ot["torso"] and h.overlap(ot["torso"]):
                    hits.append((f, nm, "hand" + s + "-" + on)); kinds[(nm, "hand-" + on)] += 1
txt = ["HAND AUDIT frames %d-%d step %d: %d hits" % (F0, F1, STEP, len(hits)), "by kind: " + str(dict(kinds))]
# group into frame ranges
runs = []
for f, nm, k in hits:
    if runs and runs[-1][1] == nm and runs[-1][2] == k and f - runs[-1][0][-1] <= STEP: runs[-1][0].append(f)
    else: runs.append(([f], nm, k))
txt += ["%s %s f%d-%d" % (nm, k, r[0], r[-1]) for r, nm, k in runs]
open(OUT, "w").write("\n".join(txt) + "\n"); print("\n".join(txt[:40]))
