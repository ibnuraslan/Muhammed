"""Camera clearance (Connect01, EarInArm v009d): the camera must never pass through or graze a character.
blender -b film.blend --python cam_clear.py -- out.json [step=2] [min_cm=10]
For every sampled frame: the distance from the camera to the nearest evaluated vertex of every visible character mesh
(body, clothes, cap, mask). Frames under min_cm are flagged (the frame turns into blurred skin or cloth)."""
import bpy, sys, json
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index("--") + 1:]
OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 2; MIN = (float(a[2]) if len(a) > 2 else 10.0) / 100
sc = bpy.context.scene; cam = sc.camera
rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
meshes = [c for r in rigs for c in r.children_recursive if c.type == 'MESH']
for m in meshes:
    for md in m.modifiers:
        if md.type == 'SUBSURF': md.show_viewport = False
res = {"frames": {}, "min_cm": MIN * 100}
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); cp = cam.matrix_world.translation
    best = (9.0, None)
    for m in meshes:
        if m.hide_render or (m.parent and m.parent.hide_render): continue
        ev = m.evaluated_get(dg); me = ev.to_mesh(); mw = m.matrix_world
        # cheap reject: bounding sphere
        if (mw.translation - cp).length > 3.0 and m.parent_type != 'BONE': ev.to_mesh_clear(); continue
        kd = KDTree(len(me.vertices))
        for i, v in enumerate(me.vertices): kd.insert(mw @ v.co, i)
        kd.balance(); co, i, d = kd.find(cp); ev.to_mesh_clear()
        if d < best[0]: best = (d, m.name)
    if best[0] < MIN: res["frames"][f] = {"near": best[1], "cm": round(best[0] * 100, 1)}
bad = sorted(int(f) for f in res["frames"]); ranges = []
for f in bad:
    if ranges and f - ranges[-1][1] <= STEP * 2: ranges[-1][1] = f
    else: ranges.append([f, f])
res["bad_ranges"] = ranges
json.dump(res, open(OUT, "w"), indent=1)
print("CAM_CLEAR", ranges, [(f, v["near"], v["cm"]) for f, v in list(res["frames"].items())[:12]])
