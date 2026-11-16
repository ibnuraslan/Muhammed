# LakeSword_v002: farm render sheet

Read back from `LakeSword_v002_60fps.blend` with `pipeline/package_for_farm.py` (Blender 5.2.2, no add-ons): no problems reported.

| Item | Value |
|---|---|
| File | `LakeSword_v002_60fps.blend`: compressed, every image and the VO packed, a normal git file (no LFS) |
| Blender | 5.2.2 |
| Engine | Cycles. Saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1826**, step 1 (30.4 s, synced to the voiceover) |
| Camera | One camera, `CAM_Film`. The 17 hard cuts are baked into its keys; no camera markers. Lens, focus and f-stop are keyed. |
| Samples | 48, adaptive, noise threshold 0.05. Denoising on (OpenImageDenoise). |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "AgX - Punchy" |
| Output | PNG sequence, `//render/LakeSword_v002_####.png` |
| Audio | `LakeSword_v002_VO.mp3` is packed as a sound strip at frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Sims and caches | None. No drivers, no linked libraries, no Scene Time nodes, no particles. Water ripples and fire flicker are keyed values. |

## Test frames before the full job
- **300**: the girl's hand on the hilt under the water (shot 04).
- **520**: the girl holding the sword upright (06).
- **900**: the museum with the logo banner (10).
- **1380**: the leather-sheath macro (14).
- **1500**: the warrior at the camp (15).
