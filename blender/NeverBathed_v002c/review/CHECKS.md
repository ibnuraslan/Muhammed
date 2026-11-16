# NeverBathed_v002c: checks

Run on `NeverBathed_v002c_60fps.blend`, frames 1–1728 (qa via `NeverBathed_v001/scripts/camproxy.py` so the marker cameras are used).

| Check | Result |
|---|---|
| body_prop_cross (tub, trough, crates, doors, props) | **0 visible crossing frames** (`body_prop_cross.json`) |
| clip_scan (hands/limbs into bodies) | **BAD_RANGES []** (`clip_scan.json`) |
| limb_check | ARMBODY 598 (same as v002b: MPFB helper points at relaxed arms, reviewed before), **ARMBACK 19** (new, explained below) |

## ARMBACK (new in v002c), f1461–1497
All 19 hits are V1's right arm in the re-staged 10a point: he faces the hermit and points sideways at the tub, so the
arm runs out to the side about 35° behind his shoulder line. Looked at in motion and in `limbcheck_ARMBACK_f1461-1506.jpg`:
it reads as a natural lateral "over there" point, with no contact with his body or the hermit. **Not a fault.**

## Watched
`preview.mp4` was watched start to finish (all pages in `pages/`). Only 1446–1728 was re-rendered (10a, 10b, 11a, 11b) and
spliced into the v002b preview; 1–1445 is unchanged from v002b.
- 10a: knees-up over-the-shoulder two-shot; V1 clearly points at the tub, the hermit steps back and shakes his head.
- 11b: V2 kneels in a loose dark-olive tunic with folds over charcoal trousers. No bare back or shoulders.
