"""contact sheet of shot stills with labels.  python3 sheet.py <dir> <out.jpg> [cols]"""
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
fs = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
ims = [Image.open(os.path.join(d, f)) for f in fs]
w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * (h + 16)), "white"); D = ImageDraw.Draw(S)
for i, (f, im) in enumerate(zip(fs, ims)):
    x, y = (i % cols) * w, (i // cols) * (h + 16); S.paste(im, (x, y + 16)); D.text((x + 3, y + 2), f[:-4], fill="black")
S.save(out, quality=88); print("SHEET", out, len(ims))
