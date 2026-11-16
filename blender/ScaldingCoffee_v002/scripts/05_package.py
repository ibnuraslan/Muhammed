"""B09 package: bake the shot cameras into ONE camera (hard cuts as constant keys), drop markers, shrink textures,
pack everything, farm settings.  blender -b lay.blend --python 05_package.py -- out_60fps.blend [max_tex]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; MAXT = int(a[1]) if len(a) > 1 else 1024
sc = bpy.context.scene
marks = sorted([(m.frame, m.camera) for m in sc.timeline_markers if m.camera], key=lambda x: x[0])
def cam_at(f):
    c = marks[0][1]
    for fr, cm in marks:
        if fr <= f: c = cm
    return c
film = bpy.data.objects.new("FilmCam", bpy.data.cameras.new("FilmCam")); sc.collection.objects.link(film)
fc = film.data; fc.dof.use_dof = True; fc.clip_start = 0.01; fc.sensor_fit = 'AUTO'
film.rotation_mode = 'XYZ'
prev_cam = None; prev_e = None
for f in range(sc.frame_start, sc.frame_end + 1):
    sc.frame_set(f); c = cam_at(f)
    M = c.matrix_world.copy(); loc, q, _ = M.decompose()
    e = q.to_euler('XYZ', prev_e) if (prev_e is not None and c == prev_cam) else q.to_euler('XYZ')
    film.location = loc; film.rotation_euler = e
    fc.lens = c.data.lens; fc.dof.aperture_fstop = c.data.dof.aperture_fstop; fc.dof.focus_distance = c.data.dof.focus_distance
    for path, owner in (("location", film), ("rotation_euler", film), ("lens", fc)):
        owner.keyframe_insert(path, frame=f)
    fc.dof.keyframe_insert("aperture_fstop", frame=f); fc.dof.keyframe_insert("focus_distance", frame=f)
    prev_cam, prev_e = c, e
for idb in (film, fc):
    ad = idb.animation_data
    for fcu in ([*ad.action.fcurves] if hasattr(ad.action, "fcurves") and len(ad.action.fcurves) else
                [x for L in ad.action.layers for st in L.strips for cb in st.channelbags for x in cb.fcurves]):
        for k in fcu.keyframe_points: k.interpolation = 'CONSTANT'   # baked per frame; constant = clean cuts
# catchlight: one small camera-only point light on the film camera
for o in list(bpy.data.objects):
    if o.name.startswith("Catch_"): bpy.data.objects.remove(o)
L = bpy.data.lights.new("Catchlight", 'POINT'); L.energy = 0.6; L.shadow_soft_size = 0.02
lo = bpy.data.objects.new("Catchlight", L); sc.collection.objects.link(lo); lo.parent = film; lo.location = (0.05, 0.06, 0)
for m in list(sc.timeline_markers): sc.timeline_markers.remove(m)
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o != film]: bpy.data.objects.remove(o)
sc.camera = film
# textures: dedupe copies of the same file, shrink to <= MAXT, re-pack the shrunk pixels.
# Opaque textures go to JPEG; anything with alpha (hair, brows, lashes, logo) stays PNG so alpha is kept (LESSONS 3).
import tempfile, hashlib
# dedupe by CONTENT, never by name: every GLB asset calls its maps Image_0/Image_1/..., so a name key swapped the
# conference table onto the chair's black textures (v002 preview, 5a).
def content_key(im):
    if im.packed_file: return hashlib.sha1(im.packed_file.data).hexdigest()
    p = bpy.path.abspath(im.filepath)
    return hashlib.sha1(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else ("name", im.name)
keep = {}
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    k = (content_key(im), tuple(im.size), im.colorspace_settings.name)
    if k in keep and keep[k] != im: im.user_remap(keep[k]); continue
    keep[k] = im
bpy.ops.outliner.orphans_purge(do_recursive=True)
tmpd = tempfile.mkdtemp(); n = 0
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90; sc.render.image_settings.color_mode = 'RGB'
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    if im.name.lower().endswith(".hdr"): continue
    w, h = im.size; big = max(w, h) > MAXT
    alpha = im.alpha_mode != 'NONE' and any(t in im.name.lower() for t in ("hair", "brow", "lash", "logo", "ponytail", "short0", "bob0", "afro", "braid", "long0"))
    if big:
        s_ = MAXT / max(w, h); im.scale(max(1, int(w * s_)), max(1, int(h * s_)))
    if big or not alpha:
        fmt, ext = ("PNG", ".png") if alpha else ("JPEG", ".jpg")
        path = os.path.join(tmpd, "img%03d%s" % (n, ext)); n += 1
        if alpha: im.filepath_raw = path; im.file_format = 'PNG'; im.save()
        else: im.save_render(path)   # opaque only: JPEG at the scene's quality
        cs = im.colorspace_settings.name
        im.filepath = path; im.source = 'FILE'
        if im.packed_file: im.unpack(method='REMOVE')
        im.filepath = path; im.reload(); im.colorspace_settings.name = cs; im.pack()
print("REPACKED", n, "images (<=%d px)" % MAXT)
sc.render.image_settings.quality = 90
bpy.ops.file.pack_all()
for s in bpy.data.sounds:
    if not s.packed_file: s.pack()
r = sc.render
r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100; r.fps, r.fps_base = 60, 1.0
sc.cycles.samples = 48; sc.cycles.adaptive_threshold = 0.05; sc.cycles.use_denoising = True; r.use_motion_blur = False
r.image_settings.file_format = 'PNG'
base = os.path.splitext(os.path.basename(OUT))[0].replace("_60fps", ""); r.filepath = "//render/%s_" % base
probs = []
if [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]: probs.append("unpacked images")
if len([o for o in bpy.data.objects if o.type == "CAMERA"]) != 1 or sc.timeline_markers: probs.append("camera/markers")
if bpy.data.libraries: probs.append("libraries")
print("FARM", dict(frames=(sc.frame_start, sc.frame_end), samples=sc.cycles.samples, view=(sc.view_settings.view_transform, sc.view_settings.look), out=r.filepath))
print("PROBLEMS", probs or "none")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB")
