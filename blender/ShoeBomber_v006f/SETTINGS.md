# ShoeBomber_v006f: farm render sheet

These values were read back from `ShoeBomber_v006f_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ShoeBomber_v006f_60fps.blend`: 73 MB, compressed, committed as a **normal git file (no LFS)**. Every image is packed. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1446**, step 1 (24.1 s) |
| Camera | **`CAM_Film` is the only camera.** It tracks the empty `CAM_Film_Aim`, with DOF focused on it at **f/8**, and the lens is animated. Shots are joined by **hard cuts**: there are no wipes, black frames or cloud crossings. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Motion blur | Off (client's animated look) |
| Colour | View AgX, look **"AgX - Punchy"**. Exposure is keyframed per set (cabin and beat-7 shoe +0.9, sky +0.35, airport −0.4), so do not override it. |
| Output | PNG to `//render/ShoeBomber_v006f_####.png` |
| Audio | None. When the VO arrives, retime with `pipeline/retime_to_vo.py`, using anchors from `beats.json`. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Every curve after f1158 is baked to per-frame constant keys (`07_retime.py`). |

## Suggested test frames
- **120**: the opening close-up on him over his shoes.
- **650**: the pin at seated eye height from the left side (the steward, the attendant and PaxA facing camera).
- **950**: PaxB kneeling face-on at the feet, with the shoes in front of him.
- **1120**: the cut-open shoe on the aisle carpet among the seat rows.
- **1190**: the plane over the cloud deck.
- **1320**: both sneakers in the tray riding the belt.

## Do not
- Do not render any other camera.
- Do not change the exposure or the world settings; both are keyed.
