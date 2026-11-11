"""blender -b film.blend --python stills_at.py -- <out_dir> t1 t2 ... (seconds)"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"
for i, t in enumerate(a[1:]):
    sc.frame_set(1 + round(float(t) * 60)); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i); bpy.ops.render.render(write_still=True)
