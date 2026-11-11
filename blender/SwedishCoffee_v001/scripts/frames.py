"""Render chosen frames at 270x480 / 8 spp.  blender -b film.blend --python frames.py -- <out_dir> f1 f2 ...  (or 'step:60')"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
fr = list(range(sc.frame_start, sc.frame_end + 1, int(a[1][5:]))) if a[1].startswith("step:") else [int(x) for x in a[1:]]
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for i, f in enumerate(fr):
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "f%04d.jpg" % f)
    bpy.ops.render.render(write_still=True)
print("DONE", len(fr))
