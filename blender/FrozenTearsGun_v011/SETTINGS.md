# FrozenTearsGun_v011: farm render sheet

These values were read back from `FrozenTearsGun_v011_60fps.blend` opened with `--factory-startup` in Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `FrozenTearsGun_v011_60fps.blend`: 70 MB, compressed. Everything is packed (textures at 1K, 2K for her face skin). There are no linked libraries, drivers or scripts. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; a GPU is fine. |
| Resolution | 1080 x 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1-1655**, step 1 (27.6 s, synced to the voiceover) |
| Camera | `CAM_Film`, one continuous move with no cuts or markers. Lens, focus and f-stop are animated (f/8-f/11). |
| Samples | 64 with adaptive sampling, noise threshold 0.04 |
| Denoising | OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics are off. Persistent data is on. |
| Simplify | Texture limit 2048, subdivision 2 |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy", exposure 0 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/FrozenTearsGun_v011_####.png` |
| Audio | `FrozenTearsGun_v011_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Caches / sims | None. Gas, frost and impact puffs are keyframed meshes, not volumes. |

## Measured cost (4-core cloud CPU, no GPU, 16 samples, full resolution)
- Frames 1, 828 and 1655 took 49-57 s each. At the farm setting of 64 adaptive samples, expect roughly 2-3x that on CPU. A farm GPU is much faster.

## Test frames before approving the whole job
- **300**: valve close-up (glass chamber, hand on the red wheel)
- **470**: CO2 gas in the chamber (translucent puffs)
- **1400**: the logo bench shot
- **1625**: the ice impact on the mentor's jacket
