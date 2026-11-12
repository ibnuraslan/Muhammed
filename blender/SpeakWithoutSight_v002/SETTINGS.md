# SpeakWithoutSight_v002: farm render sheet

These values are read back from `SpeakWithoutSight_v002_60fps.blend` opened in factory-startup Blender 5.2.2.

| Item | Value |
|---|---|
| File | `SpeakWithoutSight_v002_60fps.blend`: 80 MB (83,685,564 bytes), compressed, with every image packed. A normal git file, not LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100% |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1980**, step 1 (33.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous Catmull-Rom move. No cuts, no camera markers. Lens animated (16–70 mm), DOF on at f/5.6, focused on `CAM_Film_Aim`. |
| Samples | 48, adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX, look "AgX - Punchy" (animated-CG look). The camera sees a sky-blue gradient world; lighting comes from the HDRI. Light energies and the world strength are keyframed (the dim "trapped" beat, the explainer dome, the day/night time-lapse), so do not override them. |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/SpeakWithoutSight_v002_####.png` |
| Audio | None yet. The voiceover comes later: retime with `beats.json` and `pipeline/retime_to_vo.py`. |
| Simulations | None: no particles, cloth, caches or linked libraries. One small geometry-nodes modifier (`FloorClamp`) on the skirts, built in. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Suggested test frames
- **300**: the dim "trapped" beat, with her face on a soft key in a dark room
- **780**: the explainer dome, x-ray hand skeleton, larynx and warm pulses
- **1290**: macro of fingertips on the lips, with the O/E/M contour rings
- **1780**: time-lapse night: lamp-lit, snow outside
- **1950**: the hug, wide, with the family reacting

If the dome frames (700–1060) show noise in the glassy x-ray skin, raise samples to 96 for that range only.

## Do not
- Do not render any camera other than `CAM_Film`.
- Do not override the exposure or world strength.
