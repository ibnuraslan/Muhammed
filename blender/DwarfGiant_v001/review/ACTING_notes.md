# DwarfGiant — acting review of v002 (half-second sheet `ACT_before_v002_0p5s.jpg`)

Frames are v002 / v003 frames (60 fps). Story-beat frames (beats.json) stay where they are: 1, 180, 372, 468, 696, 882, 1074, 1248, 1476, 1710, 1860, 2040.

| # | Time (frames) | Problem | Fix |
|---|---|---|---|
| 1 | 0.0–0.5 s (1–31) | The clerk leans over the desk with his forearms *inside* it and is holding nothing. His FK arms are floating. | The clerk now has IK hands. Both palms rest on the desk top; the right hand writes in small strokes and the left holds the page. |
| 2 | 1.0–2.5 s (61–151) | Officer 1's open hand hovers over the hero's head, then drops as a claw. It touches nothing, and the "slider" does not exist. | Officer 1's right hand grips the real height rod beside the hero's head, slides down it, and stops at head height. His other hand rests at his side. |
| 3 | all office beats (1–1476) | The hero and officers stand with their arms held out from the body (stiff A-pose) and do not breathe. | Arms hang close to the body with soft elbows. Breathing, weight shifts and small head turns run on every standing character (hero, officers, normal man, young self). |
| 4 | 6.5 s (391) | The camera is inside the x-ray head. | The camera stays outside the face while it pulls back. |
| 5 | 7.5 s (451) | A blank black frame: the camera is inside geometry during the pull-back. | The pull-back path is re-keyed. A camera-fill check is now run on the whole film (`04d_cam_fill.py`). |
| 6 | 8.5–11 s (511–661) | The hero grows in place. His feet slide outward as the armature scales, and he never steps. | His feet are planted in world space. He takes small re-plant steps (lift and set down) every 1.5 s while he grows. |
| 7 | 13.5 s (811) | The frame is filled by Officer 1's sleeve: the camera passes through him. | The camera path is moved clear of him. |
| 8 | 17–17.5 s (1021–1051) | The frame is filled by Officer 2's body: the camera passes him as he steps back. | Officer 2 steps back sideways, out of the camera's path. |
| 9 | 23–24 s (1381–1441) | "Cups his ear" reads as an arm thrown over the head, and the arm fills the frame. | The elbow now stays out and down, and the cupped hand sits behind the ear with the palm forward. The camera pulls back so his face and hand read together. |
| 10 | 24.5 s (1471) | The frame is filled by the office wall. | The wall fly-through opens earlier (1462–1497). |
| 11 | 25–26.5 s (1501–1591) | The surgeons stand with their arms out like sleepwalkers. Their open hands touch nothing. | The surgeons have IK hands. They hold a sterile pose (forearms up, hands in front of the chest), then Surgeon 1 places a hand on the drape at the patient's shoulder. The nurse grips the foot rail of the bed. |
| 12 | 27.5 s (1651) | The frame is filled with skin: the camera passes through the face on the dive into the lying head. | The dive enters from the side, at the temple, so skin fills only a few frames. |
| 13 | 28.5 s (1711) | Floor tiles only: the camera is pointed at nothing after it leaves the head. | A new key frames the patient as the camera pulls out. |
| 14 | 30.5 s (1831) | A shoe sole fills the frame. | The camera pulls back and up, so the feet over the end of the bed read as feet. |
| 15 | 32.5 s (1951) | The tiled wall fills the frame during the crane to the window. | The crane aims at the window glass the whole way. |
| 16 | 29–30 s (1741–1801) | The nurse's hand floats near the blanket. | The nurse now tucks the blanket with both hands on its edge (IK, with contact). |
| 17 | 35–38.5 s (2101–2311) | The young and old selves stand frozen. | They breathe and shift weight. The old man turns his head toward the young man, and the young man looks up at him. |

