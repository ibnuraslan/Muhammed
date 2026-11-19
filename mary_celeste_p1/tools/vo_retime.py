"""Re-time Part 1 shots to the voice-over from word timestamps (faster-whisper, vo/words.json).

    python3 tools/vo_retime.py [vo/words.json] [out/vo_timings.json] [audio_seconds]
Script words are aligned to the recognised words (difflib); each shot cuts LEAD s before its first word, so pauses
(the planned silence beats) stay on the shot they follow. Cuts snap to whole frames; the last shot runs to the end of
the audio plus TAIL. Durations are written as frames/24 so the cumulative timeline matches the audio exactly."""
import os, sys, json, re, difflib
P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(P1, "comp"), os.path.join(P1, "tools")]
import storyboard as SB

FPS, LEAD, TAIL = 24, 0.125, 1.0
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def main():
    a = sys.argv[1:]
    words = json.load(open(a[0] if a else os.path.join(P1, "vo", "words.json")))
    out = a[1] if len(a) > 1 else os.path.join(P1, "out", "vo_timings.json")
    audio = float(a[2]) if len(a) > 2 else words[-1]["e"]
    shots = SB.shots()
    script = [(i, norm(w)) for i, s in enumerate(shots) for w in s["vo"].split()]
    asr = [norm(w["w"]) for w in words]
    sm = difflib.SequenceMatcher(None, [w for _, w in script], asr, autojunk=False)
    m = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            m[blk.a + k] = blk.b + k
    print(f"matched {len(m)}/{len(script)} script words to {len(asr)} spoken words")
    starts = []; pos = 0
    for i, s in enumerate(shots):
        n = len(s["vo"].split()); idx = list(range(pos, pos + n)); pos += n
        hit = [(k - idx[0], m[k]) for k in idx if k in m]
        if not hit:
            raise SystemExit(f"{s['id']}: no words matched")
        off, j = hit[0]                                  # first matched word, minus ~0.3 s per word missed before it
        starts.append(max(0.0, words[j]["s"] - 0.3 * off))
    starts[0] = 0.0
    cuts = [0] + [max(int(round((t - LEAD) * FPS)), 0) for t in starts[1:]] + [int(round((audio + TAIL) * FPS))]
    tim = {}
    for i, s in enumerate(shots):
        n = cuts[i + 1] - cuts[i]
        if n < 12:
            print("WARNING short shot", s["id"], n, "frames")
        tim[s["id"]] = round(n / FPS, 6)
        print(f"{s['id']:5s} {cuts[i] / FPS:7.2f}  {n / FPS:5.2f}s  (plan {s['dur']:.2f})  {s['vo']}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(tim, open(out, "w"), indent=1)
    print("total", cuts[-1] / FPS, "s ->", out)


if __name__ == "__main__":
    main()
