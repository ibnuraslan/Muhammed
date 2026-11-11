"""Camera path diagram (top view + height/yaw/pitch over time, beats marked).
blender -b anim.blend --python campath.py -- out.json   then   python3 -I campath.py out.json beats.json out.jpg"""
import sys, json, math, os
if "bpy" not in sys.modules and len(sys.argv) == 4:
    pts = json.load(open(sys.argv[1])); beats = json.load(open(sys.argv[2])); out = sys.argv[3]
else:
    import bpy
    from mathutils import Vector
    out = sys.argv[sys.argv.index("--") + 1]
    sc = bpy.context.scene; cam = sc.camera
    bpy.context.view_layer.layer_collection.children["PASSENGERS"].exclude = True
    pts = []; uw = 0; prev = None
    for f in range(1, 4351, 6):
        sc.frame_set(f); M = cam.matrix_world; d = M.to_3x3() @ Vector((0, 0, -1))
        y = math.degrees(math.atan2(-d.x, d.y))
        if prev is not None:
            while y + uw - prev > 180: uw -= 360
            while y + uw - prev < -180: uw += 360
        prev = y + uw
        pts.append((f, *M.translation, prev, math.degrees(math.asin(max(-1, min(1, d.z))))))
    json.dump(pts, open(out, "w")); sys.exit(0)
from PIL import Image, ImageDraw
W, H = 1400, 1100; im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
# top view: x -1.6..1.6 , y -6..2.6  -> left panel
def tv(x, y): return (60 + (x + 1.6) / 3.2 * 360, 40 + (2.8 - y) / 8.8 * 1000)
dr.rectangle((*tv(-1.45, 2.8), *tv(1.45, -6.0)), outline=(180, 180, 180))
dr.line((*tv(-1.45, -0.52), *tv(-0.38, -0.52)), fill=(120, 120, 120), width=3); dr.line((*tv(0.38, -0.52), *tv(1.45, -0.52)), fill=(120, 120, 120), width=3)
for i in range(5):
    y = -2.4 - 0.81 * i
    for x in (-1.03, -0.55, 0.55, 1.03): dr.rectangle((*tv(x - 0.22, y + 0.23), *tv(x + 0.22, y - 0.3)), outline=(200, 200, 230))
for x in (-0.52, 0.52): dr.rectangle((*tv(x - 0.25, 1.7), *tv(x + 0.25, 1.15)), outline=(200, 200, 230))
dr.text(tv(-1.4, 2.7), "TOP VIEW (m)  nose = up", fill="black"); dr.text(tv(-0.3, -0.45), "door", fill=(100, 100, 100))
for a, b in zip(pts, pts[1:]):
    c = (int(255 * a[0] / 4350), 40, int(255 * (1 - a[0] / 4350)))
    dr.line((*tv(a[1], a[2]), *tv(b[1], b[2])), fill=c, width=3)
for b in beats:
    p = min(pts, key=lambda q: abs(q[0] - b["frame"])); x, y = tv(p[1], p[2])
    dr.ellipse((x - 4, y - 4, x + 4, y + 4), fill="black"); dr.text((x + 6, y - 6), str(b["beat"]), fill="black")
# right: graphs over time
def gx(f): return 500 + (f - 1) / 4350 * 860
for k, (lab, idx, lo, hi, y0) in enumerate((("camera height z (m)", 3, 0.8, 1.8, 60), ("look yaw (deg, + = left)", 4, -200, 120, 420), ("look pitch (deg)", 5, -75, 15, 780))):
    h = 280
    dr.rectangle((500, y0, 1360, y0 + h), outline=(180, 180, 180)); dr.text((505, y0 - 16), lab, fill="black")
    def gy(v): return y0 + h - (v - lo) / (hi - lo) * h
    for b in beats:
        dr.line((gx(b["frame"]), y0, gx(b["frame"]), y0 + h), fill=(225, 225, 225)); dr.text((gx(b["frame"]) + 2, y0 + 2), str(b["beat"]), fill=(150, 150, 150))
    for a, b in zip(pts, pts[1:]):
        dr.line((gx(a[0]), gy(a[idx]), gx(b[0]), gy(b[idx])), fill=(30, 60, 200), width=2)
    for v in (lo, hi): dr.text((470, gy(v) - 6), "%g" % v, fill="black")
dr.text((500, 1075), "time ->  0 s ... 72.5 s (frames 1-4350). One camera, no cuts; head-cam until 70.6 s, then floats out to the face.", fill="black")
im.save(out, quality=90); print("PATH", out)
