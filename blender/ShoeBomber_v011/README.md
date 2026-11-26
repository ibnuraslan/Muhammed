# ShoeBomber_v011: from-scratch rebuild of batch 1 film 07. READY (client-approved)

**Status: APPROVED by the client (relayed by the director, Nov 26) and READY TO RENDER.** This is the check-4 build exactly as previewed in `review/preview.mp4`. The self-QC findings in `review/CHECK4.md` stay on record.

## What v011 is
- **Timing:** the same VO and timing as v008/v009 (`ShoeBomber_v011_VO.mp3`, identical file). Frames 1–1469 at 60 fps. The beat frames come from the VO word times (`scripts/vo_words.json`, `beats.json`).
- **Camera:** ONE camera (`CAM_Film`) and no cuts. Four sets (cabin, cutaway studio, sky, airport) swap inside fast whips at frames 885, 985 and 1138. The set roots are placed so the camera path stays continuous.
- **People:** seven MPFB people, one model each. They wear real MakeHuman community garments: the shirts01, pants01, suits01 and shoes packs.
  - **Bodies stay solid under the clothes.** No delete groups are used; the covered skin is pulled in about 13 mm instead.
  - Chest and crotch are flattened before dressing.
  - EnhancedEye cornea fix, and a camera catchlight.
- **Small props as macros:** the match is in a posed pinch, and the fuse comes out of each shoe.
  - The sneaker, the syringe (dart grip) and the black flex cuffs sit on the wrists.
- **Logo:**
  - DA KRAS FILMS bulkhead in the cabin: 3.5–4.25 s.
  - Fuselage livery: about 16.4–18.25 s.
  - Printed in the airport tray: about 19.0–20.4 s.
- **Look:** Filmic High Contrast, with deep saturated sets: purple carpet, royal-blue and magenta seats, a teal studio, an orange and teal terminal.

## Build
```
blender -b --python scripts/01_build.py -- base.blend         # sets, cast, props
blender -b base.blend --python scripts/02_animate.py -- anim.blend   # story (02b, 02c), camera + set switches (02d)
blender -b anim.blend --python scripts/03_finalize.py -- final.blend  # VO strip, farm settings, 1K textures, purge
blender -b final.blend --python ../pipeline/package_for_farm.py -- ShoeBomber_v011_60fps.blend
```
- **Garments:** the asset packs are installed into the MPFB clothes library, as in SurgeonBrandsLivers v015 `scripts/fetch_assets.sh`.
- **Models:** the CC-BY models come from `pipeline/find_models.py get` (UIDs are in `CREDITS.md`).
- **Package:** the local package is 48 MB, and `package_for_farm` reports no problems.

## Render check: PASS
These checks were run on the exact delivered file, `ShoeBomber_v011_60fps.blend` (50.4 MB, md5 `637e85c87ac3ad2f978a55ca4df02bff`). It was opened with `blender --factory-startup -b` (Blender 5.2.2).
- **Errors and links:** the console shows no errors or missing-file messages. There are no linked libraries, unpacked images or unpacked fonts.
- **Packing and scripts:** the VO sound is packed, there are 0 drivers, and no scripts or auto-run are needed.
- **Camera:** `CAM_Film` is the only camera, with no camera markers.
- **Format:** 1080x1920 at 100%, 60 fps (fps_base 1.0), frames **1–1469**.
- **Output:** PNG to `//render/ShoeBomber_v011_####.png`. The `VO` strip is at frame 1.
- **Render settings:** Cycles, 64 samples with adaptive threshold 0.04, OIDN, Persistent Data on.
- **Test frames:** 1, 735 and 1469, rendered at full resolution from the packed file. None is black, empty or pink (no missing textures).
  - Frame 1: 296 s. Frame 735: 364 s. Frame 1469: 162 s.
  - These times are on a 4-core CPU container with no GPU. Expect them to be far lower on the farm.
