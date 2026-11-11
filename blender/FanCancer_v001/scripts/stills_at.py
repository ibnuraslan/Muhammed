"""blender -b film.blend --python stills_at.py -- <out_dir> t1 t2 ...  (seconds) -> 270x480, 8 samples"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for t in a[1:]:
    f = 1 + round(float(t) * 60); sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "t%05.1f.jpg" % float(t))
    bpy.ops.render.render(write_still=True)
print("DONE_STILLS")
