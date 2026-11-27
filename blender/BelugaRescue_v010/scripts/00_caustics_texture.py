"""BelugaRescue v010: a STATIC, tileable caustics texture for the tank floor (replaces v009's animated 4D Voronoi, for render time).
Voronoi distance-to-edge (F2 - F1) on a periodic grid, two octaves, written as an 8-bit grey PNG (white = bright caustic line).
python3 00_caustics_texture.py <out.png>"""
import sys
import numpy as np
from PIL import Image
N = 1024
rng = np.random.default_rng(22)
def edge(cells):
    yy, xx = np.mgrid[0:N, 0:N] / N * cells
    f1 = np.full((N, N), 9.0); f2 = np.full((N, N), 9.0)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            for cy in range(cells):
                for cx in range(cells):
                    p = rng_pts[cells][cy, cx]                                  # one jittered point per cell
                    d = np.hypot(xx - (cx + p[0] + dx * cells), yy - (cy + p[1] + dy * cells))
                    nf1 = np.minimum(f1, d); f2 = np.minimum(f2, np.maximum(f1, d)); f1 = nf1
    return f2 - f1
rng_pts = {c: rng.random((c, c, 2)) for c in (8, 16)}
e = 0.65 * edge(8) + 0.35 * edge(16) * 0.5
line = np.clip(1.0 - e / 0.10, 0.0, 1.0) ** 2                                   # thin bright lines at the cell edges
Image.fromarray((line * 255).astype(np.uint8), "L").save(sys.argv[1])
print("caustics", sys.argv[1], N, "mean", round(float(line.mean()), 3))
