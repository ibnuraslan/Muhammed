# Tsunami2004_v002 — farm render sheet

Values read back from `Tsunami2004_v002_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `Tsunami2004_v002_60fps.blend`: 85 MB, compressed, all images packed. Normal git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Saved as CPU; GPU is fine. No special features. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2400**, step 1 (40.0 s) |
| Camera | One camera, `CAM_Film`, one continuous move keyed on every frame. No camera cuts or camera markers (the B01–B13 markers are beat labels only). Lens animated. Sensor fit Auto (36 mm). DOF off. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8, volume 0. Caustics off. Persistent data on. |
| Motion blur | Off (animated-look rule from the client) |
| Colour | View AgX, look "AgX - Punchy". Exposure 0, gamma 1. Camera rays see a sky gradient (anim_look); the world strength, sun and HDRI mix are keyframed — do not override. |
| Output | PNG, 8-bit, written to `//render/Tsunami2004_v002_####.png` |
| Audio | None yet. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `beats.json`, then add the mp3 at frame 1 when encoding. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. The wave is a shape-keyed mesh with Displace modifiers; everything is keyframed. |
| Add-ons | None needed. |

## Measured cost
Not measured at full resolution (no full renders allowed locally). A 25 % / 4-sample check of frame 1160 from the packed file took 18 s on this 4-core CPU (frame 400: 9 s), including scene sync of 420 building instances. Expect several minutes per full 48-sample frame on CPU; use GPU nodes on the farm and run the test frames below first.

## Suggested test frames
- **200** (3.3 s): exposed seabed, flapping fish macro, wet sand.
- **870** (14.5 s): earthquake cross-section in the studio bowl (volume water column + light flash).
- **1160** (19.3 s): low beach angle, the 30 m wave with crest spray volume, people running.
- **1550** (25.8 s): surge through the town street (420 building instances, churn displacement).
- **2100** (35 s): aftermath crane, warm late light, dust volume.

## Do not
- Do not render other cameras or change the colour look; the world and sun are animated.
