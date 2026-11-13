"""Bake every shot of the film into its own self-contained .blend (do NOT render here).
  python bake_all.py [part ...]        parts: cold ch1 ch2 (A) | ch3 ch4 ch5 (B, from b_shots.py) | sting
-> projects/radio-jingle/out/blend/<part>/<part>_<NN>_<set>_<move>.blend  (+ shots.json with the order and seconds)
Each bake runs in its own process (memory), with this folder first on the path."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "..", "out", "blend")
BAKE = os.path.join(ROOT, "nvidia_doc", "scenes", "bake.py")
env = dict(os.environ, PYTHONPATH=HERE + os.pathsep + os.path.join(ROOT, "nvidia_doc", "scenes"))


def shot_list(part):
    sys.path.insert(0, HERE); sys.path.insert(1, os.path.join(ROOT, "nvidia_doc", "scenes"))
    if part in ("cold", "ch1", "ch2"):
        import chapters
        return [(s, m, sec, f"{s} {m}") for (s, m, sec) in chapters.durations(part)]
    if part in ("ch3", "ch4", "ch5"):
        import b_shots
        return [(s, m, sec, lab) for (s, m, lab, sec) in b_shots.seconds(part)]
    if part == "sting":
        return [("logo", "bag", 6.0, "Seldom logo sting")]
    raise KeyError(part)


def bake(part, force=False):
    d = os.path.join(OUT, part); os.makedirs(d, exist_ok=True)
    rows = []
    for k, (s, m, sec, lab) in enumerate(shot_list(part)):
        name = f"{part}_{k:02d}_{s}_{m}" if part != "sting" else "seldom_sting"
        rows.append(dict(name=name, set=s, move=m, seconds=sec, label=lab))
        if os.path.exists(os.path.join(d, name + ".blend")) and not force:
            continue
        cmd = [sys.executable, BAKE, s, m, "--seconds", str(sec), "--out", d, "--name", name, "--samples", "32"]
        print("[bake_all]", " ".join(cmd[1:]), flush=True)
        subprocess.run(cmd, env=env, check=True, cwd=ROOT)
    json.dump(rows, open(os.path.join(d, "shots.json"), "w"), indent=1)


if __name__ == "__main__":
    parts = [a for a in sys.argv[1:] if not a.startswith("-")] or ["cold", "sting", "ch1", "ch2", "ch3", "ch4", "ch5"]
    for p in parts:
        bake(p, force="--force" in sys.argv)
