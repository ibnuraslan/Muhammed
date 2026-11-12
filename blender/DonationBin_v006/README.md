# DonationBin_v005: farm package (acting fix) (director's B and C notes applied)

This is the full 41.5 s film at 1080×1920 and 60 fps, frames 1–2490, ready for RenderStreet. No render has been submitted.

- `DonationBin_v005_60fps.blend`: the self-contained scene. Every texture is packed. It opens in factory-startup Blender 5.2.2 with no add-ons.
- `beats.json`: the start frame of each of the 11 beats at the brief's target times, for `pipeline/retime_to_vo.py` once the voiceover exists.
- `SETTINGS.md`: render settings and suggested test frames. `CREDITS.md`: the CC-BY block for the video description (7 Sketchfab models via Objaverse), plus CC0 provenance.
- `package_check_lowres.jpg`: a 270×480, 8-sample frame (f2045) rendered from the packed file in factory Blender. It shows the package works; it is not a quality reference.
- `review/`: the 0.2 s polish contact sheets and the contact audit.

**No voiceover yet.** The film is built to the brief's target beat times (frame = 1 + t·60). When the VO arrives:
1. Run `transcribe.py` to get word times.
2. Write anchors from `beats.json`: the old frame, plus the second each beat's first words are spoken.
3. Run `blender -b DonationBin_v005_60fps.blend --python ../pipeline/retime_to_vo.py -- anchors.json vo.mp3 out.blend`.

The source is `../DonationBin_v001/scripts`. Build order: `01_build_humans.py`, then `02_build_scene.py`, then `03_animate.py` (it runs `03b_fx_camera.py`), then `audit.py`, then `04_package_prep.py` (texture trim) and `pipeline/package_for_farm.py`. The assets come from `/opt/assets/ph` (Poly Haven, fetched by `pipeline/fetch_polyhaven.py`) and MPFB2.

## v005: acting fix (client, Nov 12)
This version re-stages the woman's performance from the shove to the rescue sit-up, plus the camera inside the bin, on the unchanged v004 timeline. Every story-beat frame is the same, and `beats.json` is identical to v004's. The full list of fixes is in `review/ACTING_notes.md`.

The source is `../DonationBin_v001/scripts/06_acting_fix.py`, which runs after 03 and before 05.

Review files:
- `review/BEFORE_v004_0p5s.jpg` and `review/AFTER_v005_0p5s.jpg`: half-second sheets
- `review/hands_closeups_v005.jpg`: hand close-ups
- `review/clip_scan_v005.json`: the clip scan. 0 bad ranges on camera; f1507 and f2029 are off camera with the bin closed.

## v004 changes (director's v003 review)
- **Inside-bin framing (16–22 s):** the camera finds her face from her head bone at each key, inside the bin. You now see her worried face with her palms on the wall and the flap, and her face looking up when she jumps. She also stands further from the wall and the flap so the camera fits in front of her. 16 s (f961) is still a short transition from behind as the camera re-enters.
- **Her face** reads clearly at about 18–19 s (trapped, worried), 22 s (calling), 28 s (curled, three days) and 35 s (climbing out, rescued).
- **Macro (14–15 s):** a wider 28 mm lens, so the stop bar, flap and hinge read together, with no tread-plate-only frames.
- **Bins:**
  - rounded (bevelled) edges and pressed-steel ribs with panel seams
  - rivet rows on the front
  - a sloped hood with a grab handle, and the stop bar
  - a white T-shirt clothing icon with no text, on every bin
- **Turnout:** each firefighter wears a turnout coat over the overalls: a shell made from the body's torso, arms and collar, inflated with folds. It has a dark front zip seam, a darker raised collar and reflective bands that ride over the folds, plus sleeves and gloves. Faces stay visible under the helmets.

## Look and hands pass (client direction, 22:45 and 23:00 UTC)
- **Animated look** (`blender/STYLE_ANIMATED.md`), applied by `../DonationBin_v001/scripts/05_look_hands.py`, which runs `pipeline/anim_look.py`:
  - AgX Punchy, a sky-blue gradient for camera rays, saturation ×1.25, bump ×0.35, roughness at least 0.35, f-stop at least 5.6 and no motion blur.
  - The keyframed light energies and HDRI strength are scaled to match.
  - The bins are clean painted metal (green, plus the purple, teal and grey row), not rusty.
  - The night time-lapse is a readable blue, with moon fill on her.
  - The x-ray backdrop is the sky-blue gradient.
