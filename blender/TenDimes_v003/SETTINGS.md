# TenDimes v002c: render settings

| | |
|---|---|
| File | `TenDimes_v003_60fps.blend` (all textures and the VO packed; compressed, ~50 MB) |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps |
| **Frame range** | **1 – 1868** (31.1 s; VO words 0.00–30.62 s, end 0.5 s after the last word) |
| Engine | Cycles, CPU/GPU, 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Colour | AgX, look "Punchy" |
| Motion blur | off |
| Output | PNG sequence to `//render/TenDimes_v003_` |
| Audio | VO strip on the sequencer from frame 1 (packed) |

**Cameras:** one camera per shot, switched by timeline markers (hard cuts, as the batch-2 brief asks). The packager's
"ONE camera, no camera markers" check dates from the old one-continuous-camera rule. Blender switches cameras by
marker during command-line and farm renders.
