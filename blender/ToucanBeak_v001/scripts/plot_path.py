"""python3 plot_path.py camera_path.json out.png"""
import sys, json
from PIL import Image, ImageDraw
D = json.load(open(sys.argv[1])); pts, beats = D['pts'], D['beats']; out = sys.argv[2]
W, H = 1400, 900; im = Image.new('RGB', (W, H), (18, 22, 30)); d = ImageDraw.Draw(im)
xs = [p[1] for p in pts]; ys = [p[2] for p in pts]; zs = [p[3] for p in pts]
x0, x1, y0, y1, z0 = min(xs) - .5, max(xs) + .5, min(ys) - .5, max(ys) + .5, min(zs) - .3
s = min((W - 380) / (x1 - x0), 520 / (y1 - y0))
pal = [(230, 90, 80), (240, 160, 60), (230, 220, 80), (120, 210, 90), (60, 200, 200), (80, 140, 240), (160, 110, 240), (230, 110, 200), (200, 200, 200), (150, 230, 160), (250, 200, 150)]
def beat(f): return max(i for i, b in enumerate(beats) if b['frame'] <= f)
for a, b in zip(pts, pts[1:]):
    c = pal[beat(a[0]) % len(pal)]
    d.line([(40 + (a[1] - x0) * s, 570 - (a[2] - y0) * s), (40 + (b[1] - x0) * s, 570 - (b[2] - y0) * s)], fill=c, width=3)
    d.line([(40 + (a[1] - x0) * s, 880 - (a[3] - z0) * 70), (40 + (b[1] - x0) * s, 880 - (b[3] - z0) * 70)], fill=c, width=2)
for i, b in enumerate(beats):
    d.text((W - 320, 20 + 18 * i), "beat %d  f%d  %s" % (b['beat'], b['frame'], b['first_words'][:30]), fill=pal[i % len(pal)])
d.text((40, 8), "Camera TOP VIEW (x right, y up): jungle x<4 | clinic 4..10 | monitor-portal void 10..18", fill=(220, 220, 220))
d.text((40, 610), "SIDE VIEW (x, z)", fill=(220, 220, 220))
im.save(out); print(out)
