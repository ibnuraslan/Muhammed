"""Cut each chapter's shots at the word where its line starts. -> vo/ch_timing.json"""
import json, re, sys, os, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chapter_shots import CH, LEAD
from align import norm_tokens, canon
FPS = 24
W = json.load(open(os.path.join(os.path.dirname(__file__), "..", "vo", "ch_words.json")))
out = {}
for c, shots in CH.items():
    words = W[str(c)]["words"]; dur = W[str(c)]["dur"]
    toks = [w[0] for w in words]
    starts = []
    pos = 0
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
        print(f"ch{c} {label[:34]:34s} anchor '{anchor[:30]}' match {sc}/{len(a)} at {t:7.2f}  ({' '.join(toks[idx:idx+5])})")
    ends = starts[1:] + [dur + 1.5]
    bounds = [0] + [round((LEAD + s) * FPS) for s in starts[1:]] + [round((LEAD + dur + 1.5) * FPS)]
    out[c] = [dict(set=sh[0], move=sh[1], label=sh[2], name=f"c{c}_{k+1:02d}_{sh[0]}_{sh[1]}", frames=bounds[k + 1] - bounds[k]) for k, sh in enumerate(shots)]
    print(f"ch{c}: {len(shots)} shots, {bounds[-1]} frames = {bounds[-1]/FPS:.1f} s; min shot {min(o['frames'] for o in out[c])/FPS:.2f} s")
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "vo", "ch_timing.json"), "w"), indent=1)
