import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import p5; C = p5.C
C.reset()
import bpy
from mathutils import Vector
import sea, yawl, boatsea
sc = C.render_setup(samples=32, res=(960, 540)); sc.render.resolution_percentage = 100
b = yawl.build("yawl", oars="out")
water = sea.water_material()
oc = sea.ocean(size=90, res=18, scale=0.9, chop=1.0, wind=8.0, repeat=2, foam=0.15, mat=water)
sea.far_sea(130, mat=water)
sea.sky(strength=1.0)
boatsea.float_on(oc, b["root"], 20, 0, 0, draft=0.42)
boatsea.cut_and_wash(oc, [b["hull"]], [b["root"]])
for i, (loc, tgt, lens) in enumerate([((6.5, -7.5, 2.6), (0, 0, 0.4), 35), ((-1.0, -2.6, 2.4), (0.6, 0, 0.3), 24), ((0, -9, 0.6), (0, 0, 0.4), 50)]):
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = f"/tmp/dl/t_yawl{i}.png"; bpy.ops.render.render(write_still=True)
