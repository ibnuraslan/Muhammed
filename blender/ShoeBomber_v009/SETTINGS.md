# ShoeBomber_v009: farm render sheet

These values were read back from `ShoeBomber_v009_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ShoeBomber_v009_60fps.blend`: 88 MB, compressed, committed as a **normal git file (no LFS)**. Every image is packed. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1469**, step 1 (24.5 s) |
| Camera | **`CAM_Film` is the only camera.** It tracks the empty `CAM_Film_Aim`, with DOF focused on it at **f/8**, and the lens is animated. Shots are joined by **hard cuts**: there are no wipes or black frames. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Motion blur | Off (client's animated look) |
| Colour | View AgX, look **"AgX - Punchy"**. Exposure is keyframed per set (cabin and beat-7 shoe +0.9, sky +0.35, airport −0.4; switched at the cuts), so do not override it. |
| Output | PNG to `//render/ShoeBomber_v009_####.png` |
| Audio | `ShoeBomber_v009_VO.mp3`, which starts at frame 1. Mux it onto the render; the picture is already on its beats. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Every curve is baked to per-frame constant keys (`07_retime_vo.py`). |

## Suggested test frames
- **60**: the opening, with him raising the shoe and the match at the fuse.
- **420**: the grab and the drag into the aisle.
- **560**: the pin at seated eye height.
- **760**: PaxB kneeling face-on, looking at the shoes.
- **930**: the cut-open shoe on the aisle carpet.
- **1050**: the plane over the cloud deck.
- **1260**: the payoff, with passengers in socks putting their sneakers in the trays.
- **1420**: the traveller close-up.

## Do not
- Do not render any other camera.
- Do not change the exposure or the world settings; both are keyed.
