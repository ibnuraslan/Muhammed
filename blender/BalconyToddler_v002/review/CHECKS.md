# BalconyToddler_v002: checks on the packed file (frames 1–1751)

| Check | Result | Reason for every remaining flag |
|---|---|---|
| `clip_scan` (step 6) | **0 bad ranges** | — |
| `body_prop_cross` (step 3, 15 props, all rigs) | 82 frames, **0 real** | All hits are MPFB body vertices hidden by the clothes' mask modifier, which the script switches off: soles inside the shoes (S16 f859 on the chair seat; S25–26 f1497–1751 on the slab) and grandma's shins inside her trousers while kneeling (S24 f1405–1496). With the render masks on, the same frames give 0 (checked at f1450, f2335 P1 timeline / f1555). |
| `qa_check` (step 6) | EMPTY 204, CAMJUMP 21, CLAW 81, FAN 81 | CAMJUMP = the 21 hard cuts (one per shot boundary, by design). EMPTY = the ray grid hits the cage rails / facade in front of small or caged figures (wides, close-ups through the bars); every page of the preview was watched and no frame is empty. CLAW/FAN = the man's right hand wrapped round the boy's shin (S18–23, closed on the leg by `grip_object`). |
| `limb_check` (step 2) | ARMBODY 520 (S17–23) | The man's left upper arm raised overhead: 2–6 points at the shoulder end inside the torso shell (the known upperarm false positive near the shoulder). Watched in S17/S18/S20: arms clear of the body. |
