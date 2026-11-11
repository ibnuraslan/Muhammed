# StanleyCup_v005: farm package (v004 + hands pass; v004 kept as is) (built to the brief's target beat times; no voiceover yet)

The full 25.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `StanleyCup_v005_60fps.blend`: the self-contained scene (67 MB, normal Git file; LFS upload was refused tonight). Every texture is packed; it opens in factory-startup Blender 5.2.2 with no add-ons.
- `beats.json`: beat start frames + first words, for `pipeline/retime_to_vo.py` when the VO arrives.
- `SETTINGS.md`: render settings, measured cost, suggested test frames. `CREDITS.md`: all assets are CC0 (no CC-BY block needed).
- `audit.txt`: contact audit on the final file.
- `review/hands_pass_1s.jpg`: 1 still/s sheet; `review/hand_closeups.jpg`: hand close-ups; `hand_audit.txt`, `audit.txt`.

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

## Hands pass (client, Nov 11 23:00): the only change from v004
- `scripts/06_hands_pass.py`: Limit Rotation (local space) on all 64 finger, thumb and wrist bones: fingers flex 0–100° about local +X
  (verified in close-ups; no backward bend), ±5° twist, ±10° spread; thumb cone; wrist ±60° flex / ±25° side; elbow IK limits.
- Finger curls re-keyed as true hinge flexion (they were twisting/splaying before); relaxed default curl; real grips:
  her fingers wrap the tumbler handle with the thumb over it, his hand curls around her forearm.
- Her hand-to-mouth gasp and hand-on-chest moved in front of the body with the elbow down and out (the arm was wrapping over the shoulder);
  head bow reduced so her face doesn't push into her own hand.
- `hand_audit.txt` (`scripts/hand_audit.py`, BVH every 2 frames: hand vs hand, hand vs own torso/head and clothes, hand vs the other
  character; penetration > 6 mm): **0 hits**.
- Close-up check: `review/hand_closeups.jpg`. 1 s sheet: `review/hands_pass_1s.jpg`.

## Look (client change, Nov 11 22:45): bright animated 3D, not live action
Made from the accepted v003 with `pipeline/anim_look.py` (AgX Punchy, sky-gradient backdrop for camera rays, saturation ×1.25,
bump ×0.35, roughness ≥0.35, motion blur off, lights ×1.25), then `scripts/05_anim_look_fixes.py`:
- animated f-stop keys clamped to ≥ f/5.6 (f/4 only on the impact and condensation macros)
- daylight sun instead of dusk; street lamps off; window glow down
- exposure keys +0.25 street / −0.05 room; interior fill lights lifted
- clean pale-blue painted walls/ceiling instead of the plaster scan
- brighter cyan x-ray, sparks toned to stay below blowout, lighter wall-cavity timber
Review: `review/animated_look_1s.jpg` (1 still/s, 270×480, 8 samples). Animation, camera and geometry are identical to v003.

## Changed in v003 (vs v002)
- Beat 5 weaves cup → her frightened face → cup/ice top-down → his reaching hand → cup, ~1 s each (one move).
- Dent is a visible crater with chipped powder coat (bare steel) from the impact on; she turns it toward camera as she lifts it.
- Bullet on the floor: one bounce, then rolls to a stop.
- Room: more framed pictures (no text), plants, armchair, warm wall sconces, curtains moving.
- Neighbour houses are real CC-BY models (credit block in CREDITS.md is now REQUIRED in the description).
- Ice reads in the x-ray dive.

## Known open items
- 0.0–0.6 s: the bullet is small in the frame while it streaks past the lens on the street.
- 7.8–8.6 s: the orbit from her face to his passes two framings that are mostly wall/shelf.
- 18.8–19.2 s: soft, the camera passes close to his reaching arm.
- Faces: expressions are bone-driven (lids, brows, jaw); acting is readable but subtle in wides.
- Audit: one frame (f257) where the camera grazes the edge of the drywall hole; not visible.
- Motion blur on the sparks/flash at f975–1000 is bright; if it clips on the farm, lower `M_Spark` emission (9 → 5).
- No audio, so no bullet "ding" on the floor; add it in the edit.
- Our own house shell, the tumbler and the bullet are scripted geometry (tumbler/bullet are lathe models with displacement and textures); street has no car/dog yet.
