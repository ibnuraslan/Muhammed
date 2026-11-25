# SurgeonBrandsLivers_v015: from-scratch rebuild, NOT READY (ON HOLD)

## Restage round (director-approved): result FAIL. Current `review/preview.mp4` is this round.
**Fixed this round:**
- **Burn macro:** a clean pen-tip shot with the hand out of frame. "SB" is legible at frames 240-290 (the earlier pen fault was an axis bug in the joined pen mesh).
- **Discovery:** "SB" is legible at frames 1020-1110.
- **Clothes:** the patient's jeans are closed, the collars and cuffs are rolled edges, and the defendant wears a sweater.
- **Logo and set:** the logo is readable at 10.1-13.3 s, and the hearing room has extra fill light.

**Still failing (fresh harsh review), in seconds:**
1. **Chest shaping on the male surgeon:**
   - It shows on the scrubs at 5-9.4 s and on the sweater at 21-27.3 s.
   - The sweater is light blue, not dark.
   - The rest-pose chest flattening is not enough; the body itself has to be flattened.
2. **Discovery macro, 16.9-18.5 s:** the second surgeon's fist sits in the top of the frame, and the probe does not visibly connect to it. Her forearm meets the drape at 16.5-16.9 s.
3. **Surgeon 1's hair:** a hair or brow card shows through his forehead under the cap at 5-7 s.
4. **Static holds and stiff poses:**
   - holds at 7.75-9.4 s, 22.6-23.75 s and 25.4-27.3 s; the film ends mid-blink;
   - stiff poses at 9.5 s, 10.1-10.75 s and 20.2-20.8 s.
5. **Masks:** they are moulded to the face.
6. **Patient and set:**
   - a white pillow/blob reads as a sack at her head at 14.2-15 s;
   - claw hands at 11-13 s and 15-16 s;
   - the doubled-over pose is mild;
   - dark corners at 9.9 s and in the hearing room.


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
