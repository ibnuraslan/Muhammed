"""Paper textures with NO readable text: grey line blocks + simple drawings. python3 make_textures.py outdir"""
import sys, random, math
from PIL import Image, ImageDraw
out = sys.argv[1]; random.seed(7)
def lines(d, x0, y0, x1, y1, h=10, gap=8, col=(120, 120, 125)):
    y = y0
    while y + h < y1:
        w = x1 - x0 if random.random() > 0.15 else int((x1 - x0) * random.uniform(0.4, 0.8))
        d.rounded_rectangle([x0, y, x0 + w, y + h], 3, fill=col); y += h + gap
def pin_drawing(d, cx, cy, L, col=(40, 45, 60), w=6, open_=0.0):
    r = L * 0.07
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)          # coil
    d.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], outline=col, width=w - 2)
    d.line([cx, cy + r, cx + L, cy + r], fill=col, width=w)                    # fixed leg
    a = math.radians(open_)
    d.line([cx, cy - r, cx + L * 0.93 * math.cos(a), cy - r - L * 0.93 * math.sin(a)], fill=col, width=w)  # arm
    d.rounded_rectangle([cx + L * 0.86, cy - r * 1.35, cx + L * 1.04, cy + r * 1.35], 8, outline=col, width=w)  # clasp
# patent: cream paper, ruled blocks, two pin drawings (closed + open), red wax seal
im = Image.new("RGB", (1200, 1600), (246, 238, 214)); d = ImageDraw.Draw(im)
d.rectangle([40, 40, 1160, 1560], outline=(150, 120, 80), width=6)
lines(d, 120, 110, 1080, 260, h=14, gap=12, col=(110, 100, 90))
pin_drawing(d, 230, 480, 700); pin_drawing(d, 230, 820, 700, open_=14)
lines(d, 120, 1020, 1080, 1360, h=10, gap=10, col=(140, 130, 120))
d.ellipse([880, 1360, 1060, 1540], fill=(170, 30, 35)); d.ellipse([915, 1395, 1025, 1505], outline=(120, 15, 20), width=8)
im.save(out + "/patent.png")
# debt note: small cream note, lines, no numbers, a dark stamp ring
im = Image.new("RGB", (900, 600), (240, 232, 205)); d = ImageDraw.Draw(im)
d.rectangle([20, 20, 880, 580], outline=(120, 100, 70), width=5)
lines(d, 70, 70, 830, 420, h=14, gap=16, col=(100, 90, 80))
d.ellipse([640, 400, 800, 560], outline=(150, 40, 40), width=10)
im.save(out + "/debtnote.png")
# banknote: green engraved-look note, oval portrait frame left EMPTY (pattern only), no numbers/text
im = Image.new("RGB", (1000, 430), (196, 214, 180)); d = ImageDraw.Draw(im)
d.rectangle([12, 12, 988, 418], outline=(50, 90, 60), width=10); d.rectangle([34, 34, 966, 396], outline=(80, 120, 85), width=3)
for i in range(0, 1000, 14): d.line([i, 34, i + 120, 396], fill=(170, 195, 160), width=2)
d.ellipse([380, 70, 620, 360], fill=(120, 160, 120), outline=(40, 80, 50), width=8)
for k in range(8): d.ellipse([400 + k * 10, 90 + k * 12, 600 - k * 10, 340 - k * 12], outline=(70, 115, 80), width=3)
d.ellipse([90, 140, 240, 290], outline=(50, 90, 60), width=8); d.ellipse([760, 140, 910, 290], outline=(50, 90, 60), width=8)
im.save(out + "/banknote.png")
# newspaper: grey columns + one picture box with the safety-pin drawing (no headline, no text)
im = Image.new("RGB", (1400, 1800), (232, 228, 216)); d = ImageDraw.Draw(im)
d.rectangle([60, 60, 1340, 230], fill=(205, 200, 190))                    # empty masthead band (no letters)
d.line([60, 250, 1340, 250], fill=(60, 60, 60), width=6)
d.rectangle([60, 290, 820, 900], fill=(214, 210, 200), outline=(60, 60, 60), width=5)
pin_drawing(d, 160, 600, 560, col=(50, 50, 55), w=9)
for cx in (60, 480, 900):
    lines(d, cx, 940, cx + 380, 1740, h=9, gap=9, col=(150, 148, 142))
lines(d, 860, 290, 1340, 900, h=9, gap=9, col=(150, 148, 142))
im.save(out + "/newspaper.png")
print("TEX_OK")
