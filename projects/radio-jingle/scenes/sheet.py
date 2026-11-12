"""Labelled preview sheet from graded stills (two columns, A left, B right):
  python sheet.py out.jpg "1A label" img1 "1B label" img2 ...
An image path may end in "#x0,y0,x1,y1" (fractions): that crop is shown instead (hand / detail close-ups).
A label "-" leaves an empty cell."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
rows = (len(pairs) + 1) // 2
S = Image.new("RGB", (W * 2 + 12, rows * (H + BAR) + 6), (14, 16, 20))
d = ImageDraw.Draw(S)
for i, (label, path) in enumerate(pairs):
    x, y = (i % 2) * (W + 12), (i // 2) * (H + BAR)
    if label == "-":
        continue
    crop = None
    if "#" in path:
        path, c = path.split("#"); crop = [float(v) for v in c.split(",")]
    im = Image.open(path).convert("RGB")
    if crop:
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
        cw, ch = im.size; k = min(W / cw, H / ch); im = im.resize((int(cw * k), int(ch * k)), Image.LANCZOS)
        S.paste(im, (x + (W - im.size[0]) // 2, y + BAR + (H - im.size[1]) // 2))
    else:
        S.paste(im.resize((W, H), Image.LANCZOS), (x, y + BAR))
    d.text((x + 14, y + 9), label, font=font, fill=(235, 236, 240))
S.save(out, quality=86)
print("[sheet]", out)
