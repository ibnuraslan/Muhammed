import os, sys, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector, Matrix
import people as PP, poses as P, look
sc = C.render_setup(samples=48, res=(1600, 900)); sc.render.resolution_percentage = 100
who = os.environ.get("WHO", "briggs,sarah,sophia,arthur,sailor0").split(",")
x = -1.6
for w in who:
    t = time.time()
    p = PP.sailor(int(w[-1])) if w.startswith("sailor") else getattr(PP, w)()
    P.stand(p.h, weight="L"); P.arm_down(p.h, "L"); P.arm_down(p.h, "R"); P.rest_hand(p.h, "L"); P.rest_hand(p.h, "R")
    p.finish(look_at=(x, -5, 1.4), place=Matrix.Translation((x, 0, 0)), density=0.6)
    print("BUILT", w, round(time.time() - t, 1)); x += 0.8
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.52, 1)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
C.camera((0, -5.2, 1.1), (0, 0, 0.9), lens=40)
sc.render.filepath = "/tmp/dl/t_cast.png"; bpy.ops.render.render(write_still=True)
C.camera((-1.2 + float(os.environ.get("FX", "0")), -1.6, 1.4), (-1.2 + float(os.environ.get("FX", "0")), 0, 1.2), lens=45)
sc.render.filepath = "/tmp/dl/t_cast_face.png"; bpy.ops.render.render(write_still=True)
