import os, sys, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector
import sea, yawl, boatsea, boatcrew
sc = C.render_setup(samples=32, res=(960, 540)); sc.render.resolution_percentage = 100
b = yawl.build("yawl", oars="out")
water = sea.water_material()
oc = sea.ocean(size=90, res=18, scale=0.9, chop=1.0, wind=8.0, repeat=2, foam=0.15, mat=water)
sea.far_sea(130, mat=water); sea.sky(strength=1.0)
boatsea.float_on(oc, b["root"], 20, 0, 0, draft=0.40)
boatsea.cut_and_wash(oc, [b["hull"]], [b["root"]])
t = time.time()
ppl = boatcrew.man_the_boat(b, look=Vector((30, 20, 4)), density=0.4)
print("CREW", len(ppl), round(time.time() - t, 1))
for i, (loc, tgt, lens) in enumerate([((6.5, -7.5, 2.6), (0, 0, 0.8), 35), ((-5.5, -3.0, 1.6), (-1.5, 0, 1.0), 35), ((0.5, -6, 1.2), (0, 0, 1.0), 50), ((1.5, 3.5, 3.5), (-0.8, 0, 0.8), 28)]):
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = f"/tmp/dl/t_bc{i}.png"; bpy.ops.render.render(write_still=True)
