"""Preview-render a baked shot file exactly as delivered (keys, grade, textures), lighter settings.
  python scenes/preview_render.py out/blend/intro/home_behind.blend out/preview/intro/home_behind --pct 50 --samples 16 --step 2
"""
import os, sys
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
path, outdir = argv[0], argv[1]
arg = lambda k, d: type(d)(argv[argv.index(k) + 1]) if k in argv else d
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
s = bpy.context.scene
s.render.resolution_percentage = arg("--pct", 50)
s.cycles.samples = arg("--samples", 16)
s.cycles.use_denoising = True
s.render.use_motion_blur = False
s.cycles.device = 'CPU'
os.makedirs(outdir, exist_ok=True)
step = arg("--step", 2)
for f in range(s.frame_start, s.frame_end + 1, step):
    p = os.path.join(os.path.abspath(outdir), f"f{f:04d}.png")
    if os.path.exists(p):
        continue
    s.frame_set(f); s.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print("[preview]", p, flush=True)
