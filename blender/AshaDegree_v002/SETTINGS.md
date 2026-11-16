# AshaDegree_v002: farm render sheet

| Item | Value |
|---|---|
| File | `AshaDegree_v002_60fps.blend`: compressed, every image and the VO packed, no linked libraries; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles (CPU or GPU), 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2009**, step 1 (33.5 s; built to the client's VO, last word ends at 32.96 s) |
| Cameras | One camera per shot (23 shots), bound to timeline markers: hard cuts, per the batch-2 rule (CONNECT_BRIEF_v2) |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/AshaDegree_v002_####.png` |
| Audio | `AshaDegree_v002_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Test frames before the full job
- **100**: the girl kneeling by her book bag (living room, logo box in the background)
- **500**: the girl on the night highway under the red umbrella (rain, face fill)
- **1200**: the searcher with the clipboard by the shed (daylight)
- **1960**: the framed portrait
