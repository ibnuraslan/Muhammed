# EarInArm_v002 — farm render sheet

These values were read back from `EarInArm_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `EarInArm_v002_60fps.blend`: 55 MB, compressed. All images are packed. Stored with Git LFS. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1770**, step 1 (29.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera markers. Lens and f-stop are animated, and DOF focuses on `CAM_Film_Aim`. Sensor fit is Auto (36 mm). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 (180° at 60 fps) |
| Colour | Display sRGB. View AgX with the look "AgX - High Contrast". Exposure −1.9 (scene-wide, not animated). |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/EarInArm_v002_####.png` |
| Audio | None yet. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `EarInArm_v001/beats.json`. That adds the VO strip at frame 1. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 only built the file. |

## The four set changes
The film moves between three spaces: the procedure room at the origin, the rib studio at x = 40 m and the tissue studio at x = 60 m. The camera jumps between them in one frame each, at **f171/172, f342/343, f803/804 and f1062/1063**. Each jump happens inside a full-frame skin or cartilage close-up, and those keys use constant interpolation.
- Motion blur on those four frames will smear a little across the jump.
- If that shows, render f171, f342, f803 and f1062 with motion blur off.

## Suggested test frames
- **60**: shocked patient, bandage, room
- **300**: rib studio, gloved scalpel lifting the cartilage block (transparent and SSS materials)
- **450**: carving on the tray, with shavings
- **950**: tissue studio, vessels growing on the ear (emission, glass skin)
- **1560**: stitching macro (DOF at f/16 or more)
- **1760**: final smile

## Do not
- Do not add cameras or markers; `CAM_Film` is the only camera.
- Do not change the frame range: `beats.json` and the retime anchors assume 1–1770.
