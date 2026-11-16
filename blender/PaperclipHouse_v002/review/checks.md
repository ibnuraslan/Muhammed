# PaperclipHouse_v002: checks on the packed file

All four checks were run on `PaperclipHouse_v002_60fps.blend` exactly as committed (frames 1–2000).

| Check | Result |
|---|---|
| `body_prop_cross` (step 3, per shot with that shot's rigs; props: every P_* item and the kitchen counter) | **0 visible crossing frames in all 19 shots** |
| `clip_scan` (step 6) | **0 bad ranges** |
| `qa_check` (step 6, beats.json) | BACKHEAD 1, INSIDE 11, CAMJUMP 18, PROPMOVE 4: all explained below |
| `limb_check` (step 2) | ARMBODY hits are all shoulder-region points: explained below |

## qa_check flags (none is a fault)
- **CAMJUMP 18:** the 18 hard cuts between the 19 shots, one per cut frame.
- **PROPMOVE 4** (frames 127, 253, 415, 1105): a prop is repositioned across a hard cut, for the next shot's layout. Each is the first sample after a cut; no prop moves inside a shot.
- **INSIDE 11** (frames 1561–1621, shot S24): the camera is inside the sky-blue gradient dome of the explainer stage, by design. Nothing is in front of the lens.
- **BACKHEAD 1** (frame 121, last frame of S01): PenLady, the trade partner, is seen in ¾ back view over the counter. The hero faces the camera in the whole shot.

## limb_check
- **2 pts:** the known false positive (upperarm01 points 0–2 within 4 cm of the shoulder).
- **3–6 pts:** these come only from raised arms and from the handshake arm's upper arm near the shoulder:
  - S08: the party, fists up
  - S28: the house reveal, arms up
  - S03, S05, S21, S27: the handshake arm
  - S23: PenLady pointing

  In every one of those frames the moving preview shows the upper arm outside the chest. These are the shoulder/deltoid vertices the checker classes as torso.
