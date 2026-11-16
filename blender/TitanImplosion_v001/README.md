# TitanImplosion_v001 (B16): Phase 1, no VO yet

Not a delivery. Provisional timeline (clips 1.3× expected beat length, 1–2691 @ 60 fps) for director review.

- `PLAN.md`: beats, shots, staging, logo placement.
- `TitanImplosion_v001_P1.blend`: the P1 build (textures packed). Rebuild: `scripts/02_build.py` (see its docstring) with `shots_p1.json`.
- `layout.json`: shot frame ranges of this build.
- `review/P1_sheet_3frames_540.jpg`: first / middle / last frame of every shot, 540×960, Cycles 8 samples.
- `review/bpc_*`: body_prop_cross results (sofa, coffee table, logo box) on the man's shots.

Phase 2: `shots.json` gets the VO frames, `02_build.py` is re-run (all actions keyed from shot starts at 1×, nothing stretched).

Scripts: `01_char.py` (extract the man from BellyFat_v010), `02_build.py` (everything), `shot_frames.py` + `sheet.py`
(3-frame sheet), `body_prop_cross_masked.py` (pipeline check that skips body skin hidden under clothes by MPFB's MASK).
