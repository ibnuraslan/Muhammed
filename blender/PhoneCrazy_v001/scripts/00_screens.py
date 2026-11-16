"""Phone screen atlas (no text, no real app or brand logos): 8 x 3 tiles of 300 x 650 px.
python3 -I 00_screens.py <out.png>   Tile index = row * 8 + col; 03_anim keys the index per frame."""
import sys, random, math
from PIL import Image, ImageDraw, ImageFilter
W, H, NC, NR = 300, 650, 8, 3
A = Image.new("RGB", (W * NC, H * NR), (0, 0, 0))
random.seed(3)
def grad(c0, c1):
    t = Image.new("RGB", (W, H)); d = ImageDraw.Draw(t)
    for y in range(H):
        u = y / H; d.line([(0, y), (W, y)], fill=tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3)))
    return t
def wall():
    t = grad((70, 150, 235), (190, 225, 250)); d = ImageDraw.Draw(t, "RGBA")
    for _ in range(9):
        x, y, r = random.randint(0, W), random.randint(0, H), random.randint(60, 160)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 28))
    return t.filter(ImageFilter.GaussianBlur(6))
WALL = wall()
def bar(d, light=True):   # status bar: small pills only
    c = (255, 255, 255) if light else (40, 40, 40)
    d.rounded_rectangle([22, 18, 62, 30], 6, fill=c); d.rounded_rectangle([238, 18, 278, 30], 6, fill=c)
def lock(n):
    t = WALL.copy(); d = ImageDraw.Draw(t); bar(d)
    # padlock picture
    cx = W // 2; d.rounded_rectangle([cx - 16, 90, cx + 16, 116], 5, fill=(255, 255, 255))
    d.arc([cx - 11, 72, cx + 11, 100], 180, 360, fill=(255, 255, 255), width=5) if n < 6 else d.arc([cx - 3, 66, cx + 19, 94], 180, 360, fill=(255, 255, 255), width=5)
    for i in range(6):
        x = cx - 75 + i * 30; y = 300
        if i < n: d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 255, 255))
        else: d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=(255, 255, 255), width=2)
    d.rounded_rectangle([cx - 50, 620, cx + 50, 626], 3, fill=(255, 255, 255))
    return t
APPC = [(255, 90, 80), (255, 170, 40), (80, 200, 110), (60, 150, 255), (170, 100, 240), (255, 110, 170), (40, 190, 200), (250, 210, 60)]
def home():
    t = WALL.copy(); d = ImageDraw.Draw(t); bar(d)
    for r in range(5):
        for c in range(4):
            x = 28 + c * 66; y = 70 + r * 84; col = APPC[(r * 4 + c * 3) % 8]
            d.rounded_rectangle([x, y, x + 50, y + 50], 13, fill=col)
            # simple white glyph: circle / square / triangle
            k = (r + c) % 3
            if k == 0: d.ellipse([x + 15, y + 15, x + 35, y + 35], outline=(255, 255, 255), width=4)
            elif k == 1: d.rounded_rectangle([x + 15, y + 15, x + 35, y + 35], 4, outline=(255, 255, 255), width=4)
            else: d.polygon([(x + 25, y + 13), (x + 37, y + 36), (x + 13, y + 36)], outline=(255, 255, 255), width=4)
    d.rounded_rectangle([16, 540, W - 16, 620], 26, fill=(255, 255, 255, 90))
    for c in range(4):
        x = 32 + c * 64; d.rounded_rectangle([x, 556, x + 46, 602], 12, fill=APPC[(c * 2 + 1) % 8])
    return t
def gallery(off=0):
    t = Image.new("RGB", (W, H), (248, 248, 250)); d = ImageDraw.Draw(t); bar(d, False)
    d.rounded_rectangle([20, 50, 120, 62], 6, fill=(60, 60, 70))
    for r in range(6):
        for c in range(3):
            x = 4 + c * 98; y = 80 + r * 98
            a = APPC[(r * 3 + c + off) % 8]; b = APPC[(r + c * 2 + 3 + off) % 8]
            d.rectangle([x, y, x + 94, y + 94], fill=a); d.ellipse([x + 20, y + 30, x + 80, y + 120], fill=b)
            d.polygon([(x, y + 94), (x + 40, y + 50), (x + 94, y + 94)], fill=tuple(int(v * 0.7) for v in a))
    return t
