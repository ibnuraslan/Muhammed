# MotionTest_v001 — render settings sheet

Values read back from `MotionTest_v001_60fps.blend` opened in factory-startup Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `MotionTest_v001_60fps.blend` (74 MB, compressed, all 25 images packed) |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Device saved as CPU; GPU is fine. No special features. |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | 1–600, step 1 (10.0 s) |
| Camera | Single camera `CAM_Main`, one continuous shot, no camera cuts or markers. 50 mm, sensor fit Auto (36 mm), DOF on, f/5.6, focus on `CAM_Aim`. |
| Samples | 48, adaptive sampling on, noise threshold 0.05 |
| Denoising | On, OpenImageDenoise |
| Light paths | Max 8 / diffuse 3 / glossy 3 / transmission 8 / transparent 16. Caustics off, filter glossy 1.0. |
| Motion blur | On, shutter 0.5 (180° at 60 fps) |
| Persistent data | On |
| Colour management | Display sRGB. View AgX, look "AgX - Medium High Contrast". Exposure 0.0, gamma 1.0, no curves. |
| Output | PNG, RGB, 8-bit, compression 15, path `//render/MotionTest_v001_####.png` |
| External caches | None (no sims, particles or alembic) |
| Add-ons / plugins | None required. No drivers, no linked libraries. MPFB2 built the character but is not needed to open or render. |
| Audio | None (no narration for this test) |

## Lighting / look (as built)
- **World:** Poly Haven `hausdorf_meadow` 2K HDRI (overcast), strength 0.85, Z rotation 300°.
- **Key:** Sun `Key_Sun`, 3.2 W/m², angular diameter 9°, colour (1.0, 0.94, 0.86). It sits 40° up and 10° to the right of the character's facing direction, about 55° off the camera axis.
- **Ground:** `grass_ground` 2K (diffuse/roughness/normal), tiled at 2.2 m and blended with a 5.3 m rotated copy to hide repeats. Saturation 0.82, value 0.95.
- **Skin:** MPFB "ENHANCED_SSS" material. Clothes, hair and eyes use MakeHuman MAKESKIN materials with their diffuse, normal and AO maps.
- **Bottle:** green glass (transmission 1.0, roughness 0.06, IOR 1.5, volume absorption density 60) with a paper label.

## Baseline check
48 samples / 0.05 / OIDN is carried over from the Goat Rescue baseline. It has **not** been checked at full resolution on this scene, because this container has no GPU and every preview here was 360×640 at 8 samples. Before the full farm job, render 2–3 test frames at full resolution: frame 260 (hand on glass), 445 (bottle at lips, SSS face) and 600.

## Do not
- Do not render other cameras or ranges; there is only `CAM_Main`, frames 1–600.
