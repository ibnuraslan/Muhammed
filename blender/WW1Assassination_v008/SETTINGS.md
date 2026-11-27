# WW1Assassination_v008: farm render sheet

| Item | Value |
|---|---|
| File | `WW1Assassination_v008_60fps.blend`: 90 MB, compressed. Every image is packed (including the logo). Normal git file, no LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1826** (30.4 s), synced to `WW1Assassination_v008_VO.mp3` (same VO and timing as v007). |
| Cameras | **21 shot cameras with hard cuts**, switched by timeline markers (`S01_…` to `S20_…`, each marker bound to its `CAM_…` camera). Render the animation normally and the markers switch the cameras. DOF is off. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy". Exposure is a constant −0.35 (the v007 rewind tint and exposure blips are gone). |
| Compositing | Off |
| Output | PNG, RGB, 8-bit, `//render/WW1Assassination_v008_####.png` |
| Audio | The VO is packed as sound strip `VO` from frame 1; add the mp3 at frame 1 when you encode at 60 fps. |
| Visibility | Baked `hide_render` keys: city → map at **1433**, map → city at **1681** (closing shot at the corner). |
| Caches / sims | None. Everything is baked keyframes. |
| Add-ons | None needed. |

Test frames before the full job: **813** (fireball), **1265** (shot, muzzle flash), **1500** (map, flags), **1750** (closing corner shot).
