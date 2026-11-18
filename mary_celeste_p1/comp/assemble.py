"""Assemble Part 1: rendered shot frames -> cards (shared callout.py: people slide in from the right, places from the
left, first appearance only) + burned-in Courier Prime captions (the script, verbatim, one line per cue) -> silent MP4.

    python3 comp/assemble.py [--out out/part1.mp4] [--size 2560x1440] [--only S01,S02]
Frames: out/frames/<id>/f0001.png ... (run_anim.py). A shot with missing frames is reported and holds its last frame.
Cards: 4.0 s from the start of their shot (they may run on into the next shot). Captions: each shot's words, split
into cues of <= 58 characters, timed by word count across the shot."""
import os, sys, ast, subprocess, glob
from PIL import Image

P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P1, "comp")); sys.path.insert(0, os.path.join(P1, "tools"))
import callout as CO
import storyboard as SB

FPS = 24
CARD_DUR = 4.0


def cues_for(text, t0, dur, maxc=58):
    words = text.split(); out = []; cur = []
    for w in words:
        if cur and len(" ".join(cur + [w])) > maxc:
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    n = sum(len(c) for c in out); t = t0
    res = []
    for c in out:
        d = dur * len(c) / max(n, 1); res.append((t, t + d, " ".join(c))); t += d
    return res


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    W, H = (int(v) for v in opt("--size", "2560x1440").split("x"))
    only = set(opt("--only", "").split(",")) - {""}
    out = opt("--out", os.path.join(P1, "out", "part1.mp4"))
    shots = [s for s in SB.shots() if not only or s["id"] in only]
    # timeline
    t = 0.0; cards = []; cues = []
    for s in shots:
        s["t0"] = t
        if s["card"]:
            kind, rest = s["card"].split(":", 1); name, role = rest.split("|")
            ph = SB.photo_for(name)
            if ph is not None:                               # cards only with a real free-licence photo
                cards.append(dict(kind=kind, name=name, role=role, photo=ph, t0=t))
            else:
                print("card skipped (no photo):", name)
        cues += cues_for(s["vo"], t, s["dur"])
        t += s["dur"]
    total = t
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", "-an", out], stdin=subprocess.PIPE)
    fi = 0
    for s in shots:
        n = int(round(s["dur"] * FPS))
        frames = sorted(glob.glob(os.path.join(P1, "out", "frames", s["id"], "f*.png")))
        if len(frames) < n:
            print(f"{s['id']}: {len(frames)}/{n} frames")
        last = None
        for i in range(n):
            if i < len(frames):
                last = Image.open(frames[i]).convert("RGB")
                if last.size != (W, H):
                    last = last.resize((W, H), Image.LANCZOS)
            im = last if last is not None else Image.new("RGB", (W, H))
            tt = fi / FPS
            for c in cards:
                if c["t0"] <= tt < c["t0"] + CARD_DUR:
                    fn = CO.person_right if c["kind"] == "person" else CO.place_left
                    im = fn(im, c["photo"], c["name"], c["role"], slide=CO.card_slide(tt - c["t0"], CARD_DUR))
            for (c0, c1, txt) in cues:
                if c0 <= tt < c1:
                    im = CO.caption(im, txt)
            enc.stdin.write(im.tobytes()); fi += 1
    enc.stdin.close(); enc.wait()
    print("wrote", out, fi, "frames", round(total, 2), "s")


if __name__ == "__main__":
    main()
