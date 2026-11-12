# AIAsleep v002: farm settings

- File: `AIAsleep_v002_60fps.blend` (everything packed, compressed; opens in factory Blender 5.2.2)
- Engine: Cycles, CPU or GPU. 48 samples, adaptive threshold 0.05, OpenImageDenoise.
- 1080×1920, 100 %, 60 fps, frames 1–2610 (43.5 s).
- Colour: AgX, look "AgX - Punchy" (animated-CG look, STYLE_ANIMATED.md).
- Motion blur OFF (style rule). Depth of field on, f/5.6 or higher everywhere (f/18 on the eye macros); focus follows `CamAim`.
- One camera (`FilmCam`), no camera markers.
- Compositing ON: a node group grades the AI's-eye infrared look (frames ~1532–1752). It is set to compositor device CPU; on the farm it works on CPU or GPU.
- Output: `//render/AIAsleep_v002_####` (set your format on the farm; PNG/EXR recommended).
- No voiceover yet: retime with `pipeline/retime_to_vo.py` using `beats.json` once the VO arrives.
