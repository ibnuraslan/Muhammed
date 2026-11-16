# B31 NeverBathed: body_prop_cross at P1

`pipeline/body_prop_cross.py -- out.json 3 <props>` on the provisional build (2750 frames, every 3rd frame).

Props checked (everything held, touched, sat on, walked through or knelt beside):
V_Trough, Pipe_7b, Twig_8a, V_Tub, D_SeatRock, V_Hermit (house + interior), V_Hermit_door, V_Crate, V_Crate2, V_Crate3,
D_Spit, D_Meat, D_Shovel, R_Hare, Bucket.

| Round | Result |
|---|---|
| first build | 259 visible frames: hand in the trough wall (1a), feet below the interior floor and a walk through the door leaf (4a), lower back in the seat rock (6b), thumb in the pipe (7b), legs/arms in the tub walls (10b) |
| fixes | trough re-staged (he stands at the trough end, free hand on his thigh); interior floor at 0; door leaf opens inward; flat-topped seat rock + pelvis lift on leans; tub 1.85 m, the model's water surface split off as `V_TubWaterTop` (sitting IN water is not a crossing); hermit seated forward, villager kneels behind |
| final (`P1_body_prop_cross_all_props.json` + `..._pipe_twig_final.json`) | **0 visible crossings on every prop except one:** `finger3-3.R` (middle fingertip) vs `Pipe_7b` on 29 sampled frames of shot 7b (1582–1633, 1699–1729), i.e. only while the pipe is at the lips. The lowered phase is clean. |

Open item: the 7b middle fingertip grazes the pipe stem (a few mm) while the thumb and index pinch the shank. On the
540×960 frames it reads as a normal pinch, but it is still a crossing. Planned fix in Phase 2 (one more try, then the
simplest re-stage): curl the middle finger fully under the bowl or extend it along the stem; if still flagged, 7b holds
the pipe only by the bowl in the cupped hand at chest height and lifts it to the lips with the stem never near the fingers.
