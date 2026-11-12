"""Like pipeline/stills.py but only still indices in the given ranges (same numbering).
blender -b film.blend --python stills_range.py -- <out_dir> <step_s> <i0:i1> [i0:i1 ...]"""
import sys, os, bpy
a = sys.argv[sys.argv.index("--") + 1:]
OUT, STEP = a[0], float(a[1]); RG = [tuple(int(x) for x in r.split(":")) for r in a[2:]]
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene; fps = sc.render.fps / sc.render.fps_base
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 270, 480, 100
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.use_motion_blur = False; sc.cycles.texture_limit_render = "1024"
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 85
for i0, i1 in RG:
    for i in range(i0, i1 + 1):
        f = sc.frame_start + round(i * STEP * fps)
        if f > sc.frame_end: break
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, "s%04d.jpg" % i)
        bpy.ops.render.render(write_still=True)
print("STILLS_RANGE_DONE")
