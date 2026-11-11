# SETTINGS — EscapeArtist (farm)

| Setting | Value |
|---|---|
| File | `EscapeArtist_v002_60fps.blend` (everything packed, compressed) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frames | 0 – 3750 (62.5 s) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | on, shutter 0.5 |
| Colour | AgX, look "Medium High Contrast" |
| Camera | one camera, `CAM_Main`, no markers or camera switching |
| Output | PNG sequence, `//render/EscapeArtist_v002_####.png` |
| Particles | sparks (beat 2), filings (beat 10), dust motes: baked in the cache from frame 0 if the farm resimulates; seeds are fixed |

Voiceover: none supplied yet. `beats.json` holds the beat start frames for `pipeline/retime_to_vo.py` once the VO arrives.
