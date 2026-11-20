"""Render a shot's first, middle and last frame (25%, 16 spp) for the hands/arms audit."""
import sys, os, bpy
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; sc.render.resolution_percentage = 25; sc.cycles.samples = 16
sid = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
for f in sorted({sc.frame_start, (sc.frame_start + sc.frame_end) // 2, sc.frame_end}):
    sc.frame_set(f); sc.render.filepath = os.path.join(out, f"{sid}_{f:04d}.png"); bpy.ops.render.render(write_still=True)
print("AUDITED", sid, flush=True)
