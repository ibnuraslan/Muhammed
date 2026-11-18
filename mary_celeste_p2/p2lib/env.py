"""Paths: the shared library (claude/mary-celeste-3d, unpacked unchanged into ../shared3d) and this part's lib."""
import os, sys
P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(P2, "shared3d")
for p in (os.path.join(SHARED, "lib"), os.path.join(SHARED, "scenes"), os.path.join(P2, "p2lib")):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("MH_DATA", os.path.join(SHARED, "assets", "makehuman"))
