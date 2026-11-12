"""Render F-1 and F at each camera cut. blender -b pkg.blend --python cut_strips.py -- <out_dir> f1 f2 ..."""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.image_settings.file_format = 'JPEG'
for F in a[1:]:
    for f in (int(F) - 1, int(F)):
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "f%05d.jpg" % f); bpy.ops.render.render(write_still=True)
print("STRIPS_DONE")
