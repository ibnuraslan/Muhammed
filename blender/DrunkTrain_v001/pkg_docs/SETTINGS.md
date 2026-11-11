# DrunkTrain_v002: farm render sheet

These values were read back from `DrunkTrain_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `DrunkTrain_v002_60fps.blend`: __SIZE__ MB, compressed, committed as a normal git file (no LFS). All images are packed; textures are at 1K and the HDRI at 2K. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2070**, step 1 (34.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. The lens is animated, sensor fit is Auto, and DOF is on at f/2.8 with the focus on `CAM_Film_Aim`. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 (180° at 60 fps) |
| Colour | Display sRGB, view AgX, look "AgX - Medium High Contrast". The scene exposure, sun colour and energy, and world strength are keyframed (under-train lift, warm flash-back, end lift), so do not override them. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/DrunkTrain_v002_####.png` |
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
__COST__

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are animated.
