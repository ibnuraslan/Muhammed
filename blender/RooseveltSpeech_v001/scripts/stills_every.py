"""blender -b film.blend --python stills_every.py -- <out_dir> <every_n_frames> [w]   (8-sample review stills, frame 1 to end)"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; N = int(a[1]); W = int(a[2]) if len(a) > 2 else 270
os.makedirs(OUT, exist_ok=True); sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, round(W * 16 / 9), 100
sc.cycles.samples = 8; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
i = 0
for f in range(sc.frame_start, sc.frame_end + 1, N):
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i); bpy.ops.render.render(write_still=True); i += 1
print("STILLS", i)
