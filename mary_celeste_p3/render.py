"""Render one Part 3 shot at time T (0..1) or a frame range.

    blender -b --python render.py -- SHOT [T]                  # one still (storyboard)
    SHOT=p3_01 T=0.5 PREVIEW=0.5 SPP=64 blender -b --python render.py
    SHOT=p3_01 FRAMES=0:96 OUTDIR=out/p3_01 blender -b --python render.py      # final: frames 0..95 at 24 fps
"""
import os, sys, math, time
HERE = os.path.dirname(os.path.abspath(__file__))
SC = os.path.join(HERE, "..", "mary_celeste_3d", "scenes")
for p in (os.path.join(HERE, "lib"), SC, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
import common as C
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = argv[0] if argv else os.environ["SHOT"]
T = float(argv[1]) if len(argv) > 1 else float(os.environ.get("T", "0.5"))
import shots as S


def one(t, out):
    C.reset()
    t0 = time.time()
    info = S.build(SHOT, t)
    sc = bpy.context.scene
    C.finish(out, cine=info.get("cine"), bloom=info.get("bloom", 0.3))
    print("RENDERED", out, f"{time.time() - t0:.0f}s")


if os.environ.get("FRAMES"):
    import crew
    crew.CACHE_DIR = os.path.join(HERE, "out", "haircache"); crew.CACHE_TAG = SHOT
    a, b = [int(x) for x in os.environ["FRAMES"].split(":")]
    n = S.SHOTS[SHOT]["frames"]
    od = os.environ.get("OUTDIR", os.path.join(HERE, "out", SHOT))
    for f in range(a, b):
        out = os.path.join(od, f"{SHOT}_{f:04d}.png")
        if os.path.exists(out):
            continue
        one(f / max(1, n - 1), out)
else:
    out = os.environ.get("OUT", os.path.join(HERE, "review", f"{SHOT}.png"))
    one(T, out)
