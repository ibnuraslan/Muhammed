"""Textures for the brand-intro key frames: the chalk body outline and the evidence-bag label (official logo art)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import random, math, os
HERE = os.path.dirname(os.path.abspath(__file__)); TEX = os.path.join(HERE, "..", "tex")
K = "/home/user/Muhammed/brand_overlays/kit_v1/fonts/"
rng = random.Random(7)

# ---- chalk outline: a sprawled body (union of capsules), traced as a rough hand-drawn chalk line. 4 m x 4 m at 1024 px/m
S = 4096; m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m)
def cap(p, q, r):
    d.line([p, q], fill=255, width=int(2 * r)); d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255); d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
c = (S * 0.5, S * 0.5); u = 1024 / 1.0  # px per metre
P = lambda x, y: (c[0] + x * u, c[1] + y * u)
d.ellipse([*P(-0.11, -0.95), *P(0.11, -0.70)], fill=255)                     # head
cap(P(0, -0.66), P(0.02, -0.62), 0.06 * u)                                    # neck
d.polygon([P(-0.22, -0.62), P(0.22, -0.60), P(0.17, -0.10), P(0.19, 0.05), P(-0.18, 0.05), P(-0.16, -0.12)], fill=255)  # torso
cap(P(-0.19, -0.56), P(-0.52, -0.38), 0.065 * u); cap(P(-0.52, -0.38), P(-0.62, -0.02), 0.055 * u); d.ellipse([*P(-0.70, -0.04), *P(-0.56, 0.12)], fill=255)  # left arm bent down
cap(P(0.19, -0.56), P(0.50, -0.78), 0.065 * u); cap(P(0.50, -0.78), P(0.78, -0.92), 0.055 * u); d.ellipse([*P(0.76, -1.02), *P(0.90, -0.88)], fill=255)  # right arm flung up
cap(P(-0.10, 0.02), P(-0.30, 0.48), 0.09 * u); cap(P(-0.30, 0.48), P(-0.26, 0.92), 0.07 * u); d.ellipse([*P(-0.34, 0.88), *P(-0.16, 1.04)], fill=255)   # left leg
cap(P(0.10, 0.02), P(0.30, 0.42), 0.09 * u); cap(P(0.30, 0.42), P(0.55, 0.80), 0.07 * u); d.ellipse([*P(0.52, 0.76), *P(0.70, 0.90)], fill=255)    # right leg bent out
m = m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: 255 if v > 128 else 0)
edge = ImageChops.subtract(m.filter(ImageFilter.MaxFilter(15)), m.filter(ImageFilter.MinFilter(1)))
edge = ImageChops.subtract(edge, m.filter(ImageFilter.MaxFilter(3)).point(lambda v: 0) )
# ring = dilate(mask) - mask  (a ~14 px = 1.4 cm line), then chalky: break it up with noise
ring = ImageChops.subtract(m.filter(ImageFilter.MaxFilter(41)), m)
noise = Image.effect_noise((S, S), 90).filter(ImageFilter.GaussianBlur(1.2))
grit = Image.effect_noise((S // 8, S // 8), 120).resize((S, S), Image.BICUBIC)
ch = ImageChops.multiply(ring, noise.point(lambda v: 255 if v > 95 else int(v * 1.6)))
ch = ImageChops.multiply(ch, grit.point(lambda v: min(255, int(90 + v))))
ch = ch.filter(ImageFilter.GaussianBlur(1.0))
ch.save(os.path.join(TEX, "chalk_outline.png"))

# ---- evidence bag label (header of a clear evidence bag): black print area with the OFFICIAL logo, form lines, case no.
LW, LH = 2400, 1100
lab = Image.new("RGBA", (LW, LH), (236, 234, 228, 255)); dl = ImageDraw.Draw(lab)
dl.rectangle([0, 0, LW, 230], fill=(14, 13, 12, 255))
f1 = ImageFont.truetype(K + "Oswald-Bold.ttf", 150); f2 = ImageFont.truetype(K + "IBMPlexMono-Regular.ttf", 46)
f3 = ImageFont.truetype(K + "Oswald-Medium.ttf", 54)
dl.text((70, 30), "EVIDENCE", font=f1, fill=(236, 234, 228, 255))
dl.text((LW - 70, 125), "CASE FILE  ·  DO NOT OPEN", font=f2, fill=(227, 255, 0, 255), anchor="rm")
logo = Image.open(os.path.join(HERE, "..", "logo.png")).convert("RGBA")
lw = 1500; lh = int(logo.height * lw / logo.width)
ly = 230 + 70
# dark plate behind the logo so it keeps its official look (yellow fill, dark outline)
dl.rectangle([(LW - lw) // 2 - 60, ly - 40, (LW + lw) // 2 + 60, ly + lh + 40], fill=(22, 21, 19, 255))
lab.alpha_composite(logo.resize((lw, lh), Image.LANCZOS), ((LW - lw) // 2, ly))
yy = ly + lh + 110
for i, t in enumerate(("ITEM", "LOCATION", "COLLECTED BY")):
    x0 = 70 + i * 780
    dl.text((x0, yy), t, font=f3, fill=(30, 29, 27, 255))
    dl.line([(x0, yy + 150), (x0 + 700, yy + 150)], fill=(30, 29, 27, 255), width=4)
dl.text((70, LH - 60), "No. 000-01", font=f2, fill=(60, 58, 54, 255))
lab.save(os.path.join(TEX, "evidence_label.png"))
print("ok")
