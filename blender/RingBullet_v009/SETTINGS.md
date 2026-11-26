# RingBullet v009: render settings (farm)

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | **1–1395** (23.25 s; built to the VO timing from the start; `RingBullet_v009_VO.mp3` packed as a sound strip from frame 1) |
| Engine | Cycles, CPU |
| Samples | 64, adaptive threshold 0.05, OpenImageDenoise |
| Bounces | max 6, diffuse 3, glossy 3, transmission 6, transparent 16; caustics off |
| Motion blur | off |
| Colour | Filmic, High Contrast |
| Texture limit | 2048 |
| Output | PNG, 8-bit RGB, `//render/RingBullet_v009_####.png` |
| Camera | one camera (`CAM_Film`), no markers, no cuts, depth of field off |

Logo: the DA KRAS FILMS sign above the back shelves reads in full at f1–40 (partly, top right) and **f1146–1260** (about 1.9 s, unobstructed), and stays in frame to the end.
No drivers and no Python are needed to render. Persistent data is on.
