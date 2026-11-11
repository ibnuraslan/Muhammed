"""Plot the single camera's path (top view + side view) with beat markers.
blender -b film.blend --python camera_path_plot.py -- <out.jpg>"""
import bpy, sys, json, os
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera
pts = []
for f in range(1, sc.frame_end + 1, 2):
    sc.frame_set(f); p = cam.matrix_world.translation; pts.append((f, p.x, p.y, p.z))
beats = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "beats.json")))
from PIL import Image, ImageDraw
W, H = 900, 900; im = Image.new("RGB", (W * 2, H), (20, 20, 24)); d = ImageDraw.Draw(im)
def top(x, y): return (W / 2 + x * 150, H - 80 - (y + 3.2) * 150)
def side(y, z): return (W + 60 + (y + 3.2) * 150, H - 80 - z * 280)
# room outline + people
d.rectangle([top(-2.6, -4.2), top(2.6, 1.7)], outline=(90, 90, 90)); d.text((10, 10), "TOP (x right, y up)", fill=(200, 200, 200))
d.text((W + 10, 10), "SIDE (y right, z up)", fill=(200, 200, 200))
for (x, y, c, n) in ((0, 0, (90, 200, 90), "owner"), (0.32, -2.45, (200, 90, 90), "robber"), (2.6, 0.55, (90, 90, 220), "door")):
    q = top(x, y); d.ellipse([q[0] - 6, q[1] - 6, q[0] + 6, q[1] + 6], fill=c); d.text((q[0] + 8, q[1]), n, fill=c)
for i in range(len(pts) - 1):
    t = i / len(pts); col = (int(255 * t), int(200 * (1 - t)) + 40, 255 - int(200 * t))
    d.line([top(pts[i][1], pts[i][2]), top(pts[i + 1][1], pts[i + 1][2])], fill=col, width=2)
    d.line([side(pts[i][2], pts[i][3]), side(pts[i + 1][2], pts[i + 1][3])], fill=col, width=2)
for b in beats:
    f = b["frame"]; p = min(pts, key=lambda q: abs(q[0] - f))
    q = top(p[1], p[2]); d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], outline=(255, 255, 0)); d.text((q[0] + 6, q[1] - 12), "B%d" % b["beat"], fill=(255, 255, 0))
    q = side(p[2], p[3]); d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], outline=(255, 255, 0)); d.text((q[0] + 6, q[1] - 12), "B%d" % b["beat"], fill=(255, 255, 0))
im.save(out, quality=88); print("PLOT", out)
