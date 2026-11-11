# GameBoxBullet_v002: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v002_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v002_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v003_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- No facial rig beyond jaw and eyes: there is no grin before the hit. Shock reads through the jaw drop, head and body.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box); for about 0.2 s at 23.6 s some fingers sit in the box's bottom edge while he tilts it.
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers: siding, sheathing, studs, insulation, drywall) with scanned siding; the neighbour houses and furniture are real models.
