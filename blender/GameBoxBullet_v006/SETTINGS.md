# GameBoxBullet_v006 — farm render sheet

Values read back from `GameBoxBullet_v006_60fps.blend` opened in factory-startup Blender 5.2.2 (no add-ons).

| Item | Value |
|---|---|
| File | `GameBoxBullet_v006_60fps.blend`: 76 MB, compressed, plain git (no LFS). All images packed. |
| Blender | 5.2.2 LTS |
| Engine | Cycles, saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1500**, step 1 (25.0 s) |
| Camera | One camera, `CAM_Film`, one continuous move (keyed every frame). No cuts, no camera markers. Lens and DOF focus distance are animated (f/8, minimum f/5.6). Clip start 4 mm (macro shots). |
| Samples | 48 adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, **transparent 64** (needed for the cross-section and the jewel case), caustics off. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX, look "AgX - Punchy", exposure +0.35 (animated high-key look) |
| Output | PNG RGB 8-bit to `//render/GameBoxBullet_v006_####.png` |
| Audio | No VO yet. `beats.json` gives the beat start frames; retime with `pipeline/retime_to_vo.py` when the VO arrives, then add the mp3 at frame 1 in the edit. |
| Caches / sims | None. Debris, shards, dust and water are keyframed objects; volumes are small spheres with volume shaders (dust puffs). |
| Add-ons | None needed. |

## Measured cost
One frame (f960, cross-section with shards, 48 spp, motion blur) at 50 % resolution took **125 s** on this 4-core cloud CPU, so a full 1080×1920 frame is about 8 min here (about 200 h for 1500 frames on this machine). A farm GPU node will be far faster; run the test frames first.

Suggested test frames before approving the whole job:
- **20**: exterior, bullet streak, sprinkler, walker
- **190**: inside the wall (volumetric dust + cavity light)
- **400**: impact on the box (energy ring, flakes)
- **960**: cross-section with shards and pages (transparency depth)
- **1490**: ending, his face
