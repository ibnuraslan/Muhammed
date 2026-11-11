# RooseveltSpeech_v004: farm settings

| Setting | Value |
|---|---|
| File | `RooseveltSpeech_v004_60fps.blend` (packed, compressed) |
| Engine | Cycles, CPU or GPU |
| Resolution | 1080 × 1920, 100 % |
| Frame rate | 60 fps |
| Frames | 1–1500 (25.0 s) |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | off (animated look) |
| Colour | AgX, look "Punchy", exposure +0.45 |
| Camera | one camera, `Cam`, with no markers or switching |
| Output | `//render/RooseveltSpeech_v004_####.png` |

Notes for the farm:
- Particle hair (the moustache) and volumetric gun smoke are in the scene. Both render in Cycles with no baking.
- Breath vapour (small volumes) renders in Cycles with no baking.
- Set visibility is keyed with `hide_render`:
  - The street is visible from frame 1 to 505.
  - The studio dome and cutaway are visible from frame 460 to 1205.
  - The hall is visible from frame 1165.
  - Render from the .blend as it is. Do not override visibility.
- Voiceover:
  - When the VO mp3 arrives, run `blender/pipeline/retime_to_vo.py` with anchors from `beats.json` (the beat start frames below).
  - It warps every keyframe so each beat starts on its first word, then adds the VO strip.
- Beat start frames: 1, 187, 337, 445, 721, 877, 1003, 1189, 1285.
