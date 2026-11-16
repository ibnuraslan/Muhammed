"""Bake the per-shot cameras (bound by markers) into ONE camera, CAM_Film, with the hard cuts in its keys (CONSTANT at
each cut), one catchlight parented to it (energy keyed per shot), no markers; add the VO strip at frame 1.
blender -b film2.blend --python 04_bake_camera.py -- VO.mp3 out.blend"""
import sys, bpy
a = sys.argv[sys.argv.index("--") + 1:]; VO, OUT = a[0], a[1]
sc = bpy.context.scene
mk = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
def cam_at(f):
    c = None
    for m in mk:
        if m.frame <= f: c = m.camera
    return c
cd = bpy.data.cameras.new("CAM_Film"); cd.sensor_fit = 'AUTO'; cd.clip_start = 0.03; cd.clip_end = 3000; cd.dof.use_dof = True
cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam); cam.rotation_mode = 'QUATERNION'
L = bpy.data.lights.new("Catch_Film", 'POINT'); L.shadow_soft_size = 0.02
lo = bpy.data.objects.new("Catch_Film", L); sc.collection.objects.link(lo); lo.parent = cam; lo.location = (0.08, 0.1, 0)
lo.visible_diffuse = False; lo.visible_transmission = False; lo.visible_volume_scatter = False
src_catch = {o.parent.name: o for o in bpy.data.objects if o.type == 'LIGHT' and o.name.startswith("Catch_") and o.parent}
cuts = set(m.frame for m in mk)
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = cam_at(f)
    cam.matrix_world = c.matrix_world.copy(); cam.rotation_quaternion = c.matrix_world.to_quaternion()
    cd.lens = c.data.lens; cd.dof.focus_distance = c.data.dof.focus_distance; cd.dof.aperture_fstop = c.data.dof.aperture_fstop
    L.energy = 3.0 if c.name in src_catch else 0.0
    for dp in ("location", "rotation_quaternion"): cam.keyframe_insert(dp, frame=f)
    for dp in ("lens", "dof.focus_distance", "dof.aperture_fstop"): cd.keyframe_insert(dp, frame=f)
    L.keyframe_insert("energy", frame=f)
for fc in [fc for idb in (cam, cd, L) for lay in idb.animation_data.action.layers for st in lay.strips for cb in st.channelbags for fc in cb.fcurves]:
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    for kp in fc.keyframe_points:
        if int(round(kp.co.x)) + 1 in cuts: kp.interpolation = 'CONSTANT'      # no sub-frame blend across a cut
# remove the shot cameras, their catchlights and the markers
for o in list(bpy.data.objects):
    if (o.type == 'CAMERA' and o is not cam) or (o.type == 'LIGHT' and o.name.startswith("Catch_") and o is not lo):
        bpy.data.objects.remove(o, do_unlink=True)
sc.timeline_markers.clear()
sc.camera = cam
se = sc.sequence_editor or sc.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
for s in list(strips): strips.remove(s)
strips.new_sound("VO", VO, channel=1, frame_start=1)
sc.frame_set(1)
print("BAKED", sc.frame_start, sc.frame_end, "cuts", len(cuts))
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
