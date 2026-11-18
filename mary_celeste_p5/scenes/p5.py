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
