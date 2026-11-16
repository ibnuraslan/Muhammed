"""Package for RenderStreet: VO sound strip at frame 1, final render settings, everything packed, compressed save.
blender -b anim.blend -P 05_package.py -- <vo.mp3> <out.blend>"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT = a
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sc.render.fps = 60; sc.render.fps_base = 1.0
sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Punchy'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = "//render/WhaleSwallow_"
# --- bake the per-shot cameras (marker-switched) into ONE camera with hard cuts in its keys (farm rule: one camera, no camera markers)
src = []
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = sc.camera; src.append((f, c.matrix_world.copy(), c.data.lens))
cd = bpy.data.cameras.new("CAM"); cd.clip_start = 0.05; cd.clip_end = 2000; cd.dof.use_dof = False; cd.sensor_fit = 'AUTO'
cam = bpy.data.objects.new("CAM", cd); sc.collection.objects.link(cam); cam.rotation_mode = 'XYZ'
prev_e = None
for f, mw, lens in src:
    loc, rot, _s = mw.decompose(); e = rot.to_euler('XYZ', prev_e) if prev_e else rot.to_euler('XYZ'); prev_e = e
    cam.location = loc; cam.rotation_euler = e; cd.lens = lens
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f); cd.keyframe_insert("lens", frame=f)
def _fcs(idb):
    act = idb.animation_data.action
    try: return list(act.fcurves)
    except Exception: return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
for idb in (cam, cd):
    for fc in _fcs(idb):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
for m in sc.timeline_markers: m.camera = None
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o is not cam]:
    bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o.name.startswith("TGT_")]:
    bpy.data.objects.remove(o, do_unlink=True)
sc.camera = cam
err = 0.0
for f, mw, lens in src:
    sc.frame_set(f); err = max(err, max(abs(a_ - b_) for ra, rb in zip(cam.matrix_world, mw) for a_, b_ in zip(ra, rb)), abs(cd.lens - lens))
print("CAMBAKE frames", len(src), "max_err", round(err, 6), "cameras", [o.name for o in bpy.data.objects if o.type == 'CAMERA'], "bound_markers", sum(1 for m in sc.timeline_markers if m.camera))
se = sc.sequence_editor or sc.sequence_editor_create()
coll = se.strips if hasattr(se, "strips") else se.sequences
for st in list(coll):
    coll.remove(st)
snd = coll.new_sound("VO", VO, 2, 1)
sc.render.ffmpeg.audio_codec = 'AAC'
bpy.ops.file.pack_all()
for s_ in bpy.data.sounds:
    if not s_.packed_file: s_.pack()
bpy.ops.file.make_paths_relative()
unpacked = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
print("PACK unpacked images:", unpacked, "sounds packed:", all(s_.packed_file for s_ in bpy.data.sounds))
print("RANGE", sc.frame_start, sc.frame_end, "markers", len(sc.timeline_markers))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PACKAGE_DONE", OUT, round(os.path.getsize(OUT) / 1e6, 1), "MB")
