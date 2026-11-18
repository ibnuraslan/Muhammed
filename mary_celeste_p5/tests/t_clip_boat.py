"""Yawl + ten people on a flat frame (no sea): clipping check + top / side / stern / interior views."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector
import yawl, boatcrew, clipcheck5
sc = C.render_setup(samples=16, res=(800, 450)); sc.render.resolution_percentage = 100
b = yawl.build("yawl", oars="out")
bpy.context.view_layer.update()
boatcrew.man_the_boat(b, look=Vector((30, 20, 4)), density=0.0, hair=False)
clipcheck5.check("boat_test")
if os.environ.get("BOUNDS"):
    import sketchfab as SF
    for n in os.environ["BOUNDS"].split(","):
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name.startswith(n):
                lo, hi = SF.bounds([o]); print("B", o.name, [round(v, 2) for v in lo], [round(v, 2) for v in hi])
if os.environ.get("NORENDER"):
    sys.exit(0)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
for i, (loc, tgt, lens) in enumerate([((0, 0, 9), (0, 0.001, 0), 30), ((0, -8, 0.9), (0, 0, 0.7), 35), ((-7, 0, 1.6), (0, 0, 0.6), 35), ((-1.0, -0.2, 2.2), (-2.4, 0, 0.5), 24)]):
    C.camera(Vector(loc), Vector(tgt), lens=lens)
    sc.render.filepath = f"/tmp/dl/cb{i}.png"; bpy.ops.render.render(write_still=True)
