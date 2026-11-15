# EarInArm v009k

## v009k: the director's review of v009j (5 items)
1. **Surgeon at the patient's crotch, 221–305:** the 216–295 shot is a close of the patient's worried face (no surgeon in frame).
2. **Mouth wide open:** SHOCK `mouth_open` is 0.75 → 0.18, and the 100 key is 0.45 → 0.1.
3. **Ear attach hold:** a 1.5 s medium profile (1380–1470) at f/8+, with the camera about 30 cm further back. The two faces are at 1346–1379 and 1471–1500. The stitching profile uses the same further framing.
4. **Kneeling assistant:**
   - `nurse_arms(clasp)` brings the arms in.
   - At the tray, `spine` is 10 → 2 and `head` is 16 → 6, with the hands clasped.
   - At the ending she stands upright (spine 0), a step behind and beside him, with her hands low.
5. **Arm out sideways:** `ARM_L_BOARD` wrist is 6 cm in and 7 cm forward, which gives a slight elbow bend. The arm board, incision and pocket are all placed from the arm, so they follow it.

---

# EarInArm v009j

## v009j: the director's review of v009i (6 items)
1. **Mask off the face (beard):**
   - `03c_dress_v009d.py: face_mask()` makes a copy of the body with only the nose-to-chin front skin. It keeps the same shape keys, vertex groups and armature modifier.
   - It is displaced 2.5 mm along the normals, with a 1.2 mm solidify and one subsurf level, in the old mask material. The old shells are hidden.
   - It is done for the surgeon and the nurse.
2. **Carving with no knife:** the right hand holds the scalpel in `pinch_tuck` (the `cup_hold` read as a flat empty hand). The front shot runs 343–455 (three strokes, shavings), then a cut to the carved ear (456–520), then back to him.
3. **Arm into his crotch:**
   - The camera is at the hand end of the board (881–958), so the arm recedes toward the patient and does not point at him.
   - His left hand rests on the forearm (`place_hand`, `point`).
   - Then a cut to the patient's face (959–1062).
4. **Cartilage insert:** 1 s with a push-in.
5. **Back of cap 77–125:** a clean cut at 77 to a side two-shot.
6. **Idle forceps 649–720:** the forceps tip-fix (which lifted the hand 5 cm above the target) is skipped for 640–790, and the keys are lower.
- **Build:** the hands pass had been failing silently on a pose name used before its definition. The build script now stops if the animation or hands pass fails.

- **Mask (final):** a separate mesh bound to the head bone, with a 2 mm shrinkwrap onto the deforming face, smoothed into a cloth sheet. It covers from mid-nose down to the chin; the eyes are clear.
- **At the arm (640–795):** a self-unclip keeps both hands off his belly (the lowered forceps hand had pressed into it).

## Checks (v009j, packed)
- clip_scan: 2 single frames.
  - 1657: as he steps back, his hand brushes the patient's shoulder.
  - 1753: the patient's fingertip on the new ear.
- qa: CLAW, HOVER, FACEPRESS, INSIDE and ROLL are 0.
  - CAMJUMP 17: the intended cuts.
  - EMPTY 16: the inserts.
  - BACKHEAD 1, FILL 6, PROPMOVE 137.
  - ATTACH 7 (361–553, 1345) are a bounding-box artifact. QA picks the wearer from the mask's evaluated `bound_box`, which Blender reports wrongly for this bone-parented, shrinkwrapped mesh (for example, at f361 the bbox centre is at z 0.93). The mesh itself is centred 4–9 cm from his head bone on every flagged frame, and the renders show it on his face.
