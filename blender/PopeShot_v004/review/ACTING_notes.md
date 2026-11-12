# PopeShot: acting review of v003 → fixes in v004

Method: a half-second sheet of v003 (`before_v003_halfsec.jpg`: 270×480, 8 samples, every 30 frames) plus close-ups. For every still I asked: would a real person move like this, here, for this reason? The director's `clip_scan.py` on v003 found 3 bad ranges: frame 97, frame 523 and frames 553–601. Story-beat frames are unchanged in v004 (1, 265, 505, 631, 763, 1015, 1153, 1375).

| # | v003 frames | Problem | v004 fix |
|---|---|---|---|
| 1 | 1–640, 700–1015 (whole crowd) | Wrong rotation sign on the crowd's "wave" and "cheer" poses: the arms swing past the body and stick straight out sideways, like a T-pose (visible 0–4 s and 13 s). | Signs corrected (left arm: +Y lowers, −Y raises; right arm the reverse). Waves are now a raised forearm, and cheers are both arms up and slightly forward. |
| 2 | 97 (clip_scan) | A crowd member's hand enters a neighbour. | Same cause as #1: the T-pose arms poked into the next person. |
| 3 | 505–640 | Collapse: his feet slide outward and back, and he ends in a deep held squat on nothing between the aides (8.5–10 s). | His feet stay planted. He doubles over at the hit, his knees give, and the aides lower him back onto a rear bench in the jeep (new `JeepBench`). He sits there slumped against them with his head tilted and eyes half closed. |
| 4 | 523, 553–601 (clip_scan) | The aides' hands go into the Pope's torso while catching him. | They now stand 0.56 m to either side behind him, grip just outside the armpit and flat on his back, and crouch less because he is seated. |
| 5 | 320–334 (5.4–5.8 s) | The chase camera dives into the robe: the robe rim fills the frame and the camera is effectively inside the body. | The chase camera brakes 0.7 m short of the robe. The bullet flies on into the opening porthole and the camera never enters the body. |
| 6 | 405–480 (7–7.5 s) | The hand x-ray frames a lone arm entering from the frame edge. | It is framed on the midpoint between the hit hand and his head, 1.3 m away, so his face, arm and hand read together. |
| 7 | 631–763 (11–12 s) | Theatre: the drape lay flat under the patient (its height was sampled from the masked body), and the surgeons' hands hovered 15 cm in the air. | The drape is shaped over every visible patient mesh, so he is covered to the chest. The surgeons' hands rest on the drape over his abdomen with small working motions. The nurse holds the instrument tray, which has moved in front of her. |
| 8 | 745–760 (12.5 s) | The frame is mostly the theatre wall with the monitor at its edge. | Reframed between the patient and the monitor. |
| 9 | 1015–1153 (17–18.5 s) | Cell: the Pope's arm stretches horizontally into the air without reaching the shoulder, and the prisoner slumps forward with his head hanging and hands hanging low. | The chairs are closer. The Pope leans in, and his hand travels to the prisoner's near (left) shoulder and rests on it. The prisoner sits upright with his hands resting on his thighs; he looks up at the Pope, then down, and nods while listening. His brows and lids follow his gaze. |
| 10 | 1140–1175 (19–19.5 s) | Wall-filled frame, then the camera passes through the window grille (prop fills the frame). | A key frames the lit window before the move. The grille is removed from the cell window (the barred door stays), so the camera flies out through an open window. |
| 11 | 1375–1395 (23 s) | The statue's base and veil fill the frame on the move down from the crown. | Re-pathed: from the crown macro the camera swings out in front of the statue and looks down at the praying Pope's face. |
| 12 | 1400–1530 (23.5–25 s) | The final x-ray is seen from behind: the cassock fills half the frame and his face is unreadable on beat 8. | The x-ray orbit is now in front of him (between him and the altar), so his bowed face and folded hands read with the x-ray; it then pulls out round his side to the statue. |
| 13 | 500–640 hand pose | The hands are merged on the belly when he is hit. | One hand goes to the abdomen; the other hangs and then rests on the bench beside him. |

Checked as OK:
- the Pope waving in the jeep
- the guards walking alongside, then turning in
- the blessing on the balcony
- the cleric on the step stool, reaching up and pinching the bullet
- the praying stance in the shrine
- the shooter's two-handed grip seen from behind (crowd around him)

