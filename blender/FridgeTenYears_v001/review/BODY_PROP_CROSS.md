# body_prop_cross: P1 (step 3, packed P1 file `FridgeTenYears_v001_phase1.blend`)

Props checked: CoolerHero (+_Shell, _Glass), CoolerN1/N2 (+_Shell), WallBack, Skeleton, CondUnit, TopBox0-2.
Each range runs with the rigs visible in that range (`scripts/bpc_range.py`).

| Range | Rigs | Visible crossings |
|---|---|---|
| S01–S06 (1–741) | Worker | 60 frames flagged, all explained below |
| S09–S12 (976–1521) | Manager, Detective | **0** |
| S14–S20 (1678–2496) | ConA, ConB (incl. the S16/S17 palm push on the side panel) | **0** |

## The worker's flags
- **Frames 1–172: `root|CoolerN2_Shell` / `root|CoolerHero_Shell`, 4 edges, constant.** These are false positives. The "root" label is the 16 vertices of MPFB's masked joint-helper cube at the hip (z ≈ 3.07 while he stands on the 2.15 m top). They are hidden by the body's MASK modifier and never render (LESSONS §3: helper and joint geometry). The script turns MASK off, so the cube's edges count. The shoes are 3 cm above the top in every frame.
- **Frames 277 and 403: `upperleg02.L|CoolerHero`, 1 edge.** A thigh grazes the flush back panel by a single edge while he is wedged. It is not visible on the 3-frame sheet (S03/S04, from above). I will clear it in Phase 2 by moving him 1 cm further toward the wall.

## History in this round (fixed before this push)
- Push palms: the fingers curled into the side panel (91 frames). Fixed with the `flat_palm` pose, the palm 8.5 cm off the panel, and fingers up. Now 0.
- Wedged pose: toes and knees went into the cooler-back coil tubes. Fixed with the feet splayed along the gap, the root moved toward the wall, less crouch, and the coil made flush. Now 0, apart from the 1 edge above.
