"""Burn the script captions into a video (all films), in the user's 'mystery' style (callout.caption):
small Courier-like white text with a soft shadow, one line, centred, baseline ~6% above the bottom edge.

  python scenes/caption_burnin.py <in.mp4> <captions.srt> <out.mp4> [--fade 0.12]

The SRT holds the exact script text, one line per cue, timed to the VO (word times from the VO alignment).
Audio is copied unchanged. Long cues are not wrapped: split them into separate SRT cues instead (one line each)."""
import os, re, sys, subprocess, json
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import callout


def parse_srt(path):
    cues = []
    blk = re.split(r"\n\s*\n", open(path, encoding="utf-8-sig").read().strip())
    ts = lambda s: sum(float(x) * m for x, m in zip(s.replace(",", ".").split(":"), (3600, 60, 1)))
    for b in blk:
        lines = [l for l in b.splitlines() if l.strip()]
        for i, l in enumerate(lines):
            if "-->" in l:
                a, z = [t.strip() for t in l.split("-->")]
                cues.append((ts(a), ts(z.split()[0]), " ".join(lines[i + 1:]).strip()))
                break
    return cues


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]; n, d = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(n) / float(d)


def burn(src, srt, dst, fade=0.12):
    W, H, fps = probe(src); cues = parse_srt(srt)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-i", src, "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-c:a", "copy", "-movflags", "+faststart", dst], stdin=subprocess.PIPE)
    i = 0; fsz = W * H * 3
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz:
            break
        t = i / fps; im = Image.frombytes("RGB", (W, H), buf)
        for a, z, text in cues:
            if a <= t < z:
                al = min(1.0, (t - a) / fade, (z - t) / fade) if fade > 0 else 1.0
                im = callout.caption(im, text, alpha=max(0.0, al))
                break
        enc.stdin.write(im.tobytes()); i += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print("[captions]", dst, i, "frames,", len(cues), "cues")


if __name__ == "__main__":
    a = sys.argv[1:]
    burn(a[0], a[1], a[2], float(a[a.index("--fade") + 1]) if "--fade" in a else 0.12)
