# GameBoxBullet_v006: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v006_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v006_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v006_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v005 (grip redo, director 23:35 UTC); look, animation and timing otherwise unchanged
- New grip: a real carry against the chest. Palms flat on the two sides of the box (measured palm-to-side gap 3.6 mm, i.e. touching), fingers curled under the bottom corners, thumbs on the sides, elbows bent. Replaces the v005 palm-up hold where the box floated above splayed fingers.
- Finger and thumb Limit Rotation (no backward bends) and the walker's relaxed FK arms are kept from v005.
- Hand audit (`hand_audit.txt`): every 2 frames over 750 frames, each hand vs the other hand, own body, own shirt, the other character and the box. **0 non-contact hits.** Hand-vs-box overlaps are the grip contact itself (palm/thumb pad pressing the side, at most 8 triangle pairs in a frame, i.e. a few mm).
- Close-ups: `hands_closeups.jpg` (f300 side, front, below; f1440 both sides). 1-per-second sheet: `sheet_1ps.jpg`.

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
