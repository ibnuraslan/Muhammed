# MonkeyHeadTransplant_v007: farm render sheet

These values were read back from `MonkeyHeadTransplant_v007_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `MonkeyHeadTransplant_v007_60fps.blend`: 72 MB, compressed. All images are packed; there are no linked libraries. Stored as a normal git file (no LFS, per studio policy). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1770**, step 1 (29.5 s) |
| Camera | One camera, `CAM_Film`, keyed on every frame from one spline. There are no cuts, camera switches or markers. The lens and focus distance are animated. DOF is on at f/5.6 minimum. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 12. Caustics off. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX with the look "AgX - Punchy". The exposure is keyframed (it dims at the end), so do not override it. |
| Output | PNG, RGB, 8-bit, written to `//render/MonkeyHeadTransplant_v007_####.png` |
| Audio | None yet. The voiceover is still to come. When it arrives, retime with `pipeline/retime_to_vo.py` using `beats.json`, which also adds the VO strip. |
| Sims / caches | None |
| Add-ons | None needed. |

## Suggested test frames
- **330**: the head carried between the tables, with both hands gripping.
- **560**: macro on the stitches. There's a lot of glossy steel and DOF here.
- **1100**: the x-ray void. Transparent, emissive skin with a glowing brain and spine; check for transparency noise.
- **1450**: the ECG close-up (emissive trace).
- **1740**: the end wide, dimmed.

If you see transparency noise in the x-ray, raise the samples to 96 for frames 1030–1210 only.

## Do not
- Do not change the exposure, the world or the `Fade_*` / `XRay` / `VoidOn` shader values; all of them are animated.
- Do not render any camera other than `CAM_Film`.
