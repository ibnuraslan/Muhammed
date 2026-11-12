# DwarfGiant_v002 — farm render sheet

Read back from `DwarfGiant_v002_60fps.blend` opened with `--factory-startup` in Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `DwarfGiant_v002_60fps.blend`, 92.5 MB, compressed, all 169 images packed. Normal git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles, saved as CPU (GPU fine). No add-ons needed (MPFB only built the file). |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | 1–2340 (39.0 s) |
| Camera | One camera, `CAM_Film`, one continuous catmull-spline move. No cuts, no camera markers. Lens animated. DOF on: focus empty `CAM_Focus`, f/8 normally, f/22 in the cutaways, f/1.2 only for the blurred-vision POV (≈21.5–22.5 s). |
| Samples | 48 adaptive, noise threshold 0.05, OpenImageDenoise |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 16. Caustics off. Persistent data on. |
| Motion blur | Off (animated look, client 22:45) |
| Colour | AgX, look "AgX - Punchy" (anim_look.py pass) |
| Output | PNG RGB 8-bit to `//render/DwarfGiant_v002_####.png` |
| Audio | No VO yet. Retime with `pipeline/retime_to_vo.py` using `beats.json`, then add the mp3 at frame 1 in the edit. |
| Caches / sims | None. Grass is a static hair-particle instance system. |
| Memory | About 11–13 GB RAM per frame on CPU. Allow 16 GB or more per node. |

Suggested test frames: 300 (brain cutaway), 740 (hand on desk), 1150 (x-ray spine), 1600 (surgery), 2250 (dusk ending).
