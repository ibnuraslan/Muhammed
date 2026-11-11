# FrozenTearsGun_v004: farm render sheet

These values were read back from `FrozenTearsGun_v004_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `FrozenTearsGun_v004_60fps.blend`: 69 MB, compressed, a normal git file (no LFS). Every image is packed: 1K textures, 2K for her face skin, a 1K HDRI. The check found no unpacked images and no linked libraries. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2100**, step 1 (35.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. The lens, focus distance and f-stop are animated. Sensor fit is Auto (36 mm). DOF is on, with the f-stop never below 5.6 (deeper on the macro beats). The clip start is 4 mm, for the macro shots. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | **Off** (animated-CG look) |
| Colour | View AgX, look "AgX - Punchy". **Scene exposure is keyframed**: two short +1.8 flashes, at 18.8–19.1 s and 28.2–28.5 s (6-frame peaks), and 0 everywhere else. Do not override it. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/FrozenTearsGun_v004_####.png` |
| Audio | None. No voiceover had been supplied when this was packaged. `beats.json` (in `../FrozenTearsGun_v001/`) holds each beat's start frame for `pipeline/retime_to_vo.py` once the VO arrives. |
| Caches / sims | None: no simulations, particles, Alembic or drivers. Gas, frost and impact puffs are small keyframed volume spheres. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Measured cost (4-core cloud CPU, no GPU)
- **Frame 560** (CO2 gas inside the glass chamber, the worst case): **936 s** at full resolution.
- **Other frames**, timed at 30 % resolution and scaled up to full size: about 290 s for the office (frame 1420) and about 390 s for the glass macro (frame 300).
- **Whole film:** roughly 200–250 CPU hours. A farm GPU node should be many times faster.
- The volumes (gas and frost puffs) are hidden outside the frames where they are used, because they cost render time even at zero density.

## Test frames before approving the whole job
- **300** (5.0 s): glass chamber macro on the cyan explainer backdrop, with refraction-heavy glass and water
- **560** (9.3 s): CO2 gas volume inside the glass. This is the slowest frame type. If it is noisy, raise the samples to 96 for frames 450–760 only.
- **930** (15.5 s): muzzle frost puff with the pellets and motion blur
- **1420** (23.7 s): office, with her hands over her face
- **1990** (33.2 s): impact puff on the mentor's shirt

## Do not
- Do not render other cameras. `CAM_Film` is the only camera.
- Do not change exposure or the world settings; both are animated.
