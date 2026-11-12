# GoatOwner_v003: farm render sheet

These values were read back from `GoatOwner_v003_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons. The full list is printed by `pipeline/package_for_farm.py`.

| Item | Value |
|---|---|
| File | `GoatOwner_v003_60fps.blend`. Its size is in README.md. It is compressed and is a normal git file (no LFS). Every image is packed. Textures are ≤1K JPEG (PNG only where alpha is needed), and the HDRI is 2K. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–2190**, step 1 (36.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous baked move. There are no camera cuts or camera markers. Lens and focus distance are animated. DOF is on at f/5.6. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | **Off**, per the studio look rule `STYLE_ANIMATED.md`: no heavy motion blur. |
| Colour | Display sRGB. View AgX with the look **"AgX - Punchy"**. Exposure 0.15, gamma 1.0. The sun, sky tint, sky strength and sky rotation are keyed (time-lapse in beat 3, golden pasture in beat 11), so do not override the world or the lights. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/GoatOwner_v003_####.png` |
| Audio | None packed yet. The voiceover has not been supplied. Retime with `pipeline/retime_to_vo.py` using `beats.json`, then add the VO at frame 1 when encoding. |
| Caches and sims | None. There are 3 hair particle systems that instance Poly Haven grass clumps; they are deterministic and need no bake. There are no Alembic files, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 and the rigging scripts were only used to build the file. |

## Test frames to try first on RenderStreet
- **700**: goat head close-up (beat 4), checks fur and eye detail.
- **960**: the first ram impact in slow motion, with dust burst and both characters.
- **1600**: the wide crane over the yard, with the body lying still and dust settling.
- **2150**: sanctuary close-up of the hand-feeding, under golden light.

## Do not
- Do not render any camera other than `CAM_Film`; it is the only one.
- Do not change the exposure, world or sun; all three are animated.
