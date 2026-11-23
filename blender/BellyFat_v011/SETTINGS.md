# BellyFat_v011: farm render sheet

I read these values back from `BellyFat_v011_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `BellyFat_v011_60fps.blend`: 74 MB, compressed. Everything is packed, including the VO; there are no linked libraries and no drivers. Images are 1K, except the woman's skin and hair at 2K. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU also works, and no special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1273**, step 1 (21.2 s). This is the v010 range, built straight to the VO. |
| Camera | One camera, `CAM_Film`, keyed on every frame. It makes **hard cuts** between 14 shots (no blends). Lens, clip start, focus distance and f-stop are keyed per frame. DOF is on, at f/8 or higher on every frame: f/8 on the medium shots, f/11 on the close-ups and macro, and f/22 on the bullet-flight shot. |
| Samples | 48, adaptive; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off |
| Colour | Display sRGB, view AgX, look "AgX - Punchy", exposure −0.3 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/BellyFat_v011_####.png` |
| Audio | The VO (`BellyFat_v011_VO.mp3`, 21.0 s) is packed as the sound strip `VO`, starting at frame 1. The VO ends at frame 1260; the last 13 frames are silent, as in v010. |
| Caches / sims | None: no simulations, particles or Alembic. All motion is keyframes and shape keys, plus one geometry-nodes modifier: `M_FatPoints` instances about 12.3k fat lobules from the unlinked collection `LobuleProtos`. It is driven live by the keyed empty `TipCtl` and the scene time, with nothing baked. Do not delete `LobuleProtos` or `TipCtl`. |
| Add-ons | None needed. MPFB2 was used only to build the characters. |

## Shots and visibility (expected, not a bug)
| Frames | Shot | Set |
|---|---|---|
| 1–36 | A: the woman reads a box (our logo) in the aisle | store |
| 37–72 | B: the bullet bursts through the shop window and flies down the aisle | store |
| 73–120 | C: close shot of the bullet hitting her shirt (impact at frame 90) | store |
| 121–180 | D: reaction. She folds and her hand goes to the wound; the box falls | store |
| 181–1146 | E1–H3: the cross-section set (shirt, skin, fat, fascia, muscle, peritoneum, bowel); the bullet stops at about frame 960 | macro |
| 1147–1206 | O: she lifts her hand and looks at the hole in her shirt | store |
| 1207–1273 | P: she straightens, breathes out and looks up. She is fine | store |

The store objects render only in frames 1–180 and 1147–1273. The `MACRO` collection renders only in 181–1146. The switches are constant `hide_render` keys placed on hard cuts. Keep the `hide_render` animation enabled, and do not force collections visible.

## Suggested test frames before approving the whole job
- **20**: the woman in the aisle holding the logo box. It tests faces, hair and the 2K skin.
- **55**: the bullet in flight beside the camera, at f/22.
- **240**: the cross-section, with the bullet piercing the skin layers.
- **1000**: the bullet stopped above the bowel loops.
- **1260**: the ending: her face, eyes and catchlight.

I did not measure cost: under the studio rule, no full-resolution frame was rendered here. Run the test frames above first.
