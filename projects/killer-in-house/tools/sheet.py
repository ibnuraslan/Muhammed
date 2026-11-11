"""Labelled preview sheet: python sheet.py out.jpg title  dir1|label1  dir2|label2 ...  (2 columns: A | B)"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, title, items = sys.argv[1], sys.argv[2], sys.argv[3:]
W = 640; H = int(W * 816 / 1920); LAB = 30; PAD = 8
F = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 17)
FT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 26)
rows = (len(items) + 1) // 2
sheet = Image.new("RGB", (2 * W + 3 * PAD, 50 + rows * (H + LAB + PAD) + PAD), (18, 18, 20))
d = ImageDraw.Draw(sheet); d.text((PAD, 10), title, font=FT, fill=(235, 235, 235))
for i, it in enumerate(items):
    path, lab = it.split("|", 1)
    x = PAD + (i % 2) * (W + PAD); y = 50 + (i // 2) * (H + LAB + PAD)
    p = os.path.join(path, "plate.png")
    if os.path.exists(p):
        im = Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS); sheet.paste(im, (x, y + LAB))
    else:
        d.rectangle([x, y + LAB, x + W, y + LAB + H], fill=(60, 20, 20)); d.text((x + 20, y + LAB + 20), "missing", font=F, fill=(255, 200, 200))
    d.text((x, y + 6), lab, font=F, fill=(230, 220, 200))
sheet.save(out, quality=88)
print(out, sheet.size)
