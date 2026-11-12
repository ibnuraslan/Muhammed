# SETTINGS — ToucanBeak (farm package)

| Setting | Value |
|---|---|
| Resolution | 1080 × 1920 (100 %), vertical |
| Frame rate | 60 fps |
| Frames | 1–2250 (37.5 s) |
| Engine | Cycles, CPU |
| Samples | 48, adaptive threshold 0.05, OpenImageDenoise |
| Motion blur | off (animated-CG look rule) |
| Colour | AgX, look "AgX - Punchy" (STYLE_ANIMATED.md) |
| Output | PNG sequence → `//render/ToucanBeak_v002_####.png` |
| Camera | one camera ("Camera"), no markers, no switching; f-stop ≥ 5.6 |
| Packing | all images packed, no linked libraries; textures ≤ 1K JPEG (PNG where alpha is used), 1K HDRI |
| File | normal git file, < 95 MB, no LFS |

Check before rendering: `blender -b --factory-startup ToucanBeak_v002_60fps.blend --python-expr "import bpy;print([i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])"` → `[]`.

Voiceover: none yet (our script). `beats.json` holds each beat's start frame; retime with `pipeline/retime_to_vo.py` (anchors = the beats.json frames).
