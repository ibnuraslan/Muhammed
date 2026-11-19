"""Re-time Part 5 shots to the voice-over from word timestamps (faster-whisper small.en -> vo/words.json).

    python3 tools/vo_retime.py [vo/words.json] [vo/vo_timings.json] [audio_seconds]
Same rules as Part 1 (mary_celeste_p1/tools/vo_retime.py): script words are aligned to the spoken words (difflib);
each shot cuts LEAD s before its first word, so the pauses (the silence beats) stay on the shot they follow; cuts snap to
whole frames and durations are frames/24, so the timeline matches the audio exactly.
Shots with no words (S28, the empty sea) start BEAT s after the previous line ends; the last shot holds TAIL s past
the end of the audio (the ending stays on the empty sea)."""
import os, sys, json, re, difflib
P5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P5)
from shots import SHOTS

FPS, LEAD, BEAT, TAIL = 24, 0.125, 1.6, 8.0
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def main():
    a = sys.argv[1:]
    words = json.load(open(a[0] if a else os.path.join(P5, "vo", "words.json")))
    out = a[1] if len(a) > 1 else os.path.join(P5, "vo", "vo_timings.json")
    audio = float(a[2]) if len(a) > 2 else words[-1]["e"]
    script = [(i, norm(w)) for i, s in enumerate(SHOTS) for w in s[2].split()]
    asr = [norm(w["w"]) for w in words]
    sm = difflib.SequenceMatcher(None, [w for _, w in script], asr, autojunk=False)
    m = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            m[blk.a + k] = blk.b + k
    print(f"matched {len(m)}/{len(script)} script words to {len(asr)} spoken words")
    starts = []; pos = 0; last_end = 0.0
    for i, s in enumerate(SHOTS):
        n = len(s[2].split()); idx = list(range(pos, pos + n)); pos += n
        hit = [(k - idx[0], m[k]) for k in idx if k in m]
        if not n:
            starts.append(last_end + BEAT); continue
        if not hit:
            raise SystemExit(f"{s[0]}: no words matched")
        off, j = hit[0]
        starts.append(max(0.0, words[j]["s"] - 0.3 * off))
        last_end = words[hit[-1][1]]["e"]
    starts[0] = 0.0
    cuts = [0] + [max(int(round((t - LEAD) * FPS)), 0) for t in starts[1:]] + [int(round((audio + TAIL) * FPS))]
    tim = {}
    for i, s in enumerate(SHOTS):
        n = cuts[i + 1] - cuts[i]
        if n < 12:
            print("WARNING short shot", s[0], n, "frames")
        tim[s[0]] = round(n / FPS, 6)
        print(f"{s[0]:5s} {cuts[i] / FPS:7.2f}  {n / FPS:5.2f}s  {s[2]}")
    json.dump(tim, open(out, "w"), indent=1)
    print("total", cuts[-1] / FPS, "s ->", out)


if __name__ == "__main__":
    main()
