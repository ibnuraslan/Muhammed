# ToddlerWell: acting review (v003 → v004 → v005 → v006)

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
| 30 | 1328–1342 | The holders still had their hands on the legs while the teen slid in, and their fingers sank into his calves (clip_scan). | They let go once he hangs on the rope (from 1342), then keep their hands ready. |
| 31 | Whole film | Hard hats and the head torch followed the head through a Child Of constraint, so qa read them as props moving with no hand. | They are true children of the head bone. |
| 32 | 470–1760 | Crowd1's hand on the mother's back: it was placed from the mother's spine bones, which sit 10 cm behind her mesh, so the hand floated off her. When it was moved onto her, it sank in between keys. | The hand is placed on the nearest point of her evaluated back mesh, and Crowd1 is keyed on the mother's own key frames so the hand moves with her. The other hand rests at Crowd1's side. |
| 33 | Whole film | The crowd's idle phase used Python `hash()`, which changes every run, so every rebuild moved the crowd slightly. | It uses a fixed per-name seed, so each build is repeatable. |
| 34 | 448–468 | Beat 3: the camera's tilt showed the empty world below the ground block in one corner. | The target is raised 25 cm: the toddler and the shaft wall fill the frame (`ACTING_v004_beat_frames_241_463_1501_1627.jpg`). |
| 20 | Whole film | Hand audit: rescuers' fingertips on their own clothes, and Crowd1's cheer in her hair. These were reported at D. | They were handled in v003 and are kept in v004. |

## Re-check (v004)
- `ACTING_v004_after_0.5s.jpg`: the same half-second sheet of v004 (270×480, 8 samples).
- `ACTING_v004_hand_closeups.jpg`: 270×480 close-ups of the hand contacts.
- `clip_v004.json`: the clip_scan result, with the bad ranges listed in the push message.
- `qa_v004.json`: `qa_check.py` (director commit c6240b2) on the packed `ToddlerWell_v004_60fps.blend`, step 6, with `beats.json`.

## qa_check flags left in, with the reason (qa_check e7b25f7, `qa_v004.json`)
These are all 0: BACKHEAD, CAMJUMP, ATTACH, HOVER, CLAW and FACEPRESS. clip_scan has 0 bad ranges (`clip_v004.json`).

| Flag | Frames | Why it stays |
|---|---|---|
| PROPMOVE Clod00–29 | 661–859 | Intended: dirt clods thrown by the excavator bucket during the time-lapse dig. They fly through the air and land; no hand is meant to touch them. |
| INSIDE "camera inside geometry", EMPTY "wall fills / no character / only ShaftDust", FILL ShaftDust | 127–289, 403–469 | Intended: the falls down the shaft and the rise back up. The camera travels inside the open 0.3 m steel casing, a hollow tube, so the ray test reads it as "inside". The rays also stop on the dust volume. |
| INSIDE / EMPTY | 487–547, 787–871, 1351–1741 | Intended: the cut-away cross-section. The earth block is cut open with backface-transparent faces, so the camera is "inside" the ground mass but looks through the open cut at the pipe, the teen and the toddler. In the time-lapse (793–865) the camera holds on the empty pit for the "days pass" beat. |
| EMPTY on beat frames 241, 463, 1501, 1627 ("character 0–2 %", 463 "no character") | | Checked in renders: `ACTING_v004_beat_frames_241_463_1501_1627.jpg`. The toddler's face (241, 463) and the grab with both faces (1501, 1627) read clearly. The rays pass through the transparent cut faces or stop on the dust volume, so qa under-counts the characters. |
| EMPTY "character only 1–3 %" | 73–103, 1303 | Wide framings of the toddler near the well and the crowd at the rim: the people are small in the frame, but their faces read. |
| FILL ShadowSlab | 541, 1363 | ShadowSlab is a shadow-only helper with camera visibility off. It never renders. |
| FILL "hair / top of head" | 1015 | One sampled frame in a camera move past the mother's head. Not a beat frame. |

## Re-check result
- `ACTING_v004_after_0.5s.jpg`: all 65 cells, labelled every 0.5 s. I checked every cell: no empty, black or blown-out cells, and a face reads on every beat.
- `ACTING_v004_hand_closeups.jpg`: 19 close-ups. Each shows the hand on what it holds: rope, rim, levers, the mother's back, the knot, the tripod leg, the teen's belt and shins, the toddler's forearms, the haul line, the teen's hips, the toddler, and the mother's hug.

## v005: moving-preview review of v004 (Nov 14)
I watched v004 as a moving preview (`pipeline/preview.py`, every 5th frame, all 390 frames on 8 pages, director commit e0c925f) and checked it against `LESSONS_LEARNED.md` section 1. These faults were found, and fixed in v005:

