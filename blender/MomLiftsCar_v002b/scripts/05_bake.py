"""Bake the marker-bound shot cameras into ONE camera (CAM_Film), a key on every frame, CONSTANT interpolation (hard cuts).
blender -b work/vo.blend --python 05_bake.py -- out.blend"""
import bpy, sys
OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
ms = sorted([m for m in sc.timeline_markers if m.camera], key=lambda m: m.frame)
cd = bpy.data.cameras.new("CAM_Film"); cam = bpy.data.objects.new("CAM_Film", cd); sc.collection.objects.link(cam)
cd.clip_start = 0.01; cd.sensor_fit = 'AUTO'; cd.dof.use_dof = True
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f)
    src = max([m for m in ms if m.frame <= f], key=lambda m: m.frame).camera
    cam.matrix_world = src.matrix_world.copy()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cd.lens = src.data.lens; cd.dof.focus_distance = src.data.dof.focus_distance; cd.dof.aperture_fstop = src.data.dof.aperture_fstop
    cd.keyframe_insert("lens", frame=f); cd.dof.keyframe_insert("focus_distance", frame=f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
def fcs(idb):
    a = idb.animation_data.action; out = []
    for layer in getattr(a, "layers", []):
        for st in layer.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out or list(getattr(a, "fcurves", []))
for idb in (cam, cd):
    for fc in fcs(idb):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
# euler flips: make rotation continuous inside shots is not needed with CONSTANT per-frame keys
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o != cam]: bpy.data.objects.remove(o, do_unlink=True)
for o in [o for o in bpy.data.objects if o.name.startswith("Catch_")]: bpy.data.objects.remove(o, do_unlink=True)
l = bpy.data.lights.new("Catch_Film", 'POINT'); l.energy = 0.6; l.shadow_soft_size = 0.02
lo = bpy.data.objects.new("Catch_Film", l); sc.collection.objects.link(lo); lo.parent = cam; lo.location = (0.05, 0.06, 0)
sc.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("BAKE_OK", OUT, [o.name for o in bpy.data.objects if o.type == 'CAMERA'])
