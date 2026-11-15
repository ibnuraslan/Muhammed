# StanleyCup_v009: farm render sheet

| Item | Value |
|---|---|
| File | `StanleyCup_v009_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1386**, step 1 (23.1 s; synced to the voiceover) |
| Camera | One camera, `CAM_Film`. Hard cuts are baked into its keys and there are no camera markers. DOF on, mostly f/8–f/11. |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy". Exposure is keyed (street vs. room), so do not override it. |
| Output | PNG sequence, written to `//render/StanleyCup_v009_####.png` |
| Audio | `StanleyCup_v009_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Caches / sims | None. The lawn grass is a hair particle system; booleans and the Wave ripple evaluate per frame. |

## Test frames before the full job
- **103**: the bullet hits the siding
- **553**: the tumbler, with her face
- **966**: the impact sparks on the cup (brightest frame)
- **1380**: the ending two-shot
