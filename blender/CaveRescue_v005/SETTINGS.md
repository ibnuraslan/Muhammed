# CaveRescue_v005: farm render sheet

Values read back from `CaveRescue_v005_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `CaveRescue_v005_60fps.blend`: 71 MB, compressed. All images are packed. It is a plain git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–3090**, step 1 (51.5 s) |
| Camera | One camera, `CAM_Film`, on one continuous spline. There are no camera markers. The lens is animated and DOF is at f/5.6 or higher. The four scale changes (tunnel → cross-section → chamber, passage → cross-section → tunnel) go through rock: the `CAM_RockWipe` card in front of the lens is fully black for 4 frames around frames 582, 1008, 2565 and 2726. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, volume 1. Caustics off. Persistent data on. |
| Motion blur | Off (client's animated-look rule) |
| Colour | View AgX with the look "AgX - Punchy". **Exposure is keyframed** (+1.3 to +2.2 inside the caves), so do not override it. |
| World | Forest HDRI for lighting. Camera rays see a sky-blue gradient (anim_look pass). |
| Volumes | Underwater murk (`S5_Murk`) and a silt cloud (`S5_Silt`). Expect noise there: if the passage frames 1213–1711 and 2440–2565 are noisy, raise samples to 96 for those ranges only. |
| Drivers | Simple frame expressions (`frame/90` and similar) on water ripples, rain, flood flow and silt. They evaluate without Python auto-run. |
| Output | PNG, RGB, 8-bit, written to `//render/CaveRescue_v005_####.png` |
| Audio | None yet. The VO isn't delivered; retime with `pipeline/retime_to_vo.py` using `beats.json` when it arrives. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Suggested test frames
- **150**: the walk to the cave mouth (jungle, trees, characters)
- **1100**: the chamber with the diver surfacing (torches plus blue fill)
- **1400**: the flooded squeeze (volume murk; check the noise)
- **2240**: sedation close-up (skin and hands)
- **2650**: cross-section with lights on the route (sky-gradient backdrop)
- **2850**: stretcher out of the mouth (daylight)

## Do not
- Do not render any camera other than `CAM_Film`.
- Do not change exposure, the world or `CAM_RockWipe`; all three are animated.
