# EarInArm_v015: farm render sheet

| Item | Value |
|---|---|
| File | `EarInArm_v015_60fps.blend`: about 39 MB, compressed, with all images and the VO packed. It is a plain git blob. |
| Blender | 5.2.2 (built headless, factory startup; no add-ons needed to render) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1572**, step 1 (26.2 s, built to the VO timing from the start) |
| Camera | One camera, `CAM_Film`, in one continuous move with no cuts and no markers. It uses Track To on `CAM_Film_Aim` (level horizon) and DOF at f/11 focused on the aim. |
| Samples | 48, adaptive, threshold 0.05, OpenImageDenoise |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics are off. |
| Motion blur | Off |
| Colour | AgX with the look "AgX - Punchy", exposure −0.3 |
| Output | PNG RGB 8-bit to `//render/EarInArm_v015_####.png` |
| Audio | The VO strip is at frame 1 (`EarInArm_v015_VO.mp3`, also packed). |
| Sims / caches | None |

Beat frames (from the VO): 1, 109, 301, 463, 649, 907, 1129, 1267, 1447; the last frame is 1572.
