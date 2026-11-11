# ToddlerWell_v002: farm package

This is the full 32.5 s film, 1080×1920 at 60 fps (frames 1–1950), ready for RenderStreet. No render has been submitted.

- `ToddlerWell_v002_60fps.blend`: the self-contained scene. Every texture is packed; it opens in factory Blender with no add-ons.
- `beats.json`: the start frame of each of the 11 beats, with the first words of each line.
  - The VO hasn't arrived yet, so the film is built to the brief's target times.
  - When the VO arrives, run `pipeline/transcribe.py` on it. Then run `pipeline/retime_to_vo.py` with anchors taken from `beats.json`, to warp every keyframe onto the words and add the VO strip.
- `SETTINGS.md`: render settings and test frames.
- `CREDITS.md`: the CC BY block for the video description.

## Source
The scripts are in `../ToddlerWell_v001/scripts/`. Build order (run from `blender/ToddlerWell_v001/`):
1. `01_build_cast.py` builds the MPFB humans.
2. `02_build_scene.py` builds the set: field, 15 m shaft, cross-section earth, tripod, props, excavator, vegetation, sky, vests, hats and head torch.
3. `03_animate.py` animates everything: all characters on IK with planted feet and walks between spots, ropes, the excavator and operator, the time-lapse sky, lights and FX, plus the crowd duplicates.
4. `04_camera.py` keys the one continuous camera: a Catmull-Rom spline through about 75 framings.
5. `05_package.py` shrinks textures, packs everything and saves the package compressed.

Review tools:
- `audit.py`: feet, BVH penetration and camera checks.
- `contact_pass.py`: close-ups of every contact moment.
- `stills_range.py`: review stills.
- `camera_path_plot.py`: the camera path plot.

## Known open items
- No VO is in the file yet. See above.
- Hi-vis vests are offset copies of the body torso. They can show slight ridges from behind at strong bends.
- The teen is narrowed by 10 % in width (rig object scale) while he is inside the 0.58 m pipe, so his shoulders clear the wall. It isn't visible in the frame.
- Crowd duplicates are time-offset copies of four MPFB villagers, with tinted clothes.
- The excavator is a rigid-part rig. Its tracks do not scroll.
- The toddler cries with an open jaw and head tipped back. There are no tear streaks.
