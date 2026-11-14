# WW1Assassination_v005: farm render sheet

These values are read back from `WW1Assassination_v005_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `WW1Assassination_v005_60fps.blend`: 90.9 MB (87 MiB), compressed. Every image is packed. Committed as a normal git file, with no LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2130**, step 1 (35.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. The lens and f-stop are animated (f-stop is never below 5.6), and DOF focuses on `CAM_Film_Aim`. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transparent 8. Volume step rate 4. Persistent data on. |
| Motion blur | Off (animated look) |
| Colour | AgX, look "AgX - Punchy" (client's animated-CG look). **Exposure and white balance are keyframed** (rewind tint 7–10 s, blast and muzzle-flash blips, map darker), so do not override them. |
| Compositing | Off. No compositor is used, because it needs a GPU context headless. |
| Output | PNG, RGB, 8-bit, written to `//render/WW1Assassination_v005_####.png` |
| Audio | None yet. The VO is pending; `beats.json` has the beat start frames for `pipeline/retime_to_vo.py`. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Everything is baked keyframes. Visibility switches (city ↔ map at frame 1748) are keyed `hide_render`. |
| Add-ons | None needed. |

## Measured cost
One full frame of v002 (frame 120: 1080×1920, 48 samples, with motion blur) rendered from its packed file in factory Blender took **260 s** on this 4-core cloud CPU, which comes to about 154 h for 2130 frames locally. On a farm GPU node it should be far faster. v005 has motion blur off, so it should be a little faster.
- The map frames (1748–2130) are cheaper: there are no humans, and the plumes are alpha cards.
- The explosion frames (about 930–1100) and the cloud wipe (1680–1800) carry volumes and are the slowest.

Before you approve the whole job, run these test frames:
- **120**: the car turning the corner, with crowd, bunting and the couple
- **950**: the explosion: volumes, the fireball light and debris
- **1460**: the gunman over the shoulder, with DOF
- **1748**: the cloud whiteout and the city→map swap
- **2050**: the burning map, with volume plumes

If the smoke or clouds are noisy, raise the samples to 96 for frames 930–1100 and 1680–1800 only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure, white balance or the world settings; all three are animated.
- Do not re-enable compositing.
