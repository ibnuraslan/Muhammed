# NukedWell: farm package

This is a 36.0 s true-story short at 1080×1920 and 60 fps, frames 1–2160. It is ready for RenderStreet; nothing has been rendered on a farm.

- `NukedWell_v004_60fps.blend`: the self-contained scene, with every texture packed. It is under 95 MB and committed as a normal git file (no LFS).
- `beats.json`: the start frame of each of the 11 beats with its first words. When the voiceover arrives, run `pipeline/transcribe.py`, then retime with `pipeline/retime_to_vo.py`. Use each beat's frame here as `old_frame` and the second its first word is spoken as `seconds`.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- There is no VO mp3 yet. The film is timed to the beat table in `briefs/18_NukedWell.md`.

## Build from source
The scripts are in `../NukedWell_v001/scripts`. Run them in this order:
1. `01_build_crew.py`: six MPFB crew members.
2. `02_build_scene.py <assets>`: the set, cross-section, props, effects, lights, sky and camera.
3. `03_animate.py <pipeline>`: all the animation, the camera spline and `beats.json`.
4. `04_package.py`: resizes textures to 1K and packs.

`audit.py` is the contact and penetration audit. `cam_path_plot.py` and `cam_path_draw.py` draw the camera path.

The assets come from `pipeline/fetch_polyhaven.py`, plus `pipeline/find_models.py` with the uids listed in `CREDITS.md`.

## How the film works
- **One camera, no cuts.** `CAM_Film` follows a Catmull-Rom spline through about 45 framings, roughly one per second. It sinks through the ground "skin" into the cross-section and back up.
  - The ground's underside is backfacing-transparent, and the strata face sits at y = 0.
  - Below ground, the 9:16 frame stacks the surface world over the cut rock.
- **The device is a plain steel cylinder.** It has bolted flanges, welds, lugs and a shackle, and no internals. The explosion is shown only as underground light, the rock squeezing, a surface heave and a dust ring. There is no mushroom cloud.
- **Rewind (beat 3).** Story elements play backwards, the sun races back and the fire shrinks into the wellhead.

## Look and hands (client rules, Nov 11)
- **Look:** the bright, animated 3D look (`STYLE_ANIMATED.md`), applied by `pipeline/anim_look.py`. `scripts/03b_look.py` follows it and keys the camera sky gradient to night in beats 3 and 5.
- **Hands:** every finger and thumb bone has a Limit Rotation constraint (no backward bends). Relaxed hands are curled, and grips curl around the hose.
  - `scripts/audit_hands.py` runs every 2 frames: hand vs hand, own body and clothes, and other characters.
  - Final count: **0 hits** (`review/D_hand_audit.txt`).

## v004 change (director, Nov 12 12:56): acting pass
This version fixes every unnatural action found in the review of v003. The full list is in `../NukedWell_v001/review/ACTING_notes.md`.
- On-screen teleports are gone. Story time-jumps now play as rewind and fast-forward time-lapses, and one move is hidden in the detonation flash.
- The hose crews pick up and drop the hoses with their hands; no prop pops in.
- There is no miming without a prop.
- Hands no longer pass through bodies during transitions or cheers.
- Frames filled by a wall or a prop are reframed, and faces read on beats 6, 8 and 11.

Story-beat frames are unchanged (`beats.json`). Before and after half-second sheets: `review/ACTING_before_v003_halfsec.jpg` and `review/ACTING_after_v004_halfsec.jpg`.

## v003 change (director, Nov 12 00:54)
This is a hands-only pass; everything else matches v002.
- The soldiers' palms are on the device casing at f1380–1450, within 2 cm, fingers curled.
- All four hose holders' hands are on the hose, within 2 cm, fingers curled.
- The device's swing settles before the grip.

Hand audit: 0 hits, `../NukedWell_v001/review/v003_hand_audit.txt`. Close-ups: `review/v003_hand_contact_closeups.jpg`.

## Known issues
- The brightest part of the fire column turns pale peach under AgX Punchy.
- After the flash, the blast cavity in beat 10 reads as a flat glowing disc.
- The crane is built here (lattice mast, jib, cab), not a scanned model; no period crane model was available.
- The fire trucks are a CC-BY Zil-131 model. Its door markings have not been checked at close range. The camera never comes closer than about 15 m.
- There is no voiceover yet; the timing follows the brief's beat table.
- Wrists and elbows are driven by IK and pole targets, and have no Limit Rotation constraints.
