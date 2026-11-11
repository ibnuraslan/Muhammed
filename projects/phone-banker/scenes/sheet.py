"""Labelled preview sheet: python sheet.py out.jpg "1A label" img1 "1B label" img2 ...  (two columns, like the reference)."""
import sys
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; pairs = list(zip(sys.argv[2::2], sys.argv[3::2]))
W, H, BAR = 960, 408, 44
font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 26)
rows = (len(pairs) + 1) // 2
S = Image.new("RGB", (W * 2, rows * (H + BAR)), (14, 16, 20))
d = ImageDraw.Draw(S)
for i, (label, path) in enumerate(pairs):
    x, y = (i % 2) * W, (i // 2) * (H + BAR)
    S.paste(Image.open(path).convert("RGB").resize((W, H)), (x, y + BAR))
    d.text((x + 14, y + 8), label, font=font, fill=(235, 236, 240))
S.save(out, quality=88)
