# EarInArm_v016: client-approved v015 + DA KRAS FILMS logo + fast-render settings

- `EarInArm_v016_60fps.blend` is the self-contained scene: textures and the VO are packed, about 37 MB. It is a render-ready package; the render settings are in `SETTINGS.md`.
- `EarInArm_v016_VO.mp3` and `beats.json` hold the client's VO and the beat timing taken from v014 (frames 1–1572).
- `review/preview.mp4` is a 270×480 preview of this exact package: every 5th frame, real time, with the VO.
- `scripts/03_polish_logo_fastrender.py` + `scripts/polish_cfg.json` made v016 from v015 (logo, render settings, purge, pack).
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

## v016 changes (nothing else changed)
v016 is v015, which the client approved, plus two additions. The animation, camera, characters, lights and colour are untouched.
1. **Logo.** The DA KRAS FILMS logo is on the framed wall poster (frames 1–240, 1086–1196, 1461–1572) and printed on the surgeon's left chest (frames 1–60, 266–306, 446–461, 1491–1572). Both were checked in the moving preview.
2. **Fast-render settings.** Max bounces went from 8 to 6 and transmission bounces from 8 to 6. OIDN now uses the albedo and normal passes, and Persistent Data and Simplify (2048 px texture limit) are on. The purge removed one hidden, never-rendered object (`Surgeon.short01`, hair) and its unused data.

Before/after check at full resolution: frame 786 has no logo in view and differs by RMSE 0.0007, which is noise. Frames 1 and 1572 differ only where the logos are.

## Render check: PASS
Run on the exact packed `EarInArm_v016_60fps.blend` with `blender --factory-startup -b` (Blender 5.2.2):
- Opens with no errors or warnings. The only console line is the container's "CUEW: no CUDA library" note: this container has no GPU, and the note says nothing about the file.
- 0 linked libraries, 0 unpacked images, fonts or sounds, no auto-run scripts, no invalid drivers.
- Camera `CAM_Film`. 1080×1920 at 100 %, 60 fps, frames 1–1572. PNG to `//render/EarInArm_v016_####.png`. The VO sound strip starts at frame 1 (frames 1–1554).
- Cycles: 48 samples, adaptive 0.05, OIDN (albedo + normal), bounces 6/3/3/6, transparent 16, caustics off, Persistent Data on, Simplify on (texture limit 2048), 0 orphan data blocks.
- Test frames 1, 786 and 1572 rendered at full resolution. None is black, empty or pink. Time per frame: 133 s, 265 s and 137 s on 4 CPU cores.
- `review/preview.mp4` (270×480, every 5th frame, with the VO) was watched start to finish, all 7 contact pages.
