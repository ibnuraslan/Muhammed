"""Close-up QA of Deveau: boots, hands, face (three 50-85 mm cameras)."""
import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import human as H, deveau as D, poses as P
sc = C.render_setup(samples=48, noise=0.05); sc.render.resolution_percentage = 50
d = D.Deveau(); h = d.h
P.stand(h, lean=4, weight="L"); P.head(h, pitch=4, yaw=8)
P.arm_down(h, "L"); P.arm_down(h, "R"); P.rest_hand(h, "L"); P.rest_hand(h, "R")
d.finish(look_at=(0.6, -3, 1.6), density=float(os.environ.get("HAIR", "1.0")))
import sea; sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.5
sun.rotation_euler = (0.9, 0.0, -0.6)
bpy.ops.mesh.primitive_plane_add(size=6); fl = bpy.context.active_object
import ship; fl.data.materials.append(ship.wood("wood_floor_deck", 1.0, wet=0.5))
out = os.environ.get("OUT", "/tmp/cu")
for nm, loc, tgt, lens in (("boots", (0.45, -0.75, 0.25), (0.0, -0.05, 0.1), 50),
                           ("hand", (0.55, -0.55, 0.95), (0.22, -0.02, 0.85), 60),
                           ("face", (0.25, -0.75, 1.68), (0.0, -0.05, 1.66), 85)):
    C.camera(Vector(loc), Vector(tgt), lens=lens)
    sc.render.filepath = f"{out}_{nm}.png"; bpy.ops.render.render(write_still=True)
