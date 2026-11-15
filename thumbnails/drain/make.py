"""$25M Drain thumbnail: police evidence photo + stencil headline "THEY HID $25M / IN A DRAIN!".
  python make.py <plates dir> <out dir> [pack]"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "..", "assets", "fonts")
MONO = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
W, H = 1920, 1080
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "plates")
OUT = sys.argv[2] if len(sys.argv) > 2 else HERE
YEL = (255, 206, 0); WHITE = (248, 246, 240)
STENCIL = os.path.join(FONTS, "BigShouldersStencilDisplay-Black.ttf")
ANTON = os.path.join(FONTS, "Anton-Regular.ttf")


def grade(img):
    a = np.asarray(img.convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    a = np.clip((a - 0.5) * 1.12 + 0.5, 0, 1)                                    # a little punch
    s_ = a * a * (3 - 2 * a); a = 0.65 * a + 0.35 * s_
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W * 0.47) / W) ** 2 + ((yy - H * 0.62) / H) ** 2)
    fall = np.clip(1.18 - 1.05 * r, 0.32, 1.1)[..., None]                       # flash falloff: hot centre, dark edges
    top = np.clip(0.42 + yy / (H * 0.55), 0.42, 1.0)[..., None]                 # the top darkened for the words
    a = a * fall * top
    a = a * np.array([0.98, 1.0, 1.03])                                         # flash: a touch cool
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def sparkle(img, cx, cy, R=150):
    L = Image.new("L", (W, H), 0); d = ImageDraw.Draw(L)
    for ang, rr, wd in ((0, R, 7), (90, R, 7), (45, R * 0.45, 4), (135, R * 0.45, 4)):
        a = math.radians(ang)
        for s in (1, -1):
            x2, y2 = cx + s * rr * math.cos(a), cy + s * rr * math.sin(a)
            d.polygon([(cx - wd * math.sin(a), cy + wd * math.cos(a)), (x2, y2), (cx + wd * math.sin(a), cy - wd * math.cos(a))], fill=255)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=255)
    core = L.filter(ImageFilter.GaussianBlur(1.5)); glow = L.filter(ImageFilter.GaussianBlur(22))
    m = np.clip(np.asarray(core).astype(np.float32) / 255 + np.asarray(glow).astype(np.float32) / 255 * 0.9, 0, 1)
    halo = np.asarray(Image.new("L", (W, H), 0)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]; halo = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (R * 1.1), 0, 1) ** 2 * 0.25
    m = np.clip(m + halo, 0, 1)[..., None]
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    a = a * (1 - m) + np.array([255, 252, 242]) * m
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def line(d, parts, y, size, cx=W / 2, font=STENCIL):
    f = ImageFont.truetype(font, size); sp = d.textlength(" ", font=f) * 0.9
    ws = [d.textlength(t, font=f) for t, _ in parts]; x = cx - (sum(ws) + sp * (len(parts) - 1)) / 2
    for (t, col), w in zip(parts, ws):
        d.text((x, y), t, font=f, fill=col + (255,)); x += w + sp


def compose(plate, mask, text=True):
    img = grade(Image.open(plate))
    # the stone: the densest blob in the matte (the marker numbers render into it too, as text objects)
    mm = Image.open(mask).split()[-1].resize((W, H), Image.LANCZOS)
    b = np.asarray(mm.filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
    cy, cx = np.unravel_index(np.argmax(b), b.shape)
    img = sparkle(img, cx + 30, cy - 30, 115)
    if not text:
        return img.convert("RGB")
    T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(T)
    line(d, [("THEY", WHITE), ("HID", WHITE), ("$25M", YEL)], 30, 250)
    line(d, [("IN", WHITE), ("A", WHITE), ("DRAIN!", WHITE)], 268, 190)
    sh = T.split()[-1].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.8))
    blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); blk.putalpha(sh)
    img.alpha_composite(blk); img.alpha_composite(T)
    # a small evidence label, bottom left (the bottom right stays clear for the timestamp)
    d = ImageDraw.Draw(img); f = ImageFont.truetype(MONO, 30)
    lab = "EVIDENCE  ·  MARCH 2011"; tw = d.textlength(lab, font=f)
    d.rectangle([48, H - 92, 48 + tw + 36, H - 44], fill=(245, 243, 236, 235)); d.text((66, H - 86), lab, font=f, fill=(15, 15, 15, 255))
    return img.convert("RGB")


def save(img, stem, D):
    img.save(os.path.join(D, stem + ".png")); img.save(os.path.join(D, stem + "_youtube.jpg"), quality=95, subsampling=0)


if __name__ == "__main__" and "rats" in sys.argv:
    os.makedirs(OUT, exist_ok=True); main_rats(P, OUT, "pack" in sys.argv); print("done"); sys.exit(0)
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    pl, mk = os.path.join(P, "dd_evidence.png"), os.path.join(P, "dd_evidence_mask.png")
    t = compose(pl, mk); t.save(os.path.join(OUT, "drain_final.jpg"), quality=96, subsampling=0)
    if len(sys.argv) > 3 and sys.argv[3] == "pack":
        D = os.path.join(OUT, "download"); os.makedirs(D, exist_ok=True)
        save(t, "drain_thumbnail_DRAIN", D); save(compose(pl, mk, text=False), "drain_thumbnail_notext", D)
    print("done")


def grade_dark(img):
    a = np.asarray(img.convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    s_ = a * a * (3 - 2 * a); a = 0.7 * a + 0.3 * s_
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.clip(1.1 - 0.7 * np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.55) / H) ** 2), 0.4, 1.0)[..., None]
    return Image.fromarray((np.clip(a * v, 0, 1) * 255).astype(np.uint8)).convert("RGBA")


def compose_rats(plate, mask, text=True):
    img = grade_dark(Image.open(plate))
    mm = Image.open(mask).split()[-1].resize((W, H), Image.LANCZOS)
    b = np.asarray(mm.filter(ImageFilter.GaussianBlur(10))).astype(np.float32)
    ys, xs = np.nonzero(np.asarray(mm) > 60)
    if len(xs):
        img = sparkle(img, xs.min() + (xs.max() - xs.min()) * 0.3, ys.min() + 4, 95)
        img = sparkle(img, xs.min() + (xs.max() - xs.min()) * 0.78, ys.min() + (ys.max() - ys.min()) * 0.35, 60)
    if not text:
        return img.convert("RGB")
    T = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(T)
    line(d, [("THEY", WHITE), ("HID", WHITE), ("$25M", YEL)], 36, 210, font=ANTON)
    line(d, [("IN", WHITE), ("A", WHITE), ("DRAIN!", WHITE)], 300, 150, font=ANTON)
    sh = T.split()[-1].filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.85))
    blk = Image.new("RGBA", (W, H), (0, 0, 0, 0)); blk.putalpha(sh)
    img.alpha_composite(blk); img.alpha_composite(T)
    return img.convert("RGB")


def main_rats(P, OUT, pack=False):
    pl, mk = os.path.join(P, "dd_rats.png"), os.path.join(P, "dd_rats_mask.png")
    t = compose_rats(pl, mk); t.save(os.path.join(OUT, "drain_final.jpg"), quality=96, subsampling=0)
    if pack:
        D = os.path.join(OUT, "download"); os.makedirs(D, exist_ok=True)
        save(t, "drain_thumbnail_DRAIN", D); save(compose_rats(pl, mk, text=False), "drain_thumbnail_notext", D)
