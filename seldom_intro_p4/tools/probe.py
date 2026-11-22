"""Download a Sketchfab/PolyHaven prop and render a quick look:  blender -b -P tools/probe.py -- sf|ph UID HEIGHT OUT.png"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mary_celeste_p4", "lib"))
import p4; p4.C.reset()
import bpy
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
kind, uid, H, out = a[0], a[1], float(a[2]), a[3]
if kind == "sf":
    import skfab; r, ms = skfab.model(uid, height=H)
else:
    import ph; r, ms = ph.model(uid)
bpy.context.view_layer.update()
import numpy as np
P = np.array([o.matrix_world @ Vector(c) for o in ms for c in o.bound_box])
lo, hi = P.min(0), P.max(0); c = (lo + hi) / 2; s = (hi - lo).max()
print("BOUNDS", lo.round(3), hi.round(3), "meshes", len(ms), "faces", sum(len(o.data.polygons) for o in ms))
sc = p4.C.render_setup(samples=16, noise=0.1, bounces=4)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 480, 100
p4.world_color((0.5, 0.5, 0.52), 1.0)
p4.sun(40, 45, 3)
p4.C.camera(tuple(Vector(c) + Vector((s * 1.3, -s * 1.6, s * 0.9))), tuple(c), lens=40)
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
