# SurgeonBrandsLivers_v001 — working folder

28.5 s vertical true-story short (1080×1920, 60 fps, frames 1–1710), built from our own script in the grounded, textured style. One continuous camera, no cuts.

## Files
- `PLAN.md` — checkpoint A: beat table, world layout, assets, tricky shots.
- `beats.json` — beat start frames + first words, for `pipeline/retime_to_vo.py` once the voiceover arrives.
- `CREDITS.md` — CC-BY block for the video description + CC0 list.
- `review/` — B: 1 s blocking sheet, camera path; C: 0.2 s polish sheets, audit report, change list.
- `scripts/` — the full build, in order:
  1. `01_build_people.py` — nine MPFB2 humans (MakeHuman CC0), generic faces.
  2. `02_build_scene.py` — sets (OR, studio dome under the OR, home, hearing room, corridor), props, lights, render settings.
  3. `03_animate.py` — every actor, prop, brand letters, sparks, smoke, x-ray overlays, doors, calendar (uses `pipeline/anim_lib.py`).
  4. `04_camera.py` — the one camera `CAM_Film` on a spline through ~65 framings.
  5. `05_package_prep.py` — caps texture sizes, farm settings; then `pipeline/package_for_farm.py`.
  - `build.sh` runs 01–04 (`W=/opt/work/sbl A=/opt/assets/sbl ./build.sh`).
  - `audit.py` — contact audit (hover / sink / slide, grasp distance, hands through desks, camera inside walls or bodies).
  - `frames.py`, `campath.py`, `plotpath.py` — review helpers.

## Assets needed to rebuild
`A=/opt/assets/sbl`:
- `objv/` via `pipeline/find_models.py get … liver=cf66ae46c0e148139bbb360b70343b5a bed=60651eac7e96454c8cf5c43a91412336 gavel=44581bee0a5749989dc474fe35b9dc1e sofa=03550a3529c24611a12aa158747374e0`
- `ph/` via `pipeline/fetch_polyhaven.py $A/ph 2k hospital_room_2` and `… 1k long_white_tiles large_grey_tiles white_plaster_02 laminate_floor_02 beige_wall_001 dark_paneled_wood fabric_pattern_07 white_oak_veneer Television_01 coffee_table_round_01 potted_plant_04 ArmChair_01`

The farm package (everything packed) is in `../SurgeonBrandsLivers_v002/`.
