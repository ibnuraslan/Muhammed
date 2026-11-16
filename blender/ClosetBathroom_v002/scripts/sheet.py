"""contact sheet: rows = shots, 3 columns (first/mid/last). python3 sheet.py DIR shots.json out.jpg [cols_per_row_shots]"""
import sys, json, os
from PIL import Image, ImageDraw
d, sj, out = sys.argv[1:4]; per = int(sys.argv[4]) if len(sys.argv) > 4 else 4
shots = json.load(open(sj)); cells = []
for s in shots:
    for f in (s["f0"], (s["f0"] + s["f1"]) // 2, s["f1"]):
        p = os.path.join(d, "f%04d.jpg" % f)
        if os.path.exists(p): cells.append((s["shot"], f, Image.open(p)))
w, h = cells[0][2].size; cols = per * 3; rows = (len(cells) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * (h + 16)), "white"); dr = ImageDraw.Draw(S)
for k, (sid, f, im) in enumerate(cells):
    x, y = (k % cols) * w, (k // cols) * (h + 16)
    S.paste(im, (x, y + 16)); dr.text((x + 3, y + 2), "%s f%d" % (sid, f), fill=(0, 0, 0))
S.save(out, quality=88); print("SHEET", out, S.size)
