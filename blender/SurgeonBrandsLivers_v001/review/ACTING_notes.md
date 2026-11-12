# SurgeonBrandsLivers v007: acting review and fixes

Brief: `blender/briefs/ACTING_FIX_04-10.md` (director branch `claude/beautiful-ptolemy-c5vrcq`).
Method: half-second review sheet of v006 (`before_v006_half_second.jpg`, 270×480, 8 samples, every 30 frames), fix, re-render the same sheet for v007 (`after_v007_half_second.jpg`).
Story-beat frames are unchanged: 1 / 301 / 565 / 637 / 781 / 1045 / 1231 / 1501, end 1710. No VO added.

## Problems found in v006, with the fix in v007

| # | v006 frames (time) | What a real surgeon or person wouldn't do | v007 fix |
|---|---|---|---|
| 1 | 451–541 (7.5–9.0 s) | **Mask-off.** Both arms swung up behind and over the head; the elbows rose above the shoulders; the mask moved on its own before any hand reached it. | One hand only (right). It rises upright in front of the face from 466, pinches the mask's lower edge at 474, and pulls it down onto the chin from 478 to 502. The mask moves only while the hand holds it. It is released at 508, and the hand returns to rest at 522. The elbow is kept low and in front with a forward IK pole. The left arm stays low at the side the whole time. Close-ups: `v007_mask_off_450-522.jpg`. |
| 2 | 499 | Fingertips poked into the chin during the pull. | The hand eases forward 3 cm as the pull ends. |
| 3 | 1–90 (0–1.5 s) | Beat 1 showed only the surgeon's back, and at 1.5 s the top of his head filled the frame, so there was no read of who is operating. | The opening camera was re-staged. His masked face and the marker pen are in frame from frame 1, and the move ends on the window at 115. |
| 4 | 120 (2.0 s) | Shoulder fill: the surgeon's shoulder blocked the whole frame. | Covered by the same re-staged opening keys. |
| 5 | 55–127, 331–427 | The surgeon's hands went inside the patient's torso, which is hidden under the drape (clip_scan). | The drape torso was raised to match a real body, and the patient was lowered 5 cm onto the table top. The hands now work on the drape surface. |
| 6 | 607–643, 769, 1177; patient on table/bed | "Rest" arms were driven into the thighs and pelvis. A sign bug in the rest pose adducted the arms inward instead of letting them hang. The lying patient's hands were inside her pelvis. | `arm_rest` sign fixed, so arms hang naturally outside the body. Lying arms are slightly apart. |
| 7 | 660–760 (11.0–12.5 s) | **Home:** she folded over almost double, with her face hidden by her hair. Her left hand sank into her thigh. The fingers of the hand on her side were in her belly. | She bends less (spine 28–34°, head up), so her face reads. The left palm is anchored to the knee joint. The right hand lies flat on the outside of her side with the elbow out. Close-ups: `v007_home_hands_697-740.jpg`. |
| 8 | 860–880 (14.5 s) | The bed filled the frame during the push. | The camera key at 870 moved out (2.95, 1.45, 0.85). |
| 9 | 1228–1242 (20.5 s) | The whip pan went through the anaesthetist's blue drape at close range, so the frame was a solid blue fill. | The camera rises over the screen bar (keys 1228/1231/1235/1242) and the whip reads as a move, not a fill. |
| 10 | 1273–1285, 1291–1419 | The surgeon's hands passed through each other at the lectern; the anaesthetist's hand was inside his own torso (hand audit pass 1). | Re-keyed by the hand audit: 0 hits at the end (`v007_hand_audit.txt`). |
| 11 | 270 (4.5 s), 630 (10.5 s), 1170 (19.5 s) | Not an acting problem: these are the intended 6-frame texture-wipe transits. | No change; noted so they are not read as errors. |

## Checks
- `pipeline/clip_scan.py` (director's, depth 6 mm, on camera): **v006 = 9 bad ranges** `[1-127, 277-433, 487, 607-643, 679-685, 769, 793-913, 1177, 1273-1285]` → **v007 = 0 bad ranges** (`clip_scan_v006_before.json`, `clip_scan_v007_after.json`).
- Hand audit (every 2 frames): pass 1 found 31 hits, final 0.
- Close-up of every hand contact (pen, needle driver, drape, mask pull, lamp, mug, side, knee, bed push, glove snap, liver lift, lectern, spread hands, gavel raised/strike, stamp, writing): `v007_hand_contact_closeups.jpg`.
