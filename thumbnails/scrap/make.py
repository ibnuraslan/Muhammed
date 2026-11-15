"""Radioactive Scrap thumbnails: A = hazard poster (cut-out container on hazard yellow), C = radiation-detector view.
  python make.py <plates dir> <out dir>"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
MONO = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
W, H = 1920, 1080
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "plates")
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
F = lambda name, s: ImageFont.truetype(os.path.join(FONTS, name), s)
YEL = (247, 200, 0); BLK = (16, 15, 14); RED = (222, 30, 30); WHITE = (250, 248, 244)


def trefoil(size, col, alpha=255):
    """The radiation mark: three 60-degree blades and a hub, drawn at 4x and downsampled."""
    S = size * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = S / 2
    R1, R0, r = S * 0.5, S * 0.15, S * 0.1
    for k in range(3):
        a0 = -90 - 30 + k * 120
        d.pieslice([c - R1, c - R1, c + R1, c + R1], a0, a0 + 60, fill=col + (alpha,))
    d.ellipse([c - R0, c - R0, c + R0, c + R0], fill=(0, 0, 0, 0))
    d.ellipse([c - r, c - r, c + r, c + r], fill=col + (alpha,))
    return im.resize((size, size), Image.LANCZOS)


def outline(cut, px=12, col=WHITE):
    a = cut.split()[-1]
    big = a.filter(ImageFilter.MaxFilter(px * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    o = Image.new("RGBA", cut.size, col + (0,)); o.putalpha(big)
    o.alpha_composite(cut)
    return o


def shadow(base, layer, off=(14, 20), blur=18, op=0.55):
    a = layer.split()[-1].point(lambda v: int(v * op))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); m = Image.new("L", base.size, 0); m.paste(a, off)
    sh.putalpha(m.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(sh); base.alpha_composite(layer)
    return base


def text_layer(txt, font, fill, stroke=0, sfill=None):
    bb = font.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (bb[2] - bb[0] + 4, bb[3] - bb[1] + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - bb[0], 2 - bb[1]), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im


def price_tag(txt, h=230, rot=-12):
    f = F("Anton-Regular.ttf", int(h * 0.72)); t = text_layer(txt, f, WHITE + (255,))
    w = t.width + int(h * 0.75); im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    n = h * 0.32                                         # notched left end like a shop tag, with a punched hole
    d.polygon([(20 + n, 20), (20 + w, 20), (20 + w, 20 + h), (20 + n, 20 + h), (20, 20 + h / 2)], fill=RED + (255,))
    d.ellipse([20 + n * 0.55 - 14, 20 + h / 2 - 14, 20 + n * 0.55 + 14, 20 + h / 2 + 14], fill=(0, 0, 0, 0))
    im.alpha_composite(t, (int(20 + n + (w - n - t.width) / 2), int(20 + (h - t.height) / 2)))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def poster(cut_path):
    bg = Image.new("RGBA", (W, H), YEL + (255,))
    # soft light falloff so the yellow is not flat
    yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - 1250) / W) ** 2 + ((yy - 560) / H) ** 2)
    v = np.clip(1.06 - 0.55 * r, 0.62, 1.06)[..., None]
    bg = Image.fromarray(np.clip(np.asarray(bg).astype(np.float32) * np.concatenate([v, v, v, np.ones_like(v)], -1), 0, 255).astype(np.uint8))
    bg.alpha_composite(trefoil(980, BLK, 34), (1420 - 490, 590 - 490))
    # hazard stripes along the top edge
    st = Image.new("RGBA", (W, 64), YEL + (255,)); d = ImageDraw.Draw(st)
    for x in range(-140, W + 140, 110):
        d.polygon([(x, 0), (x + 55, 0), (x + 119, 64), (x + 64, 64)], fill=BLK + (255,))
    bg.alpha_composite(st, (0, 0))
    # the container: cut out, white outline, big on the right (clear of the bottom-right timestamp)
    cut = Image.open(cut_path).convert("RGBA"); cut = cut.crop(cut.getbbox())
    sc = 780 / cut.height; cut = cut.resize((int(cut.width * sc), 780), Image.LANCZOS)
    cut = outline(cut, 11)
    bg = shadow(bg, _at(cut, 1425 - cut.width // 2, 165), off=(18, 26), blur=24, op=0.45)
    # the words, stacked left: RADIOACTIVE / SCRAP FOR, then the red $30 tag
    y = 120
    for word, wd in (("RADIOACTIVE", 860), ("SCRAP FOR", 860)):
        t = text_layer(word, F("Anton-Regular.ttf", 300), BLK + (255,))
        t = t.resize((wd, int(t.height * wd / t.width)), Image.LANCZOS)
        bg = shadow(bg, _at(t, 70, y), off=(0, 0), blur=6, op=0.0); y += t.height + 26
    tag = price_tag("$30!", 230, -8)
    bg = shadow(bg, _at(tag, 300, y + 10), off=(10, 16), blur=14, op=0.5)
    return bg.convert("RGB")


def _at(im, x, y):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); lay.alpha_composite(im, (int(x), int(y))); return lay


def detector(yard_path, mask_path):
    src = np.asarray(Image.open(yard_path).convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    lum = src @ np.array([0.3, 0.59, 0.11], np.float32)
    lum = np.clip((lum - 0.12) / 0.75, 0, 1) ** 1.35
    g = np.stack([lum * 0.25, lum * 1.0, lum * 0.42], -1) * 0.9 + np.array([0.0, 0.035, 0.015])  # green night-vision ramp
    yy_, xx_ = np.mgrid[0:H, 0:W]
    m = np.asarray(Image.open(mask_path).split()[-1].resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    heat = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(90))).astype(np.float32) / 255
    core = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(25))).astype(np.float32) / 255
    # the drum's core white-hot, falling off to orange/red at the frame, plus a modest halo
    ys_, xs_ = np.nonzero(m > 0.5); cy_, cx_ = ys_.mean(), xs_.mean(); ext = max(np.ptp(xs_), np.ptp(ys_)) / 2
    rr = np.sqrt((xx_ - cx_) ** 2 + (yy_ - cy_) ** 2) / ext
    inner = core * np.clip(1.25 - rr, 0, 1)
    h = np.clip(inner * 1.25 + heat * 0.55, 0, 1.15)
    ramp = lambda t: np.stack([np.clip(t * 2.2, 0, 1), np.clip(t * 1.6 - 0.45, 0, 1), np.clip(t * 2.0 - 1.4, 0, 1)], -1)
    col = ramp(h) ; a = np.clip(h * 0.85, 0, 0.78)[..., None]
    img = g * (1 - a) + col * a + (lum[..., None] * a * 0.25)
    # gamma speckle: white sparkle hits on the sensor, densest near the source
    rng = np.random.default_rng(5)
    field = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(260))).astype(np.float32) / 255
    field = field / max(field.max(), 1e-6)
    hits = rng.random((H, W)) < (0.00004 + 0.0028 * field ** 2.2)
    sp = np.asarray(Image.fromarray((hits * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) / 255
    img = np.clip(img + sp[..., None] * np.array([0.85, 1.0, 0.9]) * 0.9, 0, 1)
    # scanlines + a faint vignette
    sl = 1 - 0.06 * (np.arange(H) % 4 < 2)[:, None, None]
    yy, xx = np.mgrid[0:H, 0:W]; vg = np.clip(1.15 - 0.75 * np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2), 0, 1)[..., None]
    out = Image.fromarray((np.clip(img * sl * vg, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(out); hg = (150, 255, 170, 255); fm = ImageFont.truetype(MONO, 34); fs = ImageFont.truetype(MONO, 26)
    # frame corners
    L_, T = 40, 40
    for (x, y, sx, sy) in ((L_, T, 1, 1), (W - L_, T, -1, 1), (L_, H - T, 1, -1)):
        d.line([(x, y), (x + 70 * sx, y)], fill=hg, width=5); d.line([(x, y), (x, y + 70 * sy)], fill=hg, width=5)
    d.ellipse([70, 66, 96, 92], fill=(255, 40, 40, 255)); d.text((108, 62), "REC", font=fm, fill=(255, 255, 255, 255))
    d.text((70, 112), "GAMMA SCAN", font=fs, fill=hg); d.text((70, 146), "13 DEC 1998", font=fs, fill=hg)
    # target box around the hotspot
    ys, xs = np.nonzero(m > 0.5)
    x0, x1, y0, y1 = xs.min() - 30, min(xs.max() + 30, W - 280), ys.min() - 30, min(ys.max() + 30, H - 120)
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(x, y), (x + 50 * sx, y)], fill=(255, 60, 50, 255), width=6); d.line([(x, y), (x, y + 50 * sy)], fill=(255, 60, 50, 255), width=6)
    lab = "SOURCE DETECTED"; tw = d.textlength(lab, font=fm)
    d.rectangle([x0, y0 - 52, x0 + tw + 24, y0 - 8], fill=(255, 40, 40, 235)); d.text((x0 + 12, y0 - 50), lab, font=fm, fill=(255, 255, 255, 255))
    # dose-rate bar, pinned in the red (top right)
    bx, by = W - 440, 70
    d.text((bx, by), "DOSE RATE", font=fs, fill=hg)
    for k in range(14):
        cc = (150, 255, 170, 255) if k < 6 else ((255, 210, 60, 255) if k < 10 else (255, 50, 40, 255))
        d.rectangle([bx + k * 27, by + 38, bx + k * 27 + 21, by + 74], fill=cc)
    d.text((bx, by + 84), "OFF SCALE", font=fs, fill=(255, 70, 60, 255))
    # headline, bottom left: RADIOACTIVE / SCRAP FOR [$30!]
    f1 = F("Anton-Regular.ttf", 190); f2 = F("Anton-Regular.ttf", 150)
    t1 = text_layer("RADIOACTIVE", f1, WHITE + (255,)); t2 = text_layer("SCRAP FOR", f2, WHITE + (255,))
    y2 = H - 70 - t2.height; y1 = y2 - 18 - t1.height
    lay = _at(t1, 70, y1); lay.alpha_composite(t2, (72, y2))
    box = Image.new("RGBA", (0, 0))
    t3 = text_layer("$30!", f2, WHITE + (255,))
    bxr = Image.new("RGBA", (t3.width + 44, t3.height + 30), RED + (255,)); bxr.alpha_composite(t3, (22, 15))
    lay.alpha_composite(bxr, (72 + t2.width + 26, y2 - 15))
    out = shadow(out, lay, off=(6, 8), blur=10, op=0.7)
    return out.convert("RGB")


def save(img, stem, D):
    img.save(os.path.join(D, stem + ".png")); img.save(os.path.join(D, stem + "_youtube.jpg"), quality=95, subsampling=0)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a = poster(os.path.join(P, "rs_cut.png")); a.save(os.path.join(OUT, "scrap_A_poster.jpg"), quality=96, subsampling=0)
    c = detector(os.path.join(P, "rs_yard.png"), os.path.join(P, "rs_yard_mask.png")); c.save(os.path.join(OUT, "scrap_C_detector.jpg"), quality=96, subsampling=0)
    print("done")
