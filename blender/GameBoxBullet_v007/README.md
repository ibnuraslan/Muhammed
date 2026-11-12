# GameBoxBullet_v007: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v007_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v007_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v007_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v006 (acting pass, director 12:56 UTC Nov 12): story-beat frames unchanged (beats.json)
Full list with frames: `review/ACTING_notes.md`. Before/after half-second sheets: `review/before_0p5s_sheet.jpg`, `review/after_0p5s_sheet.jpg`.
- 2.5 s: the wall approach no longer fills the frame with blank siding. The camera rides further back and to the side, so the window, shutter and eave read.
- 3.0–3.5 s: the drywall dust is moved off the camera line and the depth of field is stopped down (f/22 for f184–232), so the room, the man and the incoming bullet read instead of a grey blur.
- 4–5.5 s: he shifts his weight from foot to foot, his head and shoulders follow the box he's turning, and his feet stay planted.
- 6.5–7 s (impact beat): the camera is raised, so his face and the hit on the box are in one frame (his face was cut off at the chin).
- 9.5–10.5 s: the camera is out to the side, so his face isn't hidden behind the box.
- Shock face: jaw breathing, blinks every ~2–3 s, a small head tremor after the hit (it was a frozen open-mouth mask).
- Grip (v006 chest carry) unchanged; close-ups in `review/hands_closeups_v007.jpg`.
- Checks: `pipeline/clip_scan.py` → **0 bad ranges** (`review/clip_scan_v007.json`); hand audit → **0 non-contact hits** (`review/hand_audit.txt`); camera never inside geometry (min clearance 2.9 cm); planted foot within 0.1 mm.

## Known issues
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
