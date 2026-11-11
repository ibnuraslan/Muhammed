"""Camera path plot. Step 1: blender -b anim.blend --python campath.py -- <path.json>   Step 2: python3 campath.py <path.json> <out.jpg>"""
import sys, json
if "--" in sys.argv:
    import bpy
    sc = bpy.context.scene; cam = sc.camera; pts = []
    for f in range(1, sc.frame_end + 1, 2):
        sc.frame_set(f); p = cam.matrix_world.translation; pts.append((f, p.x, p.y, p.z))
    json.dump({"end": sc.frame_end, "pts": pts}, open(sys.argv[sys.argv.index("--") + 1], "w")); print("CAMPATH json"); sys.exit(0)
from PIL import Image, ImageDraw
class P3:
    def __init__(s, x, y, z): s.x, s.y, s.z = x, y, z
J = json.load(open(sys.argv[1])); out = sys.argv[2]
class SC: frame_end = J["end"]
sc = SC(); pts = [(f, P3(x, y, z)) for f, x, y, z in J["pts"]]
BEATS = [1, 139, 271, 391, 607, 973, 1285, 1417]
W, H = 1400, 700
im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
def panel(x0, w, xs, ys, xr, yr, title):
    d.rectangle((x0, 0, x0 + w - 1, H - 1), outline=(0, 0, 0)); d.text((x0 + 6, 6), title, fill=(0, 0, 0))
    def m(x, y): return (x0 + 20 + (x - xr[0]) / (xr[1] - xr[0]) * (w - 40), H - 20 - (y - yr[0]) / (yr[1] - yr[0]) * (H - 60))
    # house walls / table outline for reference
    if "top" in title:
        for a, b in (((-0.17, -3.55), (-0.17, 6.6)), ((0, -3.4), (6.6, -3.4)), ((6.6, -3.4), (6.6, 3.2)), ((0, 3.2), (6.6, 3.2))):
            d.line([m(*a), m(*b)], fill=(150, 150, 150), width=2)
        d.rectangle([m(2.28, 0.43), m(4.52, -0.43)], outline=(160, 110, 60))
    prev = None
    for f, p in pts:
        q = m(xs(p), ys(p)); c = (int(255 * f / sc.frame_end), 40, int(255 * (1 - f / sc.frame_end)))
        if prev: d.line([prev, q], fill=c, width=2)
        prev = q
        if any(abs(f - b) <= 1 for b in BEATS): d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=(0, 0, 0)); d.text((q[0] + 5, q[1] - 12), "f%d" % f, fill=(0, 0, 0))
panel(0, 900, lambda p: p.x, lambda p: p.y, (-15, 7), (-10, 4), "top view (x right, y up), blue=start red=end, dots=beat starts")
panel(900, 500, lambda p: p.x, lambda p: p.z, (-15, 7), (-0.7, 2.0), "side view (x, z)")
im.save(out, quality=90); print("CAMPATH", out)
