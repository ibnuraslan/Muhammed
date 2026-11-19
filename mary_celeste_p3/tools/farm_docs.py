"""README.txt (farm notes) and SHOTLIST.csv / SHOTLIST.txt (CapCut timings) for the Part 3 farm package.
    python3 tools/farm_docs.py <PKG>       (durations from vo/vo_timings.json; frames = round(seconds * 24))"""
import os, sys, json, csv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import board
FPS = 24
MIN_PER_FRAME = float(os.environ.get("FARM_MIN_PER_FRAME", "0"))


def tc(t):
    f = int(round(t * FPS)); s, f = divmod(f, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def main(pkg):
    tim = json.load(open(os.path.join(HERE, "vo", "vo_timings.json")))
    rows = []; t = 0.0
    for s in board.shots_meta():
        n = int(round(float(tim[s["sid"]]) * FPS))
        rows.append(dict(shot=s["sid"], frames=f"1-{n}", n=n, start=tc(t), end=tc(t + n / FPS), dur=round(n / FPS, 3),
                         size=s["size"], action=s["action"], sfx=s["sfx"], vo=s["vo"]))
        t += n / FPS
    total = sum(r["n"] for r in rows)
    with open(os.path.join(pkg, "SHOTLIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["shot", "start", "end", "seconds", "frames", "size", "action", "sfx", "voice-over (caption text)"])
        for r in rows:
            w.writerow([r["shot"], r["start"], r["end"], r["dur"], r["n"], r["size"], r["action"], r["sfx"], r["vo"]])
    with open(os.path.join(pkg, "SHOTLIST.txt"), "w") as fh:
        fh.write(f"Mary Celeste - Part 3 - shot list for CapCut ({len(rows)} shots, {tc(t)} = {round(t, 2)} s, 24 fps, mm:ss:ff)\n")
        fh.write("Timed to vo/MaryCeleste_Part3_VO.mp3 (2:18.8): each shot cuts just before its first word, pauses stay on the shot before.\n")
        fh.write("Import each shot's frames as a PNG sequence at 24 fps and lay them end to end; the start times below follow.\n")
        fh.write("No cards or captions are burned in. Person/place cards to add in CapCut: DAVID MOREHOUSE (Captain, Dei Gratia)\n"
                 "on p3_01; GIBRALTAR + date DECEMBER 13, 1872 on p3_16; FREDERICK SOLLY FLOOD (Attorney General, Gibraltar) on p3_26.\n\n")
        for r in rows:
            fh.write(f"{r['shot']:7s} {r['start']} - {r['end']}  ({r['dur']:.2f} s, {r['n']} fr)  {r['size']}\n")
            fh.write(f"        VO:   {r['vo']}\n        SFX:  {r['sfx']}\n")
    est = ""
    if MIN_PER_FRAME:
        est = (f"Measured on this 4-core CPU box at these exact settings: about {MIN_PER_FRAME:.1f} min per frame at 2560x1440.\n"
               f"Total {total} frames, about {total * MIN_PER_FRAME / 60:.0f} CPU-box hours; a 32+ core farm node is roughly 6-10x faster.\n")
    with open(os.path.join(pkg, "README.txt"), "w") as fh:
        fh.write(f"""MARY CELESTE - PART 3 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles, CPU (GPU is fine: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera and frame range set
             textures/             shared images, relative paths (//../textures/...); fonts packed
             SHOTLIST.csv / .txt   timings for the edit
Nothing to bake: people are live rigs with keyed poses, ships and props are keyed, bending ropes/lines are shape keys,
the FFT sea's clock is keyed. No simulation caches. Render each .blend's full frame range as set (start 1, end below).

{est}
Shot     frames   seconds
""")
        for r in rows:
            fh.write(f"{r['shot']:8s} {r['frames']:8s} {r['dur']:.2f}\n")
        fh.write(f"\nTotal: {total} frames, {round(t, 2)} s\n")
    print("docs:", len(rows), "shots", total, "frames", round(t, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
