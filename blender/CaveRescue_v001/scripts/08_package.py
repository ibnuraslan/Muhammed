"""Shrink for git (<95 MB, no LFS): every image to at most 1024 px (2K HDRI kept at 2048x1024), purge orphans,
then pipeline/package_for_farm.py (packs, checks farm settings, saves compressed).
blender -b final.blend --python 08_package.py -- <repo_root> <out.blend>"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; ROOT, OUT = a[0], a[1]
sc = bpy.context.scene
for o in [o for o in bpy.data.objects if o.type == 'CAMERA' and o.name != "CAM_Film"]:
    bpy.data.objects.remove(o, do_unlink=True)
n = 0
for im in bpy.data.images:
    if im.source != 'FILE' or not im.has_data and not im.filepath: continue
    try:
        w, h = im.size
    except Exception:
        continue
    lim = 2048 if im.filepath.endswith(".hdr") else 1024
    if max(w, h) > lim:
        s = lim / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s))); n += 1
        im.pack()
print("RESIZED", n)
# packed images as JPEG (HDRI stays Radiance at 1024x512): far smaller than packed PNG/EXR
import tempfile
TMP = tempfile.mkdtemp()
nj = 0
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    try: w, h = im.size
    except Exception: continue
    if w == 0: continue
    if im.filepath.endswith(".hdr"):
        if w > 1024: im.scale(1024, 512)
        im.pack(); continue
    try:
        if im.packed_file: im.unpack(method='USE_ORIGINAL') if False else None
        path = os.path.join(TMP, "%03d.jpg" % nj)
        im.filepath_raw = path; im.file_format = 'JPEG'
        sc.render.image_settings.quality = 88
        im.save(filepath=path, quality=88) if 'quality' in im.save.__doc__ else im.save()
        if im.packed_file: im.unpack(method='REMOVE')
        im.filepath = path; im.reload(); im.pack(); nj += 1
    except Exception as e:
        print("JPEG skip", im.name, e)
print("JPEG", nj)
# decimate the instanced jungle trees (background only)
for mname in [m.name for m in bpy.data.meshes if len(m.vertices) > 200000]:
    me = bpy.data.meshes[mname]
    tmp = bpy.data.objects.new("DEC_tmp", me); sc.collection.objects.link(tmp)
    d = tmp.modifiers.new("D", 'DECIMATE'); d.ratio = 0.18
    dg = bpy.context.evaluated_depsgraph_get(); new = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    users = [o for o in bpy.data.objects if o.data == me and o != tmp]
    for o in users: o.data = new
    bpy.data.objects.remove(tmp, do_unlink=True)
    print("DECIMATED", mname, len(me.vertices), "->", len(new.vertices), "users", len(users))
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
sc.cycles.samples = 48; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.05
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1080, 1920, 100
sys.argv = [sys.argv[0], "--", OUT]
exec(open(os.path.join(ROOT, "blender", "pipeline", "package_for_farm.py")).read())
