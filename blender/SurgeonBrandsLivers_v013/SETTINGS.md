# SurgeonBrandsLivers_v013 — farm render sheet

These values were read back from `SurgeonBrandsLivers_v013_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `SurgeonBrandsLivers_v013_60fps.blend`: 68 MB, compressed, normal git file. All images and the voiceover are packed (1K textures, 2K only for the hero faces and the liver, 1K HDRI). There are no linked libraries. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1644**, step 1 (27.4 s at 60 fps). Same voiceover and beat timing as v011. The last shot (the clerk stamps the red X, sets the stamp down and the camera settles on the certificate) runs to frame 1644; there are no empty or black frames. |
| Camera | One camera, `CAM_Film`, aimed at `CAM_Film_Aim` (DOF focus). 14 shots with hard cuts at frames 136, 276, 430, 571, 641, 776, 916, 1061, 1176, 1241, 1311, 1446 and 1576; each shot has its own slow move. f/8 on the two liver close-ups (136-275, 1061-1175), f/5.6 elsewhere. Sensor fit Auto (36 mm). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | **Off** (animated-look rule: no heavy motion blur). |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (animated look). Exposure 0, gamma 1. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/SurgeonBrandsLivers_v013_####.png` |
| Audio | The voiceover `SurgeonBrandsLivers_v013_VO.mp3` (26.3 s) is packed as a sound strip on channel 1 from frame 1; the same mp3 is in this folder. |
| Caches / sims | None: no simulations, particles, Alembic or drivers. Sparks and the argon beam are keyframed objects. The caps use a Displace + Subdivision modifier only. |
| Add-ons | None needed. MPFB2 only built the people. |

## Measured cost
Not measured (no full-resolution renders here). v011 had the same sets and people; expect about 1.5–2.5 min per frame on a 4-core CPU, far less on a farm GPU node.

Before approving the whole job, run these test frames:
- **205**: the argon beam brands the liver inside the open abdomen (f/8, sparks, tip light).
- **520**: surgeon 1's smirk after the mask comes down: skin SSS, eyes, cloth cap.
- **740**: living room. She doubles over; the glow shows inside her abdomen through the shirt.
- **1120**: the second surgeon's hands lift the branded liver out of the patient.
- **1350**: hearing room. The translucent livers behind the defendant are transparent and emissive.
- **1618**: the clerk presses the stamp; the red X prints.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not re-grade toward a film look; this version follows `blender/STYLE_ANIMATED.md`.
