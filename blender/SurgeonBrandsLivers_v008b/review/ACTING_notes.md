# SurgeonBrandsLivers v008b: held tools (client reject, Nov 13)

v008b is v008 (32d7716, approved) plus a tool-grip fix only. Beat frames are unchanged (1/301/565/637/781/1045/1231/1501, end 1710). No VO.

## Client notes
| Note | Fix |
|---|---|
| The pen-shaped cautery tool is not held; it balances on open fingertips | `10_tool_grip.py`: the hand drives the tool. The fingers are `hand_poses` pinch (thumb and index close on the barrel, middle under it). The ring and little fingers curl with the middle (`11_pen_fan.py`, no fan). The pen's seat in the hand is measured from the evaluated pose (barrel through the thumb–index pinch, running back over the web). The pen is baked **every frame from the evaluated wrist**, so there's no gap and it never moves on its own. |
| The back end runs into his face, through the mask | Each frame, the hand is rotated only as far as needed to swing the barrel back over the hand toward his right-shoulder side. The tip stays exactly on its path (0.0 cm off: the incision and the letters). The barrel stays at least **23.2 cm from the head centre**, so more than 10 cm clear of his face and mask. |
| Limits before the solve | `add_hand_limits` is applied in `07_hands.py`, which runs before `10_tool_grip.py`. The grip is solved with the limits on. |
| Putting it down | The hand carries the pen to the instrument tray (300–312) and lets go. It lies still there afterwards. |

Held tools checked the same way (strip `v008b_held_tools_540x960.jpg`, every 30 frames per held range):
- OR pen, Surgeon1.R, 1–312
- studio pen, GloveHands.R, 1–300 (tip 0.0 cm off its path, barrel ≥ 38 cm from the head)
- needle driver, Surgeon1.R, 318–458 (pinch on the rings, from v008)
- mug, 601–661
- glove cuff, 990–1016
- gavel, 1480–1710
- stamp, 1556–1650

## Checks (packed file)
- `clip_scan.py`: 0 bad ranges.
- `qa_check.py`, newest version (8c76d71):
  - CLAW 0, FAN 0, FACEPRESS 0, BACKHEAD 0.
  - HOVER 4: the patient's hand under the drape while the camera is in the hearing room; not visible.
  - The remaining flags are listed below.
- CAMJUMP 12: the texture wipes that were already approved: the dive into the window and the studio (138, 278, 1060, 1183, the 6.4 m studio drop), the calendar (639), the home wall (773), the whips (570, 1232), and the dive moves (283, 286, 1057, 1058).
- PROPMOVE 11: the burn sparks and smoke (effects, not props) and the mug falling after she drops it (673). One more, 577, is from v008 and wasn't checked in this pass.
- ATTACH 40: the newest version checks whether masks sit on the skin. All five surgical masks sit about 2 cm out, as fitted since v002. This pass didn't change the masks.
- EMPTY / FILL / INSIDE: unchanged from v008 (the intended wipes and the studio macro, listed in the v008 notes).
