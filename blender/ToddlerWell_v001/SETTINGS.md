# ToddlerWell_v002: farm render sheet

Values read back from `ToddlerWell_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ToddlerWell_v002_60fps.blend`, compressed, under 95 MB. All images are packed. Normal git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. No special features. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1950**, step 1 (32.5 s) |
| Camera | One camera, `Cam`, in one continuous move with a Track To on the empty `CamTarget`. No camera cuts or camera markers. Lens animated (14–45 mm), sensor 36 mm (Auto fit), DOF on at f/5.6 (animated look: backgrounds stay readable). |
| Samples | 48 with adaptive sampling, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max bounces 8; transparent max 16. The earth uses transparent back faces for the cross-section, so do not lower transparent bounces. |
| Motion blur | Off (animated-CG look, client direction 22:45 UTC) |
| Colour | AgX, look "AgX - Punchy". The animated-CG look pass (`pipeline/anim_look.py`) is applied: saturation up, bump down, sky-gradient backdrop for camera rays. |
| World | Camera rays see a sky-blue gradient, with a cloud plane in front of it. Lighting comes from a physical sky texture (multiple scattering). Sun elevation and rotation are keyframed for the time-lapse, so do not override them. The sun lamp, cloud offset, cross-section fill, shaft fills and head torch are keyframed too. |
| Output | PNG, RGB, 8-bit, `//render/ToddlerWell_v002_####.png` |
| Audio | None yet. The VO has not arrived. When it does: `pipeline/retime_to_vo.py` with `beats.json` (11 beat start frames) retimes every keyframe and adds the VO strip. |
| Caches / sims | None: no particle or physics caches, no linked libraries, no drivers. Crowd duplicates use NLA strips with time offsets. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Suggested test frames before the full job
- **150**: inside the shaft during the fall (fill lights, dust volume)
- **640**: excavator close-up, with exhaust volume and dirt pour
- **830**: cross-section during the time-lapse (transparent-back-face earth, strata)
- **1420**: head-torch beam in the shaft (spot light plus volume)
- **1700**: cross-section rise (fill light through the pipe groove)
- **1940**: final crane with the full crowd

## Do not
- Do not render any camera other than `Cam` (it is the only one).
- Do not change the world or light keyframes.
