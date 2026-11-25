# MonkeyHeadTransplant_v016: farm render sheet

These values were read back from `MonkeyHeadTransplant_v016_60fps.blend`, opened in factory-startup Blender 5.2.2.

| Item | Value |
|---|---|
| File | `MonkeyHeadTransplant_v016_60fps.blend`, 42 MB. Everything is packed: images and the VO sound. No linked libraries. Stored as plain git, no LFS. |
| Engine | Cycles. CPU or GPU both work. |
| Resolution | 1080 × 1920 at 100% |
| Frame rate | 60 fps |
| Frame range | **1–1656** (27.6 s) |
| Camera | One camera, `CAM_Film`, keyed on every frame from one monotone spline. No cuts and no markers. DOF is at f/8. |
| Samples | 48, adaptive threshold 0.05, OIDN denoise (albedo + normal passes) |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6. Caustics are off. **Transparent bounces 48**, needed for the x-ray void. Don't lower it, or black shards appear in the x-ray. |
| Speed | Persistent Data on. Simplify on: texture limit 2048 px, max subdivision 2 (the highest render level in the file, so nothing changes). |
| Motion blur | Off |
| Colour | AgX, look "AgX - Punchy". Exposure is keyframed and dims at the end, so don't override it. |
| Output | PNG, written to `//render/MonkeyHeadTransplant_v016_####.png` |
| Audio | The v012/v013 voiceover is on a sound strip from frame 1. |

## Suggested test frames
| Frame | What to check |
|---|---|
| 250 | The head carried in both hands |
| 520 | Needle holder at the seam (stitching) |
| 760 | The monkey's eyes open |
| 1020 | The x-ray void (brain, cord, gap) |
| 1360 | Oscilloscope trace and the surgeon |
| 1640 | Ending: the lids droop and the light dims |

## Do not
- Change the exposure.
- Change the `XRay`, `VoidOn` or `VoidFade` shader values. They are animated.
- Render any camera other than `CAM_Film`.

## Logo (DA KRAS FILMS)
| Where | Readable frames |
|---|---|
| Print on the front of the surgeon's scrub cap (white logo) | 611–796 (3.1 s, large), also 81–200 and 391–456. Smaller but whole from 1086 to the end. |
| Label strip on the oscilloscope front (white logo) | in view at about 1150–1440, small (a second placement) |

## Measured render time (this container: 4 CPU cores, no GPU)
Full 1080×1920, from the packed file: frame 1 = 180 s, frame 828 = 180 s, frame 1656 = 175 s.
