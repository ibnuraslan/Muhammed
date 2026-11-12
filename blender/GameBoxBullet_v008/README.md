# GameBoxBullet_v008: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v008_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v008_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v008_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v007 (grip, director review of v007): story-beat frames unchanged
- A real two-hand carry: palms flat under the box bottom (contact, 0.6 mm), fingers wrapping up the front-bottom edge (no finger inside the box), thumbs on the sides, forearms under the box, elbows bent and close to the body. The hands take the weight in every hold frame (1–25 s), including the turn at 4–5.5 s and the hit at 6.5 s.
- Close-ups from 6 angles and frames (f61, f301 front and below, f330 far side, f400 hit, f1440): `review/hands_closeups_v008.jpg`. After sheet: `review/after_v008_0p5s_sheet.jpg`. Notes: `review/ACTING_notes.md` (item 8).
- Checks: clip_scan **0 bad ranges** (`review/clip_scan_v008.json`); hand audit **0 non-contact hits** (`review/hand_audit.txt`; hand-vs-box overlaps are the grip contact, max 18 triangle pairs per frame); camera min clearance 2.9 cm.
- Everything from the v007 acting pass is kept (camera at 2.5 s, 3–3.5 s, 6.5–7 s, 9.5–10.5 s; weight shifts; blinks and breathing).

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
