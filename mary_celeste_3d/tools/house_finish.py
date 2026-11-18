"""House finish for stills, matched to research/style_v2/YARNHUB_STYLE_BIBLE.md (branch claude/fern-analysis):
luma median 0.20-0.28 with crushed blacks (p5 ~0.01) and highlights held under clip (p95 <= 0.80),
saturation median 0.15-0.35 (earthy, no teal-orange), light fine grain, a whisper of edge chromatic softness.

    python3 house_finish.py in.png out.png [--luma 0.24] [--sat 0.28]
Prints the measured stats before and after."""
import sys, argparse
import numpy as np
from PIL import Image


def stats(a):
    y = a @ np.array([0.2126, 0.7152, 0.0722])
    mx = a.max(2); mn = a.min(2); s = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return dict(p5=float(np.percentile(y, 5)), med=float(np.median(y)), p95=float(np.percentile(y, 95)), sat=float(np.median(s)))


def finish(a, luma=0.24, sat=0.28, grain=0.010, seed=1):
    st = stats(a)
    # 1. black point: bring p5 down to ~0.012 (crushed, not clipped)
    bp = max(0.0, st["p5"] - 0.012)
    a = np.clip((a - bp) / (1 - bp), 0, 1)
    # 2. midtone gamma so the luma median lands on target
    y = a @ np.array([0.2126, 0.7152, 0.0722])
    m = float(np.median(y)); g = np.log(luma) / np.log(max(m, 1e-3))
    a = a ** g
    # 3. highlight shoulder: p95 at most 0.80
    y = a @ np.array([0.2126, 0.7152, 0.0722]); p95 = float(np.percentile(y, 95))
    if p95 > 0.8:
        k = 0.62; yy = np.where(y > k, k + (y - k) * (0.8 - k) / (p95 - k), y)
        a = a * (yy / np.maximum(y, 1e-5))[..., None]
    # 4. saturation toward the target median (scale chroma around luma)
    y = a @ np.array([0.2126, 0.7152, 0.0722])
    s_now = stats(np.clip(a, 0, 1))["sat"]; f = np.clip(sat / max(s_now, 1e-3), 0.4, 1.4)
    a = y[..., None] + (a - y[..., None]) * f
    # 5. edge chromatic softness (0.4 px at the corners) and fine luminance grain
    h, w = y.shape
    yy, xx = np.mgrid[0:h, 0:w]; r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.414
    sh = (r ** 2 * 0.4)
    for c, sgn in ((0, 1), (2, -1)):
        xs = np.clip(xx + sgn * sh * (xx - w / 2) / (w / 2), 0, w - 1).astype(np.float32)
        x0 = np.floor(xs).astype(int); t = xs - x0; x1 = np.minimum(x0 + 1, w - 1)
        a[..., c] = a[yy, x0, c] * (1 - t) + a[yy, x1, c] * t
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1)) / 3            # slightly soft grain
    a = a + (grain * (0.4 + 0.6 * np.sqrt(np.clip(y, 0, 1))))[..., None] * n[..., None]
    return np.clip(a, 0, 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--luma", type=float, default=0.24); ap.add_argument("--sat", type=float, default=0.28)
    o = ap.parse_args()
    a = np.asarray(Image.open(o.src).convert("RGB"), np.float32) / 255.0
    print("before", {k: round(v, 3) for k, v in stats(a).items()})
    b = finish(a, o.luma, o.sat)
    print("after ", {k: round(v, 3) for k, v in stats(b).items()})
    Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(o.dst, quality=95)
