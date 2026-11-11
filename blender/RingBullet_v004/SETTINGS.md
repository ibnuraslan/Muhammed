# RingBullet: render settings (farm)

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | 1–1410 (23.5 s) |
| Engine | Cycles, CPU |
| Samples | 48, adaptive threshold 0.05 |
| Denoiser | OpenImageDenoise |
| Bounces | max 8, diffuse 3, glossy 3, transmission 6, volume 0 |
| Caustics | off |
| Motion blur | off (animated look) |
| Colour | AgX, Punchy, exposure +0.6 (animated look) |
| Texture limit | 2048 |
| Output | PNG, 8-bit RGB, `//render/RingBullet_v004_####.png` |
| Camera | one camera (`Cam`), no markers. Depth of field is on, with focus distance and f-stop keyed per frame. |

Notes:
- The muzzle smoke is a small volume (Principled Volume) that is only visible in frames 30–540. Volume bounces are 0, which keeps it cheap.
- The rain, dust and window drops run on a keyed world-time property (`TimeCtl["wt"]`) through drivers, so the slow-motion section also slows the rain. Drivers use simple expressions only, so they need no Python auto-run.
- Persistent data is on.

## Package check (factory startup)
- `blender -b --factory-startup RingBullet_v004_60fps.blend` opens with **0 unpacked images**, one camera (`Cam`), no timeline markers, and no linked libraries. `package_check_factory_f36_f1020_f1258_lowres.jpg` shows two frames rendered from the packed file (f36 pistol + muzzle shake, f1020 bookshelf dust, f1258 desk, lamp, bandage) at 270×480 and 8 samples.
- Size: 58 MB, compressed, all textures packed. Textures are 1K, except the owner's skin and suit diffuse maps at 2K. The HDRI is 2K.
- Rendering needs no Python auto-run. The drivers are simple expressions reading `TimeCtl["wt"]`.

## Look (v004)
The client's animated-CG look (`blender/STYLE_ANIMATED.md`) was applied with `pipeline/anim_look.py` and then `RingBullet_v001/scripts/04_anim_fix.py`. The review sheet is `v004_animated_look_1s.jpg` (1 still per second, 270×480, 8 samples).
