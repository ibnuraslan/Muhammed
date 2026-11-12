# ToddlerWell_v004: farm package (final; director-approved fixes)

This is the full 32.5 s film, 1080×1920 at 60 fps (frames 1–1950), ready for RenderStreet. No render has been submitted.

- `ToddlerWell_v004_60fps.blend`: the self-contained scene. Every texture is packed; it opens in factory Blender with no add-ons.
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
5. `../pipeline/anim_look.py` applies the animated-CG look (run on the camera output).
6. `05_package.py` shrinks textures (1K, or 512 for background and normal maps; JPEG), purges orphans, packs everything and saves compressed.

Review tools:
- `audit.py`: feet, BVH penetration and camera checks.
- `hand_audit.py`: hand vs hand, hand vs own body and clothes, and hand vs other characters, every 2 frames.
- `hand_pass.py`: close-ups of every hand action.
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

## Hand audit (scripts/hand_audit.py, every 2 frames, 8 main characters; `hand_audit.json`)
Final count: 13 hand–hand, 548 hand–self, 268 hand–other. Each hit is one frame for one hand against one target.
- **Intended contact (about 350):**
  - The teen gripping and carrying the toddler: 127.
  - ResB's hands at the teen's waist while knotting: 91.
  - The mother's hug and the toddler on her: 95.
  - The toddler's hands at his own head while hanging with arms up: 40.
- **Remaining, not intended:**
  - ResA, ResB and ResC fingertips grazing their own dungarees or vest: about 350 frames.
    - Concentrated in beat 2: kneeling at the rim and feeding rope.
    - Also in beats 6–10: the hold and the haul.
  - Crowd1's cheering hands against her own hair: 94.
  - ResB's hands touching while knotting: 12.
- These were reduced from 862 hand–self in the first run by re-keying three poses: haulers' hands moved off their bellies, ResA's feeding lean, and ResB's kneeling hand. They are the next fix if there is time.

## Final fixes before D (director, 00:15 UTC)
- **22 s, head-first entry:** the leg-holders stand wider (±0.82 m). They grab the ankles only once the legs are up and within reach, and lean less. The camera now frames the dive from the front: the teen centred, a holder on each side, nothing passing through anything.
- **End hug:** the mother holds the toddler at chest height with both arms, one under him and one across his back. His arms go up around her neck.
- The hand-audit figures above come from the build before these two re-keys. Both fixes move hands away from bodies.

## v004 changes (director, 01:00 UTC): hands only
- **Crowd1's cheer:** her hands are now raised above and in front of her head, palms forward, clear of her hair. Her self-hits fell from 92 to 8, and the 8 are her fingertips at her own shirt cuff.
- **Rescuers:** fingertips moved off their own dungarees and vests:
  - The resting hang is wider and further forward.
  - The tired-pose hands sit forward of the knees.
  - The leg-holders' idle hands are forward of the body.
  - ResB's hand rests on the casing lip, away from his own knee.
  - The haul hands sit further along the rope, in front of the body.
- **Hand audit, full film** (every 2 frames, 8 characters; `hand_audit_full.json`, the build before the final cheer tweak): 5 hand–hand, 447 hand–self, 232 hand–other.
- **Re-run on the final build, frames 1760–1950** (`hand_audit_1760-1950_final.json`): 1 hand–hand, 71 hand–self, 134 hand–other.
  - Intended contact: the teen holding the toddler, and the mother's hug against her own body.
- **Remaining unintended:** about 250 frames of rescuers' fingertip grazes on their own clothes. Most come during the kneel at the rim and the hold and haul.
