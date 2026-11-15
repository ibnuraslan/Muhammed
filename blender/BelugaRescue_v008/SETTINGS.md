# BelugaRescue_v008: farm render sheet

| Item | Value |
|---|---|
| File | `BelugaRescue_v008_60fps.blend`: compressed, every image packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame range | **1–1736**, step 1 (28.9 s; synced to the voiceover) |
| Frame rate | 60 fps |
| Camera | One camera; clean cuts are baked into its keys; no markers |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/BelugaRescue_v008_####.png` |
| Audio | `BelugaRescue_v008_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Effects | Bubbles and water ripples are geometry nodes. Their clocks are remapped to the retimed picture (`pipeline/fix_scene_time.py`), so no caches are needed. |

## Test frames before the full job
- **300**: the cramp at the pool floor
- **825**: the beluga close to her
- **1100**: the snout at her ankle
- **1730**: the ending at the pool edge
