# SETTINGS: SwedishCoffee

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 (100 %) |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | 1 – 2670 (44.5 s) |
| Engine | Cycles, CPU |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Bounces | max 6, volume bounces 0, volume step rate 4 |
| Motion blur | on, shutter 0.35 |
| Colour | AgX, look "AgX - Medium High Contrast" |
| Output | PNG frames to `//render/SwedishCoffee_v002_####.png` |
| Camera | exactly one camera ("Camera"); no camera-switch markers. The timeline markers b01–b13 are beat markers only. |
| Data | everything packed (images, HDRI); no linked libraries. Opens in factory Blender 5.2.2 (`--factory-startup`). |

Volumes in the film: coffee steam, the skull formed in the steam (b3), the pistol smoke puff (b10), cup and stall steam. They are small, and volume bounces are 0 to keep farm time down.

No particle systems or simulation caches: the coffee beans (b4, released frames 592–712) and the falling snow (b9) are deterministic geometry-node instancers driven by the scene frame, so any frame renders identically in any order on the farm.
