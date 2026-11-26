"""DrunkTrain v008: the man's T-shirt texture from the CC0 MakeHuman male_casualsuit04 diffuse.
Shirt panels recoloured to a saturated red (shading kept), the MakeHuman print removed, the DA KRAS FILMS logo (white)
printed on the chest. Jeans kept. python3 00_shirt_texture.py <out.png>"""
import sys
import numpy as np
from PIL import Image
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/male_casualsuit04/male_casualsuit04_diffuse.png"
LOGO = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
im = np.array(Image.open(D).convert("RGB")).astype(np.float32) / 255.0
H, W, _ = im.shape
yy, xx = np.mgrid[0:H, 0:W]
r, g, b = im[..., 0], im[..., 1], im[..., 2]
shirt_blue = (b - r > 0.25) & (b - g > 0.12)
shirt_or = (r - b > 0.45)
shirt = (yy < 800) & (shirt_blue | shirt_or)
blue = shirt & (b > r); orange = shirt & (r > b)
lum = 0.3 * r + 0.59 * g + 0.11 * b
ref = np.median(lum[blue])
RED = np.array([0.78, 0.04, 0.05])
out = im.copy()
out[blue] = np.clip(RED[None] * (lum[blue] / ref)[:, None] ** 1.2, 0, 1)
out[orange] = np.clip(np.array([0.95, 0.93, 0.88])[None] * (lum[orange] / np.median(lum[orange]))[:, None] ** 0.5, 0, 1)
cx, cy, rad = 1140, 345, 185
circ = ((xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2)
rng = np.random.default_rng(3)
fab = np.median(out[blue & ~circ & (xx > 860) & (xx < 1420)], axis=0)
out[circ] = np.clip(fab[None] * (1 + 0.04 * rng.standard_normal((circ.sum(), 1))), 0, 1)
lg = Image.open(LOGO).convert("RGBA")
lw, lh = lg.size
s = 400 / lw
lg = lg.resize((int(lw * s), int(lh * s)), Image.LANCZOS)
a = np.array(lg).astype(np.float32) / 255.0
x0, y0 = cx - a.shape[1] // 2, 330 - a.shape[0] // 2
reg = out[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
al = a[..., 3:4]
reg[:] = reg * (1 - al) + np.array([0.97, 0.95, 0.92])[None, None] * al
Image.fromarray((out * 255).astype(np.uint8)).save(sys.argv[1])
print("shirt texture", sys.argv[1], "logo box", x0, y0, a.shape[:2])
