"""S11 "a soaked cabin": the shared cabin set (mary_celeste_3d/scenes/sc_b_cabin.py), run unchanged; only the
camera (a low wide across the wet floor, toward Deveau's lantern) and the shot's grade are swapped in, by
wrapping common.finish before the shared script runs."""
import os, sys, runpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p5
import common as C
from mathutils import Vector
OUT = os.environ.get("OUT", os.path.join(p5.OUTDIR, "S11.png"))
os.environ["OUT"] = OUT
os.environ.setdefault("FOG", "0.0")        # the shared scene's own haze knob: thinner for this low wide
_finish = C.finish


def finish(out, grade=True, cine=None, bloom=0.3):
    C.camera(Vector((-1.45, -1.15, 0.55)), Vector((0.05, 0.55, 1.0)), lens=22, fstop=4.0, focus=1.9)
    return _finish(out, grade=grade, cine={"exposure": 0.15, "sat": 1.08}, bloom=0.4)


C.finish = finish
runpy.run_path(os.path.join(p5.ROOT, "mary_celeste_3d", "scenes", "sc_b_cabin.py"), run_name="__main__")
