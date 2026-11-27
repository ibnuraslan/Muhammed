"""Tsunami2004 v013: the shared world (ground height, wave height). Used by 01_build (meshes) and 02_animate (feet, debris)."""
import math
def _ss(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)
HILL = (-70.0, 280.0, 7.0, 35.0)          # x, y, height, sigma: the high ground the family reaches
SECTION_Y = (-330.0, -170.0)              # the earthquake cut-away (under water): terrain removed for x < 0 in this y range
def G(x, y):
    """ground / seabed height (m). Shore at y=-10 when the sea is at 0; land 1.6 m from y=40 (town)."""
    if y >= 10: z = 0.6 + 1.0 * _ss(10, 40, y)
    elif y >= -250: z = 0.6 + 0.03 * (y - 10)
    else: z = max(-60.0, -7.2 + 0.05 * (y + 250))
    hx, hy, hh, hs = HILL
    z += hh * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * hs * hs))
    return z
# ---- the water surface (mirrors the geometry-nodes graph in 01_build exactly; ripples left out)
def wave_z(x, y, L, Yf, A, p, curl=0.0, q=(0.0, 0.0, 0.0)):
    lr = L * _ss(-1200, -400, y)
    wf = max(3.0, 0.8 * A); wb = 4.0 * A + 20.0
    u = Yf - y
    rise = _ss(-0.15 * wf, wf, u)
    decay = p + (1 - p) * math.exp(-max(0.0, u - wf) / wb)
    taper = 1 - _ss(450, 800, abs(x))
    hq = q[2] * math.exp(-((x - q[0]) ** 2) / (2 * 70.0 ** 2) - ((y - q[1]) ** 2) / (2 * 40.0 ** 2))
    return lr + A * rise * decay * taper + hq
