# Checkpoint C: polish

## Files
- `C_polish_0.2s_part1.jpg` … `part4.jpg`: one still every 0.2 s (163 stills), 270×480, 8 samples.
- `C_contact_closeups.jpg`: close-up pass of every contact moment (debug camera, 270×480).
- `C_audit.json`: the audit output (`scripts/audit.py`, every 20th frame).
- `camera_path.jpg`: the camera path, updated.

## Audit (numeric, every 20th frame, 98 frames)
See `C_audit.json` and the summary in the message. It checks four things:
- **Feet:** the lowest body or shoe vertex against the ground or the shaft floor, for every grounded character.
- **Bodies against bodies:** BVH overlap between body, clothes, shoes and vest meshes for every pair of characters.
- **Bodies against props:** the same overlap between characters and the pipe wall, casing and tripod legs.
- **Camera:** the camera must be inside the pipe or in the cross-section whenever it is below ground, and never within 6 cm of a character.

The remaining overlaps are intended contact:
- The teen's hands on the toddler's wrists while they rise.
- The mother's hug.
- ResB's hands at the teen's waist while knotting.
- The teen's shoulders brushing the pipe wall in a few frames.

## Changes since B
- **Sliding feet removed:** every change of position for the rescuers is now a real walk with planted IK feet.
  - Each move clears the keys in its range and walks a path routed around the pit, the casing and the tripod legs.
- **Tripod:** taller (3.4 m) and wider. The legs moved so they clear the rescuers' heads. The pulley moved up with it.
- **Pipe:** widened to Ø0.72 m with a smaller wall wobble. The teen's elbows tuck in while he is inside the pipe.
- **Grab and rise:** the teen sits lower in the shaft, so his arms reach straight down. He grips the toddler's raised hands, and the toddler hangs below him without the heads clashing.
- **Hi-vis vests:** rebuilt from the smooth body mesh, offset 4.5 cm, so there are no shards from the dungarees' bib straps.
- **Head torch:** strap and lamp now sit on the forehead. The strap was 1 m above the head because of a transform-apply bug.
- **Knot beat:** now a true side view between the teen and ResB. The tie spot moved out of the tripod. ResA checks a tripod leg.
- **Excavator:**
  - Its internal node name clashed with my control, so the animation went to the wrong object. That's fixed.
  - It's scaled to a realistic size and faces the pit.
  - The dump swings to the spoil heap.
- **Lighting:** the shaft has bottom and mid fill (keyed), a 90 W head torch, and a dust volume, so the beam reads.
- **Look:** warmer and darker dusty ground, and softer soil strata.
- **Crowd:** the teen stands in the crowd from frame 1, as a passer-by. The crowd was extended with duplicates (see below).
- **Camera:**
  - The knot, flip and emergence framings were re-planned around the tripod legs and the rescuers.
  - The bucket close-up is less tight.

## Director's B notes: what changed
1. **Soil cross-section:** now a real soil profile instead of wood grain.
   - Bands, top to bottom: dark topsoil, dry clay, gravel, red laterite clay, sand, darker clay, gravel, wet laterite. These use the CC0 Poly Haven scans (forrest_ground_01, excavated_soil_wall, gravelly_sand, red_laterite_soil_stones).
   - The band boundaries are wavy.
   - There's moisture darkening below 5 m.
   - Heavy bump from the scans' displacement maps.
   - 90 scanned stones (CC BY "Rocks Set Stone Collection Scan") are embedded in the cut face, 40 in the shaft wall, and pebbles lie on the floor.
   - 34 roots sit in the top 1.4 m.
   - The pipe wall uses the same strata.
2. **Excavator:**
   - Real size (×2.1).
   - Close-ups: tracks rolling in, the bucket biting at the pit, the cab with a seated MPFB operator swinging with it, and dirt pouring at the heap.
   - Dirt clods now pour from the bucket's real position at each dump.
   - Diesel exhaust puffs come from the engine deck.
3. **Toddler:**
   - He cries with his head tipped back, jaw open and arms up, in a lit close-up at the shaft bottom (3.6–4.0 s).
   - At the end he calms against his mother: the jaw closes and his head rests on her.
4. **Mother:**
   - She's restrained at the tape by a neighbour's hand on her shoulder, leaning over and pleading, with hands to her face.
   - The camera gives her a beat at 14.9 s.
   - She ducks the tape and runs in, takes the toddler, and sinks to her knees in relief.
5. **Knot:** a side framing with ResB's hands at the waist and the teen's face reacting (looking down at the knot, then up). No blank frames.
6. **Crowd:** 20 extra MPFB villagers (real duplicates, not instances). Each has a 0–2 s NLA time offset, a 0.93–1.06 scale and a different clothes tint.
7. **Vests:** rebuilt from the smooth body mesh, with smoothing and subdivision. No armpit tear.

## Realism pass (no primitives)
- **Cones and rope coils:** real CC BY models. The bottles are removed.
- **Tripod:** bark-textured poles, a bevelled rusty-steel head, a hand winch with crank and plates, and a chain.
- **Collar and spoil heap:** a concrete collar at the well, and a spoil heap sculpted with noise displacement and soil material.
- **Clods:** lumpy and displaced.
- **Pipe:** tight Ø0.58 m, as the director asked.
- **Teen:** goes in like a dive, with arms straight overhead, elbows tucked, feet together and toes pointed.
  - His width tapers 10 % while inside.
  - Numeric check: every teen vertex at frames 1401 and 1700 is within 0.26 m of the pipe axis. The wall is at 0.275 m.

## Known issues
- Vests still show slight vertical ridges from behind at bends.
- The crowd duplicates reuse four villagers' motion, time-offset by 0–2 s.
- The excavator is a rigid-part rig. The bucket comes near the pit but doesn't visibly scoop soil; the dirt clods sell the dig.
- No VO yet. Everything is built to the brief's target times, and `beats.json` is ready for `retime_to_vo.py`.

## Look change and hands (director, 22:45 and 23:00 UTC)
- **New look:** `pipeline/anim_look.py` applied as the last build step:
  - AgX Punchy, saturation up, bump down, roughness ≥ 0.35, f-stop ≥ 5.6, no motion blur.
  - A sky-gradient backdrop with soft clouds, and brighter shaft fill lights.
  - The sun stays day-bright through the time-lapse, with no golden-hour grade.
  - `C_1s_animlook.jpg` is the 1/s sheet in this look. The director dropped the 0.2 s sheets.
- **Hands:**
  - Relaxed curled fingers on everyone, and real grips while holding: rope, ankles, wrists, knot, tripod leg, levers, hug.
  - Limit Rotation (local) on every finger, thumb and wrist bone.
  - `C_hand_closeups.jpg`: 16 close-ups of every hand action.
- **Hand audit** (`scripts/hand_audit.py`, every 2 frames, 8 main characters; `C_hand_audit.json`):
  - The C run counted 4 hand–hand, 862 hand–self and 267 hand–other hits.
  - Most hand–self hits came from three poses, now re-keyed for D:
    - the haulers' hands on a rope line that ran through their own belly
    - ResA's rope-feeding lean
    - ResB's kneeling hand, and the cheering hands in the hair
  - The hand–other hits are intended grips: the teen holding the toddler, the mother's hug, and ResB knotting at the teen's waist.
  - D reports the re-run count.
