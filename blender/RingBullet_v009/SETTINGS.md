# RingBullet v009: render settings (farm)

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | **1–1395** (23.25 s; built to the VO timing from the start; `RingBullet_v009_VO.mp3` packed as a sound strip from frame 1) |
| Engine | Cycles, CPU |
| Samples | 20, adaptive threshold 0.08, OpenImageDenoise |
| Bounces | max 4, diffuse 2, glossy 2, transmission 4, transparent 10; caustics off; simplify subdivision 1 |
| Motion blur | off |
| Colour | Filmic, High Contrast |
| Texture limit | 2048 |
| Output | PNG, 8-bit RGB, `//render/RingBullet_v009_####.png` |
| Camera | one camera (`CAM_Film`), no markers, no cuts, depth of field off |

Logo: the matte DA KRAS FILMS sign above the back shelves reads in full and unobstructed at **f1146–1395** (about 4 s). It is partly cropped at f1–45.
Measured render time (exact package, factory startup, 4-core CPU): f20 98 s, f600 109 s, f1300 101 s.
No drivers and no Python are needed to render. Persistent data is on.
