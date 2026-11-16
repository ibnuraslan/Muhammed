# Render settings: NatashaRyan_v002b

| Setting | Value |
|---|---|
| File | `NatashaRyan_v002b_60fps.blend` (93 MB, all textures and the VO packed) |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps |
| **Frame range** | **1 – 2136** (VO 0–35.08 s, last word + 0.5 s) |
| Engine | Cycles, 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Colour | AgX, look "AgX - Punchy" |
| Motion blur | off |
| Cameras | one camera per shot, switched by timeline markers (hard cuts, 21 shots) |
| Output | `//render/NatashaRyan_v002b_` PNG sequence |
| Audio | VO strip on channel 1 from frame 1 (`NatashaRyan_v002b_VO.mp3`) |

The farm-check script flags "must be ONE camera, no camera markers". That rule predates batch 2: batch-2 films use hard cuts, one camera per shot, bound to markers, which RenderStreet renders natively.