| Frames | Fault in v004 | Fix in v005 |
|---|---|---|
| 1–90 | Mannequin arms: the toddler walks with both arms sticking out sideways. The walk's arm offset was in metres, sized for adults. | The arm offset scales with height, so his arms hang and swing. |
| 101–136 | **Body through a surface:** the 900 m far-field ground plane (`FieldFar`, z −0.03) ran under the well opening. Seen from above, the hole showed cracked ground, and the toddler, the rope and the teen passed through it. | A boolean cuts a 0.33 m hole in `FieldFar` at the well. The shaft is open and dark. |
| 166–191 | The toddler blows out to white as he falls past the shaft fill lights. | The shaft fill is 10 W while he falls, and comes up when he lands. |
| 226–236 | His head fills the lens at the bottom. | The camera sits 0.45–0.55 m higher above his raised hands. |
| 244–256 | Pink glare as the camera rises past the shaft fill. | The fill dips from 244. |
| 281–296 | A giant blurred tripod leg sweeps across the crowd shot. | The camera path stays clear of the leg. |
| 403–406 | Blurred ground fills the frame as the camera drops into the hole off-centre. | The drop goes down the centre of the casing. |
| 516–546 | Rescuers "float" in the sky: the camera looked up through the see-through top of the cut-away ground. | The rise looks level. |
| 651–656 | The excavator boom blurs across the lens. | The camera is pulled back from the boom. |
| 871–886 | A black void, then ResA's blurred arm across the lens: the camera flew through the rescuers. | It rises above ground and passes over everyone's heads. |
| 956–986 | The teen walks into and past the lens. | The camera is beside his path. |
| 1011–1106 | Over-the-shoulder shots filled by the back of ResA's head and his arm. | A side two-shot: the teen's face, with ResA out of the lens. |
| 1136–1141, 1301–1306 | A tripod leg blurs across the lens. | The camera routes outside the tripod. |
| 1372–1475 | About 1.7 s of near-empty shaft wall with only the teen's hands at the top, plus torch glare. | The camera holds beside his face as he goes down. |
| 1500–1640 | The teen's hands look open beside the toddler's arms, and the torch blows out a spot on the toddler. | The teen's grip is `wrap_grip` (each holds the other's forearm), and the torch is dimmer at the bottom. |
| 1760–1900 | The tripod legs and winch box blur past the lens during the emergence, ResA's arm crosses the lens, and the legs fill the crane-up. | The camera is 0.7–1 m further out round the tripod. |
| 1099, 1141 | clip_scan: hands near another rescuer as the camera moved. | ResB's spot is moved 0.3 m, and the teen's walk is routed 0.3 m wider. |

Second watch of the v005 preview (with the dust), more faults fixed:

| Frames | Fault | Fix |
|---|---|---|
| 276–291 | ResA's head and hard hat close in the lens on the way out of the shaft. | The camera goes back and up (0, −1.8, 2.4) with a 24 mm lens. |
| 521–546 | Rescuers still read as floating, seen from below the ground. | The rise stays deep, then breaks the surface fast. |
| 1011–1016 | Blank frame: the camera passed through ResB. | ResB's spot is moved to (0.9, 2.3), off the camera path. |
| 1031–1106 | ResA's gesturing arm sweeps across the lens. | Smaller, lower gestures. |
| 1131–1141 | A tripod leg fills the foreground. | The camera goes round the outside of the leg. |
| 1759–1810 | `body_prop_cross.py`: ResA walks through tripod leg 1 and stands on the collar to guide the teen; the teen's feet scrape the casing lip, then his head and legs reach the tripod legs and winch during the swing. | Simplified: ResA stays on the haul line (no hip guide). The teen swings out over the pipe, between the legs, at a moderate height, then steps to the side. 0 visible crossings on 1740–1840. |
| 1821 | ResA walks past the lens. | His route to the cheering spot goes behind the well. |

Render cost: the 24 dust and exhaust puffs were volumes that scale down to 0.001 when inactive. Cycles still built all 24 volumes on every frame, about 48 s of setup per frame. Each puff now exists (hide_render and hide_viewport keys) only during its own 40–90 frames, so at most 3 are live on any frame.
- Measured at 270×480, 4 samples: 5–7 s per frame with the dust visible (frames 20, 205, 610, 700, 880, 1400), down from about 53 s.
- The preview includes all the dust: what's in the preview is what the client renders.

