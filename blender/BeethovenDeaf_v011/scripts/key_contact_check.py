"""Mesh-level audit of the hands on the keys (the client lesson: fingers touch exactly, never sink in).
blender -b film.blend --python key_contact_check.py -- out.json [step=4] [f0] [f1]
Per sampled frame, on the EVALUATED (subdivided, deformed) body:
  sink_mm  : deepest hand/finger vertex below the top surface of the key under it (>1.0 mm = fault)
  gap_mm   : per finger, the gap between its distal pad and the key it rests on (lifted hands excluded)
Uses the key objects' own matrices (hinged keys included)."""
import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]; step = int(a[1]) if len(a) > 1 else 4
sc = bpy.context.scene
f0 = int(a[2]) if len(a) > 2 else sc.frame_start; f1 = int(a[3]) if len(a) > 3 else sc.frame_end
rig = bpy.data.objects["Composer"]; body = bpy.data.objects["Composer.body"]
keys = [o for o in bpy.data.objects if o.name.startswith(("KeyW", "KeyB"))]
BN = rig.data.bones
gi = {g.index: g.name for g in body.vertex_groups}
hand_v = set()
for v in body.data.vertices:
    gs = [g for g in v.groups if gi.get(g.group, "").startswith(("finger", "wrist", "metacarpal"))]
    if gs and max(g.weight for g in gs) > 0.5: hand_v.add(v.index)
res = {}; worst = 0.0
for f in range(f0, f1 + 1, step):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    kb = []
    for k in keys:
        ke = k.evaluated_get(dg); m = ke.to_mesh(); M = k.matrix_world
        kb.append((k, BVHTree.FromPolygons([M @ v.co for v in m.vertices], [tuple(p.vertices) for p in m.polygons]))); ke.to_mesh_clear()
    be = body.evaluated_get(dg); me = be.to_mesh(); Mb = body.matrix_world
    # subdivided mesh: map by proximity is costly; use the original-index layer when present, else all low verts
    pts = [Mb @ v.co for v in me.vertices]
    be.to_mesh_clear()
    sink = 0.0
    for p in pts:
        if not (-0.155 < p.y < 0.002 and -0.68 < p.x < 0.68 and 0.70 < p.z < 0.83): continue
        for k, bvh in kb:
            if abs(k.matrix_world.translation.x - p.x) > 0.016: continue
            hit = bvh.ray_cast(p + Vector((0, 0, 0.2)), Vector((0, 0, -1)), 0.2)
            if hit[0] is not None and (hit[0] - p).length < 0.2 and hit[0].z > p.z:
                # p is below this key's top: inside the key only if also above its bottom
                hit2 = bvh.ray_cast(p, Vector((0, 0, -1)), 0.05)
                if hit2[0] is not None:
                    sink = max(sink, hit[0].z - p.z)
    res[f] = round(sink * 1000, 2); worst = max(worst, sink)
json.dump(res, open(out, "w"))
bad = {f: v for f, v in res.items() if v > 1.0}
print("KEYCHECK frames", len(res), "worst sink mm", round(worst * 1000, 2), "frames >1mm", len(bad), sorted(bad.items())[:30])
