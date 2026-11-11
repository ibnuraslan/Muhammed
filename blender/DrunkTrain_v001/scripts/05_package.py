"""Shrink, pack and save the farm file (keeps it under ~95 MB for a plain git commit; no LFS).
blender -b anim.blend --python 05_package.py -- <out_dir>/DrunkTrain_v00N_60fps.blend
Then verify with --factory-startup."""
import sys, os
import bpy
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
# 1K JPEG textures (the HDRI stays 2K: it is the sky in many shots)
TMP = os.path.join(os.path.dirname(out), "_tex1k"); os.makedirs(TMP, exist_ok=True)
n_done = 0
for im in list(bpy.data.images):
    if im.source != 'FILE': continue
    if "bloem" in im.name.lower() or im.filepath.lower().endswith(".hdr"): continue
    try:
        w, h = im.size
    except Exception:
        continue
    if w == 0: continue
    alpha = im.name.lower().endswith(".png") and ("alpha" in im.name.lower() or im.alpha_mode != 'NONE' and "leaves" in im.name.lower())
    if max(w, h) > 1024:
        s_ = 1024 / max(w, h); im.scale(max(1, int(w * s_)), max(1, int(h * s_)))
    if "alpha" in im.name.lower() or "leaves" in im.name.lower():
        ext, fmt = ".png", 'PNG'
    else:
        ext, fmt = ".jpg", 'JPEG'
    pth = os.path.join(TMP, "".join(c if c.isalnum() else "_" for c in im.name) + ext)
    im.filepath_raw = pth; im.file_format = fmt
    if fmt == 'JPEG': bpy.context.scene.render.image_settings.quality = 88
    im.save(); im.filepath = pth; im.reload(); n_done += 1
print("TEXTURES re-saved at <=1K:", n_done)
for _ in range(3):
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
# no helper renders: the look-dev camera and hidden collections
for o in bpy.data.objects:
    if o.type == 'CAMERA' and o is not sc.camera: bpy.data.objects.remove(o, do_unlink=True)
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline", "package_for_farm.py")).read().replace(
    'out = sys.argv[sys.argv.index("--") + 1]', 'pass'))
