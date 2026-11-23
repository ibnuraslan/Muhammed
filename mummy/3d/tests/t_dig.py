import os, sys, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
import uist as U, dig as G
t0 = time.time()
sc = C.render_setup(samples=int(os.environ.get("SPP", "24")), noise=0.05, bounces=6)
T = U.island(os.environ.get("MOOD", "overcast"), grass_at=(0, 0), grass_r=28, grass_density=320, n=int(os.environ.get("N", "800")), core=4.0)
G.houses(); G.kit()
b1 = G.burial("B1", "M", "A"); b2 = G.burial("B2", "M", "C", side="L")
print("BUILD", round(time.time() - t0))
views = {"crane": ((14, -22, 9), (0, 2, 3.4), 26), "b1": ((-1.8, 8.6, 5.6), (-1.8, 8.92, 3.1), 35), "b1low": ((-0.4, 7.9, 3.75), (-1.9, 9.0, 3.1), 40), "wide": ((-24, -20, 6.8), (2, 4, 3.8), 24)}
for v in os.environ.get("VIEWS", "crane,b1,wide").split(","):
    loc, tgt, lens = views[v]
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = os.path.join(C.HERE, "..", "out", "tests", f"dig_{v}.png")
    bpy.ops.render.render(write_still=True); print("RENDERED", v, round(time.time() - t0))
