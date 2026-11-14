"""Typewriters final C: the whole sentence is the headline ("THE SOVIETS SPIED ON AMERICA / USING A"), and a hand-drawn
lime arrow curves from it down to the machine, with "typewriter" written along the curve."""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import cine
cine._grit.__defaults__ = (5, 0.0)
from cine import cine_grade, LIME, WHITE
from compose import load_plate
FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "plates")
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
NAME = sys.argv[3] if len(sys.argv) > 3 else "tw_b"
LAY = dict(l1=("THE SOVIETS SPIED ON AMERICA", 124, 110), l2=("USING A", 124, 252, 830),
           arrow=((1035, 352), (1470, 338), (1345, 600)), label=("typewriter", 56, 38, 0.14, 0.80))


def bez(p0, p1, p2, t):
    a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t * t
    return np.array([a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]])


def dbez(p0, p1, p2, t):
    return np.array([2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]), 2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1])])


def shadowed(base, layer, blur=10, dark=0.6, off=(4, 6)):
    a = layer.split()[-1]
    sh = Image.new("L", base.size, 0); sh.paste(a, off); sh = sh.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * dark))
    base = Image.composite(Image.new("RGB", base.size, (0, 0, 0)), base, sh)
    return Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")


def centred(d, text, font, cx, y, fill):
    bb = d.textbbox((0, 0), text, font=font); d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], y), text, font=font, fill=fill)
    return bb


def compose(img):
    W, H = img.size
    L = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    fa = lambda s: ImageFont.truetype(os.path.join(FONTS, "Anton-Regular.ttf"), s)
    t1, s1, y1 = LAY["l1"]; centred(d, t1, fa(s1), W / 2, y1, WHITE + (255,))
    t2, s2, y2, cx2 = LAY["l2"]; centred(d, t2, fa(s2), cx2, y2, WHITE + (255,))
    img = shadowed(img, L)
    # the arrow: a marker stroke along a quadratic curve, tapering a little, with an open head
    A = Image.new("RGBA", img.size, (0, 0, 0, 0)); da = ImageDraw.Draw(A)
    p0, p1, p2 = LAY["arrow"]; n = 160
    pts = [bez(p0, p1, p2, t / n) for t in range(n + 1)]
    for k in range(n):
        w = int(15 - 4 * k / n)
        da.line([tuple(pts[k]), tuple(pts[k + 1])], fill=LIME + (255,), width=w)
        da.ellipse([pts[k][0] - w / 2, pts[k][1] - w / 2, pts[k][0] + w / 2, pts[k][1] + w / 2], fill=LIME + (255,))
    tip = pts[-1]; tg = dbez(p0, p1, p2, 1.0); tg /= np.linalg.norm(tg)
    for s in (1, -1):
        ang = math.atan2(tg[1], tg[0]) + math.pi + s * math.radians(32)
        e = tip + 62 * np.array([math.cos(ang), math.sin(ang)])
        da.line([tuple(tip), tuple(e)], fill=LIME + (255,), width=13)
        da.ellipse([e[0] - 6, e[1] - 6, e[0] + 6, e[1] + 6], fill=LIME + (255,))
    da.ellipse([tip[0] - 7, tip[1] - 7, tip[0] + 7, tip[1] + 7], fill=LIME + (255,))
    # label along the outside of the curve, each letter turned to the tangent
    word, size, off, ta, tb = LAY["label"]
    fm = ImageFont.truetype(os.path.join(FONTS, "PermanentMarker-Regular.ttf"), size)
    widths = [fm.getlength(ch) for ch in word]; total = sum(widths)
    ts = np.linspace(0, 1, 400); P_ = np.array([bez(p0, p1, p2, t) for t in ts])
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]
    s0 = np.interp(ta, ts, seg); s1_ = np.interp(tb, ts, seg)
    start = s0 + ((s1_ - s0) - total) / 2
    pos = start
    for ch, wd in zip(word, widths):
        t = np.interp(pos + wd / 2, seg, ts); c = bez(p0, p1, p2, t); tg = dbez(p0, p1, p2, t); tg /= np.linalg.norm(tg)
        nrm = np.array([tg[1], -tg[0]])                     # outward (to the upper right of the curve)
        g = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0)); ImageDraw.Draw(g).text((size, size), ch, font=fm, fill=LIME + (255,), anchor="mm")
        g = g.rotate(-math.degrees(math.atan2(tg[1], tg[0])), resample=Image.BICUBIC)
        cc = c + nrm * off
        A.alpha_composite(g, (int(cc[0] - size), int(cc[1] - size)))
        pos += wd
    return shadowed(img, A, blur=8, dark=0.7, off=(3, 5))


if __name__ == "__main__":
    D = os.path.join(OUT, "download_c"); os.makedirs(D, exist_ok=True)
    g = cine_grade(load_plate(os.path.join(P, NAME + ".png")), clarity=0.0, grain=0.0, bloom=0.15,
                   shadows=(0.0, 0.0, 0.0), highs=(1.03, 1.0, 0.96), vignette=0.45)
    t = compose(g)
    t.save(os.path.join(OUT, "typewriters_final_C.jpg"), quality=97, subsampling=0)
    t.save(os.path.join(D, "typewriters_thumbnail_ARROW.png")); t.save(os.path.join(D, "typewriters_thumbnail_ARROW_youtube.jpg"), quality=96, subsampling=0)
    g.save(os.path.join(D, "typewriters_thumbnail_notext.png")); g.save(os.path.join(D, "typewriters_thumbnail_notext_youtube.jpg"), quality=96, subsampling=0)
    print("done")
