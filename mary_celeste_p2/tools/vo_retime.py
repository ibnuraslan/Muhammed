"""Re-time Part 2 shots to the voice-over from word timestamps (faster-whisper small.en -> vo/words.json).
Same method as Part 1 (claude/mary-celeste-p1 tools/vo_retime.py): script words are aligned to the recognised words
(difflib); each shot cuts LEAD s before its first word, so pauses (the planned silence beat before shot 27) stay on the
shot they follow. Cuts snap to whole frames; the last shot runs to the end of the audio plus TAIL.

    python3 tools/vo_retime.py [vo/words.json] [vo/vo_timings.json] [audio_seconds]"""
import os, sys, json, re, difflib
P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P2)
from shots import SHOTS

FPS, LEAD, TAIL = 24, 0.125, 1.0
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def main():
    a = sys.argv[1:]
    words = json.load(open(a[0] if a else os.path.join(P2, "vo", "words.json")))
    out = a[1] if len(a) > 1 else os.path.join(P2, "vo", "vo_timings.json")
    audio = float(a[2]) if len(a) > 2 else 151.64
    script = [(i, norm(w)) for i, s in enumerate(SHOTS) for w in s[2].split()]
    asr = [norm(w["w"]) for w in words]
    sm = difflib.SequenceMatcher(None, [w for _, w in script], asr, autojunk=False)
    m = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            m[blk.a + k] = blk.b + k
    print(f"matched {len(m)}/{len(script)} script words to {len(asr)} spoken words")
    starts = []; pos = 0
    for s in SHOTS:
        n = len(s[2].split()); idx = list(range(pos, pos + n)); pos += n
        hit = [(k - idx[0], m[k]) for k in idx if k in m]
        if not hit:
            raise SystemExit(f"{s[0]}: no words matched")
        off, j = hit[0]
        starts.append(max(0.0, words[j]["s"] - 0.3 * off))
    starts[0] = 0.0
    cuts = [0] + [max(int(round((t - LEAD) * FPS)), 0) for t in starts[1:]] + [int(round((audio + TAIL) * FPS))]
    tim = {}; rows = []
    for i, s in enumerate(SHOTS):
        n = cuts[i + 1] - cuts[i]
        if n < 24:
            print("WARNING short shot", s[0], n, "frames")
        tim[s[0]] = dict(start_frame=cuts[i] + 1, frames=n, start=round(cuts[i] / FPS, 4), dur=round(n / FPS, 4))
        print(f"{s[0]}  {cuts[i] / FPS:7.2f}  {n / FPS:5.2f}s  {s[2]}")
    json.dump(tim, open(out, "w"), indent=1)
    print("total", cuts[-1] / FPS, "s ->", out)


if __name__ == "__main__":
    main()
