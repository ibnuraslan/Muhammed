"""Tsunami2004 v013: garment textures from the CC0 MakeHuman clothes (method from BellyFat v018 00_shirt_texture.py).
Tee panels recoloured (shading kept), the MakeHuman print removed; the boy's tee carries the DA KRAS FILMS logo.
python3 00_textures.py <out_dir>"""
import sys, os
import numpy as np
from PIL import Image
C = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/"
LOGO = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png"
OUT = sys.argv[1]
def load(n): return np.array(Image.open(C + n + "/" + n + "_diffuse.png").convert("RGB")).astype(np.float32) / 255.0
def recolour(name, col, accent, centre, rad, logo=None, rot=-90, out_name=None):
    im = load(name); H, W, _ = im.shape
    yy, xx = np.mgrid[0:H, 0:W]
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    top = (yy < 900) | ((xx > 1460) & (yy > 1150))
    blue = top & (b - g > 0.17) & (b - r > 0.3)
    orange = top & (r - b > 0.45)
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    out = im.copy()
    out[blue] = np.clip(np.array(col)[None] * (lum[blue] / np.median(lum[blue]))[:, None] ** 1.2, 0, 1)
    out[orange] = np.clip(np.array(accent)[None] * (lum[orange] / np.median(lum[orange]))[:, None], 0, 1)
    # the print: the largest cluster of orange/grey pixels on the front panel -> flat fabric
    cx, cy = centre
    circ = ((xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2)
    fab = np.median(out[blue & ~circ], axis=0)
    rng = np.random.default_rng(5)
    out[circ] = np.clip(fab[None] * (1 + 0.035 * rng.standard_normal((circ.sum(), 1))), 0, 1)
    if logo:
        lg = Image.open(logo).convert("RGBA").rotate(rot, expand=True)
        lw, lh = lg.size; s = 330 / max(lw, lh) if rot == 0 else 330 / lh
        lg = lg.resize((max(1, int(lw * s)), max(1, int(lh * s))), Image.LANCZOS)
        a = np.array(lg).astype(np.float32) / 255.0
        x0, y0 = cx - a.shape[1] // 2, cy - a.shape[0] // 2
        reg = out[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]; al = a[..., 3:4]
        reg[:] = reg * (1 - al) + a[..., :3] * al
    Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(OUT, out_name))
    print(name, "->", out_name, "print centre", cx, cy)
recolour("female_casualsuit01", (0.34, 0.04, 0.58), (0.98, 0.80, 0.10), (1622, 500), 190, out_name="mom_tee_diffuse.png")
recolour("female_casualsuit02", (0.90, 0.12, 0.08), (1.0, 0.85, 0.2), (1622, 500), 190, out_name="girl_tee_diffuse.png")
recolour("male_casualsuit04", (1.0, 0.72, 0.02), (0.05, 0.25, 0.75), (1167, 320), 170, logo=LOGO, rot=0, out_name="boy_tee_diffuse.png")
