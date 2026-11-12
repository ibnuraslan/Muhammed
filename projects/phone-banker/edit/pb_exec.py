"""Run nvidia_doc/scenes/run.py or bake.py for one phone-banker shot, timed to its cut.

  python edit/pb_exec.py <seconds> <run|bake> <set> <move> [run.py / bake.py args...]

The set's anim functions take seconds as t * DUR[move]; setting DUR[move] to the cut length makes the action play in
real time (people walk and move at their designed speed) while the camera move spans the whole cut. Shots in
SCALED keep their designed DUR, so their events (a lid closing, lights going out) are spread over the cut.
PB_SHOT_FRAMES tells frame-driven effects (the seasons montage) how long the shot is.
"""
import os, sys, runpy, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
ND = os.path.abspath(os.path.join(HERE, "..", "..", "..", "nvidia_doc", "scenes"))
sys.path.insert(0, os.path.join(HERE, "..", "scenes")); sys.path.insert(0, ND)
SCALED = {("forlab", "case_close")}

seconds, tool, set_name, move = float(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
rest = sys.argv[5:]
os.environ["PB_SHOT_FRAMES"] = str(int(round(seconds * 24)))
if "--plain" in rest:
    os.environ["HOUSE_LOOK"] = "plain"
mod = importlib.import_module("sc_" + set_name)
if (set_name, move) not in SCALED:
    mod.DUR[move] = seconds
print(f"[pb] {set_name} {move}: cut {seconds:.2f} s, DUR {mod.DUR[move]:.2f}", flush=True)
script = os.path.join(ND, "run.py" if tool == "run" else "bake.py")
extra = ["--seconds", str(seconds)] if tool == "bake" else []
sys.argv = [script, set_name, move] + extra + rest
runpy.run_path(script, run_name="__main__")
