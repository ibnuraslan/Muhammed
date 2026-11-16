# IronRodHead_v001: Phase 1 (pre-VO build)

Status: **Phase 1 checkpoint, not a delivery.** Timing is the reference pacing +~30% (3366 frames). In Phase 2, edit
`scripts/timing.py` to the VO beat frames and rebuild (no time-stretch).

- `PLAN.md`: shots, staging, logo placement, risky-shot staging.
- `IronRodHead_v001_P1_60fps.blend`: the Phase-1 scene (textures packed, compressed). 1080×1920, 60 fps, Cycles, frames 1–3366, one camera per shot bound by markers.
- `review/P1_stills_3perShot_540x960.jpg`: first / middle / last frame of every shot at 540×960, Cycles 8 samples.
- `review/P1_body_prop_cross.json` + `_summary.txt`: body_prop_cross (every 3rd frame) on the iron bar and all crates.
- `review/model_credits.json`: Sketchfab/Objaverse CC-BY credits.

## Rebuild
Models: `pipeline/find_models.py get <cache> $B12_GLB` with the UIDs in `review/model_credits.json`; textures:
`pipeline/fetch_polyhaven.py $B12_PH 1k rocky_trail coast_sand_rocks_02 brown_planks_05`.
```
blender -b --factory-startup --python scripts/01_chars.py -- chars.blend   # cast from WW1Assassination_v007
blender -b chars.blend --python scripts/02_sets.py -- sets.blend
blender -b sets.blend  --python scripts/03_anim.py -- anim.blend
blender -b anim.blend  --python scripts/shot_stills.py -- out_dir first,mid,last 540 8
```
`_helpers.py` (Char wrapper, camera helpers) and `_b04_sets_helpers.txt` (box/decal/logo helpers) are taken from B04's scripts.
