"""Shrink textures before packing (keeps the .blend under ~95 MB without LFS).
blender -b film.blend --python prep_package.py -- <tmp_tex_dir> <out.blend>
- Hero close-up maps (owner skin diffuse, suit diffuse): kept at 2048, re-encoded as JPEG.
- Everything else larger than 1024: scaled to 1024.
- Duplicate images (assets appended several times) are merged. Every map except alpha maps becomes JPEG 90 (Poly Haven 1K PNGs are 16-bit, about 4.7 MB each); the HDRI stays 2K .hdr.
Then purge orphans and save. Run package_for_farm.py on the result."""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; TMP, OUT = a[0], a[1]; os.makedirs(TMP, exist_ok=True)
HERO = ("middleage_lightskinned_male_diffuse", "male_elegantsuit01_diffuse")
# de-duplicate images appended several times (same source file)
seen = {}
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.packed_file or not im.filepath: continue   # GLB-embedded images share an empty path: never merge them
    k = bpy.path.abspath(im.filepath)
    if k in seen and seen[k].colorspace_settings.name == im.colorspace_settings.name:
        im.user_remap(seen[k]); bpy.data.images.remove(im)
    else: seen[k] = im
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.name.endswith(".hdr") or im.size[0] == 0 or im.packed_file: continue   # GLB-embedded maps are already compact; leave them
    w, h = im.size; base = os.path.splitext(im.name)[0]
    lim = 2048 if base.startswith(HERO) else 1024
    if base.startswith(("teeth", "tongue", "short02", "eyebrow", "eyelash")): lim = 512
    is_exr = im.filepath.lower().endswith(".exr") or im.file_format == 'OPEN_EXR'
    nc = im.colorspace_settings.name == 'Non-Color'
    is_png = im.filepath.lower().endswith(".png")
    if max(w, h) <= lim and not is_exr and not is_png: continue
    if max(w, h) > lim: im.scale(int(w * lim / max(w, h)), int(h * lim / max(w, h)))
    has_alpha = im.channels == 4 and im.alpha_mode != 'NONE' and (
        "alpha" in base or "opacity" in base or any(px < 0.99 for px in list(im.pixels[3::4])[::97]))
    if has_alpha:
        ext, fmt = ".png", 'PNG'
    else:
        ext, fmt = ".jpg", 'JPEG'
    p = os.path.join(TMP, base.replace('.', '_') + '_%d' % n + ext)
    im.filepath_raw = p; im.file_format = fmt
    sc = bpy.context.scene; sc.render.image_settings.quality = 90
    if fmt == 'JPEG':
        im.save(filepath=p, quality=90)
    else:   # alpha maps stay PNG (plain save: no view transform baked in)
        im.save(filepath=p)
    cs = im.colorspace_settings.name
    im.filepath = p; im.source = 'FILE'; im.reload(); im.colorspace_settings.name = cs
    n += 1
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
print("PREP shrunk", n, "images")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
