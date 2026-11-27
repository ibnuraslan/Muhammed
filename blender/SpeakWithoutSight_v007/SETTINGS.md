# SpeakWithoutSight_v007: farm render sheet

These values are read back from `SpeakWithoutSight_v007_60fps.blend` opened in factory-startup Blender 5.2.2.

| Item | Value |
|---|---|
| File | `SpeakWithoutSight_v007_60fps.blend`: 55 MB, compressed, every image and the VO packed. A normal git file, not LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100% |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1645**, step 1 (27.4 s, synced to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move with no cuts. DOF is on at f/8, focused on `CAM_Film_Aim`. |
| Samples | 64, adaptive, noise threshold 0.04, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. |
| Colour | AgX, look "AgX - Punchy" |
| Output | PNG to `//render/SpeakWithoutSight_v007_####.png` |
| Audio | `SpeakWithoutSight_v007_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Simulations | None: no particles, cloth, caches, drivers, scripts or linked libraries. |
| Keyed values | Light energies, the world strength, the window's season and daylight, the throat ripples and the pulse dots are keyed. Do not override them. |

## Logo
The DA KRAS FILMS logo is framed on the parlour wall. It is readable in the opening wide (f1–130) and again in the time-lapse and finale (f1359–1645).

## Test frames (measured, 4-core CPU, no GPU)
See the "Render check" block in README.md.
