# Chat B → A: Ch3–Ch5 hand-off (bake from code)

Branch `claude/radio-jingle-b`. Chat A bakes; no renders from B.

## Shot list
`b_shots.py` → `CHAPTERS["ch3"|"ch4"|"ch5"]`: `(set, move, label)` in film order. `seconds(ch)` gives `(set, move, label, seconds)`.
Seconds are estimates (184 wpm, +3 s title lead on each chapter's first shot) until the VO arrives. Then B commits the retimed values and the matching `DUR` in each scene module.
Title specs live in the scene modules' `MOVES[move]["title"]`, and `bake.py` adds them itself:
- 3-1A `b_woods wire`
- 4-1A `b_dna swab`
- 5-1A `b_court bench`

## Bake
```
PYTHONPATH=projects/radio-jingle/scenes:nvidia_doc/scenes \
  python nvidia_doc/scenes/bake.py <set> <move> --seconds S --out out/blend/chN
```
- `<set>` is the module name without `sc_`, e.g. `b_court`.
- Do **not** set `B_PREVIEW`: it caps subdivision for B's previews only.
- Each module uses `DUR[move]` for its motion pace. Pass `--seconds` equal to that value; B will set them equal once the VO is in.
- 5-11 `b_hall offhook`: the reels stop at `stop` seconds (currently 5.0), then a 3 s hold. Retimed to the word "answered".

## Imports
B's modules: `b_common`, `b_props`, `b_shots`, `sc_b_*`.

They also import A's modules from this branch (same folder):
- `rj`, `rjp`, `rj_vehicles`
- `sc_house` (for `b_hall`), `sc_box` (for `b_boxprint`), `sc_path` and `sc_woods` (for `b_woods`)

From `nvidia_doc/scenes` they use `kit`, `common`, `human`, `ph`, `look`, `grade`, `title_card` and `vehicles`.
B reuses A's sets read-only (no edits to A's modules).

## Generated assets
All are committed under `projects/radio-jingle/assets/generated/b_*.png`, and they regenerate on build anyway.
Title PNGs (`nvidia_doc/assets/generated/ChapterTitle_<slug>.png`) are generated per title and are not tracked.

## Poly Haven IDs used by B
ArmChair_01 CoffeeTable_01 Sofa_01 Television_01 WoodenTable_03 alarm_clock_01 asphalt_02 binder_notebook binoculars
book_encyclopedia_set_01 boombox brass_pot_01 brick_wall_02 brick_wall_08 cassette_player circuit_board classic_laptop
cobblestone_02 concrete_floor_02 concrete_floor_worn_001 concrete_pavers concrete_wall_006 concrete_wall_008 desk_lamp_arm_01
dining_chair_02 dirty_carpet farm_soil fir_tree_01 floor_tiles_06 forest_ground_04 granite_tile granite_tile_02 gravel_road
grey_plaster_02 grey_roof_tiles grey_tiles hanging_industrial_lamp herringbone_parquet laminate_floor_02 leafy_grass lifebuoy
magnifying_glass_01 mantel_clock_01 metal_office_desk metal_tool_chest metal_toolbox mounted_fluorescent_lights oak_veneer_01
office_notepads old_linoleum_flooring_01 old_wooden_floor_02 painted_wooden_cabinet potted_plant_01 retro_multimeter
rusted_spade_01 screwdrivers_02 security_light shrub_02 street_lamp_01 tree_small_02 vintage_flashlight vintage_oil_lamp
vintage_radio_transceiver vintage_stapler wall_clock wooden_bookshelf_worn wooden_table_02

(`tree_small_02` comes through `rj.low_instances("birch")`, and `fir_tree_01` through `"fir_a"`.)

## QC
B checks every shot at t 0 / 0.5 / 1 with `b_run.py` and `b_sheet.py`, plus `b_lum.py`: day shots must have a graded mean of at least 0.18. The latest table is `review/b_luminance.txt`.
