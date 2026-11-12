# HeadsetBullet_v006: farm render sheet

These values were read back from `HeadsetBullet_v006_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `HeadsetBullet_v006_60fps.blend`: 74 MB, compressed. Every image is packed (no unpacked or dirty images). Textures are 1K (the face skin is 2K), the HDRI is 1K, opaque maps are JPEG q92, and alpha maps are 8-bit PNG. It is a normal git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1500**, step 1 (25.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. Track To → `CAM_Film_Aim`; DOF focus object `CAM_Film_Focus`. The lens (24–55 mm) and f-stop are animated. The f-stop is at least 5.6, except at least 4 for the macro at the ear cup (f600–960). Clip start is 4 mm for the macro moments. Sensor fit is Auto (36 mm). |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | **Off** (animated look, client 22:45 UTC) |
| Colour | Display sRGB. View AgX with the look **"AgX - Punchy"**. Exposure +0.15. |
| Output | PNG, RGB, 8-bit, written to `//render/HeadsetBullet_v006_####.png` |
| Audio | None packed yet: the VO hasn't been supplied. After the retime, lay the mp3 at frame 1 when encoding. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. Glass shards, debris, sparks and dust are all baked as keyframes. |
| Animated material and modifier values | Screen panning and flicker, the LED strip hue, the crack radius, the dying RGB ring, the cutaway Boolean on/off (frames 815–975, EXACT solver) and the curtain wave. All are keyframed; do not override them. |
| Constraints | 32 Limit Rotation constraints (local) on the finger, thumb and wrist bones. They are evaluated live, so keep them on. |
| Add-ons | None needed. MPFB2 only built the file. |

## World
Camera rays see a sky-blue gradient (cyan to near-white, from `pipeline/anim_look.py`). Lighting still comes from the HDRI at 1.6× strength.

## Measured cost
Measured on v002 (v005 adds a few lights, so it is slightly slower): one full frame (f700: 1080×1920, 48 samples, motion blur, the macro with DOF) took **5 min 23 s** on this 4-core cloud CPU. That is about 135 h for 1500 frames locally, so render on the farm GPU nodes.

Suggested test frames on RenderStreet before you approve the whole job:
- **40**: exterior chase, with the bullet at 12 cm, the HDRI sky, the tree and the car
- **150**: the camera flying through the shard cloud (glass transmission, 183 shards)
- **860**: the cutaway Boolean on the cup, with the cyan rim light
- **975**: ricochet sparks and the point-light flash
- **1335**: face close-up (skin SSS, eyes)
