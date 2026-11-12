# FanCancer_v004: farm render sheet

| Item | Value |
|---|---|
| File | `FanCancer_v004_60fps.blend`, compressed, with every image packed. It is a normal git file with no LFS. The size is in the README. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2640**, step 1 (44.0 s) |
| Camera | One camera, `FilmCam`, in one continuous move keyed every frame. There are no camera markers. Set changes happen only while a surface fills the lens: neck skin, the skin macro, the ceiling light panel, a lit window, the curtain, the laptop screen. Those keys are CONSTANT. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Motion blur | Off (animated look) |
| Colour | AgX with the look "AgX - Punchy.. The world HDRI/colour mix is keyed per set, so do not override the world. |
| Output | PNG, 8-bit, written to `//render/FanCancer_v004_####.png` |
| Audio | None yet. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `beats.json`. |
| Sims / caches | None. The confetti is keyframed objects. There are no particles, no Alembic, no linked libraries and no add-ons. |

## Test frames before approving the full job
| Frame | Content |
|---|---|
| 60 | Rink wide with the crowd |
| 420 | Skin cross-section with the cells |
| 1000 | The slap on the glass |
| 1560 | The clinic excision |
| 2000 | The city at dusk |
| 2200 | Home, the shock |
| 2500 | Finale with the confetti |
