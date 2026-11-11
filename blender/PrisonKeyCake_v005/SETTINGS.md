# PrisonKeyCake_v005: farm render sheet

These values were read back from `PrisonKeyCake_v005_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `PrisonKeyCake_v005_60fps.blend`: 67 MB, compressed, committed as a normal git file (no LFS). All images are packed as JPEG: 1K textures, with the prisoner's skin at 2K. The HDRIs are packed at 1K. MPFB body shape keys are baked. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1890**, step 1 (31.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move (Track-To an empty, `CAM_Film_Aim`). There are no camera cuts or camera markers. The lens and f-stop are animated. Sensor fit is Auto (36 mm). DOF is on, focused on the aim empty. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated look). |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy". The scene exposure is keyframed (day 0.55, night 0.9, final day 0.25), so do not override it. The world shows a sky gradient to camera rays only; lighting comes from the HDRIs. |
| Output | PNG, RGB, 8-bit, written to `//render/PrisonKeyCake_v005_####.png` |
| Audio | None yet. When the VO arrives, the director retimes with `pipeline/retime_to_vo.py` using `beats.json`. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Sparks, pour, smoke density, flags (Wave modifier) and birds are keyframed or time-based. |
| Volumes | There are two thin volumes. Foundry smoke (`Smoke`) is visible for frames 515–830. Cell dust (`CellDust`) is visible for frames 1–1459 and does not cast shadows. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Suggested test frames
Run a few test frames on RenderStreet before you approve the whole job:
- **200**: candle-lit cell, hands pressing the key into the wax
- **560**: foundry pour, with sparks, smoke volume and the glow light
- **1240**: night cell, with moonlight and the candle burned down
- **1530**: corridor gates and lanterns
- **1860**: day reveal, with crowd, flags and pigeons

Night cell frames (870–1460) are the noisiest. If you see noise there, raise the samples to 96 for that range only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are animated (the day/night mix is the `DayNight` node in the world).
