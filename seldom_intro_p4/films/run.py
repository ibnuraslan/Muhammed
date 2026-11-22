"""Render one frame of an intro film:  blender -b --factory-startup -P films/run.py -- f1 B 0.5 out.png
Env: PCT (resolution percentage of 2560x1440, default 50 = 1280x720 key frames)."""
import os, sys, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import si
si.C.reset()
import bpy
a = sys.argv[sys.argv.index("--") + 1:]
film, shot = a[0], a[1]; t = float(a[2]) if len(a) > 2 else 0.5
out = a[3] if len(a) > 3 else os.path.join(HERE, "..", "out", "key", f"{film}_{shot}.png")
mod = importlib.import_module({"f1": "f1_lamp", "f2": "f2_letters", "f3": "f3_locksmith", "f4": "f4_salvage"}[film])
_orig = si.C.render_setup
def rs(*k, **kw):
    sc = _orig(*k, **kw); sc.render.resolution_percentage = int(os.environ.get("PCT", "50"))
    if os.environ.get("SPP"):
        sc.cycles.samples = int(os.environ["SPP"])
    return sc
si.C.render_setup = rs
si.T = t
mod.build(shot, t, os.path.abspath(out))
