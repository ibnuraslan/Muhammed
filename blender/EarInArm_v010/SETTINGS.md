# EarInArm_v010 — farm render sheet

These values were read back from `EarInArm_v010_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `EarInArm_v010_60fps.blend`: 70 MB, compressed. All images are packed. Stored as a plain git blob: the Git LFS push was refused (lfs.github.com returned 403 through the proxy), and the file is under GitHub’s 100 MB limit. |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1572**, step 1 (26.2 s at 60 fps; synced to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera markers. Lens and f-stop are animated, and DOF focuses on `CAM_Film_Aim`. Sensor fit is Auto (36 mm). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated-CG look) |
| Colour | Display sRGB. View AgX with the look "AgX - Punchy". Exposure −1.5 (scene-wide, not animated). |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/EarInArm_v010_####.png` |
| Audio | None yet. When the VO arrives, retime with `pipeline/retime_to_vo.py` using `EarInArm_v001/beats.json`. That adds the VO strip at frame 1. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 only built the file. |

## The two set changes
The film moves between two spaces: the procedure room at the origin and the rib-cage studio at x = 40 m. The camera jumps between them in one frame each, at **f171/172** (into the chest) and **f342/343** (out of the harvested cartilage onto the tray). Each jump happens inside a full-frame close-up of tee/skin or cartilage, held about 4–6 frames, and those keys use constant interpolation.
- The x-ray beat (5) stays in the real forearm with no jump: the arm skin turns glassy.
- The tissue-studio objects at x = 60 m are hidden (`hide_render`); they are left over from v002.

## Suggested test frames
- **60**: shocked patient, bandage, room
- **300**: rib studio, gloved scalpel lifting the cartilage block (transparent and SSS materials)
- **450**: carving on the tray, with shavings
- **950**: x-ray forearm, vessels growing on the ear inside the arm (glass skin, emission)
- **1560**: stitching macro (DOF at f/16 or more)
- **1760**: final smile

## Do not
- Do not add cameras or markers; `CAM_Film` is the only camera.
- Do not change the frame range: `beats.json` and the retime anchors assume 1–1770.
