import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; sc = bpy.context.scene; f = int(a[1])
sc.render.resolution_x, sc.render.resolution_y = 540, 960; sc.cycles.samples = 8
sc.frame_set(f); ms = [m for m in sc.timeline_markers if m.camera and m.frame <= f]; sc.camera = max(ms, key=lambda m: m.frame).camera
sc.render.image_settings.file_format = 'JPEG'; sc.render.filepath = a[0]; bpy.ops.render.render(write_still=True)
