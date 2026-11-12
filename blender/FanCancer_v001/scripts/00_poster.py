"""python3 -I 00_poster.py <work>: a wordless clinic wall poster (layered skin diagram shapes, no text)."""
import sys
from PIL import Image, ImageDraw, ImageFilter
W = sys.argv[1]
im = Image.new("RGB", (300, 420), (236, 246, 250)); d = ImageDraw.Draw(im)
for i, (c, y0, y1) in enumerate((((248, 196, 160), 80, 120), ((236, 120, 120), 120, 230), ((250, 200, 90), 230, 330))):
    d.rectangle((30, y0, 270, y1), fill=c)
for x in range(40, 270, 22): d.ellipse((x, 250 + (x % 3) * 20, x + 18, 268 + (x % 3) * 20), fill=(240, 175, 60))
d.line((60, 330, 90, 140, 120, 330), fill=(200, 40, 40), width=6); d.line((180, 330, 200, 150, 230, 330), fill=(60, 90, 200), width=6)
d.ellipse((130, 66, 170, 96), fill=(70, 40, 30)); d.rectangle((0, 0, 299, 419), outline=(60, 140, 170), width=10)
im.filter(ImageFilter.GaussianBlur(0.8)).save(f"{W}/poster.png"); print("POSTER_OK")
