"""Camera path chart from camlog.json: distance to target (log), plus top/side traces. python3 -I camera_chart.py camlog.json out.jpg"""
import sys, json, math
from PIL import Image, ImageDraw
L = json.load(open(sys.argv[1])); W, H = 1400, 700
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
def X(f): return 60 + (f - 1) / 1289 * (W - 100)
def Y(v): return 330 - (math.log10(v) + 3.5) / 3.3 * 300      # 0.3 mm .. 0.6 m+
for v, lab in ((0.001, "1 mm"), (0.01, "1 cm"), (0.1, "10 cm"), (1, "1 m")):
    d.line((60, Y(v), W - 40, Y(v)), fill=(225, 225, 225)); d.text((5, Y(v) - 6), lab, fill=(0, 0, 0))
beats = [(1, 0.0), (2, 2.0), (3, 3.0), (4, 7.8), (5, 12.6), (6, 14.8), (7, 20.1)]
for b, t in beats:
    x = X(1 + t * 60); d.line((x, 20, x, 680), fill=(255, 190, 190)); d.text((x + 3, 22), "beat %d" % b, fill=(200, 0, 0))
for f0 in (154, 1225):
    d.text((X(f0) - 30, 340), "swap f%d" % f0, fill=(0, 0, 200))
pts = [(X(r[0]), Y(max(r[3], 3e-4))) for r in L]; d.line(pts, fill=(0, 0, 0), width=2)
d.text((70, 300), "camera distance to its target (log)", fill=(0, 0, 0))
# camera speed in its own frame (units/s) -> shows no jumps at the swap frames
sp = [0] + [math.dist(L[i][2], L[i - 1][2]) * 60 for i in range(1, len(L))]
m = max(sp[150:]) or 1
d.text((70, 380), "camera speed, macro-frame units/s (clipped)", fill=(0, 0, 0))
d.line([(X(L[i][0]), 680 - min(1, sp[i] / 60) * 280) for i in range(len(L))], fill=(0, 120, 0), width=2)
im.save(sys.argv[2], quality=90); print("chart", sys.argv[2])
