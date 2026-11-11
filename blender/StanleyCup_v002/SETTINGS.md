# StanleyCup_v002 — farm render sheet

Values read back from `StanleyCup_v002_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `StanleyCup_v002_60fps.blend`: 131 MB, compressed. All 95 images packed (≤2K; normal/roughness maps 1K 8-bit). Stored with Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Device saved as CPU; GPU is fine. No special features. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1530**, step 1 (25.5 s) |
| Camera | One camera, `CAM_Film`, one continuous move. No camera cuts or camera markers. Lens and f-stop are animated (16–70 mm, f/2.8–11); DOF on, focus object `CAM_Film_Aim`. Clip start 2 mm (the camera flies through a bullet hole). |
| Samples | 48, adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 (180° at 60 fps) |
| Colour | Display sRGB. View AgX, look "AgX - Medium High Contrast", exposure −0.45. Gamma 1.0. |
| Output | PNG, RGB, 8-bit, written to `//render/StanleyCup_v002_####.png` |
| Audio | None yet (VO not supplied). |
| Caches / sims | None. The lawn grass is a hair particle system (no cache needed). Booleans (bullet holes) and the Wave modifier (ripples) evaluate per frame. No Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Measured cost
FULLFRAME_LINE

## Suggested test frames
- **200**: inside the wall cavity, lit only by the light leaking through the hole (check noise).
- **250**: looking through the drywall hole at the couple.
- **985**: impact sparks with motion blur (brightest frame).
- **1100**: x-ray of the tumbler (transparent shaders, water).
- **1500**: her gripping the dented tumbler (faces, hands).

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change the exposure or the world; the HDRI rotation and the light keys are set for the move.
