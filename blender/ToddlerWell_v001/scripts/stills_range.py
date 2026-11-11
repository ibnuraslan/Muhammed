"""Like pipeline/stills.py but only renders the given still indices (resume / partial re-render).
blender -b film.blend --python stills_range.py -- <out_dir> <step_s> <i0-i1>[,<i0-i1>...]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]; OUT, STEP = a[0], float(a[1])
idx = []
for part in a[2].split(","):
    lo, hi = map(int, part.split("-")); idx += list(range(lo, hi + 1))
sc = bpy.context.scene; fps = sc.render.fps / sc.render.fps_base
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for i in idx:
    f = sc.frame_start + round(i * STEP * fps)
    if f > sc.frame_end: break
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i); bpy.ops.render.render(write_still=True)
print("STILLS done", len(idx))
