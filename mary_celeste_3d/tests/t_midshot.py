"""Mid-shot QA at 40 spp (the hub's black-strips-by-the-eyes check): Deveau at 3 m, 35 mm, side light."""
import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import human as H, deveau as D, poses as P, sea
sc = C.render_setup(samples=40, noise=0.1); sc.render.resolution_percentage = 50; sc.cycles.use_adaptive_sampling = False
d = D.Deveau(); h = d.h
P.stand(h, lean=4, weight="L"); P.head(h, pitch=8, yaw=20); P.arm_down(h, "L"); P.arm_down(h, "R")
d.finish(look_at=(1.0, -3, 1.4))
sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3
sun.rotation_euler = (1.2, 0, -1.2)
for nm, loc in (("mid", (0.9, -2.9, 1.55)), ("mid3q", (1.9, -2.1, 1.6))):
    C.camera(Vector(loc), Vector((0, 0, 1.45)), lens=35)
    sc.render.filepath = os.environ.get("OUT", "/tmp/ms") + f"_{nm}.png"; bpy.ops.render.render(write_still=True)
