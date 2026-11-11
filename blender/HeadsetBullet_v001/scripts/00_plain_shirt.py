"""Remove the print/logo and the orange trims from MakeHuman casualsuit04's tee; recolour the tee. python3 -I 00_plain_shirt.py <in.png> <out.png>"""
import sys, colorsys
from PIL import Image, ImageFilter, ImageStat
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB"); W, H = im.size
band_h = int(H * 0.43)
band = im.crop((0, 0, W, band_h)); px = band.load()
mask = Image.new("L", band.size, 0); mk = mask.load()
for y in range(band.size[1]):
    for x in range(W):
        r, g, b = [c / 255 for c in px[x, y]]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if not (0.53 < h < 0.70 and s > 0.25) and l > 0.12:   # not shirt-blue (logo lines, orange trims)
            mk[x, y] = 255
mask = mask.filter(ImageFilter.MaxFilter(15))
inv = mask.point(lambda v: 255 - v)
mean_col = tuple(int(c) for c in ImageStat.Stat(band, inv).mean)
noise = Image.effect_noise(band.size, 18).convert("L")
fill = Image.merge("RGB", [noise.point(lambda v, c=c: max(0, min(255, c + (v - 128) // 6))) for c in mean_col])
clean = Image.composite(fill, band, mask)
# recolour: keep the knit detail (luminance), set a dark heather green-grey
lum = clean.convert("L"); mean = ImageStat.Stat(lum).mean[0] or 1
tgt = (58, 66, 60)
col = Image.merge("RGB", [lum.point(lambda v, t=t: max(0, min(255, int(t * v / mean)))) for t in tgt])
bgmask = Image.new("L", band.size, 0); bm = bgmask.load(); cp = band.load()
for y in range(band.size[1]):
    for x in range(W):
        r, g, b = cp[x, y]
        bm[x, y] = 255 if (r + g + b) > 60 else 0
res = Image.composite(col, band, bgmask)
im.paste(res, (0, 0)); im.save(out); print("SAVED", out)
