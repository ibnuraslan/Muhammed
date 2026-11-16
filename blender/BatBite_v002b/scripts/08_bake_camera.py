"""One farm camera: bake the marker-bound shot cameras into a single camera keyed every frame (CONSTANT, so every cut is a
clean switch between two frames), lens included; remove the shot cameras and the markers; one small camera-side catchlight.
blender -b edit.blend --python 08_bake_camera.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
def shot_cam(f):
    c = None
    for m in mk:
        if m.frame <= f: c = m.camera
    return c
cd = bpy.data.cameras.new("FilmCam"); cam = bpy.data.objects.new("FilmCam", cd); sc.collection.objects.link(cam)
cd.clip_start = 0.05; cd.clip_end = 6000; cd.dof.use_dof = False; cam.rotation_mode = 'QUATERNION'
prev = None
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); src = shot_cam(f)
    cam.matrix_world = src.matrix_world.copy(); cd.lens = src.data.lens; cd.sensor_fit = src.data.sensor_fit
    q = cam.rotation_quaternion.copy()
    if prev is not None and prev.dot(q) < 0: cam.rotation_quaternion = -q
    prev = cam.rotation_quaternion.copy()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f); cd.keyframe_insert("lens", frame=f)
for idb in (cam, cd):
    act = idb.animation_data.action
    fcs = act.fcurves if hasattr(act, "fcurves") else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
cuts = [m.frame for m in mk]
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
names = [o.name for o in bpy.data.objects if o.type == 'CAMERA' and o is not cam]
for n in names:
    o = bpy.data.objects[n]
    for ch in [c.name for c in o.children]: bpy.data.objects.remove(bpy.data.objects[ch], do_unlink=True)
    bpy.data.objects.remove(o, do_unlink=True)
L = bpy.data.objects.new("FilmCam_catch", bpy.data.lights.new("FilmCam_catch", 'POINT')); L.data.energy = 3.0; L.data.shadow_soft_size = 0.03
L.data.use_shadow = False; L.parent = cam; L.location = (0.12, 0.10, 0.0); sc.collection.objects.link(L)
sc.camera = cam
print("BAKED camera, cuts at", cuts)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
