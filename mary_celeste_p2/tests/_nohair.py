import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "p2lib"))
import env
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import cast, poses as P
sc = C.render_setup(samples=16, noise=0.05)
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
WHO = os.environ.get("WHO", "Briggs,Sarah,Child,Sailor").split(",")
xs = [(-1.2 + 0.8 * i) for i in range(len(WHO))]
for i, w in enumerate(WHO):
    p = getattr(cast, w)()
    P.stand(p.h, weight="L"); P.arm_down(p.h, "L"); P.arm_down(p.h, "R")
    P.rest_hand(p.h, "L"); P.rest_hand(p.h, "R")
    p.finish_live(look_at=(0, -4, 1.5), place=Matrix.Translation((xs[i], 0, 0)), density=0.5, hair=False)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.22, 0.16, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
l = bpy.data.lights.new("key", 'AREA'); l.energy = 900; l.size = 2; l.color = (1, 0.85, 0.7)
o = bpy.data.objects.new("key", l); sc.collection.objects.link(o); o.location = (-2.5, -3, 3)
o.rotation_euler = (Vector((0, 0, 1)) - o.location).to_track_quat('-Z', 'Y').to_euler()
fl = bpy.data.objects.new("fl", bpy.data.meshes.new("fl")); sc.collection.objects.link(fl)
fl.data.from_pydata([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)], [], [[0, 1, 2, 3]])
Y = float(os.environ.get("CZ", "1.1"))
C.camera((0, -4.2, Y + 0.3), (0, 0, Y), lens=float(os.environ.get("LENS", "40")))
C.finish(os.environ.get("OUT", "/tmp/claude-0/t_cast.png"))
