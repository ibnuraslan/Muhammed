# BeethovenDeaf_v002: farm package

This is the full 26.5 s film at 1080×1920 and 60 fps (frames 1–1590), ready for RenderStreet. No render has been submitted.

- `BeethovenDeaf_v002_60fps.blend`: the self-contained scene. Every texture is packed, and it opens in factory-startup Blender 5.2.2.
- `beats.json`: the beat start frames for the voiceover retime.
- `SETTINGS.md`: render settings and suggested test frames.
- `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: low-resolution frames rendered from the packed file in factory Blender. They show the package works; they are not a quality reference.

The source is in `../BeethovenDeaf_v001/scripts`. Run `build_all.sh <work_dir>`: it fetches the assets, then runs 01 to 05 and the audit in 06.
Review sheets and the audit are in `../BeethovenDeaf_v001/review/`.

## Story beats (target times from the brief; there is no VO yet)
| # | Frame | Line starts | Picture |
|---|---|---|---|
| 1 | 1 | He would bite down… | Macro of the teeth clamping the brass rod; profile; pull back along the rod into the candlelit room |
| 2 | 235 | …as he played | Hands crash on the keys; low camera on the keys |
| 3 | 313 | The piano's vibrations… | Cyan rings run up the rod; the camera rides beside them |
| 4 | 517 | …into his jawbone… | X-ray: skin to glass, the room dissolves into a cyan studio, rings run through the mandible |
| 5 | 715 | This sent the sound… | Glow wave over the skull; orbit; ear cross-section |
| 6 | 985 | …skipping his damaged eardrums… | Torn grey eardrum; a red pulse dies on it; cyan rings bypass it |
| 7 | 1105 | …so he could still hear | Cochlea lights from cyan to warm white; pull out to his face as his eyes close |
| 8 | 1207 | And by using this trick… | Passionate playing, pages fly, spiral crane up to top-down |

## Voiceover
None has been delivered. When it arrives:
1. Run `pipeline/transcribe.py` to get the word times.
2. Build `anchors.json` from `beats.json`: old frame → the second of each beat's first word.
3. Run `blender -b BeethovenDeaf_v002_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 BeethovenDeaf_v003_60fps.blend`.
4. Re-pack with `package_for_farm.py`.

The X-ray fades, glow radii and ring paths are all ordinary keyframes, so they warp with everything else.

## Known issues
- **No VO yet.** The timing follows the brief's target beat times (±0.3 s); a retime is needed when the VO arrives.
- **Strike contact:**
  - At 4 of 256 key strikes the lowest fingertip hovers 9–19 mm above the key, instead of within about 4 mm.
  - In two in-between frames (f595 and f763) a fingertip dips 8–10 mm under the key tops. Both are during the X-ray, when the hands are invisible.
- **Piano keys:** they don't move; the model's keys are a single mesh.
- **Cravat:** it is the suit's tie region recoloured to dark red silk, with the suit's own stripe shading, rather than a separately modelled neckcloth.
- **Ear scale:** the ear cross-section (eardrum, ossicles, labyrinth) is scaled about 2.5× life size so it reads in vertical frame. The canal is a stylised cut-away.
- **Skull:** it is one rigid mesh that follows the head bone. Its jaw does not open with his (the jaw is nearly closed on the rod during the X-ray, so this does not show).
- **Hair:** particle strands are only checked at 270×480 and 8 samples, so check frame 40 on the farm.
- **Room hidden during the X-ray:** the bench, piano and music desk are hidden by keyframe from f629 to f1137, while the opaque studio backdrop surrounds the head. Nothing outside the backdrop is visible then.
