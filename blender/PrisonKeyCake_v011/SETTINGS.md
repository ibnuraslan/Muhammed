# PrisonKeyCake_v011: farm render sheet

These values were read back from `PrisonKeyCake_v011_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `PrisonKeyCake_v011_60fps.blend`, 67 MB, compressed. All images and the voiceover are packed, and there are no linked libraries. It is a plain git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1836**, step 1 (30.6 s, timed to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move (keyed every frame). There are no camera markers. The lens is animated. DOF is on at f/11, focused on `CAM_Film_Aim`. Clip start is 6 mm. |
| Samples | 64, adaptive, noise threshold 0.04 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 6; diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Simplify: texture limit 2048, subdivision 2. |
| Motion blur | Off |
| Colour | Display sRGB. View **Filmic**, look **High Contrast** (as in the approved LegoInNose v013). |
| Output | PNG, written to `//render/PrisonKeyCake_v011_####.png` |
| Audio | `PrisonKeyCake_v011_VO.mp3` is packed and placed as the VO strip at frame 1. The same mp3 sits next to the .blend for encoding. |
| Caches and sims | None: no simulations, particles, Alembic, drivers or linked libraries. The flags use a Wave modifier. Glows, pour, candle burn and visibility switches are keyframed. |
| Animated visibility | `hide_render` keys switch props, costumes and the steps set. The glow and flash fills are a camera-parented sphere seen by camera rays only (frames 329–356 and 1609–1638). Do not use a "render visible only" override. |
| Test render time | See the "Render check" block in README.md. It gives the measured time per frame on this CPU-only cloud machine; the farm will be faster. |

## Test frames to run first on RenderStreet
| Frame | Time | What it shows |
|---|---|---|
| 150 | 2.5 s | The master key pressed into the red wax, with his face |
| 590 | 9.8 s | The molten pour into the sand mould |
| 985 | 16.4 s | His fingers on the key in the lock (the jam) |
| 1240 | 20.7 s | The second cut cake with the key hollow |
| 1800 | 30.0 s | Years later: he waves on the steps, with his allies |
