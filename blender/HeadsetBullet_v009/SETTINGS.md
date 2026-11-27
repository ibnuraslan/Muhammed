# HeadsetBullet_v009: farm render sheet

These values were read back from `HeadsetBullet_v009_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons (see "Render check" in README.md).

| Item | Value |
|---|---|
| File | `HeadsetBullet_v009_60fps.blend`, 91 MB, compressed. Every image is packed as an 8-bit PNG, with alpha kept. The character, shirt and poster textures are 2K; the rest are 1K or smaller. The VO is packed. It's a normal git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1203**, step 1 (20.05 s, built to your voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move with no camera markers. DOF is off. The lens is animated (20–40 mm). Clip start is 4 mm for the macro. |
| Samples | 64, adaptive, noise threshold 0.05; OpenImageDenoise on |
| Light paths | Max 6: diffuse 3, glossy 3, transmission 6, transparent 16. Caustics are off. Persistent data is on. |
| Motion blur | Off |
| Colour | Filmic, look High Contrast, exposure −0.4 |
| Output | PNG, RGB, 8-bit, to `//render/HeadsetBullet_v009_####.png` |
| Audio | `HeadsetBullet_v009_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries, drivers or Python. Glass shards, chips, sparks and plaster chips are all baked keyframes. |
| Animated values | These are all keyed; don't override them:<br>• visibility of the two sets (room / ear-cup cross-section, swaps at 600 and 738)<br>• the glass and cup crack "Grow" values<br>• the cup crater shape key<br>• the wound-control empty that drives the geometry-nodes bullet track<br>• the impact-flash alpha |
| Constraints | Limit Rotation on the finger, thumb and wrist bones. IK limits on knees (0–150°), elbows and hips. Child Of on the headset (head bone until frame 935). |
| Add-ons | None needed. MPFB2 only built the file. |
