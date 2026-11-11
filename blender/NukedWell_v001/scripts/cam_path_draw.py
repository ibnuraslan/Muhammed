"""Draw the camera path csv as top + front views (PIL only). python3 -I cam_path_draw.py cam.csv beats.json out.png"""
import sys, csv, json
from PIL import Image, ImageDraw
rows = [list(map(float, r)) for r in list(csv.reader(open(sys.argv[1])))[1:]]
beats = json.load(open(sys.argv[2]))
W, H = 1400, 760
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
def panel(ox, title, i, j, rng):
    (x0, x1), (y0, y1) = rng; pw, ph = 660, 660
    s = min(pw / (x1 - x0), ph / (y1 - y0))
    T = lambda x, y: (ox + 20 + (x - x0) * s, 60 + ph - (y - y0) * s)
    d.text((ox + 20, 20), title, fill="black")
    d.rectangle((ox + 20, 60, ox + 20 + pw, 60 + ph), outline="grey")
    if j == 3: d.line([T(x0, 0), T(x1, 0)], fill=(140, 80, 30), width=2); d.text(T(x0 + 2, 2), "ground z=0", fill=(140, 80, 30))
    if j == 2: d.line([T(x0, 0), T(x1, 0)], fill=(140, 80, 30), width=1); d.text(T(x0 + 2, 2), "cut line y=0 (strata face)", fill=(140, 80, 30))
    pts = [T(r[i], r[j]) for r in rows]
    for k in range(len(pts) - 1):
        c = int(255 * k / len(pts)); d.line([pts[k], pts[k + 1]], fill=(c, 60, 255 - c), width=2)
    for b in beats:
        r = min(rows, key=lambda r: abs(r[0] - b["frame"])); p = T(r[i], r[j])
        d.ellipse((p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4), fill="red"); d.text((p[0] + 5, p[1] - 6), "B%d f%d" % (b["beat"], b["frame"]), fill="red")
    for name, x, y in (("shaft", -14, -2.7 if j == 2 else -60), ("well", 0, -1.6 if j == 2 else -60)):
        p = T(x, y); d.text(p, "x " + name, fill="green")
xs = [r[1] for r in rows]; ys = [r[2] for r in rows]; zs = [r[3] for r in rows]
panel(0, "TOP VIEW (x right, y into the set); colour = time (blue->red)", 1, 2, ((min(xs) - 10, max(xs) + 10), (min(ys) - 10, max(ys) + 10)))
panel(700, "FRONT VIEW (x, z); below z=0 = cross-section", 1, 3, ((min(xs) - 10, max(xs) + 10), (min(zs) - 10, max(zs) + 10)))
im.save(sys.argv[3]); print("PNG", sys.argv[3])
