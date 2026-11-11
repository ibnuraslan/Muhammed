"""Before packing: merge duplicate images (x.png.001 -> x.png) and cap texture sizes so the package stays ~150 MB.
blender -b anim.blend --python slim_textures.py -- out.blend
Skins and hair stay at 2K (faces fill the frame in close-ups); every other image is capped at 1K. HDRIs are untouched."""
import sys, re, bpy
out = sys.argv[sys.argv.index("--") + 1]
# 1. duplicates: same file on disk
by_path = {}
for im in list(bpy.data.images):
    if im.source != "FILE": continue
    key = bpy.path.abspath(im.filepath)
    if key in by_path and by_path[key] is not im:
        im.user_remap(by_path[key]); bpy.data.images.remove(im)
    else:
        by_path[key] = im
n = 0
for im in bpy.data.images:
    if im.source != "FILE" or im.name.lower().endswith((".hdr", ".exr")) or im.size[0] == 0: continue
    keep2k = any(k in im.name.lower() for k in ("skin", "lightskinned", "diffuse")) and any(k in im.name.lower() for k in ("young", "short02", "ponytail", "skin"))
    cap = 2048 if keep2k else 1024
    w, h = im.size
    if max(w, h) > cap:
        s = cap / max(w, h); im.scale(int(w * s), int(h * s)); im.pack(); n += 1
print("SLIM scaled", n, "images; total images", len(bpy.data.images))
bpy.ops.wm.save_as_mainfile(filepath=out)
