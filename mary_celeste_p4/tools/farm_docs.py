"""README.txt (farm notes) and SHOTLIST.csv / SHOTLIST.txt (CapCut timings) for the Part 4 farm package.
    python3 tools/farm_docs.py <PKG>     (timings: vo/vo_timings.json)   (adapted from Part 1's farm_docs.py)"""
import os, sys, json, csv
P4 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P4, "tools"))
from shots_vo import SHOTS
FPS = 24
MIN_PER_FRAME = float(os.environ.get("FARM_MIN_PER_FRAME", "0"))


def tc(f):
    s, f = divmod(int(f), FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def main(pkg):
    tim = json.load(open(os.path.join(P4, "vo", "vo_timings.json")))
    rows = []
    for sid, vo, card in SHOTS:
        t = tim[sid]; st, n = t["start"], t["frames"]
        rows.append(dict(shot=sid, start=tc(st), end=tc(st + n), n=n, dur=round(n / FPS, 3), card=card, vo=vo))
    total = sum(r["n"] for r in rows)
    with open(os.path.join(pkg, "SHOTLIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["shot", "start", "end", "seconds", "frames", "card / label (add in CapCut)", "voice-over"])
        for r in rows:
            w.writerow([r["shot"], r["start"], r["end"], r["dur"], r["n"], r["card"], r["vo"]])
    with open(os.path.join(pkg, "SHOTLIST.txt"), "w") as fh:
        fh.write(f"Mary Celeste - Part 4 - shot list for CapCut ({len(rows)} shots, {tc(total)} = {total / FPS:.2f} s, 24 fps, mm:ss:ff)\n")
        fh.write("Timed to vo/MaryCeleste_Part4_VO.mp3 (Edmund, 2:43.6) from word timestamps; the last shot holds 1 s past the voice.\n")
        fh.write("Import each shot's frames as a PNG sequence at 24 fps and lay them end to end from 00:00:00; the starts below follow.\n")
        fh.write("Cards, labels and captions are NOT burned in: add them in CapCut where noted.\n\n")
        for r in rows:
            fh.write(f"{r['shot']}  {r['start']} - {r['end']}  ({r['dur']:.2f} s, {r['n']} fr)\n")
            if r["card"]:
                fh.write(f"      {r['card']}\n")
            fh.write(f"      VO: {r['vo']}\n")
    est = ""
    if MIN_PER_FRAME:
        est = (f"Estimated from 50%-resolution test renders on a 4-core CPU box at these settings: about {MIN_PER_FRAME:.0f} min per frame at 2560x1440.\n"
               f"Total {total} frames, about {total * MIN_PER_FRAME / 60:.0f} CPU-box hours; a 32+ core farm node is roughly 6-10x faster.\n")
    with open(os.path.join(pkg, "README.txt"), "w") as fh:
        fh.write(f"""MARY CELESTE - PART 4 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles, CPU (GPU is fine: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera and frame range set
             textures/             shared images (2K max), relative paths (//../textures/...); fonts packed
             SHOTLIST.csv / .txt   timings for the edit
Nothing to bake: ocean, ship motion, people and camera are keyframed or computed per frame. No simulation caches.
Render each .blend's full frame range as set in the file (start 1, end below).

{est}
Shot   frames   seconds
""")
        for r in rows:
            fh.write(f"{r['shot']:6s} 1-{r['n']:<6d} {r['dur']:.2f}\n")
        fh.write(f"\nTotal: {total} frames, {total / FPS:.2f} s\n")
    print("docs:", len(rows), "shots", total, "frames", round(total / FPS, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
