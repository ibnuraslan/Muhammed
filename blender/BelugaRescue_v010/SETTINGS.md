# BelugaRescue_v010: farm render sheet

| Item | Value |
|---|---|
| File | `BelugaRescue_v010_60fps.blend`, 43 MB, compressed. Everything is packed, including the VO. No linked libraries, drivers or Python. Plain git, no LFS. |
| Blender | 5.2.2 |
| Engine | Cycles (saved as CPU; GPU also works) |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1736** (28.9 s), built to the VO, no retime |
| Camera | One camera, `CAM_Film`, keyed every frame, one continuous move with no cuts and no markers. It crosses the water surface between f1511 and f1512 (z −0.46 at f1508 to +0.30 at f1514). |
| Samples | **24** max, adaptive, threshold 0.05, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, **transparent 8**. Caustics off, filter glossy 1.0. **Fast GI** on (replace, AO bounces 1). Light tree off. Persistent data on. Simplify: subdivision 2, texture limit 2048. |
| Materials | No subsurface scattering (skin and beluga). The tank-floor caustics are a **static** tileable texture (`assets/tex/caustics.png`), not animated. The beluga has no subdivision modifier (the 100k-face sculpt is smooth-shaded). |
| Colour | AgX, look "AgX - Punchy", exposure −0.2 |
| Compositor | **Must stay on** (CPU device). The underwater haze is the Mist pass mixed to deep teal. `HazeAmount` is keyed (0.8 underwater, 0 from f1512). |
| Output | PNG RGB 8-bit to `//render/BelugaRescue_v010_####.png` |
| Audio | `BelugaRescue_v010_VO.mp3` packed as strip `VO` at frame 1; the same mp3 sits next to the .blend for encoding |
| Sims | None. Bubbles and splash are one geometry-nodes system (`GN_Drops`) driven by the keyed empty `FX_Clock` (never the scene clock); do not delete it. Waves ride the keyed empty `WaveCtl`. |

## Logo
DA KRAS FILMS appears on the exhibit plate above the viewing window (reads f760–1000), on her tee (many shots) and on the deck banner (f1516–1736).

## Measured render time (the exact file, `blender --factory-startup -b`, 1080×1920, 4 CPU threads, no GPU)
| Frame | Shot | Seconds |
|---|---|---|
| 20 | the dive | 112.2 |
| 400 | the cramp | 99.0 |
| 900 | the window vignette | 74.1 |
| 1250 | the foot in the mouth | 105.2 |
| 1700 | the surface | 52.0 |

All five are at or under 120 s per frame on 4 CPU cores. Expect it to be much faster on farm GPUs.
