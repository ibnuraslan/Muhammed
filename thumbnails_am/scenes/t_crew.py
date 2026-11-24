import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tcommon as T
C = T.use("antwerp")
import bpy
from mathutils import Vector
import crew, sets as S
sc = T.res_setup(16, noise=0.1); sc.render.resolution_percentage = 30
p, arm, ms, hand = crew.thief(Vector((0, 0, 0)), 0, pose=eval(os.environ.get("POSE", "crew.CROUCH")))
print("HAND", hand)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=hand)
S.box("floor", (0, 0, -0.01), (6, 6, 0.02), S.flat("f", (0.5, 0.5, 0.5), 0.8))
S.world((1, 1, 1), 1.0)
for tag, loc in (("side", (4, 0, 0.9)), ("front", (0, -4, 0.9))):
    C.camera(Vector(loc), Vector((0, 0, 0.7)), lens=35)
    sc.render.filepath = os.path.join(T.OUTDIR, f"crew_{tag}.png"); bpy.ops.render.render(write_still=True)
