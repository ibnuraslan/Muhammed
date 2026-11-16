# PaperclipHouse_v002b: farm render sheet

| Item | Value |
|---|---|
| File | `PaperclipHouse_v002b_60fps.blend` : compressed, every image and the VO packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU; 48 samples, adaptive threshold 0.05, OIDN denoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2000**, step 1 (33.3 s; built to the voiceover, ending 0.5 s after the last word) |
| Camera | One camera (`Camera`), with hard cuts baked into its keys and no markers |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/PaperclipHouse_v002b_####.png` |
| Audio | `PaperclipHouse_v002b_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Test frames before the full job
- **60**: kitchen counter handshake (paperclip and fish pen on the counter)
- **700**: garage, the blue snowmobile presented
- **1000**: the van-side logo
- **1180**: the condo handshake at the brick house
- **1950**: the house reveal
