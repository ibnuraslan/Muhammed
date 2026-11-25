# LegoInNose_v014: farm render sheet

These values were read back from `LegoInNose_v014_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `LegoInNose_v014_60fps.blend`, about 41 MB, compressed. Everything is packed: no unpacked images, no linked libraries. The voiceover is packed too. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2036**, step 1 (33.9 s, timed to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move: no cuts and no camera markers. The lens is animated. Sensor fit is Auto (36 mm). DOF is on at f/22, focused on `CAM_Film_Aim`. Clip start is 4 mm, for the nostril macros. |
| Samples | 48 with adaptive sampling, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise, albedo + normal passes) |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 32 (kept for the x-ray voids). Caustics off. |
| Speed | Persistent Data on. Simplify on: texture limit 2048 px, max subdivision 2 (only the bathroom curtain had 3; no visible change). |
| Motion blur | Off (animated look) |
| Colour | Display sRGB. View **Filmic**, look **High Contrast**. The scene exposure is keyframed (-0.45 in the living room and bedroom, -0.55 in the bathroom), so do not override it. |
| Output | PNG, RGBA, 8-bit, written to `//render/LegoInNose_v014_####.png` |
| Audio | `LegoInNose_v014_VO.mp3` is packed and placed as the VO strip at frame 1. The same mp3 sits next to the .blend for encoding. |
| Caches and sims | None: no simulations, particles, Alembic, drivers or linked libraries. The shower water is keyframed curves. |
| Add-ons | None needed. MPFB2 was used only to build the file. |
| Animated visibility | `hide_render` keys switch the three sets (living room, bedroom, bathroom) inside the x-ray voids. Do not use any "render visible only" override. |

## Test frames to run first on RenderStreet
| Frame | Time | What it shows |
|---|---|---|
| **104** | 1.7 s | The boy's fingertips pinching the red brick into the nostril (x-ray window) |
| **858** | 14.3 s | Mom kneeling, with the tweezers at the nostril |
| **925** | 15.4 s | The yellow brick held up on the tweezers, with the boy's face |
| **1210** | 20.2 s | The void: the skull and passage on deep purple-blue |
| **1350** | 22.5 s | The bedroom (saturated blue wall) |
| **1900** | 31.7 s | The red brick on the teal ledge in the shower |

## Logo (DA KRAS FILMS)
| Where | Readable frames |
|---|---|
| Print on the dad's yellow PJ top (dark logo, bedroom) | 1326–1500 (2.9 s). His resting hand crosses part of it at times. |
| Print on all 4 sides of the green toy box (white logo, living room) | 821–896 and 951–996. Partly at the frame edge at 1–60 and 200–260. |

## Measured render time (this container: 4 CPU cores, no GPU)
Full 1080×1920, from the packed file: frame 1 = 104 s, frame 1018 = 169 s, frame 2036 = 119 s.
