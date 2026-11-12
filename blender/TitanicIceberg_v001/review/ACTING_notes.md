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

## Round 2: director review of v004 (4e27dd5), fixes in v004 rev 2
| # | Director note | Cause found | Fix |
|---|---|---|---|
| R1 | 22 s: Expert B's legs disappear into the desk | **Both desks stood side-on.** The object rotation was not applied to the desk mesh, so the office desk ran front to back and Expert B stood *inside* it. The darkroom bench had the same bug, so the tech stood inside the bench. The table-top heights were also read from stale dimensions, so the lamp and books floated 9 cm above the desk and beside it. | The desk mesh data is rotated now. The table tops are measured from the mesh (office 1.607 m, bench 1.719 m). Expert B now stands 0.24 m behind the office desk, the tech in front of the bench, and the lamp and books sit on the desk top. The camera at 21.8 s is raised so the desk top reads in front of him. |
| R2 | 17.5–18.0 s: near-blank pale ice frames | The approach was too close and the dive was slow. | The approach is from wider (berg form, scrape and water in frame). The dive key moved from 1080 to 1072, so the skin is crossed at 1074, and 18.0 s is already the darkroom wide shot. Beat 6 stays at 1092. |
| R3 | Darkroom: dark, and the tech's face is turned away | The camera was at his side, his head yawed away, and the reaction was late. | The camera is over the bench looking back at his face from 1100, with a red face-fill light (safelight bounce). The reaction (head lift, brows, jaw) is now at 1125–1180, so it reads in the 19.0 s cell. The print develops from 1092 to 1145. The darkroom front wall is shown to the camera again 10 frames after the dive, because it showed the sea behind the tech. |
| R4a | Steward: fingers flat and splayed on the bellows | The left hand was on the bellows. | The left hand grips the front standard (fingers round, thumb in front), and the right palm supports the camera underneath. |
| R4b | Tech: a claw at the tray edge | The hand was not on anything. The tray also rocked by itself. | The left hand rests flat on the bench beside the tray. The tray no longer moves (the tongs agitate the print). |
| R4c | Expert A: hand hovering off the desk | The hand was out of reach, and the desk height was wrong. | He stands 18 cm closer. His hand is flat on the real desk top, and the magnifier moves with him. |
| extra | Tech's MakeHuman shirt has a chest print/logo | — | The print is patched out (solid navy fabric, `06_look_fix.py`). |
| extra | 19.7 s: the pan to the door dipped to a full-frame floor | The target spline passed under the camera. | The pan now aims straight at the door. |

Re-check:
- `after_v004_0.5s_sheet.jpg` and `v004_hand_closeups.jpg` were re-rendered.
- `clip_scan.py`: 0 bad ranges, both as saved and at frame 1250 with all 5 characters.
- Own audit: float 0, hand–hand 0, hand-in-clothes 0, penetration 7, hover/sink 0, camera-in-geometry 0.

## Round 3: director hand library + QA (v004 rev 3)
Every hand contact now uses `blender/pipeline/hand_poses.py`:
- `add_hand_limits` on all 5 rigs, replacing my own limits.
- `apply_pose` presets replace every hand-set finger angle:
  - `wrap_grip`: the coil and the magnifier handle
  - `cup_hold`: the steward's camera hands and the deckhand's rope end
  - `pinch`: the tongs and the print corners
  - `flat_palm`: Expert A on the desk
- `place_hand`: the steward's left palm on the camera's side.
- `grip_object`: the tech's left hand on the tray rim.

On the camera body, the magnifier, the tongs and the print corners, `grip_object` either landed short or crossed the arms under the library's wrist limits. There, the hand keeps its acting-pass IK placement plus the preset, and **the held prop follows the hand's real, limit-clamped palm**: the camera rests on the steward's right palm, the magnifier handle sits in Expert A's palm, and the tongs sit in the tech's thumb–index pinch. That way contact holds on every frame.

Beat framings fixed for BACKHEAD:
- 120: the steward is now seen in three-quarter profile over his camera.
- 1092: the camera is over the bench facing the tech.
- 1200: the camera is behind the desk facing Expert A.

### qa_check.py (`review/qa_v004.json`): HOVER 0, CLAW 0, FACEPRESS 0, BACKHEAD 0
These flags stay, all intended:
| Flag | Frames | Why it stays |
|---|---|---|
| EMPTY "no character in view" | 126–150, 174–726, 882–1074, 1332–1830 | Character-free story beats by design: the iceberg and the ghost liner (beat 2), the paint-scrape glide (3), the debris aerial (4), the night ghost scrape (5), the explainer cyc (8) and the lone berg in the fog (9). Each frame shows the berg, liner, ship, debris or photo; none is a bare wall. |
| EMPTY | 1170 | A 2-frame pan from the tech to the darkroom door, with the door and the office visible through it. |
| INSIDE | 306–336, 390–438, 1764 | The camera is inside the volumetric mist box (an invisible volume container, not a surface). |
| INSIDE | 1422–1428 | The camera is inside the explainer cyc dome (its gradient backdrop). |
| INSIDE | 1554–1572 | The camera is passing through the berg's interior (the berg is `hide_render`) after flying through the giant photo, then out to the floes. |
| FILL | 234 (Mist_Bank), 1074 (Darkroom_WallFront), 1338 (Office_WallBack) | The mist volume at 234. At 1074 and 1338, single sampled frames of the two fly-throughs: the surface is crossed and hidden within the next 1–2 frames. |

`clip_scan.py` reports 0 bad ranges, both as saved and at frame 1250 (all 5 characters).

### Mandatory 6-point self-check (looked at `after_v004_0.5s_sheet.jpg` and `v004_hand_closeups.jpg` myself)
1. Hands touch what they hold: **checked**
   - deckhand: wraps the coil
   - tech: pinches the tongs, left hand on the tray rim
   - Expert A: palm flat on the desk, hand round the magnifier handle
   - Expert B: pinches both top corners of the print, arms uncrossed
   - steward: the camera rests on his right palm and his left palm is on its side and top
2. No claws: **checked**. There are no curled fingers in the air, and QA reports CLAW 0.
3. Nothing pressed into a face: **checked**. QA reports FACEPRESS 0, and the steward's camera stays at chest height, clear of his face.
4. No empty, blurred or black cells, and no back of the head on beats: **checked**. Empty cells only appear on the character-free story beats listed above, each showing the berg, ship or photo. QA reports BACKHEAD 0.
5. The close-ups show hands: **checked**. All 10 close-ups are aimed at the hand and lit.
6. `hand_poses.py` is used: **checked**. Presets and limits are used on all rigs, with no hand-set finger angles left. See above for where the props follow the hands instead of `grip_object`.
