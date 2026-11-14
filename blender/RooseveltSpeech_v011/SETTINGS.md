# RooseveltSpeech_v011: farm settings

| Setting | Value |
|---|---|
| File | `RooseveltSpeech_v011_60fps.blend` (packed, compressed) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps |
| Frames | **1–1307** (21.8 s at 60 fps; synced to the voiceover, `RooseveltSpeech_v011_VO.mp3` packed as a sound strip from frame 1) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | off (animated look) |
| Colour | AgX, look "Punchy", exposure +0.45 |
| Camera | one camera, `Cam`, with no markers or switching |
| Output | `//render/RooseveltSpeech_v011_####.png` |

Notes for the farm:
- Particle hair (the moustache) and volumetric gun smoke are in the scene. Both render in Cycles with no baking.
- Breath vapour (small volumes) renders in Cycles with no baking.
- Set visibility is keyed with `hide_render`:
