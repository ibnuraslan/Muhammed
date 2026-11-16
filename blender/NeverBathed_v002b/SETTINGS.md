# NeverBathed_v002b: render settings

| Setting | Value |
|---|---|
| File | `NeverBathed_v002b_60fps.blend` (all textures and the VO packed) |
| Resolution | 1080 × 1920 (vertical), 100 % |
| Frame rate | 60 fps |
| Frame range | **1 – 1728** (28.8 s; VO speech 0.00–28.28 s, end = last word + 0.5 s) |
| Engine | Cycles, CPU or GPU, 48 samples, adaptive threshold 0.05, OIDN denoise |
| Colour | AgX, look "AgX - Punchy", exposure −0.9 |
| Motion blur | off |
| Cameras | one camera per shot, bound by timeline markers (hard cuts, batch-2 rule); 20 shots |
| Output | PNG sequence to `//render/NeverBathed_v002b_` (the VO is in the sequencer at frame 1 for an MP4 mux) |
