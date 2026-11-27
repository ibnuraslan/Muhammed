# Speed test: P1 S14 (office, low sun through blinds, Leonardo from behind, slow push)

Machine: this 4-core cloud CPU box, Blender 5.2.2 Cycles CPU. The original `shots/P1/S14.blend` is untouched;
the fast version is built on the fly by `tools/fast_render.py` (it saves a copy, never the original).

| | Original (farm settings) | Fast (self-render) |
|---|---|---|
| Time per frame | **986 s** (16.4 min, frame 40, one render) | **22.7 s average** (median 22.5, min 20.9, max 24.9; all 80 frames; whole shot 30 min 15 s wall time) |
| Output | 2560x1440 native | 960x540 rendered, then 1920x1080 via ffmpeg lanczos + unsharp 5:5:0.6 |
| Samples | 64, adaptive 0.01, OIDN | 16, adaptive 0.03, OIDN (albedo+normal, accurate prefilter) |
| Bounces | 8 total / diffuse 4 / glossy 4 / transmission 8 / volume 1 | 4 / 2 / 2 / 2 / 0, caustics off, clamp indirect 5 |
| Haze | real volume scatter (density 0.03, anisotropy 0.6) | volume hidden; compositor depth fog (screen blend, 1-exp(-0.07*Z), warm colour 0.92/0.70/0.50) + Sun Beams glare 0.12 |
| Other | motion blur 0.5 | motion blur off, persistent data on, simplify textures 1K |
| Camera, grade, composition | | identical (same camera, same compositor grade) |

At 20 spp the steady state was 27.1 s per frame, too slow. At 12 spp a still took ~19.6 s, but 16 spp was chosen as the best quality that stays inside 20–25 s.
Overall brightness and colour match the original within ~3/255 on average (the haze was calibrated region by region against the original frame).

## Visible quality losses (see S14_frame40_fast_vs_original.jpg)
- Hair: individual strands smear into a smooth "helmet" (low resolution plus the OIDN denoiser at 16 spp). This is the most noticeable loss.
- Fine texture: sweater knit, carpet and brick detail are softer; the image is overall a bit soft, even after upscaling with unsharp.
- Haze: the depth fog is uniform and lacks the sun-lit glow that the volume gave the upper blinds and the window area. The window band is ~10/255 dimmer, and the lower-left corner is slightly brighter than the original.
- Shadows and bounce light: a little less fill in dark corners (fewer diffuse bounces); no reflective caustics.
- Motion blur is gone (the slow push makes this barely visible here; fast moves and walks would show it).
- Flat walls: the frame-to-frame difference on the static wall region is 2.8/255 mean (6.2 max), partly from the camera move. I have not checked yet whether this shows as denoiser shimmer at playback.

## Files
- S14_fast_1080p.mp4: the whole shot, 80 frames, 24 fps, 1920x1080, H.264 CRF 17
- S14_frame40_fast_vs_original.jpg: frame 40, fast (left) vs original quality (right, downscaled to 1080p)
- S14_frame40_crop_fast_vs_original.jpg: a 1:1-ish crop of the head and blinds (fast left, original right)
