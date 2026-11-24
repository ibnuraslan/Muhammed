"""Farm packaging, step 1 (one Blender per shot): copy a built shot into the delivery folder with every external
image it uses copied beside it (capped at 2K) and its paths made relative, so the folder renders anywhere.

    blender -b shots/P1/S01.blend --python tools/pack_shot.py -- <PKG dir>
    -> <PKG>/shots/S01.blend, <PKG>/tex/<images>
"""
import os, sys, shutil
import bpy

PKG = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
SHOTS, TEX = os.path.join(PKG, "shots"), os.path.join(PKG, "tex")
os.makedirs(SHOTS, exist_ok=True); os.makedirs(TEX, exist_ok=True)
sid = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
sc = bpy.data.scenes[0]
sc.name = sid
missing = []
for im in bpy.data.images:
    if im.source not in ('FILE', 'SEQUENCE', 'MOVIE') or im.packed_file or not im.filepath:
        continue
    src = bpy.path.abspath(im.filepath, library=im.library)
    if not os.path.exists(src):
        missing.append(src); continue
    base = os.path.basename(src)
    # same name, different file: keep both
    stem, ext = os.path.splitext(base)
    rel_dir = os.path.basename(os.path.dirname(src))
    name = f"{rel_dir}__{stem}{ext}" if rel_dir else base
    dst = os.path.join(TEX, name)
    if not os.path.exists(dst):
        w, h = im.size[:] if im.size[0] else (0, 0)
        if max(w, h) > 2048 and ext.lower() in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = None
            pil = Image.open(src)
            f = 2048 / max(pil.size)
            pil = pil.resize((max(1, int(pil.size[0] * f)), max(1, int(pil.size[1] * f))), Image.LANCZOS)
            pil.save(dst, quality=92) if ext.lower() in (".jpg", ".jpeg") else pil.save(dst)
        else:
            shutil.copy2(src, dst)
    im.filepath = "//../tex/" + name
for lib in bpy.data.libraries:
    missing.append("LIBRARY " + lib.filepath)
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not f.packed_file:
        f.pack()
for snd in bpy.data.sounds:
    if not snd.packed_file:
        snd.pack()
out = os.path.join(SHOTS, sid + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, relative_remap=False, copy=True)
print("PACKED", sid, out, "missing:", missing, flush=True)
