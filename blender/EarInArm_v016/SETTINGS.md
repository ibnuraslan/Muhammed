# EarInArm_v016: farm render sheet

| Item | Value |
|---|---|
| File | `EarInArm_v016_60fps.blend`: about 37 MB, compressed, with all images and the VO packed. It is a plain git blob. |
| Blender | 5.2.2 (built headless, factory startup; no add-ons needed to render) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1572**, step 1 (26.2 s, built to the VO timing from the start) |
| Camera | One camera, `CAM_Film`, in one continuous move with no cuts and no markers. It uses Track To on `CAM_Film_Aim` (level horizon) and DOF at f/11 focused on the aim. |
| Samples | 48, adaptive, threshold 0.05, OpenImageDenoise (albedo + normal passes) |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics are off. |
| Speed | Persistent Data on. Simplify on: texture limit 2048 px, max subdivision 2 (the highest render level in the file, so nothing changes), child particles 100 % (no particles). |
| Motion blur | Off |
| Colour | AgX with the look "AgX - Punchy", exposure −0.3 |
| Output | PNG RGB 8-bit to `//render/EarInArm_v016_####.png` |
| Audio | The VO strip is at frame 1 (`EarInArm_v016_VO.mp3`, also packed). |
| Sims / caches | None |

Beat frames (from the VO): 1, 109, 301, 463, 649, 907, 1129, 1267, 1447; the last frame is 1572.

## Logo (DA KRAS FILMS)
| Where | Readable frames |
|---|---|
| Framed poster on the back wall (dark logo on a cream panel) | 1–240 (4.0 s), 1086–1196, 1461–1572 |
| Chest print on the surgeon's scrub top (left chest, dark logo) | 1–60, 266–306, 446–461, 1491–1572 |

## Measured render time (this container: 4 CPU cores, no GPU)
Full 1080×1920, from the packed file: frame 1 = 133 s, frame 786 = 265 s, frame 1572 = 137 s.
A many-core farm node or a GPU is several times faster.
