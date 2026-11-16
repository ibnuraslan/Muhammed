# B23 v002b checks (on the exact packed file `HandlessWarrior_v002b_60fps.blend`, frames 1–1615)

Run as for v002 with `scripts/check_per_shot.py` (each shot with its own camera, Mask effects applied) and
`scripts/bpc_masked.py`.

| Check | Result |
|---|---|
| clip_scan (step 6, every shot) | **0** in all 16 shots. (A first pass caught the woman's raised arm passing through her torso in S05; fixed with a mid-raise key and the hand placed from her head bone.) |
| body_prop_cross S14 (step 1 around the cut and thrust, step 2 over the whole shot), split per rig | **Warrior** vs sword, brass cuirass, helmet, knives, straps: 0 (his forearm inside his own bandage = how the bandage is built, as in v002). **Officer** vs knives, sword, helmet: 0 after three fixes (the thrust first entered the cuirass at f1081–1087 and was shortened to stop short; the wind-up sword clipped his helmet at f1049; the hand-on-chest sank into the plate). His torso and arms against his own cuirass are on every frame, identical in v002 (the plate is a solidified copy of his jacket: the garment layering, nothing visible pokes through). Upper arm vs plate edge at the wind-up (f1048–1052) checked in a close render: no visible poke. |
| body_prop_cross S05 (step 2: crate, anvil, table, knives) | **0** (first pass: the woman's leg was in the logo crate; she was moved back to her v002 spot). |
| limb_check (step 2, every shot) | Only ARMBODY: the known 2–3 pt shoulder false positives, plus VillagerW 6 pts (S05, hand at her mouth), Warrior 6 pts (S14, the extended thrust) and Warrior 4 pts (S17, as in v002). The S05 and S14 frames were rendered as close-ups and checked by eye: no arm through a torso. |
| Pack | 87.9 MB, all images and the VO packed. |
| Preview | `preview.mp4`, every 5th frame, 270×480, Cycles 4 + OIDN, with the VO. Re-rendered from this file: S01–S06 (1–480), S13–S14 (891–1146), S16–S17 (1211–1615), spliced into the v002 frames (S07–S12 and S15 have no soldiers and are unchanged). Watched page by page. |
