# ToddlerWell_v008: farm render sheet

| Item | Value |
|---|---|
| File | `ToddlerWell_v008_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1728**, step 1 (28.8 s; synced to the voiceover) |
| Camera | One camera. Hard cuts are baked into its keys; there are no markers. |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/ToddlerWell_v008_####.png` |
| Audio | `ToddlerWell_v008_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Effects | Dust is cheap surface sprites, not volumes. Measured on 4 CPU threads, a preview frame (4 samples) takes about 9 s. |

## Test frames before the full job
- **207**: the toddler at the bottom of the shaft
- **1212**: the teen lowered with the flashlight
- **1321**: the grab in the shaft
- **1724**: the ending with the crowd
