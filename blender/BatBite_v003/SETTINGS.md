# BatBite_v003: farm render sheet

| Item | Value |
|---|---|
| File | `BatBite_v003_60fps.blend`: compressed, every image and the VO packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU, 64 samples + OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1362**, step 1 (22.7 s; built to the voiceover, no retime) |
| Camera | One camera (`FilmCam`), hard cuts baked into its keys, no markers |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/BatBite_v003_####.png` |
| Audio | `BatBite_v003_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Cuts (first frame of each shot)
1, 95, 150, 276, 349, 386, 416, 460, 494, 599, 712, 843, 929, 1029, 1093, 1239 — see `beats.json`.

## Test frames before the full job
- **120**: the bat landing by the singer (crowd behind)
- **480**: the profile bite (bat head at the lips)
- **760**: the shock close-up
- **1300**: the oxygen-mask close-up
