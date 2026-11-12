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
c = Image.new("RGB", (512, 384), (60, 90, 120)); d = ImageDraw.Draw(c)
d.rectangle((0, 250, 512, 384), fill=(90, 70, 60)); d.ellipse((190, 70, 320, 230), fill=(205, 155, 125)); d.ellipse((180, 50, 330, 150), fill=(70, 45, 35))
d.rectangle((150, 220, 362, 384), fill=(30, 50, 140)); d.ellipse((235, 140, 250, 152), fill=(40, 30, 30)); d.ellipse((265, 140, 280, 152), fill=(40, 30, 30))
d.arc((235, 165, 280, 200), 20, 160, fill=(150, 60, 60), width=5); d.rectangle((20, 20, 150, 110), fill=(230, 210, 180)); d.ellipse((60, 35, 110, 85), fill=(200, 140, 110))
c.filter(ImageFilter.GaussianBlur(3.5)).save(f"{W}/call.png")
print("TEX_OK")
