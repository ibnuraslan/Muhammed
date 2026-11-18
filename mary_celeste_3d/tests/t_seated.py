"""Seated Deveau: boots must follow the shins (P5 report), then run the clip checker."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import human as H, deveau as D, poses as P, sea
sc = C.render_setup(samples=24, noise=0.1); sc.render.resolution_percentage = 40
d = D.Deveau(); H.pose_sit(d.h); d.finish(density=0.3)
sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (0.9, 0, -0.8)
C.camera(Vector((1.9, -1.6, 0.8)), Vector((0, -0.25, 0.45)), lens=35)
sc.render.filepath = os.environ.get("OUT", "/tmp/seat") + ".png"; bpy.ops.render.render(write_still=True)
for o in d.sea_boots:
    print("BOOT", o.name, [round(v, 2) for v in o.matrix_world.translation], "zmin", round(min((o.matrix_world @ v.co).z for v in o.data.vertices), 3))
