"""Per frame: distance from each held tool's evaluated mesh to the nearest evaluated fingertip vertex of the holding hand.
blender -b film.blend --python toolmeas.py -- out.json f0 f1"""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; F0, F1 = int(a[1]), int(a[2])
sc = bpy.context.scene; D = bpy.data.objects
TOOLS = [("Forceps", "Surgeon", "L"), ("NeedleHolder", "Surgeon", "R")]
body = D["Surgeon.body"]
for m in body.modifiers:
    if m.type in ("MASK", "SUBSURF", "MULTIRES"): m.show_viewport = False
gi = {g.index: g.name for g in body.vertex_groups}
def tipverts(side):
    out = {}
    for v in body.data.vertices:
        gs = [g for g in v.groups if gi[g.group].startswith("finger")]
        if not gs: continue
        g = max(gs, key=lambda x: x.weight); n = gi[g.group]
        if n.endswith("-3." + side) and g.weight > 0.5: out.setdefault(n.split("-")[0], []).append(v.index)
    return out
TV = {s: tipverts(s) for s in "LR"}
res = {}
for f in range(F0, F1 + 1):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    eb = body.evaluated_get(dg); mb = eb.to_mesh(); vw = [eb.matrix_world @ v.co for v in mb.vertices]; eb.to_mesh_clear()
    for tn, _, s in TOOLS:
        t = D[tn]
        if t.hide_render: continue
        tw, tp = [], []
        for o_ in [t] + [c for c in t.children_recursive if c.type == "MESH"]:
            et = o_.evaluated_get(dg); mt = et.to_mesh(); n0 = len(tw)
            tw += [et.matrix_world @ v.co for v in mt.vertices]; tp += [tuple(n0 + i for i in p.vertices) for p in mt.polygons]; et.to_mesh_clear()
        bvh = BVHTree.FromPolygons(tw, tp)
        lo = Vector([min(q[i] for q in tw) for i in range(3)]); hi = Vector([max(q[i] for q in tw) for i in range(3)])
        per = {}
        for fing, ids in TV[s].items():
            per[fing] = min((bvh.find_nearest(vw[i], 1.0)[3] or 1.0) for i in ids)
        bbd = min(Vector((max(lo.x - vw[i].x, 0, vw[i].x - hi.x), max(lo.y - vw[i].y, 0, vw[i].y - hi.y), max(lo.z - vw[i].z, 0, vw[i].z - hi.z))).length for ids in TV[s].values() for i in ids)
        per["bbox"] = bbd
        res.setdefault(tn, {})[f] = {k: round(v * 100, 2) for k, v in per.items()}
json.dump(res, open(OUT, "w"))
for tn, d in res.items():
    near = {f: min(x for k, x in v.items() if k != "bbox") for f, v in d.items()}
    print("TOOL", tn, "bbox-to-nearest-fingertip max cm", max(v["bbox"] for v in d.values()))
    th = {f: (v.get("finger1", 99), v.get("finger2", 99), v.get("finger4", 99)) for f, v in d.items()}
    print("TOOL", tn, "frames", len(d), "nearest-tip max cm", max(near.values()), "at", max(near, key=near.get), "| thumb max", max(x[0] for x in th.values()), "index max", max(x[1] for x in th.values()), "ring max", max(x[2] for x in th.values()))
