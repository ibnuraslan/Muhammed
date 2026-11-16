"""3-frame sheet: python3 -I sheet.py <stills_dir> <out.jpg> [rows_per_page]. One row per shot: first | middle | last."""
import sys, glob, os, re
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
fs = sorted(glob.glob(src + "/*.jpg"))
rows = {}
for f in fs:
    m = re.match(r"(\d+)_(\w+?)_(\d)_f(\d+)\.jpg", os.path.basename(f)); rows.setdefault(m.group(2), []).append((int(m.group(3)), int(m.group(4)), f))
sids = sorted(rows, key=lambda s: min(r[1] for r in rows[s]))
per = 2  # shots per sheet row (6 images across)
w, h = Image.open(fs[0]).size; tw, th = w // 2, h // 2
S = Image.new("RGB", (tw * 3 * per, th * ((len(sids) + per - 1) // per)), "black"); d = ImageDraw.Draw(S)
for i, sid in enumerate(sids):
    for j, fr, f in sorted(rows[sid]):
        im = Image.open(f).convert("RGB").resize((tw, th)); x = ((i % per) * 3 + j) * tw; y = (i // per) * th
        S.paste(im, (x, y)); d.rectangle((x, y, x + 92, y + 14), fill=(0, 0, 0)); d.text((x + 2, y + 1), f"S{sid} f{fr}", fill=(255, 255, 0))
S.save(out, quality=85); print(out, S.size)
