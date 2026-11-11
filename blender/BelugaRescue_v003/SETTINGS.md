# BelugaRescue_v003 — farm render sheet

Values read back from `BelugaRescue_v003_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `BelugaRescue_v003_60fps.blend`: 69 MB, compressed. All 61 images are packed. Stored with Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Device saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2190**, step 1 (36.5 s) |
| Camera | One camera, `CAM_Film`, one continuous move (Track To an aim empty, animated lens, DOF on, f/6 except the calf X-ray (f/4) and her blurring vision (f/2)). No camera cuts, no camera markers. |
| Samples | 48 adaptive, noise threshold 0.05 |
| Denoising | OpenImageDenoise |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8, volume 1. Volume step rate 4, max steps 256. Caustics off (painted by a gobo spot). Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | sRGB, AgX, look "AgX - Punchy" (animated look). Exposure is keyframed per beat; do not override. |
| Output | PNG RGB 8-bit, compression 15, `//render/BelugaRescue_v003_####.png` |
| Audio | No voiceover yet. Beat start frames are in `beats.json`; when the VO arrives run `pipeline/retime_to_vo.py`. |
| Procedural FX | Ocean modifier (surface), Geometry Nodes bubbles / particulates / droplets driven by scene time and keyed values. No caches, no simulations, no linked libraries. |
| Add-ons | None. MPFB2 only built the characters. |

## Measured cost
No full-resolution frame was rendered (studio rule: review stills only). Estimate from review stills: a 270×480, 8-sample still takes about 8 s on this 4-core CPU,
so a full 1080×1920, 48-sample frame with the (now thin) water volume and denoising is roughly **8–12 min per frame on CPU** (≈300–440 h for 2190 frames).
On RenderStreet GPU nodes it should be far faster, but **the water volume is the cost driver**: run the test frames below first and check the time.
If time is a problem, raise `Volume step rate` from 4 to 8 (fewer volume steps) before lowering samples.

## Suggested test frames
- **380**: calf X-ray on the cyan-white explainer card (emission pulse, porthole shader)
- **880**: beluga reveal, god rays + particulates in the volume
- **1700**: ankle in the mouth, ascent with bubbles (volume heavy)
- **1930**: surface break, droplets, above/below water

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure, volume density or the world; they are animated.
