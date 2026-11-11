# ElectricianPolice_v003: farm render sheet

These values were read back from `ElectricianPolice_v003_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ElectricianPolice_v003_60fps.blend`: 44.7 MB (42.6 MiB), compressed, md5 `be493b7b4b8bb970a22ff77b9e68ad17`. Every image is packed: 256 images, mostly ≤512 px JPEG and ≤1K for large surfaces, with the hero's skin and shirt at 2K and two 1K HDRIs. Committed as a normal git file, with no LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1560**, step 1 (26.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous move, with a Track To on the `CAM_Film_Aim` empty. There are no camera cuts or camera markers. The lens is animated (22–50 mm). Sensor fit is Auto (36 mm). DOF is on at f/5.6, focused on the aim empty, so backgrounds stay readable. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | **Off**, per the animated look (STYLE_ANIMATED.md). |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (the animated look). Several things are keyframed: the scene exposure (day 0.25, dusk 0.6, night interior and street 0.75), the world lighting strength, the sky gradient seen by the camera (bright cyan to white by day, dimmed to an evening blue from 19.2 s) and the sun. Do not override them. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/ElectricianPolice_v003_####.png` |
| Audio | None yet. The voiceover has not arrived. `beats.json` lists each beat's start frame for `pipeline/retime_to_vo.py`. |
| Volumes | `DustHaze` is a very low-density warm volume (density halved for the animated look) over the street (x ±7.2, y −40…140, z 0…14). It is the only volume. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Sparks, dust and grid pulses are keyframed meshes. Flags and washing use F-curve noise modifiers. |
| Add-ons | None needed. MPFB2 was only used to build the humans. |

## Test frames before approving the whole job
- **60**: bike chase. Motion blur on the wheels, the rickshaw and the stalls.
- **760**: laptop close-up. The emissive screen UI and the red glow on his face.
- **1065**: the lever arc flash and sparks. This is the brightest frame, so check for clipping.
- **1306**: station interior at dusk, with an officer tapping the dead fan. This is the darkest frame; if it is noisy, raise samples to 96 for frames 1231–1381 only.
- **1550**: the final smirk at dusk, with the street lamps on.

## Do not
- Do not render any camera other than `CAM_Film`; it is the only one.
- Do not change the exposure, the world or the sun settings; all three are animated.
