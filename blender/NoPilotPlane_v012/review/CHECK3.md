# v012 check 3 (after round 2, the last fix round allowed)
`review/preview.mp4` at commit 3e2e983 is the check 3 preview of the exact package (270x480, every 5th frame, VO).

**Verdict: FAIL.** My watch of all 14 contact pages and a fresh reviewer on the 29 time-stamped pages agree. Both fix rounds are used, so I stopped here as the brief says. No .blend is pushed.

## What round 2 fixed (confirmed in motion)
- The camera is continuous. The PROF/BACK stations have no cut-like whips; max camera speed is about 6°/frame, at one spot only (f411–417, below).
- The haul is beside the FO's seat: no arm through the headrest.
- At f1250–1300 his right hand rests on the outer thigh, clear of the yoke horn.
- The throttle is a fist around the knob, and the lever arm no longer pokes through the hand.
- The look-back pans to the slumped FO.
- The red alarm light reads.
- The altimeter needle unwinds the right way.
- The logo reads for well over 1.5 s; colour is deep and saturated.

## Remaining faults (film frames) and the fix I propose for a director-approved round 3
| Frames | Fault | Proposed fix |
|---|---|---|
| 2221–2316 | Altimeter insert: about 1.5 s with no person, and near-black frames on the way in (2221–2226) and out (2301–2316) as the lens skims the panel under the yoke | Cut the person-free time to about 0.6 s. Enter and leave from above (z ≥ 1.25) so the lens never goes under the glareshield, or frame the dial past his shoulder from PROF. |
| 1081–1236 | Mic: it stands upright beside his fist with the fingers draped over its top, so it is not gripped. At about f1231–1236 it leaves his hand while it is lowered (a pop). | Hand-key a wrap grip with the mic body along the fist and the grill at his mouth; keep it Child Of the hand until it is back on the hook (1290–1325). |
| 411–421 | Stand-up: the camera swings past the teal passenger in about 3 preview cells, which reads as two cuts | Add a mid key so the 395→445 move stays on one side of him (≤3°/frame) |
| 1451–1566 | Loses grip: a forearm pointed at the lens (reads as a stump), big hands near the lens, top of his head as he drops into the seat | Wider and higher camera from FR, then FC, at lens 18; keep the hands below chest height while he stumbles back |
| minor 276–331 | The window beat: the near porthole reads as a grey disc and he is half out of frame | Target the window on the far side (wing and horizon) and frame him at 1/3 |
| minor 1716–1800 | The dive does not read through the side window (only dark-blue sky) | PROF looking about 25% toward the windscreen so the tilted ground shows |
| minor 2800–2900 | The throttle pull-back barely reads | Larger lever travel (-12 to +10°) |

## Automated checks
camcheck on the check 2 package: SET 0, BODY 0, FACE 0. On check 3 it was still running when I stopped.
body_prop_cross on the check 2 package flags only intended contacts:
- the seated body into the seat cushions
- the hands round the yoke grips and the throttle knob
- the mic in the hand