## Also found and fixed during the pass
- The two guards sat at z = −60 for the whole film (a lone hide key at 700). They now walk beside the jeep in the square and turn in at the shot.
- Elbow flips in the aides' catch (pole too close to the arm line). The aides now hold him under the armpits with their inner hands, outer hands relaxed. Their heads are up and turned to him, not bowed onto their own raised hands.
- The haze volumes are off (the camera flew through them, and the animated look wants no haze).

## Checks on v004
- **`clip_scan.py` (step 6): 0 bad ranges.**
  - v003 had 3 bad ranges: frames 97, 523 and 553–601.
  - Residual frames are 10–23 probe vertices (under the 25 threshold): surgeons' fingertips resting on the drape over the patient (frames 661–709).
- **`qa_check.py` (c6240b2, step 12, on the packed file): INSIDE 8, EMPTY 15, BACKHEAD 1, and 0 for FILL, HOVER, CLAW and FACEPRESS.**
  - **INSIDE 409–481, 1393, 1537:** the camera is inside the x-ray backdrop dome. It is a camera-only gradient sphere by design (the explainer backdrop), not a body or wall.
  - **EMPTY 625, 769, 781, 1009, 1141:** half-second fly-through transitions (into the theatre window, back out of it, through the balcony doorway, through the cell window). No character is in view for those few frames.
  - **EMPTY 1261–1357:** the crown macro (beat 7, "placed in the crown of a statue"). It is a prop insert of the crown and the bullet; the cleric's hand enters at its start.
  - **BACKHEAD 1153:** the start of beat 7. The camera looks through the cell window into the shrine, with the Pope at 7 m seen from behind, praying before the statue. His face reads from 1375 (beat 8).
- **Hand close-ups:** `after_v004_hand_closeups.jpg`.

## Director 6-point self-check (looked at the images myself)
1. **Hands touch what they hold: checked.** Pistol grip, the aides under the armpits, the Pope's hands on his stomach, the surgeons' fingertips on the drape, the nurse on the tray, the Pope's hand on the prisoner's shoulder, the bullet pinch at the crown, the prayer hands.
2. **No claws: checked.** Idle hands use relaxed curls under Limit Rotation (no backward joints). The aides' outer hands at their sides are loosely curled, not clawed.
3. **Nothing pressed into a face: checked.** qa_check reports FACEPRESS 0.
4. **No empty, blurred or black cells, and no back-of-head on beats: checked on the sheets.** The QA EMPTY and BACKHEAD frames are the intended transitions and the beat-7 wide, listed above.
5. **Close-ups show the hands: checked.** Two of the 16 close-ups (nurse, surgeon A) had been black because the close-up camera sat inside geometry. They were re-rendered from the packed v004 file with explicit cameras (`after_v004_hand_closeups.jpg`).
6. **`hand_poses.py`: not applied in v004.** The director's library message reached me after the pass was finished. The contacts were set with IK targets, surface ray casts and finger curls instead, and every hand contact passed the checks above. It can be adopted in a v005 if wanted.

## Director review round 2 (16:00), applied in the same v004 package
1. **Black close-ups 7 and 8:** re-aimed with explicit cameras (nurse on the tray, surgeon A on the drape).
2. **Close-up 14 (raised claw):** now a relaxed pinch. Index and thumb meet, and the other fingers are loosely curled.
3. **18 s (the back of the prisoner's head):** over the Pope's shoulder onto the prisoner's face (hand on his shoulder), then an arc round to both profiles.
4. **13 s:** the camera comes out of the theatre window onto the crowd below. **10.5 s:** re-aimed over the left crowd rows. At that instant the square crowd is mostly behind the camera, so the frame is the facade (windows, shutters, flags).
5. **Crown macro:** now under 0.5 s (around frame 1318), then a pull-back to the statue and the cleric's hand by frame 1345.

`qa_check` (step 12, on the packed file): INSIDE 7 (the x-ray backdrop dome, by design), EMPTY 13 (the half-second fly-through transitions and the short crown insert), BACKHEAD 1 (frame 1153, the Pope at 7 m seen through the cell window). HOVER, CLAW, FACEPRESS and FILL are 0.

## Round 3 (16:17 note): 10.5 s
- The jeep and the Pope (held by the aides) stay in the foreground until frame 624. The fly into the theatre window now takes about 10 frames (under 0.3 s), and people stay visible at the bottom of the frame.
- `qa_check` (step 12, on the packed file): INSIDE 7 (x-ray dome), EMPTY 11 (transitions and the crown insert), BACKHEAD 2. The BACKHEADs are frame 625, the Pope seen from behind the jeep as the camera lifts away from it, and frame 1153, the beat-7 wide. HOVER, CLAW, FACEPRESS and FILL are 0.
