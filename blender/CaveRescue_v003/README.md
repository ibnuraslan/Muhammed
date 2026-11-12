# CaveRescue_v003: farm package

The full 51.5 s film (1080×1920, 60 fps, frames 1–3090), built to the brief's target beat times. No render has been submitted.

## Contents
- `CaveRescue_v003_60fps.blend`: self-contained, with every texture packed. 71 MB, a plain git file.
- `beats.json`: the start frame of each beat, for `pipeline/retime_to_vo.py` when the voiceover arrives (there is no VO yet).
- `SETTINGS.md`: render settings and test frames.
- `CREDITS.md`: everything is CC0, plus an optional credit line.
- `package_check_f2160_lowres.png`: a 25 %, 8-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

## Source and review
- **Source:** `../CaveRescue_v001/scripts`. Build order:
  1. `01_build_chars`
  2. `02_build_scene`
  3. `03_animate` (runs `03b_camera`)
  4. `06_finish` (look, cave fill, wetsuits, hand limits, 4-frame wipes), then `09_v003` (director D review: brighter dark beats, banded cutaway, tank detail and hoses, neoprene seams, diver rims)
  5. `08_package`

  The checks are `04_audit` (feet, penetration, camera), `05_closeups` (contact close-ups) and `07_hand_audit` (hand BVH).
- **Review:** `../CaveRescue_v001/review/`: the D 1/s sheet, hand close-ups and audit reports.

## Known open items
- **Scale changes:** these are rock fly-throughs with a 4-frame black card, not a true continuous scale. The passage → cross-section exit (around frame 2566–2572) can show a few more dark frames while the camera leaves the mountain mesh.
- **Rendering effects:** rain, flood front and silt are shader effects (no simulations). The water surface is a ripple shader.
- **Crowd:** 4 distinct adult villagers plus 3 rescued boys and the coach. There are no Thai uniforms or media crews yet.
- **Dive gear:** procedural, but detailed: twin tanks with domed ends, valve heads, knobs, cam bands and a regulator hose to the mouth (hooked to the tank and the head). The full-face mask is a rubber seal plus a clear visor.
- **Hand audit:** see the D message and `review/D_hand_audit.txt`. The remaining hits are intended contacts (the diver's hands on the boy's head and mask while strapping it), explained there.
- **Diver close-up:** the dive mask on the surfacing diver reads as a dark visor in close-up.
- **Respectful beat:** beat 7 shows only a light fading into the dark water. No body is ever shown.
