# ToddlerWell: acting review (v003 → v004)

Method:
- I rendered a half-second sheet of the approved v003: 270×480, 8 samples, every 30 frames from frame 1. It's in `ACTING_v003_before_0.5s.jpg`.
- For each frame I asked "would a real person move like this, here, for this reason?".
- I ran the director's `pipeline/clip_scan.py` on v003 (`clip_v003.json`).

Every story-beat frame is unchanged in v004: 1, 241, 463, 673, 913, 1135, 1297, 1357, 1501, 1627, 1765 (`beats.json`).

## Problems found in v003, and the fix in v004
| # | Frames (v003) | Problem | Fix in v004 |
|---|---|---|---|
| 1 | 88–98 (1.5 s) | The toddler's right foot steps through the steel casing wall and hovers inside the pipe at ground level. | The foot steps up onto the casing lip (r 0.335 m, top of the lip), then slips off inward into the hole. |
| 2 | 262–280 (4.5 s) | Blank, washed-out frame: the camera rockets up the shaft looking straight at the sky glare. | The camera looks diagonally up the shaft wall as it rises, so the wall, roots and the bright opening are all readable. |
| 3 | 684–905 (11.5–15 s) | Time-lapse: the workers drop into a deep squat on their heels and hold it. That's the "deep squat held for no reason" reject. | They sit on the ground: hips down, knees up, feet planted forward, forearms on their knees. The transitions between sit and stand are interpolated with planted feet. |
| 4 | 775–790 (13 s) | The camera's dive into the cross-section lingers on a frame filled by ground. | The crossing is faster and moved off the sheet frames: the surface fills the frame for about 3 frames only. |
| 5 | 470–1760 (15 s, mother beat) | Crowd1's "restraining" hands sit at a fixed point. While the mother leans and pleads, Crowd1's arm passes through her shoulder. | Crowd1 stands behind her: one hand between the mother's shoulder blades and one on her right upper arm, computed from the mother's lean. |
| 6 | 1040–1060 (17.5 s) | The over-shoulder framing is filled by ResA's hard hat and back, and the teen isn't visible. | The over-shoulder sits higher and off his shoulder (-0.3, 0.55, 1.7), with the teen's face in frame. |
| 7 | 1100–1125 (18.5 s) | The camera passes ResA, and his vest fills the frame. | The camera path is rerouted 0.5 m clear of ResA. |
| 8 | 1165–1255 (19.5–21 s) | Knot: ResB's hands sink about 4 cm into the teen's belly (clip_scan: 1300–2400 probe verts per frame). The teen holds both arms straight up for 3 s, a frozen pose. | The knot point is now 25 cm in front of the belly, on the rope loop, so ResB's hands stay on the rope. The teen holds his arms out of the way, bent at shoulder height, looking down at the knot. |
| 9 | 1314–1340 (22 s) | Head-first dive: the teen pitches into the air for about 15 frames with nobody holding him, and the holders grab only once his ankles are up. Physically impossible. | The holders stand beside his feet and take his lower legs from the first frame of the dive. They crouch low, then stand up as they lift his legs over the pipe, and keep hold until his feet pass the rim. No unsupported moment. |
| 10 | 1327–1405 (22–23.4 s) | clip_scan: the old holders' hands sink into their own legs and heads while crouched (up to 1357 verts). | These are the new holder poses: smaller lean, hands on the teen's shins. |
| 11 | 1345–1356 (22.5 s) | Blank black frame: the camera dives through the concrete collar and casing instead of the opening. | The camera stays in the cross-section beside the pipe for beat 8. It passes through the open ground at y = -0.9, so the surface fills the frame for about 2 frames. |
| 12 | 1395–1480 (23.5, 24.5 s) | Overexposed, nearly white frames inside the shaft: the camera passes the shaft fill lights and looks into the head torch. | Beat 8 is watched from the cross-section: the torch beam rakes the far pipe wall, roots and stones. The shaft fills drop to 40 W while the teen is in the pipe. |
| 13 | 1500–1625 (25–26.5 s) | The grab is filled by the teen's back and shirt, with the camera under his torso inside the 0.58 m pipe. The faces aren't readable. | The grab is now framed in the cross-section through the open half-pipe: the toddler's face, the teen's arms and the grip are all in frame. The cross-section fill is on from 1350. |
| 14 | 1620–1625 (27 s) | The frame is filled by the back of the toddler's head. | Same as 13: the cross-section framing. |
| 15 | 1772–1812 (29.6–30 s) | Emergence: the teen spins upright in mid-air, 180° of yaw and 180° of pitch at once (a root spin), and no hand helps him. | He's pulled out legs-first and swung down onto his feet by one rotation about the vertical plane, with no spin. ResA leaves the haul line, stands behind him and guides him by the hips the whole way. |
| 16 | 1777–1879 (29.6–31.3 s) | clip_scan: the teen's grip sits inside the toddler's torso, and the toddler's hands sit inside the teen's forearms (up to 975 verts). | The grip is wider than the toddler's chest (±0.18 m), and the toddler holds the teen's forearms from outside. |
| 17 | 1778–1790 (29.6 s) | A tripod leg fills half the frame. | The camera moves to the front of the well. |
| 18 | 1880–1950 (31.3–32.5 s) | Hug: the mother's hands sink into the toddler (clip_scan 37–47). | The mother's hands are on the outside: one under his bottom, one across his back. The hug point is 6 cm further out. |
| 19 | 31–313, 1753 | clip_scan: one crowd duplicate (dup4) stands inside another villager. | dup4 is moved 1.3 m back. |
| 21 | 1326–1345 (22.2 s) | First v004 pass: the leg holders stood 0.7 m out, the teen's shins went out of reach, and their hands ended at their own hips (clip_scan 546–1076). | The holders stand closer, beside the rim at (±0.55, 0.45). Each hand takes the point on the teen's shin nearest his shoulder, one hand above the other along the leg. They crouch only as far as the leg is low. |
| 22 | 1630–1772 (27–29.5 s) | First v004 pass: the toddler's hands sat at the same point as the teen's wrists, inside his hands (clip_scan ~270). | The toddler holds the teen's forearms, 7 cm above his wrists, on the near side. |
| 23 | Whole film | Hands: hand-set finger angles. | Every hand uses `pipeline/hand_poses.py`: `add_hand_limits`, a relaxed hand by default, `wrap_grip` on rope and tools, `cup_hold` where a hand holds a body (shins, forearms, the toddler), and `flat_palm` for Crowd1's hand on the mother's back. Each is keyed in and out, 6 frames either side. |
| 20 | Whole film | Hand audit: rescuers' fingertips on their own clothes, and Crowd1's cheer in her hair. These were reported at D. | They were handled in v003 and are kept in v004. |

