# Mary Celeste — Part 3 of 5 (5:20–7:50): the salvage, the gale, Gibraltar, the court

Script span (mary_celeste/SCRIPT.txt on `claude/mary-celeste`, unchanged): from "Morehouse warns him that taking her
in could put both crews at risk." to "The Mary Celeste can finish the voyage Briggs began." 44 shots, ≈2:23 of
shot time at the storyboard durations (to be stretched to the recorded VO).

Everything is real Blender 5.2 Cycles 3D built on the shared library (`mary_celeste_3d/lib` on
`claude/mary-celeste-3d`: ship, sea, deveau, human, poses, grade), used unchanged.

## Files

| Path | What |
|---|---|
| `shots.py` | The shot list: one function per shot, `f(t)` builds set, people, props and camera for t in [0, 1]. Each `@shot` carries VO, size, duration, action, SFX, card and date tag |
| `render.py` | `blender -b --python render.py -- p3_07 0.5` renders a still; `FRAMES=0:77` renders a shot's frames (hair cached per shot) |
| `lib/crew.py` | Part 3 cast on the shared Deveau class: Morehouse, two Dei Gratia sailors, Flood (barrister's wig, bands), the surveyor, the Admiralty marshal, the judge, the chemist, the helmet diver; top hats; seated / kneeling leg IK; hair cache |
| `lib/props.py` | Ship's boat, sextant case, food sack, pivoted pump brake, table/chair/oil lamp/inkwell/dip pen/letter, warrant + nails + hammer, sword and scabbard (rust), glassware, magnifier, deck stains in the wood |
| `lib/sets.py` | Exteriors (Poly Haven skies, warm sun), Mary Celeste with the spare fore course, Dei Gratia, ocean, real coasts, rain, the soft orange ripple-band marker |
| `lib/terrain.py` | Real elevation (Terrarium tiles): the Rock of Gibraltar, the bay hills, Jebel Musa, the Spanish shore, the chart-table relief |
| `lib/rooms.py` | Interiors: Deveau's cabin, the Vice-Admiralty Court, the chemist's laboratory, the Mary Celeste's cabin, under the hull |
| `tools/storyboard.sh`, `tools/board.py` | Storyboard stills → boards with captions, cards and notes → `review/P3_STORYBOARD.pdf`, `review/contact.jpg` |
| `shared/callout.py` | The shared card/caption module from `claude/killer-in-house`, unchanged |

## New shared assets (built here, offered to the hub)

The gale (`shots.gale`, `sets.rain`), Gibraltar harbour (`shots.gib_land`: real DEM Rock + town + bay hills),
the court (`rooms.court`), Flood / judge / marshal / surveyor / diver (`crew.CAST`), the underwater harbour
(`rooms.underwater`), the chart-table maquette (`shots.maquette`).
