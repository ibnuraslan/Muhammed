"""Finish the three plates: grade + text, then a review sheet with the phone-size check.
  python make.py            -> out/<film>_thumbnail.jpg (+ _notext), out/SHEET.jpg"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "lib"))
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import compose
compose.FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
from compose import draw_text, WHITE, LIME, W, H, load_plate
from cine import cine_grade

P = os.path.join(HERE, "plates"); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
FONTS = compose.FONTS


def darken(img, box_, strength=0.55, feather=260):
    """Soft dark pool behind the words (top-left), so white type reads on any plate."""
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m); d.rectangle(box_, fill=int(255 * strength))
    m = m.filter(ImageFilter.GaussianBlur(feather))
    return Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, m)


def marker_arrow(img, pts, color=LIME, width=16, head=46):
    """Hand-drawn style arrow along a smooth curve (quadratic Bezier through 3 points)."""
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    (x0, y0), (cx, cy), (x1, y1) = pts
    path = []
    for i in range(61):
        t = i / 60
        path.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    ds.line([(x + 4, y + 6) for x, y in path], fill=(0, 0, 0, 150), width=width, joint="curve")
    d.line(path, fill=color, width=width, joint="curve")
    ex, ey = path[-1]; px, py = path[-6]
    a = math.atan2(ey - py, ex - px)
    for sgn in (1, -1):
        hx = ex - head * math.cos(a + sgn * 0.5); hy = ey - head * math.sin(a + sgn * 0.5)
        ds.line([(hx + 4, hy + 6), (ex + 4, ey + 6)], fill=(0, 0, 0, 150), width=width)
        d.line([(hx, hy), (ex, ey)], fill=color, width=width)
    for x, y in (path[0], (ex, ey)):
        d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=color)
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    out = img.convert("RGBA"); out.alpha_composite(sh); out.alpha_composite(L)
    return out.convert("RGB")


def sparkle(img, cx, cy, R=70, strength=0.9):
    """A small four-point star on the big stone (a real lens glint, kept modest)."""
    Lm = Image.new("L", img.size, 0); d = ImageDraw.Draw(Lm)
    for ang, rr, wd in ((0, R, 4), (90, R, 4), (45, R * 0.4, 2.5), (135, R * 0.4, 2.5)):
        a = math.radians(ang)
        for s_ in (1, -1):
            x2, y2 = cx + s_ * rr * math.cos(a), cy + s_ * rr * math.sin(a)
            d.polygon([(cx - wd * math.sin(a), cy + wd * math.cos(a)), (x2, y2), (cx + wd * math.sin(a), cy - wd * math.cos(a))], fill=255)
    m = np.clip(np.asarray(Lm.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255 +
                np.asarray(Lm.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255 * 0.8, 0, 1)[..., None] * strength
    a = np.asarray(img).astype(np.float32)
    a = a * (1 - m) + np.array([255, 250, 238]) * m
    return Image.fromarray(a.astype(np.uint8))


def finish(name, plate, build):
    g = cine_grade(load_plate(os.path.join(P, plate)), clarity=0.35, grain=0.008, bloom=0.18,
                   shadows=(0.0, 0.01, 0.02), highs=(1.03, 1.0, 0.96), vignette=0.3)
    g.save(os.path.join(OUT, f"{name}_thumbnail_notext.jpg"), quality=95, subsampling=0)
    t = build(g)
    t.save(os.path.join(OUT, f"{name}_thumbnail.jpg"), quality=95, subsampling=0)
    return os.path.join(OUT, f"{name}_thumbnail.jpg")


def drain(g):
    g = darken(g, (0, 0, 1150, 300), 0.75, 160)
    t = draw_text(g, ["FOUND ON"], 90, 60, 92, font="anton", color=WHITE, tracking=4)
    t = draw_text(t, [[("SEARCH ", WHITE), ("#5", LIME)]], 82, 150, 250, font="anton")
    return t


def killer(g):
    g = darken(g, (0, 0, 820, 640), 0.7, 180)
    t = draw_text(g, ["HE LIVED", [("IN ", WHITE), ("HERE", LIME)]], 80, 70, 230, font="anton", spacing=0.98)
    return marker_arrow(t, ((560, 560), (700, 780), (850, 640)))


def radio(g):
    g = darken(g, (0, 0, 1100, 380), 0.6, 160)
    return draw_text(g, ["HE NEVER", [("SAID A ", WHITE), ("WORD", LIME)]], 80, 60, 185, font="anton", spacing=0.98)


JOBS = {"drain": ("drain.png", drain), "killer": ("killer.png", killer), "radio": ("radio.png", radio)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    done = [finish(n, *JOBS[n]) for n in names if os.path.exists(os.path.join(P, JOBS[n][0]))]
    compose.sheet([(p_, os.path.basename(p_)) for p_ in done], os.path.join(OUT, "SHEET.jpg"), "Seldom thumbnails: approved concepts")
    print("\n".join(done))
