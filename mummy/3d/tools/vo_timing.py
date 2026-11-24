"""Cut a part's shots to its recorded VO: each VO paragraph spans from the pause before it to the pause after it
(paragraph ends found by silence detection and matched to the text), and the paragraph's shots share that span in
proportion to their planned lengths. Total = VO length exactly.

    python3 tools/vo_timing.py P1 <paragraph end times in seconds, comma separated> <vo length s>
    -> vo/P1_timing.json  {"fps": 24, "frames_total": N, "shots": [{"shot","para","start","frames"}...]}
"""
import sys, json, re, importlib, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
part, ends, total = sys.argv[1], [float(x) for x in sys.argv[2].split(",")], float(sys.argv[3])
FPS = 24
src = open(os.path.join(ROOT, "scenes", part.lower() + ".py")).read()
i = src.index("PLAN = ["); j = src.index("\n]", i)
plan = re.findall(r'\("(S\d+)",\s*(\d+),\s*([\d.]+),', src[i:j])
plan = [(s, int(p), float(d)) for s, p, d in plan]
N = int(round(total * FPS))
ends = ends + [total] if len(ends) == max(p for _, p, _ in plan) - 1 else ends
bounds = [0.0] + ends
assert len(bounds) - 1 == max(p for _, p, _ in plan), (len(bounds), max(p for _, p, _ in plan))
out = []; frame_cursor = 1; t_cursor = 0.0
for para in range(1, len(bounds)):
    shots = [(s, d) for s, p, d in plan if p == para]
    t0, t1 = bounds[para - 1], bounds[para]
    tot = sum(d for _, d in shots)
    for s, d in shots:
        t_cursor += (t1 - t0) * d / tot
        end_frame = int(round(t_cursor * FPS)) if not (para == len(bounds) - 1 and s == shots[-1][0]) else N
        out.append(dict(shot=s, para=para, start=frame_cursor, frames=end_frame - frame_cursor + 1))
        frame_cursor = end_frame + 1
assert out[-1]["start"] + out[-1]["frames"] - 1 == N, "frames must add up to the VO"
os.makedirs(os.path.join(ROOT, "vo"), exist_ok=True)
json.dump(dict(fps=FPS, frames_total=N, vo_seconds=total, shots=out), open(os.path.join(ROOT, "vo", part + "_timing.json"), "w"), indent=1)
for o in out:
    print(o["shot"], o["para"], o["start"], o["frames"], round(o["frames"] / FPS, 2))
print("TOTAL", sum(o["frames"] for o in out), N)
