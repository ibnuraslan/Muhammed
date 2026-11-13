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

## v008b (director's last round)
1. Camera off the arm's path: keys 121/241 raised 0.2–0.3 m and moved 0.3 m sideways; 420/480 raised 0.17 m. Key 1560 now aims at the monkey's face in the chair.
   - **Still open:** at 25.5–26.5 s the surgeon's gown passes between the camera and the chair and fills the frame (visible in `after_sheet_v008b_0.5s.jpg`).
2. f200: `place_hand` with the palm flat on the shoulder surface (4 mm), plus `flat_palm`.
3. f470 forceps: the left contact is lower on the seam (9 cm out, side-down direction), so the wrist stays below the chin.
4. f300 bag: `grip_object(..., grip="wrap")`, the contact 8 % inside the bag radius, keyed every 10 frames.
5. f480 knob close-up: aimed at the hand-knob contact from 0.5 m.
6. f1270 wave: `relaxed` with spread 5.
- Also: both hands are pushed off the surgeon's own chest at 195–250 (clip_scan had flagged frame 229 after the camera change).
- QA (director qa_check 771d2da, clip_scan 3cfc53c): 0 for HOVER, CLAW, FACEPRESS, INSIDE, CAMJUMP. ROLL 113 (the same approved ranges), EMPTY 181, FILL 33 (intended, as in v008). clip_scan: 0 bad ranges.

