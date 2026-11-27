# Tsunami2004_v013: farm render sheet

| Item | Value |
|---|---|
| File | `Tsunami2004_v013_60fps.blend` (90 MB, compressed, every image and the VO packed). It opens in factory-startup Blender 5.2.2 with no add-ons, no linked libraries, no drivers and no scripts. |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2066**, step 1 (34.4 s, built to the VO; the beats are in `beats.json`) |
| Camera | `CAM_Film`: one continuous camera, keyed every frame, no markers and no cuts |
| Sampling | Adaptive, max 28 samples, threshold 0.06, OpenImageDenoise. Bounces 4 / diffuse 2 / glossy 2 / transmission 6 / transparent 12. Caustics off, persistent data on, simplify subdivision 1, texture limit 2048. |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy" |
| Output | PNG sequence to `//render/Tsunami2004_v013_####.png` |
| Audio | `Tsunami2004_v013_VO.mp3` is packed as the sound strip at frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Measured render time (4-core CPU, no GPU, full resolution, from the packed file)
- f20: 94.2 s (the family at the water's edge)
- f1062: 85.8 s (the run, with the wall behind)
- f1840: 79.3 s (the family on the high ground at golden hour)

## The logo
DA KRAS FILMS is printed on the boy's yellow T-shirt. It reads in the beach close-ups (f1–60) and in the end close-ups (f1741–1860). The hotel's roof sign shows it in the wide beach and flood shots.
