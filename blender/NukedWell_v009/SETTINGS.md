# NukedWell_v009: farm render sheet
| Item | Value |
|---|---|
| File | `NukedWell_v009_60fps.blend` (41 MB, compressed, all images and the VO packed, plain git) |
| Blender | 5.2.2 LTS, factory startup, no add-ons needed |
| Engine | Cycles (saved as CPU; GPU is fine) |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1541** (25.7 s, built to the VO) |
| Camera | `CAM_Film` only, one continuous move keyed on every frame; no DOF, no motion blur |
| Samples | 64 adaptive, noise threshold 0.05, OpenImageDenoise |
| Light paths | max 6, diffuse 3, glossy 3, transmission 6, transparent 24, caustics off, persistent data on |
| Volumes / sims / particles | none (the fire, smoke, steam, water and dust are surface shaders on keyed meshes) |
| Colour | Filmic, High Contrast. **Exposure is keyed** (detonation flash, f1133–1213); do not override it |
| Output | PNG RGB 8-bit to `//render/NukedWell_v009_####.png`; add the VO at frame 1 when encoding at 60 fps |
| Logo frames | DA KRAS FILMS crate f1–95 (opening) and f1416–1541 (end) |
| Test times | f30 106 s, f700 172 s, f1500 97 s at full res on a 4-core CPU (a farm GPU node should be much faster) |