## v008c (beat 1561)
- The camera at the beat is now left-front of the chair and 0.3 m higher. Keys: 1500 `SCR+(0.06,-0.36,0.05)`, new 1530 `(2.55,-0.42,1.45)`, 1560 `(1.98,0.22,1.32)` aimed at the monkey's eyes, 1620 `(2.0,-0.55,1.55)`. The camera stays on the near side and doesn't swing back across the surgeon.
- Strip: `strip_1530-1590_v008c.jpg` (frames 1490–1590, every 10). The monkey's face reads from 1520 through 1590.
- Known: around f1510 the surgeon's sleeve wipes the foreground for about 0.15 s as the camera pans off the monitor.
- QA: HOVER, CLAW, FACEPRESS, INSIDE and CAMJUMP are 0. ROLL 113 is only the approved ranges. clip_scan finds 0 bad ranges.
  - Intended flags: FILL "hair/top of head" 1537–1609 (the monkey's head filling the face framing) and BACKHEAD Surgeon at 1561 (his back at the frame edge, with his head out of frame).

## v008d (client rejection: floating pen and mask)
**Root cause:** `add_hand_limits` was called at the end of `03_animate.py`, after every grip and the pen had been solved. Its wrist and finger limits then rotated the hands about 15 cm off the props they had been fitted to. The limits are now added right after the rigs are built, so every grip is solved with them on. A final contact bake then places each held prop in the evaluated pinch.

1. **Pen**
   - Baked every frame 1–226 from the evaluated right hand. This is equivalent to Child Of on hand.R, baked; no keys move the pen on its own.
   - The tip sits on the skin at the dash being revealed (reveal keyed every 2 frames from the same angle). The barrel runs through the thumb–index pinch and out over the web.
   - Grip-to-tip distance is 4.9–7.7 cm.
   - At 205–226 his hand carries the pen down onto the drape. It rests there from 226 (its last baked pose), with no jump.
   - Left hand: `flat_palm` on the top of the monkey's skull.
2. **Masks** (Surgeon, Nurse, Anaes): an Armature modifier with weights copied from the nearest face vertices, plus a Shrinkwrap onto the face (2 mm), then Solidify. qa ATTACH: 0.
3. **f1 camera**: 22 cm higher, off the foreground drape.
4. **Prop audit** (every object that moves; qa PROPMOVE, director e7b25f7):

| Prop | Frames moving | Carrier / contact |
|---|---|---|
| MarkerPen | 1–226 | Baked to the surgeon's R pinch (finger tips 0.0 cm from the pen bbox) |
| NeedleHolder | 400–672 | grip_object pinch R; the final bake snaps each key to the evaluated pinch |
| Forceps | 400–672 | grip_object pinch L; same final bake |
| Trolley | 1–150 | Nurse pushes with both palms flat on the top (place_hand) |
| Tray, Instruments, Bowl (on trolley) | 1–150 | Parented to the Trolley (ride along) |
| Bowl | 200–917 | Carried on the nurse's flat L palm (place_hand, hold_flat_object) |
| Bowl | 918–960 | Slips and falls to the floor: intended drop (beat 5 clang) |
| Monkey head (MK_Head) | 250–380 | Both surgeon hands, grip_object (approved v008) |
| Breathing bag | all | Anaes R wrap grip, keyed every 10 frames |
| Gas knob (gauge) | 452–508 | Nurse R grip_object |
| Scalpel | n/a | Never moves |
| ClockHandHour, ClockHandMin | 1693–1765 | Wall clock mechanism: intended, no hand |

- QA (qa_check e7b25f7, clip_scan 3cfc53c): HOVER, FACEPRESS, INSIDE, CAMJUMP and ATTACH are 0.
  - PROPMOVE: only the clock hands (intended).
  - ROLL 113: the approved ranges only.
  - CLAW: 0 (the Anaes R bag hand at 641–661 uses cup_hold between grip keys; follow-up commit).
  - clip_scan: 0 bad ranges.

- **24.5 s monitor (director item 2):** keys 1440/1460/1480/1500 lie on one straight push-in line, aimed at the screen. Before, the spline bowed toward the screen and swung the aim onto the black case side. Strip: `strip_1440-1530_v008d.jpg`.

## v008e (held tools: director, Nov 13)
Base: 24ce61b (the approved v008d / v010). The 1703083 monitor-camera change is undone, so only the tools differ from v010.

**Root cause:** `Forceps` and `NeedleHolder` are thin bars, 0.5 × 0.3 × 12 cm and 15 cm. The previous snap matched bone tails only at the grip keys (every 6 frames), using a contact point 1.5 cm from the bar's centre. On the evaluated mesh the left fingers were 3.8–4.4 cm off the shaft. The tools were also visible from 382, before any hand held them.

**Fix (`03_animate.py`, end of the script, after all hand keys):**
- Both hands are keyed `pinch` on every frame 392–671, with no interleaved finger keys. Thumb-to-index is 1.0 cm; thumb-to-ring is 3.7 cm.
- Every frame 392–671, each tool is baked from the evaluated fingertip vertices. This is equivalent to Child Of on the fingertips, baked.
  - Forceps (L): the shaft passes through the thumb–index pinch, with the tip toward its seam point.
  - Needle holder (R): the ring midpoint sits between the thumb and ring-finger tips, with the ring axis along thumb→ring and the jaws toward the seam.
- The tools are visible only from 392 to 671, the frames a hand holds them.

**Measured on every frame** (`review/toolmeas.py`: evaluated tool mesh including children, against evaluated fingertip vertices of the holding hand; cm):

| Tool | Frames | bbox to nearest fingertip vertex, max | Surface to nearest fingertip, max | Per finger, max |
|---|---|---|---|---|
| Forceps (L) | 392–671 | 0.0 | 0.06 | thumb 0.06, index 0.14 |
| NeedleHolder + rings (R) | 392–671 | 0.0 | 0.03 | ring finger 0.05, thumb 0.55 |
| MarkerPen (R) | 1–225 | 0.0 | 1.59 (at f225, setting it down) | index 1.59, thumb 1.86 |

- QA (qa_check e7b25f7): HOVER, CLAW, FACEPRESS, INSIDE, CAMJUMP and ATTACH are 0. PROPMOVE: only the clock hands. ROLL: only the approved ranges. clip_scan: 0 bad ranges.
- Strip: `strip_400-700_540x960_v008e.jpg` (540×960, every 20 frames, 400–700).
