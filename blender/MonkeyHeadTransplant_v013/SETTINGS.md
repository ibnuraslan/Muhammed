# MonkeyHeadTransplant_v013: farm render sheet

These values were read back from `MonkeyHeadTransplant_v013_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `MonkeyHeadTransplant_v013_60fps.blend`: 78 MB, compressed. All images are packed; there are no linked libraries. Stored as a normal git file (no LFS, per studio policy). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1656**, step 1 (27.6 s) |
| Camera | One camera, `CAM_Film`, keyed on every frame from one spline. There are no cuts, camera switches or markers. The lens and focus distance are animated. DOF is on at f/5.6 minimum. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 12. Caustics off. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX with the look "AgX - Punchy". The exposure is keyframed (it dims at the end), so do not override it. |
| Output | PNG, RGB, 8-bit, written to `//render/MonkeyHeadTransplant_v013_####.png` |
| Audio | The v012 voiceover (`MonkeyHeadTransplant_v013_VO.mp3`) is on a sound strip from frame 1. The timing is the same as v012, retimed with the v012 anchors. |
| Sims / caches | None |
| Add-ons | None needed. |

## Suggested test frames
- **290**: the head carried between the tables, with the surgeon's face, cap and mask.
- **500**: stitching from the far side of the table. There's glossy steel and DOF at f/11 here.
- **1000**: the x-ray void. Transparent, emissive skin with the brain and spine; check for transparency noise.
- **1330**: the ECG close-up (emissive trace).
- **1640**: the ending. The surgeon is three-quarters to camera, checking the monkey.

If you see transparency noise in the x-ray, raise the samples to 96 for frames 940–1100 only.

## Do not
- Do not change the exposure, the world or the `Fade_*` / `XRay` / `VoidOn` shader values; all of them are animated.
- Do not render any camera other than `CAM_Film`.
