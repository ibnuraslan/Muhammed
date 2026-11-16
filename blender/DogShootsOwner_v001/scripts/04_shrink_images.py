"""Shrink packed images so the package fits under 95 MB (clean animated look needs no 1k normal/rough/disp detail).
blender -b pkg.blend --python 04_shrink_images.py -- <tmp_dir> <out.blend>
- normal / roughness / displacement / ao maps: 512 px, JPEG q85
- colour maps with no transparency: original size (max 1024), JPEG q88
- images that use alpha (leaves, needles, grass, hair, brows, lashes, logos): PNG kept, Image.save() (keeps alpha), max 1024
"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]
TMP, OUT = a
os.makedirs(TMP, exist_ok=True)
DATA = ("nor", "rough", "disp", "_ao", "spec", "bump", "metal")
before = sum(i.packed_file.size for i in bpy.data.images if i.packed_file)
n = 0
for img in list(bpy.data.images):
    if not img.packed_file or img.size[0] == 0: continue
    nm = img.name.lower()
    if "dakrasfilms" in nm: continue                     # logo stays untouched
    w, h = img.size
    px = img.pixels[:]
    has_alpha = img.channels == 4 and min(px[3::4]) < 0.98
    is_data = any(k in nm for k in DATA)
    if is_data:
        tw = min(w, 512); fmt = 'JPEG'
    elif has_alpha:
        tw = min(w, 1024); fmt = 'PNG'
    else:
        tw = min(w, 1024); fmt = 'JPEG'
    th = max(1, round(h * tw / w))
    if (tw, th) != (w, h): img.scale(tw, th)
    base = "".join(c if c.isalnum() else "_" for c in img.name)
    path = os.path.join(TMP, base + (".jpg" if fmt == 'JPEG' else ".png"))
    cs = img.colorspace_settings.name
    img.filepath_raw = path; img.file_format = fmt
    sc = bpy.context.scene
    if fmt == 'JPEG':
        sc.render.image_settings.quality = 85 if is_data else 88
    img.save(filepath=path, quality=85 if is_data else 88) if fmt == 'JPEG' else img.save(filepath=path)
    img.unpack(method='REMOVE') if img.packed_file else None
    img.filepath = path; img.source = 'FILE'; img.reload(); img.colorspace_settings.name = cs
    img.pack()
    n += 1
after = sum(i.packed_file.size for i in bpy.data.images if i.packed_file)
print("SHRINK", n, "images", before // 2**20, "MB ->", after // 2**20, "MB")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, relative_remap=True)
print("SHRINK SAVED", OUT, os.path.getsize(OUT) // 2**20, "MB")
