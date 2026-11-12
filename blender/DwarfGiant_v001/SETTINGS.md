# DwarfGiant — farm render sheet

| Item | Value |
|---|---|
| File | `DwarfGiant_v002_60fps.blend` (packed, compressed; normal git file, no LFS) |
| Blender | 5.2.2 LTS |
| Engine | Cycles, saved as CPU (GPU fine). No add-ons needed (MPFB only built the file). |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | 1–2340 (39.0 s) |
| Camera | One camera, `CAM_Film`, one continuous catmull-spline move; no cuts or camera markers. Lens animated; DOF on (focus empty `CAM_Focus`, f/4, f/1.2 during the blurred-vision POV). |
| Samples | 48 adaptive, noise threshold 0.05, OpenImageDenoise |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16; caustics off; persistent data on |
| Motion blur | On, shutter 0.5 |
| Colour | AgX, look "AgX - Medium High Contrast" |
| Output | PNG RGB 8-bit to `//render/DwarfGiant_v002_####.png` |
| Audio | No VO yet. Retime with `pipeline/retime_to_vo.py` using `beats.json` when it arrives. |
| Caches / sims | None (grass is a static hair-particle instance system; no simulations). |
| Memory | Peak ~11 GB RAM per frame on CPU at 270×480 review size; allow 16 GB+ per node. |
