# BatBite_v002b: director notes on v002 (for review)

Built from BatBite_v002 (commit d5655c5, untouched) with the three ranges the director flagged. Same VO, same cuts
(1, 95, 150, 276, 349, 386, 416, 460, 494, 599, 712, 843, 929, 1029, 1093, 1239), frames **1–1362** at 60 fps, shift-only
edit (no retime). `BatBite_v002b_60fps.blend`: 51 MB, textures + VO packed, package_for_farm PROBLEMS none.
Settings: `SETTINGS.md`. Credits: `CREDITS.md`.

## The three notes
1. **f721–851 (S10 shock close-up):** he lifts his right hand in front of his chin and looks at it (palm up), then lifts
   his head and looks up (source 1030–1048); slow push-in (camera travels 0.5 m over the shot, framed on head + hand).
2. **f941–1021 (S12):** new knees-up camera in front of him (lens 40, ~1.9 m) instead of the wide behind the crowd fists;
   his left hand is wrapped over his right fist in front of him (clutching his hand).
3. **f1101–1231 (S14 hospital):** camera moved to his left beside the bed (lens 28): the doctor's face is fully in frame
   (head at ~25 % of the width all shot, reading the chart), the patient in profile with the mask. The patient's elbows
   are bent and both hands rest on his lap. The shot uses source 1625–1771 (25 frames later than v002) so his legs have
   settled under his hands from the first frame; the cut frames are unchanged.

## Preview
`review/preview.mp4` (with the VO): v002's watched frames with **f721–1026 and f1091–1361 re-rendered** and spliced in
(wider than the three notes because S11's start, the rest of S12 and S15 changed too). All 6 pages watched, plus
540×960 zooms of f790, 960, 1100, 1170, 1230.

## Checks on the packed file (`review/`)
| Check | Result |
|---|---|
| clip_scan | **0 bad ranges, 0 hits** |
| qa_check | BACKHEAD 3 (crowd-POV / over-shoulder, as v002), CAMJUMP 14 (the planned cuts), PROPMOVE 6 (mask moving with his breathing head); EMPTY 0, ATTACH 0 |
| limb_check | ARMBODY 4067: every hit is an upper-arm point within 8 cm of the shoulder joint (no forearm/wrist, no arm in another body) — the shoulder false positive; more than v002 only because more of the crowd is in view |
| body_prop_cross | Bat: in-fist only (accepted, as v002). Clipboard: the doctor's fingertips under the board (it rests on his flat hand). Blanket: the patient's fingertips meet the side of the blanket's top edge, f1093–1237 |
| bat ↔ face | ≥ 7.0 mm, frames 400–600 (unchanged) |

## Known issues
- Hospital f1093–1237: the far (left) hand's fingertips touch the side of the blanket edge (reads as resting against it).
- Bent over f1029–1092 (unchanged from v002): the right palm sits ~4.5 cm off the jeans.
