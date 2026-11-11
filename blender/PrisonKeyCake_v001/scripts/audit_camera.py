"""Camera audit: inside-geometry and too-close checks every N frames.
blender -b film.blend --python audit_camera.py -- [step]"""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
STEP = int(a[0]) if a else 4
sc = bpy.context.scene; cam = sc.camera
dirs = [Vector(d).normalized() for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1),(-1,-1,1),(1,-1,-1),(-1,1,-1),(1,1,-1),(-1,-1,-1),(1,-1,1),(-1,1,1))]
for vo in [o for o in bpy.data.objects if o.name in ("CellDust", "Smoke")]:
    vo.animation_data_clear(); vo.hide_viewport = True
bad = []
for f in range(sc.frame_start, sc.frame_end + 1, STEP):
    sc.frame_set(f); dg = bpy.context.evaluated_depsgraph_get()
    p = cam.matrix_world.translation
    back = 0; near = (9, None)
    for d in dirs:
        hit, loc, nrm, idx, ob, M = sc.ray_cast(dg, p, d)
        if hit:
            if nrm.dot(d) > 0: back += 1
            dist = (loc - p).length
            if dist < near[0]: near = (dist, ob.name)
    if back >= 5 or near[0] < 0.08:
        bad.append((f, back, round(near[0], 3), near[1]))
for b in bad: print("CAMBAD", *b)
print("CAMAUDIT frames", len(range(sc.frame_start, sc.frame_end + 1, STEP)), "bad", len(bad))
