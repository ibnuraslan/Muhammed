"""Render the LAST frame of baked shots (small, fast) to check heads and arms after the bake.
  python tools/lastframe.py out/blend/ch2 out/last/ch2
"""
import os, sys, glob
import bpy
src, dst = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, "*.blend"))):
    name = os.path.basename(f)[:-6]
    if "_" not in name or name.split("_")[0] not in ("hint", "hx", "ward", "dining", "station", "press42", "court42", "pen"):
        continue
    o = os.path.join(dst, name, "plate.png")
    if os.path.exists(o): continue
    bpy.ops.wm.open_mainfile(filepath=f)
    s = bpy.context.scene
    s.frame_set(s.frame_end)
    s.render.resolution_percentage = 25; s.cycles.samples = 8; s.render.use_compositing = False
    os.makedirs(os.path.dirname(o), exist_ok=True); s.render.filepath = o
    bpy.ops.render.render(write_still=True)
    print("[last]", name, s.frame_end, flush=True)
