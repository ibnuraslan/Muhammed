# NatashaRyan_v001 (B15), Phase 1 work folder

**Phase 1 only.** There is no VO yet, so this folder has no delivery package. The plan is in `PLAN.md` and the review material is in `review/`.

Rebuild from the repo blends (needs the MPFB extension, so do **not** use `--factory-startup`):
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
python3 -I blender/pipeline/find_models.py get <cache> blender/NatashaRyan_v001/assets <name>=<uid> ...   # uids in review/asset_credits.json
$B -b --python scripts/01_chars.py -- work/chars.blend
$B -b work/chars.blend --python scripts/02_dress.py -- work/dressed.blend
$B -b work/dressed.blend --python scripts/03_build.py -- work/film.blend
$B -b work/film.blend --python scripts/04_portrait.py -- portrait.png     # memorial photo (then rebuild 03 once)
$B -b work/film.blend --python scripts/check_frames.py -- OUT - 540 <frames>
$B -b work/film.blend --python scripts/bpc_shots.py -- review/body_prop_cross_P1.json 6 shots_provisional.json
```
`bpc_shots.py` runs the same edge-through-surface ray test as `pipeline/body_prop_cross.py`, with two changes:
- It runs per shot, against that set's props only.
- It counts only the characters rendered at that frame.

The stock script reported false crossings from hidden rigs parked at the origin, and it would take about 3 hours on this 8-set file.
