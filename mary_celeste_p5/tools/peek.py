"""Quick look at Poly Haven models: blender -b --python peek.py -- id1 id2 ..."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mary_celeste_3d", "scenes"))
import common as C
import bpy
from mathutils import Vector
import ph
ids = sys.argv[sys.argv.index("--") + 1:]
for aid in ids:
    C.reset(); sc = C.render_setup(samples=24, res=(640, 400))
    sc.render.resolution_percentage = 100
    root, ms = ph.model(aid)
    lo, hi = ph.bounds(ms)
    lo, hi = Vector(lo), Vector(hi); c = (lo + hi) / 2; s = (hi - lo).length
    print("SIZE", aid, tuple(round(v, 3) for v in (hi - lo)))
    C.camera(c + Vector((s * 0.9, -s * 1.1, s * 0.6)), c, lens=40)
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
    sc.render.filepath = f"/tmp/dl/peek_{aid}.png"; bpy.ops.render.render(write_still=True)
