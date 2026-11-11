# StanleyCup_v002: farm package (built to the brief's target beat times; no voiceover yet)

The full 25.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `StanleyCup_v002_60fps.blend`: the self-contained scene (58 MB, normal Git file; LFS upload was refused tonight). Every texture is packed; it opens in factory-startup Blender 5.2.2 with no add-ons.
- `beats.json`: beat start frames + first words, for `pipeline/retime_to_vo.py` when the VO arrives.
- `SETTINGS.md`: render settings, measured cost, suggested test frames. `CREDITS.md`: all assets are CC0 (no CC-BY block needed).
- `audit.txt`: contact audit on the final file.
- `package_check_f1500_lowres.png`, `package_check_f985_lowres.png`: 20 %, 4-sample frames rendered from the packed file in factory Blender. They show the package works; they are not quality references.

Source: `../StanleyCup_v001/scripts`. Build order (assets fetched with `pipeline/fetch_polyhaven.py`, see CREDITS):
`01_build_humans.py` → `02_build_scene.py` → `03_animate.py` (runs 03b_fx, 03a_humans, 03d_acting, 03c_camera) → `04_slim_textures.py -- <tex_dir> <out.blend> 2048 1024` → `python3 04b_png8.py <tex_dir>` → `pipeline/package_for_farm.py`.
Review sheets and the audit are in `../StanleyCup_v001/review/`.

## Story / camera
One camera (`CAM_Film`) on one monotone-cubic spline, ~35 framings (one per ~0.7–1 s), no cuts:
dusk street bullet-chase → through the siding hole, the stud bay and the drywall hole → room reveal → her freeze / his reach in extreme slow motion →
rack focus and macro orbit on the tumbler → impact: dent, sparks, droplets, x-ray dive into the cup (ripples, ice) → flattened bullet pops back and drops off the table → real time: floor bounces → crane up to her gripping the dented tumbler, him reaching for her arm.

## Voiceover retime
No VO yet. When it arrives: transcribe (`pipeline/transcribe.py`), then `retime_to_vo.py` with anchors from `beats.json` (old frame = the beat frame, new = the word time).
Beat 1 starts at frame 1 already.

## Known open items
- 0.0–0.6 s: the bullet is small in the frame while it streaks past the lens on the street.
- 7.8–8.6 s: the orbit from her face to his passes two framings that are mostly wall/shelf.
- X-ray dive (17.6–18.6 s): water and ripples read; the ice cubes barely.
- 18.8–19.2 s: soft, the camera passes close to his reaching arm.
- Faces: expressions are bone-driven (lids, brows, jaw); acting is readable but subtle in wides.
- Audit: one frame (f257) where the camera grazes the edge of the drywall hole; not visible.
- Motion blur on the sparks/flash at f975–1000 is bright; if it clips on the farm, lower `M_Spark` emission (9 → 5).
