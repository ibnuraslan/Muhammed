"""Assemble shot stills into one labelled sheet: python3 sheet.py <stills_dir> <out.jpg> [scale]
Stills are named Snn_FFFF.jpg (shotstills.py). Rows = shots (first, middle, last frame side by side), 4 shots per row."""
import sys, os, glob, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; k = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
shots = {}
for f in glob.glob(os.path.join(d, "*.jpg")):
    m = re.match(r"S(\d+)_(\d+)\.jpg", os.path.basename(f))
    if m: shots.setdefault(int(m.group(1)), []).append((int(m.group(2)), f))
W0, H0 = Image.open(next(iter(shots.values()))[0][1]).size; W, H = int(W0 * k), int(H0 * k)
per_row = 4; keys = sorted(shots); rows = (len(keys) + per_row - 1) // per_row
im = Image.new("RGB", (per_row * (3 * W + 12), rows * (H + 22)), "white"); dr = ImageDraw.Draw(im)
for i, s in enumerate(keys):
    x0 = (i % per_row) * (3 * W + 12); y0 = (i // per_row) * (H + 22)
    dr.text((x0 + 4, y0 + 4), "S%02d" % s, fill="black")
    for j, (fr, f) in enumerate(sorted(shots[s])[:3]):
        im.paste(Image.open(f).resize((W, H)), (x0 + j * W, y0 + 20)); dr.text((x0 + j * W + 4, y0 + 24), str(fr), fill="yellow")
im.save(out, quality=88); print(out, im.size)
