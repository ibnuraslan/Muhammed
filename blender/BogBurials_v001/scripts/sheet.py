"""contact sheet: rows = shots, 3 columns (first, middle, last). python3 sheet.py <frames_dir> <out.jpg> [cell_w]"""
import sys, os, re
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; W = int(sys.argv[3]) if len(sys.argv) > 3 else 270
fs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
rows = {}
for f in fs:
    m = re.match(r"(\d+)_([^_]+)_(\d)_f(\d+)\.jpg", f)
    if m: rows.setdefault((int(m.group(1)), m.group(2)), {})[int(m.group(3))] = (f, int(m.group(4)))
H = W * 16 // 9; keys = sorted(rows)
per = 4  # shots per sheet row group
cols = 3 * per
S = Image.new("RGB", (cols * W, ((len(keys) + per - 1) // per) * (H + 22)), "white"); dr = ImageDraw.Draw(S)
for i, k in enumerate(keys):
    r, cblock = divmod(i, per)
    for j in range(3):
        if j not in rows[k]: continue
        f, fr = rows[k][j]
        im = Image.open(os.path.join(d, f)).convert("RGB").resize((W, H))
        x = (cblock * 3 + j) * W; y = r * (H + 22)
        S.paste(im, (x, y + 22)); dr.text((x + 4, y + 4), f"S{k[1]} f{fr}", fill="black")
S.save(out, quality=88); print("SHEET", out, S.size)
