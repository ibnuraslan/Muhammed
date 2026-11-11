# ShoeBomber_v002: farm render sheet

These values were read back from `ShoeBomber_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ShoeBomber_v002_60fps.blend`: 120 MB, compressed, stored with Git LFS. Every image is packed (textures capped at 2K, background-extra textures at 1K). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1620**, step 1 (27.0 s) |
| Camera | One camera, `CAM_Film`, on one continuous spline move. There are no camera cuts or camera markers. It tracks the empty `CAM_Film_Aim` (DOF focuses on it, f/2.8) and the lens is animated. Set changes happen inside covered frames: into the black of the shoe at f1062–1069, a white cloud wipe at f1240–1258, and a cloud dive at f1388–1398. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 |
| Colour | View AgX, look "AgX - Medium High Contrast". The exposure is keyframed per set (cabin −0.5, studio −0.3, sky 0.0, airport −1.3), so do not override it. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/ShoeBomber_v002_####.png` |
| Audio | None yet. When the VO arrives, run `pipeline/retime_to_vo.py` with anchors built from `beats.json`; it warps the keys and adds the VO strip. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. The smoke is a few keyframed low-density volume spheres. |
| Add-ons | None needed. |

## Measured cost
One full frame (f700, the tackle pile: 1080×1920, 48 samples, motion blur) took **342 s** on this 4-core cloud CPU, about 154 h for all 1620 frames locally. It will be far faster on a farm GPU node. Run the test frames below before you approve the whole job.

## Suggested test frames
- **120**: the match flame at the sneaker (warm point light inside the night cabin).
- **560**: the tackle pile from above.
- **965**: the fuse out of the sole, held up to camera.
- **1180**: the studio cutaway (the slab and its glowing wire edge).
- **1340**: the plane over the cloud deck. It has the most volume and SSS, so it's likely the slowest frame.
- **1600**: the traveller at the airport.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are keyed.
