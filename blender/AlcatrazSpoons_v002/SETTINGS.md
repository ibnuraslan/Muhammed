# AlcatrazSpoons_v002: farm render sheet

Read back from `AlcatrazSpoons_v002_60fps.blend` with `pipeline/package_for_farm.py` (Blender 5.2.2, no add-ons).

| Item | Value |
|---|---|
| File | `AlcatrazSpoons_v002_60fps.blend`: compressed, every image packed, a normal git file (no LFS) |
| Blender | 5.2.2 |
| Engine | Cycles. Saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2007**, step 1 (33.4 s, synced to the voiceover) |
| Camera | One camera, `CAM_Film`. The 24 hard cuts are baked into its keys; there are no camera markers. Lens, focus and f-stop are keyed. |
| Samples | 48, adaptive, noise threshold 0.05. Denoising on (OpenImageDenoise). |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "AgX - Punchy" |
| Output | PNG sequence, `//render/AlcatrazSpoons_v002_####.png` |
| Audio | `B07_AlcatrazSpoons_VO.mp3` is packed as a sound strip at frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Sims and caches | None. No drivers, no linked libraries, no Scene Time nodes. |

## Test frames before the full job
- **150**: the trio in the cell (shot 1b).
- **330**: P1 scraping at the vent, face toward the camera (2a).
- **1300**: the corridor with the logo crate (5d).
- **1700**: the raft on the bay (7b).
