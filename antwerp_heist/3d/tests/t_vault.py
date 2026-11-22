import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import sets
st = os.environ.get("STATE", "wreck")
sc = C.render_setup(samples=int(os.environ.get("SPP", "32")), noise=0.06, bounces=6)
A = sets.vault_complex(st)
print("BOXES", A["n_boxes"], "OPEN", len(A["open_cells"]), "DEBRIS", A.get("debris"))
out = os.path.join(C.HERE, "..", "out", "tests"); os.makedirs(out, exist_ok=True)
views = {"in": ((2.2, 0.4, 1.55), (-1.0, 3.6, 0.6), 22), "corr": ((0.5, -6.5, 1.6), (0, 0.5, 1.0), 30),
         "door": ((-0.7, -3.0, 1.5), (0.6, -1.0, 1.1), 26)}
for k, (loc, tgt, lens) in views.items():
    C.camera(Vector(loc), Vector(tgt), lens=lens)
    sc.render.filepath = os.path.join(out, f"vault_{st}_{k}.png"); bpy.ops.render.render(write_still=True)
