# B37 YardTrench: Phase 1 checkpoint notes

- **Sheet:** `review/P1_sheet_3frames_540.jpg` shows the first, middle and last frame of all 23 shots at 540×960 (Cycles 8 spp, denoised), on the reference timing (frames 1–2310).
- **Contact check:** `review/body_prop_cross_P1.json` (`body_prop_cross.py`, step 3, whole film). Props checked: Helmet, FireStep, SectTurf, SectTop, and the 12 sandbags around the peek spot. Nobody holds a prop in this film.
  - The only hits are shoe-sole edges labelled `root` touching the surface they stand or walk on: up to 4–5 edges a frame on SectTurf/SectTop (S06) and FireStep (S23). This is foot contact, not a crossing. No hand, leg or body passes through anything.
  - Before the fix, every sole sat 1.5 cm under the ground (an MPFB rest offset). Feet and root are now lifted 1.6 cm, so soles rest on the surface.
- **Build:** `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` (+`03a_shots.py`). The full rebuild takes about 30 s. `scripts/sheet.py` builds the sheet.

## Faults I found on my own sheets and fixed before P1
- S09 → S10: the raised-hand keys from the 30% overrun leaked into the next shot. Actions are now procedural and end at the cut, and Phase 2 regenerates each one at 1× for its VO window.
- The man's white top turned blue in the trench, and his cuffs were blue. The colour split used deformed coordinates; it now uses rest-space coordinates.
- The logo was mirrored, and later sat off-centre. It is now correct and centred on the chest, about 24 cm wide.
- The helmet floated about 1 m off his head. Its offset was computed before the rig was placed. It is now Child-Of style on the head bone, keyed every 2 frames.
- Rain streaks crossed the lens. Drops within 2.2 m of the camera are removed and the streaks are thinner. The water had a sun hotspot; it is now rougher with low specular.
- Framing on first and last frames:
  - S04 first frame was a giant leg with the head cut. It is now his whole body.
  - S05 had the subject out of frame.
  - S06 had him half out at the frame edges and cut at the shoulders. It is now a clean legs-only frame with the clods large.
  - S20 had the man too small.
  - S22 had his face hidden behind the sandbags. He now stands on a fire step and his face clears the bags.

## Unsure / for the director
- **S02, S03, S18, S19 are top-down or high wides**, as in the reference, so the person is small and the face doesn't read there. Every other beat shows the acting face.
- **S04–S06 are feet and legs shots** ("your feet crush the grass", "compact"), as in the reference. S06 is cut at the thigh (legs only), with no torso-only frame.
- **The clock overlay** in the reference (bare and hard "over time") is replaced by sun shadows sweeping across the strip.
- **There is one logo placement** (the man's shirt, S17 and S21; it also shows briefly at the start of S23).
- **Time-lapse with a 1× walker:** in S18–S19 the man walks at 1× while the trench deepens under him. His feet follow the floor every frame.
