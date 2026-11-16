"""Phase-2 package prep: one baked camera (hard cuts in its keys, no markers), VO sound strip, unused rigs/props removed,
textures capped at 2048 px. blender -b build/look.blend --python 05_package.py -- timing.json VO.mp3 out_pre.blend
Then run pipeline/package_for_farm.py on out_pre.blend."""
import bpy, sys, json, os
a = sys.argv[sys.argv.index("--") + 1:]
T = json.load(open(a[0])); VO = a[1]; OUT = a[2]
sc = bpy.context.scene; O = bpy.data.objects
sc.frame_start = 1; sc.frame_end = max(v[1] for v in T.values()) - 1

# ---- unused cast and props (beats not in the client's final VO)
USED_RIGS = {"Hero", "PenLady", "KnobMan", "Camper", "Worker", "KegGuy", "SledGuy", "Exec", "Landlady", "Director", "Mayor"}
for r in [o for o in O if o.type == 'ARMATURE' and "upperarm01.L" in o.pose.bones and o.name not in USED_RIGS]:
    for c in list(r.children_recursive): bpy.data.objects.remove(c)
    print("DROP rig", r.name); bpy.data.objects.remove(r)
for n in ("P_Guitar", "P_Newspaper", "P_Pen2", "P_PhotoFrame", "P_TicketCard", "P_HouseKeys" if False else "", "Table_S12", "Table_S17"):
    o = O.get(n)
    if o:
        for c in list(o.children_recursive): bpy.data.objects.remove(c)
        print("DROP", n); bpy.data.objects.remove(o)

# ---- bake the per-shot cameras into ONE camera
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); sc.collection.objects.link(cam)
cam.data.sensor_width = 36; cam.data.clip_start = 0.01; cam.data.dof.use_dof = True
catch = bpy.data.objects.new("Camera_Catch", bpy.data.lights.new("Camera_Catch", 'POINT')); sc.collection.objects.link(catch)
catch.parent = cam; catch.location = (0, 0.06, 0); catch.data.energy = 1.5; catch.data.shadow_soft_size = 0.02; catch.data.use_shadow = False
for k, (t0, t1) in sorted(T.items(), key=lambda kv: kv[1][0]):
    src = O["CAM_" + k]
    for f in range(t0, t1):
        sc.frame_set(f)
        cam.matrix_world = src.matrix_world.copy()
        cam.data.lens = src.data.lens; cam.data.dof.focus_distance = src.data.dof.focus_distance
        cam.data.dof.aperture_fstop = max(8.0, src.data.dof.aperture_fstop)
        cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
        cam.data.keyframe_insert("lens", frame=f); cam.data.dof.keyframe_insert("focus_distance", frame=f)
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
for ad in (cam.animation_data, cam.data.animation_data):
    act = ad.action
    fcs = list(act.fcurves) if hasattr(act, "fcurves") else [fc for l in act.layers for s in l.strips for b in s.channelbags for fc in b.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'          # a key on every frame: cuts stay hard
sc.camera = cam
for o in [o for o in O if o.type == 'CAMERA' and o is not cam]:
    for c in list(o.children): bpy.data.objects.remove(c)
    bpy.data.objects.remove(o)
sc.timeline_markers.clear()

# ---- VO
if not sc.sequence_editor: sc.sequence_editor_create()
seq = sc.sequence_editor
strips = seq.strips if hasattr(seq, "strips") else seq.sequences
for s in list(strips): strips.remove(s)
snd = strips.new_sound("VO", VO, channel=1, frame_start=1)
snd.sound.pack()

# ---- textures: cap at 2048 px (re-packed from pixels, alpha kept)
for im in bpy.data.images:
    if im.source != 'FILE' or im.size[0] <= 2048 and im.size[1] <= 2048: continue
    w, h = im.size; s = 2048 / max(w, h)
    try:
        im.scale(int(w * s), int(h * s)); im.pack()
        print("SCALED", im.name, w, h)
    except Exception as e:
        print("SCALE_FAIL", im.name, e)
bpy.ops.outliner.orphans_purge(do_recursive=True)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = 60; r.fps_base = 1.0; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'; r.use_stamp = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("PRE saved", OUT, sc.frame_start, sc.frame_end)
