# AIAsleep_v007: farm render sheet

| Item | Value |
|---|---|
| File | `AIAsleep_v007_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU. 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2046**, step 1 (34.1 s; synced to the voiceover) |
| Camera | One camera (`FilmCam`), no markers. Clean cuts are baked into the keys. DOF is on (f/5.6 or more; f/18 on the eye macros). |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "AgX - Punchy" |
| Compositing | On (CPU or GPU). Leave it as saved. |
| Output | PNG sequence, written to `//render/AIAsleep_v007_####.png` |
| Audio | `AIAsleep_v007_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Test frames before the full job
- **193**: the dashboard flashes red at his face
- **948**: the alarm goes off again
- **1490**: the eye macro with the red ring
- **1600**: the eyelid cross-section
- **2040**: the ending on his face
