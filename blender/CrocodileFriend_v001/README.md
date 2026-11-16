# CrocodileFriend_v001 — B28 Phase 1 (built before the VO)

Work folder, not a farm package. `PLAN.md` = beats/shots/staging. `shots.json` = shot ranges (P1 timeline, 3900 frames).
Review: `review/P1_sheet_3frames.jpg` (first/middle/last frame of every shot, 540×960, Cycles 8 samples),
`review/body_prop_cross.json`.

Rebuild (Blender 5.2.2, headless):
```
B=/opt/blender/blender-5.2.2-linux-x64/blender
$B -b --factory-startup -P scripts/01_croc_rig.py -- assets/croc_hp.glb work/croc.blend   # straighten + rig the croc
$B -b --factory-startup -P scripts/02_people.py -- work/people.blend                      # reuse MPFB cast (Beluga, CaveRescue)
$B -b work/people.blend -P scripts/03_sets.py -- work/sets.blend                          # HOME / RIVER / HALL sets
$B -b work/sets.blend -P scripts/04_anim.py -- work/film.blend                            # 21 shot clips + cameras/markers
$B -b work/film.blend -P scripts/portrait.py -- assets/portrait.png                       # funeral portrait from the film
$B -b work/film.blend --python ../pipeline/anim_look.py -- work/look_base.blend --no-sky
$B -b work/look_base.blend -P scripts/05_look.py -- work/look.blend                       # portrait, crate logo, catchlights
$B -b work/look.blend -P scripts/sheet3.py -- review/p1 540
```
Phase 2 (VO): trim each shot range to its beat frames (never stretch), pack, checks, full preview, watch, push `CrocodileFriend_v002/`.
