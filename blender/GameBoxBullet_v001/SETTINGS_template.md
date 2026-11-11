# GameBoxBullet_v002 — farm render sheet

Values read back from `GameBoxBullet_v002_60fps.blend` opened in factory-startup Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `GameBoxBullet_v002_60fps.blend`: __SIZE__ MB, compressed, plain git (no LFS). All images packed. |
| Blender | 5.2.2 LTS |
| Engine | Cycles, saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1500**, step 1 (25.0 s) |
| Camera | One camera, `CAM_Film`, one continuous move (keyed every frame). No cuts, no camera markers. Lens and DOF focus distance are animated (f/8). Clip start 4 mm (macro shots). |
| Samples | 48 adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, **transparent 64** (needed for the cross-section and the jewel case), caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 |
| Colour | AgX, look "AgX - Medium High Contrast" |
| Output | PNG RGB 8-bit to `//render/GameBoxBullet_v002_####.png` |
| Audio | No VO yet. `beats.json` gives the beat start frames; retime with `pipeline/retime_to_vo.py` when the VO arrives, then add the mp3 at frame 1 in the edit. |
| Caches / sims | None. Debris, shards, dust and water are keyframed objects; volumes are small spheres with volume shaders (dust puffs). |
| Add-ons | None needed. |

## Measured cost
__COST__

Suggested test frames before approving the whole job:
- **20**: exterior, bullet streak, sprinkler, walker
- **190**: inside the wall (volumetric dust + cavity light)
- **400**: impact on the box (energy ring, flakes)
- **960**: cross-section with shards and pages (transparency depth)
- **1490**: ending, his face
