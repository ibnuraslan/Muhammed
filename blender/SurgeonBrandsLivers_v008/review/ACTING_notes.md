# SurgeonBrandsLivers v008: director notes on v007 (5700c40) and qa_check fixes

Beat frames are unchanged: 1 / 301 / 565 / 637 / 781 / 1045 / 1231 / 1501, end 1710. No VO was added.
The v007 fixes are kept (one-hand mask-off, home pose, rest arms, lectern hands).

## The director's 7 notes
| # | Note | v008 fix |
|---|---|---|
| 1 | Empty frames at 9.5, 10.0, 10.5, 20.5 and 21.5 s | 9.5–10.5 s: whip to the nurse, then over her shoulder onto the calendar, then one push through it (~6 frames). 20.5 s: the camera holds on Surgeon2 at the beat, then whips. 21.5 s: the camera swings round in front of the surgeon, so the SB wall reads behind him. Also: 13.0 s (beat 5) the bed bursts through the doors with the patient on it; 26–28 s the judge stays in frame over the licence; 24.2 s the pan crosses the panel, not the side wall. |
| 2 | Opening 0–1.5 s: his back and the top of his cap | The camera is low, across the table and in front. His eyes and mask read with the pen and the skin. His working elbows now hang down and out (IK poles); before, the one-sided elbow limit flipped his right forearm up across his face. |
| 3 | Gavel: splayed fingers, held sideways | The gavel was re-framed (its stick was tilted inside its own mesh). The block moved forward. It is held in a fist (`power_fist`, thumb over the fingers) with the stick across the palm, head forward. Raised at 1525, strikes down flat on the block at 1538, then rests there. |
| 4 | Stamp: one fingertip on the knob | Fist round the handle (`wrap_grip`, thumb wrapped), hand upright beside it, pressing down. The stamp starts within easy reach. |
| 5 | Nurse: claw by the rail | The head-board grab point was 7 cm off the bed in the air. The hands now grip the top edge of the head-board (`wrap_grip`). The nurse walks close enough to reach. |
| 6 | Mask hand comes up as a claw | It rises `relaxed`, then `pinch` on the lower edge, then pulls down. The mask still only moves while the hand holds it. |
| 7 | Close-up 9.0 nearly black | The glove snap was inside the drape. Surgeon2's hands are now in front of his chest and the close-up is re-aimed. The nurse close-up is also re-aimed onto her hands. |

## Hand system
- Every hand uses a preset from `pipeline/hand_poses.py` (`HAND_POSE_RULES` in `03_animate.py`). There are no hand-set finger angles.
- `add_hand_limits` is applied to all 9 rigs (`07_hands.py`).
- Contact pass `08_contacts.py`:
  - It applies qa_check's own HOVER rule.
  - A hovering visible hand is moved so a fingertip rests on the surface.
  - On the pen and the needle driver, the thumb and index tips are closed onto the tool.
- `07_hands.py` capsule audit: final 0. `clip_scan.py`: see the submission message.

## qa_check.py (`qa_v008.json`): remaining flags, all intended
- **HOVER 4** (1309, 1411–1423): the patient's left hand is under the drape on the OR table while the camera is in the hearing room. It is not visible.
- **INSIDE 2** (277, 1177): the single frame where the camera crosses the studio membrane between the OR window and the studio. These are the approved texture wipes of 6 frames or fewer.
- **EMPTY / FILL (one sample per wipe)**: 133–139 and 1057 (dive into the window), 277–289 and 1177–1189 (rise out), 637 (through the calendar), 775 (through the home wall), 1237 (through the west wall). These are texture wipes of 6 frames or fewer.
- **EMPTY / FILL (studio macro)**:
  - 163–247: the gloved hand burns S, then B, into the liver.
  - 1087–1159: the gloved hands lift the liver with the SB burn.
  - The liver and the gloved hands are the subject; the characters' bodies are not in this set.
- **EMPTY (wide)**: 835–889 is the establishing wide of the bed rolling in through the doors (patient on the bed, nurse behind).
- **EMPTY (prop in hand)**: 1507–1519 is the gavel in the judge's fist; 1567–1627 is the stamp in her fist on the licence. Both are hands-on-prop close-ups.
- CLAW, FACEPRESS and BACKHEAD: 0.

## Checks on the packed file
- `clip_scan.py` (director, step 6): **0 bad ranges** (`clip_scan_v008.json`).
- `qa_check.py` (director c6240b2, step 6, beats.json): `qa_v008.json`. CLAW 0, FACEPRESS 0, BACKHEAD 0, HOVER 4 (hidden hand, listed above), INSIDE 2 plus EMPTY/FILL (intended wipes, studio macro, wide shot and prop-in-hand close-ups, listed above).
- Known weak spot: the stamp close-up at 1596. The fist sits low on the handle, near the base.
