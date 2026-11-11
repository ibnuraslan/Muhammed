"""python3 -I 00_textures.py <work_dir>: phone note (blurred, unreadable blobs), share icons, video-call frame. No text."""
import sys, os, random
from PIL import Image, ImageDraw, ImageFilter
W = sys.argv[1]; os.makedirs(W, exist_ok=True); random.seed(5)
im = Image.new("RGB", (256, 512), (245, 245, 240)); d = ImageDraw.Draw(im); y = 40
for line in range(7):
    x = 18
    while x < 226:
        w = random.randint(14, 34); d.rounded_rectangle((x, y, x + w, y + 46), 10, fill=(20, 20, 25)); x += w + random.randint(6, 16)
    y += 66
im.filter(ImageFilter.GaussianBlur(9)).save(f"{W}/note_blur.png")
im = Image.new("RGB", (256, 512), (25, 30, 45)); d = ImageDraw.Draw(im)
for cx, cy in ((90, 200), (170, 150), (170, 250)): d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=(90, 200, 255))
d.line((90, 200, 170, 150), fill=(90, 200, 255), width=10); d.line((90, 200, 170, 250), fill=(90, 200, 255), width=10)
d.polygon([(128, 420), (78, 370), (78, 345), (100, 330), (128, 350), (156, 330), (178, 345), (178, 370)], fill=(255, 70, 90))
im.filter(ImageFilter.GaussianBlur(1.5)).save(f"{W}/share_icons.png")
c = Image.new("RGB", (256, 192), (40, 60, 80)); d = ImageDraw.Draw(c)
d.ellipse((90, 40, 166, 130), fill=(200, 150, 120)); d.rectangle((70, 120, 186, 192), fill=(30, 40, 120)); d.ellipse((10, 10, 70, 60), fill=(80, 90, 110))
c.filter(ImageFilter.GaussianBlur(5)).save(f"{W}/call.png")
print("TEX_OK")
