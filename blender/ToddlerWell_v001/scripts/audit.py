"""ToddlerWell contact audit: feet hover/sink, BVH penetration (bodies vs bodies, vs pipe/casing/tripod), head items, camera clearance.
blender -b work/film.blend --python scripts/audit.py -- <out.json> [step]"""
import sys, json, math
import bpy
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 10
sc = bpy.context.scene
DEPTH = 15.24; FLOOR = -DEPTH + 0.05
CH = ["Toddler", "Teen", "ResA", "ResB", "ResC", "Mother", "Crowd1", "Crowd2", "Crowd3", "Crowd4"]
# frames when a character is legitimately off the ground
AIR = {"Toddler": [(98, 200), (1627, 1950)], "Teen": [(1312, 1820)]}
def in_air(n, f): return any(a_ <= f <= b_ for a_, b_ in AIR.get(n, []))
def meshes(n):
    r = bpy.data.objects[n]
    return [c for c in r.children if c.type == "MESH" and any(k in c.name for k in ("body", "shoes", "suit", "vest"))]
def bvh(o, dg):
    e = o.evaluated_get(dg); me = e.to_mesh()
    M = o.matrix_world
    t = BVHTree.FromPolygons([M @ v.co for v in me.vertices], [p.vertices[:] for p in me.polygons]) if len(me.polygons) else None
    zs = [(M @ v.co).z for v in me.vertices]
    e.to_mesh_clear(); return t, (min(zs) if zs else 0)
def hands_feet(o, dg, groups):
    e = o.evaluated_get(dg); me = e.to_mesh(); M = o.matrix_world
    idx = {g.index: g.name for g in o.vertex_groups if any(k in g.name for k in groups)}
    pts = []
    for v in me.vertices:
        for g in v.groups:
            if g.group in idx and g.weight > 0.5: pts.append(M @ v.co); break
    e.to_mesh_clear(); return pts
props = [bpy.data.objects[n] for n in ("ShaftTube", "Casing", "TripodLeg0", "TripodLeg1", "TripodLeg2") if n in bpy.data.objects]
rep = {"feet": [], "penetration": [], "pipe": [], "camera": [], "counts": {}}
pen_total = 0; pipe_total = 0; feet_total = 0; cam_total = 0
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    T = {}
    for n in CH:
        rig = bpy.data.objects[n]
        if rig.pose.bones["root"].head.length > 12:
            continue
        ts = []; zmin = 1e9
        for m in meshes(n):
            if m.hide_render: continue
            t, z = bvh(m, dg); ts.append(t); zmin = min(zmin, z)
        T[n] = ts
        if not in_air(n, f):
            g = FLOOR if (rig.matrix_world @ rig.pose.bones["root"].head).z < -5 else 0.0
            d = zmin - g
            held = n == "Toddler" and f > 1500
            if not held and (d > 0.04 or d < -0.04):
                rep["feet"].append([f, n, round(d, 3)]); feet_total += 1
    names = list(T)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            for ta in T[names[i]]:
                for tb in T[names[j]]:
                    if ta and tb:
                        k = len(ta.overlap(tb))
                        if k:
                            rep["penetration"].append([f, names[i], names[j], k]); pen_total += k
        for p in props:
            if p.hide_render: continue
            tp, _ = bvh(p, dg)
            for ta in T[names[i]]:
                if ta and tp:
                    k = len(ta.overlap(tp))
                    if k:
                        rep["pipe"].append([f, names[i], p.name, k]); pipe_total += k
    cam = sc.camera.matrix_world.translation
    if cam.z < -0.05:
        inside_pipe = math.hypot(cam.x, cam.y) < 0.27
        in_xsec = cam.y < -0.01
        if not (inside_pipe or in_xsec):
            rep["camera"].append([f, "camera inside soil", tuple(round(c, 2) for c in cam)]); cam_total += 1
    best = 9
    for n, ts in T.items():
        for t in ts:
            if t:
                hit = t.find_nearest(cam)
                if hit[0] is not None: best = min(best, hit[3])
    if best < 0.06:
        rep["camera"].append([f, "camera within %.3f m of a character" % best]); cam_total += 1
rep["counts"] = dict(frames=len(range(1, sc.frame_end + 1, STEP)), feet_hover_or_sink=feet_total, body_body_overlap_faces=pen_total,
                     body_prop_overlap_faces=pipe_total, camera_issues=cam_total)
json.dump(rep, open(OUT, "w"), indent=1)
print("AUDIT", rep["counts"])
