# HandlessWarrior_v001 (B23): Phase-1 checkpoint (no VO yet)

- `HandlessWarrior_v001_P1_60fps.blend`: P1 build (1080×1920, 60 fps, Cycles, all textures packed, 76 MB). Frames 1–2415
  are the Phase-1 clips laid end to end (reference pacing +30%); Phase 2 retimes by editing `scripts/timing.py` only.
- `PLAN.md`: shots, staging, logo placement, risky-shot staging.
- `review/P1_stills_3perShot_540x960.jpg`: first / middle / last frame of every shot, 540×960, Cycles 8 samples, rendered from the packed file.
- `review/P1_body_prop_cross.txt`: contact check on every held/touched prop.
- `review/model_credits.json`: CC-BY models (Sketchfab via Objaverse); Poly Haven CC0 assets listed in PLAN/CREDITS at v002.

Build (Blender 5.2.2, headless):
```
blender -b --factory-startup --python scripts/01_chars.py -- chars.blend
blender -b chars.blend --python scripts/02_sets.py -- sets.blend
blender -b sets.blend  --python scripts/03_anim.py -- anim.blend
blender -b anim.blend  --python scripts/04_pack.py -- HandlessWarrior_v001_P1_60fps.blend
blender -b HandlessWarrior_v001_P1_60fps.blend --python scripts/shot_stills.py -- outdir first,mid,last 540 8
```
Assets are fetched with `pipeline/find_models.py get` (ids in `review/model_credits.json`) and `pipeline/fetch_polyhaven.py`
(leafy_grass thatch_roof_angled dirt_floor clay_plaster wood_planks grass_medium_01 shrub_02 shrub_04 tree_stump_01
wicker_basket_01 wooden_bucket_01 stone_fire_pit island_tree_02); set `B23_PH` / `B23_GLB` to their folders.
