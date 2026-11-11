"""Hand audit (client 23:00 UTC). blender -b film.blend --python audit_hands.py -- <report.txt> [step]
Every <step> frames: BVH overlaps of each hand (wrist + finger verts of the body) vs the other hand, vs its own
torso/head/legs (body minus that arm), vs the shirt. Also reports joint angles: wrist vs forearm (flex/side) and elbow bend."""
import sys, math, bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2
sc = bpy.context.scene; A = bpy.data.objects["Teen"]
body = bpy.data.objects["Teen.body"]; shirt = bpy.data.objects["Teen.male_casualsuit04"]
gn = {g.index: g.name for g in body.vertex_groups}
BONES = set(b.name for b in A.data.bones)
def dom(v):
    best = max((g for g in v.groups if gn.get(g.group) in BONES), key=lambda g: g.weight, default=None)
    return gn[best.group] if best else ""
def side_of(n): return n[-1] if n[-2:] in (".L", ".R") else ""
HAND = {s: set() for s in "LR"}; ARM = {s: set() for s in "LR"}
for v in body.data.vertices:
    n = dom(v); s = side_of(n)
    if not s: continue
    if n.startswith(("wrist", "finger", "metacarpal")): HAND[s].add(v.index)
    if n.startswith(("lowerarm", "upperarm", "wrist", "finger", "metacarpal", "shoulder", "clavicle")): ARM[s].add(v.index)
for m in body.modifiers:
    if m.type in ('SUBSURF', 'MASK'): m.show_viewport = False      # keep vertex indices aligned with the vertex groups
print("HANDVERTS", {s: len(HAND[s]) for s in "LR"})
def tree_sel(o, sel):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); me = e.to_mesh()
    ok = len(me.vertices) == len(o.data.vertices)
    V = [e.matrix_world @ v.co for v in me.vertices]; me.calc_loop_triangles()
    T = [tuple(t.vertices) for t in me.loop_triangles if (sel is None) or (ok and all(sel(i) for i in t.vertices))]
    e.to_mesh_clear()
    return BVHTree.FromPolygons(V, T) if T else None
def ang(f):
    out = {}
    for s in "LR":
        fa = A.pose.bones["lowerarm02." + s].matrix; wr = A.pose.bones["wrist." + s].matrix
        ua = A.pose.bones["upperarm02." + s].matrix
        r0 = A.data.bones["lowerarm02." + s].matrix_local.to_3x3().inverted() @ A.data.bones["wrist." + s].matrix_local.to_3x3()
        rel = ((fa.to_3x3().inverted() @ wr.to_3x3()) @ r0.inverted()).to_euler('XYZ')
        el = math.degrees(ua.to_3x3().col[1].angle(fa.to_3x3().col[1]))
        out[s] = (math.degrees(rel.x), math.degrees(rel.y), math.degrees(rel.z), el)
    return out
rows = []; tot = {}; amax = {}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    t = {s: tree_sel(body, lambda i, s=s: i in HAND[s]) for s in "LR"}
    issues = []
    n = len(t["L"].overlap(t["R"])) if t["L"] and t["R"] else 0
    if n: issues.append("handL x handR %d" % n); tot["hand x hand"] = tot.get("hand x hand", 0) + n
    for s in "LR":
        rest = tree_sel(body, lambda i, s=s: i not in ARM[s])
        n = len(t[s].overlap(rest)) if t[s] and rest else 0
        if n: issues.append("hand%s x own body %d" % (s, n)); tot["hand x own body"] = tot.get("hand x own body", 0) + n
        ts = tree_sel(shirt, None)
        n = len(t[s].overlap(ts)) if t[s] and ts else 0
        if n: issues.append("hand%s x shirt %d" % (s, n)); tot["hand x shirt"] = tot.get("hand x shirt", 0) + n
    for s, (x, y, z, el) in ang(f).items():
        if el > 145 or abs(x) > 70 or abs(z) > 70: issues.append("joint%s wristX %.0f wristZ %.0f elbow %.0f" % (s, x, z, el)); tot["joint over range"] = tot.get("joint over range", 0) + 1
        for k, v in (("wristX", x), ("wristY", y), ("wristZ", z), ("elbow", el)):
            key = k + s; lo, hi = amax.get(key, (1e9, -1e9)); amax[key] = (min(lo, v), max(hi, v))
    if issues: rows.append("f%04d  " % f + "; ".join(issues))
rep = ["Hand audit every %d frames" % STEP, "TOTAL " + (", ".join("%s=%d" % kv for kv in sorted(tot.items())) or "0 overlaps"),
       "FLAGGED FRAMES %d" % len(rows), "JOINT RANGES " + ", ".join("%s=[%.0f,%.0f]" % (k, v[0], v[1]) for k, v in sorted(amax.items())), ""] + rows
open(OUT, "w").write("\n".join(rep)); print("\n".join(rep[:4]))
