# ShoeBomber_v004: farm render sheet

These values were read back from `ShoeBomber_v004_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ShoeBomber_v004_60fps.blend`: 75 MB, compressed, committed as a **normal git file (no LFS)**. Every image is packed: 2K only for hero close-ups (the bomber's and attendant's skin and eyes, the sneakers), 1K for everything else. Opaque diffuse maps are packed as JPEG; the HDRI is a 1K .hdr. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1620**, step 1 (27.0 s) |
| Camera | One camera, `CAM_Film`, on one continuous spline move. There are no camera cuts or camera markers. It tracks the empty `CAM_Film_Aim` (DOF focuses on it, f/5.6 minimum) and the lens is animated. Set changes happen inside covered frames. The camera pushes into the shoe (4 black frames, f1066–1069). It flies through a volumetric cloud bank out of the studio into the sky (f1236–1256; peak cover f1247–1250). It dives through a volumetric cloud bank into the terminal skylight (f1384–1398). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (client animated look: no film blur) |
| Colour | View AgX, look **"AgX - Punchy"** (the client's animated look). The exposure is keyframed per set (cabin +0.9 readable blue night, studio 0.0, sky +0.35, airport −0.4), so do not override it. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/ShoeBomber_v004_####.png` |
| Audio | None yet. When the VO arrives, run `pipeline/retime_to_vo.py` with anchors built from `beats.json`; it warps the keys and adds the VO strip. |
| Volumes | Three small volumetric cloud banks for the crossings, each renderable only around its crossing, plus a few keyframed low-density smoke spheres. Volume step rate 4 and max 256 steps (saved in the file). |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. |
| Add-ons | None needed. |

## Measured cost
One full frame (f120, the match at the shoe in the night cabin: 1080×1920, 48 samples, motion blur) took **436 s in v002; v003 is lighter (no motion blur) and should not be slower** on this 4-core cloud CPU, about 196 h for all 1620 frames locally. It will be far faster on a farm GPU node. Run the test frames below before you approve the whole job.

## Suggested test frames
- **120**: the match flame at the sneaker (warm point light inside the night cabin).
- **560**: the tackle pile from above.
- **965**: the fuse out of the sole, held up to camera.
- **1180**: the studio cutaway (the grey putty slab with the cyan rim light).
- **1250**: the volumetric cloud crossing into the sky; check it for noise.
- **1340**: the plane over the dusk cloud deck.
- **1600**: the traveller at the airport.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are keyed.
