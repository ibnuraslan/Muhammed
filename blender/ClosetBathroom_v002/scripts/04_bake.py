"""Farm prep: bake the per-shot cameras (marker cuts) into ONE camera keyed every frame (hard cuts stay hard), move the
camera-riding face fills onto it, add the VO as a sound strip from frame 1, remove the shot cameras and markers.
blender -b work/film.blend --python 04_bake.py -- work/baked.blend"""
import bpy, sys, os
HERE = "/home/user/Muhammed/blender/ClosetBathroom_v002/"
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
marks = sorted([(m.frame, m.camera) for m in sc.timeline_markers if m.camera], key=lambda x: x[0])
def cam_at(f):
    c = None
    for fr, cm in marks:
        if fr <= f: c = cm
    return c
cd = bpy.data.cameras.new("FilmCam"); cd.clip_start = 0.05; cd.clip_end = 600; cd.sensor_width = 36; cd.dof.use_dof = False
fc = bpy.data.objects.new("FilmCam", cd); sc.collection.objects.link(fc); fc.rotation_mode = 'QUATERNION'
mats = {}
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = cam_at(f)
    mats[f] = (c.matrix_world.copy(), c.data.lens, c.name)
prevq = None
for f, (M, lens, nm) in mats.items():
    loc, q, _ = M.decompose()
    if prevq is not None and prevq.dot(q) < 0: q = -q
    prevq = q
    fc.location = loc; fc.rotation_quaternion = q; cd.lens = lens
    fc.keyframe_insert("location", frame=f); fc.keyframe_insert("rotation_quaternion", frame=f); cd.keyframe_insert("lens", frame=f)
for idb in (fc, cd):
    ad = idb.animation_data
    act = ad.action
    fcs = []
    try: fcs = list(act.fcurves)
    except Exception:
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: fcs += list(cb.fcurves)
    for fcu in fcs:
        for kp in fcu.keyframe_points: kp.interpolation = 'LINEAR'
# face fills: same local offset, now on the one camera (each keeps its own per-shot energy keys)
for o in list(bpy.data.objects):
    if o.name.startswith("FaceFill_") and o.parent and o.parent.type == 'CAMERA':
        loc = o.location.copy(); o.parent = fc; o.location = loc
# remove markers, shot cameras and their targets
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in list(bpy.data.objects):
    if (o.type == 'CAMERA' and o is not fc) or o.name.startswith("TGT_") or o.name in ("TC", "TT", "GCam"):
        bpy.data.objects.remove(o)
sc.camera = fc
# VO
if not sc.sequence_editor: sc.sequence_editor_create()
se = sc.sequence_editor
strips = se.strips if hasattr(se, "strips") else se.sequences
snd = strips.new_sound("VO", HERE + "ClosetBathroom_v002_VO.mp3", channel=1, frame_start=1)
print("BAKED", len(mats), "frames; VO strip", snd.frame_final_start, snd.frame_final_end, "cameras", [o.name for o in bpy.data.objects if o.type == 'CAMERA'])
# drop the unused Scan scene left by 02b if present, and any scratch objects
for s2 in list(bpy.data.scenes):
    if s2 is not sc: bpy.data.scenes.remove(s2)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
