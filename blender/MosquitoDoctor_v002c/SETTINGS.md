# MosquitoDoctor_v002c: farm render sheet

| Item | Value |
|---|---|
| File | `MosquitoDoctor_v002c_60fps.blend`: compressed, every image and the VO packed; opens in factory-startup Blender 5.2.2 with no add-ons |
| Engine | Cycles, CPU or GPU; 48 samples, adaptive threshold 0.05, OpenImageDenoise |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps |
| Frame range | **1–2113**, step 1 (35.2 s; built to the voiceover) |
| Camera | One camera (`FilmCam`), with clean cuts baked into its keys and no markers |
| Motion blur | Off (the animated look) |
| Colour | AgX, look "Punchy" |
| Output | PNG sequence, written to `//render/MosquitoDoctor_v002c_####.png` |
| Audio | `MosquitoDoctor_v002c_VO.mp3` is packed as a sound strip from frame 1. Add the mp3 at frame 1 when you encode at 60 fps. |

## Test frames before the full job
- **200**: the mosquito biting (macro)
- **500**: the vial over the mosquito on the boy's hand
- **1300**: the doctor's yellow eyes
- **1650**: the organ cutaway
- **1950**: the ward with the logo crate