- cam_clear: 0.
- limb_check: ARMBODY 1446, ARMBACK 17, PROPHEAD 161 (shoulder-root residuals, plus the bump shot's reach).

---

# EarInArm v009i

## v009i: the director's review of v009h (10 items; re-stage simpler)
1. **Headless framings:**
   - 127–155: the patient's face and chest, with the surgeon's hand on the ribs.
   - 343–579: the tray from his front at chest height, his face in the top third.
   - 580–632: he walks toward the camera.
   - 633–795 and 881–1062: two-shots with both faces.
   - The only face-less shots are the two short inserts the director allowed: the cartilage on the tray (156–295) and the growing bump (796–880).
2. **See-through x-ray chest:** removed, together with the arm x-ray and the chest-side pieces. A clean cut goes to the cartilage already on the tray. The torso stays masked under the tee.
3. **Floating hands and props:**
   - 167–283: replaced by the insert.
   - 481–527: in the new tray framing his arms run to his body.
   - 1375–1395: the ear is always in his forceps, and his hand and arm run to him.
   - 1497–1501 and 1651–1657: new cuts.
4. **Disembodied arm, 619–647:** at the arm the patient is in the two-shot, so his arm runs to him in the chair.
5. **Giant gloves, 649–790:** the two-shot at 1.35–1.5 m; the forceps hand stays low by the arm (keys 740/775 lowered).
6. **Long holds:**
   - The grow beat is a 1.4 s bump shot (bump displacement 0.8 to 2.2 cm, patch ledge reduced), then the two-shot.
   - 1441–1640 is cut between profile and two-shot.
7. **Ear attach and stitch:** profile of his head with the new ear to camera; the needle holder and glove are at the ear, the surgeon's face at right, f/8+.
8. **White triangle:** the cabinet glass now has a matte dark material (`CabGlass_Matte`); it mirrored a light.
9. **"Pumpkin" cap, 1243–1295:** the 1240/1266/1300 keys are at about his head height.
10. **Ending:**
    - The camera is on his ear side, so the new ear faces it.
    - His left hand comes up at his side, with the elbow pole keyed down and out. His fingertips rest on the back half of the ear, so the ear stays visible, and he smiles.
    - The nurse walks round the chair (1560–1695) and stands beside him.

- **Lift-out (1071–1250):** framed with his face, the hands with the forceps and ear low over the arm.
  - The tip-fix is skipped there; it pulled his hand up to his face.
  - A name clash (`_b`) had silently broken the animation pass in one build; the build script now stops when that pass fails.

## Checks (v009i, packed)
- clip_scan: 2 single frames.
  - 1657: as the surgeon steps back, his hand brushes the patient's shoulder for one frame.
  - 1753: the patient's fingertip on his new ear.
- qa: CLAW, HOVER, FACEPRESS, INSIDE and ROLL are 0.
  - CAMJUMP 11: the intended clean cuts (156, 296, 580, 607, 633, 796, 881, 1346, 1441, 1501, 1601).
  - EMPTY 36: the two inserts (the cartilage on the tray 156–295, and the arm bump 796–880), which have no head or hand by design.
  - BACKHEAD 2, FILL 4, PROPMOVE 139.
- cam_clear: 0.
- limb_check: ARMBODY 1240, PROPHEAD 161. These are the shoulder-root residuals plus the new two-shots, where both shoulders are seen.
- **Watched** the full preview (every 6th film frame) for items 1, 3, 7 and 8:
  - every shot shows a face, except the two inserts;
  - every glove runs to its arm and body or off the frame edge, and the forceps are always in a hand;
  - the new ear reads in profile during the attach and the stitching;
  - no white triangle (the cabinet doors keep thin soft highlights).

---

# EarInArm v009h

## v009h: the director's review of the v009g preview (nothing else changed)
1. **f793–950, skin filling the frame:** 795 is now a medium shot (`INC + (0.06, -0.28, 0.38)`, lens 44). The close macro holds at 830–840 (about 0.6 s of skin-filling frames, 820–855). From 870 the camera is wide (`INC + (0.08, -0.3, 0.42)`, lens 40), with the forearm, the drape and the surgeon.
2. **f1441–1651, the blurred cap at the right third:** every head-framing key (1414–1625) is moved 20 cm to camera-left, along the camera's left vector `(-0.94, -0.34, 0)`. The cap is out of frame; the glove and instrument stay in, with the arm leaving the right edge.

- The macro hold keys (830, 840) are equal and about 19 cm off the arm. The first try dipped to 9.6 cm at 833–835 (cam_clear flagged it). Skin fills the frame for about 0.45 s (823–850).

## Checks (v009h, packed)
- clip_scan: 0.
- cam_clear: 0.
- qa: CLAW, HOVER, FACEPRESS, INSIDE, CAMJUMP, ROLL and ATTACH are all 0.
  - BACKHEAD 2: f1, f127.
  - EMPTY 3: 625–637.
  - FILL 5.
  - PROPMOVE 136.
- limb_check: ARMBODY 805, PROPHEAD 172 (the shoulder-root residuals).
- Watched the full preview (every 6th film frame). During the stitching (1441–1651) the cap is out of frame; a sliver of his scrub shoulder shows at the right edge, with his arm going to it.

---

# EarInArm v009g

## v009g: the director's review of the v009f preview (blur and fill; nothing else changed)
1. **f841–1013, soft x-ray macro:** f/16 or more for 840–1062 (the depth of field is computed from the focus distance, with a floor of f/16). The close macro holds about 1.4 s (841–925). From 950 the camera pulls back to `INC + (0.08, -0.3, 0.42)`, lens 40, so the arm, the drape and the hand read.
2. **f1081–1201, blurred gloves filling the frame:** the camera keys at 1071, 1130 and 1180 are about 1.8× further from the pocket, and the aperture is f/8 or more for 1063–1250. Both hands, the forceps and the ear are in frame and sharp.
3. **f285–385, his back filling the frame:** new keys at 270 and 284 hold the camera on the patient's side, so his profile shows while he faces the patient. At 302 the camera is on his front-right as he walks to the tray, and 322 is his front at the tray. His back shows for about 4 frames in a medium shot as he turns (286–290).
4. **f1301–1330, top of his cap:** the camera at 1266/1300/1330/1340 is at 1.58–1.6 m (it was 1.8–1.85 m), aimed at 1.2 m, so his face and mask show. The arm still never crosses the patient's body on screen.
5. **f1657–1690, the arm straight out sideways:** while the chair rises (1655–1720), both hands are re-placed on his own thighs every 6 frames (thigh point from the upperleg/lowerleg bones), with the elbows bent. The left hand lifts off the board at 1664 and is in his lap by 1678. A self-unclip keeps the hands on the jeans.

- **Found while watching:** after the lift-out pull-back, the camera sat above him and his cap dome topped the frame at 1141–1255. The 1130/1180/1240 keys are now at about face height, so his face shows above the hands, and the forceps and ear stay to the side of his face. The wider x-ray framing also revealed his hanging hand 2–4 cm into the patient's upper arm at 1045 (an old fault, off-frame before), which is now cleared (unclip 990–1066).

## Checks (v009g, packed)
- clip_scan: 0.
- cam_clear: 0.
- qa: CLAW, HOVER, FACEPRESS, INSIDE, CAMJUMP, ROLL and ATTACH are all 0.
  - BACKHEAD 2: f1, f127, the foreground wipe as he passes the lens.
  - EMPTY 3: 625–637.
  - FILL 5: hair at the frame edge.
  - PROPMOVE 136.
- limb_check (9a0a692): ARMBODY 823, PROPHEAD 172. Shoulder-root residuals as in v009f; nothing into another person.
- Watched the full every-2nd-frame preview (every 6th film frame on sheets). Residuals:
  - his back for about 4 frames as he turns at 286–290 (medium shot);
  - the top of his cap for about 12 frames at 1237–1249 as he bends over the arm (medium shot, under a quarter of the frame).

---

# EarInArm v009f

## v009f: the director's review of the v009e preview
1. **Tray hand (361–457), option (a):** the left hand rests on the tray beside the cartilage with relaxed, even fingers (`relaxed_even`), the fingertips at the cartilage's edge, and the wrist in line with the forearm (`place_hand`). The fingers point across at the cartilage, not at the camera: pointing at the camera foreshortened the hand into a fist. The scalpel hand is 3 cm further left for the whole carve, so it never lies over the left hand. Both hands were checked at 540×960 at f373, 397, 421 and 445: two separate hands, no ring, no claw. The old carving keys for that hand are removed, so the placement isn't fighting them.
2. **f1300–1350 (the hug), and every other frame where the surgeon's arm crossed the patient's body on screen (director's rule 2):**
   - **1300–1340:** a wide shot from in front of him, from the patient's foot side. He carries the ear in front of his own chest, his left hand at his side, and his body and arm read clearly beside the patient's. A commented-out left-hand carry key (an inline-comment bug) is restored.
   - **1358–1396:** tight on the patient's face, from in front. His reach from the arm to the head happens outside the frame. The forceps bring the ear in from the edge, beside the patient's head, with the arm going off the frame edge, using the v009e approach keys (over and outside the head, then in from the side). Then the shot goes out to the approved head framing (1414 on). Every framing that showed the reach put his hand across the patient's chest: I tried four hand paths and three camera paths, and per rule 1 I removed the risk instead of iterating further.
   - **1141–1243 (lift-out):** seen from the patient's foot side, over the arm, so his forceps arm no longer crosses the patient's shoulder and chest on screen. The camera no longer moves behind his head (his cap filled the frame at 1250–1267).
   - **1240–1300:** the lifted ear stays low over the arm and comes straight back to him (it went up by the patient's chin on screen). A self-unclip (1256–1300) keeps that hand off his own belly.
   - **1625–1660 (end of stitching):** the camera pulls away from his head instead of sliding 29 cm past his cap.
   - Fixed two camera keys (1385, 1425) that an inline comment had silently disabled.
3. **End (1741–1770): no ear touch (director's simplify rule).** I made two attempts at the touch, and neither was clean. The old world-space keys swept his hand across his face at f1749, and keys placed from the ear put it at his throat. So his left hand stays relaxed out of the shot from 1715, and the last beat plays on his smile with the new ear in view. The story beat and its frames are unchanged.
- **Clip-scan false hit at the ear site (1402–1416):** the patient's original ear is a shape-key stub, and its folded back faces faced inward, so a fingertip 7 cm outside the head counted as "inside". The stub is now sunk 2–3 mm under the scalp. It is covered by the dressing early on and by the new ear from 1404.

- **Tray, after carving (471–535):** the old keys laid the left hand over the carved ear. It now stays beside the ear until the pinch at 536, so the ear is uncovered (the "hands lift away to reveal the ear" beat).
- **Opening (118–132):** the camera now rounds the surgeon (it passed 9 cm from his hair). He still crosses the lens as a quick foreground wipe at about 120–128, at least 44 cm from the camera. QA marks f127 BACKHEAD for it.

## Director's rules 1–4: watched the full preview (every 6th frame on contact sheets, 270×480; doubtful spots re-rendered at 540×960)
1. **Hand/prop actions are clean, or the risk is removed.** Tray hand: placed. End ear touch: removed after two failed tries. The ear's trip to the head: kept off-frame, with the camera tight on the face.
2. **No arm crosses another person's body or face on screen.** The closest frame is 1405: his glove holds the forceps at the ear site, beside the patient's jaw line, as in v009e.
3. **No camera move passes through or brushes a body, arm, cap or wall.** cam_clear at 10 cm: 0 frames. At 25 cm, the only hits are the macro holds on the forearm (693–1159, 11–21 cm from the arm or glove, holding, not passing) and nothing else.
4. **Every hand on screen is connected to its arm**, or the arm goes off the frame edge (the macros, the forceps entering at 1364–1396).

## Checks (v009f, packed)
- clip_scan (40c131b): 0.
- qa (e7b25f7): CLAW, HOVER, FACEPRESS, INSIDE, CAMJUMP, ROLL and ATTACH are all 0.
  - BACKHEAD 2: f1, f127 (the wipe above).
  - EMPTY 3: 625–637.
  - FILL 5: hair at the frame edge at 85, 121, 649–661.
  - PROPMOVE 131.
- cam_clear: 0.
- limb_check (the director's, 9a0a692), step 2: ARMBODY 759, PROPHEAD 184.
  - Every ARMBODY line for 1300–1350 is in `armbody_1300-1350.txt`: 58 lines, all "inside own torso", 2–5 points each.
  - Re-run with point labels: all of these are upperarm01 points from the shoulder joint to mid-shaft (4–8 cm under the clavicle/shoulder-weighted skin where the arm meets the body), plus the patient's right upperarm02 head. There are no forearm or wrist points, and none inside another person.
- limb_scan: residual ranges as before (shoulder-root hits).

---

# EarInArm v009e

## v009e: the director's review of the v009d preview
1. **Tray (351–443):** the hands start apart, so they never stack. The left hand holds the cartilage in `pinch_light`: the index and thumb pinch, the other fingers lightly curled (`pinch_tuck` read as a ring). The right hand holds the scalpel, then lies flat on the tray.
2. **The patient's arm:** the arm board was parented to the chair's recline pivot, so it tilted up across the forearm and his hand showed under it. It is now world-placed under the reclined forearm and hand, sloping with the arm, and his hand rests relaxed on it (`relaxed_even`) from 470 to the end of the beat.
3. **X-ray macro (840–1110):** f/11 or more (at f/5.6 it was soft, with about 2 cm depth of field).
4. **The ear to the head:** the ear stays in the forceps tips and comes in from the side, close to the head. It no longer rises 14 cm above it. It is lowered onto the head over 1404–1440.
5. **Surgeon at the head:** he stands right beside the head on the ear side. The camera is in front of him at the front-outer side, so his shoulder and body read, and nothing blocks the ear. His arm axes were tested against Chair_Headrest and Chair_Back over 1300–1700, with 0 hits. His free left hand waits relaxed at his side (reaching the top of the head from there crossed his own body).
6. **Stray gloves:**
   - f7: the opening is wider, so the surgeon's whole body is in frame with his hands.
   - f157: the free hand is flat on the chest from 136, with no hovering.
   - f277: his carried left hand is at his side.
   - The new contacts these created are cleared: his hand at the patient's knee (unclip, 268–304), his walk past the patient's hand on the board (route 20 cm wider), and his hand on its way to the ear (a key over and outside the head).
- **Ending (1655–1685):** the camera swings to the front-left of the patient, so the surgeon stepping back no longer blocks it.

## Checks (v009e, packed)
- clip_scan: 0.
- qa: CLAW, HOVER, FACEPRESS, INSIDE, CAMJUMP, ROLL and ATTACH are all 0.
  - BACKHEAD 1: f1.
  - EMPTY 3: 625–637, the high shot following the forceps to the arm on the wider route.
  - FILL 8: the surgeon's cap at the frame edge.
  - PROPMOVE 124: as before.
- cam_clear: f123 only (9 cm from the surgeon's hair).
- limb_scan: the same residuals as v009d (listed below), plus one 1.6 cm fingertip brush on the nurse at f593.
- Headrest/chair-back check: 0.

---

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
  - BACKHEAD 1: f1, the wide opener with the surgeon's back to the camera.
  - EMPTY 2: 625/631, the high shot that follows the forceps to the arm. The arm, the glove and the ear are in frame.
  - FILL 22: the push-ins at 85 and 121; the surgeon's cap at the frame edge at 877/883 and 1327; the head close-ups at 1429–1501 and 1633–1651, where the ear is placed and the stitching ends.
  - PROPMOVE 120: items in the forceps tips, the grafted ear and the shavings, as accepted in v009c. The hand tools themselves are 0.
- **limb_scan (new, `pipeline/limb_scan.py`):** the upper-arm, forearm and hand bone axes of every character are tested against every body's skin, including their own torso, head and legs. Visible hits that remain:
  - **Patient.L upper arm, 569–1717, 8.3 cm, constant:** the arm lies out on the arm board, and the sample by the armpit is under the chest skin. It does not show in renders.
  - **Surgeon upper arm against his side, up to 7 cm:** during the hand-to-chest moves (77–289) and the walks (293–613).
  - **Nurse forearms, 45–213, 2.6 cm:** against her hips while she walks (scrub-covered).
  - **Single frames:** fingertips on the patient's chest during the press (225, 273, 285); the patient's hand passing over his chest to the ear (1737).
- **cam_clear (new, `pipeline/cam_clear.py`):** the camera comes within 10 cm of a character only at f123, where it passes 9 cm from the edge of the surgeon's hair.

## Moving preview
`review/preview_v009d_270x480_every2nd.mp4`: every 2nd frame at 30 fps (real time), 270×480, 2 samples, with the frame number in the corner. I checked every 6th film frame in order, start to finish. The first pass found the problems below, which were fixed before this final preview was rendered:
- f19 and f79–91: the surgeon's back or cap filled the frame. The opening now stays on the patient's side, then arcs over the surgeon to the front.
- f367–391: the carving hands were too close; the camera now pulls back.
- f1393–1441: the camera sat on the skull; the ear placement is now framed like the stitching.
- Second pass: at f85 the surgeon's head blocked the move to the profile, so a high key at f84 now gives an over-the-shoulder two-shot. At f1440 the ear snapped about 15 cm from the forceps onto the head; it is now lowered onto the head over 1404–1440.
- The black forearm in the first preview was a preview-only artefact (too few light bounces for the skin's subsurface scattering). The full-quality render was checked at f661.
