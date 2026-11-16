"""python3 review_pages.py RENDER_DIR shots.json : 3 frames per shot (first/mid/last) -> page0.jpg, page1.jpg"""
import sys, json, os
from PIL import Image, ImageDraw
d, sh = sys.argv[1], json.load(open(sys.argv[2]))
cells = [(s["id"], f) for s in sh for f in (s["f0"], s["f0"] + s["len"] // 2, s["f0"] + s["len"] - 1)]
ims = {f: Image.open(os.path.join(d, "f%05d.jpg" % f)) for _, f in cells if os.path.exists(os.path.join(d, "f%05d.jpg" % f))}
w, h = next(iter(ims.values())).size
per = 36
for p in range((len(cells) + per - 1) // per):
    part = cells[p * per:(p + 1) * per]; c = Image.new("RGB", (w * 9, h * ((len(part) + 8) // 9)), "white"); dr = ImageDraw.Draw(c)
    for i, (sid, f) in enumerate(part):
        if f not in ims: continue
        x, y = (i % 9) * w, (i // 9) * h; c.paste(ims[f], (x, y)); dr.text((x + 3, y + 3), "%s %d" % (sid, f), fill=(255, 255, 0))
    c.save(os.path.join(d, "page%d.jpg" % p), quality=85)
