"""Camera clearance: probe 5 rays per frame; flag hits closer than the frame's limit and backface hits (camera inside a mesh).
blender -b work/film.blend --python scripts/cam_clearance.py -- <step> [report]"""
import sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; STEP = int(a[0]); rep = a[1] if len(a) > 1 else None
sc = bpy.context.scene; cam = sc.camera
SKIP = ("FaceMeshOverlay", "TrackBox", "IrisCircle", "Sec_Backdrop", "DashScreen")
for o in bpy.data.objects:
    if o.hide_render or o.name.startswith(SKIP) or "Glass" in o.name: o.hide_viewport = True
bad = []
for f in range(1, sc.frame_end + 1, STEP):
    sc.frame_set(f)
    for o in bpy.data.objects:   # keyed render visibility -> viewport visibility for the ray cast
        if o.animation_data and o.type == "MESH" and not o.name.startswith(SKIP): o.hide_viewport = o.hide_render
    dg = bpy.context.evaluated_depsgraph_get()
    M = cam.matrix_world; o_ = M.translation; fr = cam.data.view_frame(scene=sc)
    lim = 0.006 if 1729 <= f <= 2448 else 0.03
    worst = None
    for p in [Vector((0, 0, fr[0].z))] + [fr[i] * 0.8 for i in range(4)]:
        d = (M.to_3x3() @ p).normalized()
        hit, loc, n, i, ob, _ = sc.ray_cast(dg, o_, d)
        if not hit: continue
        dist = (loc - o_).length; inside = n.dot(d) > 0.2 and dist < 0.3
        if dist < lim or inside:
            if worst is None or dist < worst[1]: worst = (ob.name, round(dist, 4), "INSIDE" if inside else "near")
    if worst: bad.append((f,) + worst)
txt = "camera clearance, every %d frames: %d flagged\n" % (STEP, len(bad)) + "\n".join(str(b) for b in bad)
print(txt)
if rep: open(rep, "w").write(txt)
