"""blender -b anim.blend --python stills_frames.py -- <out_dir> <w> f1 f2 ...  (8 samples review stills)"""
import sys, os, time, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; W = int(a[1]); FR = [int(x) for x in a[2:]]
os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for f in FR:
    t = time.time(); sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "f%04d.jpg" % f)
    bpy.ops.render.render(write_still=True); print("STILL", f, round(time.time() - t, 1), "s")
