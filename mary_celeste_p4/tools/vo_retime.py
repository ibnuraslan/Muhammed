"""Re-time Part 4 shots to the voice-over (same method as Part 1): script words aligned to the recognised words
(difflib); each shot cuts LEAD s before its first word so pauses stay on the shot they follow; cuts on whole frames;
the last shot runs to the end of the audio plus TAIL.   python3 tools/vo_retime.py vo/words.json vo/vo_timings.json AUDIO_S"""
import os, sys, json, re, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots_vo import SHOTS
FPS, LEAD, TAIL = 24, 0.125, 1.0
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
words = json.load(open(sys.argv[1])); out = sys.argv[2]; audio = float(sys.argv[3])
script = [(i, norm(w)) for i, (_, v, _) in enumerate(SHOTS) for w in v.split()]
asr = [norm(w["w"]) for w in words]
sm = difflib.SequenceMatcher(None, [w for _, w in script], asr, autojunk=False)
m = {}
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        m[blk.a + k] = blk.b + k
print(f"matched {len(m)}/{len(script)} script words to {len(asr)} spoken words")
starts = []; pos = 0
for sid, v, _ in SHOTS:
    n = len(v.split()); idx = list(range(pos, pos + n)); pos += n
    hit = [(k - idx[0], m[k]) for k in idx if k in m]
    if not hit:
        raise SystemExit(f"{sid}: no words matched")
    off, j = hit[0]
    starts.append(max(0.0, words[j]["s"] - 0.3 * off))
starts[0] = 0.0
cuts = [0] + [max(int(round((t - LEAD) * FPS)), 0) for t in starts[1:]] + [int(round((audio + TAIL) * FPS))]
tim = {}
for i, (sid, v, _) in enumerate(SHOTS):
    n = cuts[i + 1] - cuts[i]
    if n < 24:
        print("WARNING short shot", sid, n, "frames")
    tim[sid] = dict(start=cuts[i], frames=n, seconds=round(n / FPS, 4))
    print(f"{sid} {cuts[i] / FPS:7.2f}  {n / FPS:5.2f}s  {v}")
json.dump(tim, open(out, "w"), indent=1)
print("total", cuts[-1] / FPS, "s ->", out)
