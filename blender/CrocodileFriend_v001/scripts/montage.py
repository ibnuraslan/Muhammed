"""python3 montage.py dir out.jpg : rows = shots (first|mid|last), labelled"""
import sys, os, glob
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; fs = sorted(glob.glob(os.path.join(d, "*.jpg")))
shots = {}
for f in fs:
    n = os.path.basename(f); key = n.rsplit("_", 2)[0]; shots.setdefault(key, []).append(f)
keys = sorted(shots); im0 = Image.open(fs[0]); w, h = im0.size
per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rows = (len(keys) + per - 1) // per
S = Image.new("RGB", (per * 3 * w + (per - 1) * 12, rows * (h + 22)), "white"); D = ImageDraw.Draw(S)
for i, k in enumerate(keys):
    x0 = (i % per) * (3 * w + 12); y0 = (i // per) * (h + 22)
    for j, f in enumerate(sorted(shots[k])):
        S.paste(Image.open(f), (x0 + j * w, y0 + 20)); D.text((x0 + j * w + 3, y0 + 4), os.path.basename(f)[:-4], fill=(0, 0, 0))
S.save(out, quality=85); print(out, S.size)
