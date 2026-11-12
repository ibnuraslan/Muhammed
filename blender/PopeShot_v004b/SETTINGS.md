# PopeShot: farm settings

| | |
|---|---|
| File | `PopeShot_v004b_60fps.blend` (self-contained: every texture and the HDRI are packed, no linked libraries) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 (9:16), 100 % |
| Frame rate | 60 fps |
| Frames | 1 – 1620 (27.0 s) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | off (animated look) |
| Colour | AgX, look "Punchy" (STYLE_ANIMATED.md) |
| Camera | one camera, `CAM` (no markers, no camera switching), DOF focused on `CamFocus` |
| Output | PNG sequence to `//render/PopeShot_v004b_####.png` |

## Suggested test frames before the full job
- 130: square, the Pope waving from the jeep, crowd and flags
- 300: slow-motion bullet ride
- 380: torso x-ray inside the teal-navy dome
- 560: collapse into the aides' arms
- 700: operating theatre from above
- 960: balcony blessing
- 1100: cell: the two men face to face
- 1330: crown macro with the bullet seated
- 1450: closing x-ray (the curved path past the aorta)

## Heavy parts
- Volumes: light haze in the cell and the shrine (`CellHaze`, `ShrineHaze`), so frames 1015–1620 render a little slower.
- About 80 MPFB crowd people in the square (frames 1–640) and below the balcony (700–1015).
- Voiceover: not supplied yet. The timing follows the brief's beat table (`beats.json`). Retime with `pipeline/retime_to_vo.py` when the VO arrives.
