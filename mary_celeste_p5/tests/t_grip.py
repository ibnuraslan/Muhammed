"""One seated rower gripping a bar: renders hand close-ups from three sides (visual grip check)."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector
import people as PP, ship
from sitpose import Seat
sc = C.render_setup(samples=24, res=(640, 480)); sc.render.resolution_percentage = 100
p = PP.sailor(1)
st = Seat(p, Vector((0, 0, 0.4)), 180.0)
st.legs({"L": Vector((-0.48, -0.1, 0.25)), "R": Vector((-0.48, 0.1, 0.25))})
st.lean(fwd=8)
c = Vector((-0.45, 0.05, 0.88)); bar = Vector((0, 1, -0.13)).normalized()
ship.cyl("bar", c - bar * 0.6, c + bar * 0.6, 0.024, verts=16)
e1 = st.grip_bar("R", c + bar * 0.07, bar); e2 = st.grip_bar("L", c - bar * 0.05, bar)
print("GRIPERR", round(e1 * 1000), round(e2 * 1000))
st.place_finish(Vector((-3, 0, 1)), density=0.0, hair=False)
import clipcheck5; clipcheck5.check("grip_test")
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
for i, off in enumerate([Vector((-0.45, -0.3, 0.2)), Vector((-0.5, 0.35, 0.1)), Vector((0.1, -0.1, 0.45))]):
    C.camera(c + off, c, lens=60)
    sc.render.filepath = f"/tmp/dl/grip{i}.png"; bpy.ops.render.render(write_still=True)
