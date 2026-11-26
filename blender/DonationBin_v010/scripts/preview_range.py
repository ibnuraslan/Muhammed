"""= pipeline/preview.py (270x480, every 5th frame, Cycles 4 spp + OIDN, frame stamp) for a frame range, with subdivision 1
so eyelids, lashes and garment hems render as in the film (subdivision 0 showed false eye bands and torn hems)."""
import bpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
out, f0, f1 = a[0], int(a[1]), int(a[2])
sc = bpy.context.scene; r = sc.render
sc.frame_start, sc.frame_end = f0, f1
r.resolution_x, r.resolution_y, r.resolution_percentage = 270, 480, 100
r.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
r.use_simplify = True; r.simplify_subdivision_render = 1
r.image_settings.file_format = 'JPEG'
r.use_stamp = True
for k in ("date", "time", "render_time", "camera", "lens", "scene", "filename", "memory", "hostname", "marker", "sequencer_strip", "note", "frame_range"):
    if hasattr(r, "use_stamp_" + k): setattr(r, "use_stamp_" + k, False)
r.use_stamp_frame = True; r.stamp_font_size = 12
sc.frame_step = 5
r.filepath = out.rstrip("/") + "/f_"
bpy.ops.render.render(animation=True)
print("PREVIEW_DONE", f0, f1)
