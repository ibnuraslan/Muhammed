"""Write README.txt (farm notes) and SHOTLIST.csv / SHOTLIST.txt (CapCut timings) into a farm package.

    TIMINGS=vo_timings.json python3 tools/farm_docs.py <PKG>
Frame counts use the same rounding as run_anim.py: round(dur * 24)."""
import os, sys, json, csv
P1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(P1, "comp")); sys.path.insert(0, os.path.join(P1, "tools"))
import storyboard as SB

FPS = 24
MIN_PER_FRAME = float(os.environ.get("FARM_MIN_PER_FRAME", "0"))   # measured on the 4-core test box at farm settings


def tc(t):
    f = int(round(t * FPS)); s, f = divmod(f, FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


def main(pkg):
    tim = json.load(open(os.environ["TIMINGS"])) if os.environ.get("TIMINGS") else {}
    rows = []; t = 0.0
    for s in SB.shots():
        dur = float(tim.get(s["id"], s["dur"])); n = int(round(dur * FPS))
        card = ""
        if s.get("card"):
            kind, rest = s["card"].split(":", 1); name, role = rest.split("|"); card = f"{name} - {role}"
        rows.append(dict(shot=s["id"], blend=f"shots/{s['id']}.blend", frames=f"1-{n}", n=n, start=tc(t), end=tc(t + n / FPS),
                         dur=round(n / FPS, 3), card=card, vo=s["vo"]))
        t += n / FPS
    total_f = sum(r["n"] for r in rows)
    with open(os.path.join(pkg, "SHOTLIST.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["shot", "start", "end", "seconds", "frames", "card (add in CapCut)", "voice-over / caption"])
        for r in rows:
            w.writerow([r["shot"], r["start"], r["end"], r["dur"], r["n"], r["card"], r["vo"]])
    with open(os.path.join(pkg, "SHOTLIST.txt"), "w") as fh:
        fh.write(f"Mary Celeste - Part 1 - shot list for CapCut ({len(rows)} shots, {tc(t)} = {round(t, 2)} s, 24 fps, mm:ss:ff)\n")
        fh.write("Import each shot's frames as a PNG sequence at 24 fps and lay them end to end; the start times below follow.\n")
        fh.write("Cards and Courier Prime captions are NOT burned in: add them in CapCut at the times shown.\n\n")
        for r in rows:
            fh.write(f"{r['shot']:5s} {r['start']} - {r['end']}  ({r['dur']:.2f} s, {r['n']} fr)\n")
            if r["card"]:
                fh.write(f"      CARD: {r['card']}\n")
            fh.write(f"      VO:   {r['vo']}\n")
    est = ""
    if MIN_PER_FRAME:
        est = (f"Measured on a 4-core CPU test box at these exact settings: about {MIN_PER_FRAME:.1f} min per frame at 2560x1440\n"
               f"(the open-sea wides S01 S13 S15 S18 S20 S25 S30 S41 run longer, about 1.5x, because of the FFT ocean).\n"
               f"Total {total_f} frames, about {total_f * MIN_PER_FRAME / 60:.0f} CPU-box hours; a farm node with 32+ cores\n"
               f"should be roughly 6-10x faster per frame.\n")
    with open(os.path.join(pkg, "README.txt"), "w") as fh:
        fh.write(f"""MARY CELESTE - PART 1 - RenderStreet package

Blender:     5.2.2 (built and tested with 5.2.2; any 5.2.x should open it)
Engine:      Cycles, CPU (GPU is fine: no CPU-only features are used)
Output:      2560 x 1440, 100%, 24 fps, PNG 16-bit RGB, written to //../frames/<shot>/<shot>_####.png
Sampling:    64 max samples, adaptive (threshold 0.03), OpenImageDenoise, motion blur on (shutter 0.4)
Grade:       in the compositor of each .blend (bloom, cinematic look, vignette) - leave "Compositing" on
Frames:      clean - no cards, captions or labels (they are added in CapCut)

Layout:      shots/<shot>.blend    one scene per shot, camera and frame range set
             textures/             shared images, relative paths (//../textures/...); fonts packed
             SHOTLIST.csv / .txt   timings for the edit
Nothing to bake: ocean, ships, people and camera are all keyframed or computed per frame. No simulation caches.
Render each .blend's full frame range as set in the file (start 1, end below).

{est}
Shot   frames   seconds
""")
        for r in rows:
            fh.write(f"{r['shot']:6s} {r['frames']:8s} {r['dur']:.2f}\n")
        fh.write(f"\nTotal: {total_f} frames, {round(t, 2)} s\n")
    print("docs:", len(rows), "shots", total_f, "frames", round(t, 2), "s")


if __name__ == "__main__":
    main(sys.argv[1])
