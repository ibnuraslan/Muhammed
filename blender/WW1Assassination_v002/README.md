# WW1Assassination_v002: farm package

The full 35.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `WW1Assassination_v002_60fps.blend`: the self-contained scene, with every texture packed. It is under 95 MB and committed as a normal git file, with no LFS, per the director's package policy.
- `beats.json`: the beat start frames and their first words, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `SETTINGS.md`: the render settings and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_1s.jpg`: a 1-per-second sheet rendered from the packed file in factory Blender (270×480, 8 samples). `frame0120_fullres_48spp.jpg` is one full-quality frame from the earlier v002 build. Both show the package works; neither is a quality reference.
- **VO:** none yet. When it arrives, run `retime_to_vo.py` with anchors from `beats.json`. Every animation is baked keyframes, including the story clock, the visibility switches and the map's fire clock, so the warp keeps everything in sync.

The source is `../WW1Assassination_v001/scripts`, and `scripts/build_all.sh` rebuilds the film from scratch. It runs 01 humans → 02 set → 03 cars/props → 04 animation → 04b horses → 06a/06b map → 05 camera/FX, then `07_slim_textures.py` (skins as 2K JPEG, data and cloth maps as 1K JPEG, hair kept as PNG, and lossless thinning of 1.67M constant keys) and `pipeline/package_for_farm.py`.
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

## Fixes from the director's notes (applied after checkpoint C)
- **Helmet:** a dark shell fitted to the skull with a thin gold band and finial, plus about 70 thin dark-green plume strands streaming back. Nothing covers the eyes. It is placed from the evaluated skull top and is Child Of the head bone (the parent bone).
- **Archduke:** a handlebar moustache placed from the evaluated nose tip.
- **Couple:** both sit about 10 cm lower in the seat.
- **Would-be assassins:** 1914 suits instead of overalls, and one flat cap.
- **Cloud wipe:** finer cloud noise and a 60 % card, so detail (rooftops, then map borders) shows through the swap. No frame is blank.
- **Map:** muted red Central Powers and muted blue Entente, lit state borders, a darker sea, saturated fire fronts and embers, larger flags, and soft alpha smoke wisps. The relief mesh is decimated (STEP 4).
- **Blast smoke:** dark grey-black.
- **Crowd:** 0.8 m minimum spacing, and randomised flee targets so no two people end up in the same spot.

## Audit (`../WW1Assassination_v001/review/D_audit.txt`)
- **Penetration counts** (sampled every 20 frames up to the map swap): `{'people_overlap': 73, 'hand_off_prop': 0, 'helmet_clip_or_gap': 0, 'seat_sink': 0}`.
  - **People overlap:** almost all of it is one bomb-site crowd pair that ends up 0.3 m apart after the scatter, seen only at a distance during the rewind and the post-blast orbit. The rest is the officer grabbing the gunman, which is intended contact.
  - **Props:** hand-to-pistol and hand-to-parasol offsets stay within 2 cm of their attach offsets.
  - **Helmet and seat:** the helmet keeps a constant offset from the head bone (no clip or gap), and the Archduke's pelvis never sinks below the seat.
- **Camera:** the café CAM_IN flags are false positives from the cornice overhang in that building's bounding box; the camera is 35 cm outside the wall.
- **Feet:** the worst sink is 4.4 cm.

## Known issues
- **No VO yet.** Beats are built to the brief's target times; retime once the mp3 arrives.
- **1914 borders are approximate.** Modern Natural Earth countries are grouped into the 1914 states.
- **The rewind grade is a white-balance shift plus an exposure flicker.** The compositor needs a GPU context headless, so compositing is off.
- **No facial rig.** Expressions come from head and body acting only, and the faces are the stock MPFB skins.
- **Not added:** the kids, horse cart and pigeons the director asked for.
- **Cycles logs "Failed to load 1 image files"** at render start. Every image is packed and decodes, and the frames look correct.
- **The steering-wheel mesh does not turn,** although the driver's hands follow the rim.
- **A few crowd feet sink 3–4.4 cm** (see the audit).
