# IronRodHead_v002: checks on the exact package (IronRodHead_v002_60fps.blend)

| Check | Result |
|---|---|
| body_prop_cross (step 3; TampingIron, CrateKick0-2, CrateSup0-2) | **0 visible crossings** |
| clip_scan (step 6) | **0 bad ranges** |
| qa_check (step 6, beats.json) | EMPTY 204: diagram shots (no character by design: S06, S08, S13-S16) and frames where the head is visible but the check finds no head/hand sample (S11, S18-S22; watched, the face is in frame). CAMJUMP 18 = the 18 hard cuts. PROPMOVE 40 = blast dust/grit/iron flight (S03-S04, keyed effects) and the parked bandage at the S12 cut (off camera). BACKHEAD 1 = WorkerB at S09 frame 697 (3/4 back, squatting; Gage's face is the acting face) |
| limb_check (step 2) | ARMBODY: 2-3 points on Gage's upper arm at the shoulder in S04/S05/S09 (the known shoulder false positive, upperarm points 0-2 within 4 cm). Watched, no arm inside the torso. PROPHEAD 252: Gage's bandage pad while he is parked off camera (S12-S16) |

Preview: `review/preview.mp4` (every 5th frame, 270x480, Cycles 4 samples, VO). Watched in full, all 8 contact pages. The changed ranges
(696-795, 961-1100, 1096-1281, 1561-1647, 1841-1909) were re-rendered from this exact package and spliced in.
