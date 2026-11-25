# SurgeonBrandsLivers_v015: farm render sheet
| Item | Value |
|---|---|
| File | `SurgeonBrandsLivers_v015_60fps.blend`. It is 65 MB with everything packed: images, the VO and the garment textures. No linked libraries. |
| Engine | Cycles (CPU or GPU) |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1644** (27.4 s). The VO runs from frame 1 to 1578, followed by the closing beat. |
| Camera | `CAM_Film`, the only camera. One continuous move with no cuts and no markers; it whip-pans between the rooms at the hub. |
| Samples | 64, adaptive, threshold 0.04, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. |
| Colour | AgX, look "AgX - Punchy", exposure −0.55 |
| Output | PNG RGB 8-bit to `//render/SurgeonBrandsLivers_v015_####.png` |
| Measured | 65–100 s per full frame on a 4-core CPU at 16 samples. Expect about 3–5 min per frame at 64 samples on CPU, much less on a GPU farm. |
| Logo frames | DA KRAS FILMS poster in the home scene: about frames 606–800 |
