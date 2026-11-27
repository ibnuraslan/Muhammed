"""DwarfGiant v009: recoloured CC0 MakeHuman garment textures + the logo plaque.
python3 00_textures.py <pkg_dir>
- hero overalls (male_worksuit01): deeper indigo denim, the white tee -> warm mustard
- officer (male_elegantsuit01): the grey suit -> deep Prussian-blue uniform cloth, shirt and tie kept
- plaque: the DA KRAS FILMS logo (dark) on cream enamel with a thin red border"""
import sys, os
import numpy as np
from PIL import Image
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes"
OUT = os.path.join(sys.argv[1], "assets/tex")
def load(p): return np.array(Image.open(p).convert("RGB")).astype(np.float32) / 255.0
def save(a, p): Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p)
# ---- hero overalls
im = load(D + "/male_worksuit01/male_worksuit01_diffuse.png")
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.3 * r + 0.59 * g + 0.11 * b
sat = im.max(-1) - im.min(-1)
denim = (b - r > 0.15)
tee = (sat < 0.10) & (lum > 0.75)
out = im.copy()
ref = np.median(lum[denim])
out[denim] = np.clip(np.array([0.05, 0.12, 0.38])[None] * (lum[denim] / ref)[:, None] ** 1.1, 0, 1)
ref2 = np.median(lum[tee])
out[tee] = np.clip(np.array([0.92, 0.60, 0.10])[None] * (lum[tee] / ref2)[:, None], 0, 1)
save(out, OUT + "/hero_overalls_diffuse.png")
# ---- officer uniform
im = load(D + "/male_elegantsuit01/male_elegantsuit01_diffuse.png")
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.3 * r + 0.59 * g + 0.11 * b; sat = im.max(-1) - im.min(-1)
cloth = (sat < 0.06) & (lum > 0.12) & (lum < 0.45)
out = im.copy(); ref = np.median(lum[cloth])
out[cloth] = np.clip(np.array([0.10, 0.20, 0.42])[None] * (lum[cloth] / ref)[:, None], 0, 1)
save(out, OUT + "/officer_uniform_diffuse.png")
# ---- logo plaque (2.4:1)
W, H = 1200, 500
pl = np.ones((H, W, 3), np.float32) * np.array([0.93, 0.88, 0.74])
pl[:14, :] = pl[-14:, :] = pl[:, :14] = pl[:, -14:] = np.array([0.62, 0.05, 0.05])
logo = Image.open("/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_dark.png").convert("RGBA")
lw = 900; lh = int(logo.size[1] * lw / logo.size[0]); logo = logo.resize((lw, lh), Image.LANCZOS)
L = np.array(logo).astype(np.float32) / 255.0
x0, y0 = (W - lw) // 2, (H - lh) // 2
a = L[..., 3:4]
pl[y0:y0 + lh, x0:x0 + lw] = pl[y0:y0 + lh, x0:x0 + lw] * (1 - a) + L[..., :3] * 0.15 * a
save(pl, OUT + "/plaque_logo.png")
print("TEX_DONE")
