# B23 v002 checks (on the exact packed file `HandlessWarrior_v002_60fps.blend`, frames 1–1615)

The pipeline checks read `sc.camera` once and evaluate MPFB bodies with Mask modifiers disabled. This film cuts
between one camera per shot and masks the warrior's hands, so the checks were run with `scripts/check_per_shot.py`
(each shot with its own camera; every Mask modifier's effect applied first) and `scripts/bpc_masked.py`.

| Check | Result |
|---|---|
| body_prop_cross (step 3, all props: stump, swords, spears, knives, straps, hot plate, anvil, table, crate) | **0 visible crossings** (only knife/strap self-hits, excluded) |
| clip_scan (step 6, per shot) | **0** in every shot |
| limb_check (step 2, per shot) | ARMBODY hits are upper-arm points next to the shoulder (2 pts = known false positive; 3–6 pts in S01 kneel, S07 fist, S13/S14/S17 wind-ups). Worst frames 1, 495, 1099, 1336 rendered at 540×960/full res and checked by eye: no arm through a torso. ARMBACK fixed (S03 point now in front of the soldier). |
| qa_check (step 6, per shot, beats.json) | EMPTY only in the prop inserts S08 (forge), S10 (knives on the table) and S15 (flag), by design. ATTACH = morion helmets 10–14 cm from skin median: the wide brim, the helmet is bone-parented to the head (no drift). PROPMOVE = the stylised impact sparks (no hand by design). FAN in S03 = the soldier's deliberate point pose. BACKHEAD at frame 245 = last frame of S03 as the warrior walks off (his face shows earlier in the shot). CAMJUMP = the intended hard cuts. |
| Render memory | heaviest frames (S16/S17 with the army) peak at 5.9 GB at full 1080×1920 (crowd copies render without subdivision). |
| Preview | `preview.mp4`, every 5th frame, 270×480, Cycles 4 + OIDN, from this file (changed ranges re-rendered and spliced), watched page by page with the VO. |
