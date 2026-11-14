# GameBoxBullet_v009: farm package

The full 25.0 s film (frames 1–1500) at 1080×1920, 60 fps, ready for RenderStreet. No render has been submitted.

- `GameBoxBullet_v009_60fps.blend`: the self-contained scene, all textures packed (76 MB, plain git, no LFS).
- `beats.json`: the start frame of each beat, built to the brief's target times. No VO exists yet.
  When it arrives: `blender -b GameBoxBullet_v009_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 GameBoxBullet_v009_60fps.blend`.
  Build anchors from `beats.json` (old frame) plus each beat's first-word time from `pipeline/transcribe.py`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_lowres.jpg`: frames 20, 960 and 1490 at 270×480, 8 spp, rendered from the packed file opened in factory Blender, to prove the package works.

Source: `../GameBoxBullet_v001/scripts`. Build order: `01_build_man.py`, `01b_build_walker.py`, `02_scene.py`, `03_anim.py`, `04_audit.py`, then `pipeline/anim_look.py`, `06_anim_fix.py`, `05_prepack.py`, then `pipeline/package_for_farm.py`.
Review sheets: `../GameBoxBullet_v001/polish_sheet_[abc].jpg`; audit `../GameBoxBullet_v001/audit.txt`.

## Changes from v008 (director's moving-preview notes, Nov 14); every story-beat frame unchanged (beats.json)
- **Box macro cut from ~9 s to ~2.5 s:** the case cracks (f661–706), a sharp cutaway where the discs shatter around the slowing bullet (f706–770, camera 0.3 m off, f/11), and the bullet stopped halfway (f770–812). The bullet's path through the layers is retimed into this window. From f812 the camera returns to his face and holds the reaction (face plus the cracked box) through beats 7–9: he stares at the box, glances up at the hole in the wall and back, breathes and blinks.
- **Bullet at ~191–219:** past the drywall the camera swings up and aside (0.3–0.4 m from the bullet) instead of riding 8 cm behind it.
- **Hands:** palms flat under the box, the hand turned so all four knuckles sit just past the front-bottom edge, fingers flat on the front face (skin contact), thumbs on the sides; identical at every hold frame, including 355–383 and 1371–1500.
- **Camera inside geometry (qa_check, 517–613 and 1159):** fixed by moving the hidden cutaway backdrop card back and pulling those keys in.
- **Moving preview:** `review/GameBoxBullet_v009_preview.mp4` (every 5th frame at 12 fps, real speed) and its contact pages `review/preview_page_p01–p06.jpg`, all watched.
- **Checks:** clip_scan **0 bad ranges**; limb_check **0**; hand audit **0 non-contact hits**. qa_check (`review/qa_check_v009.json`) flags only intended cases: EMPTY on the exterior bullet shots (he is inside) and on medium shots where the box (a prop) covers more than his body does; PROPMOVE for the flying bullet; FILL/INSIDE for the 0.3 s wall fly-through and the crack macro.

## Known issues
- f186–195 (about 0.15 s): right after the wall the bullet is still a medium-size soft orb in front of the camera before it moves aside.
- No VO yet, so the timing follows the brief's target times; retime when the VO arrives.
- The shirt fabric touches the back of the box by up to 1.5 cm (hidden behind the box).
- The bullet is small in frame for the first ~1.5 s of the exterior; the bright streak carries it.
- Our own house front is procedural (the bullet cuts its real layers) with scanned siding; the neighbour houses and furniture are real models.
