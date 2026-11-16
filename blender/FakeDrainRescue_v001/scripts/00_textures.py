"""Text-free textures: phone call screen and complaint form (photo of trash + empty field boxes). python3 00_textures.py"""
from PIL import Image, ImageDraw, ImageFilter
import random
D = "/home/user/Muhammed/blender/FakeDrainRescue_v001/assets/tex/"
# phone screen 540x1170: blue gradient, avatar circle, three grey keypad rows of dots, green + red call buttons
W, H = 540, 1170; im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
for y in range(H):
    t = y / H; d.line([(0, y), (W, y)], fill=(int(30 + 40 * t), int(90 + 60 * t), int(200 - 40 * t)))
d.ellipse([195, 170, 345, 320], fill=(235, 240, 250)); d.ellipse([240, 195, 300, 255], fill=(120, 150, 210)); d.pieslice([215, 245, 325, 355], 180, 360, fill=(120, 150, 210))
for r in range(4):
    for c in range(3):
        x = 120 + c * 150; y = 470 + r * 120; d.ellipse([x - 42, y - 42, x + 42, y + 42], fill=(255, 255, 255, 60), outline=(220, 230, 255), width=3)
d.ellipse([90, 960, 220, 1090], fill=(40, 200, 90)); d.ellipse([320, 960, 450, 1090], fill=(230, 50, 50))
d.rounded_rectangle([130, 1008, 180, 1042], 12, fill=(255, 255, 255)); d.rounded_rectangle([360, 1008, 410, 1042], 12, fill=(255, 255, 255))
im.save(D + "phone_screen.png")
# complaint form 700x990: header band, trash photo, empty field boxes, signature line, red ring stamp
random.seed(4)
def form(i):
    im = Image.new("RGB", (700, 990), (250, 250, 246)); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, 660, 95], fill=(70, 110, 170))
    ph = Image.new("RGB", (560, 380), (95, 80, 55)); pd = ImageDraw.Draw(ph)
    pd.rectangle([0, 0, 560, 60], fill=(170, 170, 165)); pd.rectangle([0, 320, 560, 380], fill=(160, 160, 155))
    for k in range(70):
        x, y = random.randint(0, 560), random.randint(60, 330); r = random.randint(14, 40)
        col = random.choice([(25, 25, 30), (40, 70, 160), (190, 40, 40), (220, 120, 170), (60, 140, 60), (200, 200, 200), (230, 200, 60)])
        pd.ellipse([x - r, y - int(r * 0.8), x + r, y + int(r * 0.8)], fill=col)
    ph = ph.filter(ImageFilter.GaussianBlur(1.2)); im.paste(ph, (70, 130)); d.rectangle([70, 130, 630, 510], outline=(40, 40, 40), width=4)
    for k in range(4):
        y = 560 + k * 80; d.rectangle([70, y, 630, y + 46], outline=(150, 150, 155), width=3)
    d.line([(380, 900), (630, 900)], fill=(60, 60, 60), width=3)
    if i % 2 == 0: d.ellipse([90, 840, 210, 960], outline=(200, 40, 40), width=10)
    im.save(D + "form_%d.png" % i)
for i in range(3): form(i)
print("ok")
