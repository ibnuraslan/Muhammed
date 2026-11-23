"""README.txt + SHOTLIST.txt / SHOTLIST.csv (CapCut) for one intro film package.   python3 tools/film_docs.py f1 <PKG>"""
import os, sys, csv, re
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "..", "mary_celeste_p4", "intro_concepts"))
FPS = 24
F, PKG = sys.argv[1], sys.argv[2]
idx = int(F[1]) - 1
src = open(os.path.join(HERE, "..", "mary_celeste_p4", "intro_concepts", "make_pdf.py")).read()
ns = {"LOGO": "the Seldom wordmark"}
exec(src[src.index("FILMS = ["):src.index("\ndef build")], ns)
film = ns["FILMS"][idx]
mod = {"f1": "f1_lamp", "f2": "f2_letters", "f3": "f3_locksmith", "f4": "f4_salvage"}[F]
ft = open(os.path.join(HERE, "films", mod + ".py")).read()
sh = {}; exec(ft[ft.index("SHOTS = dict("):].split("\n")[0], sh); SHOTS = sh["SHOTS"]


def tc(f):
    s, f = divmod(int(f), FPS); m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}:{f:02d}"


# what each shot shows, as built (camera; action; sound cue for CapCut)
BUILT = {
 "f1": [("Low on the spiral stair behind him, looking up; the camera rises with him.",
         "The keeper climbs two iron treads, storm lantern swinging from his left fist, right hand on the brass rail.",
         "Boots on iron treads x2, lantern bail creak, rain on the slit window, wind in the tower."),
        ("Over his shoulder in the lamp room, the Fresnel optic turning above.",
         "Kneeling at the pedestal, he works a rag in small circles on the salt-crusted housing.",
         "Clockwork tick of the turning optic, rag on salt, storm against the glazing."),
        ("Close over his right shoulder on the plate.",
         "One stroke of the rag across the plate: the salt crust comes away and the plate shows.",
         "Long rag scrape on salt; on the reveal, a low foghorn note."),
        ("Locked off: him and the pedestal, the beams turning.",
         "He sits back on his heel and looks at the plate. HOLD on the plate.",
         "Optic clockwork, wind; silence under the foghorn tail.")],
 "f2": [("Wide, high: pigeon-holes, the long table, one green-shaded lamp.",
         "The clerk stamps letters in a steady rhythm (three strokes).",
         "Rubber stamp x3, wall clock tick, paper."),
        ("Medium across the table, side-lit.",
         "She lifts the unaddressed parcel and turns it, looking for an address.",
         "Parcel lifted off the wood, paper rustle, a pause."),
        ("Over her right shoulder on the parcel.",
         "She brings the scissors to the knot and snips the string; the ends fall loose.",
         "Scissors snip; the string slithers; room tone drops."),
        ("Over her left shoulder, high, into the opened parcel.",
         "On the tissue lies the letterpress card. Her stamp hand stays raised. HOLD on the card.",
         "One clock tick on the reveal.")],
 "f3": [("Side-on, low: the locksmith kneeling at the safe in the lantern beam, dust in the air.",
         "Stethoscope to the door, he turns the dial a click at a time.",
         "Dial clicks (magnified), his breath, dust."),
        ("Close on the dial over his right shoulder.",
         "The dial clicks round under his fingers.",
         "Dial clicks; the last one lands with a deeper click."),
        ("Side-on: the safe and the man.",
         "He hauls the handle down, the bolts draw back, the door groans open.",
         "Handle, three bolt thunks, long hinge groan."),
        ("Over his shoulder, down into the open safe.",
         "He raises the lantern: on the red velvet, the enamel plaque. HOLD on the plaque.",
         "Near silence; his slow breath.")],
 "f4": [("From the water: the quay, the crane, the man on the stones.",
         "He signals the crane up; the crate breaks the surface on its chains.",
         "Gulls, chain rattle, steam hiss, water slough."),
        ("Behind him on the quay, the crate swinging up out of the mist.",
         "He steadies the rising crate with a boathook.",
         "Chain under load, boathook knock on wet wood, drips."),
        ("Close over him at the landed crate.",
         "Kneeling, he wipes the mud off its side with his sleeve: paint shows through.",
         "Sleeve on wet wood, mud slap."),
        ("Slow push-in on the crate and the man.",
         "The stencilled logo shows on the wet planks; he turns to look back at the water. HOLD on the crate.",
         "A ship's bell somewhere in the mist.")],
}[F]
BUILT.append({                                 # every film ends on a clean, readable 2.5 s hold of the logo
 "f1": ("Straight on, close: the cleaned maker's plate.", "LOGO HOLD: the Seldom wordmark on the plate, still; the beam light passes.", "Foghorn tail fading, optic tick."),
 "f2": ("Straight down, close: the card on the tissue.", "LOGO HOLD: the Seldom wordmark on the letterpress card, still.", "Room tone, one clock tick."),
 "f3": ("Straight on, close: the enamel plaque on the velvet.", "LOGO HOLD: the Seldom wordmark on the plaque, still, lantern light.", "Near silence, a low settle of the door."),
 "f4": ("Straight on, close: the stencil on the crate side.", "LOGO HOLD: the Seldom wordmark stencilled on the wet planks, still.", "Drips, distant ship's bell."),
}[F])

