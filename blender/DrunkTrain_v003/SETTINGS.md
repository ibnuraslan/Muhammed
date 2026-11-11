# DrunkTrain_v003: farm render sheet

These values were read back from `DrunkTrain_v003_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `DrunkTrain_v003_60fps.blend`: 73 MB, compressed, committed as a normal git file (no LFS). All images are packed; textures are at 1K and the HDRI at 2K. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2070**, step 1 (34.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. The lens is animated, sensor fit is Auto, and DOF is on at f/5.6 (animated look: backgrounds stay readable), focused on `CAM_Film_Aim`. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics off. Persistent data on. |
| Motion blur | **Off** (client look, Nov 11 22:45: clean animated CG) |
| Colour | Display sRGB, view AgX, look **"AgX - Punchy"** (the animated look). The scene exposure, sun colour and energy, and world strength are keyframed (under-train lift, warm flash-back, end lift), so do not override them. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/DrunkTrain_v003_####.png` |
| Audio | None yet. The VO will be retimed in with `pipeline/retime_to_vo.py` using `beats.json`. |
| Caches / sims | None: no simulations, particles, Alembic or linked libraries. Geometry Nodes scatter (ballast stones, weeds, grass) is evaluated at render time. Muscle ripple and laundry wind are Wave modifiers. |
| Add-ons | None needed. MPFB2 only built the file. |

## Volumes
Dust uses Principled Volume (impact dust, horn exhaust, the stop dust wave). It is visible in frames 541–700, 409–500 and 900–1000. If these frames are slow on the farm, they are the reason.

## Suggested test frames
- **560**: the impact, with volume dust and debris
- **760**: under the train between the rails, with spark light (dark shot, exposure lifted)
- **1500**: the x-ray studio with the translucent skin and muscles
- **1700**: the slow-motion replay, with the ghost train and force arrows
- **2050**: the final close-up of his face

## Measured cost
The figure below was measured on v002, which had motion blur and denser volumes; v003 should be a little cheaper.
One full frame (frame 560, the impact with volume dust; 1080×1920, 48 samples, motion blur) took **325 s** wall-clock on this 4-core cloud CPU. About 25 s of that is loading the file and textures. That works out to roughly 170 h for 2070 frames locally, but it is a heavy frame and most frames have no volumes. On farm GPU nodes it should be far faster. Run the test frames below before approving the whole job.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are animated.
