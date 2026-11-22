import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
from mathutils import Vector
import sets as ST, sets2 as S2, modern as MD, acts as AC, props as PR
sc = C.render_setup(samples=32, noise=0.06, bounces=6)
out = os.path.join(C.HERE, "..", "out", "tests")
which = os.environ.get("W", "pose")
if which == "pose":
    A = ST.vault_complex("heist", forced=40, debris=0.3, contacts="bypassed", taped=True)
    m = MD.Finotto(night=True); k = AC.Kneel(m, (0.4, 2.0), 180, lean=35); k.finish(look=(0, 2, 0), density=0.4)
    t = MD.Trader(2); s = AC.SitFloor(t, (-1.6, 3.4), 0, back_lean=-10); s.finish(look=(0, 3, 0.5), density=0.4)
    g = MD.Trader(0); st = AC.Stand(g, (1.2, 3.0), 160); AC.hands_to_face(st); st.finish(density=0.4)
    import clipcheck; clipcheck.check("t_p2")
    views = [((1.8, 0.4, 1.5), (-0.2, 2.8, 0.6), 24), ((0, -1.5, 2.2), (-0.3, -0.5, 2.0), 30)]
elif which == "garage":
    A = S2.garage(); views = [((-1.5, -6.5, 1.6), (2.0, 6.0, 1.0), 22), ((0, 6.0, 1.6), (0, -12, 2.0), 24)]
else:
    A = S2.district()
    for a, b in A["district_streets"]:
        S2.soft_strip(a, b, 0.012, 0.05)
    views = [((-0.6, -0.8, 0.7), (0, 0, 0), 35)]
for i, (l, t_, lens) in enumerate(views):
    C.camera(Vector(l), Vector(t_), lens=lens)
    sc.render.filepath = os.path.join(out, f"p2_{which}_{i}.png"); bpy.ops.render.render(write_still=True)
