"""Bake the marker-switched shot cameras into ONE camera (CAM_Film) with hard cuts in its keys, remove the markers and
shot cameras, re-parent the catchlights, add the VO sound strip. blender -b look.blend --python bake_cam.py -- vo.mp3 out.blend"""
import bpy, sys, math
from mathutils import Vector, Euler
a = sys.argv[sys.argv.index("--") + 1:]; vo, out = a[0], a[1]
sc = bpy.context.scene; O = bpy.data.objects
def fcs(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return []
    act = ad.action
    if hasattr(act, "fcurves") and len(act.fcurves): return list(act.fcurves)
    r = []
    for layer in getattr(act, "layers", []):
        for st in layer.strips:
            for bag in st.channelbags: r += list(bag.fcurves)
    return r
def ev(idb, path, idx, f, default):
    for fc in fcs(idb):
        if fc.data_path == path and fc.array_index == idx: return fc.evaluate(f)
    return default
marks = sorted((m.frame, m.camera) for m in sc.timeline_markers if m.camera)
camd = bpy.data.cameras.new("CAM_Film"); film = bpy.data.objects.new("CAM_Film", camd); sc.collection.objects.link(film)
camd.sensor_width = 36; camd.clip_start = 0.05; camd.dof.use_dof = True; film.rotation_mode = 'XYZ'
for f in range(sc.frame_start, sc.frame_end + 1):
    c = [cm for fr, cm in marks if fr <= f][-1]
    loc = [ev(c, "location", i, f, c.location[i]) for i in range(3)]
    rot = [ev(c, "rotation_euler", i, f, c.rotation_euler[i]) for i in range(3)]
    film.location = loc; film.rotation_euler = rot
    film.keyframe_insert("location", frame=f); film.keyframe_insert("rotation_euler", frame=f)
    camd.lens = c.data.lens; camd.dof.aperture_fstop = c.data.dof.aperture_fstop
    camd.dof.focus_distance = ev(c.data, "dof.focus_distance", 0, f, c.data.dof.focus_distance)
    camd.keyframe_insert("lens", frame=f); camd.dof.keyframe_insert("aperture_fstop", frame=f); camd.dof.keyframe_insert("focus_distance", frame=f)
for idb in (film, camd):
    for fc in fcs(idb):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# catchlights follow the film camera (their per-shot hide keys stay)
for o in list(O):
    if o.type == 'LIGHT' and o.name.endswith("_Catch"):
        loc = o.location.copy(); o.parent = film; o.location = loc
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in list(O):
    if o.type == 'CAMERA' and o is not film: bpy.data.objects.remove(o, do_unlink=True)
sc.camera = film
# render settings (farm)
r = sc.render; r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps = 60; r.fps_base = 1.0
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'
# VO
if not sc.sequence_editor: sc.sequence_editor_create()
seq = sc.sequence_editor
coll = seq.strips if hasattr(seq, "strips") else seq.sequences
for s in list(coll): coll.remove(s)
snd = coll.new_sound("VO", vo, 1, 1)
print("BAKED", len(marks), "shots", sc.frame_start, sc.frame_end, "sound", snd.name)
bpy.ops.wm.save_as_mainfile(filepath=out)
