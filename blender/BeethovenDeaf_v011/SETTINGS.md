# BeethovenDeaf_v011: farm render sheet

| Item | Value |
|---|---|
| File | `BeethovenDeaf_v011_60fps.blend`, 33 MB, compressed. Everything is packed, including the VO. No linked libraries. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1435** (23.9 s, timed to the voiceover) |
| Camera | `CAM_Film` only: one continuous move with no markers. The lens and f-stop are animated (f/6–11). |
| Samples | Adaptive, max 64, noise threshold 0.04, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Texture limit 2048. |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy", exposure +0.35 |
| Output | PNG RGB 8-bit, `//render/BeethovenDeaf_v011_####.png` |
| Audio | The VO strip is at frame 1. The same mp3 sits next to the .blend. |
| Animated visibility | `hide_render` keys switch the x-ray anatomy on at frame 394 and off at frame 1031. Do not use any "render visible only" override. |

Measured on a 4-core CPU at full resolution:
- frame 100: 3 min 6 s
- frame 700 (x-ray): about 6 min
- frame 1400: 3 min

A GPU farm node will be much faster.

Test frames to run first: 100 (rod and hands), 700 (x-ray skull) and 1400 (ending).
