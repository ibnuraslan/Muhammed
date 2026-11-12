# ShoeBomber v006b: camera only (the director approved v006's acting and hands)
- The client's spec is one continuous camera. v006's hard cuts (213, 377, 389, 403, 437, 479, 521, 546, 575, 649, 775) are now real moves.
- The `cam_search.py` framings stay as key poses. Moves between them run 13–40 frames with Catmull ease:
  - 199→232: up the aisle at z 1.7 to the attendant.
  - 455→481 and 508→534: over the seat backs at z 1.68.
  - 566→594: out toward the aisle, then up (it was clipping an overhead bin lip).
  - 625→655: down to the steward's face.
- Each beat framing is reached by its beat frame (199, 373, 481, 655, 769). No beat frame moved.
- Checks:
  - `scripts/cam_speed_check.py`, the director's acceptance check: no frame-to-frame move over 0.25 m in 1–1060.
  - `scripts/cam_inside_check.py` (wipe card hidden): the camera is inside geometry only at the cloud wipe, 1253.
- Hands and acting are the same as v006 (60a59c2). The contact snap and push-out passes were re-run because the snap depends on what the camera sees.

## Results (v006b)
- Camera speed check: `SPEED_BAD []`, so no move over 0.25 m per frame in 1–1060 (`review/cam_speed_v006b.txt`).
- clip_scan: no bad ranges (`review/clip_scan_v006b.json`).
- qa_check (`review/qa_v006b.json`): HOVER 0, CLAW 0, FACEPRESS 0, BACKHEAD 0.
  - Intended, as in v006: EMPTY in the studio and sky cutaways (1063–1392) and at 1057 (the push into the sole); FILL/INSIDE at the cloud wipes (1069, 1243, 1255).
  - New, from the moves that replaced the cuts:
    - EMPTY at 205–223 (0–6 %), while the camera travels up the aisle from his seat to the attendant.
    - EMPTY at 463 (11 %), rising over the seat backs.
    - FILL "top of head" at 517, 583 and 775 (29–32 %), as the camera passes over heads on its way across the row.
