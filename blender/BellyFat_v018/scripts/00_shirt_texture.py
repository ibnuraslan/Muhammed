"""BellyFat v018: the woman's T-shirt texture from the CC0 MakeHuman female_casualsuit01 diffuse.
Shirt panels recoloured to a deep magenta (shading kept), the MakeHuman print removed, the DA KRAS FILMS logo (white)
printed on the chest. Jeans kept. python3 00_shirt_texture.py <out.png>"""
import sys
import numpy as np
from PIL import Image
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/female_casualsuit01/female_casualsuit01_diffuse.png"
LOGO = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
im = np.array(Image.open(D).convert("RGB")).astype(np.float32) / 255.0
H, W, _ = im.shape
yy, xx = np.mgrid[0:H, 0:W]
r, g, b = im[..., 0], im[..., 1], im[..., 2]
sat = im.max(-1) - im.min(-1)
shirt_blue = (b - g > 0.17) & (b - r > 0.3)           # shirt blue is (44,85,139); the denim is greyer (60,88,124)
shirt_or = (r - b > 0.5)
shirt = ((yy < 890) | ((xx > 1460) & (yy > 1150))) & (shirt_blue | shirt_or)
blue = shirt & (b > r)
orange = shirt & (r > b)
lum = 0.3 * r + 0.59 * g + 0.11 * b
ref = np.median(lum[blue])
MAG = np.array([0.62, 0.03, 0.30])
out = im.copy()
out[blue] = np.clip(MAG[None] * (lum[blue] / ref)[:, None] ** 1.2, 0, 1)
out[orange] = np.clip(np.array([1.0, 0.78, 0.10])[None] * (lum[orange] / np.median(lum[orange]))[:, None], 0, 1)
# remove the MakeHuman print (grey ring + orange figure) on the front panel: flat fabric with light noise
cx, cy, rad = 1622, 500, 175
LX, LY = 1590, 470
circ = (xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2
rng = np.random.default_rng(3)
fab = np.median(out[blue & ~circ], axis=0)
out[circ] = np.clip(fab[None] * (1 + 0.04 * rng.standard_normal((circ.sum(), 1))), 0, 1)
# the logo, text upright on the shirt (shirt up = +x in this UV layout), white
lg = Image.open(LOGO).convert("RGBA").rotate(-90, expand=True)     # top of the text -> +x
lw, lh = lg.size
s = 430 / lh                                                          # 430 px across the chest
lg = lg.resize((int(lw * s), int(lh * s)), Image.LANCZOS)
a = np.array(lg).astype(np.float32) / 255.0
x0, y0 = LX - a.shape[1] // 2, LY - a.shape[0] // 2
reg = out[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
al = a[..., 3:4]
reg[:] = reg * (1 - al) + np.array([0.97, 0.95, 0.92])[None, None] * al
Image.fromarray((out * 255).astype(np.uint8)).save(sys.argv[1])
print("shirt texture", sys.argv[1], "logo box", x0, y0, a.shape[:2])
