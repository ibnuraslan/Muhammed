# BelugaRescue_v009: farm render sheet

| Item | Value |
|---|---|
| File | `BelugaRescue_v009_60fps.blend`, 42 MB, compressed. Everything is packed, including the VO. No linked libraries, drivers or Python. Plain git, no LFS. |
| Blender | 5.2.2 |
| Engine | Cycles (saved as CPU; GPU also works) |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–1736** (28.9 s), built to the VO, no retime |
| Camera | One camera, `CAM_Film`, keyed every frame, one continuous move with no cuts and no markers. It crosses the water surface at f1531. |
| Samples | 64 max, adaptive, threshold 0.05, OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Simplify: subdivision 2, texture limit 2048. |
| Colour | AgX, look "AgX - Punchy", exposure −0.2 |
| Compositor | **Must stay on** (CPU device). The underwater haze is the Mist pass mixed to deep teal. `HazeAmount` is keyed (0.8 underwater, 0 from f1531). |
| Output | PNG RGB 8-bit to `//render/BelugaRescue_v009_####.png` |
| Audio | `BelugaRescue_v009_VO.mp3` packed as strip `VO` at frame 1; the same mp3 sits next to the .blend for encoding |
| Sims | None. Bubbles and splash are one geometry-nodes system (`GN_Drops`) driven by the keyed empty `FX_Clock` (never the scene clock); do not delete it. Waves ride the keyed empty `WaveCtl`. |

## Logo
DA KRAS FILMS appears on the exhibit plate above the viewing window (f1–1000, reads f760–1000), on her tee (many shots) and on the deck banner (f1536–1736).

## Test frames
20 (the dive), 400 (the cramp), 900 (the window vignette), 1250 (the foot in the mouth), 1700 (the surface).

## Measured render time
4-core CPU, no GPU: f20 644 s, f900 547 s, f1700 297 s. Expect it to be much faster on farm GPUs.
