"""Bake the per-shot cameras into ONE camera 'FilmCam' (keys every frame, constant interpolation, so each cut is clean),
with one camera-only catchlight; remove the shot cameras, aims and markers (farm convention: one camera, no markers).
blender -b edit.blend --python 06_bake_cam.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; D = bpy.data.objects
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
def shot_cam(f):
    c = None
    for m in mk:
        if m.frame <= f: c = m.camera
    return c
fc = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam")); sc.collection.objects.link(fc)
fc.rotation_mode = 'QUATERNION'; cd = fc.data; cd.sensor_width = 36
L = bpy.data.objects.new("FilmCam_Catchlight", bpy.data.lights.new("FilmCam_Catchlight", 'POINT')); sc.collection.objects.link(L)
L.parent = fc; L.location = (0.08, 0.10, 0); L.data.shadow_soft_size = 0.02
L.visible_diffuse = False; L.visible_transmission = False; L.visible_volume_scatter = False; L.visible_camera = False
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = shot_cam(f)
    fc.matrix_world = c.matrix_world.copy()
    fc.keyframe_insert("location", frame=f); fc.keyframe_insert("rotation_quaternion", frame=f)
    cd.lens = c.data.lens; cd.clip_start = c.data.clip_start; cd.keyframe_insert("lens", frame=f); cd.keyframe_insert("clip_start", frame=f)
    cd.dof.use_dof = c.data.dof.use_dof; cd.dof.keyframe_insert("use_dof", frame=f)
    if c.data.dof.use_dof:
        cd.dof.focus_distance = (c.data.dof.focus_object.matrix_world.translation - c.matrix_world.translation).length
        cd.dof.aperture_fstop = c.data.dof.aperture_fstop
    cd.dof.keyframe_insert("focus_distance", frame=f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
    cl = [o for o in c.children if o.type == 'LIGHT']
    L.data.energy = cl[0].data.energy if cl else 1.0; L.data.keyframe_insert("energy", frame=f)
for idb in (fc.animation_data.action, cd.animation_data.action, L.data.animation_data.action):
    for layer in idb.layers:
        for st in layer.strips:
            for cb in st.channelbags:
                for fcu in cb.fcurves:
                    for k in fcu.keyframe_points: k.interpolation = 'CONSTANT'
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in [o for o in D if o.name.startswith(("CAM_", "AIM_", "CATCH_", "TestCam"))]: bpy.data.objects.remove(o, do_unlink=True)
sc.camera = fc
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.render.use_motion_blur = False
# helper/hidden-only objects that the farm never needs
for o in [o for o in D if o.name == "CutawayCutter"]: o.hide_render = True
print("BAKED camera frames", sc.frame_start, sc.frame_end, "cameras left", [o.name for o in D if o.type == 'CAMERA'])
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
