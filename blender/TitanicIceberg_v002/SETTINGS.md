# TitanicIceberg_v002: farm render sheet

These values were read back from `TitanicIceberg_v002_60fps.blend` by `pipeline/package_for_farm.py`. The file was then reopened with `--factory-startup` in Blender 5.2.2, with no add-ons: 0 unpacked images and 1 camera.

| Item | Value |
|---|---|
| File | `TitanicIceberg_v002_60fps.blend`: 46 MB, compressed. All images are packed. It is a normal git file, with **no LFS**. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **0–1830**, step 1 (30.5 s, 1831 frames) |
| Camera | One camera, `Camera_Main`, in one continuous move. There are no camera cuts and no camera markers. Lens, f-stop and focus distance are animated, and DOF is on. Sensor 36 mm, fit Auto. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 6, volume 1, **transparent 64**. The ghost liner needs the high transparent count. Caustics off. Persistent data on. Volume step rate 4. |
| Motion blur | Off. The animated-CG look avoids heavy blur; enable it at shutter 0.5 only if the director asks. |
| Colour | Display sRGB. View AgX with the look **"AgX - Punchy"**. This is the animated-CG look from STYLE_ANIMATED.md, applied with `pipeline/anim_look.py --no-sky` plus `scripts/06_look_fix.py`. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/TitanicIceberg_v002_####.png` |
| Audio | None yet. The VO hasn't been delivered. Retime with `beats.json` and `pipeline/retime_to_vo.py`, then add the mp3 at frame 0 when you encode. |
| Animated visibility | `visible_camera` and `hide_render` are keyed (constant) on the iceberg, the rooms inside it, the prints, the cyc and the explainer props. This is how the camera flies through surfaces without a cut. Don't disable "animated visibility", and don't bake or flatten it. |
| Animated world/lights | The world mixes dawn and night (node `DayNight`), and sky strength, sun, moon, fog density and the scrape glow are all keyed. Don't override them. |
| Simulations | One particle system (sparks, frames 930–1080), computed at render time with no cache. No Alembic, no linked libraries. One driver: the Ocean modifier time (`1 + frame/60`). The farm must allow Python drivers, or the ocean freezes. |
| Add-ons | None needed. MPFB2 only built the humans. |

## Heavy frames: test these first on RenderStreet
- **240**: bright morning sky, ghost liner (64 transparent bounces) and ocean.
- **1000**: night scrape, with sparks, the glow light and SSS ice.
- **1150**: darkroom macro of the developer tray, which has liquid transmission.
- **1270**: office, with three humans, SSS skin and the desk lamp.
- **1440**: explainer cyc with the ghost hull and red band.
- **1750**: final orbit around the bright berg, with light haze.

Local cost is not measured, because the brief forbids full-resolution renders here. Review stills at 270×480 and 8 samples took about 20 s per frame on this 4-core CPU, so expect several minutes per full frame on a CPU and far less on a farm GPU. If the night frames (930–1090) show noise, raise their samples to 96.

## Do not
- Do not render any camera other than `Camera_Main`; it is the only one.
- Do not change world, exposure, fog or visibility keys.
