# WaterTubes_v006: farm render sheet

| Item | Value |
|---|---|
| File | `WaterTubes_v006_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1769**, step 1 (29.5 s; synced to the voiceover) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | Off (the animated-CG look) |
| Colour | AgX, look "Punchy" |
| Camera | One camera (`Camera`); no markers and no cuts |
| Output | PNG sequence, written to `//render/WaterTubes_v006_####.png` |
| Audio | `WaterTubes_v006_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Effects | The tube filling, flood surface, rain and spray are geometry nodes driven by keyed values. There are no simulation caches, and every frame renders independently. |

## Test frames before the full job
- **420**: the flood arrives in the street
- **927**: the tube cutaway
- **1100**: the water hits the tube ring, with spray
- **1700**: the closing aerial of the dry house in the flood
