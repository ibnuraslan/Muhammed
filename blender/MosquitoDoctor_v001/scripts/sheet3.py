"""3-per-shot sheet: rows of shots, columns first/mid/last. python3 sheet3.py dir out.jpg [shots_per_row]"""
import sys, glob, os
from PIL import Image, ImageDraw
fs = sorted(glob.glob(sys.argv[1] + "/S*_*.jpg")); per = int(sys.argv[3]) if len(sys.argv) > 3 else 4
shots = sorted({os.path.basename(f).split("_")[0] for f in fs})
im0 = Image.open(fs[0]); w, h = im0.size
rows = (len(shots) + per - 1) // per
S = Image.new("RGB", (w * 3 * per + 8 * (per - 1), h * rows), (30, 30, 30))
for k, s in enumerate(shots):
    for j, tag in enumerate("abc"):
        g = glob.glob(f"{sys.argv[1]}/{s}_{tag}_*.jpg")
        if not g: continue
        im = Image.open(g[0]).convert("RGB"); d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 92, 16), fill=(0, 0, 0)); d.text((3, 2), f"{s} {tag} f{g[0][-9:-4]}", fill=(255, 255, 0))
        S.paste(im, ((k % per) * (3 * w + 8) + j * w, (k // per) * h))
S.save(sys.argv[2], quality=85); print(sys.argv[2], S.size)
