"""GameBoxBullet v012 stage C: slim the package before packing (dedupe appended images, shrink background textures).
blender -b anim.blend --python 03_slim.py -- <out.blend>"""
import bpy, sys, re
out = sys.argv[sys.argv.index("--") + 1]
# 1. the four shrubs and the plant were appended separately: point every duplicate image (name.001 ...) at the first copy
by = {}
for im in list(bpy.data.images):
    base = re.sub(r"\.\d{3}$", "", im.name)
    if base in by and tuple(by[base].size) == tuple(im.size):
        im.user_remap(by[base]); bpy.data.images.remove(im)
    else:
        by.setdefault(base, im)
# 2. background / small-on-screen textures to 512 px (characters, garments and hero props keep their size)
SMALL = ("shrub_", "potted_plant_", "sofa_02", "teeth", "tongue", "shoes0", "sss")
for im in bpy.data.images:
    if any(k in im.name for k in SMALL) and im.size[0] > 512:
        im.scale(512, 512); im.pack()
# normal maps of the garments to 1024
for im in bpy.data.images:
    if ("norm" in im.name.lower() or "NORM" in im.name) and im.size[0] > 1024:
        im.scale(1024, 1024); im.pack()
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SLIM_OK", out)
