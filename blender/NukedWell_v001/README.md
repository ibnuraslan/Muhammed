# NukedWell: farm package

This is a 36.0 s true-story short at 1080×1920 and 60 fps, frames 1–2160. It is ready for RenderStreet; nothing has been rendered on a farm.

- `NukedWell_v002_60fps.blend`: the self-contained scene, with every texture packed. It is under 95 MB and committed as a normal git file (no LFS).
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
