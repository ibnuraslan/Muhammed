"""Textures for the written props (run with system python3, PIL): make_textures.py log|slate <out.png>"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def make(path, kind, w=1600, h=1100):
    """The logbook's last written page / the slate's chalk lines, drawn to a texture once (in Python, PIL)."""
    fonts = os.path.join(P1, "assets", "fonts")
    hand = os.path.join(fonts, "Hand.ttf")
    if not os.path.exists(hand):
        hand = os.path.join(P1, "assets", "fonts", "CourierPrime-Regular.ttf")
    if kind == "log":
        im = Image.new("RGB", (w, h), (226, 212, 178)); d = ImageDraw.Draw(im)
        for y in range(120, h, 54):
            d.line([(40, y), (w - 40, y)], fill=(170, 160, 150), width=2)
        d.line([(w // 2, 0), (w // 2, h)], fill=(150, 130, 100), width=6)
        f = ImageFont.truetype(hand, 40); fs = ImageFont.truetype(hand, 30)
        d.text((70, 40), "Mary Celeste  from New York towards Genoa", font=fs, fill=(40, 30, 25))
        lines = ["Nov 21  Wind S.W.  fresh  all sail set", "Nov 22  Light winds  steady  course E by S",
                 "Nov 23  Fresh breeze  heavy sea", "Nov 24  Wind S.W.  Lat 36 56 N   Long 27 20 W",
                 "            the ship going  8 knots"]
        for k, t in enumerate(lines):
            d.text((70, 130 + k * 108), t, font=f, fill=(35, 28, 24))
        im = im.filter(ImageFilter.GaussianBlur(0.6))
    else:
        im = Image.new("RGB", (w, h), (32, 36, 38)); d = ImageDraw.Draw(im)
        f = ImageFont.truetype(hand, 54)
        lines = ["Nov 25", "5 a.m.  made the island of", "St Mary's  bearing  E.S.E.", "8 a.m.  Eastern point bore",
                 "S.S.W.  6 miles distant"]
        for k, t in enumerate(lines):
            d.text((80, 90 + k * 170), t, font=f, fill=(215, 215, 205))
        im = im.filter(ImageFilter.GaussianBlur(1.0))
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(path)
    return path




def compass_card(path, n=1400):
    """A 19th-century compass card: cream paper, 32-point rose in black and red, N fleur, degree ring."""
    import math
    im = Image.new("RGB", (n, n), (226, 214, 184)); d = ImageDraw.Draw(im); c = n / 2
    f = ImageFont.truetype(os.path.join(P1, "assets", "fonts", "CourierPrime-Bold.ttf"), int(n * 0.05))
    for k in range(360):
        a = math.radians(k); r0 = c * (0.9 if k % 10 else 0.86); r1 = c * 0.95
        d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + r1 * math.sin(a), c - r1 * math.cos(a))], fill=(30, 25, 20), width=2)
    d.ellipse([c - c * 0.96, c - c * 0.96, c + c * 0.96, c + c * 0.96], outline=(30, 25, 20), width=4)
    d.ellipse([c - c * 0.84, c - c * 0.84, c + c * 0.84, c + c * 0.84], outline=(30, 25, 20), width=3)
    for k in range(32):
        a = math.radians(k * 11.25); L = c * (0.8 if k % 8 == 0 else 0.62 if k % 4 == 0 else 0.48 if k % 2 == 0 else 0.4)
        w = c * (0.09 if k % 8 == 0 else 0.06 if k % 4 == 0 else 0.04)
        tip = (c + L * math.sin(a), c - L * math.cos(a))
        l1 = (c + w * math.sin(a - math.pi / 2), c - w * math.cos(a - math.pi / 2))
        l2 = (c + w * math.sin(a + math.pi / 2), c - w * math.cos(a + math.pi / 2))
        col = (150, 25, 20) if k % 8 == 0 else (30, 25, 20)
        d.polygon([tip, l1, (c, c)], fill=col); d.polygon([tip, l2, (c, c)], fill=(226, 214, 184), outline=col)
    for lab, k in (("N", 0), ("E", 8), ("S", 16), ("W", 24)):
        a = math.radians(k * 11.25); r = c * 0.72
        bb = d.textbbox((0, 0), lab, font=f)
        d.text((c + r * math.sin(a) - (bb[2] - bb[0]) / 2, c - r * math.cos(a) - (bb[3] - bb[1]) / 2 - bb[1]), lab, font=f, fill=(30, 25, 20))
    d.ellipse([c - 18, c - 18, c + 18, c + 18], fill=(120, 90, 40))
    im.save(path)


def cracks(path, n=1200, seed=5):
    """RGBA crack map for the compass glass: R = crack lines, A = glass present (a hole knocked out of it)."""
    import math, random
    rnd = random.Random(seed)
    im = Image.new("RGBA", (n, n), (0, 0, 0, 255)); d = ImageDraw.Draw(im); c = n / 2
    ix, iy = c * 0.82, c * 1.12                      # impact point, off centre
    for k in range(17):                               # radial cracks, wandering
        a = rnd.uniform(0, 2 * math.pi); x, y = ix, iy; L = 0
        while 0 < x < n and 0 < y < n and L < n:
            a += rnd.gauss(0, 0.12); st = rnd.uniform(8, 20)
            nx_, ny_ = x + st * math.cos(a), y + st * math.sin(a)
            d.line([(x, y), (nx_, ny_)], fill=(255, 0, 0, 255), width=3); x, y = nx_, ny_; L += st
    for r in (60, 130, 230):                          # concentric breaks
        pts = []
        for k in range(40):
            a = 2 * math.pi * k / 40; rr = r * rnd.uniform(0.85, 1.15)
            pts.append((ix + rr * math.cos(a), iy + rr * math.sin(a)))
        d.line(pts + [pts[0]], fill=(255, 0, 0, 255), width=2)
    hole = [(ix + 95 * math.cos(a) * rnd.uniform(0.7, 1.2), iy + 95 * math.sin(a) * rnd.uniform(0.7, 1.2))
            for a in [2 * math.pi * k / 9 for k in range(9)]]
    d.polygon(hole, fill=(0, 0, 0, 0))
    im.save(path)


if __name__ == "__main__":
    {"compass": compass_card, "cracks": cracks}.get(sys.argv[1], lambda p: make(p, sys.argv[1]))(sys.argv[2])
