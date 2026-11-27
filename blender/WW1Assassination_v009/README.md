# WW1Assassination_v009: fix rounds 1–2 on the v008 rebuild, NOT READY (ON HOLD)

No .blend is pushed. After 2 fix rounds (the brief's limit) the film still fails on watched faults (listed below).
`review/preview.mp4` is the full preview of the final scripts (every 5th frame, 270×480, with the VO).

## Build
`scripts/fetch_assets.sh` → `01_build.py` → `02_animate.py` → `03a_map_raster.py` + `03_map.py` → `04_slim.py` → `pipeline/package_for_farm.py`.
Timing: the v007/v008 VO and beat frames (`beats.json`), frames 1–1826 at 60 fps. v008 is left untouched.

## What v009 changed (all from watching the v008 and v009 previews plus the checks)
- The cloud white-out at f1486–1500 is replaced: the camera rises while the city shrinks onto Sarajevo on the 1914 map (one move, no empty frame). The map is now a real grid mesh, so previews (Simplify) match the render.
- Deep map colours, a raster at twice the resolution, an orange fire band on a dark ember base, and no grey flag poles.
- Camera: off the green suit (f556–581) and the fender (f1166–1176); over the cross bunting and lamp heads (f860–960); side-on staging of the shots (f1244–1362); a clean whip at f41–50 (no 86° snap); a seamless join to the rise at f1432 (was a 2.4 m jump).
- Archduke's lap hands lifted out of his thighs; Q6 has no wave and the crowd's hands are off their hips (clip_scan is now clean).
- IK soles on the real surfaces: seated drivers and Archduke on the car floor (0.0–0.1 cm), standing cast on the pavements (±0.4 cm; was 0.9–1.7 cm under).
- The gunman's arm is lowered before the rise; the blast is hotter; the empty MPFB fedora image node is removed at packaging.

## Checks on the final scripts (work file = these scripts)
- clip_scan: BAD_RANGES [] (clean).
- qa_check: CAMJUMP 0, FILL 0, INSIDE 0, ROLL 0, CLAW 0, FAN 0, PROPMOVE 0.
  - EMPTY: f43 (whip), f739–763 (the bomb macro, intended), and from f1501 (the map, which has no people).
  - BACKHEAD: f913, 1057 and 1435 (overheads of the car).
  - HOVER: f1531 (city <1 % scale).
  - FACEPRESS: all from f1495, inside the shrinking city, which is not readable.
  - ATTACH: the helmet sits on the hair, 4–5 cm off the skin.
- limb_check:
  - ARMBODY: 2-point upper-arm-in-torso hits on seated and relaxed rigs (MPFB shoulder volume).
  - Q3 arm.L, 4 pts, f637–697: the wave, background.
- body_prop_cross: the Pistol hits are the closed-fist grip (checked at 1080 p: pistol in the fist). The Car1/Car2 hits are the seated bodies inside the car-body bounding mesh (seats and floor are part of it). These are not visible crossings.

## Open faults (why this is not a PASS)
1. **f1351–1366:** the gunman is cut by the left frame edge; only his arm and hand show (a "hand from the frame edge"). **f1386–1396:** the top of his head sits at the bottom edge.
2. **f906–956:** thin bunting strings cross the overhead of the car. They don't block the lens, but they read as lines over the picture.
3. The fresh-subagent page review was not run because faults 1–2 were already known.
