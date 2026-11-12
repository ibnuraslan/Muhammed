"""Camera-inside check that ignores the lens-parented WipeCard (qa_check's INSIDE test is blocked by it).
blender -b film.blend --python cam_inside_check.py"""
import bpy
from mathutils import Vector
sc = bpy.context.scene; cam = sc.camera
w = bpy.data.objects.get("WipeCard")
if w: w.hide_viewport = True
D = [Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
bad = []
for f in range(sc.frame_start, sc.frame_end + 1, 2):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); p = cam.matrix_world.translation
    back = 0; who = set()
    for d in D:
        ok, loc, n, i, ob, _ = sc.ray_cast(dg, p, d, distance=0.6)
        if ok and n.dot(d) > 0.2: back += 1; who.add(ob.name)
    if back >= 3: bad.append((f, sorted(who)))
runs = []
for f, who in bad:
    if runs and f - runs[-1][1] <= 2: runs[-1][1] = f; runs[-1][2] |= set(who)
    else: runs.append([f, f, set(who)])
print("CAM_INSIDE", [(a, b, sorted(c)[:3]) for a, b, c in runs])
