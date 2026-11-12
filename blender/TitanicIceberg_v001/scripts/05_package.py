"""Shrink and pack for the farm (target < 95 MB, normal git, no LFS).
blender -b anim_p.blend --python 05_package.py -- <tmp_dir> <out.blend> <package_for_farm.py>
- removes helper/unused objects (disabled gulls, leftover cameras), purges orphans
- re-encodes every file image to <= 1024 px (JPEG for colour, PNG for data maps); HDRIs stay 2K
- then runs pipeline/package_for_farm.py (pack all, farm checks, compressed save)."""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; TMP, OUT, PKG = a
os.makedirs(TMP, exist_ok=True); os.makedirs(os.path.dirname(OUT), exist_ok=True)
sc0 = bpy.context.scene; sc0.cycles.samples = 48; sc0.render.use_motion_blur = False; sc0.render.motion_blur_shutter = 0.5
sc0.render.image_settings.file_format = "PNG"; sc0.render.image_settings.color_depth = "8"; sc0.render.image_settings.compression = 15
sc0.frame_set(0)
D = bpy.data
for o in list(D.objects):
    if o.name.startswith(("gull", "TCam", "PhotoCam")) or (o.type == 'CAMERA' and o.name != "Camera_Main"):
        D.objects.remove(o, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
n = 0
for im in list(D.images):
    if im.source not in ('FILE', 'GENERATED') or im.name in ("Render Result", "Viewer Node"): continue
    if im.filepath.lower().endswith(".hdr"): continue
    if im.name == "Photo_Iceberg": continue
    w, h = im.size
    if w == 0: continue
    data = im.colorspace_settings.name in ("Non-Color", "Linear Rec.709") or im.filepath.lower().endswith(".exr")
    s = min(1.0, 1024 / max(w, h))
    if s < 1.0: im.scale(max(1, int(w * s)), max(1, int(h * s)))
    alpha = im.channels == 4 and not im.filepath.lower().endswith((".jpg", ".jpeg")) and any(k in im.name.lower() for k in ("eyebrow", "eyelash", "hair", "short0", "lash", "brow"))
    ext = "png" if alpha else "jpg"
    p = os.path.join(TMP, "%03d_%s.%s" % (n, bpy.path.clean_name(im.name)[:40], ext)); n += 1
    cs = im.colorspace_settings.name; am = im.alpha_mode
    try:
        im.filepath_raw = p; im.file_format = 'PNG' if alpha else 'JPEG'; im.save(filepath=p, quality=88)
    except Exception as e:
        print("SKIP", im.name, e); continue
    nim = D.images.load(p); nim.colorspace_settings.name = cs; nim.alpha_mode = am
    im.user_remap(nim); D.images.remove(im)
print("RECODED", n)
sys.argv = [sys.argv[0], "--", OUT]
exec(open(PKG).read())
