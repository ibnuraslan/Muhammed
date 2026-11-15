"""$25M Drain: the diamond on a jeweller's display against a dark brick wall; creepy headline "$25M… / SEALED UNDER A DRAIN".
  python make_display.py <plate dir> <out dir> [pack]"""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from make import save, ANTON, W, H, YEL
RED = (214, 22, 22)


def grade(pl, mk):
    a = np.asarray(pl.convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    yy, xx = np.mgrid[0:H, 0:W]
    ys, xs = np.nonzero(mk > 60); cx, cy = (xs.mean(), ys.mean()) if len(xs) else (W / 2, H / 2)
    r = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2)
    v = np.clip(1.15 - 1.1 * r, 0.25, 1.0)[..., None]                                   # dark, cold edges
    a = a * v
    l = a.mean(-1, keepdims=True); edge = np.clip(r * 1.6, 0, 1)[..., None]
    a = a * (1 - edge * 0.35) + l * np.array([0.85, 0.95, 1.15]) * edge * 0.35          # desaturate + cool toward the edges
    # a faint red glow behind the stone (not on it)
    g = np.exp(-(((xx - cx) / 260) ** 2 + ((yy - cy + 20) / 200) ** 2))[..., None]
    stone = (np.asarray(Image.fromarray(mk).filter(ImageFilter.MaxFilter(9))).astype(np.float32) / 255)[..., None]
    a = a + g * (1 - stone) * np.array([0.30, 0.02, 0.02])
    s = a * a * (3 - 2 * a); a = 0.75 * a + 0.25 * s
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA"), (cx, cy)


def distress(alpha, seed=5):
    """Eat into lettering: speckle, pits and a few scratches."""
    rnd = np.random.default_rng(seed)
    n = rnd.random((H // 3, W // 3)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    fine = rnd.random((H, W)).astype(np.float32)
    keep = ((n > 0.17) & (fine > 0.025)).astype(np.float32)
    sc = Image.new("L", (W, H), 255); d = ImageDraw.Draw(sc); r = random.Random(seed)
    for _ in range(14):
        x, y = r.uniform(0, W), r.uniform(0, H * 0.5); ln = r.uniform(40, 220); ang = r.uniform(-0.5, 0.5)
        d.line([(x, y), (x + ln * np.cos(ang), y + ln * np.sin(ang))], fill=0, width=r.choice([2, 3, 4]))
    keep = keep * (np.asarray(sc).astype(np.float32) / 255)
    return Image.fromarray((np.asarray(alpha).astype(np.float32) * keep).astype(np.uint8))


def compose(plate, mask, text=True):
    mk = np.asarray(Image.open(mask).split()[-1].resize((W, H), Image.LANCZOS))
    img, (cx, cy) = grade(Image.open(plate), mk)
    if not text:
        return img.convert("RGB")
    T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); t = ImageDraw.Draw(T)
    f1 = ImageFont.truetype(ANTON, 250); f2 = ImageFont.truetype(ANTON, 128)
    l1, l2 = "$25M…", "SEALED UNDER A DRAIN"
    w1 = t.textlength(l1, font=f1); w2 = t.textlength(l2, font=f2)
    t.text((W / 2 - w1 / 2, 6), l1, font=f1, fill=YEL + (255,))
    t.text((W / 2 - w2 / 2, 290), l2, font=f2, fill=RED + (255,))
    a = distress(T.split()[-1]); T.putalpha(a)
    sh = a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(min(255, v * 1.1)))
    blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); blk.putalpha(sh)
    img.alpha_composite(blk); img.alpha_composite(blk); img.alpha_composite(T)
    return img.convert("RGB")


if __name__ == "__main__":
    PD, OUT = sys.argv[1:3]
    pl, mk = os.path.join(PD, "dd_velvet.png"), os.path.join(PD, "dd_velvet_mask.png")
    t = compose(pl, mk); t.save(os.path.join(OUT, "drain_display.jpg"), quality=96, subsampling=0)
    if "pack" in sys.argv:
        D = os.path.join(OUT, "download_display"); os.makedirs(D, exist_ok=True)
        save(t, "drain_thumbnail_SEALED", D); save(compose(pl, mk, text=False), "drain_thumbnail_display_notext", D)
    print("done")
