# Live test: timings (4-core CPU, no GPU, Blender 5.2 Cycles)

| Step | Setting | Time |
|---|---|---|
| Scene build + walk solve + keyframing (once) | 3 rigged figures with clothes, 120 frames | ~50 s |
| Render, fast preset | 960x540, 16 spp, OIDN, 120 frames | 18 min 4 s in total, **about 9.1 s per frame** (frame 1 saved at 0:59, frame 120 at 19:03) |
| Render, native | 1920x1080, 16 spp, OIDN, frame 60 only | **about 38 s** (89 s wall minus ~50 s setup), so ~4.2x the fast preset |
| Post: upscale (Lanczos + unsharp r1.2/45%) + overlay | 120 frames to 1920x1080 | 31 s in total (0.26 s per frame) |
| Encode | H.264 CRF 18, yuv420p, 24 fps | 5 s |

Whole clip end to end: about 20 minutes. At the same settings, native 1080p for all 120 frames would be about 76 min of render.

Files: `vault_live_test_1080p.mp4` (5.0 s, 120 frames), `upscaled_vs_native.jpg` (frame 60: upscaled vs native, plus a 100% crop of the lead figure and the red bag).
Scenes: `thumbnails_am/scenes/style_yellow.py` (set), `style_anim.py` (animation), `live_post.py` (upscale and overlay).
