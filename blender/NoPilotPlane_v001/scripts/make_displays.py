"""Symbol-only cockpit display graphics (no digits, no text). python3 -I make_displays.py <out_dir>"""
import sys, math
from PIL import Image, ImageDraw
out = sys.argv[1]; S = 512
G, M, C, W, A = (60, 230, 90), (230, 80, 220), (60, 220, 240), (235, 235, 235), (240, 180, 40)
def base(): return Image.new("RGB", (S, S), (4, 6, 10))
# PFD frame (attitude window is a separate animated plane; this draws tapes, bank scale, heading arc)
im = base(); d = ImageDraw.Draw(im)
d.rectangle((150, 90, 362, 330), outline=(30, 30, 30), width=2)
for x0 in (40, 400):
    d.rectangle((x0, 80, x0 + 72, 380), fill=(28, 30, 38), outline=W, width=2)
    d.polygon([(x0 + (72 if x0 < 200 else 0), 220), (x0 + (88 if x0 < 200 else -16), 210), (x0 + (88 if x0 < 200 else -16), 230)], fill=A)
for a in range(-60, 61, 10):
    r = 130; cx, cy = 256, 210; t = math.radians(a - 90)
    l = 14 if a % 30 == 0 else 8
    d.line((cx + r * math.cos(t), cy + r * math.sin(t), cx + (r + l) * math.cos(t), cy + (r + l) * math.sin(t)), fill=W, width=2)
d.polygon([(256, 72), (248, 60), (264, 60)], fill=W)
d.arc((96, 370, 416, 690), 200, 340, fill=W, width=2)
for a in range(200, 341, 10):
    t = math.radians(a); d.line((256 + 160 * math.cos(t), 530 + 160 * math.sin(t), 256 + 150 * math.cos(t), 530 + 150 * math.sin(t)), fill=W, width=2)
d.polygon([(256, 372), (248, 360), (264, 360)], fill=A)
d.rectangle((440, 420, 500, 470), outline=G, width=2); d.rectangle((12, 420, 72, 470), outline=G, width=2)
for i in range(3): d.rectangle((160 + i * 70, 30, 210 + i * 70, 50), outline=G, width=2)
im.save(out + "/disp_pfd.png")
# ND: compass rose, track line, range arcs, waypoint diamonds
im = base(); d = ImageDraw.Draw(im); cx, cy = 256, 330
for r in (110, 220): d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=W, width=2)
for a in range(0, 360, 5):
    t = math.radians(a); l = 16 if a % 30 == 0 else (10 if a % 10 == 0 else 5)
    d.line((cx + 220 * math.cos(t), cy + 220 * math.sin(t), cx + (220 - l) * math.cos(t), cy + (220 - l) * math.sin(t)), fill=W, width=2)
d.line((cx, cy, cx + 40, 70), fill=M, width=4)
for p in ((cx + 40, 70), (cx + 90, 180), (cx - 120, 150)):
    d.polygon([(p[0], p[1] - 10), (p[0] + 8, p[1]), (p[0], p[1] + 10), (p[0] - 8, p[1])], outline=C, width=2)
d.polygon([(cx, cy - 18), (cx - 12, cy + 14), (cx + 12, cy + 14)], outline=W, width=3)
for i in range(14):
    x = 40 + (i * 37) % 430; y = 420 + (i * 53) % 70; d.ellipse((x, y, x + 10, y + 6), fill=(40, 120, 50))
im.save(out + "/disp_nd.png")
# EICAS: engine arc gauges + bars
im = base(); d = ImageDraw.Draw(im)
for k, (cx, cy) in enumerate(((140, 120), (372, 120), (140, 290), (372, 290))):
    d.arc((cx - 70, cy - 70, cx + 70, cy + 70), 150, 390, fill=W, width=3)
    d.arc((cx - 70, cy - 70, cx + 70, cy + 70), 360, 390, fill=(230, 40, 30), width=5)
    t = math.radians(150 + 160 + k * 12); d.line((cx, cy, cx + 62 * math.cos(t), cy + 62 * math.sin(t)), fill=W, width=4)
    d.rectangle((cx - 30, cy + 20, cx + 30, cy + 44), outline=W, width=2)
for i in range(8):
    x = 60 + i * 52; h = 40 + (i * 37) % 60
    d.rectangle((x, 470 - h, x + 22, 470), outline=W, width=2); d.rectangle((x + 3, 470 - h + 10, x + 19, 467), fill=C)
im.save(out + "/disp_eicas.png")
# scrolling tape (tileable): tick marks only
im = Image.new("RGB", (128, 1024), (28, 30, 38)); d = ImageDraw.Draw(im)
for y in range(0, 1024, 32):
    d.line((90 if (y // 32) % 5 else 50, y, 128, y), fill=W, width=3 if (y // 32) % 5 == 0 else 2)
    if (y // 32) % 5 == 0: d.rectangle((14, y - 8, 40, y + 8), outline=W, width=2)
im.save(out + "/disp_tape.png")
# radio / FMS heads: segment bars and key grid
im = Image.new("RGB", (512, 256), (14, 15, 18)); d = ImageDraw.Draw(im)
for r in range(2):
    d.rectangle((20, 20 + r * 60, 240, 70 + r * 60), fill=(2, 4, 3))
    for k in range(5): d.rectangle((32 + k * 40, 34 + r * 60, 60 + k * 40, 56 + r * 60), fill=(50, 230, 90) if (k + r) % 3 else (40, 140, 60))
for i in range(6):
    for j in range(4):
        d.rectangle((280 + i * 36, 20 + j * 52, 306 + i * 36, 56 + j * 52), fill=(60, 62, 66), outline=(110, 110, 110))
im.save(out + "/disp_radio.png")
# blank checklist (lines only)
im = Image.new("RGB", (256, 360), (230, 228, 215)); d = ImageDraw.Draw(im)
for i in range(16):
    y = 30 + i * 20; d.line((24, y, 24 + 90 + (i * 47) % 110, y), fill=(60, 60, 70), width=3); d.rectangle((210, y - 6, 222, y + 6), outline=(60, 60, 70), width=2)
d.rectangle((90, 0, 166, 14), fill=(140, 140, 140))
im.save(out + "/checklist.png")
print("DISPLAYS", out)
