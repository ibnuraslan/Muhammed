"""Part 5 shared scene setup: puts the shared library (mary_celeste_3d/lib, scenes/common.py) and lib5 on the path."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
for p in (os.path.join(HERE, "..", "lib5"), os.path.join(ROOT, "mary_celeste_3d", "lib"), os.path.join(ROOT, "mary_celeste_3d", "scenes")):   # scenes/common.py must win over lib/common.py
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("MH_DATA", os.path.join(ROOT, "mary_celeste_3d", "assets", "makehuman"))
import common as C
OUTDIR = os.environ.get("OUTDIR", os.path.join(HERE, "..", "out", "frames"))


# every shot runs the clipping check before it renders (CLIPONLY=1: check, write out/clip/<shot>.json, no render)
_finish = C.finish


ANIM = bool(os.environ.get("P5_ANIM"))      # final render: the scene is built, graded and handed to tools/run_anim5.py
FLOATS = []                                  # boatsea.float_on calls (ocean, root, heading, x, y, kwargs): replayed per frame
if ANIM:
    import boatsea as _BS
    _float_on = _BS.float_on

    def _rec_float_on(ocean, root, heading_deg, x, y, **kw):
        FLOATS.append((ocean, root, heading_deg, x, y, kw))
        return _float_on(ocean, root, heading_deg, x, y, **kw)
    _BS.float_on = _rec_float_on
    _BS.float_on_raw = _float_on              # the animation re-solves with the original (no recording)


def _checked_finish(out, *a, **k):
    import bpy, clipcheck, weather
    shot = os.path.splitext(os.path.basename(out))[0]
    weather.soften_chips()
    if ANIM:
        import grade as G
        G.add_grade(bpy.context.scene, bloom=k.get("bloom", 0.3), look="cinematic", cine=k.get("cine"))
        print("BUILT", shot, flush=True)
        return
    bad = clipcheck.check(shot)
    if os.environ.get("CLIPONLY"):
        print("RENDERED", out, "(clip check only)")
        return
    return _finish(out, *a, **k)


C.finish = _checked_finish
