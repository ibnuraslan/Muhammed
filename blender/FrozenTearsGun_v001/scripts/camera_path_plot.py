"""Top view (x,y) and speed graph of the camera path. python3 -I camera_path_plot.py campath.json beats.json out.jpg"""
import sys, json, math
from PIL import Image, ImageDraw
rows = json.load(open(sys.argv[1])); beats = json.load(open(sys.argv[2])); out = sys.argv[3]
W, H = 900, 1300
im = Image.new("RGB", (W, H), (20, 22, 26)); d = ImageDraw.Draw(im)
xs = [r["p"][0] for r in rows]; ys = [r["p"][1] for r in rows]
x0, x1, y0, y1 = -2.6, 2.6, -8.6, 1.8
def P(x, y): return (40 + (x - x0) / (x1 - x0) * (W - 80), 40 + (y1 - y) / (y1 - y0) * (900 - 80))
# rooms
for (a, b, c, e, col) in ((-2.4, -3.8, 2.4, 1.6, (70, 60, 50)), (-2.5, -9.0, 2.5, -4.0, (50, 60, 75))):
    d.rectangle([P(a, e), P(c, b)], outline=col, width=2)
d.text(P(-2.3, 1.5), "WORKSHOP", fill=(200, 170, 130)); d.text(P(-2.3, -4.2), "OFFICE (memory)", fill=(150, 180, 220))
for i in range(len(rows) - 1):
    t = i / len(rows); col = (int(255 * t), int(200 * (1 - t)) + 40, 255 - int(200 * t))
    d.line([P(xs[i], ys[i]), P(xs[i + 1], ys[i + 1])], fill=col, width=2)
for b in beats:
    r = rows[b["frame"] - 1]; p = P(r["p"][0], r["p"][1])
    d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=(255, 255, 0)); d.text((p[0] + 6, p[1] - 6), str(b["beat"]), fill=(255, 255, 0))
for k in range(0, len(rows), 60):
    r = rows[k]; p = P(r["p"][0], r["p"][1]); d.point(p, fill=(255, 255, 255))
# speed graph (m/s, log-ish) and height
gy0 = 930; gh = 330
d.rectangle([40, gy0, W - 40, gy0 + gh], outline=(90, 90, 90))
sp = [math.dist(rows[i]["p"], rows[i + 1]["p"]) * 60 for i in range(len(rows) - 1)]
for i in range(len(sp) - 1):
    def gx(i): return 40 + i / len(sp) * (W - 80)
    def g(v): return gy0 + gh - min(1, math.log10(1 + v * 10) / 2.3) * gh
    d.line([(gx(i), g(sp[i])), (gx(i + 1), g(sp[i + 1]))], fill=(120, 220, 255), width=1)
for b in beats:
    x = 40 + (b["frame"] - 1) / len(sp) * (W - 80); d.line([(x, gy0), (x, gy0 + gh)], fill=(90, 80, 30)); d.text((x + 2, gy0 + 2), str(b["beat"]), fill=(255, 255, 0))
d.text((44, gy0 + gh - 14), "camera speed (log scale, 0-20 m/s), beat starts in yellow; dots on path = 1 s", fill=(200, 200, 200))
im.save(out, quality=90); print(out, "max speed %.1f m/s" % max(sp))
