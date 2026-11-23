import os, sys
sys.path.insert(0, "/home/user/Muhammed/antwerp_heist/3d/lib"); sys.path.insert(0, "/home/user/Muhammed/antwerp_heist/3d/scenes")
import common as C; C.reset()
import bpy, sets3 as S3
from mathutils import Vector
sc = C.render_setup(samples=32, noise=0.06, bounces=6)
w = os.environ["W"]
V = {"woodland": (lambda: S3.woodland(), [((-3.0, -2.0, 1.6), (0.5, 3.0, 0.5), 28), ((-8, -12, 3), (0, 3, 2), 24)]),
     "lab": (lambda: S3.lab(), [((-2.2, -2.4, 1.7), (0, -0.4, 0.9), 26)]),
     "court": (lambda: S3.courtroom(), [((0.5, -5.5, 1.7), (0, 5.0, 1.5), 24)]),
     "replica": (lambda: S3.replica(), [((-4, -5, 2.0), (0, 3, 1.2), 24)]),
     "interview": (lambda: S3.interview(), [((-1.6, -1.6, 1.5), (0.5, 0.3, 0.9), 26)]),
     "super": (lambda: S3.supermarket(), [((2.5, -3.5, 2.8), (-1, -1.0, 0.6), 20)]),
     "sandwich": (lambda: (S3.lab(), S3.sandwich(loc=(0, 0, 0.923))), [((0.25, -0.3, 1.15), (0, 0, 0.95), 50)])}
b, views = V[w]
A = b()
for i, (l, t, lens) in enumerate(views):
    C.camera(Vector(l), Vector(t), lens=lens)
    sc.render.filepath = f"/home/user/Muhammed/antwerp_heist/3d/out/tests/p3_{w}_{i}.png"; bpy.ops.render.render(write_still=True)
