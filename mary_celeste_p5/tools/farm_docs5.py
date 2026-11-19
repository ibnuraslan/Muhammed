"""README.txt (farm notes) and SHOTLIST.csv / SHOTLIST.txt (CapCut timings) for the Part 5 RenderStreet package.

    python3 tools/farm_docs5.py <PKG> [vo/vo_timings.json]
Frame counts: round(seconds * 24), the same as tools/run_anim5.py."""
import os, sys, json, csv
P5 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P5)
from shots import SHOTS

FPS = 24


def tc(t):
    f = int(round(t * FPS)); s, f = divmod(f, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def rows(tim):
    out = []; t = 0.0
    for sid, scene, vo, see, cam, sfx, card in SHOTS:
        n = int(round(float(tim[sid]) * FPS))
        c = f"{card[1]} - {card[2]} ({'person, slides in from the right' if card[0] == 'person' else 'place, slides in from the left'})" if card else ""
        out.append(dict(shot=sid, n=n, start=tc(t), end=tc(t + n / FPS), t0=t, dur=n / FPS, card=c, vo=vo, see=see, sfx=sfx))
        t += n / FPS
    return out, t


def main(pkg, tim_path):
    tim = json.load(open(tim_path))
    R, total = rows(tim)
    nfr = sum(r["n"] for r in R)
    os.makedirs(pkg, exist_ok=True)
    with open(os.path.join(pkg, "SHOTLIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["shot", "start (mm:ss:ff)", "end", "seconds", "frames", "card (add in CapCut)", "caption = voice-over (Courier Prime)", "SFX"])
        for r in R:
            w.writerow([r["shot"], r["start"], r["end"], f"{r['dur']:.3f}", r["n"], r["card"], r["vo"], r["sfx"]])
    with open(os.path.join(pkg, "SHOTLIST.txt"), "w") as fh:
        fh.write(f"Mary Celeste - Part 5 - shot list for CapCut ({len(R)} shots, {tc(total)} = {total:.2f} s, 24 fps, mm:ss:ff)\n")
        fh.write("Voice-over: MaryCeleste_Part5_VO.mp3 starts at 00:00:00. Each shot cuts just before its first word, so the\n")
        fh.write("silence beats stay on the shot they follow; the last shot holds the empty sea about 8 s past the end of the voice.\n")
        fh.write("Import each shot's frames (frames/<shot>/<shot>_####.png) as a PNG sequence at 24 fps and lay them end to end.\n")
        fh.write("Cards and Courier Prime captions are NOT burned in: add them in CapCut at the times below.\n\n")
        for r in R:
            fh.write(f"{r['shot']:5s} {r['start']} - {r['end']}  ({r['dur']:.2f} s, {r['n']} fr)\n")
            if r["card"]:
                fh.write(f"      CARD:    {r['card']}\n")
            if r["vo"]:
                fh.write(f"      CAPTION: {r['vo']}\n")
            fh.write(f"      SFX:     {r['sfx']}\n")
    with open(os.path.join(pkg, "README.txt"), "w") as fh:
        fh.write(f"""MARY CELESTE - PART 5 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles (CPU or GPU: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera and frame range set
             textures/             shared images, relative paths (//../textures/...), 2K max; fonts packed
             SHOTLIST.csv / .txt   timings for the edit
Nothing to bake: sea, ships, boats and cameras are keyframed or computed per frame. No simulation caches.
Render each .blend's full frame range as set in the file (start 1, end below).

Shot   frames   seconds
""")
        for r in R:
            fh.write(f"{r['shot']:6s} 1-{r['n']:<6d} {r['dur']:.2f}\n")
        fh.write(f"\nTotal: {nfr} frames, {total:.2f} s\n")
    print("docs:", len(R), "shots", nfr, "frames", round(total, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(P5, "vo", "vo_timings.json"))
