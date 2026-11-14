"""Typed 1981 statement page (typewriter, uneven ink) struck through by hand in red ballpoint: rough, wavering,
double-pass strokes with pressure variation. Writes assets/generated/b_statement_struck.png (and an unstruck copy).
  python3 b_gen_statement.py
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated")
W, H = 1240, 1754                                     # A4 at 150 dpi
FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 34)
HEAD = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 35)
TEXT = """Niederschrift

Zur Sache befragt, gebe ich folgendes an:

Am Abend des betreffenden Tages war ich
nicht zu Hause. Ich bin gegen 19 Uhr mit
dem Moped in Richtung Wald gefahren. Ich
hatte einen Spaten dabei, den ich mir
vorher aus der Werkstatt geholt hatte.

Im Wald habe ich an einer Stelle neben
dem Weg ein Loch gegraben. Das Loch war
etwa so tief wie der Spaten lang ist. Den
Aushub habe ich neben das Loch gelegt.
Den Boden kann ich beschreiben, er war
lehmig und weiter unten steinig.

Fuer die Arbeit wurde mir Geld und ein
Farbfernseher versprochen. Den Auftrag
habe ich nicht gefragt, wofuer.

Ich habe diese Angaben freiwillig gemacht.

Selbst gelesen, genehmigt, unterschrieben."""


def typed(rng):
    im = Image.new("L", (W, H), 0)                    # ink coverage
    d = ImageDraw.Draw(im)
    x0, y = 150, 170
    for li, line in enumerate(TEXT.split("\n")):
        f = HEAD if li == 0 else FONT
        x = x0 + rng.uniform(-1.5, 1.5)
        for ch in line:
            a = int(255 * rng.uniform(0.8, 1.0))    # uneven ribbon / key pressure
            d.text((x + rng.uniform(-0.6, 0.6), y + rng.uniform(-0.8, 0.8)), ch, font=f, fill=a)
            x += 19.8
        y += 58 if line else 36
    return im.filter(ImageFilter.GaussianBlur(0.55)), y


def ballpoint(d, p0, p1, rng, width=8.0):
    """One hand stroke: slight arc, tremor, pressure swell and fade, ink skips."""
    n = 60; bow = rng.uniform(-6, 6)
    pts = []
    for i in range(n + 1):
        u = i / n
        x = p0[0] + (p1[0] - p0[0]) * u
        y = p0[1] + (p1[1] - p0[1]) * u + bow * math.sin(math.pi * u) + rng.gauss(0, 0.9)
        pts.append((x, y, u))
    for (x0, y0, u0), (x1, y1, u1) in zip(pts, pts[1:]):
        if rng.random() < 0.04:                       # skip (dry ballpoint)
            continue
        pr = math.sin(math.pi * min(1.0, u0 * 1.4)) ** 0.5 * (0.75 + 0.25 * rng.random())
        d.line((x0, y0, x1, y1), fill=int(255 * min(1.0, 0.35 + 0.65 * pr)), width=max(1, int(width * (0.6 + 0.5 * pr))))


def main():
    rng = random.Random(7)
    ink, ybot = typed(rng)
    paper = np.array(Image.new("RGB", (W, H), (226, 222, 208))).astype(np.float32)
    nz = np.random.default_rng(3).normal(0, 4.0, (H, W, 1)).astype(np.float32)
    paper += nz
    yy = np.linspace(0, 1, H)[:, None, None]; paper *= (0.97 + 0.03 * np.cos(yy * 6))   # faint handling
    k = np.array(ink).astype(np.float32)[..., None] / 255.0
    typed_rgb = paper * (1 - k) + np.array([30, 30, 36], np.float32) * k
    Image.fromarray(np.clip(typed_rgb, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "b_statement.png"))
    red = Image.new("L", (W, H), 0); d = ImageDraw.Draw(red)
    y = 170 + 44 + 30 + 44                             # from the first statement line down
    lines = [l for l in TEXT.split("\n")]
    yy_ = 170
    for li, line in enumerate(lines):
        step = 58 if line else 36
        if li >= 2 and line.strip():
            x_end = 150 + 19.8 * len(line) + rng.uniform(4, 24)
            yc = yy_ + 20
            ballpoint(d, (140 + rng.uniform(-6, 6), yc + rng.uniform(-3, 3)), (x_end, yc + rng.uniform(-5, 5)), rng)
            if rng.random() < 0.5:                    # a second, hastier pass on some lines
                ballpoint(d, (150 + rng.uniform(0, 30), yc + rng.uniform(-4, 4)), (x_end - rng.uniform(0, 40), yc + rng.uniform(-4, 4)), rng, 6.0)
        yy_ += step
    # one big diagonal across the block, as a frustrated final mark
    ballpoint(d, (170, 330), (980, ybot - 50), rng, 10.0)
    ballpoint(d, (195, 345), (965, ybot - 30), rng, 7.0)
    r = np.array(red.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)[..., None] / 255.0
    ink_red = np.array([150, 22, 26], np.float32)
    out = typed_rgb * (1 - 0.88 * r) + ink_red * 0.88 * r
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "b_statement_struck.png"))
    print("[statement] written", OUT)


if __name__ == "__main__":
    main()
