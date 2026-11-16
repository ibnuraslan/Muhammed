"""Bake the per-shot cameras (bound by timeline markers at each cut) into ONE camera, CAM_Film, keyed every frame;
catchlights move onto CAM_Film with their keyed visibility; old cameras and markers are removed.
blender -b in.blend --python 04_bake_camera.py -- out.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
marks = sorted([(m.frame, m.camera) for m in sc.timeline_markers if m.camera], key=lambda x: x[0])
cd = bpy.data.cameras.new("CAM_Film"); cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam)
cam.rotation_mode = 'QUATERNION'; cd.sensor_fit = 'AUTO'; cd.dof.use_dof = True; cd.clip_start = 0.03; cd.clip_end = 80.0
def shot_cam(f):
    c = marks[0][1]
    for fr, cc in marks:
        if fr <= f: c = cc
    return c
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = shot_cam(f); M = c.matrix_world.copy()
    loc, q, _ = M.decompose()
    if f > sc.frame_start and cam.rotation_quaternion.dot(q) < 0: q = -q
    cam.location = loc; cam.rotation_quaternion = q
    cd.lens = c.data.lens; cd.dof.focus_distance = c.data.dof.focus_distance; cd.dof.aperture_fstop = c.data.dof.aperture_fstop
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
    for p in ("lens", "dof.focus_distance", "dof.aperture_fstop"): cd.keyframe_insert(p, frame=f)
olds = [c for _, c in marks]
for o in bpy.data.objects:
    if o.parent in olds and o.type == 'LIGHT':
        L = o.matrix_local.copy(); o.parent = cam; o.matrix_parent_inverse.identity(); o.matrix_basis = L
sc.timeline_markers.clear(); sc.camera = cam
for c in set(olds): bpy.data.objects.remove(c, do_unlink=True)
print("BAKED", len(marks), "cuts into CAM_Film; cameras now", [o.name for o in bpy.data.objects if o.type == 'CAMERA'])
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
