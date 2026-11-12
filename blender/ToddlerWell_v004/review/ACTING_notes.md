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
| 24 | 1 (beat 1), 1–40 | qa BACKHEAD: the opening wide shot showed the toddler from behind. | The camera starts in front of him, near the well, at his eye height. His face reads on the beat, and the camera moves to a three-quarter view as he walks. |
| 25 | 1765 (beat 11) | qa BACKHEAD: the camera on the -y side saw the back of the teen's head as he came out. | The camera is on the +y side, the side he faces while head-down and after he is set on his feet. |
| 26 | 262–292 (4.5 s) | The rise up the shaft was blown out by the shaft fill light and the sky glare. | The camera looks at the shaft wall as it rises, and the shaft fill dips to 60 W for those frames. The wall, the stones and the bright opening read. |
| 27 | 1864–1900 | Hand-off: the teen's and the mother's hands were on the same points on the toddler. The teen's left and right were mirrored (crossed arms), and the toddler was still above the mother's reach (clip_scan up to 750). | The hand-down is continuous from the hold-up grip. The teen keeps hold under the toddler's arms until halfway. The mother reaches up and only takes him (one hand under, one across his back) once he is in reach. |
| 28 | 1324 | Crowd1's hand on the mother's upper arm crossed her pleading hand. | Crowd1's hand rests on top of her right shoulder. |
| 29 | 1762–1786 | ResA's hip-guide hands sank into the teen. | ResA stands 10 cm further back (-0.6, -0.15), with his hands on the front of the teen's hips. |
| 20 | Whole film | Hand audit: rescuers' fingertips on their own clothes, and Crowd1's cheer in her hair. These were reported at D. | They were handled in v003 and are kept in v004. |

## Re-check (v004)
- `ACTING_v004_after_0.5s.jpg`: the same half-second sheet of v004 (270×480, 8 samples).
- `ACTING_v004_hand_closeups.jpg`: 270×480 close-ups of the hand contacts.
- `clip_v004.json`: the clip_scan result, with the bad ranges listed in the push message.
- `qa_v004.json`: `qa_check.py` (director commit c6240b2) on the packed `ToddlerWell_v004_60fps.blend`, step 6, with `beats.json`.

## qa_check flags left in, with the reason
BACKHEAD, HOVER and FACEPRESS are all 0 in v004. These flags stay:

| Flag | Frames | Why it stays |
|---|---|---|
| INSIDE "camera inside geometry", EMPTY "wall fills / no character / only ShaftDust" | 127–289, 403–469 | Intended: the falls down the shaft and the rise back up. The camera travels inside the open 0.3 m steel casing, which is a hollow tube, so the ray test reads it as "inside". The toddler is small in the frame by design: this is the depth shot. On the way up the frame shows the shaft wall and the bright opening. |
| INSIDE / EMPTY | 487–547, 787–871, 1351–1741 | Intended: the cut-away cross-section. The earth block is cut open with backface-transparent faces, so the camera is "inside" the ground mass but looks through the open cut at the pipe, the teen and the toddler. In the time-lapse (793–865) the camera holds on the empty pit for the "days pass" beat. |
| EMPTY "character only 1–3 %" | 73–103, 1303 | Wide framings of the toddler near the well and the crowd at the rim: the people are small in the frame, but their faces read. |
| FILL ShaftDust / ShadowSlab | 139–169, 253–265, 457, 541, 1363, 1555–1591 | ShaftDust is a thin volume of dust in the light shaft. ShadowSlab is a shadow-only helper that the camera never renders. Neither is a wall in the image. |
| FILL "hair / top of head 32 %" | 1015 | One sampled frame in a camera move past the mother's head. Not a beat frame. |

## Still open (this push, 18:20)
I checked these myself on the sheet and the close-ups. They are not fixed yet; a fix is in progress for each.
- **Sheet incomplete:** 52 of 65 cells. From s0039 on only the even cells rendered, because a render worker was killed for lack of memory. The cell labels after 19.5 s are therefore shifted: those cells are 1 s apart.
- **Frame 271 (4.5 s):** still a near-empty frame of the orange shaft wall with a pink light glow.
- **Frames 1681 and 1741 (the cells labelled 24.0 and 24.5 s):** the casing tube, the tripod leg and the winch plate fill the frame during the rise.
- **Hand close-ups that fail:**
  - Teen grabs toddler (1580) and toddler clings (1700): there is a 20–26 cm gap between their hands. The teen's arms can't reach the grip point inside the pipe. In progress: the teen goes 17 cm lower and they hold each other's forearms at a reachable height.
  - Crowd1 restraining the mother (900): her hand is not visibly on the mother's back. In progress: the hand moves onto the back surface, with a grip.
  - The operator's levers (640) and holders 1336: the close-up camera is blocked by the cab or a tripod leg, so the hands don't show.
  - Hand-off (1884): shot in the moment the mother is still reaching. The shot moves to 1900, when she holds him.
- **qa_check fc62c27:** CAMJUMP 0, BACKHEAD 0, HOVER 0, FACEPRESS 0. EMPTY 177, INSIDE 120 and FILL 19 are the intended shaft and cross-section shots in the table above, except 271, 1681 and 1741 (listed here as open).
- **clip_scan:** 0 bad ranges on this package (`clip_v004.json`).
