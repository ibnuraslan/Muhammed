# TitanicIceberg: acting review of v003 → fixes in v004

The source is the half-second sheet of v003 (`review/before_v003_0.5s_sheet.jpg`, 270×480, 8 samples, every 30 frames). For every frame I asked whether a real person would move like this, here, for this reason. Times are in seconds, with frames in brackets (60 fps). Story-beat frames are unchanged: 0, 120, 348, 612, 912, 1092, 1200, 1338, 1530.

| # | Time [frames] | Problem | Fix in v004 |
|---|---|---|---|
| 1 | 1.5–2.5 s [90–160] | **The bellows camera reads as a box sitting on the steward's head/hat.** He lifts a 1912 folding camera to eye height with both hands, and from behind it looks balanced on his head. | A 1912 folding camera is used at chest height with a waist-level finder. He holds it in front of his chest with both palms on its sides. He looks **down** into the finder to compose (head pitch down), presses the shutter with his right thumb, then lifts his head to look at the berg with a reaction (brows up, jaw drops). The camera never rises above his chin. |
| 2 | 0–1 s [0–60] | The steward is stiff: he stands with the camera out and only the head moves. | He gets a weight shift, breathing (spine), a small step-in toward the rail, and a head turn from the berg down to the camera. |
| 3 | 2.0–2.5 s [120–150] | Over-the-shoulder framing is cluttered by the camera box next to his ear. | Fixed by #1: the camera is at his chest, and the over-shoulder view now shows his head turning to the berg. |
| 4 | 11.0 s [≈660] | A blank sea frame as the camera cranes up between the macro and the aerial. | Re-aimed the crane so the berg's edge and the nearest debris stay in frame. |
| 5 | 18.5–19.0 s [1110–1140] | Darkroom: the camera sees the tech's **back and the top of his head**. His face is never readable on beat 6, "When the film was developed". | The camera moves to the bench side at face height, looking across the tray to his face. As the image appears (≈1160), he lifts his head from the tray (head pitch 26° → 6°), raises his brows and opens his mouth, then looks back down. |
| 6 | 18.5–19.5 s [1100–1190] | The tech holds the same hunched pose (only the tray rocks). | Added a breathing and weight shift, a lean-in as the image appears, then the head lift in #5. |
| 7 | 21.0–22.0 s [1260–1320] | Office: both experts are seen **from behind**, and their faces aren't readable on beat 7, "experts studied the image carefully". | The orbit swings to the desk's +X side, so Expert A is in three-quarter profile behind the magnifier and Expert B faces the camera. |
| 8 | 21.0–22.0 s [1260–1330] | **Expert B looks down at the back of the print** he is holding up. The image faces away from him, so there is nothing for him to see, and the camera sees the top of his bald head. | He holds the print up for Expert A and looks at Expert A (head level, turned toward him), then glances at the print's edge. His face is readable above the print. |
| 9 | 21.0–22.0 s [1260–1330] | Expert A leans over the desk with his free hand flat on it, but his head doesn't track the magnifier. | His head follows the lens (pitch and yaw toward the print), with a small forward step-in. The reaction stays: brows up and jaw open at ≈1300. |
| 10 | 22.0 s [1320] | The frame is mostly the top of Expert B's head and shoulders just before the print fly-through. | Fixed by #8 (head level). The camera also pushes in on the print at print height, so the print fills the frame and his head doesn't. |
| 11 | 17.5–18.0 s [1050–1085] | Ice fills the frame for about 0.5 s before the dive (macro). | Kept, because it is a macro with ice detail visible. The camera already crosses the skin at 1084, and the darkroom reveal stays at 1092. |
| 12 | 0–6 s | Deckhand (background, coiling rope): the circling motion is fine, but he never looks up. | He looks up toward the berg once at ≈150 (head turn), then goes back to coiling. |

Not changed (checked):
- the feet are planted for all five actors (the audit shows 0 hover and 0 sink)
- no prop moves without a hand: the camera, tongs, print and magnifier are all keyed to hands; the falling ice and bobbing debris are physics
- the explainer and the final orbit have no characters

## Re-check of v004
- The half-second sheet of v004 is `review/after_v004_0.5s_sheet.jpg`. It was rendered from the packed v004 file with `--factory-startup`.
- Hand close-ups at 270×480 of every contact are in `review/v004_hand_closeups.jpg`:
  - steward: palm under the camera, the other palm on its side, looking down into the finder
  - deckhand: hand on the coil
  - tech: tongs and tray edge
  - Expert A: magnifier handle, and his other hand flat on the desk
  - Expert B: print held up by its top corners
- `blender/pipeline/clip_scan.py` (director branch) reported **0 bad ranges** on camera in both runs (`review/clip_scan_v004*.json`):
  - as saved: Steward and Deckhand
  - at frame 1250: all 5 characters, including the Tech and both Experts, who are `hide_render` at frame 0
- Own audit (`scripts/audit.py`, every 2 frames, `review/v004_audit.txt`):
  - 0 for: hover, sink, hand float, hand–hand, hand inside own clothes, camera inside geometry
  - finger penetration 7: fingers around the 1.5 cm magnifier handle, and the steward's supporting palm under the camera body
- Expert B's hold went through three passes, because the experts' wrist limits clamp the hand orientation. The final is a top-corner pinch: fingers over the top edge, image visible.
