# MonkeyHeadTransplant_v005: farm package

This is the 29.5 s film (1770 frames at 60 fps, 1080×1920), built to our 80-word script at the brief's target beat times. No render has been submitted.

- `MonkeyHeadTransplant_v005_60fps.blend`: the self-contained scene, with all textures packed. It opens in factory Blender 5.2.2.
- `beats.json`: the start frame and first words of each beat, ready for `pipeline/retime_to_vo.py` when the VO arrives. There is no VO mp3 yet.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_f*_lowres.jpg` (frames 330, 862, 1110 (from v003)): 20 %, 4-sample frames from the packed file in factory Blender. They show the package works; they are not a quality reference.

**Source:** `../MonkeyHeadTransplant_v001/scripts`. Build order:
1. `01_build_monkey.py`
2. `01b_build_people.py`
3. `02_build_scene.py`
4. `03_animate.py`
5. `package_for_farm.py`

**Review:** `../MonkeyHeadTransplant_v001/review/` holds the 0.2 s polish sheets, the 1 s blocking sheet and `audit.txt`.

## v005: hands pass (client, 23:00 UTC)
This is v004 with only the hands changed (see the "Hands" section of `blender/STYLE_ANIMATED.md`).
- **Limit Rotation constraints** (local space) on every finger and thumb bone of all three staff, 210 bones in total:
  - fingers bend 0–90° forward only, with ±10° spread
  - the thumb moves in a natural cone
- **Relaxed default hand:** every hand key carries a light curl.
- **Grips:**
  - The left palm is on the temple with the fingers curled over.
  - The right hand cradles the skull flat, with no curl, so the fingers of the two hands no longer merge around the head.
- **Re-keyed self-intersections:**
  - The carry approach starts from the shoulder grip.
  - The surgeon's hands are apart while waiting.
  - The hanging hands are moved off the thighs.
  - The surgeon lifts the clipboard before he steps, so it no longer goes through his chest or hip.
  - The nurse turns smoothly at the ends of her walks (no 180° snap), with a smooth hand-off from the trolley.
- **Hand audit:** `hand_audit.txt` (`v001/scripts/hand_audit.py`). It checks every 2 frames with BVH each hand against:
  - the other hand
  - its own torso, legs and head (arms excluded)
  - its own gown
  - the other characters
- **Result:** 16 frames flagged, 133 sampled finger vertices in total, with at most 22 per frame. All of these are light contact during grip changes:
  - head pickup (frames 213–221)
  - release (397–401)
  - fingers meeting behind the head mid-carry (297–303)
  - a gown brush at 705
  - the nurse's trolley hand-off (161, 181)
- **Review:**
  - Sheet: `../MonkeyHeadTransplant_v001/review/v005_hands_sheet_1s.jpg`
  - Hand close-ups: `../MonkeyHeadTransplant_v001/review/v005_hand_moments.jpg`

## v004: animated look (client, 22:45 UTC)
This is v003 with the look moved to a bright, clean 3D animation; see `blender/STYLE_ANIMATED.md`. Animation and geometry are unchanged.
- **`pipeline/anim_look.py`:**
  - AgX Punchy.
  - A sky-gradient world for camera rays, with brighter lighting.
  - Saturation ×1.25 and bump ×0.35.
  - Roughness at least 0.35, f-stop at least 5.6, motion blur off.
- **`v001/scripts/04_anim_look_fixes.py`:**
  - The x-ray void and the glow behind the frosted partition use the sky gradient (#4FC3F7 to #E8F7FF). The void ramp is flipped so cyan is at the top of the frame.
  - The x-ray spine has a cream glow.
  - The floor and walls are lighter, and the fill and rim lights are ×1.6.
  - The end dim is softened from −0.9 EV to −0.35 EV.
- **Review sheet:** `../MonkeyHeadTransplant_v001/review/v004_animlook_sheet_1s.jpg` (1 per second, 270×480, 8 samples).
- **Package check stills:** the `package_check` stills are copied from v003, so they show the old look.

## Changes from v002 (director's C notes)
- **Blinks:** the camera now rolls during the face push-in (11–16 s), so the lying monkey's face reads upright. The lids close top-down: the upper lid sweeps down over the eye and the lower lid rises slightly. The lid shells are flattened and close with no gap.
- **Gloves:** a darker blue-grey latex (albedo 0.17/0.23/0.27, coat 0.35), so they no longer blow out under the lamp.
- **Stray orb at about 4 s:** the main lamp's spot light was being parented before its matrix updated, so it sat at the world origin on the floor. It now sits inside the dome, which also fixes the OR key light.
  - Dust motes fade out near the lens, so they can't become bokeh balls.
  - The ceiling panels are hidden from glossy rays, and the chrome and floor are rougher.

## Realism pass ("no blocks", client note at 21:00)
- **Operating tables:** the box tables are replaced with a real CC-BY cushioned pedestal table (Hospital Bed by CobbleGames).
- **Table drapes:** the flat slab drapes are now one cloth sheet per table that hangs over the edges, with folds and an uneven hem.
- **Body drapes:** they now have wrinkle displacement.
- **Gowns:** the tube gowns are now pleated (72 segments, 20 rings) with an uneven hem and a smaller flare. They are still procedural; no gown model could be rigged in time.
- **X-ray spine:** the cylinder vertebrae are replaced with a real textured spine model (Human Spine by EdwinCaBe), bent along the back. The x-ray brain was already a real model (3DRT STUDIOS). The spinal cord has a fibrous bump.
- **Gauze collars and head-rest towels:** subdivided and displaced so they read as wrapped fabric.
- **The surgical lamp domes are still procedural.** The only real lamp found is a modern LED ring, wrong for 1970.

## How the one-camera rule is kept
There is one camera on one Catmull-Rom spline.

The move from the operating table to the recovery chair happens inside the x-ray "dive":
- The camera goes top-down onto the neck seam.
- A camera-centred cyan studio void fades in, and the table fades out.
- The monkey is carried rigidly together with the camera to the chair. Camera keys during that window are in the monkey's own space, so nothing in the frame jumps.
- The void then fades out around the chair.

## Known issues
- **Monkey has no rig.** In the chair its arms hang limp between its knees, which is the asset's own sitting pose. The "slump" is a whole-body tilt; only the eyes, lids, ears and breathing animate.
- **Neck seam.** The head and body of the composite are separate meshes. A thin dark seam ring plus stitches hide the join; a faint line is visible in extreme macro.
- **Surgeon, nurse and anaesthetist are IK-posed.**
  - The head grips come from a numeric search: the gloves rest on the fur and the fingers curl.
  - `audit.txt` reports 131 penetrating sampled vertices over 13 audited frames. These are mostly slight glove contact and gowns brushing.
  - The feet step during position changes, but they creep up to about 3 cm at step landings.
- **Chair contact.** The monkey's feet press up to 3 cm into the chair cushion's raised front edge.
- **Stitching close-ups.** These are dominated by the gloved hands. The needle holder is visible but the needle arc is small.
- **Clothing.** The gowns are procedural tubes skinned to the body, worn over a tinted MPFB shirt and trousers. Some sleeves show at the shoulders.
