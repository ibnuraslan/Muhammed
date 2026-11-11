"""blender -b film.blend --python 99_camera_path_plot.py -- <out.png> : top view + height plot of CAM_Film (beat colours)"""
import bpy, sys, json, subprocess
out = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; cam = sc.camera
pts = []
for f in range(1, sc.frame_end + 1, 3):
    sc.frame_set(f); p = cam.matrix_world.translation; pts.append((f, p.x, p.y, p.z))
json.dump(pts, open(out + ".json", "w"))
code = r'''
import json, sys
from PIL import Image, ImageDraw
pts = json.load(open(sys.argv[1] + ".json")); W, H = 900, 900
im = Image.new("RGB", (W, H + 300), (250, 250, 250)); d = ImageDraw.Draw(im)
B = [1, 235, 313, 517, 715, 985, 1105, 1207, 1591]; COL = [(200,60,60),(220,140,30),(60,160,60),(40,140,200),(80,80,220),(160,60,200),(200,60,140),(90,90,90)]
def col(f): return COL[max(i for i in range(8) if B[i] <= f)]
X = lambda x: W / 2 + x * 180; Y = lambda y: H / 2 - (y - 0.3) * 180
d.rectangle((X(-0.72), Y(1.96), X(0.72), Y(0.0)), outline=(120, 80, 40)); d.text((X(-0.7), Y(1.0)), "piano", fill=(120, 80, 40))
d.rectangle((X(-0.42), Y(-0.33), X(0.42), Y(-0.87)), outline=(150, 40, 40)); d.text((X(-0.4), Y(-0.6)), "bench / composer", fill=(150, 40, 40))
for a, b in zip(pts, pts[1:]): d.line((X(a[1]), Y(a[2]), X(b[1]), Y(b[2])), fill=col(a[0]), width=3)
for i in range(8): d.text((10, 10 + i * 14), "beat %d  f%d" % (i + 1, B[i]), fill=COL[i])
d.text((10, H - 20), "top view, 1 grid unit = 1 m (5.56 px/cm)", fill=(0, 0, 0))
for a, b in zip(pts, pts[1:]): d.line((a[0] / 1590 * W, H + 280 - a[3] * 70, b[0] / 1590 * W, H + 280 - b[3] * 70), fill=col(a[0]), width=3)
d.text((10, H + 10), "camera height (m) over frames 1-1590", fill=(0, 0, 0)); im.save(sys.argv[1])
'''
subprocess.run(["python3", "-I", "-c", code, out])
