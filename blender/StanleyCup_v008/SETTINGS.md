# StanleyCup_v008 — farm render sheet

Values read back from `StanleyCup_v008_60fps.blend` opened in factory-startup Blender 5.2.2 with no add-ons.

| Item | Value |
|---|---|
| File | `StanleyCup_v008_60fps.blend`: 67 MB, compressed. All images packed: characters, floor and wall colour at 2K; props, set dressing and all normal/roughness maps at 1K (JPEG q90, alpha masks PNG). Stored as a normal Git file (under 100 MB; the LFS upload was refused tonight). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. Device saved as CPU; GPU is fine. No special features. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1386**, step 1 (23.1 s at 60 fps; synced to the voiceover) |
| Camera | One camera, `CAM_Film`, one continuous move. No camera cuts or camera markers. Lens and f-stop are animated (16–70 mm, f/5.6–11; f/4 only on the impact and condensation macros); DOF on, focus object `CAM_Film_Aim`. Clip start 2 mm (the camera flies through a bullet hole). |
| Samples | 48, adaptive, noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated look, per STYLE_ANIMATED.md) |
| Colour | Display sRGB. View AgX, look "AgX - Punchy". Exposure keyed: +0.25 on the street, −0.05 in the room (ramp f160–240). Gamma 1.0. |
| Output | PNG, RGB, 8-bit, compression 15, written to `//render/StanleyCup_v008_####.png` |
| Audio | None yet (VO not supplied). |
| Caches / sims | None. The lawn grass is a hair particle system (no cache needed). Booleans (bullet holes) and the Wave modifier (ripples) evaluate per frame. No Alembic, linked libraries or drivers. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Measured cost
Measured on v003 (same geometry, with motion blur): one full frame (f700, 1080×1920, 48 samples, macro DOF on the tumbler) took **399 s** on this 4-core cloud CPU while other jobs shared it; expect roughly 4–6 min per frame on 4 CPU cores, i.e. about 100–150 h for 1530 frames locally. A farm GPU node should be far faster. Run the test frames below first.

## Suggested test frames
- **200**: inside the wall cavity, lit only by the light leaking through the hole (check noise).
- **250**: looking through the drywall hole at the couple.
- **985**: impact sparks with motion blur (brightest frame).
- **1100**: x-ray of the tumbler (transparent shaders, water).
- **1500**: her gripping the dented tumbler (faces, hands).

## Do not
- Do not render other cameras; `CAM_Film` is the only one.
- Do not change the exposure or the world; the exposure and the light keys are animated for the move.

> **Note (voiceover sync):** frame counts in the time estimate and the test-frame numbers above come from the version before the sync. The film is now the range in the table at the top. Any test frame inside that range is fine to render.
