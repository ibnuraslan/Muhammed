# RingBullet: render settings (farm)

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | 1–1410 (23.5 s) |
| Engine | Cycles, CPU |
| Samples | 48, adaptive threshold 0.05 |
| Denoiser | OpenImageDenoise |
| Bounces | max 8, diffuse 3, glossy 3, transmission 6, volume 0 |
| Caustics | off |
| Motion blur | on, shutter 0.5 |
| Colour | AgX, Medium High Contrast |
| Texture limit | 2048 |
| Output | PNG, 8-bit RGB, `//render/RingBullet_v00N_####.png` |
| Camera | one camera (`Cam`), no markers. Depth of field is on, with focus distance and f-stop keyed per frame. |

Notes:
- The muzzle smoke is a small volume (Principled Volume) that is only visible in frames 30–540. Volume bounces are 0, which keeps it cheap.
- The rain, dust and window drops run on a keyed world-time property (`TimeCtl["wt"]`) through drivers, so the slow-motion section also slows the rain. Drivers use simple expressions only, so they need no Python auto-run.
- Persistent data is on.
