"""Render single frames from a baked shot .blend (or the film master) for checks.
  python edit/blend_frames.py <file.blend> <outdir> <pct> <samples> <frame> [frame ...]"""
import sys, os, bpy
path, out, pct, smp = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
bpy.ops.wm.open_mainfile(filepath=path)
s = bpy.context.scene
s.render.resolution_percentage = pct
if s.render.engine == 'CYCLES':
    s.cycles.samples = smp
for sc in bpy.data.scenes:
    if sc.render.engine == 'CYCLES':
        sc.cycles.samples = smp
    sc.render.resolution_percentage = pct
os.makedirs(out, exist_ok=True)
s.render.image_settings.file_format = 'PNG'
for f in sys.argv[5:]:
    s.frame_set(int(f)); s.render.filepath = os.path.join(os.path.abspath(out), f"f{int(f):05d}.png")
    bpy.ops.render.render(write_still=True); print("[frame]", s.render.filepath, flush=True)
