"""Generated textures for the investigation room: typed pages, photo sheets, spreadsheets, folder tabs.
Generic dramatization props: no real names, logos or readable claims."""
import os, math
import numpy as np
import skia

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "generated", "invest")
SANS = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
SANS_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
MONO = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"


def _save(surface, path):
    surface.makeImageSnapshot().save(path, skia.kPNG)
    return path


def _font(f, size):
    return skia.Font(skia.Typeface.MakeFromFile(f), size)


def page(seed, w=850, h=1100, kind="text"):
    """A typed page: header block, paragraphs of grey text bars, a few redaction bars; or a table page."""
    rng = np.random.default_rng(seed)
    s = skia.Surface(w, h); c = s.getCanvas(); c.clear(skia.Color4f(0.93, 0.92, 0.89, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.15, 0.15, 0.16, 1)); c.drawString("CONFIDENTIAL", 70, 90, _font(SANS_SB, 26), p)
    c.drawRect(skia.Rect.MakeXYWH(70, 105, w - 140, 2), p)
    y = 160
    if kind == "table":
        for r in range(26):
            for k in range(5):
                ww = rng.uniform(60, 120)
                p.setColor4f(skia.Color4f(0.35, 0.35, 0.37, 1)); c.drawRect(skia.Rect.MakeXYWH(70 + k * 145, y, ww, 9), p)
            p.setColor4f(skia.Color4f(0.75, 0.75, 0.74, 1)); c.drawRect(skia.Rect.MakeXYWH(70, y + 22, w - 140, 1), p)
            y += 34
    else:
        while y < h - 90:
            n = rng.integers(3, 7)
            for k in range(n):
                ln = (w - 140) * (rng.uniform(0.55, 0.8) if k == n - 1 else rng.uniform(0.92, 1.0))
                red = rng.random() < 0.08
                p.setColor4f(skia.Color4f(0.06, 0.06, 0.06, 1) if red else skia.Color4f(0.42, 0.42, 0.44, 1))
                c.drawRect(skia.Rect.MakeXYWH(70, y, ln, 13 if red else 8), p)
                y += 24
            y += 22
    return _save(s, os.path.join(GEN, f"page_{kind}_{seed}.png"))


def photo(seed, w=800, h=600):
    """A grainy surveillance-style print: soft blurred shapes, timestamp, white border."""
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * 0.92
    yy, xx = np.mgrid[0:h - 80, 0:w - 80].astype(np.float32)
    base = 0.25 + 0.15 * np.sin(xx / rng.uniform(40, 120) + rng.uniform(0, 6)) * np.cos(yy / rng.uniform(40, 120))
    for _ in range(4):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(40, 160)
        base += 0.25 * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
    base += rng.normal(0, 0.05, base.shape)
    img[40:h - 40, 40:w - 40] = np.clip(base, 0, 1)[..., None] * np.array([0.9, 0.95, 1.0])
    from PIL import Image, ImageDraw, ImageFont
    im = Image.fromarray((img * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.text((60, h - 75), f"CAM {rng.integers(1, 9):02d}  {rng.integers(10, 23)}:{rng.integers(10, 59)}:{rng.integers(10, 59)}",
           fill=(240, 240, 240), font=ImageFont.truetype(MONO, 22))
    path = os.path.join(GEN, f"photo_{seed}.png"); im.save(path); return path


def sheet_screen(seed, w=1600, h=900):
    """A monitor: spreadsheet of records (grey cells), one highlighted row."""
    rng = np.random.default_rng(seed)
    s = skia.Surface(w, h); c = s.getCanvas(); c.clear(skia.Color4f(0.95, 0.96, 0.97, 1))
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(skia.Color4f(0.2, 0.25, 0.32, 1)); c.drawRect(skia.Rect.MakeXYWH(0, 0, w, 60), p)
    y = 100; hl = rng.integers(6, 16)
    for r in range(22):
        if r == hl:
            p.setColor4f(skia.Color4f(1.0, 0.92, 0.5, 1)); c.drawRect(skia.Rect.MakeXYWH(20, y - 8, w - 40, 32), p)
        for k in range(7):
            ww = rng.uniform(80, 170)
            p.setColor4f(skia.Color4f(0.4, 0.42, 0.45, 1)); c.drawRect(skia.Rect.MakeXYWH(40 + k * 220, y, ww, 12), p)
        p.setColor4f(skia.Color4f(0.85, 0.86, 0.88, 1)); c.drawRect(skia.Rect.MakeXYWH(20, y + 26, w - 40, 1), p)
        y += 36
    return _save(s, os.path.join(GEN, f"screen_{seed}.png"))


def make_all():
    os.makedirs(GEN, exist_ok=True)
    names = dict(pages=[f"page_text_{k}.png" for k in range(6)] + [f"page_table_{10 + k}.png" for k in range(3)],
                 photos=[f"photo_{k}.png" for k in range(6)], screens=[f"screen_{k}.png" for k in range(3)])
    paths = {k: [os.path.join(GEN, n) for n in v] for k, v in names.items()}
    if all(os.path.exists(q) for v in paths.values() for q in v):
        return paths                      # already generated (seeded, identical): don't rewrite tracked files
    out = dict(pages=[page(k) for k in range(6)] + [page(10 + k, kind="table") for k in range(3)],
               photos=[photo(k) for k in range(6)], screens=[sheet_screen(k) for k in range(3)])
    return out


if __name__ == "__main__":
    print(make_all())
