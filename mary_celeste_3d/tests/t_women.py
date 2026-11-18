"""Full-body preview of Sarah and Sophia (lib/women.py) side by side."""
import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import human as H, poses as P, women as W, sea
sc = C.render_setup(samples=int(os.environ.get("SPP", "48")), noise=0.05); sc.render.resolution_percentage = 50
s = W.Sarah(); P.stand(s.h, lean=2, weight="L"); P.head(s.h, pitch=4, yaw=-10)
P.arm_down(s.h, "L", out=0.1, fwd=0.12, bend=35); P.arm_down(s.h, "R", out=0.1, fwd=0.05, bend=20)
P.rest_hand(s.h, "L"); P.rest_hand(s.h, "R")
s.finish(look_at=(0.8, -3, 1.3), place=Matrix.Translation((-0.35, 0, 0)), density=float(os.environ.get("HAIR", "0.6")))
k = W.Sophia(); P.stand(k.h, lean=0, weight="R"); P.head(k.h, pitch=-6, yaw=15)
P.arm_down(k.h, "L", out=0.3, fwd=0.15, bend=30); P.arm_down(k.h, "R", out=0.3, fwd=0.1, bend=25)
k.finish(look_at=(0.5, -3, 1.0), place=Matrix.Translation((0.35, -0.1, 0)), density=float(os.environ.get("HAIR", "0.6")))
sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (0.9, 0, -0.7)
bpy.ops.mesh.primitive_plane_add(size=8); fl = bpy.context.active_object
import ship; fl.data.materials.append(ship.wood("wood_floor_deck", 1.0, wet=0.2))
out = os.environ.get("OUT", "/tmp/women")
for nm, loc, tgt, lens in (("front", (0.4, -3.6, 1.0), (0.0, 0, 0.8), 35), ("34", (2.6, -2.6, 1.2), (0.0, 0, 0.8), 40),
                           ("face", (-0.15, -0.95, 1.55), (-0.35, 0, 1.52), 70)):
    C.camera(Vector(loc), Vector(tgt), lens=lens)
    sc.render.filepath = f"{out}_{nm}.png"; bpy.ops.render.render(write_still=True)
