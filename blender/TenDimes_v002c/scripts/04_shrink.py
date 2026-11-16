"""Shrink packed textures so the package stays < 95 MB.
blender -b in.blend --python 04_shrink.py -- out.blend
- images whose alpha is really used (hair/brow/lash cards, leaves, logo: min alpha < 0.98) stay PNG with alpha (LESSONS s3)
- everything else -> JPEG q88; normal / roughness / AO maps -> max 512 px, colour maps -> max 1024 px."""
import bpy, sys, os, numpy as np, tempfile
out = sys.argv[sys.argv.index("--") + 1]
tmp = tempfile.mkdtemp()
bpy.ops.outliner.orphans_purge(do_recursive=True)
n_j = n_k = 0; before = after = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    if not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)): continue
    before += im.packed_file.size if im.packed_file else 0
    w, h = im.size; ch = im.channels
    px = np.empty(w * h * ch, dtype=np.float32); im.pixels.foreach_get(px)
    has_alpha = ch == 4 and px[3::4].min() < 0.98
    nm = im.name.lower()
    data = any(k in nm for k in ("nor", "normal", "rough", "_ao", "ao_", "disp", "spec", "metal", "bump"))
    charmap = any(k in nm for k in ("skin", "male", "female", "suit", "eye", "brow", "lash", "short", "bob", "teeth", "tongue"))
    mx = 512 if (data or not charmap) else 1024
    if has_alpha or "dakras" in nm:
        n_k += 1
        if w > 1024: im.scale(1024, int(1024 * h / w))
        continue
    if w > mx: im.scale(mx, max(1, int(mx * h / w)))
    p = os.path.join(tmp, "%04d.jpg" % n_j); n_j += 1
    cs = im.colorspace_settings.name
    im.filepath_raw = p; im.file_format = 'JPEG'
    im.save(filepath=p, quality=88)
    new = bpy.data.images.load(p); new.colorspace_settings.name = cs; new.pack()
    new.alpha_mode = im.alpha_mode
    im.user_remap(new); nm0 = im.name; bpy.data.images.remove(im); new.name = nm0
    after += new.packed_file.size
print("SHRINK jpeg", n_j, "kept-alpha", n_k, "MB before %.1f after(jpeg part) %.1f" % (before / 1e6, after / 1e6))
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
