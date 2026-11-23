import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scenes"))
import common as C
C.reset()
import bpy
import uist as U
sc = C.render_setup(samples=int(os.environ.get("SPP", "32")), noise=0.05, bounces=6)
mood = os.environ.get("MOOD", "golden")
T = U.island(mood, grass_at=None if os.environ.get("NOGRASS") else (0, 0), grass_r=40, n=int(os.environ.get("N", "700")))
views = {"aerial": ((-250, -330, 45), (-40, 120, 2), 28), "dig": ((-15, -13, 7.6), (0, 0, 4.0), 28), "coast": ((-200, -60, 40), (-320, 120, 0), 24)}
for v in os.environ.get("VIEWS", "aerial,dig").split(","):
    loc, tgt, lens = views[v]
    C.camera(loc, tgt, lens=lens)
    sc.render.filepath = os.path.join(C.HERE, "..", "out", "tests", f"island_{mood}_{v}.png")
    bpy.ops.render.render(write_still=True); print("RENDERED", sc.render.filepath)
