"""Paint rough, real-looking chalk marks (broken dusty strokes, hand-written numbers) into an RGBA decal.
Coordinates are in metres on the ceiling; the image covers [X0, X1] x [Y0, Y1] at PX pixels per metre."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PX = 2600


def make(path, X0, X1, Y0, Y1, strokes, texts, font, seed=3):
    W_, H_ = int((X1 - X0) * PX), int((Y1 - Y0) * PX)
    rng = np.random.default_rng(seed)
    core = Image.new("L", (W_, H_), 0); d = ImageDraw.Draw(core)
    to = lambda x, y: ((x - X0) * PX, (Y1 - y) * PX)          # image y down = ceiling +y up
    for (xa, ya), (xb, yb) in strokes:
        # several slightly wobbly passes, like a real chalk line pressed unevenly
        for p in range(3):
            n = 40; pts = []
            off = rng.normal(0, 0.0012, 2)
            for i in range(n + 1):
                t = i / n
                x = xa + (xb - xa) * t + off[0] + rng.normal(0, 0.0006); y = ya + (yb - ya) * t + off[1] + rng.normal(0, 0.0006)
                pts.append(to(x, y))
            d.line(pts, fill=int(200 + 40 * rng.random()), width=int(PX * rng.uniform(0.005, 0.008)))
    f = ImageFont.truetype(font, int(PX * 0.075))
    for s_, (x, y), rot in texts:
        L = Image.new("L", (int(PX * 0.32), int(PX * 0.13)), 0); dl = ImageDraw.Draw(L)
        for p in range(2):
            dl.text((10 + rng.normal(0, 3), 6 + rng.normal(0, 3)), s_, font=f, fill=230)
        L = L.crop(L.getbbox())
        L = L.transpose(Image.FLIP_TOP_BOTTOM).rotate(-rot, expand=True, resample=Image.BICUBIC)   # seen from below: mirror
        cx, cy = to(x, y); core.paste(Image.new("L", L.size, 255), (int(cx - L.width / 2), int(cy - L.height / 2)), L)
    a = np.asarray(core).astype(np.float32) / 255
    # chalk grain: the stick skips over the plaster -> broken, speckled coverage
    g = rng.random(a.shape).astype(np.float32)
    g2 = np.asarray(Image.fromarray((rng.random((H_ // 6, W_ // 6)) * 255).astype(np.uint8)).resize((W_, H_), Image.BILINEAR)).astype(np.float32) / 255
    cover = np.clip((g * 0.6 + g2 * 0.7) - 0.35, 0, 1) * 1.6
    a = np.clip(a * cover, 0, 1)
    # dust: a faint smudge halo round every mark
    dust = np.asarray(core.filter(ImageFilter.GaussianBlur(PX * 0.006))).astype(np.float32) / 255 * 0.28
    a = np.clip(np.maximum(a, dust * (0.5 + 0.5 * g2)), 0, 1)
    rgba = np.zeros((H_, W_, 4), np.uint8); rgba[..., :3] = (235, 233, 226); rgba[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(rgba).save(path)
    return path
