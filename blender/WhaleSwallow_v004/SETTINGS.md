# WhaleSwallow_v004: farm render sheet

| Item | Value |
|---|---|
| File | `WhaleSwallow_v004_60fps.blend`: compressed, every image and the VO packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU, 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1715**, step 1 (28.6 s; built to the voiceover, which ends at 28.45 s) |
| Camera | One camera `CAM`; the hard cuts are baked into its keys (constant interpolation); no camera markers |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/WhaleSwallow_####.png` |
| Audio | `WhaleSwallow_v004_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

Frames after 1715 hold parked, unused animation (dropped shots); they are outside the render range.

## Test frames before the full job
- **150**: the jaws closing over the diver at the surface
- **420**: the humpback head-on, jaws open, the diver inside
- **700**: the diver inside the mouth, hand on the baleen
- **1000**: the hospital bed, shirt and blanket
- **1690**: the diver treading water at the end
