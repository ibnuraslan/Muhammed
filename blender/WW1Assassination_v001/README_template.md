# WW1Assassination_v002: farm package

The full 35.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `WW1Assassination_v002_60fps.blend`: the self-contained scene, with every texture packed.
- `beats.json`: the beat start frames and their first words, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `SETTINGS.md`: the render settings and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_lowres.jpg`: a low-resolution frame rendered from the packed file in factory Blender. It shows that the package works; it is not a quality reference.
- **VO:** none yet. When it arrives, run `retime_to_vo.py` with anchors from `beats.json`. Every animation is baked keyframes, including the story clock, the visibility switches and the map's fire clock, so the warp keeps everything in sync.

The source is `../WW1Assassination_v001/scripts`, and `scripts/build_all.sh` rebuilds the film from scratch. It runs 01 humans → 02 set → 03 cars/props → 04 animation → 04b horses → 06a/06b map → 05 camera/FX, then `07_slim_textures.py` and `pipeline/package_for_farm.py`.
Assets are not in git. Fetch them with `pipeline/fetch_polyhaven.py` and `pipeline/find_models.py` (the IDs are in `CREDITS.md`). The map needs Natural Earth `ne_50m_admin_0_countries.geojson`.

## How the film works
- **One set:** Sarajevo's riverside quay meets a narrow side street by a stone bridge and a café.
- **The story clock** `SIG(t)` in `00_story.py`:
  - Beats 1–2 show the moment just before the fatal shots.
  - Beat 3 rewinds the whole world: cars, crowd, flags and the explosion all play backwards.
  - Beats 4–6 play the morning: the would-be assassins, the throw in slow motion, the bounce off the folded roof, and the blast under the second car.
  - Beat 7 fast-forwards back to the corner, and beats 8–9 are the shots.
- **One camera**, `CAM_Film`, follows a Catmull-Rom path through 45 framings anchored to moving subjects. There are no cuts.
- **The city→map swap** happens inside a cloud whiteout at frame 1748. The camera keeps rising.

## Known issues
__ISSUES__
