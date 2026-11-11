"""Shrink packed/linked textures before packaging so the .blend stays ~150 MB.
Skins: 2K JPEG (q92). Everything else larger than 1K: scaled to 1K, PNG kept (alpha for hair/brows/lashes survives).
blender -b film.blend --python 07_slim_textures.py -- <tmp_dir> <out.blend>"""
import sys, os
import bpy
a = sys.argv[sys.argv.index("--") + 1:]; TMP, OUT = a[0], a[1]
os.makedirs(TMP, exist_ok=True)
n = 0
for im in list(bpy.data.images):
    if im.source != 'FILE' or im.size[0] == 0: continue
    w, h = im.size
    skin = "skinned" in im.name and "diffuse" in im.name
    if skin:
        dst = os.path.join(TMP, os.path.splitext(im.name)[0] + ".jpg")
        im.filepath_raw = dst; im.file_format = 'JPEG'
        sc = bpy.context.scene; sc.render.image_settings.quality = 92
        im.save(filepath=dst, quality=92) if 'quality' in im.save.__doc__ else im.save()
    elif max(w, h) > 1024:
        im.scale(1024, max(1, int(h * 1024 / w)))
        dst = os.path.join(TMP, os.path.splitext(im.name)[0] + ".png")
        im.filepath_raw = dst; im.file_format = 'PNG'; im.save()
    else:
        continue
    if im.packed_file: im.unpack(method='REMOVE') if False else None
    im.filepath = dst; im.reload(); n += 1
print("SLIM", n, "images")
bpy.ops.wm.save_as_mainfile(filepath=OUT)
