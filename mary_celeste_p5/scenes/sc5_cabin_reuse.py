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
_finish = C.finish


def finish(out, grade=True, cine=None, bloom=0.3):
    C.camera(Vector((1.45, -1.2, 0.62)), Vector((-0.35, 0.45, 1.0)), lens=22, fstop=4.0, focus=2.2)
    return _finish(out, grade=grade, cine={"exposure": 0.15, "sat": 1.08}, bloom=0.4)


C.finish = finish
runpy.run_path(os.path.join(p5.ROOT, "mary_celeste_3d", "scenes", "sc_b_cabin.py"), run_name="__main__")
