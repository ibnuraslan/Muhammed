# SurgeonBrandsLivers v008d: fixes from the director's moving preview of v010 (= v008c synced)

v008d is the approved v008c plus `13_preview_fixes.py` and the camera keys in `04_camera.py`.
- Beat frames are unchanged (1/301/565/637/781/1045/1231/1501, end 1710). No VO.
- I mapped the synced times back to my frames by matching the camera path (v010 frame → v008c frame).

| Director note (synced time) | My frames | Fix |
|---|---|---|
| ~10.75 s fully BLACK frame | 638–640 | The snapped camera sat inside the calendar's paper, then behind the home picture frame on the other side of the wall. The picture now hangs 0.8 m along the wall, and the camera's near stop is in front of the calendar. Now one wall/calendar wipe frame. |
| ~17.5–19 s hands with no arms, empty glove | 1040–1200 | Cut to the liver alone: the glove hands are hidden from 311 on and the liver is held still (no prop moving by itself). The SB liver reads alone in the light. |
| 2.25 s, 3.75 s, 12.5 s, 19 s, 19.75 s blur / empty wall | 145, 240, 1060, 1177, 1234 | The studio dives (in at 133 and 1057, out at 275 and 1175) are now clean cuts, with no membrane or skin fill frames. Macro shots are pulled back. The whip at 1231 passes the anaesthetist before the wall. The home→OR wall pass at 774 is one frame. 12.5 s maps to the home shot (my 745), which reads (person in frame). |
| ~5.25–5.75 s giant glove | 330–358 | The camera is pulled back and up (z 1.62, 30 mm), so the hands and the stitched incision read. |
| ~3 s ghost oval with an arc | 192–196 | The translucent smoke puffs (`Smoke_*`) are removed. The arc was the glowing burn trail of the S, now seen clean. |
| Writing glove with no arm (same fault, studio 100–310) | 100–310 | The writing hand now has its nitrile forearm, entering from the frame edge. The studio macro cameras moved left of the arm so it doesn't cross the lens. |

Found while watching the preview, also fixed:
- 776 black frame: the camera is already in the OR on 776.
- 1176–1196: Surgeon2 shot low and to the side, so his face reads under his cap.
- 1446: faster pan (no empty side wall).
- 1578: a key keeps the judge in frame.
- 318: no shirt fill.

## Checks on the packed file
- **clip_scan: 0 bad ranges.**
  - Frame 325 was new on camera: the surgeon's forearm was inside the patient's hidden torso under the drape.
  - On the OR table she now sits 7 cm lower. Her face mask, neck towel and tube go down with her.
  - Her head still rests on the table.
- **limb_check (director 9a0a692):** ARMBODY 874, PROPHEAD 228, ARMBACK 1.
  - ARMBODY: 721 of the hits are only the first 2–3 points of the upper arm, inside the shoulder/deltoid mass (the shoulder joint, classed as torso).
  - The rest I checked in side renders: the anaesthetist's hanging arm, the nurse reaching for the drape and pushing the bed, Surgeon1's pen arm across his chest, and Surgeon2's glove snap. The arms hug the torso but read outside it.
  - PROPHEAD: the anaesthesia mask cone and rim on the patient's face, and the neck towel round her neck. Intended contacts.
  - ARMBACK 1: one frame of the anaesthetist at 775 (transit).
- **qa_check (newest):**
  - CLAW 2 and HOVER 14: the patient's hands under the drape and in the OR while the camera is elsewhere. Not visible.
  - CAMJUMP 7: the four studio cuts, the calendar wipe, the home wall wipe and the whip.
  - PROPMOVE 33: the burn sparks (effects) and the mug falling after it's dropped.
  - ATTACH 39: masks sit about 2 cm off the skin, as fitted.
  - EMPTY 44 / FILL 2: the liver-alone studio shots (no character in the set by design) and the single-frame wipes.

## Moving preview
`v008d_preview_every5th_270x480.mp4`: every 5th frame, 270×480, Cycles 4 samples + denoise, 342 frames, 28.5 s at 12 fps. I watched it start to finish (all 342 frames).
