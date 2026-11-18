"""Render one Part 1 shot (a storyboard frame, or with FRAMES set, the animated shot).

    blender -b --python run.py -- S01 [S02 ...]
    PREVIEW=0.5 SPP=24 blender -b --python run.py -- S01      (storyboard: half res, few samples)
Output: out/board/<id>.png"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "p1")); sys.path.insert(0, HERE)
import env as E
import bpy
import shots

ids = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for sid in ids:
    E.reset()
    sh = shots.SHOTS[sid]
    out = os.path.join(HERE, "out", "board", f"{sid}.png")
    sh["fn"]()
    # mandatory clipping check (shared lib/clipcheck.py): every character shot must report zero clips
    if any("person" in o for o in bpy.data.objects):
        import clipcheck
        bad = clipcheck.check(sid)
        print(f"CLIPRESULT {sid} {len(bad)}", flush=True)
    E.finish(out, cine=sh.get("cine"))
