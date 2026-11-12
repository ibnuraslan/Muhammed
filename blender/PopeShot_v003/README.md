# PopeShot_v003: farm package

**v003 = v002 + one change only:** the aides' catch fingertips were moved onto the jacket surface. v002 stays approved as the fallback. The sheets and close-ups in v002 apply unchanged except for frames 505–640; see `aide_catch_closeups.jpg`.

This is the full 27.0 s film (frames 1–1620) at 1080×1920 and 60 fps, in the animated look from `blender/STYLE_ANIMATED.md`. It is ready for RenderStreet. No render has been submitted.

- `PopeShot_v003_60fps.blend` (92.7 MB, normal git, no LFS) is fully self-contained: every texture and the HDRI are packed, and there are no linked libraries. Verified with `--factory-startup`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `beats.json`: beat start frames for the voiceover retime (`pipeline/retime_to_vo.py`).
- **No voiceover yet.** The brief supplied our script but no mp3. Timing follows the brief's beat table.
- `D_sheet_1ps.jpg`: 1 still per second, rendered from this packed file. `D_hand_closeups.jpg`: 270×480 close-ups of every hand action.
- `hand_audit.txt`: BVH hand audit every 2 frames.
- `package_check_f380_lowres.png`: a 20 %, 4-sample frame from the packed file opened in factory Blender. It shows the package works; it is not a quality reference.

Source: `../PopeShot_v001/scripts`. Build order:
1. `01_build_humans.py`
2. `02_build_scene.py`
3. `03_animate.py`
4. `pipeline/anim_look.py`
5. `04_prepare_package.py`
6. `pipeline/package_for_farm.py`

## Content
- No blood and no wound at any point. The shot is a pistol seen from behind, one muzzle flash and a slow-motion bullet.
- The bullet path is shown only inside the x-ray porthole on the sky-blue gradient dome.
- All characters are generic MPFB people; the Pope is a generic white-robed elderly man. There is no text or logos anywhere, and the jeep's insignia are painted out.

## Hand audit (every 2 frames, 801 frames checked)
210 hits (v002: 263). v003 changes only the aides' catch: their fingertips now sit on the jacket surface (offset 0.11 -> 0.15 m from the armpit, 0.21 -> 0.25 m on the back). What remains:
- **About 110 frames: the aides' catch (frames 505–640).** Down from about 190 in v002; the fingertips still touch his jacket.
- **45 frames: the seated prisoner's right fingertips touch his trouser leg.**
- **About 50 frames: a standing aide's resting hand touches his own jacket hem.**

There are no hand-through-hand hits, and no finger bends backwards: every finger, thumb and wrist has a Limit Rotation constraint.

## Known issues
- **Theatre:** the surgical drape lies flat on the table under the patient instead of over him; he lies in his white robe.
- **Cassock:** a rigid skirt shell weighted from the legs. It reads as a robe standing up, but folds are modest when seated (the cell); while lying in the theatre it is hidden.
- **Stone:** the columns' marble tint reads slightly golden after the saturation pass.
- **Brief framings:**
  - about 6 frames at 5.6 s where the camera dives through the robe
  - a 0.3 s pass close by the statue's base at 23 s
- **Faces:** brows and lids are animated but subtle at thumbnail size.
