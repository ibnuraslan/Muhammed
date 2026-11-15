# TitanicIceberg_v014: farm render sheet

| Item | Value |
|---|---|
| File | `TitanicIceberg_v014_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1464**, step 1 (24.4 s; synced to the voiceover) |
| Camera | One camera object with clean cuts baked into its keys; no markers. DOF is mostly at f/8–f/16. |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/TitanicIceberg_v014_####.png` |
| Audio | `TitanicIceberg_v014_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Effects | The Ocean modifier is driven by the frame number. The scrape sparks are a particle system (frames 727–807); no cache is needed. |

## Test frames before the full job
- **278**: the red smear on the berg
- **760**: the night scrape, with the sparks
- **813**: the darkroom under the safelight
- **1011**: the expert with the print
- **1460**: the ending berg
