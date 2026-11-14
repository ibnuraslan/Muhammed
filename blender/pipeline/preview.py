"""Cheap MOVING preview for review (no GPU needed).

blender -b Film_60fps.blend --python blender/pipeline/preview.py -- OUT_DIR [step=5] [max_frames]

Renders every `step`-th frame at 270x480, Cycles 4 samples + OIDN denoise, frame number burned in.
Workbench needs a GPU (libEGL) and fails in the cloud containers, so this uses Cycles.
Then run pipeline/watch_pages.sh OUT_DIR to get an MP4 at real speed plus contact pages,
and WATCH EVERY PAGE before approving or delivering anything.
"""
import bpy, sys, time

a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
step = int(a[1]) if len(a) > 1 else 5
sc = bpy.context.scene
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 270, 480, 100
r.engine = 'CYCLES'
sc.cycles.samples = 4
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
r.use_simplify = True
r.simplify_subdivision_render = 0
r.image_settings.file_format = 'JPEG'
# burn in the frame number so every review note can quote an exact frame
r.use_stamp = True
for k in ("date", "time", "render_time", "camera", "lens", "scene", "filename", "memory", "hostname", "marker", "sequencer_strip", "note", "frame_range"):
    if hasattr(r, "use_stamp_" + k):
        setattr(r, "use_stamp_" + k, False)
r.use_stamp_frame = True
r.stamp_font_size = 12
sc.frame_step = step
if len(a) > 2:
    sc.frame_end = min(sc.frame_end, sc.frame_start + step * int(a[2]) - 1)
r.filepath = out.rstrip("/") + "/f_"
t = time.time()
bpy.ops.render.render(animation=True)
print("PREVIEW_DONE", out, "frames", sc.frame_start, sc.frame_end, "step", step, "took %.0fs" % (time.time() - t))
