"""Find a VO's paragraph ends: silence detection on the recording, then a DP that picks one pause per paragraph
boundary so the time each paragraph gets is closest to its share of the text (by letters). Prints the paragraph
end times to pass to vo_timing.py, with each paragraph's sentence count vs pauses inside it as a check.

    python3 tools/vo_align.py ../vo/MUMMY_P2_VO.txt ../vo_audio/MUMMY_P2_VO.mp3
"""
import sys, re, subprocess
txt, mp3 = sys.argv[1], sys.argv[2]
paras = [p.strip() for p in open(txt).read().split("\n\n") if p.strip()]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3]))
log = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
gaps = [(a, b) for a, b in zip(st, en) if a > 0.3 and b < dur - 0.05]
w = [len(re.sub(r"[^A-Za-z0-9]", "", p)) for p in paras]
speech = dur - sum(b - a for a, b in gaps)
def speech_time(t):   # seconds of speech before t
    return t - sum(min(b, t) - a for a, b in gaps if a < t)
P = len(paras); G = len(gaps)
cum = [sum(w[:i + 1]) / sum(w) * speech for i in range(P)]
sn = [len(re.findall(r"[.!?\u2019\"]?[.!?](\s|$)", p_)) or 1 for p_ in paras]
def pen(i, inside):   # a paragraph of k sentences has at least k-1 pauses inside it (commas can add more)
    need = sn[i] - 1
    return 40.0 * (need - inside) if inside < need else 2.0 * (inside - need)
INF = 1e18
# dp[i][g]: paragraph i ends at gap g
best = [[INF] * G for _ in range(P - 1)]; back = [[-1] * G for _ in range(P - 1)]
for g in range(G):
    best[0][g] = (speech_time(gaps[g][0]) - cum[0]) ** 2 - 4 * (gaps[g][1] - gaps[g][0]) + pen(0, g)
for i in range(1, P - 1):
    for g in range(G):
        cost = (speech_time(gaps[g][0]) - cum[i]) ** 2 - 4 * (gaps[g][1] - gaps[g][0])
        for h in range(g):
            v = best[i - 1][h] + cost + pen(i, g - h - 1)
            if v < best[i][g]:
                best[i][g], back[i][g] = v, h
g = min(range(G), key=lambda g: best[P - 2][g] + pen(P - 1, G - g - 1)); picks = [g]
for i in range(P - 2, 0, -1):
    g = back[i][g]; picks.append(g)
picks = picks[::-1]
ends = [round((gaps[g][0] + gaps[g][1]) / 2, 2) for g in picks]
prev = -1
for i, p in enumerate(paras):
    gi = picks[i] if i < P - 1 else G
    inside = gi - prev - 1; prev = gi
    sents = len(re.findall(r"[.!?](\s|$)", p))
    print(f"{i + 1:2d} end {ends[i] if i < P - 1 else dur:7.2f}  sentences {sents} pauses-inside {inside}  gap {gaps[picks[i]][1] - gaps[picks[i]][0]:.2f}" if i < P - 1 else f"{i + 1:2d} end {dur:7.2f}  sentences {sents} pauses-inside {inside}", "|", p[:60])
print("ENDS", ",".join(str(e) for e in ends), "DUR", round(dur, 3))
