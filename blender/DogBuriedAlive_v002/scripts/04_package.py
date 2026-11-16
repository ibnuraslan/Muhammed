"""DogBuriedAlive: bake the per-shot cameras into ONE camera (clean cuts = constant keys, no camera markers),
add the client VO as a sound strip from frame 1, farm render settings. Then pipeline/package_for_farm.py packs and saves.
blender -b built.blend --python 04_package.py -- <vo.mp3> <out_prepacked.blend>"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = a
sc = bpy.context.scene
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
shots = [(m.name, m.frame, m.camera) for m in mk]
cd = bpy.data.cameras.new("CAM_Film"); cd.dof.use_dof = True
cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam)
cam.rotation_mode = 'QUATERNION'
for i, (nm, f0, src) in enumerate(shots):
    f1 = shots[i + 1][1] - 1 if i + 1 < len(shots) else sc.frame_end
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        cam.matrix_world = src.matrix_world.copy()
        cd.lens = src.data.lens; cd.clip_start = src.data.clip_start; cd.clip_end = max(src.data.clip_end, 200)
        cd.dof.use_dof = src.data.dof.use_dof; cd.dof.aperture_fstop = src.data.dof.aperture_fstop
        cd.dof.focus_distance = src.data.dof.focus_distance
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_quaternion", frame=f)
        for p in ("lens", "dof.aperture_fstop", "dof.focus_distance"):
            cd.keyframe_insert(p, frame=f)
def fcs(idb):
    act = idb.animation_data.action
    try: return list(act.fcurves)
    except Exception:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
for idb in (cam, cd):
    for fc in fcs(idb):
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
# remove the shot cameras and the camera bindings of the markers (keep the markers as shot labels)
for nm, f0, src in shots:
    d = src.data; bpy.data.objects.remove(src, do_unlink=True)
    if d.users == 0: bpy.data.cameras.remove(d)
for m in sc.timeline_markers: m.camera = None
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o is not cam]:
    bpy.data.objects.remove(o, do_unlink=True)
sc.camera = cam
# VO
if not sc.sequence_editor: sc.sequence_editor_create()
ed = sc.sequence_editor
strips = ed.strips if hasattr(ed, "strips") else ed.sequences
for s_ in list(strips): strips.remove(s_)
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
# farm settings
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; r.engine = 'CYCLES'
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'; r.use_stamp = False
sc.frame_start = 1
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("PKG_OK", len(shots), "shots baked into CAM_Film; frames", sc.frame_start, sc.frame_end)
