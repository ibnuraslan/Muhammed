import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; sc = bpy.context.scene
r = sc.render; r.resolution_percentage = 50; sc.cycles.samples = 24; r.image_settings.file_format = 'JPEG'
for f in a[1:]:
    sc.frame_set(int(f)); r.filepath = a[0] + "_%s.jpg" % f; bpy.ops.render.render(write_still=True)
