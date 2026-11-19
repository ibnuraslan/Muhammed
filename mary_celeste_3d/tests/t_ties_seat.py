import sys, os, math; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector, Matrix
import women as W, sitpose as SP, sea
sc = C.render_setup(samples=32, noise=0.08); sc.render.resolution_percentage = 40
s = W.Sarah(); s.relaxed(); s.finish(look_at=(0, -3, 1.5), density=0.4)
d = W.Sarah(name="SeatSarah", seated=True)
st = SP.Seat(d, Vector((1.5, 0, 0.45)), 0.0)
st.legs({"L": Vector((1.6, -0.45, 0.08)), "R": Vector((1.4, -0.45, 0.08))})
tgt = Vector((3.5, -1.0, 1.2))                          # to her left (+X) and in front
st.head(tgt); st.place_finish(tgt, density=0.3)
hd = d.h.arm  # after finish the rig is hidden; measure the face direction from the eyes
e = d.h.eyes; mid = (e[0].matrix_world.translation + e[1].matrix_world.translation) / 2
print("HEADTURN eyes at", [round(v, 2) for v in mid], "target", tuple(tgt))
sea.sky(strength=0.8, rot_deg=240)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3; sun.rotation_euler = (0.9, 0, -0.7)
out = os.environ.get("OUT", "/tmp/ts")
C.camera(Vector((0.75, -0.25, 1.52)), Vector((0, -0.05, 1.47)), lens=70)
sc.render.filepath = out + "_side.png"; bpy.ops.render.render(write_still=True)
C.camera(Vector((1.5, -3.0, 1.2)), Vector((1.5, 0, 0.8)), lens=40)
sc.render.filepath = out + "_seat.png"; bpy.ops.render.render(write_still=True)
