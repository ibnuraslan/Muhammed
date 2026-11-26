# DonationBin_v010: farm render sheet (client-approved)

| Item | Value |
|---|---|
| File | `DonationBin_v010_60fps.blend` (78 MB, everything packed; opens in factory-startup Blender 5.2.2 with no errors) |
| Engine | Cycles, adaptive sampling up to 64 samples (threshold 0.04), OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2388** (39.8 s, built to the client's VO from the v009 sync anchors) |
| Camera | `Cam`, one continuous camera, no markers |
| Colour | AgX, look "Punchy" |
| Output | PNG to `//render/DonationBin_v010_####.png` |
| Audio | `DonationBin_v010_VO.mp3`, packed as a sound strip from frame 1 |
| Logo frames | 1–55 (bin header) and 2245–2388 (crane reveal) |
| Measured | 154–323 s per full 1080×1920 frame on a 4-core CPU without a GPU (a GPU farm node will be much faster) |

## Test frames before the full job
- **20**: the woman at the bin, with the logo
- **1200**: inside the bin, reaching up
- **2370**: the rescue and the row of bins
