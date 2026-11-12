"""Hands audit (client rule, 23:00): BVH every <step> frames for crew near the camera.
  HAND_HAND   one hand's vertices inside / through the other hand
  HAND_BODY   hand vertices inside the character's own torso, clothes or head
  HAND_OTHER  hand vertices inside another character
blender -b anim.blend --python audit_hands.py -- <report.txt> [step]"""
import sys
import bpy
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; O = bpy.data.objects
CREW = ["SolA", "SolB", "SolC", "SolD", "EngA", "EngB"]
def child(nm, key): return next((c for c in O[nm].children if c.name.split(".")[-1] == key), None)
def cloth(nm): return next((c for c in O[nm].children if c.type == 'MESH' and "suit" in c.name), None)
HANDG = {}
sc.frame_set(1); _dg = bpy.context.evaluated_depsgraph_get()
for nm in CREW:
    b = child(nm, "body"); gi = {"L": set(), "R": set()}; _ev = b.evaluated_get(_dg); _me = _ev.to_mesh()
    for g in b.vertex_groups:
        for s in "LR":
            if g.name.endswith("." + s) and (g.name.startswith(("finger", "metacarpal", "wrist"))): gi[s].add(g.index)
    HANDG[nm] = {s: [v.index for v in _me.vertices if any(gg.group in gi[s] and gg.weight > 0.5 for gg in v.groups)] for s in "LR"}
    tg = {g.index for g in b.vertex_groups if g.name.startswith(("spine", "pelvis", "neck", "head", "clavicle", "breast", "root"))}
    HANDG[nm]["torso"] = [v.index for v in _me.vertices if any(gg.group in tg and gg.weight > 0.6 for gg in v.groups)]; _ev.to_mesh_clear()
issues = {}; total = 0
def tree_of(verts_world, me, idx_set=None):
    if idx_set is None:
        return BVHTree.FromPolygons(verts_world, [p.vertices[:] for p in me.polygons])
    return BVHTree.FromPolygons(verts_world, [p.vertices[:] for p in me.polygons if all(v in idx_set for v in p.vertices)])
def inside(tree, pts, tol=0.006):
    n = 0
    for p in pts:
        loc, nrm, i, d = tree.find_nearest(p)
        if loc is not None and d < 0.05 and (p - loc).dot(nrm) < -tol: n += 1
    return n
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera.matrix_world.translation
    data = {}
    for nm in CREW:
        rig = O[nm]
        if (rig.matrix_world @ rig.pose.bones["root"].head - cam).length > 40: continue
        b = child(nm, "body"); ev = b.evaluated_get(dg); me = ev.to_mesh(); W = [b.matrix_world @ v.co for v in me.vertices]
        tors = set(HANDG[nm]["torso"])
        data[nm] = dict(W=W, L=[W[i] for i in HANDG[nm]["L"]][::2], R=[W[i] for i in HANDG[nm]["R"]][::2],
                        torso=tree_of(W, me, tors), body=tree_of(W, me),
                        handL=tree_of(W, me, set(HANDG[nm]["L"])), handR=tree_of(W, me, set(HANDG[nm]["R"])))
        cl = cloth(nm)
        if cl:
            ce = cl.evaluated_get(dg); cm = ce.to_mesh(); data[nm]["cloth"] = tree_of([cl.matrix_world @ v.co for v in cm.vertices], cm); ce.to_mesh_clear()
        ev.to_mesh_clear()
    for nm, d in data.items():
        hh = inside(d["handR"], d["L"]) + inside(d["handL"], d["R"])
        if hh > 2: issues.setdefault("HAND_HAND", []).append((f, "%s %d" % (nm, hh))); total += hh
        hb = inside(d["torso"], d["L"] + d["R"])
        if "cloth" in d: hb += inside(d["cloth"], d["L"] + d["R"], 0.004) // 2
        if hb > 3: issues.setdefault("HAND_BODY", []).append((f, "%s %d" % (nm, hb))); total += hb
        for nm2, d2 in data.items():
            if nm2 == nm: continue
            ho = inside(d2["body"], d["L"] + d["R"])
            if ho > 2: issues.setdefault("HAND_OTHER", []).append((f, "%s->%s %d" % (nm, nm2, ho))); total += ho
lines = ["HAND AUDIT NukedWell (every %d frames, crew within 40 m of camera)" % STEP, "HAND_PENETRATION_COUNT %d" % total]
for k, v in sorted(issues.items()):
    fr = sorted(set(f for f, _ in v))
    lines.append("%-10s %d frames, e.g. %s" % (k, len(fr), "; ".join("f%d %s" % x for x in v[:6])))
if not issues: lines.append("no hand hits")
open(OUT, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
