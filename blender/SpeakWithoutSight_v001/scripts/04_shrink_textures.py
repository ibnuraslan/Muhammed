"""Re-encode opaque textures as JPEG (q92) so the packed farm file stays under ~150 MB; alpha textures (hair, leaves, lashes, brows) stay PNG.
blender -b anim.blend --python 04_shrink_textures.py -- <tmp_dir> <out.blend>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
TMP, OUT = a[0], a[1]; os.makedirs(TMP, exist_ok=True)
KEEP = ("hair", "ponytail", "braid", "long01", "short0", "bob0", "leaves", "eyelash", "eyebrow", "lashes", "brow", "flame", "glass")
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or not im.filepath: continue
    p = bpy.path.abspath(im.filepath); low = (im.name + p).lower()
    if p.lower().endswith((".hdr", ".exr")) and "nor_gl" not in low and "rough" not in low: continue
    if any(k in low for k in KEEP): continue
    if p.lower().endswith((".jpg", ".jpeg")) and im.size[0] <= 2048: continue
    try:
        im.reload(); _ = im.pixels[0]
    except Exception as e:
        print("SKIP", im.name, e); continue
    cs = im.colorspace_settings.name
    out = os.path.join(TMP, "%03d_%s.jpg" % (n, bpy.path.clean_name(os.path.splitext(im.name)[0])))
    im.filepath_raw = out; im.file_format = 'JPEG'
    sc = bpy.context.scene; sc.render.image_settings.quality = 92
    try:
        im.save(quality=92) if 'quality' in im.save.__doc__ else im.save()
    except TypeError:
        im.save()
    im.filepath = out; im.reload(); im.colorspace_settings.name = cs; im.alpha_mode = 'NONE'; n += 1
print("SHRUNK", n)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
