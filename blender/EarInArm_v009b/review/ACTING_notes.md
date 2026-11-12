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

## v009b (director review of v009): hands closed on what they hold
See `../README.md` for the full list. Each point from the review:
1. **Chest x-ray (3.0–4.5 s):** the forceps hand is `grip_object` pinch on the shafts, with the tip at the rib site. The free hand is `place_hand` + `flat_palm` on the chest beside it. The forceps stays (it lifts the piece out at 4.3 s), so no tripod scalpel is used here.
2. **Tray (9.0–9.5 s):** the left hand is `grip_object` pinch on the carved ear; the right hand is `place_hand` flat on the tray.
3. **f1140:** the forceps hand is `grip_object` pinch, re-applied every 12 frames, with the forceps re-baked to the pinch point.
4. **Nurse:** relaxed at her sides (`apply_pose relaxed`).
5. **Ear placement (1392–1498):** the left hand is `place_hand` flat on the scalp above the ear; the right hand pinches the forceps (`grip_object` + pinch).
6. **Patient's free hand (480–1640):** relaxed on the armrest (`place_hand`).
7. **Final ear touch:** no clip_scan hit inside 10 cm at 1729; f1735 is listed below.
8. **f25, f577, f691, f1375:** an unclip pass pushes the hand vertices at least 1 cm off the surface. f577, f691 and f1375 are now clean; f25–31 is listed below.
9. **Camera:** the gown-filled stretches are re-framed (9.5 s from across the tray; 11.5–13.5 s and 16.5–18.5 s raised 25–30 cm), and the camera starts beside the surgeon.

## Remaining flags (with reasons)
Both checks were run on the packed `EarInArm_v009b_60fps.blend`, step 6, with `beats.json`.

**qa_check (`qa_v009b.json`, 771d2da):** HOVER 0, CLAW 0, FACEPRESS 0, INSIDE 0, CAMJUMP 0, ROLL 0, EMPTY 0, BACKHEAD 1, FILL 15.

| Frame | Flag | Reason |
|---|---|---|
| 1 | BACKHEAD: Surgeon | The wide establishing frame. The surgeon stands beside the patient, who is the subject. |
| 73, 139 | FILL: surface < 12 cm | The push-ins to the dressing and to the chest. |
| 601–631, 1177–1273 | FILL: hair / top of head 25–29 % | The surgeon's cap in the foreground while the camera follows the forceps between the tray, the arm and the head. |

**clip_scan (`clip_scan_v009b.json`, 3cfc53c skin only):** bad ranges 1–31, 301–307, 589–643, 1207 and 1735. **The target of 0 is not met.**
I checked every bad frame by measuring how far the "inside" vertices are from the surface they are counted inside:

| Frames | Who | Nearest-surface distance of the flagged vertices | Verdict |
|---|---|---|---|
| 1–19 | Patient's hand "in" the surgeon | 42–50 cm | **False positive.** The hand rests on his knee, far from the surgeon. |
| 25–31 | Patient's left hand rising past the surgeon's hip | 2–10 cm (165 vertices under 5 cm at f31) | **Real**, for about 10 frames as his hand comes up in alarm. Not fixed. |
| 301–307 | Nurse's hand "in" the surgeon | 41–48 cm | **False positive.** |
| 589–643 | Patient's or nurse's hand "in" the surgeon | 19–43 cm | **False positive** (the surgeon walks past). |
| 1207 | Patient's hand "in" the surgeon | 14–15 cm | **False positive.** |
| 1735 | Patient's hand "in" own head | 10–17 cm | **False positive.** His hand is at his ear and collar. |

A probe 10–50 cm from a body cannot be inside it. `inside()` counts any point within the 0.5 m search radius that lies behind its nearest face's normal, and on the skin-only (open) surgeon mesh that includes points in front of him.
