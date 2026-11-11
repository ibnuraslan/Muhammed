"""Review stills at given seconds. blender -b film.blend --python stills_at.py -- <out_dir> t1 t2 ..."""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"
for i, t in enumerate(a[1:]):
    sc.frame_set(1 + round(float(t) * 60)); sc.render.filepath = os.path.join(OUT, "t%02d_%05.1f.jpg" % (i, float(t)))
    bpy.ops.render.render(write_still=True)
