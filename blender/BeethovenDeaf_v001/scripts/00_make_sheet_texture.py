"""Hand-copied-looking manuscript page (staves + note heads only, no text). python3 -I 00_make_sheet_texture.py <out.jpg> <seed>"""
import sys, random
from PIL import Image, ImageDraw, ImageFilter
out, seed = sys.argv[1], int(sys.argv[2]); R = random.Random(seed)
W, H = 768, 1024
im = Image.new("RGB", (W, H), (226, 212, 178)); d = ImageDraw.Draw(im)
for _ in range(1400):   # foxing / paper grain
    x, y = R.randrange(W), R.randrange(H); c = R.randrange(195, 222)
    d.point((x, y), fill=(c, c - 14, c - 46))
for _ in range(14):
    x, y, r = R.randrange(W), R.randrange(H), R.randrange(8, 40)
    d.ellipse((x - r, y - r, x + r, y + r), fill=(214, 196, 156))
ink = (38, 28, 22)
y0 = 70
while y0 < H - 90:
    sl = [y0 + i * 9 + R.uniform(-0.6, 0.6) for i in range(5)]
    for y in sl: d.line((48, y, W - 48, y + R.uniform(-1.5, 1.5)), fill=(70, 58, 48), width=1)
    d.line((48, sl[0], 48, sl[4]), fill=ink, width=2)
    x = 80
    while x < W - 70:
        if R.random() < 0.12:
            d.line((x, sl[0], x, sl[4]), fill=ink, width=1); x += 14; continue
        n = R.choice([1, 1, 2, 3, 4])
        heads = []
        for k in range(n):
            yy = sl[0] + R.randint(-4, 12) * 4.5
            d.ellipse((x - 4, yy - 3, x + 4, yy + 3), fill=ink if R.random() < 0.8 else None, outline=ink)
            heads.append((x, yy)); x += R.randint(11, 18)
        up = R.random() < 0.5
        for hx, hy in heads:
            d.line((hx + (3 if up else -3), hy, hx + (3 if up else -3), hy + (-26 if up else 26)), fill=ink, width=1)
        if n > 1:
            yb = min(h[1] for h in heads) - 26 if up else max(h[1] for h in heads) + 26
            d.line((heads[0][0] + (3 if up else -3), yb, heads[-1][0] + (3 if up else -3), yb), fill=ink, width=3)
        if R.random() < 0.15:   # an angry scratch-out, as in real manuscripts
            d.line((x - 30, sl[0] - 4, x, sl[4] + 4), fill=ink, width=2); d.line((x - 30, sl[4] + 4, x, sl[0] - 4), fill=ink, width=2)
        x += R.randint(10, 22)
    y0 += R.randint(78, 92)
for _ in range(3):   # ink blots
    x, y, r = R.randrange(W), R.randrange(H), R.randrange(3, 9)
    d.ellipse((x - r, y - r, x + r, y + r), fill=ink)
im = im.filter(ImageFilter.GaussianBlur(0.5)); im.save(out, quality=88)