rows = []; start = 0
for k, (key, (t0, t1)) in enumerate(sorted(SHOTS.items(), key=lambda kv: kv[1][0])):
    n = int(round((t1 - t0) * FPS))
    cam_, act_, snd_ = BUILT[k]
    rows.append(dict(shot=f"{F}{key}", start=tc(start), end=tc(start + n), frames=n, seconds=round(n / FPS, 3),
                     camera=cam_, action=act_, sound=snd_))
    start += n
total = start
title = film["title"].split(". ", 1)[1]
with open(os.path.join(PKG, "SHOTLIST.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["shot", "start", "end", "seconds", "frames", "camera", "action", "sound (add in CapCut)"])
    for r in rows:
        w.writerow([r["shot"], r["start"], r["end"], r["seconds"], r["frames"], r["camera"], r["action"], r["sound"]])
with open(os.path.join(PKG, "SHOTLIST.txt"), "w") as fh:
    fh.write(f"Seldom intro - {title} ({total} frames = {total / FPS:.2f} s, 24 fps, mm:ss:ff)\n")
    fh.write(f"{film['log']}\n\nThe MASTER render is the whole film in one piece; this list is for adding sound in CapCut.\n\n")
    for r in rows:
        fh.write(f"{r['shot']}  {r['start']} - {r['end']}  ({r['seconds']:.2f} s, {r['frames']} fr)\n      {r['camera']}\n      {r['action']}\n      SFX: {r['sound']}\n")
    fh.write(f"\nWHERE THE LOGO IS: {film['logo']}\n")
with open(os.path.join(PKG, "README.txt"), "w") as fh:
    fh.write(f"""SELDOM INTRO - {title} - RenderStreet package

Extract all zips into ONE folder -> upload the folder -> render MASTER.blend, scene MASTER, frames 1-{total}.

Blender:   5.2.2 (any 5.2.x)
Engine:    Cycles (CPU or GPU), 2560 x 1440, 24 fps, 64 samples adaptive (0.03) + OpenImageDenoise, motion blur 0.4
Output:    //frames/SELDOM_{F.upper()}_####.png (PNG 16-bit RGB)
Layout:    MASTER.blend (scene MASTER: the shots as Scene strips, linked from shots/) + shots/{F}A..D.blend, each
           self-contained (textures packed). Grade is in each shot's compositor. No cards or captions are burned in.
Nothing to bake: people, props, camera and lights are keyframed. No simulation caches.

Shots: {', '.join(f"{r['shot']} {r['frames']} fr" for r in rows)}   Total {total} frames ({total / FPS:.2f} s)
""")
print("docs", F, total, "frames")
