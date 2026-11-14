"""Moving preview frames: every STEP-th frame, 270x480, Cycles 4 samples + denoise. blender -b film.blend --python preview_frames.py -- <dir> [step]"""
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; OUT = a[0]; STEP = int(a[1]) if len(a) > 1 else 5
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 4; sc.cycles.use_denoising = True; sc.render.use_motion_blur = False
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for i, f in enumerate(range(sc.frame_start, sc.frame_end + 1, STEP)):
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "p%04d.jpg" % i); bpy.ops.render.render(write_still=True)
print("PREVIEW_DONE", i + 1)
