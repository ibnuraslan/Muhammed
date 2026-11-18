"""Paper textures: Deveau's letter (pen script, not legible at film distance), the court warrant (printed
heading + script), and the clerk's papers. Written with PIL; strokes are procedural, no fonts copied."""
import os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tex")
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
os.makedirs(OUT, exist_ok=True)


def script_line(d, x0, y0, x1, rng, ink, w=3, size=26):
    x = x0
    while x < x1 - 40:
        word = rng.randint(2, 7)
        pts = []
        for k in range(word * 8):
            t = k / 8.0
            yy = y0 - (size * 0.35) * (0.5 + 0.5 * math.sin(t * math.pi * 2 + rng.random())) * (1.5 if rng.random() < 0.12 else 1.0)
            if rng.random() < 0.08:
                yy -= size * 0.6
            pts.append((x + t * size * 0.55, yy + rng.uniform(-1.5, 1.5)))
        d.line(pts, fill=ink, width=w, joint="curve")
        x += word * size * 0.55 + rng.randint(12, 22)


def letter(path, seed=1, lines=22, heading=None):
    rng = random.Random(seed)
    W, H = 1400, 1800
    im = Image.new("RGB", (W, H), (232, 220, 192)); d = ImageDraw.Draw(im)
    for _ in range(2500):
        x, y = rng.randrange(W), rng.randrange(H); c = rng.randint(200, 228)
        d.point((x, y), fill=(c + 8, c, c - 22))
    ink = (40, 32, 50)
    y = 170
    if heading:
        f = ImageFont.truetype(os.path.join(FONT, "CourierPrime-Bold.ttf"), 46)
        d.text((W / 2, 110), heading, font=f, fill=(25, 22, 22), anchor="mm"); y = 230
    for i in range(lines):
        x0 = 130 + (60 if i == 0 else 0)
        script_line(d, x0, y, W - 120 if i < lines - 1 else W * 0.55, rng, ink)
        y += 68
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(path)


letter(os.path.join(OUT, "letter.png"), 3)
letter(os.path.join(OUT, "warrant.png"), 7, lines=14, heading="VICE-ADMIRALTY COURT  ·  GIBRALTAR")
letter(os.path.join(OUT, "papers.png"), 11, lines=24)
print("ok")
