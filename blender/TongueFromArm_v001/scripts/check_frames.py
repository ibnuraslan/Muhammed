"""render frames at W x 16:9, Cycles 8 spp. blender -b film.blend --python check_frames.py -- OUT_DIR W f1,f2,..."""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; out = a[0]; os.makedirs(out, exist_ok=True); W = int(a[1])
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, round(W * 16 / 9), 100
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8; sc.cycles.use_denoising = True; r.image_settings.file_format = 'JPEG'; sc.render.use_motion_blur = False
for f in [int(x) for x in a[2].split(",")]:
    sc.frame_set(f); r.filepath = os.path.join(out, "f%04d.jpg" % f); bpy.ops.render.render(write_still=True)
