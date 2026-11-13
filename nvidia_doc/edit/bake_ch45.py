"""Bake every shot of Ch4 or Ch5 to the VO timing, into out/blend/ch<4|5>/<name>.blend (one self-contained .blend
per shot, textures packed), ready for make_master.py. Resumable: a shot whose .blend already exists is skipped.

  python edit/bake_ch45.py 4 [--samples 32] [--only c5_01_interview_passport_slide] [--force]
Then: python scenes/make_master.py chapter4 out/blend/ch4 vo/ch4_vo.mp3 3.0

Titles are injected by bake.py from the first shot's MOVES[...]['title'] entry; nothing extra needed here.
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PY = sys.executable
FPS = 24
chapter = sys.argv[1]
arg = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
samples = arg("--samples", 32)
only = arg("--only", "")
force = "--force" in sys.argv
step = arg("--step", 2)

tim = json.load(open(os.path.join(ROOT, "vo", "ch45_timing.json")))[chapter]
outdir = os.path.abspath(os.path.join(ROOT, "out", "blend", f"ch{chapter}"))
os.makedirs(outdir, exist_ok=True)
scenes_dir = os.path.join(ROOT, "scenes")

done, skipped = [], []
for sh in tim:
    name = sh["name"]
    if only and name != only:
        continue
    blend = os.path.join(outdir, name + ".blend")
    if os.path.exists(blend) and not force:
        skipped.append(name); continue
    seconds = sh["frames"] / FPS
    cmd = [PY, os.path.join(scenes_dir, "bake.py"), sh["set"], sh["move"],
           "--seconds", f"{seconds:.4f}", "--out", outdir, "--name", name, "--samples", str(samples), "--step", str(step)]
    print("[bake_ch45]", name, f"{seconds:.2f}s", sh["frames"], "frames", flush=True)
    env = dict(os.environ, BAKE_STEP=str(step))
    r = subprocess.run(cmd, cwd=scenes_dir, env=env)
    if r.returncode != 0:
        print("[bake_ch45][ERR]", name, "rc", r.returncode, flush=True); sys.exit(2)
    done.append(name)
print(f"[bake_ch45] ch{chapter}: baked {len(done)}, skipped {len(skipped)} -> {outdir}")
