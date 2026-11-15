"""QA scan for rendered redo frames: per-frame mean luma, the jump to the next frame, and render time (from a log of
'[render] <id> frame N <s>s' lines). Flags frames whose luma or difference jumps against their neighbours, or that
rendered much faster than the shot's median (a sign of the intermittent black-glass corruption seen by W3).
  python edit/qa_frames.py c4_08 [--log path/to/w0.log]   -> prints flagged frame numbers (empty = clean)"""
import os, sys, re, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sid = sys.argv[1]
log = sys.argv[sys.argv.index("--log") + 1] if "--log" in sys.argv else None
fs = sorted(glob.glob(os.path.join(ROOT, "out", "ch45_redo_render", sid, "f_*.png")))
nums = [int(os.path.basename(f)[2:7]) for f in fs]
lum = {}
prev = None; diff = {}
for n, f in zip(nums, fs):
    a = np.asarray(Image.open(f).convert("L").resize((480, 204)), np.float32) / 255
    lum[n] = a.mean()
    if prev is not None and prev[0] == n - 1:
        diff[n] = float(np.abs(a - prev[1]).mean())
    prev = (n, a)
times = {}
if log and os.path.exists(log):
    for l in open(log):
        m = re.match(rf"\[render\] {sid} frame (\d+) ([\d.]+)s", l)
        if m:
            times[int(m[1])] = float(m[2])          # last render of a frame wins
flags = {}
ln = np.array([lum[n] for n in nums])
for i, n in enumerate(nums):
    nb = [lum[m] for m in (n - 2, n - 1, n + 1, n + 2) if m in lum]
    if nb and abs(lum[n] - np.median(nb)) > max(0.03, 0.12 * np.median(nb)):
        flags.setdefault(n, []).append(f"luma {lum[n]:.3f} vs nbrs {np.median(nb):.3f}")
dv = np.array(list(diff.values())) if diff else np.array([0.0])
dmed = float(np.median(dv))
for n, d in diff.items():
    if d > max(0.02, 4 * dmed):
        flags.setdefault(n, []).append(f"jump {d:.3f} (median {dmed:.3f})")
if times:
    tmed = float(np.median(list(times.values())))
    for n, t in times.items():
        if t < 0.6 * tmed:
            flags.setdefault(n, []).append(f"fast {t:.0f}s (median {tmed:.0f}s)")
print(f"{sid}: {len(nums)} frames, luma {ln.min():.3f}-{ln.max():.3f}, median diff {dmed:.4f}"
      + (f", median {np.median(list(times.values())):.0f} s/frame" if times else ""))
for n in sorted(flags):
    print(f"  FLAG f_{n:05d}: " + "; ".join(flags[n]))
print("FLAGGED:", " ".join(str(n) for n in sorted(flags)) or "none")
