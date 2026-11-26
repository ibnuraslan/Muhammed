"""NoPilotPlane v012: the hero's long-sleeve tee texture from the CC0 MakeHuman male_casualsuit02 diffuse.
Tee panels (everything above the denim, y < 845) recoloured to a deep saturated red-orange with the shading kept, the
MakeHuman print removed, the DA KRAS FILMS logo (white) printed on the chest. Jeans recoloured a touch deeper indigo.
python3 00_textures.py <out_dir>"""
import sys, os
import numpy as np
from PIL import Image
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/male_casualsuit02/male_casualsuit02_diffuse.png"
LOGO = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"
out_dir = sys.argv[1]
im = np.array(Image.open(D).convert("RGB")).astype(np.float32) / 255.0
H, W, _ = im.shape
yy, xx = np.mgrid[0:H, 0:W]
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.3 * r + 0.59 * g + 0.11 * b
tee = yy < 845
ref = np.median(lum[tee])
TEE = np.array([0.80, 0.10, 0.03])                      # saturated red-orange
out = im.copy()
orange = tee & (r - b > 0.3)
collar = tee & (b - r > 0.45)
out[tee] = np.clip(TEE[None] * (lum[tee] / ref)[:, None] ** 1.15, 0, 1)
out[orange] = np.clip(np.array([1.0, 0.72, 0.05])[None] * (lum[orange] / np.median(lum[orange]))[:, None], 0, 1)   # yellow trims
out[collar] = np.clip(np.array([0.05, 0.05, 0.25])[None] * (lum[collar] / np.median(lum[collar]))[:, None], 0, 1)
# remove the print (grey ring + orange figure): flat fabric with light noise
cx, cy, rad = 1146, 336, 128
circ = (xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2
rng = np.random.default_rng(3)
fab = np.median(out[tee & ~circ & (xx > 900) & (xx < 1400) & (yy > 200) & (yy < 700)], axis=0)
out[circ] = np.clip(fab[None] * (1 + 0.04 * rng.standard_normal((circ.sum(), 1))), 0, 1)
# denim: deeper indigo
den = ~tee
out[den] = np.clip(out[den] * np.array([0.65, 0.75, 1.05])[None], 0, 1)
lg = Image.open(LOGO).convert("RGBA")
lw, lh = lg.size
s = 400 / lw                                     # 400 px across the chest
lg = lg.resize((int(lw * s), int(lh * s)), Image.LANCZOS)
a = np.array(lg).astype(np.float32) / 255.0
x0, y0 = cx - a.shape[1] // 2, 360 - a.shape[0] // 2
reg = out[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]
al = a[..., 3:4]
reg[:] = reg * (1 - al) + np.array([0.98, 0.96, 0.92])[None, None] * al
Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(out_dir, "hero_tee_diffuse.png"))
print("hero tee", x0, y0, a.shape[:2])
