"""blender -b film.blend --python frames.py -- out_dir t1 t2 ...  (seconds; review stills 270x480 8spp)"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; os.makedirs(a[0], exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.cycles.samples = 8; sc.render.use_motion_blur = False; sc.render.image_settings.file_format = "JPEG"
for t in a[1:]:
    f = 1 + round(float(t) * 60); sc.frame_set(f); sc.render.filepath = os.path.join(a[0], "f_%06.2f.jpg" % float(t)); bpy.ops.render.render(write_still=True)
