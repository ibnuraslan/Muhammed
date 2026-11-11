# BellyFat_v001: working folder

The source for the BellyFat film. The farm package is in `../BellyFat_v002/`.

## Build (about 2 min on 4 CPU cores)
`./build.sh` runs the three scripts in order:
1. `scripts/01_build_woman.py` → `humans.blend`: the woman and two background shoppers. They are MPFB2 with MakeHuman CC0 assets. The tee texture is `assets/tex/woman_tee_clean_diffuse.png`, which is the MPFB tee with its chest graphic painted out.
2. `scripts/02_build_scene.py` → `scene.blend`: everything else.
   - The procedural supermarket. Products have per-face UV labels with no text.
   - The cart, basket and bullet.
   - The macro cross-section, in macro units under `MacroRoot`: fabric, skin, fat lobules, fascia, muscle fibres, peritoneum, intestines, the studio dome and studio lights.
3. `scripts/03_animate.py` → `anim.blend`:
   - The woman's IK acting and the shoppers' walks.
   - `MacroRoot` is parented to her `spine03` bone at the impact point, at scale 0.025.
   - The bullet depth curve and the tissue deformation (dimple shape keys, lobule push/squash/ripple, energy rings, fibre parting, droplets, intestine noise).
   - The visibility swap, and the baked camera.
   - It writes `beats.json` and `camlog.json`.

## Review tools
- `../pipeline/stills.py`, `../pipeline/contact_sheet.py`: the review sheets.
- `scripts/frames.py`: renders chosen frames.
- `scripts/debug_pose.py`: a side view with the store forced visible.
- `scripts/audit.py`: the contact, penetration and camera audit.
- `scripts/camera_chart.py`: camera distance and speed.

## One camera, two scales
`CAM_Film` is the only camera, on one baked path.
- The camera is solved in the `MacroRoot` frame: target = smoothed bullet-tip reference + Catmull-Rom offsets; position = spherical (az, el, log distance) around the target.
- The opening is a dolly on her, cross-blended into the bullet-locked chase between 0.3 and 0.75 s.
- The store (REAL objects) and the tissue (MACRO collection) swap render visibility at frames 154 and 1225. At both frames the frame is filled with the shirt fabric, about 1.8 cm from the lens, and the macro fabric patch lies on the real shirt.
