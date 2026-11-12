"""Bake every shot of a chapter (shots.py order) into out/blend/<chapter>/<set>_<move>.blend.
Seconds come from each set's DUR (estimates until the voiceovers arrive); the first shot gets the lead-in.
  python tools/bake_chapter.py ch2 [jobs] [lead]
"""
import os, sys, subprocess, importlib
from concurrent.futures import ThreadPoolExecutor
ROOT = "/home/user/Muhammed"; P = os.path.join(ROOT, "projects/killer-in-house")
sys.path[:0] = [os.path.join(P, "scenes"), os.path.join(ROOT, "nvidia_doc/scenes")]
import shots
ch = sys.argv[1]; jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 2; lead = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
out = os.path.join(P, "out/blend", ch); os.makedirs(out, exist_ok=True)
env = dict(os.environ, PYTHONPATH=os.path.join(P, "scenes") + ":" + os.path.join(ROOT, "nvidia_doc/scenes"))
todo = []
for k, (st, mv, t, lab) in enumerate(shots.CHAPTERS[ch]):
    mod = importlib.import_module("sc_" + st)
    sec = mod.DUR[mv] + (lead if k == 0 else 0.0)
    todo.append((st, mv, sec))
def run(a):
    st, mv, sec = a
    f = os.path.join(out, f"{st}_{mv}.blend")
    if os.path.exists(f):
        return f"skip {st}_{mv}"
    log = os.path.join(out, f"{st}_{mv}.log")
    r = subprocess.run([sys.executable, os.path.join(P, "scenes/bake_kih.py"), st, mv, "--seconds", str(sec), "--out", out],
                       env=env, cwd=ROOT, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    return f"{'ok' if r.returncode == 0 and os.path.exists(f) else 'FAIL'} {st}_{mv} {sec:.2f}s"
with ThreadPoolExecutor(jobs) as ex:
    for msg in ex.map(run, todo):
        print(msg, flush=True)
