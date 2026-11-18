import os, sys, math
sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes")]
import p5; C = p5.C
import bpy
from mathutils import Vector
import sketchfab as SF
for uid in sys.argv[sys.argv.index("--") + 1:]:
    C.reset(); sc = C.render_setup(samples=24, res=(480, 480)); sc.render.resolution_percentage = 100
    try:
        root, ms = SF.model(uid, size=1.0)
    except Exception as e:
        print("FAIL", uid, e); continue
    lo, hi = SF.bounds(ms); c = (lo + hi) / 2; s = (hi - lo).length
    C.camera(c + Vector((0.3 * s, -1.3 * s, 0.25 * s)), c, lens=45)
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.7, 0.7, 1)
    sc.render.filepath = f"/tmp/dl/sf_{uid[:8]}.png"; bpy.ops.render.render(write_still=True); print("PEEK", uid, tuple(round(v, 2) for v in hi - lo))
