import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; f0, f1, st = int(a[1]), int(a[2]), int(a[3])
os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 270, 480; sc.cycles.samples = 8; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"; sc.cycles.texture_limit_render = "1024"
for i, f in enumerate(range(f0, f1 + 1, st)):
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % f); bpy.ops.render.render(write_still=True)
