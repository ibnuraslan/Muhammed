"""Transparent captions-only overlay for the c5_17 patch window: master frames 7551-7875 (325 frames), frame 1 = 7551.
Same caption layer as the burned-in MP4 (callout.caption_layer, Courier Prime, soft shadow), hard cut, ProRes 4444 + alpha."""
import sys, os, subprocess, numpy as np
sys.path.insert(0, os.path.join(sys.argv[1], "scenes"))
import callout
from caption_burnin import parse_srt
srt, out = sys.argv[2:4]; W, H = 1920, 816; A, B = 7551, 7875
cues = parse_srt(srt); cache = {}; log = []
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-framerate", "24", "-i", "-",
    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-vendor", "apl0", "-r", "24", out], stdin=subprocess.PIPE)
empty = bytes(W * H * 4)
for n in range(A, B + 1):
    t = (n - 1) / 24; hit = None
    for k, (a, z, text) in enumerate(cues, 1):
        if a <= t < z: hit = (k, text); break
    if hit:
        if hit[1] not in cache: cache[hit[1]] = callout.caption_layer(W, H, hit[1]).tobytes()
        enc.stdin.write(cache[hit[1]]); log.append(hit[0])
    else:
        enc.stdin.write(empty); log.append(0)
enc.stdin.close(); assert enc.wait() == 0
import itertools
print("frames", len(log)); f = A
for k, g in itertools.groupby(log):
    m = len(list(g)); print(f"  local {f-A+1:3d}-{f-A+m:3d} (master {f}-{f+m-1}): " + (f"cue #{k}" if k else "empty")); f += m
