# EarInArm_v015: from-scratch rebuild (client-approved restage + rib-carry arm fix)

- `EarInArm_v015_60fps.blend` is the self-contained scene: textures and the VO are packed, about 39 MB. It is a render-ready package; the render settings are in `SETTINGS.md`.
- `EarInArm_v015_VO.mp3` and `beats.json` hold the client's VO and the beat timing taken from v014 (frames 1–1572).
- `review/preview.mp4` is a 270×480 preview of this exact package: every 5th frame, real time, with the VO.
- `scripts/` rebuilds the scene:
  - `01_build.py`: set, characters and props (assets downloaded from Sketchfab, see CREDITS)
  - `02_animate.py`: animation and camera
  - `arm_torso_check.py`: per-frame test of the surgeon's arms against his torso

## Status
- The client approved the restage version.
- Fix applied: in the rib-carry, the surgeon turns to the dish and his left elbow stays forward, so his arm passes in front of his torso. On all 1572 frames the arm-vs-torso test shows at most 3 armpit-crease vertices at 10 mm, the same as in the rest pose.
- Internal self-QC (harsh reviewer) still listed open items:
  - tool jaws in the hair at the graft (about 18–23.5 s)
  - stretches with no face, including the surgeon's head out of frame in close shots
  - hands at the frame edge
  - a large glove near the lens at 3.75–3.9 s

  These were pushed at the client's request. Watch the preview before paying for a render.
