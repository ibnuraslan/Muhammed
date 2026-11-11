"""Estimated shot durations from PLAN.md until the voiceover arrives: each set's script line at 125 wpm,
split evenly between shots A and B. The intro's first shot carries the 2.5 s lead-in; each chapter's first
shot gets 2 s for its title card to breathe.  dur("ch3_17b") -> seconds."""
import os, re

PLAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PLAN.md")
WPM = 125.0
_D = None


def _load():
    global _D
    _D = {}
    chap = None
    for line in open(PLAN, encoding="utf8"):
        m = re.match(r"## (Intro|Chapter (One|Two|Three|Four))", line)
        if m:
            chap = {"Intro": "intro", "Chapter One": "ch1", "Chapter Two": "ch2", "Chapter Three": "ch3", "Chapter Four": "ch4"}[m.group(1)]
            continue
        if chap and line.startswith("| ") and not line.startswith("| Set") and not line.startswith("|---"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            sm = re.match(r"(\d+)", cells[0])
            if not sm:
                continue
            n = int(sm.group(1)); words = len(re.sub(r"\(title card\)", "", cells[1]).split())
            sec = max(4.0, words / WPM * 60.0)
            a = b = sec / 2
            if n == 1:
                a += 2.5 if chap == "intro" else 2.0
            _D[f"{chap}_{n}a"] = round(a, 2); _D[f"{chap}_{n}b"] = round(b, 2)
    return _D


def dur(shot, default=4.0):
    if _D is None:
        _load()
    return _D.get(shot, default)


if __name__ == "__main__":
    _load()
    tot = {}
    for k, v in _D.items():
        tot[k.split("_")[0]] = tot.get(k.split("_")[0], 0) + v
    print(tot, sum(tot.values()))
