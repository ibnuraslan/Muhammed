"""Milgram: VO strip, frame range, render path, look checks.  blender -b vo.blend --python 03_finish.py -- <vo.mp3> <out.blend> <frame_end>"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT, FE = a[0], a[1], int(a[2])
sc = bpy.context.scene
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
for st in list(strips): strips.remove(st)
snd = strips.new_sound("VO", VO, 1, 1)
sc.frame_start, sc.frame_end = 1, FE
sc.render.fps, sc.render.fps_base = 60, 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False
base = os.path.splitext(os.path.basename(OUT))[0].replace("_60fps", "")
sc.render.filepath = "//render/%s_" % base
sc.render.image_settings.file_format = 'PNG'
# ---- bake the per-shot marker cameras into ONE camera (hard cuts = constant keys), as the farm packages require
marks = sorted(sc.timeline_markers, key=lambda m: m.frame)
cd = bpy.data.cameras.new("CAM_Main"); cam = bpy.data.objects.new("CAM_Main", cd); sc.collection.objects.link(cam)
cd.sensor_fit = 'AUTO'; cd.clip_start = 0.03; cd.clip_end = 3000; cd.dof.use_dof = True
cam.rotation_mode = 'QUATERNION'
def src_at(f):
    c = None
    for m in marks:
        if m.frame <= f: c = m.camera
    return c
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = src_at(f)
    cam.matrix_world = c.matrix_world.copy(); cam.rotation_quaternion = c.matrix_world.to_quaternion()
    cam.location = c.matrix_world.translation
    cd.lens = c.data.lens; cd.dof.focus_distance = c.data.dof.focus_distance; cd.dof.aperture_fstop = c.data.dof.aperture_fstop
    for path in ("location", "rotation_quaternion"): cam.keyframe_insert(path, frame=f)
    for path in ("lens", "dof.focus_distance", "dof.aperture_fstop"): cd.keyframe_insert(path, frame=f)
for idb in (cam, cd):
    for layer in idb.animation_data.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# catchlights: re-parent each shot's camera-only catchlight to the main camera (same offset), keep its visibility keys
olds = [m.camera for m in marks]
for L in [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith("Catch_")]:
    off = L.matrix_parent_inverse.copy(); loc = L.location.copy()
    L.parent = cam; L.matrix_parent_inverse = off; L.location = loc
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for c in set(olds):
    d = c.data; bpy.data.objects.remove(c, do_unlink=True); bpy.data.cameras.remove(d)
sc.camera = cam
sc.frame_set(1)
bpy.ops.file.pack_all()
for snd_ in bpy.data.sounds:
    if not snd_.packed_file: snd_.pack()
print("CAMERAS", [o.name for o in bpy.data.objects if o.type == 'CAMERA'], "markers", len(sc.timeline_markers))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("FINISH_OK", sc.frame_start, sc.frame_end, len(sc.timeline_markers), "markers")
