"""Write README.txt (farm notes) and SHOTLIST.csv / SHOTLIST.txt (CapCut timings) into the Part 2 farm package.

    python3 tools/farm_docs.py <PKG>
Timings come from vo/vo_timings.json (shots aligned to the Edmund voice-over, word timestamps)."""
import os, sys, json, csv
P2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P2)
import shots

FPS = 24
MIN_PER_FRAME = float(os.environ.get("FARM_MIN_PER_FRAME", "0"))


def tc(f):
    s, f = divmod(int(f), FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def main(pkg):
    T = json.load(open(os.path.join(P2, "vo", "vo_timings.json")))
    rows = []
    for sid, scene, vo, shot, action, sfx, card in shots.SHOTS:
        t = T[sid]; a = t["start_frame"] - 1; n = t["frames"]
        rows.append(dict(shot=sid, a=a, n=n, start=tc(a), end=tc(a + n), dur=round(n / FPS, 3), vo=vo, card=card or "",
                         sfx=sfx, what=action, have=os.path.exists(os.path.join(pkg, "shots", f"{sid}.blend"))))
    total = rows[-1]["a"] + rows[-1]["n"]
    with open(os.path.join(pkg, "SHOTLIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["shot", "start", "end", "seconds", "frames", "card / tag (add in CapCut)", "voice-over / caption", "sfx", "picture"])
        for r in rows:
            w.writerow([r["shot"], r["start"], r["end"], r["dur"], r["n"], r["card"], r["vo"], r["sfx"], r["what"]])
    with open(os.path.join(pkg, "SHOTLIST.txt"), "w") as fh:
        fh.write(f"Mary Celeste - Part 2 - shot list for CapCut ({len(rows)} shots, {tc(total)} = {total / FPS:.2f} s, 24 fps, mm:ss:ff)\n")
        fh.write("Voice-over: MaryCeleste_Part2_VO.mp3 (Edmund, 2:31.6) starts at 00:00:00. Import each shot's frames as a PNG\n")
        fh.write("sequence at 24 fps and lay them end to end from 00:00:00; the start times below then line up with the voice.\n")
        fh.write("Cards, tags, callouts and Courier Prime captions are NOT burned in: add them in CapCut at the times shown\n")
        fh.write("(person cards slide in from the right, place cards from the left).\n\n")
        for r in rows:
            fh.write(f"{r['shot']}  {r['start']} - {r['end']}  ({r['dur']:.2f} s, {r['n']} fr)\n")
            if r["card"]:
                fh.write(f"    CARD: {r['card']}\n")
            fh.write(f"    VO:   {r['vo']}\n")
            fh.write(f"    SFX:  {r['sfx']}\n")
    est = ""
    if MIN_PER_FRAME:
        est = (f"Measured on a 4-core CPU box at these exact settings: about {MIN_PER_FRAME:.1f} min per frame at 2560x1440\n"
               f"(open-sea shots with the FFT ocean run longer). Total {total} frames, about {total * MIN_PER_FRAME / 60:.0f} hours\n"
               f"on that box; a farm node with 32+ cores should be roughly 6-10x faster per frame.\n")
    with open(os.path.join(pkg, "README.txt"), "w") as fh:
        fh.write(f"""MARY CELESTE - PART 2 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles, CPU (GPU is fine: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera, animation and frame range set
             textures/             shared images (2K max), relative paths (//../textures/...); fonts packed
             SHOTLIST.csv / .txt   timings for the edit, aligned to the voice-over
Nothing to bake: sea, ships, people and camera are all keyframed or computed per frame. No simulation caches.
Render each .blend's full frame range as set in the file (start 1, end below).

{est}
Shot   frames   seconds
""")
        for r in rows:
            fh.write(f"{r['shot']:6s} 1-{r['n']:<6d} {r['dur']:.2f}{'' if r['have'] else '   (MISSING)'}\n")
        fh.write(f"\nTotal: {total} frames, {total / FPS:.2f} s\n")
    print("docs:", len(rows), "shots", total, "frames", round(total / FPS, 2), "s; missing:", [r["shot"] for r in rows if not r["have"]])


if __name__ == "__main__":
    main(sys.argv[1])
