"""python3 sheet.py dir out.jpg [cols-per-row shots]: rows of shots, 3 frames each, labelled"""
import sys, glob, os, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
fs = sorted(glob.glob(d + "/S*_*.jpg")); shots = {}
for f in fs:
    m = re.match(r"(S\d+)_([abc])_(\d+)", os.path.basename(f)); shots.setdefault(m.group(1), []).append((m.group(2), int(m.group(3)), f))
ks = sorted(shots); w, h = Image.open(fs[0]).size; pad = 6
rows = (len(ks) + per - 1) // per
S = Image.new("RGB", (per * (3 * w + pad * 3), rows * (h + 26)), (30, 30, 30)); dr = ImageDraw.Draw(S)
for i, k in enumerate(ks):
    r, c = divmod(i, per); x0 = c * (3 * w + pad * 3); y0 = r * (h + 26)
    for j, (tag, fr, f) in enumerate(sorted(shots[k])):
        S.paste(Image.open(f), (x0 + j * w, y0 + 22)); dr.text((x0 + j * w + 4, y0 + 4), "%s %s f%d" % (k, tag, fr), fill=(255, 255, 0))
S.save(out, quality=85); print(out, S.size)