## Second round (director QA + hand-pose library, Nov 13)
| # | Problem (qa_check / audit) | Fix |
|---|---|---|
| 18 | FAN on every hand (~840 flags). MPFB rest fingers fanned out. | Every hand now uses `pipeline/hand_poses.py` presets. Idle hands are `relaxed`; the hero's desk hand, Surgeon 1's hand on the drape and the nurse's hands on the blanket are `flat_palm`; the ear is `cup_hold`. The library's `add_hand_limits` replaces my own finger limits. Hanging hands sit a little further from the thighs so the relaxed curl clears the trousers. **FAN is now 0 and CLAW is 0.** |
| 18b | Clerk's palms hovered above the desk (his arms could not reach). | He stands closer, and both palms are placed on the desk surface (found by ray cast) with `place_hand` + `flat_palm`. The right hand writes in small strokes. |
| 18c | Officer 1's hand hovered beside the rod; then his right arm reached across his own chest. | The column is a 2.3 cm bar flush with the wall, so no hand can wrap it. He now stands beside it, turned toward it, with his LEFT palm flat on its side face, fingers up (`place_hand` + `flat_palm`, palm 0.6–1.8 cm from the bar). His hand comes away out to his side. He is off for the x-ray beat (he would straddle the cutaway card) and returns behind the card while it is still opaque. |
| 19 | BACKHEAD at frame 1: the clerk's back was nearest the camera. | The opening framing now starts from the clerk's desk side, looking at the hero. **BACKHEAD is now 0.** |
| 20 | INSIDE at 187–193 and 757: the camera was in the brain mesh after the temple dive, and in the desk corner. | Both keys were moved outside the mesh. **INSIDE is now 0.** |
| 21 | Ear-cup arm went straight up (after the clipping fix). | The wrist now sits just below and outside the ear, with the fingers cupped up behind it. Hand audit and clip_scan are both 0 for this range. |
| 22 | Two hand close-ups missed the hands. | The close-up cameras were re-aimed (`scripts/04c_closeups.py`). |

On IK-solved wrists, the library's wrist limit is muted. The orientation is solved explicitly there, and that clamp is what folded the hands into mittens in v002. FK wrists keep the limit.

## Remaining qa_check flags: intended (qa_v003.json)
| Flag | Frames | Why it stays |
|---|---|---|
| PROPMOVE | across the office and theatre | All 118 flagged objects are the dust motes (`Dust000–159`): 2.5 mm specks drifting in the window light. They are ambient air particles, not hand props. |
| EMPTY | 1–67 | The opening establishing move. It frames the whole recruitment office, so the people are small in the frame. |
| EMPTY | 643–655 | The wide growth framing that keeps the door frame in shot for scale (beat 4). |
| FILL | 157–379 | The temple dive and brain cutaway (beats 1–2). The real brain is parented to the hero's head bone, so qa reads it as "hair / top of head". This is the intended anatomy macro on the cyan card. |
| EMPTY | 487–523 | The x-ray body fading back into the office (a dissolve). |
| EMPTY / FILL | 715–721, 823–871, 829 | Beat 5 macros: the hand on the desk, the shoes, and the mirror. The subject is a hand, a shoe or a reflection rather than a head. |
| EMPTY | 1249 | First frame of the blurred-vision POV (beat 8). |
| EMPTY / FILL | 1453–1495 | The whip from the ear past the window into the operating theatre. The shared wall is not rendered while the camera passes it. |
| FILL | 1645–1717 | The dive into the lying patient's head, then the tumour-removal brain macro (beat 9). The skin pass lasts about 5 frames. |
| EMPTY | 1963–1999 | The crane up to the theatre window, looking out onto the cemetery. |
| EMPTY | 2029–2041 | The pull-up over the grave (beat 11, the line "By the time he died"). The grave is the subject. |

**Checks on the final package `DwarfGiant_v003_60fps.blend`:**
- qa_check: INSIDE, BACKHEAD, CLAW, FAN, HOVER, FACEPRESS, CAMJUMP, ROLL and ATTACH are all 0.
- clip_scan: 0 bad ranges.
- BVH hand audit: 0 hits.

## Still open
- No officer caps. The CC-BY cap import lost its axis conversion; see the v002 README.
- Sleeves and hems don't ride up during the growth.
- Officer 1 steadies the rod with a flat palm rather than a wrap grip: the bar is too close to the wall to wrap (`grip_object` found no finger contact).
- Officer 2 stays visible at the left edge during the x-ray beat, in front of the cutaway card.
