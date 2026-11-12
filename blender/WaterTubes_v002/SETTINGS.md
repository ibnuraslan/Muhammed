# WaterTubes: render settings (farm)

| Setting | Value |
|---|---|
| File | `WaterTubes_v002_60fps.blend` (packed, compressed, opens in factory Blender 5.2) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frames | 1 – 2010 (33.5 s) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | off (animated-CG look, client 22:45) |
| Colour | AgX, look "Punchy" (animated-CG look) |
| Camera | one camera (`Camera`), no markers, no cuts |
| Output | PNG sequence at `//render/WaterTubes_v002_####.png` |
| Audio | none yet; the VO will be retimed with `pipeline/retime_to_vo.py` using `beats.json` |

## Notes for the farm
- All effects (tube filling, flood surface, rain, spray) are **geometry nodes driven by scene time and keyed values**. There are no simulation caches to bake, and every frame renders independently.
- The cutaway shell is visible to camera rays only (it doesn't light the set).
- The heaviest frames are the flood aerials (beats 7 and 11: water with subdivision, about 14k rain streaks). The budget is roughly the same as the rest of the film.
