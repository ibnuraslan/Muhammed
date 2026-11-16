"""Shrink the package: dedupe identical images (.001/.002 copies), cap textures (characters 2048, everything else 1024),
re-pack opaque images as JPEG (q90); images with real alpha (hair, lashes, brows, leaves, logos) stay PNG.
blender -b pre.blend --python 06_shrink.py -- out.blend"""
import bpy, sys, os, re, tempfile
OUT = sys.argv[sys.argv.index("--") + 1]
TMP = tempfile.mkdtemp(prefix="shrink_")
# ---- dedupe by base name + size
groups = {}
for im in bpy.data.images:
    if im.source != 'FILE' or (not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath))): continue
    base = re.sub(r"\.\d{3}$", "", im.name)
    groups.setdefault((base, tuple(im.size), im.packed_file.size if im.packed_file else bpy.path.abspath(im.filepath)), []).append(im)
n_d = 0
for key, ims in groups.items():
    keep = ims[0]
    for d in ims[1:]:
        d.user_remap(keep); n_d += 1
bpy.ops.outliner.orphans_purge(do_recursive=True)
print("DEDUPED", n_d)
CHAR = ("diffuse", "normal", "sss", "eyebrow", "lashes", "long01", "bob", "afro", "ponytail", "short0", "braid", "skin", "eye", "teeth")
n_j = n_p = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    is_char = any(k in im.name.lower() for k in CHAR) and not im.name.lower().startswith(("fir_", "wooden_", "flood", "tool_", "shelf", "armchair"))
    cap = 2048 if is_char else (512 if ("nor" in im.name.lower() or "rough" in im.name.lower()) else 1024)
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s)))
    px = im.pixels[:]
    has_alpha = im.channels == 4 and any(px[i] < 0.98 for i in range(3, len(px), 4 * 7))
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", im.name)
    if has_alpha:
        p = os.path.join(TMP, name + ".png"); im.file_format = 'PNG'
        im.save(filepath=p); n_p += 1
    else:
        p = os.path.join(TMP, name + ".jpg"); im.file_format = 'JPEG'
        im.save(filepath=p, quality=90); n_j += 1
    cs = im.colorspace_settings.name
    if im.packed_file: im.unpack(method='REMOVE')
    im.filepath = p; im.source = 'FILE'; im.reload(); im.colorspace_settings.name = cs; im.pack()
print("REPACKED jpeg", n_j, "png", n_p)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SHRUNK", OUT, os.path.getsize(OUT) // 2**20, "MB")
