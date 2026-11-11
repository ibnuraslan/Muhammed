"""Top-down map of the camera path.
blender -b film.blend --python camera_map.py -- dump.json   then   python3 -I camera_map.py dump.json out.jpg"""
import sys, json
if "bpy" not in sys.modules and len(sys.argv) == 3 and sys.argv[1].endswith(".json"):
    from PIL import Image, ImageDraw
    D = json.load(open(sys.argv[1])); out = sys.argv[2]
    S = 40; X0, Y0, W, H = -12, -4, 34, 28
    im = Image.new("RGB", (W * S, H * S), (25, 25, 28)); d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - X0) * S, (H - (y - Y0)) * S)
    for r in D["rects"]: d.rectangle([P(r[0], r[3]), P(r[2], r[1])], outline=(110, 110, 110))
    pts = D["pts"]
    for (f0, *a), (f1, *b) in zip(pts, pts[1:]):
        t = f0 / 1890; d.line([P(a[0], a[1]), P(b[0], b[1])], fill=(int(255 * t), int(200 * (1 - t)) + 40, 255 - int(200 * t)), width=3)
    for f, x, y, z in pts:
        if f % 60 == 1:
            q = P(x, y); d.ellipse([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], fill=(255, 255, 0)); d.text((q[0] + 5, q[1]), "%ds z%.1f" % ((f - 1) // 60, z), fill=(255, 255, 255))
    im.save(out, quality=88); print("MAP", out); sys.exit()
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; cam = sc.camera
rects = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.users_collection and o.users_collection[0].name in ("Set", "Yard", "Foundry", "Corridor", "Gov") and o.dimensions.z > 1.5:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        rects.append([min(v.x for v in bb), min(v.y for v in bb), max(v.x for v in bb), max(v.y for v in bb)])
pts = []
for f in range(1, 1891, 3):
    sc.frame_set(f); p = cam.matrix_world.translation; pts.append([f, p.x, p.y, p.z])
json.dump(dict(rects=rects, pts=pts), open(out, "w")); print("DUMP", out)