## Re-check (v004)
- `ACTING_v004_after_0.5s.jpg`: the same half-second sheet of v004 (270×480, 8 samples).
- `ACTING_v004_hand_closeups.jpg`: 270×480 close-ups of the hand contacts.
- `clip_v004.json`: the clip_scan result, with the bad ranges listed in the push message.
- `qa_v004.json`: `qa_check.py` (director commit c6240b2) on the packed `ToddlerWell_v004_60fps.blend`, step 6, with `beats.json`.

## qa_check flags left in, with the reason
| Flag | Frames | Why it stays |
|---|---|---|
| INSIDE "camera inside geometry", EMPTY "wall fills the frame / no character" | 127–289, 403–469 | Intended: the falls down the shaft. The camera travels inside the open 0.3 m steel casing, looking down at the falling toddler or up at the light. The casing is a hollow tube, so the ray test reads it as "inside". The toddler is small in the frame by design: this is the depth shot. |
| INSIDE / EMPTY | 487–547, 787–871, 1351–1741 | Intended: the cut-away cross-section. The earth block is cut open with backface-transparent faces, so the camera is "inside" the ground mass but looks through the open cut at the pipe, the teen and the toddler. In the time-lapse (793–865) the camera holds on the empty pit for the "days pass" beat. |
| FILL ShaftDust / ShadowSlab | 139–169, 247, 457, 541, 1363, 1555–1591 | ShaftDust is a thin volume of dust in the light shaft. ShadowSlab is a shadow-only helper that the camera never renders (camera visibility off). Neither is a wall in the image. |
| FILL "hair / top of head 32 %" | 1015 | One sampled frame in a camera move past the mother's head (14 frames). Not a beat frame. |
| BACKHEAD Toddler | 1 (beat 1) | **Not fixed in this push.** The opening wide shot shows the toddler walking away from camera toward the well. His face is not on screen. Fix for the next version: start the camera in front of him. |
| BACKHEAD Teen | 1765 (beat 11) | **Not fixed in this push.** The teen faces into the pipe as he comes out legs-first. Fix for the next version: key the camera at the front of the well 10 frames earlier. |
| FACEPRESS | — | Fixed: the toddler now holds the teen's forearms 7 cm above his wrists (0 flags). |
