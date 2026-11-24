# MonkeyHeadTransplant_v014: farm render sheet

These values were read back from `MonkeyHeadTransplant_v014_60fps.blend`, opened in factory-startup Blender 5.2.2.

| Item | Value |
|---|---|
| File | `MonkeyHeadTransplant_v014_60fps.blend`, 43 MB. Everything is packed: images and the VO sound. No linked libraries. Stored as plain git, no LFS. |
| Engine | Cycles. CPU or GPU both work. |
| Resolution | 1080 × 1920 at 100% |
| Frame rate | 60 fps |
| Frame range | **1–1656** (27.6 s) |
| Camera | One camera, `CAM_Film`, keyed on every frame from one monotone spline. No cuts and no markers. DOF is at f/8. |
| Samples | 48, adaptive threshold 0.05, OIDN denoise |
| Light paths | Max 12 bounces. **Transparent bounces 48**, needed for the x-ray void. Don't lower it, or black shards appear in the x-ray. |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy". Exposure is keyframed and dims at the end, so don't override it. |
| Output | PNG, written to `//render/MonkeyHeadTransplant_v014_####.png` |
| Audio | The v012/v013 voiceover is on a sound strip from frame 1. |

## Suggested test frames
| Frame | What to check |
|---|---|
| 250 | The head carried in both hands |
| 520 | Needle holder in the fist, stitching the seam |
| 760 | The monkey's eyes open |
| 1020 | The x-ray void (brain, cord, gap) |
| 1360 | Oscilloscope trace and the surgeon |
| 1640 | Ending: the lids droop and the light dims |

## Do not
- Change the exposure.
- Change the `XRay`, `VoidOn` or `VoidFade` shader values. They are animated.
- Render any camera other than `CAM_Film`.
