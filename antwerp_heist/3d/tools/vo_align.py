"""Align each VO line (vo/ANTWERP_Px_VO.txt, one line per row) to the narration mp3: silences from ffmpeg
silencedetect, line boundaries estimated by character share and snapped (monotonic DP) to the nearest pause.
Writes timing/Px_lines.json: [{line, start, end}] (seconds).     python3 tools/vo_align.py P1"""
import os, sys, re, json, subprocess
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PART = sys.argv[1]; n = PART[1:]
mp3 = os.path.join(D, "..", "..", "antwerp_vo", f"ANTWERP_P{n}_VO.mp3")
txt = os.path.join(D, "..", "vo", f"ANTWERP_P{n}_VO.txt")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]))
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
sil = [((a + b) / 2, b - a) for a, b in zip(st, en)]          # (mid, length)
lines = [l.strip() for l in open(txt) if l.strip()]
speech0 = en[0] if st and st[0] < 0.05 else 0.0
speech1 = st[-1] if st and abs(en[-1] - dur) < 0.2 else dur
w = [len(l) + 12 for l in lines]                               # + a little per-line overhead
tot = sum(w); est = []; acc = 0
for x in w[:-1]:
    acc += x; est.append(speech0 + (speech1 - speech0) * acc / tot)
# DP: pick a pause for each boundary, monotonic, minimising |pause - estimate| minus a bonus for long pauses
import math
cand = [m for m, L in sil if speech0 + 0.5 < m < speech1 - 0.5]
L_ = {m: L for m, L in sil}
INF = 1e18
best = [[INF] * len(cand) for _ in est]; back = [[-1] * len(cand) for _ in est]
for i, e in enumerate(est):
    for j, c in enumerate(cand):
        cost = abs(c - e) - 1.5 * min(L_[c], 1.2)
        if i == 0:
            best[i][j] = cost
        else:
            pj = min(range(j), key=lambda q: best[i - 1][q], default=None)
            if pj is None or best[i - 1][pj] >= INF:
                continue
            best[i][j] = best[i - 1][pj] + cost; back[i][j] = pj
j = min(range(len(cand)), key=lambda q: best[-1][q]); picks = []
for i in range(len(est) - 1, -1, -1):
    picks.append(cand[j]); j = back[i][j]
picks = picks[::-1]
bounds = [0.0] + picks + [dur]
out = [dict(line=k + 1, start=round(bounds[k], 3), end=round(bounds[k + 1], 3), text=lines[k][:60]) for k in range(len(lines))]
os.makedirs(os.path.join(D, "timing"), exist_ok=True)
json.dump(dict(part=PART, duration=dur, lines=out), open(os.path.join(D, "timing", f"{PART}_lines.json"), "w"), indent=1)
for o in out:
    print(f"{o['line']:>2} {o['start']:7.2f} {o['end']:7.2f} {o['end'] - o['start']:5.2f}  {o['text']}")
