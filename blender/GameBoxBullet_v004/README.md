# GameBoxBullet_v004: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v004_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v004_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v004_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v003 (client look change, 22:45 UTC: bright, clean 3D animation, not live-action)
- `pipeline/anim_look.py` applied: AgX Punchy, sky gradient seen by the camera, saturation up, bump/normal down, roughness >= 0.35, f-stop >= 5.6, motion blur off, volumes thinner, lights x1.25.
- Hand fixes (`../GameBoxBullet_v001/scripts/06_anim_fix.py`): the cross-section card is now the sky-blue gradient (#4FC3F7 to #E8F7FF, self-lit); cleaner cream pages; brighter section key; exposure +0.35; brighter bedroom fill and lighter blue walls; lighter house siding.
- Animation, geometry and timing are unchanged from v003 (v003 is kept as is). The v003 changes (smile, wide eyes, grip fix) are all included.
- 1-per-second review sheet: `sheet_1ps.jpg` (270x480, 8 spp).

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
