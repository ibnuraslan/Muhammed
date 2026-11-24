"""v014 contact audit: surgeon finger/hand/forearm points vs the monkeys, seats, backrests, towel; needle tip vs skin.
Points inside a surface by more than TOL are flagged. blender -b film.blend --python contact_check.py -- out.json [frames a-b,...] [step]"""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; ranges = a[1] if len(a) > 1 else "1-1656"; step = int(a[2]) if len(a) > 2 else 1
frames = sorted({f for r in ranges.split(",") for f in range(int(r.split("-")[0]), int(r.split("-")[1]) + 1, step)})
sc = bpy.context.scene; D = bpy.data
rig = D.objects["Surgeon"]
TOL = 0.004
def local_bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    b = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [p.vertices[:] for p in me.polygons]); oe.to_mesh_clear(); return b
TARGETS = [n for n in ("MK_BodyB", "MK_BodyA", "MK_Head", "Seat_A", "Seat_B", "Backrest_A", "Backrest_B", "InstrTowel",
                       "BackPost_A0", "BackPost_A1", "BackPost_B0", "BackPost_B1", "T1_Pad", "T2_Pad") if n in D.objects]
sc.frame_set(1)
BV = {n: local_bvh(D.objects[n]) for n in TARGETS}
BB = {}
for n in TARGETS:
    o = D.objects[n]; bb = [Vector(c) for c in o.bound_box]
    BB[n] = (Vector([min(v[i] for v in bb) for i in range(3)]), Vector([max(v[i] for v in bb) for i in range(3)]))
def inside(n, pw):
    o = D.objects[n]; inv = o.matrix_world.inverted(); p = inv @ pw
    lo, hi = BB[n]
    if any(p[i] < lo[i] or p[i] > hi[i] for i in range(3)): return 0.0
    loc, nrm, idx, dist = BV[n].find_nearest(p)
    if loc is None: return 0.0
    d = (p - loc)
    s = d.dot(nrm)
    if s < 0:
        w = (o.matrix_world @ loc - pw).length
        if w > 0.05: return 0.0
        # confirm with a ray along the outward normal: a point truly inside hits the surface going out
        hit = BV[n].ray_cast(p, nrm, 0.06)
        return w if hit[0] is not None else 0.0
    return 0.0
BONES = [b.name for b in rig.data.bones if b.name.startswith(("finger", "wrist", "metacarpal", "lowerarm"))]
flags = []
nh = D.objects.get("NeedleHolder")
TIP = Vector((0.0, 0.041, -0.006))
for f in frames:
    sc.frame_set(f)
    if D.objects["MK_Head"].hide_render: continue
    for bn in BONES:
        pb = rig.pose.bones[bn]
        for u in (0.0, 0.5, 1.0):
            pw = rig.matrix_world @ pb.head.lerp(pb.tail, u)
            for n in TARGETS:
                if n.startswith(("T1_", "T2_")) and not bn.startswith("finger"): continue
                d = inside(n, pw)
                r = 0.006 if bn.startswith("finger") else 0.02
                if d > TOL + (0.0 if bn.startswith("finger") else 0.01):
                    flags.append((f, bn, round(u, 1), n, round(d * 1000, 1)))
    if nh:
        tw = nh.matrix_world @ TIP
        for n in ("MK_BodyB", "MK_Head"):
            d = inside(n, tw)
            if d > 0.003: flags.append((f, "NEEDLE_TIP", 1.0, n, round(d * 1000, 1)))
agg = {}
for f, bn, u, n, d in flags:
    k = (bn.split(".")[0][:7] + "." + bn.split(".")[-1], n); agg.setdefault(k, []).append((f, d))
def runs(fs):
    fs = sorted(set(fs)); out = []; a_ = b_ = fs[0]
    for x in fs[1:]:
        if x - b_ <= 4: b_ = x
        else: out.append("%d-%d" % (a_, b_)); a_ = b_ = x
    out.append("%d-%d" % (a_, b_)); return out
summary = {"%s|%s" % k: {"frames": runs([v[0] for v in vs]), "n": len(vs), "max_mm": max(v[1] for v in vs)} for k, vs in agg.items()}
json.dump({"frames_checked": len(frames), "flags": len(flags), "summary": summary}, open(out, "w"), indent=1)
print("CONTACT", len(frames), "frames,", len(flags), "flags"); print(json.dumps(summary, indent=1)[:3000])
