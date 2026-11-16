"""Same settings as pipeline/preview.py, but only the given edited-frame ranges (for splicing re-rendered ranges into
an existing preview). blender -b film.blend --python preview_ranges.py -- OUT_DIR STEP 721-851,941-1021,1101-1231"""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]; out, step = a[0], int(a[1]); rngs = [tuple(map(int, x.split("-"))) for x in a[2].split(",")]
sc = bpy.context.scene; r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 270, 480, 100
r.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
r.use_simplify = True; r.simplify_subdivision_render = 0; r.image_settings.file_format = 'JPEG'
r.use_stamp = True
for k in ("date", "time", "render_time", "camera", "lens", "scene", "filename", "memory", "hostname", "marker", "sequencer_strip", "note", "frame_range"):
    if hasattr(r, "use_stamp_" + k): setattr(r, "use_stamp_" + k, False)
r.use_stamp_frame = True; r.stamp_font_size = 12
for f0, f1 in rngs:
    for f in range(f0, f1 + 1, step):
        sc.frame_set(f); r.filepath = out.rstrip("/") + "/f_%04d.jpg" % f; bpy.ops.render.render(write_still=True)
print("RANGES_DONE", rngs)
