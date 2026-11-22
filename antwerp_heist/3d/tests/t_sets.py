import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import sets2
which = os.environ.get("SET", "office")
sc = C.render_setup(samples=int(os.environ.get("SPP", "32")), noise=0.06, bounces=6)
V = {"office": (lambda: sets2.office("leonardo"), [((1.8, -1.8, 1.6), (-0.3, 1.0, 0.9), 22)]),
     "leasing": (lambda: sets2.office("leasing"), [((-1.5, -1.6, 1.5), (0.3, 1.0, 0.8), 24)]),
     "security": (lambda: sets2.security_room("building"), [((-1.5, -1.6, 1.6), (0.3, 2.0, 1.2), 22), ((-1.0, 0.5, 1.5), (2.4, -0.9, 1.0), 24)]),
     "alarm": (lambda: sets2.security_room("alarm"), [((-1.5, -1.6, 1.6), (0.3, 2.0, 1.4), 22)]),
     "street": (lambda: sets2.exterior("dawn"), [((-14, -16, 1.7), (0, 2, 7), 24)]),
     "street_day": (lambda: sets2.exterior("day"), [((-14, -16, 1.7), (0, 2, 7), 24)]),
     "turin": (lambda: sets2.turin_flat(), [((-2.4, -2.2, 1.8), (0.5, 1.0, 0.8), 22)]),
     "maquette": (lambda: sets2.maquette(), [((-0.35, -0.55, 0.3), (0.0, 0.0, 0.07), 35)])}
build, views = V[which]
A = build()
out = os.path.join(C.HERE, "..", "out", "tests")
for i, (loc, tgt, lens) in enumerate(views):
    C.camera(Vector(loc), Vector(tgt), lens=lens)
    sc.render.filepath = os.path.join(out, f"set_{which}_{i}.png"); bpy.ops.render.render(write_still=True)
