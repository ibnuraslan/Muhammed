import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; res = int(a[1])
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = res, res * 16 // 9; sc.cycles.samples = 16
for f in a[2:]:
    sc.frame_set(int(f)); sc.render.filepath = "%s_f%04d.png" % (out, int(f)); bpy.ops.render.render(write_still=True)
