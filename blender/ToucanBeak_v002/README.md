# ToucanBeak v002: farm package (Connect28)

- **File:** `ToucanBeak_v002_60fps.blend`, packed, 94.7 MB, normal git file with no LFS. It opens in factory Blender 5.2.2 with 0 unpacked images and no linked libraries.
- **Format:** 1080×1920, 60 fps, frames 1–2250 (37.5 s), Cycles CPU at 48 samples / 0.05 / OIDN, AgX Punchy. One camera, no cuts, no markers. Output goes to `//render/ToucanBeak_v002_####.png`.
- **Look:** animated CG per `blender/STYLE_ANIMATED.md` (`pipeline/anim_look.py` plus `ToucanBeak_v001/scripts/05_look.py`).
- **Voiceover:** none yet, because we used our own script. `beats.json` gives each beat's start frame and first words. Retime with `pipeline/retime_to_vo.py`.
- **Check still:** `package_check_lowres.jpg`, rendered from this exact file at 270×480 and 8 samples.
- **Review sheets:** `ToucanBeak_v001/stills/final_1ps.jpg`, `stills/hands_closeups_D.jpg`, and `stills/polish_0p2s_*.jpg` (from C).
- **Sources and rebuild:** `ToucanBeak_v001/` (`scripts/build_all.sh full`, then `scripts/06_package.py`). See `ToucanBeak_v001/README.md` for the beat-by-beat staging.

## Audit (`audit_D.txt`: every 2 frames, 1125 samples)
Every check is 0:
- toe hover/sink
- hand into bird
- hand into held prosthetic
- hand vs hand
- hand vs own torso/clothes/head
- hand vs other character
- camera inside a mesh
- fig floating off the platform

No head-worn items are used.

## Hands
- Gloves are a nitrile material on the real MPFB hand and wrist faces, with a cuff. There are no separate glove meshes.
- The wrist copy-rotation influence is 0.35. At full influence it twisted the wrist into a balloon shape.
- Limit Rotation constraints are on every finger, thumb and wrist.
- Grips are solved from each tool's handle, with settle loops for the bird and the held prosthetic.

## Known issues
1. **Clinic → void entry and exit:** the camera passes through the monitor screen. On the way out (about 25.0 s) there are about 6 frames of plain sky gradient while it whips from the printer back to the screen.
2. **Hero toucan body:** Lary's CC-BY toucan, rebuilt as a closed skin with procedural keel-billed plumage and a feather-fibre layer. The beak is the real MooreLab specimen scan. Up close the body is smoother than a real bird.
3. **Background trees:** procedural bark trunks (displaced cylinders with Poly Haven bark), which read a little stake-like from low angles.
4. **Grips:** solved geometrically, then checked in close-ups. The prosthetic is held with the fingers laid along the culmen rather than a full wrap.
5. **Ghost bird (beat 7):** an explainer device: a translucent blue copy on the sky gradient.
6. **Framed photos:** they show a crop of the forest HDRI. They contain no text.
