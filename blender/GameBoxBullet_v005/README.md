# GameBoxBullet_v005: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v005_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v005_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v005_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v004 (hands pass only, client 23:00 UTC); look, animation and timing otherwise unchanged
- Limit Rotation (local space) on every finger and thumb bone of both characters: fingers 0 to 90 degrees forward, no backward bends, +-10 degrees spread; thumb in a natural cone. A wrist limit was tried but broke the IK hand alignment of the grip, so the wrists are left to the IK. The grip is a natural palm-up carry well inside the wrist's range.
- Grip: palms under the box, index and middle fingers wrap up the front edge, ring and little fingers lie flat (no backward bend), and the thumbs rest on the box sides, opposing the fingers. Re-keyed so no finger digs into the cover or bottom.
- Neighbour (walker): her arms were reaching for an unkeyed IK target and are now FK, hanging at her sides with a small swing; relaxed, slightly curled fingers.
- Hand audit (`hand_audit.txt`, `../GameBoxBullet_v001/scripts/07_hand_audit.py`): BVH overlap every 2 frames over 750 frames for each hand vs the other hand, vs own body, vs own shirt, vs the other character and vs the box. **0 flagged frames.** Close-ups: `hands_closeups.jpg`.
- 1-per-second sheet: `sheet_1ps.jpg`.

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
