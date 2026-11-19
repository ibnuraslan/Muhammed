"""Re-time Part 3 shots to the voice-over from word timestamps (vo/words.json, faster-whisper), as Part 1 does.

    python3 tools/vo_retime.py [vo/words.json] [vo/vo_timings.json] [audio_seconds]
Script words are aligned to the spoken words (difflib); each shot cuts LEAD s before its first word, so the pauses
(silence beats) stay on the shot they follow. Cuts snap to whole frames; the last shot runs to the end of the audio
plus TAIL. Durations are frames/24, so the cumulative timeline matches the audio exactly."""
import os, sys, json, re, difflib
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import board

FPS, LEAD, TAIL = 24, 0.125, 1.0
NUM = {"seventeen": "1", "hundred": "700", "thirteenth": "13"}       # how the recogniser writes these
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def main():
    a = sys.argv[1:]
    words = json.load(open(a[0] if a else os.path.join(HERE, "vo", "words.json")))
    out = a[1] if len(a) > 1 else os.path.join(HERE, "vo", "vo_timings.json")
    audio = float(a[2]) if len(a) > 2 else words[-1]["e"]
    shots = board.shots_meta()
    script = [(i, norm(NUM.get(norm(w), w))) for i, s in enumerate(shots) for w in s["vo"].split()]
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
            raise SystemExit(f"{s['sid']}: no words matched")
        off, j = hit[0]
        starts.append(max(0.0, words[j]["s"] - 0.3 * off))
    starts[0] = 0.0
    cuts = [0] + [max(int(round((t - LEAD) * FPS)), 0) for t in starts[1:]] + [int(round((audio + TAIL) * FPS))]
    tim = {}
    for i, s in enumerate(shots):
        n = cuts[i + 1] - cuts[i]
        if n < 24:
            print("WARNING short shot", s["sid"], n, "frames")
        tim[s["sid"]] = round(n / FPS, 6)
        print(f"{s['sid']:7s} {cuts[i] / FPS:7.2f}  {n / FPS:5.2f}s  (plan {s['dur']:.2f})  {s['vo']}")
    json.dump(tim, open(out, "w"), indent=1)
    print("total", cuts[-1] / FPS, "s ->", out)


if __name__ == "__main__":
    main()
