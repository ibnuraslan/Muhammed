import os, sys, math, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
import uist as U, dig as G, cast as K
t0 = time.time()
sc = C.render_setup(samples=24, noise=0.05, bounces=6)
T = U.island("golden", grass_at=(0, 0), grass_r=24, grass_density=300, n=600, core=4.0)
G.houses(); b1 = G.burial("B1", "M", "A")
st = K.kneel_trowel(K.DiggerA, (-1.0, 8.1), 135, work=(-1.35, 8.55))
st2 = K.kneel_trowel(K.DiggerB, (-2.9, 9.7), -30, work=(-2.45, 9.25))
print("BUILD", round(time.time() - t0))
import clipcheck
bad = clipcheck.check("t_digger", limit=80, hand_ok=("trowel", "Uist", "fill"))
for v, (loc, tgt, lens) in {"back": ((0.6, 6.6, 4.6), (-1.6, 8.9, 3.4), 35), "side": ((-4.2, 12.6, 4.1), (-1.8, 8.9, 3.4), 35)}.items():
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = os.path.join(C.HERE, "..", "out", "tests", f"digger_{v}.png")
    bpy.ops.render.render(write_still=True); print("RENDERED", v, round(time.time() - t0))
