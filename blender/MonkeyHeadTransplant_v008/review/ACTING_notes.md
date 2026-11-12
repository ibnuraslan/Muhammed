# MonkeyHeadTransplant v008: acting review and fixes (from v006)

The beat frames are unchanged: 1, 259, 391, 673, 889, 1027, 1207, 1393, 1561 (`beats.json`). No VO was added.

## Problems found in the v006 half-second sheet (`before_sheet_v006_0.5s.jpg`), with fixes
| v006 frames / time | Problem | Fix in v008 |
|---|---|---|
| 1–120 (0–2 s) | The surgeon's back and sleeve fill the frame, and his face isn't readable on beat 1. | The camera now starts on the far side of table 1: the masked face, the marker pen and the monkey are all in view. |
| 1–240 | The pen hand used a hand-set curl, and the pen followed a wrist offset (not in the fingers). | `hand_poses` **pinch**. The pen's position is the midpoint of the thumb and index tips on every key. |
| 214–380 (head carry) | The hands hovered beside the head with flat or claw fingers (close-up). | `grip_object` on the head every 4 frames: the palm goes on the surface, the fingers close until they touch, and the thumb opposes. 68 grips, all fingers in contact. My own IK keys are skipped while the head is held. |
| 221–235 | The right hand passed through the surgeon's torso on its way to the head. | A delayed, outward arc; orientation is blended from the pen pose. |
| 400–670 (stitching) | Tools followed a wrist offset; the gloves were pale blobs. | The tools are placed at the seam (tip on the stitch) and `grip_object` pinches each one (92 grips). f/11 for the macro. |
| 200–918 (nurse bowl) | The bowl floated by her wrist with no fingers on the rim. | The bowl sits in front of her, and `grip_object` holds the rim from above every 6 frames. |
| 452–508 (gas knob) | The hand reached for the knob without touching it. | `grip_object` on the gauge face. |
| 1–1770 (anaesthetist) | Hand-set curl beside the breathing bag; the palm was in the air. | `grip_object` on the bag every 30 frames, with no other right-hand keys. |
| 1380–1560 (monitor) | The surgeon "held a clipboard" that doesn't exist: mimed hands. | He watches the monitor with both hands relaxed at his sides. |
| 1417–1489 | `clip_scan` bad range: the surgeon's hands were inside the nurse's gown at the monitor. | The nurse moved to (3.62, 1.05); no knob reach. `clip_scan` now reports 0 bad ranges. |
| 1530–1620 (25.5–27 s) | The nurse's gown filled the frame. | Same nurse move. |
| 1–97, 1207–1765 | QA INSIDE: the camera sat inside the transparent x-ray void sphere. | The void exists only from 1016 to 1212, with normals facing in. |
| 1189–1333 | The transparent table-2 group was still renderable (QA FILL). | That group is hidden for good from 1187. |
| all | Hand-set finger angles. | Every hand uses `hand_poses` presets or `grip_object`, plus `add_hand_limits` on all three staff. |

## QA (`qa_v008.json`, step 6, beats.json)
- **HOVER, CLAW, FACEPRESS, INSIDE and CAMJUMP are all 0.**
- **CLIP:** `clip_scan_v008.json` has 0 bad ranges.

Remaining flags, all intended:
- **ROLL, 113 frames (682–967 and 1087–1135).**
  - 682–967 is the deliberate 90° camera roll during the face push-in. The monkey lies on its side, and the director asked (C note, Nov 11) for the face upright on screen so the blinks close top-down.
  - 1087–1135 is inside the x-ray void (no horizon) while the monkey is carried, upright, with the camera from the table to the chair.
- **EMPTY, 188 frames, and FILL, 38 frames.** The film's main character is the macaque, which is not an MPFB rig, so QA counts monkey-only frames as "no character in view". This covers:
  - the neck-line close-up (163–193)
  - the stitching macro (391–733)
  - the face push-in and the x-ray (955–1375)
  - FILL "T2_Drape" (961–1033): the sheet under the monkey's head in the face macro
  - FILL "hair / top of head" (1189–1267): the monkey's fur at the void exit
  - EMPTY/FILL at the ECG close-up (1429–1543): the oscilloscope that illustrates "technically a success"
  - frames 7–13: the wide establishing shot where the surgeon is small in frame

## Known remaining issues (honest)
- Close-up f470 L (`hand_contact_closeups_v008.jpg`): the forceps hand sits high, near the surgeon's mask, while he leans in. It doesn't touch the face (FACEPRESS 0), but it reads awkwardly. A follow-up should lower the forceps contact.
- The surgeon's sleeve passes close to the lens at 2.0–2.5 s and 7.0–7.5 s, and his gown at 26–26.5 s (a foreground blur for under 0.5 s).
- The monkey has no body rig, so the chair pose is the asset's own sitting pose.
