"""Plot the camera path (top view x/y and side view y/z) with beat labels.
blender -b work/film.blend --python scripts/camera_path_plot.py -- out.json ; then python3 -I scripts/camera_path_plot.py out.json out.jpg"""
import sys, json
if "bpy" in sys.modules or sys.argv[0].endswith("blender"):
    pass
try:
    import bpy
    out = sys.argv[sys.argv.index("--") + 1]; sc = bpy.context.scene; P = []
    for f in range(1, sc.frame_end + 1, 5):
        sc.frame_set(f); c = sc.camera.matrix_world.translation; P.append([f, c.x, c.y, c.z])
    json.dump(P, open(out, "w"))
except ImportError:
    from PIL import Image, ImageDraw
    P = json.load(open(sys.argv[1])); B = json.load(open("beats.json"))
    W, H = 900, 900; im = Image.new("RGB", (W * 2, H), "white"); d = ImageDraw.Draw(im)
    def col(f): t = f / 1950; return (int(255 * t), 60, int(255 * (1 - t)))
    def top(x, y): return (W / 2 + x * 55, H / 2 - y * 55)
    def side(y, z): return (W + W / 2 + y * 45, 180 - z * 45)
    d.text((10, 10), "TOP VIEW (x right, y up), 1 m = 55 px; well at centre", fill=(0, 0, 0))
    d.text((W + 10, 10), "SIDE VIEW (y right, z up), 1 m = 45 px; ground z=0, shaft bottom z=-15.2", fill=(0, 0, 0))
    d.ellipse([*top(-0.28, 0.28), *top(0.28, -0.28)], outline=(0, 0, 0))
    d.line([side(-12, 0), side(8, 0)], fill=(120, 90, 60), width=2); d.rectangle([*side(-0.28, 0), *side(0.28, -15.24)], outline=(0, 0, 0))
    d.line([side(0, 0), side(0, -16)], fill=(150, 150, 150))
    for a, b in zip(P, P[1:]):
        d.line([top(a[1], a[2]), top(b[1], b[2])], fill=col(a[0]), width=3); d.line([side(a[2], a[3]), side(b[2], b[3])], fill=col(a[0]), width=3)
    fr = {p[0]: p for p in P}
    for b in B:
        p = min(P, key=lambda q: abs(q[0] - b["frame"]))
        for xy in (top(p[1], p[2]), side(p[2], p[3])):
            d.ellipse([xy[0] - 5, xy[1] - 5, xy[0] + 5, xy[1] + 5], fill=(0, 0, 0)); d.text((xy[0] + 7, xy[1] - 6), "B%d" % b["beat"], fill=(0, 0, 0))
    im.save(sys.argv[2], quality=88); print(sys.argv[2])
