# SurgeonBrandsLivers_v015: from-scratch rebuild, NOT READY (ON HOLD)

**Status: ON HOLD. Self-QC check 3 FAILED, and the two fix rounds allowed by the rebuild brief are used up.** No .blend is pushed, because none passed. `review/preview.mp4` is the check-3 preview: 270×480, every 5th frame, with the VO, rendered from the packed local build.

## What v015 is
- **Timing:** the same VO and timing as v011/v014. Frames 1–1644 at 60 fps, VO from frame 1. The beat frames are in `beats.json`.
- **Camera:** one continuous camera with no cuts. Four open rooms (OR1, home, OR2, hearing room) are built as 90° sectors around a hub, and the camera whip-pans past the dividing wall between them.
- **People:** four MPFB people:
  - the patient
  - surgeon 1, who is also the defendant
  - the second (female) surgeon
  - the judge
- **Clothes:** one-piece cloth garments relaxed in the rest pose, so they bridge hollows instead of hugging anatomy. The EnhancedEye cornea fix is applied.
- **Logo:** the DA KRAS FILMS poster sits on the home wall and is readable for about 1.5 s (frames 606–700).
- **Build:** `scripts/01_build.py` (set, people, look), then `scripts/02_animate.py` (staging, acting, liver, camera), then `pipeline/package_for_farm.py`. `scripts/lib.py` holds the shared helpers.

## Known faults at check 3 (frames are film frames)
- **1–250, pen and burn:** the hand is a fist and the laser pen is not visible in the fingers. The letters still appear, so nothing visible is doing the burning.
- **225–250, macro:** "SB" is now legible, but the surgeon's glove fills most of the frame.
- **Hearing, 1183–1644:** the suit still reads as a grey one-piece. The collars are ragged and the room has dark corners.
- **Patient top and scrubs:** the necklines read off-shoulder.
- **Drape:** the edge of the abdomen window is stair-stepped.
- **Static stretches:** 351–416 and the end hold 1590–1644.

## A fresh reviewer also found (check 3)
- **Nudity reads:**
  - a light triangle at the crotch of her jeans, 606–835
  - chest shaping on the male scrub top and on the suit
  - a nipple-like dot on the suit, 1560–1644
- **Discovery beat, 1050–1115:** the second surgeon's glove and forearm fill the frame, the probe sits in the heel of her palm, and "SB" is not legible.
- **"SB" legibility:** it is legible only for about 0.4 s, at 250–275.
- **Static holds and stiff poses:** 0–3.6 s, 5.3–6.75 s, 8.0–9.4 s, 22.0–23.75 s and 25.4–27.3 s, with A-poses at 10.1–10.6 s and 20.25–20.75 s.
- **Gavel beat, 1440–1530:** this beat passed the review.

## Recommended next step
The fault that keeps coming back is the hand grip on small tools. Either restage the burn with the pen held by a correctly keyed grip, or frame the hand out of the shot and show only the tip and beam. Then replace the suit with a jacket mesh.
