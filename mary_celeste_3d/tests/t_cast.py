"""Shared cast line-up: Briggs, Sarah (bonnet off, no shawl), Sarah seated, Sophia (shawl), Arthur."""
import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import human as H, poses as P, women as W, briggs as BR, sea
sc = C.render_setup(samples=int(os.environ.get("SPP", "40")), noise=0.06); sc.render.resolution_percentage = 50
D_ = float(os.environ.get("HAIR", "0.5"))
def place(x): return Matrix.Translation((x, 0, 0))
b = BR.Briggs(); P.stand(b.h, lean=2, weight="R"); P.arm_down(b.h, "L"); P.arm_down(b.h, "R"); P.rest_hand(b.h, "L"); P.rest_hand(b.h, "R")
b.finish(look_at=(-1.3, -3, 1.6), place=place(-1.3), density=D_)
s = W.Sarah(bonnet=False, shawl=False); P.stand(s.h, lean=2, weight="L"); P.head(s.h, yaw=-10)
P.arm_down(s.h, "L", out=0.12, fwd=0.15, bend=40); P.arm_down(s.h, "R", out=0.12, fwd=0.15, bend=40); P.rest_hand(s.h, "L"); P.rest_hand(s.h, "R")
s.finish(look_at=(-0.4, -3, 1.5), place=place(-0.45), density=D_)
ss = W.Sarah(name="SarahSeated", seated=True); H.pose_sit(ss.h, lean=6)
ss.finish(look_at=(0.4, -3, 1.0), place=place(0.4) @ Matrix.Translation((0, 0, 0.0)), density=D_)
k = W.Sophia(shawl=True); P.stand(k.h, weight="R"); P.arm_down(k.h, "L", out=0.3, fwd=0.15, bend=30); P.arm_down(k.h, "R", out=0.3, fwd=0.1, bend=25)
k.finish(look_at=(1.1, -3, 0.8), place=place(1.1), density=D_)
a = W.Arthur(); P.stand(a.h, weight="L"); P.arm_down(a.h, "L", out=0.12); P.arm_down(a.h, "R", out=0.12); P.rest_hand(a.h, "L"); P.rest_hand(a.h, "R")
a.finish(look_at=(1.7, -3, 1.2), place=place(1.7), density=D_)
sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (0.9, 0, -0.7)
bpy.ops.mesh.primitive_plane_add(size=12); fl = bpy.context.active_object
import ship; fl.data.materials.append(ship.wood("wood_floor_deck", 1.0, wet=0.2))
C.camera(Vector((0.2, -5.6, 1.1)), Vector((0.2, 0, 0.85)), lens=35)
sc.render.filepath = os.environ.get("OUT", "/tmp/cast") + ".png"; bpy.ops.render.render(write_still=True)
C.camera(Vector((-0.2, -1.3, 1.5)), Vector((-0.45, 0, 1.45)), lens=60)
sc.render.filepath = os.environ.get("OUT", "/tmp/cast") + "_sarahhair.png"; bpy.ops.render.render(write_still=True)
