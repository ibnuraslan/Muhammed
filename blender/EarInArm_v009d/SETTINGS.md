# EarInArm_v009d — farm render sheet

These values were read back from `EarInArm_v009d_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `EarInArm_v009d_60fps.blend`: 70 MB, compressed. All images are packed. Stored as a plain git blob: the Git LFS push was refused (lfs.github.com returned 403 through the proxy), and the file is under GitHub’s 100 MB limit. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1770**, step 1 (29.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera markers. Lens and f-stop are animated, and DOF focuses on `CAM_Film_Aim`. Sensor fit is Auto (36 mm). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated-CG look) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy". Exposure −1.5 (scene-wide, not animated). |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/EarInArm_v009d_####.png` |
| Audio | None yet. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `EarInArm_v001/beats.json`. That adds the VO strip at frame 1. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 only built the file. |

## No set changes
The whole film stays in the procedure room. There are no camera jumps: `CAM_Film` makes one continuous move from frame 1 to 1770.
- Beat 2 (chest) is an x-ray inside the patient's chest: his tee turns glassy and the rib-cage model sits inside it.
- Beat 5 (arm) is an x-ray inside the real forearm, as before.
- The old rib-cage and tissue studios are deleted from the file.

## Suggested test frames
- **60**: shocked patient, bandage, room
- **250**: chest x-ray, forceps lifting the cartilage piece out of the rib cage (glass tee, SSS)
- **450**: carving on the tray, with shavings
- **950**: x-ray forearm, vessels growing on the ear inside the arm (glass skin, emission)
- **1560**: stitching macro (DOF at f/16 or more)
- **1760**: final smile

## Do not
- Do not add cameras or markers; `CAM_Film` is the only camera.
- Do not change the frame range: `beats.json` and the retime anchors assume 1–1770.
