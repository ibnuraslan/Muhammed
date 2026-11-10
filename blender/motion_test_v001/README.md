# MotionTest_v001: 10 s walk, pick up, drink (1080×1920, 60 fps)

| File | What it is |
|---|---|
| `MotionTest_v001_60fps.blend` | Packed, editable farm file (Blender 5.2.2). Render frames 1–600 from `CAM_Main`. |
| `preview/MotionTest_v001_preview_360x640_60fps.mp4` | Continuous low-sample Cycles preview of all 600 frames. Motion review only, not a lighting or quality reference. |
| `SETTINGS.md` | Render settings sheet (read back from the file). |
| `CREDITS.md` | Asset sources and licences (all CC0). |
| `scripts/` | Scripts that rebuild the file from scratch. |

## Rig controls (armature `Farmer`, bone collection "Controls")
- `IK_foot.L/R`: foot IK with heel/ball roll baked into the keys. `Pole_knee.L/R` sets knee direction.
- `IK_hand.L/R`: hand IK; the wrist copies the control's rotation. `Pole_elbow.L/R` sets elbow direction.
- `root`: pelvis / centre of mass. Spine, neck, head, jaw, clavicles and fingers are keyed FK (quaternions).
- `IK_hand.R` has a Child Of constraint `Grip_Bottle` (influence 0 → 1 at frame 272). From frame 272 the **bottle object is the animation control**: move or rotate `Bottle` and the hand follows.
- The bottle drink poses were placed relative to the head so the rim lands at the lips. If you change head keys during 405–490, re-check that contact.

## Rebuild
1. Install the MPFB 2.0.18 extension and put the MakeHuman system assets (CC0) in MPFB's user data folder.
2. Download the Poly Haven assets listed in `CREDITS.md` (2K) into `<assets>/hdri`, `grass_ground`, `wooden_crate_01` and `grass_medium_01`.
3. Run:
```bash
blender -b --python scripts/01_build_character.py -- character.blend
```
```bash
blender -b character.blend --python scripts/02_build_scene.py -- <assets> scene.blend
```
```bash
blender -b scene.blend --python scripts/03_animate.py -- anim.blend
```
```bash
blender -b anim.blend --python scripts/05_package.py -- MotionTest_v001_60fps.blend
```
`03_animate.py` also runs `03b_arms_bottle.py` (crate/bottle placement, arms, grasp solve, fingers) and `04_camera.py`.
`check_motion.py` prints IK reach errors and records point trajectories for speed and acceleration analysis.
