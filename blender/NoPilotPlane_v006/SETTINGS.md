# NoPilotPlane_v006: farm render sheet

These values were read back from `NoPilotPlane_v006_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `NoPilotPlane_v006_60fps.blend`: 41 MB, compressed. All 56 images are packed (1K JPEG, 2K for YOU's face and shirt). It is a normal git file, not Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–4410**, step 1 (73.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. It is baked per frame (head-cam from 0 s, float-out to the face from 71.4 s). The lens is animated: 14 mm, then 24 mm at the reveal. Sensor fit is Auto (36 mm). DOF is off. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 12, diffuse 4, glossy 4, transmission 12, transparent 16. The MPFB procedural eyes render black below this depth. Caustics off. Persistent data on. |
| Motion blur | Off (client look rule: no heavy motion blur) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy" (client's animated look). Exposure +0.3, gamma 1.0. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/NoPilotPlane_v006_####.png` |
| Audio | None yet. There is no voiceover; the film is timed to the brief's target beat times (`beats.json`). |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Every motion is keyframed, including the alarm strobes, display tapes and attitude, and the exterior flight. |
| Add-ons | None needed. MPFB2 only built the humans. |

## Measured cost
One full frame of v002 (1080×1920, 48 samples, frame 2400, mid-dive cockpit) took **326 s** on this 4-core cloud CPU, about 400 h for 4410 frames locally. v004 has no motion blur but deeper light paths, so expect a similar cost. This needs a farm GPU node. Before you approve the whole job, run a few test frames on RenderStreet:
- **420**: cabin, window seat. Transparent window cut-outs, 49 rigged passengers, the spill.
- **2400**: the dive. Red strobe, tilted horizon, town, floating mug.
- **3100**: the descent past cloud cards. This is the transparency-heavy frame.
- **4380**: the face reveal (SSS skin, eyes). Check that the irises are blue, not black.

The cabin frames (0–16 s and 64–69 s, looking back) cost the most, because every passenger rig deforms on every frame.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change the world, the exposure or the light-path depths. The sky is an emissive dome under `EXT_ROT` that turns with the aircraft's attitude.
