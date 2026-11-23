# BellyFat_v013: farm render sheet

I read these values back from `BellyFat_v013_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `BellyFat_v013_60fps.blend`: 74 MB, compressed. Everything is packed, including the VO; there are no linked libraries and no drivers. Images are 1K, except the woman's skin and hair at 2K. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU also works, and no special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1273**, step 1 (21.2 s). This is the v010 range, built straight to the VO. |
| Camera | One camera, `CAM_Film`, keyed on every frame. It makes **hard cuts** between 8 shots (no blends); the cross-section is one continuous push. Lens, clip start, focus distance, f-stop and DOF on/off are keyed per frame. In the macro shots the clip start is set to 55 % of the subject distance, so nothing can block the lens. |
| Samples | 48, adaptive; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off |
| Colour | Display sRGB, view AgX, look "AgX - Punchy", exposure −0.3 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/BellyFat_v013_####.png` |
| Audio | The VO (`BellyFat_v013_VO.mp3`, 21.0 s) is packed as the sound strip `VO`, starting at frame 1. The VO ends at frame 1260; the last 13 frames are silent, as in v010. |
| Caches / sims | None: no simulations, particles or Alembic. All motion is keyframes and shape keys, plus one geometry-nodes modifier: `M_FatPoints` instances about 12.3k fat lobules from the unlinked collection `LobuleProtos`. It is driven live by the keyed empty `TipCtl` and the scene time, with nothing baked. Do not delete `LobuleProtos` or `TipCtl`. |
| Add-ons | None needed. MPFB2 was used only to build the characters. |

## Shots and visibility (expected, not a bug)
| Frames | Shot | Set |
|---|---|---|
| 1–48 | S1: long lens down the aisle, the shop window shatters behind her, she startles | store |
| 49–110 | S2: face and belly together; the hit (frame 72): she flinches and staggers a step, the box stays in her grip | store |
| 111–180 | S3: closer; she looks down at her stomach, hand on it | store |
| 181–420 | One continuous push into the cross-section: the bullet comes in nose-first against dark tissue, pierces the shirt and skin, slows and STOPS IN THE FAT (well above the muscle) | macro |
| 421–640 | R1: wide; she stands bent over in pain, a shopper notices | store |
| 641–860 | R2: her face and hands; pain, breathing, blinks | store |
| 861–1146 | R3: the shopper comes to her; she takes her hand off and looks at the hole in her shirt | store |
| 1147–1273 | P: relief; she straightens, breathes out, smiles to the helper and nods; held end frame | store |

The store objects render in frames 1–180 and 421–1273, and the MACRO collection renders in 181–420. The switches are constant `hide_render` keys on hard cuts.

## Suggested test frames before approving the whole job
- **30**: the window shattering behind her (long lens).
- **80**: the hit and stagger, with the box in her hand.
- **215**: the bullet at the shirt and skin.
- **400**: the bullet stopped in the fat.
- **700**: her face in pain.
- **1260**: the relief ending: her face, eyes and catchlight.

I did not measure cost: under the studio rule, no full-resolution frame was rendered here. Run the test frames above first.
