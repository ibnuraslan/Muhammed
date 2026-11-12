# BeethovenDeaf_v009: farm render sheet

These values were read back from `BeethovenDeaf_v009_60fps.blend`, opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `BeethovenDeaf_v009_60fps.blend`: 93 MB, compressed. All 43 images are packed. Stored as a regular git file, not LFS: the LFS upload was refused (403) from this session, and 93 MB is under GitHub's 100 MB limit. |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU, but GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1590**, step 1 (26.5 s) |
| Camera | One camera, `CAM_Film`, in one continuous move. There are no camera cuts or camera markers. Lens and f-stop are animated: f/5.6 on wide shots, f/8–11 on macro. DOF focuses on `CAM_Film_Aim`. |
| Samples | 48 with adaptive sampling; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, **transparent 32**. Keep transparent at 32: the X-ray ghosting stacks transparent layers. Caustics off. Persistent data on. |
| Motion blur | **Off**, per the animated look |
| Colour | Display sRGB. View AgX with the look **"AgX - Punchy"**. **Exposure +0.25.** |
| Output | PNG, RGB, 8-bit, written to `//render/BeethovenDeaf_v009_####.png` |
| Audio | None yet; no VO has been supplied. Lay the VO at frame 1 when encoding, after the retime (see README). |
| Caches / sims | None: no simulations, physics caches, Alembic, linked libraries or drivers. |
| Hair | One legacy particle hair system (`WildHair` on `Composer.short02`): 420 guide hairs × 40 interpolated children, with no dynamics. It is switched off by a keyframe during the X-ray (f612–1150). |
| Add-ons | None needed. MPFB2 only built the file. |

## Measured cost
These were measured on this 4-core cloud CPU at 25 % resolution (270×480), with 48 samples and motion blur:
- f40 (macro of the face and hair): 26 s, which includes first-frame scene load
- f650 (X-ray studio): 20 s
- f1500 (overhead room): 14 s

Full resolution has 16× the pixels, so expect roughly 4–8 min per frame on CPU, or about 110–200 h for 1590 frames. On a farm GPU node it should be far faster.

Before you approve the whole job, run these test frames:
- **40**: macro of the teeth on the rod, with particle hair in the foreground
- **620**: X-ray transition, where the glass-ghost skin dissolves into the studio. This is the heaviest transparency frame.
- **1020**: torn eardrum, with a red pulse and cyan rings
- **1500**: overhead room with 13 candles. Check the candle-light noise; if it is noisy, raise the samples to 96 for frames 1207–1590 only.

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not lower the transparent bounces below 32.
- Do not change exposure or the X-ray / backdrop node values; they are animated.
