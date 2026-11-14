# EarInArm v009d: fixes for the client's rejection of v010

The client's frame numbers are in the synced v010 timeline (1–1572). I mapped them back to this file's timeline (1–1770) by matching v010's camera keyframes against v009c's. For example: v010 200→229, 240–260→274–297, 420–440→506–534, 1060–1100→1233–1277, 1270–1440→1503–1639. Every frame below is in this file's timeline.

## Major items (client)
| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | X-ray: forceps through the palm, gloves through each other (~229) | The forceps lay along the wrist axis, so its back end ran 4 cm into the palm. The free hand was placed on top of the forceps hand. | The forceps is tilted 20° out of the palm, like a pen. The tip solve and the re-bake use the same tilt. The free hand rests on his upper-left chest, clear of the forceps hand. |
| 2 | Walking to the table, the arm bends backwards (274–297) | His yaw blended from −140° to 0° through −70°, so he walked backwards. The hands were keyed at fixed world points while his body moved. | He turns on the spot toward the table (281–298), then walks forwards and squares up (299–338). During the walk both hands are keyed relative to his body every 4 frames, in front of the torso. |
| 3 | Tray: a hand comes out of his torso (308–331) | Same world-space hand keys as #2. | Body-relative carry keys, plus an unclip pass against his own torso (268–340). |
| 4 | Tray: crushed glove, hands into the cartilage and each other (506–534) | After carving, the right hand stayed over the block while the left pinched the ear. He also stood too close, so the IK elbows folded into his belly. | The right hand moves aside to the tray edge (456–476) and lies flat there. He stands 8 cm further back with less lean, and both elbow poles point out and back. The left hand pinches the ear (`grip_object`). |
| 5 | Turning to the patient: arms out of the body, a hole in the scrubs, the patient's arm floating (573–607) | Same walk faults as #2. The body under the scrubs was deleted by the MPFB clothes mask, so a sleeve gap showed the hollow inside as a dark hole. The arm board was placed using the forearm at f400, mid-move. | Both walk legs face the direction of travel, with body-relative carry keys and an unclip pass. The surgeon's mask is off, and the body faces under the scrubs wear the scrub material, so a gap reads as cloth. |
| 6 | Ear transfer: the ear goes into the surgeon's eye (1233–1277) | The forceps was lifted to face height (+25 cm) while he leaned over. | The lift is lowered to +14 cm. From 1300 to 1372 the ear is carried in front of his chest, relative to his body. |
| 7 | Head: a tool in the temple, forceps scratching the scalp, his cap merging into the head (1277–1408) | The needle holder was parked at the f1501 pinch point for every earlier frame, which put it in the temple. He stood behind the skull and leaned in. | The needle holder is hidden until it is in his hand (1500). The forceps lift off the scalp after the ear is placed and are hidden once put down (1503). He stands beside the head on the ear side, taller, with a gentle lean. |
| 8 | The grafted ear faces backwards | The ear model's front/back axis was reversed on the left side. | The Ear_New mesh is mirrored along its front/back axis, with normals flipped back. |

## Also (director)
| # | Fix |
|---|---|
| 9 | The camera passed through the surgeon's head at 43–81. It now goes round the front of the surgeon and over his head (`cam_clear`: one frame at 9 cm, f123, the edge of his hair). |
| 10 | The dressing is seen from the front-left (face profile and bandage), not from behind the head. |
| 11 | At f127–145 the camera is wider (28–32 mm) and the surgeon's body is in frame with his arm. |
| 12 | Chest x-ray: the real torso skin is kept (the clothes mask is off only from 139 to 348, render only). The skin goes glassy around the rib cage and only the tee over the chest goes glass, so the torso is body-shaped and the arms are attached. The legs stay masked under the jeans (a second, legs-only mask). |
| 13 | The arm on the camera side is back: carry keys during the walk (see #2). |
| 14 | Nurse: her torso and legs wear the scrub material, her hands the nitrile glove, and she has a cap and mask bound to her head bone. Her hair is hidden under the cap. She no longer carries the dish, and her arms hang at her sides. |
| 15 | Ghost disc: the arm patch now uses the patient's own skin material, with UVs copied from the forearm under it. It is hidden while the arm is x-rayed. |
| 16 | The ear on top of the skin: the ear in the arm is now 60 % size and 13 mm down, under the skin. The incision line is hidden during the x-ray (it floated). |
| 17 | Crater: the arm x-ray is gentler (60 %) and has a smaller radius. During that beat both of the surgeon's hands hang at his sides, out of the macro. |
| 18 | The floating palm-up glove (1100–1325): the left hand hangs at his side during the growing beat. After that it is flat on the scalp from 1392 to 1650. |
| 19 | Wound: the incision stays as a closed red line after the ear comes out. The arm patch stays to the end. The surgeon's mask is 10 % larger so his nose no longer pushes through it. |
| 20 | Neck: the patient's head turn is 18° (was 28°), with a little forward pitch. |
| 21 | The join vessels and the glow ball stood off the skin, so they are not shown. |
| 22 | Stitching: the needle holder is in his pinch and points along his reach. Each stitch is solved on the final pose to within 3 mm: the needle is on the stitch, then lifts 3 cm. He stands beside the head and the camera is wide enough to show the hand, holder, thread and stitches. The stitches sit half in the skin. |
| 23 | End hand: the patient's fingers are relaxed (`relaxed_even`, spread 0) on the ear, not cup_hold. |

## Checks on the packed `EarInArm_v009d_60fps.blend`
- **clip_scan (40c131b):** 0 bad ranges.
- **qa_check (e7b25f7):** CLAW, HOVER, FACEPRESS, INSIDE, CAMJUMP, ROLL and ATTACH are all 0.
  - BACKHEAD 1 (f1, the wide opener; the surgeon's back is to the camera).
  - EMPTY 2 (625/631, the high shot following the forceps to the arm).
  - FILL 27: the push-ins at 19, 79, 85 and 121; the surgeon's cap at the frame edge at 877/883 and 1369–1501; the stitching shot at 1633–1651.
  - PROPMOVE 115: items in the forceps tips, the grafted ear, and the shavings (all accepted in v009c).
- **limb_scan (new, `pipeline/limb_scan.py`):** the upper-arm, forearm and hand bone axes of every character are tested against every body's skin, including their own torso, head and legs. Visible hits that remain, and why:
  - **Patient.L upper arm, 569–1717, 8.3 cm, constant:** the arm lies out on the arm board. The sample by the armpit is under the chest skin; it does not show in renders.
  - **Surgeon upper arm (upperarm02) at the walks, 293–613, up to 4 cm:** the upper arm brushing the side of the torso as he walks.
  - **Nurse forearms, 5–213, 2.5 cm:** forearms against her hips while she walks. They are now covered by scrub material.
  - **Single frames:** f225, 273 and 285 (fingertips on the patient's chest during the press); f1737 (the patient's hand passing over his chest to the ear).
- **cam_clear (new, `pipeline/cam_clear.py`):** the camera comes within 10 cm of a character only at f123 (9 cm from the surgeon's hair).

## Moving preview
`review/preview_v009d_270x480_every2nd.mp4`: every 2nd frame at 30 fps (real time), 270×480, 2 samples, with the frame number in the corner. I watched it start to finish before sending.
