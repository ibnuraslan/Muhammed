"""Cut each Ch4-5 shot at the word where its line starts. -> vo/ch45_timing.json (same method as time_chapters.py)."""
import json, os, sys, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chapter_shots_ch45 import CH, LEAD
from align import norm_tokens, canon
FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, "..", "vo", "ch45_words.json")))
out = {}
for c, shots in CH.items():
    words = W[str(c)]["words"]; dur = W[str(c)]["dur"]
    toks = [w[0] for w in words]
    starts = []; pos = 0
    for k, (_, _, label, anchor) in enumerate(shots):
        a = [canon(t) for t in norm_tokens(anchor)]
        best = None
        for i in range(pos, len(toks)):
            win = toks[i:i + len(a) + 2]
            sm = difflib.SequenceMatcher(None, a, win)
            m = sm.get_matching_blocks()
            score = sum(b.size for b in m)
            first = next((b.b for b in m if b.size), 0)
            if best is None or score > best[0]:
                best = (score, i + first)
            if score == len(a):
                break
        sc, idx = best
        t = 0.0 if k == 0 else max(0.0, words[idx][1] - 0.08)
        starts.append(t); pos = idx + 1
        print(f"ch{c} {label[:40]:40s} anchor '{anchor[:26]}' {sc}/{len(a)} @{t:7.2f}  ({' '.join(toks[idx:idx+5])})")
    bounds = [0] + [round((LEAD + s) * FPS) for s in starts[1:]] + [round((LEAD + dur + 1.5) * FPS)]
    out[c] = [dict(set=sh[0], move=sh[1], label=sh[2],
                   name=f"c{c}_{k+1:02d}_{sh[0]}_{sh[1]}", frames=bounds[k + 1] - bounds[k])
              for k, sh in enumerate(shots)]
    lens = [o["frames"] / FPS for o in out[c]]
    print(f"ch{c}: {len(shots)} shots, {bounds[-1]} frames = {bounds[-1]/FPS:.1f}s; "
          f"shot len min {min(lens):.1f}s max {max(lens):.1f}s")
json.dump(out, open(os.path.join(HERE, "..", "vo", "ch45_timing.json"), "w"), indent=1)
