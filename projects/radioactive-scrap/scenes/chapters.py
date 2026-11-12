"""Shot order per chapter for make_master.py (baked file names are <set>_<move>).
make_master merges these into its CHAPTERS when this folder is on PYTHONPATH."""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = ["scrapyard", "ikitelli", "hospital", "smelter", "therapy", "ankara", "building"]


def _moves():
    found = {}
    for s in SETS:
        src = open(os.path.join(HERE, f"sc_{s}.py"), encoding="utf8").read()
        for m in re.findall(r'^    "((?:intro|ch\d)_\d+[ab])"', src, re.M):
            found[m] = s
    return found


def chapters():
    mv = _moves()
    out = {}
    for ch in ("intro", "ch1", "ch2", "ch3", "ch4"):
        keys = sorted([k for k in mv if k.startswith(ch + "_")], key=lambda k: (int(re.findall(r"_(\d+)", k)[0]), k[-1]))
        out["rs_" + ch] = [(f"{mv[k]}_{k}", f"Set {k.split('_')[1].upper()}") for k in keys]
    return out


CHAPTERS = chapters()

if __name__ == "__main__":
    for k, v in CHAPTERS.items():
        print(k, len(v), [a for a, b in v])
