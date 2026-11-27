# CaveRescue_v012: farm render sheet

| Item | Value |
|---|---|
| File | `CaveRescue_v012_60fps.blend` (90.4 MB, compressed, all images and the VO packed, no linked libraries). It opens in Blender 5.2.2 with no add-ons. |
| Engine | Cycles, CPU or GPU, 12 samples, adaptive threshold 0.08, OpenImageDenoise |
| Bounces | max 3 (diffuse 1, glossy 1, transmission 3, transparent 8), caustics off, Persistent Data on |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2436**, step 1 (40.6 s, built to the voiceover) |
| Camera | `CAM_Film`: one continuous camera, no cuts |
| Motion blur | Off |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, `//render/CaveRescue_v012_####.png` |
| Audio | `CaveRescue_v012_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |
| Measured render time | 59.9 s (f1), 107.5 s (f1200), 98.8 s (f1950), 68.4 s (f2436) per frame on a 4-core CPU with no GPU |

## Logo frames
- DA KRAS FILMS on the rescuers' navy gear bag in the chamber: f1470–1600.
- DA KRAS FILMS on the ambulance side: f2150–2436.

## Test frames before the full job
- **300**: the walk into the cave
- **1200**: the diver at the restriction (the slowest frame)
- **1650**: the injection
- **1950**: the tow under water
- **2350**: the carry-out and the ambulance with the logo
