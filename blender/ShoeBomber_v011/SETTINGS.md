# ShoeBomber_v011: render sheet (READY; client-approved)

| Item | Value |
|---|---|
| Frame range | **1–1469** at 60 fps |
| Resolution | 1080x1920 at 100% |
| Engine | Cycles CPU/GPU: 64 samples, adaptive threshold 0.04, OIDN (albedo + normal) |
| Light paths | max 6, diffuse 3, glossy 3, transmission 6, transparent 16; caustics off |
| Performance | Persistent Data on; Simplify subdivision 2; texture limit 2048 |
| Colour | Filmic, High Contrast. Exposure is keyed per set: −0.2 cabin, 0 studio, −0.65 sky, −0.45 airport. |
| Camera | `CAM_Film` only (Track To `CAM_Film_Aim`), f/11 |
| Output | PNG to `//render/ShoeBomber_v011_####.png`. The VO strip is packed at frame 1. |
| Logo frames | bulkhead 210–255, fuselage 985–1095, tray 1141–1225 |
| Test frames | 1, 735 and 1469 render clean from the packed file. Measured on a 4-core CPU with no GPU: 296 s, 364 s and 162 s per frame. |
| File | `ShoeBomber_v011_60fps.blend`: 50.4 MB, everything packed, a plain git file |
