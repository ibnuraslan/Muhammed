# NeverBathed_v002: checks on the packed file

All four ran on `NeverBathed_v002_60fps.blend` as pushed. This film cuts between per-shot cameras bound by timeline
markers; `qa_check`, `clip_scan` and `limb_check` read `scene.camera` once at start, so they were run through
`../NeverBathed_v001/scripts/camproxy.py` (a proxy camera that copies the active shot camera on every frame).

| Check | Result |
|---|---|
| `body_prop_cross` (step 3; trough, pipe, both twigs, tub, seat rock, house, door, crates, spit, meat, shovel, hare, bucket) | **0 visible crossings** |
| `clip_scan` (step 6, 2 cm) | **0 bad ranges** |
| `limb_check` (step 2) | ARMBODY only. 626 of 630 hits are 2–3 points on the upper arm next to the shoulder (known false positive, LESSONS §4). The 4 remaining are 4–5 points at 425 and 443: shot 3a, his right fist thumping his own chest (intended contact). |
| `qa_check` (step 6) | see below |

`qa_check` flags and reasons:
- CAMJUMP 18: the hard cuts between shots (batch-2 rule: hard cuts, one camera per shot).
- EMPTY 847–931: shot 7a, the insert of the dung cakes and the pipe the VO names ("smoked animal poop"); no person by design.
  EMPTY 529: first frames of 4a, the hermit is still inside his doorway (11 % of frame) as he steps out.
- PROPMOVE: fire flames (keyed noise flicker), flies and smoke puffs; effects, not held props.
- CLAW / FAN: 1a and 10a are the `point` preset (index out, others curled); 7b is the pipe pinch (thumb + index on the
  stem, the other fingers folded into the palm).

Watched: the full preview (`preview.mp4`, every page in `pages/`), plus 540×960 zooms of 2c, 5b, 8a, 8b, 10b, 11b.
After watching, 7a (camera push), 1a, 7b–8a and 11b were fixed and only those ranges re-rendered from the final package and spliced
(1–84, 846–931, 931–1216, 1621–1728); the rest of the build is unchanged.
