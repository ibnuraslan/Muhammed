"""Procedural alpine heightfield generation (numpy only)."""
import numpy as np


def perlin(X, Y, seed):
    """Classic 2D gradient noise evaluated at arbitrary float coords (arrays). Range ~[-1,1]."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(512).astype(np.int64)
    perm = np.concatenate([perm, perm])
    ang = rng.random(512) * 2 * np.pi
    gxs, gys = np.cos(ang), np.sin(ang)
    xi = np.floor(X).astype(np.int64); yi = np.floor(Y).astype(np.int64)
    xf = X - xi; yf = Y - yi
    xi &= 511; yi &= 511
    def g(ix, iy, dx, dy):
        hsh = perm[(perm[ix] + iy) & 1023] & 511
        return gxs[hsh] * dx + gys[hsh] * dy
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)
    n00 = g(xi, yi, xf, yf); n10 = g(xi + 1, yi, xf - 1, yf)
    n01 = g(xi, yi + 1, xf, yf - 1); n11 = g(xi + 1, yi + 1, xf - 1, yf - 1)
    return ((n00 * (1 - u) + n10 * u) * (1 - v) + (n01 * (1 - u) + n11 * u) * v) * 1.414


def _coords(shape):
    h, w = shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    m = max(h, w)
    return x / m, y / m


def _octave(X, Y, freq, i, seed):
    a = 0.7 + i * 1.13  # rotate each octave to kill axis alignment
    ca, sa = np.cos(a), np.sin(a)
    xr = (X * ca - Y * sa) * freq + i * 17.3
    yr = (X * sa + Y * ca) * freq + i * 31.7
    return perlin(xr, yr, seed + i)


def fbm(shape, seed=2, octaves=7, base_freq=2.0, X=None, Y=None):
    if X is None:
        X, Y = _coords(shape)
    h = np.zeros(X.shape); amp = 1; freq = base_freq; norm = 0
    for i in range(octaves):
        h += _octave(X, Y, freq, i, seed) * amp
        norm += amp; amp *= 0.5; freq *= 2.03
    return h / norm


def ridged_fbm(shape, seed=1, octaves=9, base_freq=3.0, gain=0.5, lac=2.03, X=None, Y=None):
    if X is None:
        X, Y = _coords(shape)
    h = np.zeros(X.shape)
    amp, freq, weight = 1.0, base_freq, np.ones(X.shape)
    norm = 0
    for i in range(octaves):
        r = 1.0 - np.abs(_octave(X, Y, freq, i, seed))
        r = r * r * weight
        weight = np.clip(r * 2.0, 0, 1)
        h += r * amp
        norm += amp
        amp *= gain
        freq *= lac
    return h / norm


def thermal_erosion(h, iters=40, talus=0.004, k=0.5):
    for _ in range(iters):
        dx = np.zeros_like(h)
        for sy, sx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = np.roll(np.roll(h, sy, 0), sx, 1)
            d = h - nb
            m = np.where(d > talus, (d - talus) * k * 0.25, 0)
            dx -= m
            dx += np.roll(np.roll(m, -sy, 0), -sx, 1)
        h = h + dx
    return h


def alpine(n=768, seed=7, peak_bias=None, base_freq=2.2):
    """Return heightfield in [0,1] of shape (n,n)."""
    shape = (n, n)
    X, Y = _coords(shape)
    # domain warp for organic ridgelines
    wx = fbm(shape, seed + 101, 5, 1.5, X, Y) * 0.12
    wy = fbm(shape, seed + 202, 5, 1.5, X, Y) * 0.12
    Xw, Yw = X + wx, Y + wy
    base = fbm(shape, seed + 11, 4, 1.0, Xw, Yw) * 0.5 + 0.5
    ridge = ridged_fbm(shape, seed, 11, base_freq, 0.52, X=Xw, Y=Yw)
    h = ridge * (0.25 + 1.0 * base)
    if peak_bias is not None:
        for (py, px, r, a) in peak_bias:
            h *= 1 + a * np.exp(-((Y - py) ** 2 + (X - px) ** 2) / (r * r))
    h -= h.min(); h /= h.max()
    return (h ** 1.4).astype(np.float32)


# ---------------------------------------------------------------------------
# Hydraulic droplet erosion (numba-accelerated). Carves gullies, ridges and
# talus fans so the terrain reads like real glaciated alpine rock.
try:
    from numba import njit
except ImportError:  # pragma: no cover
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@njit(cache=True)
def _erode(H, n_drops, seed, inertia=0.05, capacity=4.0, deposition=0.3, erosion=0.3,
           evaporation=0.01, gravity=4.0, max_steps=64, radius=3):
    np.random.seed(seed)
    ny, nx = H.shape
    for _ in range(n_drops):
        x = np.random.random() * (nx - 2); y = np.random.random() * (ny - 2)
        dx = 0.0; dy = 0.0; speed = 1.0; water = 1.0; sed = 0.0
        for _s in range(max_steps):
            ix = int(x); iy = int(y)
            if ix < 0 or iy < 0 or ix >= nx - 1 or iy >= ny - 1:
                break
            fx = x - ix; fy = y - iy
            h00 = H[iy, ix]; h10 = H[iy, ix + 1]; h01 = H[iy + 1, ix]; h11 = H[iy + 1, ix + 1]
            gx = (h10 - h00) * (1 - fy) + (h11 - h01) * fy
            gy = (h01 - h00) * (1 - fx) + (h11 - h10) * fx
            hcur = h00 * (1 - fx) * (1 - fy) + h10 * fx * (1 - fy) + h01 * (1 - fx) * fy + h11 * fx * fy
            dx = dx * inertia - gx * (1 - inertia)
            dy = dy * inertia - gy * (1 - inertia)
            ln = np.sqrt(dx * dx + dy * dy)
            if ln < 1e-9:
                break
            dx /= ln; dy /= ln
            nxp = x + dx; nyp = y + dy
            jx = int(nxp); jy = int(nyp)
            if jx < 0 or jy < 0 or jx >= nx - 1 or jy >= ny - 1:
                break
            gx2 = nxp - jx; gy2 = nyp - jy
            hnew = (H[jy, jx] * (1 - gx2) * (1 - gy2) + H[jy, jx + 1] * gx2 * (1 - gy2)
                    + H[jy + 1, jx] * (1 - gx2) * gy2 + H[jy + 1, jx + 1] * gx2 * gy2)
            dh = hnew - hcur
            cap = max(-dh * speed * water * capacity, 0.01)
            if sed > cap or dh > 0:
                amt = min(dh, sed) if dh > 0 else (sed - cap) * deposition
                sed -= amt
                H[iy, ix] += amt * (1 - fx) * (1 - fy); H[iy, ix + 1] += amt * fx * (1 - fy)
                H[iy + 1, ix] += amt * (1 - fx) * fy; H[iy + 1, ix + 1] += amt * fx * fy
            else:
                amt = min((cap - sed) * erosion, -dh)
                wsum = 0.0
                for oy in range(-radius, radius + 1):
                    for ox in range(-radius, radius + 1):
                        d = np.sqrt(ox * ox + oy * oy)
                        if d <= radius:
                            wsum += radius - d
                for oy in range(-radius, radius + 1):
                    for ox in range(-radius, radius + 1):
                        d = np.sqrt(ox * ox + oy * oy)
                        px = ix + ox; py = iy + oy
                        if d <= radius and px >= 0 and py >= 0 and px < nx and py < ny:
                            H[py, px] -= amt * (radius - d) / wsum
                sed += amt
            speed = np.sqrt(max(speed * speed + dh * gravity, 0.0))
            water *= (1 - evaporation)
            x = nxp; y = nyp
    return H


def eroded_alpine(n=1024, seed=7, drops=None, peak_bias=None, relief=None):
    """Alpine terrain: ridged multifractal + droplet erosion. Returns heights in [0,1]."""
    h = alpine(n, seed, peak_bias).astype(np.float64)
    # work in "pixel units" of height so gradients are meaningful
    scale = (relief or n * 0.06)
    H = h * scale
    drops = drops or n * n // 2
    H = _erode(H, drops, seed)
    H -= H.min(); H /= H.max()
    return H.astype(np.float32)
