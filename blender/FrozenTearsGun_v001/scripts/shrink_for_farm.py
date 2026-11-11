"""Shrink before packaging (studio cap 95 MB, no LFS): textures to 1K (2K kept for her face skin), HDRI to 1K, orphans purged.
blender -b film.blend --python shrink_for_farm.py -- out.blend   (then run pipeline/package_for_farm.py on out.blend)"""
import sys, bpy
out = sys.argv[sys.argv.index("--") + 1]
HERO = ("young_lightskinned_female_diffuse",)
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    w, h = im.size
    cap = 2048 if any(k in im.name for k in HERO) else 1024
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(max(1, int(w * s)), max(1, int(h * s)))
        im.pack(); n += 1
import os
TMP = os.path.join(os.path.dirname(os.path.abspath(out)), "shrink_tmp"); os.makedirs(TMP, exist_ok=True)
ALPHA = ("opacity", "alpha", "leaves", "hair", "eye", "brow", "ponytail", "lash")
sc = bpy.context.scene
sc.render.image_settings.quality = 90
j = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    nm = im.name.lower()
    if nm.endswith(".hdr") or ".hdr" in nm:
        fmt, ext = 'HDR', '.hdr'
    elif any(k in nm for k in ALPHA):
        continue
    else:
        fmt, ext = 'JPEG', '.jpg'
    path = os.path.join(TMP, "img%03d%s" % (j, ext)); j += 1
    if im.packed_file: pass
    im.filepath_raw = path; im.file_format = fmt
    try:
        im.save()
    except Exception as e:
        print("SKIP", im.name, e); continue
    if im.packed_file: im.unpack(method='REMOVE')
    im.filepath = path; im.reload(); im.pack()
print("REENCODED", j)
bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SHRUNK", n, "images")
