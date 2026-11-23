# BellyFat_v012: farm render sheet

I read these values back from `BellyFat_v012_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `BellyFat_v012_60fps.blend`: 74 MB, compressed. Everything is packed, including the VO; there are no linked libraries and no drivers. Images are 1K, except the woman's skin and hair at 2K. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU also works, and no special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1273**, step 1 (21.2 s). This is the v010 range, built straight to the VO. |
| Camera | One camera, `CAM_Film`, keyed on every frame. It makes **hard cuts** between 13 shots (no blends). Lens, clip start, focus distance, f-stop and DOF on/off are keyed per frame. In the macro shots the clip start is set to 55 % of the subject distance, so nothing can block the lens. |
| Samples | 48, adaptive; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off |
| Colour | Display sRGB, view AgX, look "AgX - Punchy", exposure −0.3 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/BellyFat_v012_####.png` |
| Audio | The VO (`BellyFat_v012_VO.mp3`, 21.0 s) is packed as the sound strip `VO`, starting at frame 1. The VO ends at frame 1260; the last 13 frames are silent, as in v010. |
| Caches / sims | None: no simulations, particles or Alembic. All motion is keyframes and shape keys, plus one geometry-nodes modifier: `M_FatPoints` instances about 12.3k fat lobules from the unlinked collection `LobuleProtos`. It is driven live by the keyed empty `TipCtl` and the scene time, with nothing baked. Do not delete `LobuleProtos` or `TipCtl`. |
| Add-ons | None needed. MPFB2 was used only to build the characters. |

## Shots and visibility (expected, not a bug)
| Frames | Shot | Set |
|---|---|---|
| 1–40 | A: medium close; she reads a box with our logo | store |
| 41–52 | W: the bullet punches through the shop window (crack, shards) | store |
| 53–100 | B: tracking behind the bullet down the aisle, she is ahead in frame; it hits her stomach (frame 92) | store |
| 101–1005 | Inside, side-on at one fixed distance: shirt and skin, fat, fascia, muscle; the bullet stops at about 952 above the bowel, holds 0.9 s | macro |
| 1006–1146 | D: reaction, both hands on her belly, face visible | store |
| 1147–1273 | One continuous shot: she checks her palm, looks at the hole, straightens, breathes out, nods and pats her belly | store |

The store objects render in frames 1–100 and 1006–1273, and the MACRO collection renders in 101–1005. The switches are constant `hide_render` keys on hard cuts. Depth of field is keyed off in the window and tracking shots (W and B), so the bullet and the woman are both sharp. Every other frame uses f/8 or higher, and the macro shots use f/45.

## Suggested test frames before approving the whole job
- **20**: the woman holding the logo box. It tests faces, hair and the 2K skin.
- **46**: the window crack.
- **75**: the tracking shot behind the bullet.
- **180**: the bullet piercing the skin layers.
- **980**: the bullet stopped above the bowel.
- **1260**: the ending: her face, eyes and catchlight.

I did not measure cost: under the studio rule, no full-resolution frame was rendered here. Run the test frames above first.
