# YardTrench_v002: checks on the packed file (`YardTrench_v002_60fps.blend`, frames 1–1825)

| Check | Result | Notes |
|---|---|---|
| `clip_scan.py` (step 6) | **0 bad ranges** | The first package had fingertips 2+ cm inside the thigh fronts in every standing pose. The hands now hang beside the thighs (rest offsets re-tuned, verified with a per-region diagnostic at 0 hits). |
| `limb_check.py` (step 2) | ARMBODY 468, all "Man arm.L/R inside own torso (2 pts)" | Exactly 2 points on both arms in every Man frame, whatever the pose (walking, standing, top-down, peeking). These are the upperarm01 points at the shoulder joint, the known false positive in LESSONS §4. No ARMBACK, no PROPHEAD. |
| `qa_check.py` (step 6, beats.json) | EMPTY 259, CAMJUMP 21, PROPMOVE 88, ATTACH 9, BACKHEAD 2 | **EMPTY:** the shots that show the strip, water or groove (S7, S8, S11–S16), or a tiny figure in a wide (S3, S19). These are the "thing the VO names". **CAMJUMP:** the 21 intended hard cuts. **PROPMOVE:** keyed clod squash under the feet (S6), the rain host box, and the helmet riding the head bone; the one 322 cm jump is the S22→S21 cut. **ATTACH:** median helmet-to-skin distance of 7–11 cm, because hair sits between them; the helmet visibly sits on the head (checked at 1080 px, f1660 and f1801). **BACKHEAD:** S4 (241–313), the boy walking away to the house from behind, as in the reference's feet beat. |
| `body_prop_cross.py` (step 3; Helmet, FireStep, section turf/top, 12 sandbags) | sole contact only, plus 6 edges at f1801 | Shoe-sole edges touch the section turf they walk on (S6). Six head-label edges meet the helmet rim at f1801; at 1080 px there is no visible poke-through. No hand, leg or body passes through anything. |

The preview was watched page by page (every 5th frame, 365 frames) before this push.

## v002b (director fix round 1): re-rendered ranges f321–481, f1361–1421, f1731–1825, spliced into the v002 preview
- **S5/S6 (321–481):** low-angle full body with the head in frame, the cross-section kept. The soil clods are now grey faceted stones (own RNG, so nothing else in the set moved).
- **S17 (1361–1421):** walk with bent elbows (hands 8 cm higher and forward) and a fuller swing.
- **S21 (1731–1825):** relaxed bent arms, a weight shift, a look up at the rim, and one small action: an open-hands shrug. A hand on the trench wall was tried twice and dropped (fingers 3–11 cm into the soil; LESSONS §2.15). An area fill light (70 W, behind the camera, S21 only, invisible to the camera) lifts the dark lower legs.
- **Checks on the changed ranges (v002b package):** clip_scan 0 bad ranges in all three. limb_check only shows shoulder points (upperarm01 points 0–2, the known false positive). body_prop_cross shows sole contact on the turf (S6) and 2 helmet-rim edges at f1824. A finger-into-thigh diagnostic reads 0 hits.
- **Splice check:** control frames re-rendered from the v002b package. f1696 RMSE 0 against v002. f596 RMSE 0.0047, which is sampling noise from the extra 0 W light in the light tree, with no visible change.
