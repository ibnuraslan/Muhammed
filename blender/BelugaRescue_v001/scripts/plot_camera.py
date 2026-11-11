"""Plot the film camera's full path (top view + side view) with beat markers.
blender -b film.blend --python plot_camera.py -- out.png   (uses Blender's bundled Python; PIL not needed)"""
import bpy, sys, json, math
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene; cam = sc.camera
pts = []
for f in range(1, sc.frame_end + 1, 3):
    sc.frame_set(f); p = cam.matrix_world.translation; pts.append((f, p.x, p.y, p.z))
beats = json.loads(sc.get("beats", "{}"))
W, H = 1400, 900
img = [[(18, 22, 28)] * W for _ in range(H)]
def put(x, y, c, r=1):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if 0 <= x + dx < W and 0 <= y + dy < H: img[y + dy][x + dx] = c
def line(a, b, c):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for i in range(n + 1):
        t = i / max(1, n); put(int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), c)
# panel 1: top view x[-7,7], y[-10,7] ; panel 2: side view y[-10,7] vs z[-0.5,9]
def top(x, y): return (int(40 + (x + 7) / 14 * 620), int(860 - (y + 10) / 17 * 820))
def side(y, z): return (int(740 + (y + 10) / 17 * 620), int(860 - (z + 0.5) / 9.5 * 820))
for a, b in (((-6, -5), (6, -5)), ((6, -5), (6, 5)), ((6, 5), (-6, 5)), ((-6, 5), (-6, -5))):
    line(top(*a), top(*b), (90, 140, 170))
line(side(-5, 0), side(5, 0), (90, 140, 170)); line(side(-5, 6), side(5, 6), (60, 160, 220)); line(side(-5, 0), side(-5, 6.25), (150, 150, 150))
line(side(-9.5, 6.25), side(-5, 6.25), (150, 150, 150))
for (f0, x0, y0, z0), (f1, x1, y1, z1) in zip(pts, pts[1:]):
    t = f0 / sc.frame_end; c = (int(255 * t), int(200 * (1 - abs(2 * t - 1))) + 55, int(255 * (1 - t)))
    line(top(x0, y0), top(x1, y1), c); line(side(y0, z0), side(y1, z1), c)
for b, f in beats.items():
    sc.frame_set(int(f)); p = cam.matrix_world.translation
    put(*top(p.x, p.y), (255, 255, 255), 4); put(*side(p.y, p.z), (255, 255, 255), 4)
# write PPM then convert by Blender image
ppm = out + ".ppm"
with open(ppm, "wb") as fh:
    fh.write(b"P6 %d %d 255\n" % (W, H))
    fh.write(bytes(v for row in img for px in row for v in px))
print("PPM written; convert with PIL")
print("CAMPLOT", out)
