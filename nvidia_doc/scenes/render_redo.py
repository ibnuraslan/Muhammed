"""Resumable renderer for the Ch4-5 redo patches. Renders the frames of one patch that are not on disk yet, stops
before the time budget runs out (default 25 min, chunks stay under 30), and encodes the MP4 when all frames exist.
  python scenes/render_redo.py c4_03 [--budget 1500] [--first 1 --last 288]
  -> out/ch45_redo_render/c4_03/f_00001.png ...   out/ch45_redo_render/c4_03.mp4  (H.264 CRF 16, yuv420p, 24 fps)
Run it again (or in a loop) until it prints DONE. A frame is written to a temp name and renamed when complete,
so a chunk killed mid-frame never leaves a broken PNG behind."""
import os, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
sid = sys.argv[1]
arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
BUDGET = arg("--budget", 1500.0)
PATCH = os.path.join(ROOT, "out", "deliver", "ch45_redo", f"{sid}_patch.blend")
OUT = os.path.join(ROOT, "out", "ch45_redo_render", sid); os.makedirs(OUT, exist_ok=True)
MP4 = os.path.join(ROOT, "out", "ch45_redo_render", f"{sid}.mp4")
import bpy
t0 = time.time()
bpy.ops.wm.open_mainfile(filepath=PATCH)
m = [s for s in bpy.data.scenes if s.name.startswith("PATCH_")][0]
bpy.context.window.scene = m if bpy.context.window else None
first, last = arg("--first", m.frame_start), arg("--last", m.frame_end)
todo = [f for f in range(first, last + 1) if not os.path.exists(os.path.join(OUT, f"f_{f:05d}.png"))]
print(f"[render] {sid}: {len(todo)} of {last - first + 1} frames left", flush=True)
per = None
for f in todo:
    if per is not None and time.time() - t0 + per * 1.2 > BUDGET:
        print(f"[render] {sid}: budget reached, {len(todo) - todo.index(f)} frames left — run again", flush=True)
        sys.exit(0)
    a = time.time()
    m.frame_set(f)
    m.render.filepath = os.path.join(OUT, f"tmp_{f:05d}.png")
    bpy.ops.render.render(write_still=True, scene=m.name)
    os.replace(os.path.join(OUT, f"tmp_{f:05d}.png"), os.path.join(OUT, f"f_{f:05d}.png"))
    dt = time.time() - a; per = dt if per is None else 0.7 * per + 0.3 * dt
    print(f"[render] {sid} frame {f} {dt:.1f}s", flush=True)
n = m.frame_end - m.frame_start + 1
have = len([x for x in os.listdir(OUT) if x.startswith("f_") and x.endswith(".png")])
if have >= n:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "24", "-start_number", str(m.frame_start),
                    "-i", os.path.join(OUT, "f_%05d.png"), "-frames:v", str(n), "-c:v", "libx264", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-r", "24", "-movflags", "+faststart", MP4], check=True)
    print(f"[render] {sid} DONE {n} frames -> {MP4}", flush=True)
