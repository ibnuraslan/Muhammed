# v005b = v005 plus one camera polish: the two one-frame camera snaps (f1486, 74 deg; f1751, 134 deg; a Track-To roll flip) are eased into 6-frame whips, max 54.8 deg/frame. The camera rotation is baked per frame by WW1Assassination_v001/scripts/10_camjump.py. Nothing else changed.

# WW1Assassination_v005: farm package (acting pass)

**v005 = v004 plus the client's acting pass** (`briefs/ACTING_FIX_04-10.md`). Every story-beat frame is unchanged, so `beats.json` is the same.
- The full problem list, with times, is in `../WW1Assassination_v001/review/ACTING_notes.md`: 25 items, from the half-second sheet review, `clip_scan.py` and the mandatory 6-point self-check.
- Before and after half-second sheets: `../WW1Assassination_v001/review/ACTING_v004_sheet_*.jpg` and `ACTING_v005_sheet_*.jpg`.
- `pipeline/clip_scan.py` reports **0 bad ranges** (v004 had 6). The hand audit reports 14: 7 intended palm-on-coat, plus 7 brushes between distant extras.


v005 = v003 plus one change: the cloud wipe now holds a near-white card for 6 frames or fewer (1743–1751) over thinner clouds, so 29.0 s shows rooftops and 29.1 s shows the map coming through.

The full 35.5 s film at 1080×1920 and 60 fps, ready for RenderStreet. No render has been submitted.

- `WW1Assassination_v005_60fps.blend`: the self-contained scene, with every texture packed. It is under 95 MB and committed as a normal git file, with no LFS, per the director's package policy.
- `beats.json`: the beat start frames and their first words, for `pipeline/retime_to_vo.py` when the voiceover arrives.
- `SETTINGS.md`: the render settings and suggested test frames. `CREDITS.md`: the CC-BY credit block for the video description.
- `package_check_1s.jpg`: a 1-per-second sheet rendered from the packed file in factory Blender (270×480, 8 samples). It shows the package works; it is not a quality reference. `hand_closeups.jpg` holds 270×480 close-ups of every hand action.
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

## v005 changes (client look change at 22:45 UTC and the hands rule at 23:00 UTC). Everything else is the same as v002.
- **Look:** `pipeline/anim_look.py` (`--no-sky --sat 1.3 --bump 0.35`) followed by `scripts/09_look.py`:
  - AgX Punchy, saturation ×1.3, bump ×0.35, roughness at least 0.35, and motion blur off.
  - The keyed f-stop is clamped to at least 5.6, the keyed sun energy is ×1.25, and the keyed exposure is +0.35 for a high-key image.
  - A soft shadowless fill sun is added, and the blast smoke is a lighter stylised grey.
- **Hands** (`scripts/08_hands_faces.py`):
  - Every human has a relaxed curl. The curl axis is computed from palm geometry, and the thumb opposes the fingers.
  - Tighter real grips on the parasol, pistol, steering wheel, bomb and the officer's grab.
  - Limit Rotation constraints (local space) on every finger and thumb (0–90° forward on the bend axis, ±10° spread) and on the wrists (±60°, ±35° side, ±70° twist).
  - Clapping hands keep a gap, and the officer grabs the gunman's upper arm instead of his chest.
- **Seating:** the couple's legs stay inside the car, with feet forward under the front seat, knees straight ahead and hips settled into the cushion. Their knees no longer ride over the door at 3–7 s and 25–26 s.
- **Blinks:** the Archduke, Duchess and gunman blink every 2.4–3.6 s, and the gunman flinches at each shot.
- **Faces:** the Archduke and Duchess smile while waving. Their eyes widen, brows go up and jaws drop at the thrown object and at the gun, and their eyes close after the slump. This uses the MPFB face bones (risorius, oris, levator, orbicularis, oculi, jaw).
- **Shots:** muzzle flashes from behind the gunman and the couple's reactions only, with no blood.

## Hand audit
`HAND AUDIT (every 2 frames, frames 1-1748; skeleton capsules: torso r=8.5 cm, head r=7 cm, fingertip/wrist points): {'hand_hand': 2, 'hand_own_torso': 8, 'hand_own_head': 0, 'hand_other_char': 12}`. Full list: `../WW1Assassination_v001/review/v005_hand_audit.txt`. It was about 1,100 hits before the fixes.
- **Hand-in-coat (8, intended):** the would-be assassin's hand slipping into his coat at the chest (7), and the bomber reaching into his coat for the bomb (1).
- **The struggle (4):** the gunman's hand at the officer while the officer pulls him back.
- **Scattered crowd (8):** bomb-site crowd brushing neighbours in the post-blast scatter, seen only at a distance.
- **Clap contacts (2):** palms touching.
- **Head:** no hand enters a head anywhere.
- **Method:** fingertip and wrist points tested every 2 frames against skeleton capsules (torso radius 8.5 cm, head radius 7 cm); this is not a full mesh BVH.
- **Close-ups:** `hand_closeups.jpg` covers the parasol and lap hand, the steering-wheel grip, the hand-in-coat, the bomb grip, the pistol grip and the officer's grab.

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
- **Not added:** the kids, horse cart and pigeons the director asked for.
- **Cycles logs "Failed to load 1 image files"** at render start. Every image is packed and decodes, and the frames look correct.
- **The steering-wheel mesh does not turn,** although the driver's hands follow the rim.
- **A few crowd feet sink 3–4.4 cm** (see the audit).
