"""$25M Drain, idea 3: split thumbnail. Left: the diamond in a jeweller's velvet display ("$25M"); right: the same stone
on bricks in the drain ("IN A DRAIN!"); a ragged paper rip down the middle.
  python make_split.py <velvet plate dir> <drain plate dir> <out dir> [pack]"""
import os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make import save, ANTON, W, H, YEL, WHITE


def load(d, name):
    pl = Image.open(os.path.join(d, name + ".png")).convert("RGB").resize((W, H), Image.LANCZOS)
    mk = np.asarray(Image.open(os.path.join(d, name + "_mask.png")).split()[-1].resize((W, H)))
    ys, xs = np.nonzero(mk > 60)
    return pl, (int(xs.mean()), int(ys.min())) if len(xs) else (W // 2, H // 2)


def half(pl, cen, grade):
    x0 = int(np.clip(cen[0] - W // 4, 0, W // 2))
    a = np.asarray(pl.crop((x0, 0, x0 + W // 2, H))).astype(np.float32) / 255
    return grade(a)


def g_left(a):
    a = np.clip((a - 0.5) * 1.1 + 0.5, 0, 1) * np.array([0.97, 1.0, 1.06])       # clean, cool, rich
    return a


def g_right(a):
    l = a.mean(-1, keepdims=True); a = 0.75 * a + 0.25 * l                       # dirtier: less colour, greenish murk
    a = a * np.array([0.95, 1.0, 0.86]); s = a * a * (3 - 2 * a); a = 0.7 * a + 0.3 * s
    return a


def rip_path(seed=7):
    rnd = random.Random(seed); pts = []; y = -20; x = W / 2
    while y < H + 40:
        pts.append((x + rnd.uniform(-22, 22), y)); y += rnd.uniform(18, 46)
    return pts


def compose(vel, drn, text=True):
    (lp, lc), (rp, rc) = vel, drn
    L = half(lp, lc, g_left); R = half(rp, rc, g_right)
    canvas = np.zeros((H, W, 3), np.float32); canvas[:, :W // 2] = L; canvas[:, W // 2:] = R
    # left gets a little of the right's space and vice versa along the ragged line
    pts = rip_path()
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m); d.polygon([(0, 0)] + pts + [(0, H + 50)], fill=255)
    left_full = np.zeros_like(canvas); left_full[:, :W // 2] = L; left_full[:, W // 2:] = L[:, -1:, :]
    right_full = np.zeros_like(canvas); right_full[:, W // 2:] = R; right_full[:, :W // 2] = R[:, :1, :]
    mm = (np.asarray(m).astype(np.float32) / 255)[..., None]
    img = left_full * mm + right_full * (1 - mm)
    img = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    # torn paper edge: a ragged white band with a shadow
    band = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(band)
    rnd = random.Random(3)
    edge = [(x + rnd.uniform(-3, 3), y) for x, y in pts]
    bd.line(edge, fill=255, width=14, joint="curve")
    sh = band.filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.7))
    blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); blk.putalpha(sh); img.alpha_composite(blk, (6, 0))
    fib = band.filter(ImageFilter.GaussianBlur(0.8))
    wh = Image.new("RGBA", (W, H), (236, 232, 222, 0)); wh.putalpha(fib); img.alpha_composite(wh)
    if not text:
        return img.convert("RGB")
    T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); t = ImageDraw.Draw(T)
    f1 = ImageFont.truetype(ANTON, 250); f2 = ImageFont.truetype(ANTON, 160)
    w1 = t.textlength("$25M", font=f1); t.text((W / 4 - w1 / 2, 30), "$25M", font=f1, fill=YEL + (255,))
    w2 = t.textlength("IN A DRAIN!", font=f2); t.text((3 * W / 4 - w2 / 2, 80), "IN A DRAIN!", font=f2, fill=WHITE + (255,))
    sh = T.split()[-1].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.9))
    blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); blk.putalpha(sh); img.alpha_composite(blk); img.alpha_composite(T)
    return img.convert("RGB")


if __name__ == "__main__":
    VD, DD, OUT = sys.argv[1:4]
    vel = load(VD, "dd_velvet"); drn = load(DD, "dd_rats")
    t = compose(vel, drn); t.save(os.path.join(OUT, "drain_split.jpg"), quality=96, subsampling=0)
    if "pack" in sys.argv:
        D = os.path.join(OUT, "download_split"); os.makedirs(D, exist_ok=True)
        save(t, "drain_thumbnail_SPLIT", D); save(compose(vel, drn, text=False), "drain_thumbnail_split_notext", D)
    print("done")
