# DrunkTrain_v008: farm render sheet (client-approved build)

| Item | Value |
|---|---|
| File | `DrunkTrain_v008_60fps.blend`, 74 MB, compressed, everything packed (VO included). Stored as a plain git file (no LFS). |
| Engine | Cycles. 64 max samples, adaptive threshold 0.05, OIDN denoising. Bounces 6/3/3/6, transparent 16, caustics off, persistent data on, simplify texture limit 2048. |
| Resolution | 1080 × 1920 at 100 %, 60 fps |
| Frame range | **1–1735** (28.9 s). Built to the v007 VO, so no retime. |
| Camera | `CAM_Film`, keyed every frame, one move. The scene changes only inside two white flashes (f1180–1193 and f1507–1520). |
| Colour | AgX, look Punchy. Motion blur is off. |
| Output | PNG to `//render/DrunkTrain_v008_####.png`. The VO is packed as strip `VO` at frame 1. |
| Animated visibility | `hide_render` and `hide_viewport` keys on the man (hidden f541–646, under the passing train) and on the worker (hidden f1–779). |
| Test frames | f300 123 s, f900 171 s, f1650 189 s on a 4-core CPU. |
