"""Poster-style finishing: cinematic grade (contrast curve, split-tone, bloom, clarity, grain) and textured title text
(spaced kicker + huge condensed word that fades into the scene at the bottom, with a fine grit), optionally behind a matte."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from compose import FONTS, FONT, W, H, LIME, WHITE, load_plate


def cine_grade(img, bloom=0.25, clarity=0.6, shadows=(0.02, 0.05, 0.07), highs=(1.04, 1.0, 0.94), vignette=0.45, grain=0.018):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    s_ = a * a * (3 - 2 * a)                                      # S-curve: deeper shadows, brighter highlights
    a = np.clip(0.55 * a + 0.45 * s_, 0, 1)
    l = a.mean(axis=2, keepdims=True)
    a = a + np.array(shadows) * (1 - l) ** 2 * 1.5                # cool shadows
    a = a * (1 + (np.array(highs) - 1) * l)                       # warm highlights
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    det = im.filter(ImageFilter.UnsharpMask(radius=6, percent=int(clarity * 120), threshold=2))   # local contrast / crispness
    im = det.filter(ImageFilter.UnsharpMask(radius=1.2, percent=60, threshold=1))
    b = np.asarray(im).astype(np.float32) / 255
    hi = np.clip((b - 0.6) / 0.4, 0, 1)
    glow = np.asarray(Image.fromarray((hi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))).astype(np.float32) / 255
    b = 1 - (1 - b) * (1 - glow * bloom)                          # screen-blend bloom
    yy, xx = np.mgrid[0:b.shape[0], 0:b.shape[1]]
    r = np.hypot((xx / b.shape[1] - 0.5) * 1.5, (yy / b.shape[0] - 0.5) * 1.3)
    b = b * (1 - vignette * np.clip(r - 0.3, 0, None) ** 1.5)[..., None]
    b = b + np.random.default_rng(3).normal(0, grain, b.shape[:2])[..., None]
    return Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8))


def _grit(size, seed=5, amount=0.12):
    rng = np.random.default_rng(seed)
    n = rng.random((size[1] // 2, size[0] // 2)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize(size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))) / 255
    return 1 - amount * np.clip((n - 0.55) * 4, 0, 1)


def title(img, kicker, word, word_color=WHITE, kicker_color=LIME, word_font="anton", size=360, y=140, kicker_size=64,
          tracking_k=14, fade=0.45, matte=None, glow=0.0, stroke=0):
    """Kicker (spaced caps) above a huge condensed word; the word fades out toward its bottom; grit texture."""
    out = img.convert("RGB")
    fk = ImageFont.truetype(os.path.join(FONTS, FONT["montserrat"]), kicker_size)
    fw = ImageFont.truetype(os.path.join(FONTS, FONT[word_font]), size)
    # word layer (alpha) with vertical fade
    L = Image.new("L", out.size, 0); d = ImageDraw.Draw(L)
    bw = d.textbbox((0, 0), word, font=fw)
    x = (W - (bw[2] - bw[0])) / 2 - bw[0]
    d.text((x, y), word, font=fw, fill=255)
    top, bot = y + bw[1], y + bw[3]
    ramp = np.ones(out.size[::-1], np.float32)
    yy = np.arange(out.size[1])[:, None]
    f0 = top + (bot - top) * (1 - fade)
    ramp = np.clip(1 - (yy - f0) / max(1, (bot - f0)) * 0.85, 0.15, 1) * np.ones((1, out.size[0]))
    a = np.asarray(L).astype(np.float32) / 255 * ramp * _grit(out.size)
    base = np.asarray(out).astype(np.float32)
    col = np.array(word_color, np.float32)
    if glow:
        g = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
        base = base + (col - base) * (g * glow)[..., None] * 0.5
    sh = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255
    base = base * (1 - 0.45 * sh[..., None])
    comp = base * (1 - a[..., None]) + col * a[..., None]
    res = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8))
    # kicker, letter-spaced, centred above the word
    dk = ImageDraw.Draw(res)
    widths = [dk.textlength(ch, font=fk) for ch in kicker]
    tw = sum(widths) + tracking_k * (len(kicker) - 1)
    kx = (W - tw) / 2; ky = top - kicker_size - 22
    for ch, wd in zip(kicker, widths):
        dk.text((kx + 2, ky + 3), ch, font=fk, fill=(0, 0, 0))
        dk.text((kx, ky), ch, font=fk, fill=kicker_color); kx += wd + tracking_k
    if matte is not None:
        m = Image.open(matte).split()[-1].resize(out.size, Image.LANCZOS)
        res = Image.composite(out, res, m)
    return res
