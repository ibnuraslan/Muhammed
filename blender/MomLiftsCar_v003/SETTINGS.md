# MomLiftsCar_v003: render settings

- File: `MomLiftsCar_v003_60fps.blend` (all textures and the VO packed)
- Resolution 1080×1920, 100%, 60 fps
- **Frame range 1–1577** (VO speech 0.00–25.76 s; frame_end 0.5 s after the last word)
- Engine Cycles, 48 samples, adaptive threshold 0.05, OpenImageDenoise
- Colour: AgX, look "AgX - Punchy"; motion blur off
- One camera: `CAM_Film` (the hard cuts are baked as per-frame CONSTANT keys; no camera markers)
- Output: PNG sequence to `//render/MomLiftsCar_v003_`; the VO is in the sequencer (strip "VO", frame 1)
