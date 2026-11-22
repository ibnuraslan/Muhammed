# GameBoxBullet_v011 — farm render sheet

Values read back from `GameBoxBullet_v011_60fps.blend` opened in factory-startup Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `GameBoxBullet_v011_60fps.blend`: 72 MB, compressed, plain git (no LFS). All images packed. |
| Blender | 5.2.2 LTS |
| Engine | Cycles, saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1311**, step 1 (21.85 s, built to the VO) |
| Camera | One camera, `CAM_Film`. 19 hard cuts (20 shots) are baked into its keys (constant interpolation, keyed every frame), with no camera markers. Lens, f-stop (min f/8, f/11–16 on macros) and focus are animated. Clip start 1 cm. |
| Samples | 48 adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, **transparent 64** (needed for the cross-section and the jewel case), caustics off. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX, look "AgX - Punchy", exposure +0.35 (animated high-key look) |
| Output | PNG RGB 8-bit to `//render/GameBoxBullet_v011_####.png` |
| Audio | `GameBoxBullet_v011_VO.mp3` (the director's VO). Lay it at frame 1 in the edit. Beats are in `beats.json`. |
| Caches / sims | None. Debris, shards, dust and water are keyframed objects; volumes are small spheres with volume shaders (dust puffs). |
| Add-ons | None needed. |

## Test frames before approving the whole job
- **10**: the shooter, muzzle flash
- **105**: exterior wall break, splinters (volumes)
- **525**: impact, side profile, hand on the box
- **720**: cross-section with disc shards and rings (transparency depth)
- **1300**: ending, his face and the logo poster
