"""Sarah's bonnet ties and shawl front up close (local fixes in people.sarah): side view of the chin, 3/4 of the chest."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector, Matrix
import people as PP, poses as P
sc = C.render_setup(samples=48, res=(900, 900)); sc.render.resolution_percentage = 100
p = PP.sarah()
P.stand(p.h, weight="L"); P.arm_down(p.h, "L"); P.arm_down(p.h, "R"); P.rest_hand(p.h, "L"); P.rest_hand(p.h, "R")
p.finish(look_at=(0, -5, 1.5), place=Matrix.Identity(4), density=0.4)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.52, 1)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
z = p.h.bone_head("head").z
for nm, cam, tgt, lens in (("side", (0.9, -0.25, z + 0.0), (0, 0, z - 0.02), 85), ("chest", (0.9, -1.6, z - 0.15), (0, 0, z - 0.3), 50)):
    C.camera(cam, tgt, lens=lens)
    sc.render.filepath = f"/tmp/dl/t_sarah_{nm}.png"; bpy.ops.render.render(write_still=True)
