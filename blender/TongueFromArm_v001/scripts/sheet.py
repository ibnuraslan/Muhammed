"""3 frames per shot sheet: python3 sheet.py frames_dir shots.json out.jpg cellW [first_shot last_shot]"""
import sys, json, os
from PIL import Image, ImageDraw
d, sj, out, W = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]); H = round(W * 16 / 9)
shots = json.load(open(sj))
if len(sys.argv) > 6: shots = [s for s in shots if sys.argv[5] <= s["id"] <= sys.argv[6]]
cols = 3; S = Image.new("RGB", (cols * W * 2 if False else W * 6, ((len(shots) + 1) // 2) * (H + 24)), "white")
dr = ImageDraw.Draw(S)
for i, s in enumerate(shots):
    fr = [s["f0"], (s["f0"] + s["f1"]) // 2, s["f1"]]
    x0 = (i % 2) * 3 * W; y0 = (i // 2) * (H + 24)
    for j, f in enumerate(fr):
        p = os.path.join(d, "f%04d.jpg" % f)
        if os.path.exists(p): S.paste(Image.open(p).resize((W, H)), (x0 + j * W, y0 + 24))
        dr.text((x0 + j * W + 4, y0 + 4), "%s f%d" % (s["id"], f), fill=(0, 0, 0))
S.save(out, quality=88); print("SHEET", out, S.size)
