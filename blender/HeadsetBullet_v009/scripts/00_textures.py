"""HeadsetBullet v009: textures made for this film (all from CC0 sources or drawn here).
python3 00_textures.py <tex_dir>
- boy_tee_diffuse.png: the CC0 MakeHuman male_casualsuit04 diffuse, T-shirt recoloured mustard yellow, its print painted out.
- game_screen.png: a generic, text-free colourful game scene for the monitor (drawn here).
- deskmat.png: a deep-purple desk mat (plain).
- logo_poster.png: a framed wall poster, the DA KRAS FILMS logo (white) on a deep navy-to-magenta gradient."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
OUT = sys.argv[1]
D = "/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data/clothes/male_casualsuit04/male_casualsuit04_diffuse.png"
LOGO = "/home/user/Muhammed/blender/assets/brand/DaKrasFilms_logo_white.png"

# ---- T-shirt
im = np.array(Image.open(D).convert("RGB")).astype(np.float32) / 255.0
H, W, _ = im.shape
yy, xx = np.mgrid[0:H, 0:W]
r, g, b = im[..., 0], im[..., 1], im[..., 2]
top = yy < 800
blue = top & (b - r > 0.28)
orange = top & (r - b > 0.4)
lum = 0.3 * r + 0.59 * g + 0.11 * b
ref = np.median(lum[blue])
MUS = np.array([0.95, 0.62, 0.05])
out = im.copy()
cx, cy, rad = 1143, 360, 196
circ = (xx - cx) ** 2 + (yy - cy) ** 2 < rad ** 2
out[blue] = np.clip(MUS[None] * (lum[blue] / ref)[:, None] ** 1.1, 0, 1)
out[orange] = np.clip(np.array([0.55, 0.05, 0.04])[None] * (lum[orange] / np.median(lum[orange]))[:, None], 0, 1)
rng = np.random.default_rng(3)
ring = ((xx - cx) ** 2 + (yy - cy) ** 2 < (rad + 60) ** 2) & ~circ
fab = np.median(out[blue & ring], axis=0)
bg = (np.abs(im - np.array([62, 96, 117]) / 255.0).max(-1) < 0.04)
src_ok = np.roll(~bg, 840, axis=1)
ys_, xs_ = np.nonzero(circ & top & ~bg & src_ok & (yy > 175))
out[ys_, xs_] = out[ys_, xs_ - 840] * (fab / np.median(out[ys_, xs_ - 840], axis=0))[None]   # fabric copied from the back panel
Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(OUT, "boy_tee_diffuse.png"))

# ---- game screen (16:9, 1280x720): a stylised sci-fi canyon at sunset, a hover-bike, a crosshair-free HUD made of bars only
Wd, Hd = 1280, 720
img = Image.new("RGB", (Wd, Hd)); dr = ImageDraw.Draw(img)
for y in range(Hd):
    t = y / Hd
    c = (int(40 + 200 * t), int(10 + 60 * t), int(120 - 40 * t)) if t < 0.55 else (int(240 - 120 * (t - 0.55)), int(120 - 60 * (t - 0.55)), int(40))
    dr.line([(0, y), (Wd, y)], fill=c)
dr.ellipse([760, 170, 980, 390], fill=(255, 200, 80))
rng2 = np.random.default_rng(5)
for layer, (col, base, amp) in enumerate((((120, 30, 110), 420, 120), ((70, 15, 80), 480, 140), ((30, 8, 50), 560, 90))):
    pts = [(0, Hd)]
    for x in range(0, Wd + 40, 40):
        pts.append((x, base - amp * abs(math.sin(x * 0.006 + layer * 1.7)) - rng2.uniform(0, 30)))
    pts.append((Wd, Hd)); dr.polygon(pts, fill=col)
# glowing road lines converging
for k in range(-6, 7):
    dr.line([(640 + k * 20, 470), (640 + k * 260, Hd)], fill=(0, 230, 255) if k % 3 == 0 else (255, 40, 200), width=3)
# a hover-bike (simple shapes)
dr.polygon([(560, 610), (720, 610), (760, 640), (520, 640)], fill=(240, 240, 250))
dr.polygon([(600, 590), (690, 590), (720, 610), (570, 610)], fill=(255, 60, 60))
dr.ellipse([540, 632, 740, 660], fill=(0, 240, 255))
# HUD bars (no text)
dr.rectangle([40, 40, 340, 62], outline=(255, 255, 255), width=3); dr.rectangle([44, 44, 260, 58], fill=(60, 255, 120))
dr.rectangle([40, 76, 260, 92], outline=(255, 255, 255), width=3); dr.rectangle([44, 80, 180, 88], fill=(0, 200, 255))
dr.ellipse([1120, 40, 1240, 160], outline=(255, 255, 255), width=4); dr.ellipse([1172, 92, 1188, 108], fill=(255, 60, 60))
img = img.filter(ImageFilter.GaussianBlur(0.8))
img.save(os.path.join(OUT, "game_screen.png"))

# ---- desk mat (2:1, 1600x800): deep purple, a magenta stitched rim, the logo in white
mat = Image.new("RGB", (1600, 800), (34, 8, 62)); dm = ImageDraw.Draw(mat)
for i in range(800):
    t = i / 800
    dm.line([(0, i), (1600, i)], fill=(int(34 + 30 * t), int(8 + 4 * t), int(62 + 40 * t)))
dm.rectangle([8, 8, 1591, 791], outline=(255, 30, 160), width=10)
mat.save(os.path.join(OUT, "deskmat.png"))
# ---- logo poster (3:2, 1200x800)
po = Image.new("RGB", (1200, 800)); dp = ImageDraw.Draw(po)
for i in range(800):
    t = i / 800
    dp.line([(0, i), (1200, i)], fill=(int(10 + 120 * t), int(12 + 4 * t), int(60 + 40 * t)))
dp.rectangle([0, 0, 1199, 799], outline=(0, 230, 255), width=14)
lg = Image.open(LOGO).convert("RGBA")
s_ = 880 / lg.size[0]
lg = lg.resize((int(lg.size[0] * s_), int(lg.size[1] * s_)), Image.LANCZOS)
po.paste(lg, (600 - lg.size[0] // 2, 400 - lg.size[1] // 2), lg)
po.save(os.path.join(OUT, "logo_poster.png"))
print("TEXTURES_DONE")
