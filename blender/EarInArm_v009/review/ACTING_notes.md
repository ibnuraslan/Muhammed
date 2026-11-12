# EarInArm v007 → v009: acting review

Beat frames are unchanged from v007: 1, 127, 343, 565, 775, 1063, 1309, 1501, 1645. End frame 1770.

## Problems found in v007

Sources: `sheet_before_v007_05s.jpg`, plus `qa_v007_before.json`.

QA counts: CLAW 104, FACEPRESS 20, FILL 70, EMPTY 29, HOVER 1, INSIDE 1, CAMJUMP 2.

| v007 time (frames) | Problem |
|---|---|
| 0.5–2.0 s (30–120) | **Shock:** the patient's right palm is pressed over his mouth, and the left hand presses the dressing on his ear (FACEPRESS ×20). |
| 0–1 s (1–60) | **Surgeon:** both hands curled into claws in the air (CLAW). |
| 2.8–3.0 s (170–181) | **Cut:** a hard camera jump into the rib studio, hidden only by a tee-coloured membrane (CAMJUMP f172). The membrane frames are empty (EMPTY/FILL). |
| 3–5.5 s (181–335) | **Rib studio:** a floating rib cage with a cloned surgeon. The prop fills the frame and the characters cover under 15 % (EMPTY ×20). The camera passes inside the clone (INSIDE f241), and the clone's hand hovers by the ribs (HOVER f223). |
| 5.6–5.8 s (337–345) | **Cut:** the second hard jump (CAMJUMP f343). The cartilage macro fills the frame (FILL). |
| 6–9 s (343–560) | **Carving:** the scalpel hand is a curled fist with no tool contact (CLAW in the air). |
| 9.5–10 s, 20–23 s (595–640, 1231–1273, 1405–1417) | **Framing:** the surgeon's cap or hair fills the frame (FILL hair > 25 %). |
| 10–12 s, 18–21 s | **Arm:** the forceps hand floats a few cm off the incision (CLAW in the air). |
| 13.5–17 s (811–1051) | **X-ray macro:** the camera is under 12 cm from the arm (FILL surface < 12 cm). |
| 24–27 s (1531–1603) | **Stitching macro:** the camera is about 10 cm from the ear (FILL surface < 12 cm). The surgeon's hand blobs pass across the lens (24.5–25 s). |
| 28.8–29.4 s (1735–1741) | **Ear touch:** the left hand touches the new ear. This is intended, but it counts as FACEPRESS. |

## Fixes in v009

- **Hands:** every hand pose now goes through `pipeline/hand_poses.py` (`add_hand_limits` and `apply_pose`). No finger angles are set by hand.
  - Patient shock: both hands come up open in front of the chest (`open_alarm`). Nothing touches the face.
  - Surgeon: holds the forceps in a `pinch` from frame 1, presses the chest with his free left hand (`flat_palm`), uses a pen-style `tripod` on the scalpel, and a `pinch` on the cartilage, forceps and skin edge.
  - Nurse: `relaxed`, then `cup_hold` on the kidney dish.
- **Tools:** each tool now sits at the thumb–index pinch point and is oriented with the hand. A 3-pass solve re-keys the hand so the tool tip lands on its target.
- **Beat 2:** restaged in the room, so there are **no camera jumps** (CAMJUMP 0).
  - The patient's tee turns x-ray glass, and the real rib-cage model sits inside his chest.
  - A glowing cut line circles the costal cartilage, and the surgeon's forceps lift the piece out.
  - He walks it to the tray (281–338) and puts it down at 334.
  - The rib studio and the cloned surgeon are deleted.
- **Chair recline:** moved to 350–470, so the patient sits upright for the harvest. His arm moves to the arm board while the chair reclines.
- **Macros:** pulled back to at least 15 cm with longer lenses, for the arm x-ray (830–1030) and the stitching (1465–1625).
- **Camera:** the 262–322 path now flies wide of the surgeon's walk.

## Remaining flags (with reasons)
Both checks were run on the packed `EarInArm_v009_60fps.blend`, step 6, with `beats.json`.

**qa_check (`qa_v009.json`):** HOVER 1, CLAW 0, FACEPRESS 0, INSIDE 0, CAMJUMP 0, ROLL 0, EMPTY 0, BACKHEAD 1, FILL 15.

| Frame | Flag | Reason |
|---|---|---|
| 559 | HOVER: Surgeon.R near Shaving13 (14.3 cm) | Intended. The right hand has put the scalpel down (464) and rests just above the tray, next to the shavings, before it takes the forceps at 566. It holds nothing. |
| 1 | BACKHEAD: Surgeon | Intended. It's the wide establishing frame: the surgeon stands with his back to the camera beside the patient, and the patient's face is the subject. |
| 73, 139 | FILL: surface < 12 cm | The push-in to the dressing (73) and to the chest (139). The dressing and the tee fill the frame on purpose, and the frame reads as the bandaged ear or the chest. |
| 601–631, 1177–1273 | FILL: hair / top of head 25–29 % | The surgeon's cap passes through the foreground while the camera tracks the forceps to the arm (601–631) and back to the head (1177–1273). The tool and the arm stay readable. It is just over the 25 % limit, not on a beat frame. |

**clip_scan (`clip_scan_v009.json`):** 6 bad ranges remain (≥ 25 hand or finger vertices more than 2 cm inside something visible to the camera). **This target (0) is not met.**

| Frames | Who | Verts | What |
|---|---|---|---|
| 25 | Patient, into other | 34 | Patient's right hand rising in alarm, fingertips briefly into the surgeon's gown sleeve. |
| 577 | Surgeon, self | 43 | Taking the forceps: fingers fold into his own palm for one sample. |
| 691 | Surgeon, into other | 195 | Fingers of the forceps hand into the patient's forearm at the incision. |
| 1375 | Surgeon, self | 57 | Fingers into his own hand while lowering the ear. |
| 1423–1447 | Surgeon, into other | 45–83 | Fingers into the side of the patient's head while placing the ear. |
| 1729–1735 | Patient, self | 39–133 | The patient's fingertips sink into his own head when he touches the new ear. |
