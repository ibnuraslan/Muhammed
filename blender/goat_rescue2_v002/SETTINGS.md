# GoatRescue2_v002 — farm render sheet

These values were read back from `GoatRescue2_v002_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `GoatRescue2_v002_60fps.blend`: 266 MB, compressed. All 66 images and the voiceover are packed. Stored with Git LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2100**, step 1 (35.0 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. The lens is animated. Sensor fit is Auto (36 mm). DOF is on at f/4. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | On, shutter 0.5 (180° at 60 fps) |
| Colour | Display sRGB. View AgX with the look "AgX - Medium High Contrast". Gamma 1.0. The scene exposure is keyframed for the night and day changes, so do not override it. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/GoatRescue2_v002_####.png` |
| Audio | `VO_Marcus` strip on channel 1 starting at frame 1. It is packed in the file, and a copy is `GoatRescue2_v002_VO_Marcus.mp3` (34.27 s). Image-sequence renders do not carry audio, so add this mp3 at frame 1 when you encode the video. |
| Caches / sims | None: no simulations, particles, Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 and the rigging scripts only built the file. |

## Measured cost
One full frame (1080×1920, 48 samples, motion blur) took **125 s** on this 4-core cloud CPU, which comes to about 73 h for 2100 frames locally. On a farm GPU node it should be far faster. Before you approve the whole job, run a few test frames on RenderStreet:
- **400**: farmer stuck in the heap, with mud displacement and the muck overlay
- **1100**: night, which is lit by the moon only
- **1560**: milking close-up, with fingers, udder and bottle
- **1950**: hospital through the window

If you see noise at night, raise the samples to 96 for frames 1010–1210 only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change exposure or the world settings; both are animated.
