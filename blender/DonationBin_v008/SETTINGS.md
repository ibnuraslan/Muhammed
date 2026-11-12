# DonationBin_v008: farm render sheet

These values were read back from `DonationBin_v008_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `DonationBin_v008_60fps.blend`: 89 MB (93,242,879 bytes), compressed. Every image is packed. Committed as a plain git file, not Git LFS.  |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2388**, step 1 (39.8 s at 60 fps) |
| Camera | One camera, `CAM_Film`, in one continuous move baked per frame. There are no camera cuts or camera markers. The lens and focus distance are animated. Sensor fit is Auto (36 mm). DOF is on at f/5.6, but the focus distance is animated, so the background stays readable. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated-look rule) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (animated look). Gamma 1.0. The scene exposure is keyframed for the inside-bin and time-lapse light changes, so do not override it. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/DonationBin_v008_####.png` |
| Audio | None yet. There's no voiceover, so the film is timed to the brief's target beat times. Retime with `beats.json` and `pipeline/retime_to_vo.py` when the VO arrives. |
| Constraints | 160 Limit Rotation constraints on fingers, thumbs and wrists, plus the IK and Copy Rotation of the control rigs. They need no baking. |
| Caches / sims | None: no simulations, Alembic, linked libraries or drivers. The only particle systems are the static hair on the Poly Haven rat (two HAIR systems, nothing to bake). Two "Auto Smooth" geometry-node modifiers come with Poly Haven props. |
| Animated shading | Bin shell, liner and mechanism materials have a keyframed `XRAY` value (x-ray explainer f492–975). The world has a keyframed `STUDIO_MIX` (cyan-white studio gradient over the same frames) and an HDRI strength. |
| Add-ons | None needed. MPFB2 only built the file. |

## Measured cost
A 270×480, 8-sample frame (f2045, sparks) took **8.5 s** on this 4-core cloud CPU. Full-resolution frames were not rendered locally (studio rule). Scaling by pixels and samples puts a full frame at very roughly 2–4 min on this CPU, which is far faster on a farm GPU node.

Before you approve the whole job, run a few test frames on RenderStreet:
- **120**: daylight exterior, tiptoe reach, many props
- **700**: the x-ray explainer, with transparent shell and studio gradient (check transparency noise)
- **1640**: night time-lapse inside the bin, lit by the dim blue fill and the slit rake light (check noise; raise to 96 samples for frames 1600–1800 if needed)
- **1356**: wall pounding, with the scanned clothes heaps and raking slit light
- **2012**: firefighter A's 3/4 face through the grinder sparks
- **2040**: grinder sparks and the emissive cut line
- **2300**: the blanket wrap and both firefighters in daylight

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure, the world settings or the bin materials' XRAY values; all are animated.