### v005 checks (all on the packed `ToddlerWell_v005_60fps.blend`)
- `clip_v005.json`: full clip_scan, 0 bad ranges. The final camera key change at 1142 was re-scanned on 1093–1200: still 0.
- `body_prop_cross.py` (casing, lip, collar, tube, tripod legs, winch, head) on 1740–1840: 0 visible crossings. On 1100–1170 (tripod legs): 0.
- `qa_v005.json` (qa_check e7b25f7): BACKHEAD, CAMJUMP, ATTACH, HOVER, CLAW and FACEPRESS are all 0.
  - PROPMOVE is only the 30 excavator clods (661–859), which are thrown dirt.
  - EMPTY, INSIDE and FILL are the shaft and cross-section cut-away shots (table above).
- `preview.mp4`: the moving preview of this exact package (every 5th frame at 12 fps, 270×480, 4 samples, with all the dust), with all 8 contact pages in `preview_pages/`. I watched every page.
- Render cost: 5–7 s per frame at 270×480 with the dust (was about 53 s).

Known small items left, judged acceptable:
- One-frame dark or ground frames where the camera enters or leaves the shaft (136–141, 406, 781, 1366, 1736). Each is under 0.1 s.
- A thin, sharp tripod leg crosses the knot approach (1131–1146).
- ResA's arm enters from the frame edge, attached to his body, while he talks with the teen (1051–1106).

## v006: director's review of v005 (Nov 14, 22:26)
| # | Frames | Director's note | Fix in v006 |
|---|---|---|---|
| 1 | 1496–1620 | The teen's fists sit on the toddler's head and face. | The toddler raises his arms wide; his wrists reach about 0.35 m above his pelvis, beside his head. The teen's fists close on his raised hands and wrists (teen wrist targets ±0.14 m, 0.47 m above the toddler's pelvis), clear of his head. Also fixed: facing about 164°, his left hand belongs on the −x side; before, his arms crossed. |
| 2 | 1736–1800 | During the haul-up the toddler dangles separately, up to 1 m from the teen's hands. | He hangs from the teen's grip all the way up the shaft and out of the rim (to 1767). The swing upright is the one moment his short arms can't keep his hands visibly in the teen's grip, so it is now off screen. Hard cut at 1768 to the mother at the tape: she ducks under and runs in, 1768–1831. Hard cut back at 1832 to the teen holding him against his chest. The hand-off to the mother starts from that chest hold. |
| 3 | 136–260 | Nearly black frames looking down the shaft. | The shaft fills sit off-axis, against the wall (0.22, 0.22). A new upper-shaft fill (ShaftFillTop, z −2.4) is on for 134–160 and 250–268. The lower fill stays on to 252 on the rise. |
| 4 | 401–416 | Black and brown blur as the camera enters the shaft. | ShaftFillTop moves up into the casing (z −0.9) for 391–412, so the dive back down is lit. |
| 5 | 1366–1371 | Empty pipe interior. | Hard cut at 1372, from the holders feeding his legs in to beside his face inside the casing. The empty pipe is never on screen. |
| 6 | 1036–1081 (and 1101–1106) | A disembodied arm (ResA) sweeps across the lens. | The arm was ResA's left hand, raised at chest height toward the teen. From 1085 both his arms hang before the camera pulls back past him. The camera stays further out on the teen (0.8, 1.5, 1.55) at 38–40 mm. |
| 7 | 1201–1311 | The volunteer's arm is raised straight up, stiff, for about 2 s. | While he is tied his hands rest low, behind his hips, clear of the knot and of ResB crouched in front. Then they hang. At the rim his hands come forward and in, clear of the holders' grip, and go down the pipe only once he is bent (no arm straight up at 1314). |
| – | 1820–1870 | (follow-on) | ResA walks away to (−1.3, 2.4) to cheer, so he stays out of the front camera. From 1846 the camera goes round the outside of the tripod feet. |

### v006 checks (on the packed `ToddlerWell_v006_60fps.blend`, built from film87)
- Moving preview: `review/preview.mp4`, every 5th frame at 270×480, 4 samples, with all the dust. `review/preview_pages/p01–p08.jpg` (all 8 pages watched). 390 frames in 1816 s on 2 processes × 2 threads, about 9.3 s per frame per process (5–7 s per frame with 4 threads).
- clip_scan at step 2 on the changed ranges (1160–1330, 1760–1850): only f1174 (ResC, self contact, one frame) is left, and it was already in v005.
- Full clip_scan and qa_check: see `clip_v006.json`, `qa_v006.json`.
- Known, left: f141, f251 and f406 are single preview samples (about 5 frames each) that are still dark as the camera passes the ground level or the bottom fill. f1146: two background crowd figures touch for one frame.