- **Hand limits:** Limit Rotation (local) on every finger (0–90° bend, ±5° twist, ±10° spread), every thumb (a cone) and every wrist (±60° flex, ±45° twist, ±25° side) on all 5 characters, 160 constraints in all. Elbows bend only toward their IK poles.
- **Palms:** contact palms now face the surface they touch (flap, walls, the shover's push).
- **Hand audit** (`scripts/hand_audit.py`, a BVH test every 2 frames of hand vs hand, hand vs own torso, neck and head, and hand vs other characters): it went from 532 hits to **110 hits on 87 frames**. What remains:
  - 55 (her scream, f1319–1339 and f1393–1479): her cupped hands' fingertips touch at her mouth. This is intended contact (≤8 mm), not penetration.
  - 13 + 1 (the shover's hands during and after the shove, f157–231): his hands come within 8 mm of each other, and once a hand touches his own chest.
  - 35 (her, own torso): brief moments when her hands are near her chest or face while she pushes and searches the flap and lands from the jump (f803–835, f1105–1171, f1261–1269, f1311–1315), plus 3 single frames.
  - The other-character check shows 0 (FireB's hold is on her outer arm).
- **Close-ups:** `review/hands_closeups.jpg` holds 14 hand actions at 270×480.

## Changes from v002
- **Costume:** she wears a plain burgundy tee and jeans (no crop top, no logo).
- **Clothes pile:** two CC-BY scanned cloth heaps and CC-BY plastic bags on a denim-textured base heap. The balloon spheres are gone.
- **Firefighters:** turnout overalls show the fabric's fold texture, tan with reflective bands. They have turnout sleeves, black leather gloves on the articulated MPFB hands, black boots, a CC-BY breathing cylinder on the back and CC-BY helmets. The box cutter is replaced by a CC-BY angle grinder held in both hands.
- **Beat 10:** a 3/4-front framing of firefighter A's face through the sparks (around f2012), lit by the spark light.
- **Beat 7:** she pounds the front wall twice with her fists and the steel and flap shudder.
- **Mechanism:** the flap, stop bar and pawl are textured steel tread plate and stay opaque, with a warm rim, in the x-ray. The ghost shell is a deeper cyan and the studio gradient deeper teal.
- **Lighting:** the interior is brighter: more fill and exposure, plus a raking spotlight from the slit across her and the clothes.
- **Bin row:** the three extra bins are painted purple, teal and grey.
- **Fly-throughs:** the x-ray stays on while the camera passes through the side walls (f492–975), the slot entry is faster, and the flap passes go through textured tread steel.
- **Bin height:** the bin is now 2.45 m tall (was 2.15) so she has headroom on the clothes and the walls read "too high to climb". Her head peaks at 2.38 m against a 2.44 m inner roof on the jump.
- **Stepping:** she now steps between standing poses on the clothes, one foot at a time, instead of sliding through the heap.

## Known issues
- **Hair-top frames:** a few transitional frames inside the bin still show the top or back of her head: about 15.5 s (camera arriving from the x-ray), 21.5 s (turning from the back wall) and 23 s (the flap pass).
- **Curled pose:** in the three days she lies on her side, so her face reads rotated in the vertical frame.
- **No VO:** the film is built to the brief's target times, so it needs a retime once the narration exists.
- **Fly-throughs:** the side-wall passes happen while the x-ray is on, so they read as ghost steel. The flap passes (out at about f1395, in at about f1570 and out at about f1870) go through textured steel and last about 4–8 frames each.
- **Feet on the clothes:** her toes and heels press up to about 12 cm into the soft scanned cloth heaps in beats 5–7 (f944–1310); on soft clothes I'd treat that as plausible. During three short pose transitions (f966–972, f1314–1320, f1390–1392) both feet are briefly up to 11 cm off the heap.
- **Finger tips:** they touch the bin walls with up to 4 mm of penetration during the wall pats and the jump (f1177–1303), and when the passer-by knocks (f1925–1957). Not visible at these framings.
- **Remaining simple geometry:** the bin panels, hood, stop bar and pawl are bevel-free boxes, though textured. The bottle, the puddles (flat discs), the leaves and the paper bag (crumpled planes) and the dust motes are also procedural.
- **Firefighter helmet:** the CC-BY helmet has no face shield, so "visor up" is the default look. Its helmet torch sits on top.
- **Simple hand poses:** fingers use a single curl value, so there are no individual finger grips on the cutter or the panel edge.
- **Keyframed acting:** the fall and tumble through the chute are keyed, not simulated. Clothes, bags and the blanket do not simulate either: the bags squash on her landing via scale keys, and the blanket is a skin-following shell.
- **Wall pounding:** when she pounds the wall in beat 7, the shudder is a few millimetres of shell translation, not a deformation.
- **The woman's outfit** is the MPFB `female_casualsuit01` tee and jeans. The tee's logo and orange piping were painted out of the texture (`../DonationBin_v001/textures/`) and the tee recoloured burgundy.
- **Turnout gear:** the firefighters wear MPFB work overalls with the fabric's own fold texture, tinted tan with reflective bands. Their sleeves and black gloves are materials on the MPFB arm and hand faces (no separate cloth), so a sleeve shows no thickness at the cuff. Each firefighter wears a CC-BY helmet (with its helmet torch) as a child of the head bone, and a CC-BY cylinder on the back serves as the breathing pack. There are no harness straps.
- **Clothes pile:** two CC-BY scanned cloth heaps and CC-BY plastic bags sit on a textured procedural base heap. Contacts are ray-cast against all of them.
- **Bin row:** the three bins in the final reveal are duplicates of the hero bin, repainted purple, teal and grey.
- **Background sign:** the HDRI background contains a generic blue "P" parking sign, with no brand.