def mapapp():
    t = Image.new("RGB", (W, H), (226, 236, 220)); d = ImageDraw.Draw(t)
    d.rectangle([0, 0, W, 300], fill=(190, 225, 245))
    for i in range(7): d.line([(random.randint(0, W), 0), (random.randint(0, W), H)], fill=(255, 255, 255), width=10)
    for i in range(5): d.line([(0, random.randint(0, H)), (W, random.randint(0, H))], fill=(250, 220, 120), width=8)
    d.ellipse([W // 2 - 18, 330, W // 2 + 18, 366], fill=(240, 70, 60)); d.ellipse([W // 2 - 7, 341, W // 2 + 7, 355], fill=(255, 255, 255))
    bar(d, False); return t
def flash(): return Image.new("RGB", (W, H), (255, 255, 255))
def shot(src):
    t = src.copy(); d = ImageDraw.Draw(t, "RGBA")
    th = src.resize((96, 208)); d.rounded_rectangle([14, 420, 118, 636], 10, fill=(255, 255, 255)); t.paste(th, (18, 424))
    return t
KEYS = [(c, r) for r in range(4) for c in range(3)]
def dial(hi=None, calling=False):
    t = Image.new("RGB", (W, H), (24, 28, 36)); d = ImageDraw.Draw(t); bar(d)
    # entered "number": dots only (no digits on screen)
    n = {None: 0, 8: 1, 0: 2, 1: 3, 99: 3}.get(hi, 0)
    for i in range(n): d.ellipse([120 + i * 24, 120, 134 + i * 24, 134], fill=(255, 255, 255))
    for i, (c, r) in enumerate(KEYS):
        x = 60 + c * 90; y = 220 + r * 86
        col = (235, 235, 240) if i == hi else (70, 76, 90)
        d.ellipse([x - 32, y - 32, x + 32, y + 32], fill=col)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(30, 30, 36) if i == hi else (190, 195, 205))
    d.ellipse([W // 2 - 34, 560, W // 2 + 34, 628], fill=(60, 205, 90) if not calling else (90, 240, 120))
    d.rounded_rectangle([W // 2 - 14, 586, W // 2 + 14, 602], 8, fill=(255, 255, 255))
    return t
def calling(p):
    t = grad((20, 90, 110), (10, 40, 60)); d = ImageDraw.Draw(t, "RGBA"); bar(d)
    for k in range(3):
        r = 60 + k * 30 + p * 20; d.ellipse([W // 2 - r, 230 - r, W // 2 + r, 230 + r], outline=(255, 255, 255, 120 - k * 35), width=3)
    d.ellipse([W // 2 - 50, 180, W // 2 + 50, 280], fill=(200, 210, 220))
    d.ellipse([W // 2 - 20, 198, W // 2 + 20, 238], fill=(120, 130, 145)); d.chord([W // 2 - 36, 240, W // 2 + 36, 300], 180, 360, fill=(120, 130, 145))
    d.ellipse([W // 2 - 34, 560, W // 2 + 34, 628], fill=(235, 60, 55)); d.rounded_rectangle([W // 2 - 16, 588, W // 2 + 16, 600], 6, fill=(255, 255, 255))
    return t
def glitch(src, seed):
    rnd = random.Random(seed); t = src.copy()   # bars, blocks and colour shifts only (no glyph fragments)
    r, g, b = t.split(); t = Image.merge("RGB", (r.transform(t.size, Image.AFFINE, (1, 0, rnd.randint(-14, 14), 0, 1, 0)), g, b.transform(t.size, Image.AFFINE, (1, 0, rnd.randint(-14, 14), 0, 1, 0))))
    for _ in range(14):
        y = rnd.randint(0, H - 20); h = rnd.randint(4, 40); dx = rnd.randint(-60, 60)
        band = t.crop((0, y, W, y + h)); t.paste(band, (dx, y))
    d = ImageDraw.Draw(t, "RGBA")
    for _ in range(10):
        y = rnd.randint(0, H); d.rectangle([0, y, W, y + rnd.randint(2, 10)], fill=(rnd.choice([0, 255]), rnd.randint(0, 255), 255, 140))
    for _ in range(6):
        x, y = rnd.randint(0, W), rnd.randint(0, H); d.rectangle([x, y, x + rnd.randint(20, 90), y + rnd.randint(8, 40)], fill=(rnd.randint(0, 255), rnd.randint(0, 255), rnd.randint(0, 255), 200))
    return t
def ripple():
    t = Image.new("RGB", (W, H), (8, 10, 16)); d = ImageDraw.Draw(t)
    for k in range(9):
        r = 20 + k * 34; c = max(0, 160 - k * 16); d.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], outline=(c // 3, c, c + 40 if c else 0), width=3)
    return t.filter(ImageFilter.GaussianBlur(1.5))
G = gallery(); M = mapapp()
TILES = [Image.new("RGB", (W, H), (6, 6, 8)),            # 0 off
         lock(0), lock(1), lock(2), lock(3), lock(4), lock(5), lock(6),   # 1-7 lock, dots filling, padlock opens at 7
         home(), G, M, flash(), shot(G), shot(M),       # 8 home, 9 gallery app, 10 map app, 11 flash, 12-13 screenshot thumbs
         dial(), dial(8), dial(0), dial(99, True),       # 14 pad, 15 '9' lit, 16 '1' lit, 17 call pressed
         calling(0), calling(1),                         # 18-19 calling (pulsing)
         glitch(WALL, 1), glitch(grad((10, 30, 60), (60, 10, 70)), 2), glitch(grad((5, 5, 8), (20, 60, 70)), 3), ripple()]   # 20-22 glitch, 23 dark ripple
for i, t in enumerate(TILES):
    t = t.convert("RGB"); m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, W - 1, H - 1], 34, fill=255)
    bg = Image.new("RGB", (W, H), (0, 0, 0)); bg.paste(t, (0, 0), m)
    A.paste(bg, ((i % NC) * W, (i // NC) * H))
A.save(sys.argv[1]); print("ATLAS", len(TILES), "tiles", A.size)
