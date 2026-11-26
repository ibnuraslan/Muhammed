# ElectricianPolice_v011: farm render sheet

These values were read back from `ElectricianPolice_v011_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `ElectricianPolice_v011_60fps.blend`: 39 MB, compressed, md5 `d912bb0c658c691cac3fc06fbc7af457`. Every image and the VO are packed. It is committed as a normal git file, with no LFS. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. |
| Resolution | 1080 x 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1-1446**, step 1 (24.1 s at 60 fps; built to the voiceover) |
| Camera | One camera, `CAM_Film`, in one continuous move, with no camera markers. DOF is off. The lens is animated (22-60 mm). |
| Samples | 64 with adaptive sampling; noise threshold 0.04 |
| Denoising | OpenImageDenoise |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. |
| Simplify | Subdivision render level 2, texture limit 2048 |
| Motion blur | Off |
| Colour | AgX with the look "AgX - Punchy". Several things are keyframed: the exposure (day 0, dusk 0.55, the dark station 0.22), the sky gradient, the world light, the sun, the street lamps and the room lights. Do not override them. |
| Output | PNG, RGB, 8-bit, written to `//render/ElectricianPolice_v011_####.png` |
| Audio | The VO strip is packed from frame 1. Add `ElectricianPolice_v011_VO.mp3` at frame 1 when you encode at 60 fps. |
| Volumes, sims, particles | None. Sparks are keyed meshes. |
| Rig constraints | Limit Rotation (hand limits) and IK. They are plain Blender constraints and need no add-on. |
| Test render | 76-111 s per 1080x1920 frame on 4 CPU cores at 16 samples. Expect a few times that at 64 adaptive samples on CPU, and much less on a farm GPU. |

## Test frames before approving the whole job
- **1:** the bike on the street (daylight).
- **723:** the control room (bright interior).
- **1046:** the arc flash and the red emergency light.
- **1220:** the dark station by candlelight. This is the darkest frame; if it is noisy, raise samples for 1162-1278 only.
- **1446:** the final close-up at dusk.
