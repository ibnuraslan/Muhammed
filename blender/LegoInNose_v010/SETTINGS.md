# LegoInNose_v010: farm render sheet

These values were read back from `LegoInNose_v010_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `LegoInNose_v010_60fps.blend`, 56 MB, compressed. All images are packed: no unpacked files, no linked libraries. It's a normal git file (no LFS). Textures are 1K, and the hero male skin is 2K. Images are JPEG q90, except PNG where alpha matters (hair, brows, lashes, leaves). The HDRIs are 1K. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2036**, step 1 (33.9 s at 60 fps; synced to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move. No camera cuts or camera markers. The lens and f-stop are animated. Sensor fit is Auto (36 mm). DOF is on, focusing on `CAM_Film_Aim`. Clip start is 1 mm, for the nostril dives. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated look, per `STYLE_ANIMATED.md`) |
| Colour | Display sRGB. View AgX, look "AgX - Punchy". The scene exposure is keyframed (studio, night, time-lapse flashes), so do not override it. |
| Output | PNG, RGB, 8-bit, written to `//render/LegoInNose_v010_####.png` |
| Audio | None yet. The voiceover isn't recorded. Once it is, retime with `retime_to_vo.py`, which adds the VO strip at frame 1, and add the mp3 when encoding. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Water streaks are keyframed meshes, and the steam is a volume material. |
| Add-ons | None needed. MPFB2 only built the file. |
| Animated visibility | `hide_render` and `visible_camera` keys hide the tunnels, the character swaps and the wall pass. Do not use "render visible only" overrides. |

## Cost
No full-resolution frame was rendered here (the studio rule for tonight: review stills only).
- The goat film measured about 125 s per full frame on this 4-core CPU, and this scene is similar in weight.
- The steam volume (31–38.5 s) and the frosted and clear glass will be the slowest frames.

## Test frames to run first on RenderStreet
| Frame | Time | What it shows |
|---|---|---|
| **190** | 3.2 s | The nose porthole cutaway, with the brick inside |
| **517** | 8.6 s | The click flash on the floating dream bricks |
| **800** | 13.3 s | The cross-section studio: bricks wedging |
| **1250** | 20.8 s | The glowing hidden brick (emission + point light) and the realistic tissue shaders (SSS, coat) |
| **730** | 12.2 s | Inside the nostril tunnel: nose hairs, wet veined mucosa |
| **1420** | 23.7 s | Time-lapse: the teen with the gamepad, a snow season through the window |
| **1800** | 30.0 s | The bedroom at night, lit by moonlight and the lamp. If it's noisy, raise the samples to 96 for frames 1724–1868. |
| **2120** | 35.3 s | The shower: steam volume, glass, water streaks, and the brick in flight |

## Do not
- Do not render other cameras. `CAM_Film` is the only one.
- Do not change exposure or the world settings. Both are animated: seasons mix, time-lapse sun, night.
