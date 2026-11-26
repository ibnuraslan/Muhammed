# ShoeBomber_v011: from-scratch rebuild of batch 1 film 07. NOT READY (ON HOLD)

**Status:** self-QC check 3 FAILED and the two allowed fix rounds are used up. No .blend is pushed. `review/preview.mp4` is the latest preview, rendered from the packed local build. The findings are in `review/CHECK1.md` and `review/CHECK3.md`.

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
