# BelugaRescue_v00N — farm render sheet

Values read back from `BelugaRescue_v00N_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `BelugaRescue_v00N_60fps.blend`: {SIZE} MB, compressed. All {NIMG} images are packed. Stored with Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Device saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2190**, step 1 (36.5 s) |
| Camera | One camera, `CAM_Film`, one continuous move (Track To an aim empty, animated lens, DOF on, f-stop animated 0.8–4). No camera cuts, no camera markers. |
| Samples | 48 adaptive, noise threshold 0.05 |
| Denoising | OpenImageDenoise |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8, volume 1. Volume step rate 4, max steps 256. Caustics off (painted by a gobo spot). Persistent data on. |
| Motion blur | On, shutter 0.5 |
| Colour | sRGB, AgX, look "AgX - Medium High Contrast". Exposure is keyframed per beat; do not override. |
| Output | PNG RGB 8-bit, compression 15, `//render/BelugaRescue_v00N_####.png` |
| Audio | No voiceover yet. Beat start frames are in `beats.json`; when the VO arrives run `pipeline/retime_to_vo.py`. |
| Procedural FX | Ocean modifier (surface), Geometry Nodes bubbles / particulates / droplets driven by scene time and keyed values. No caches, no simulations, no linked libraries. |
| Add-ons | None. MPFB2 only built the characters. |

## Measured cost
{COST}

## Suggested test frames
- **380**: calf X-ray on the cyan-white explainer card (emission pulse, porthole shader)
- **880**: beluga reveal, god rays + particulates in the volume
- **1700**: ankle in the mouth, ascent with bubbles (volume heavy)
- **1930**: surface break, droplets, above/below water

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure, volume density or the world; they are animated.
