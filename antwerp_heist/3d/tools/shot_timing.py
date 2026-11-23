"""Time every shot of a part to its narration: each VO line's span (timing/Px_lines.json, from vo_align.py) is shared
by that line's shots in proportion to their planned lengths; frames are integers at 24 fps and the part's total is
exactly the VO length. Writes timing/Px_shots.json {shot: {start, frames, dur, line}}.   python3 tools/shot_timing.py P1"""
import os, sys, re, json
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PART = sys.argv[1]; FPS = 24
L = json.load(open(os.path.join(D, "timing", f"{PART}_lines.json")))
src = open(os.path.join(D, "scenes", PART.lower() + ".py")).read()
plan = [(s, int(l), float(d)) for s, l, d in re.findall(r'\("([A-Z]\d+)", (\d+), ([0-9.]+), "', src)]
total = int(round(L["duration"] * FPS))
out = {}; frame = 1
by = {}
for s, l, d in plan:
    by.setdefault(l, []).append((s, d))
missing = [x["line"] for x in L["lines"] if x["line"] not in by]
if missing:
    raise SystemExit(f"lines without shots: {missing}")
for x in L["lines"]:
    shots = by[x["line"]]
    end_f = int(round(x["end"] * FPS)) + 1 if x["line"] < len(L["lines"]) else total + 1
    span = end_f - frame; w = sum(d for _, d in shots); acc = 0.0; start = frame
    for k, (s, d) in enumerate(shots):
        acc += d
        nxt = frame + int(round(span * acc / w)) if k < len(shots) - 1 else end_f
        out[s] = dict(start=start, frames=nxt - start, dur=round((nxt - start) / FPS, 3), line=x["line"])
        start = nxt
    frame = end_f
assert frame - 1 == total, (frame, total)
json.dump(dict(part=PART, fps=FPS, frames=total, shots=out), open(os.path.join(D, "timing", f"{PART}_shots.json"), "w"), indent=1)
short = [s for s, v in out.items() if v["frames"] < 30]
print(PART, total, "frames,", len(out), "shots; min", min(v["frames"] for v in out.values()), "max", max(v["frames"] for v in out.values()), "short<30:", short)
