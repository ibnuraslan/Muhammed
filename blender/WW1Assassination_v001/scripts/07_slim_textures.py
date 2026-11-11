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
    lname = im.name.lower()
    skin = ("skinned" in lname and "diffuse" in lname) or any(k in lname for k in ("normal", "_ao", "rough", "sss", "specular", "nor_gl", "bump", "suit", "shoes", "fedora", "teeth", "tongue", "image_", "gallinera", "diffuse")) and not any(h in lname for h in ("short0", "bob0", "long0", "braid", "ponytail", "afro", "eyebrow", "eyelash", "brow", "lash")) and not lname.endswith(".jpg")
    if skin:
        if max(w, h) > 1024 and not ("skinned" in lname and "diffuse" in lname):
            im.scale(1024, max(1, int(h * 1024 / w)))
        dst = os.path.join(TMP, os.path.splitext(im.name)[0] + ".jpg")
        im.filepath_raw = dst; im.file_format = 'JPEG'
        sc = bpy.context.scene; sc.render.image_settings.quality = 85
        im.save(filepath=dst, quality=85) if 'quality' in im.save.__doc__ else im.save()
    elif max(w, h) > 1024:
        im.scale(1024, max(1, int(h * 1024 / w)))
        dst = os.path.join(TMP, os.path.splitext(im.name)[0] + ".png")
        im.filepath_raw = dst; im.file_format = 'PNG'; im.save()
    else:
        continue
    if im.packed_file: im.unpack(method='REMOVE') if False else None
    im.filepath = dst; im.reload(); n += 1
print("SLIM", n, "images")
# lossless key thinning: drop interior keys inside runs of equal values (planted feet, poles, held props, visibility)
removed = 0; total = 0
for act in bpy.data.actions:
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    kps = fc.keyframe_points; nk = len(kps); total += nk
                    if nk < 3: continue
                    vals = [kp.co[1] for kp in kps]
                    drop = [i for i in range(1, nk - 1) if abs(vals[i] - vals[i - 1]) < 1e-6 and abs(vals[i] - vals[i + 1]) < 1e-6]
                    for i in reversed(drop):
                        kps.remove(kps[i], fast=True)
                    removed += len(drop)
                    if drop: fc.update()
print("KEYS removed", removed, "of", total)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
