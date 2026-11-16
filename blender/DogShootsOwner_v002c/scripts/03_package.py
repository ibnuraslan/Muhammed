"""DogShootsOwner Phase 2 package: one baked camera (hard cuts, no markers), unused data removed, VO packed, compressed.
blender -b film_vo.blend --python 03_package.py -- <vo.mp3> <out .blend>"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
VO, OUT = a
sc = bpy.context.scene

# ---- one camera with the cuts baked into its keys (every frame keyed, constant interpolation)
mk = sorted(sc.timeline_markers, key=lambda m: m.frame)
cd = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", cd); sc.collection.objects.link(cam)
cd.clip_start = 0.02; cd.dof.use_dof = True
for f in range(sc.frame_start, sc.frame_end + 1):
    src = max((m for m in mk if m.frame <= f), key=lambda m: m.frame).camera
    sc.frame_set(f)
    cam.matrix_world = src.matrix_world.copy()
    cd.lens = src.data.lens; cd.dof.focus_distance = src.data.dof.focus_distance; cd.dof.aperture_fstop = src.data.dof.aperture_fstop
    cd.sensor_fit = src.data.sensor_fit; cd.sensor_width = src.data.sensor_width
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    cd.keyframe_insert("lens", frame=f); cd.dof.keyframe_insert("focus_distance", frame=f); cd.dof.keyframe_insert("aperture_fstop", frame=f)
def fcurves(idb):
    act = idb.animation_data.action
    try: return list(act.fcurves)
    except Exception:
        return [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
for idb in (cam, cd):
    for fc in fcurves(idb):
        for k in fc.keyframe_points: k.interpolation = 'CONSTANT'
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o is not cam]:
    bpy.data.objects.remove(o, do_unlink=True)
sc.camera = cam
print("PKG camera baked", sc.frame_start, sc.frame_end)

# ---- remove what the film no longer uses
def drop(rig_name):
    r = bpy.data.objects.get(rig_name)
    if not r: return
    for c in list(r.children_recursive): bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(r, do_unlink=True)
drop("MedB")                                   # his shot (10) was cut for the VO
for n in ("ClipHeld",):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True)
for cname in ("PROPS", "PLANTS"):              # hidden library originals (placed copies keep their data)
    c = bpy.data.collections.get(cname)
    if c:
        for o in list(c.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
for _ in range(4):
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# ---- VO as a packed sound strip at frame 1
se = sc.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences
s = strips.new_sound("VO", VO, 1, 1)
s.sound.pack()

# ---- farm settings
r = sc.render; cy = sc.cycles
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps, r.fps_base = 60, 1.0
r.engine = 'CYCLES'; cy.samples = 48; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.05
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'; r.use_simplify = False
r.filepath = "//render/" + os.path.splitext(os.path.basename(OUT))[0].replace("_60fps", "") + "_"
bpy.ops.file.pack_all()
unpacked = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file]
print("PKG unpacked images", unpacked)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("PKG SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB", "frames", sc.frame_start, sc.frame_end)
