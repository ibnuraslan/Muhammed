"""Finish a thumbnail plate: light grade (vignette, contrast, fine grain), then the word(s) in a bold condensed sans.
Used as a library (compose(...)) by each film's make.py, or:  python compose.py plate.png out.jpg "WORD?" [x y size]"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
FONT = {"anton": "Anton-Regular.ttf", "bebas": "BebasNeue-Regular.ttf", "oswald": "Oswald-Bold.ttf", "montserrat": "Montserrat-Black.ttf", "archivo": "ArchivoBlack-Regular.ttf"}
W, H = 1920, 1080
RED = (214, 28, 32)
WHITE = (244, 242, 238)
LIME = (224, 248, 0)        # Seldom brand lime #E0F800
OUTLINE = (24, 24, 0)      # logo outline #181800


def grade(img, vignette=0.35, contrast=1.04, grain=0.012, lift=0.0, seed=1):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    r = np.hypot((xx / a.shape[1] - 0.5) * 1.6, (yy / a.shape[0] - 0.5) * 1.2)
    v = 1.0 - vignette * np.clip(r - 0.25, 0, None) ** 1.6
    a = a * v[..., None]
    a = np.clip((a - 0.5) * contrast + 0.5 + lift, 0, 1)
    rng = np.random.default_rng(seed)
    g = rng.normal(0, grain, a.shape[:2]).astype(np.float32)
    a = np.clip(a + g[..., None], 0, 1)
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8))


def load_plate(path):
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    return im


def draw_text(img, lines, x, y, size, font="anton", color=WHITE, accent=None, anchor="la", spacing=0.92,
              shadow=0.55, tracking=0, stroke=0, stroke_fill=(24, 24, 0)):
    """lines: list of strings, or of [(text, color), ...] runs. Clean edge, soft dark shadow (no glow)."""
    f = ImageFont.truetype(os.path.join(FONTS, FONT[font]), size)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(layer); ds = ImageDraw.Draw(sh)
    cy = y
    for ln in lines:
        runs = ln if isinstance(ln, list) else [(ln, color)]
        total = sum(d.textlength(t, font=f) + tracking * len(t) for t, _ in runs)
        cx = x - total if anchor[0] == "r" else x - total / 2 if anchor[0] == "m" else x
        for t, c in runs:
            for ch in t:
                d.text((cx, cy), ch, font=f, fill=c, stroke_width=stroke, stroke_fill=stroke_fill)
                ds.text((cx + size * 0.02, cy + size * 0.035), ch, font=f, fill=255)
                cx += d.textlength(ch, font=f) + tracking
        cy += size * spacing
    if shadow:
        sh = sh.filter(ImageFilter.GaussianBlur(size * 0.06)).point(lambda p: int(p * shadow))
        img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, sh)
    img = img.convert("RGBA"); img.alpha_composite(layer)
    return img.convert("RGB")


def save(img, path, q=94):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".jpg"):
        img.save(path, quality=q, subsampling=0, optimize=True)
    else:
        img.save(path)


def sheet(items, path, title=""):
    """items: [(image_path, label)] -> one sheet: each concept full width row + its 320x180 phone-size check."""
    rows = []
    for p, lab in items:
        im = Image.open(p).convert("RGB")
        big = im.resize((1280, 720), Image.LANCZOS)
        small = im.resize((320, 180), Image.LANCZOS)
        row = Image.new("RGB", (1280 + 40 + 320 + 40, 720 + 70), (18, 18, 20))
        row.paste(big, (20, 50)); row.paste(small, (1280 + 40, 50))
        d = ImageDraw.Draw(row)
        f = ImageFont.truetype(os.path.join(FONTS, FONT["oswald"]), 30)
        d.text((20, 8), lab, font=f, fill=WHITE)
        d.text((1340, 240), "phone size", font=ImageFont.truetype(os.path.join(FONTS, FONT["oswald"]), 20), fill=(150, 150, 150))
        rows.append(row)
    Wd = rows[0].width; Ht = sum(r.height for r in rows) + 60
    sh = Image.new("RGB", (Wd, Ht), (18, 18, 20))
    ImageDraw.Draw(sh).text((20, 12), title, font=ImageFont.truetype(os.path.join(FONTS, FONT["oswald"]), 36), fill=WHITE)
    y = 60
    for r in rows:
        sh.paste(r, (0, y)); y += r.height
    save(sh, path, q=88)
