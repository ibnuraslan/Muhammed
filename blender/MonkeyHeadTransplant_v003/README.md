# MonkeyHeadTransplant_v003: farm package

This is the 29.5 s film (1770 frames at 60 fps, 1080×1920), built to our 80-word script at the brief's target beat times. No render has been submitted.

- `MonkeyHeadTransplant_v003_60fps.blend`: the self-contained scene, with all textures packed. It opens in factory Blender 5.2.2.
- `beats.json`: the start frame and first words of each beat, ready for `pipeline/retime_to_vo.py` when the VO arrives. There is no VO mp3 yet.
- `SETTINGS.md`: render settings and test frames. `CREDITS.md`: the CC-BY block for the video description.
- `package_check_f*_lowres.jpg` (frames 330, 862, 1110): 20 %, 4-sample frames from the packed file in factory Blender. They show the package works; they are not a quality reference.

**Source:** `../MonkeyHeadTransplant_v001/scripts`. Build order:
1. `01_build_monkey.py`
2. `01b_build_people.py`
3. `02_build_scene.py`
4. `03_animate.py`
5. `package_for_farm.py`

**Review:** `../MonkeyHeadTransplant_v001/review/` holds the 0.2 s polish sheets, the 1 s blocking sheet and `audit.txt`.

## Changes from v002 (director's C notes)
- **Blinks:** the camera now rolls during the face push-in (11–16 s), so the lying monkey's face reads upright. The lids close top-down: the upper lid sweeps down over the eye and the lower lid rises slightly. The lid shells are flattened and close with no gap.
- **Gloves:** a darker blue-grey latex (albedo 0.17/0.23/0.27, coat 0.35), so they no longer blow out under the lamp.
- **Stray orb at about 4 s:** the main lamp's spot light was being parented before its matrix updated, so it sat at the world origin on the floor. It now sits inside the dome, which also fixes the OR key light.
  - Dust motes fade out near the lens, so they can't become bokeh balls.
  - The ceiling panels are hidden from glossy rays, and the chrome and floor are rougher.

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
  - `audit.txt` reports 85 penetrating sampled vertices over 13 audited frames. These are mostly slight glove contact and gowns brushing.
  - The feet step during position changes, but they creep up to about 3 cm at step landings.
- **Chair contact.** The monkey's feet press up to 3 cm into the chair cushion's raised front edge.
- **Stitching close-ups.** These are dominated by the gloved hands. The needle holder is visible but the needle arc is small.
- **Clothing.** The gowns are procedural tubes skinned to the body, worn over a tinted MPFB shirt and trousers. Some sleeves show at the shoulders.
