# BellyFat_v015: farm render sheet

I read these values back from `BellyFat_v015_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `BellyFat_v015_60fps.blend`: 74 MB, compressed. Everything is packed, including the VO; there are no linked libraries and no drivers. Images are 1K, except the woman's skin and hair at 2K. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU also works, and no special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1273**, step 1 (21.2 s). This is the v010 range, built straight to the VO. |
| Camera | One camera, `CAM_Film`, keyed on every frame. It makes **hard cuts** between 12 shots (no blends); the cross-section is one continuous push. Lens, clip start, focus distance, f-stop and DOF on/off are keyed per frame. In the macro shots the clip start is set to 55 % of the subject distance, so nothing can block the lens. |
| Samples | 48, adaptive; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off |
| Colour | Display sRGB, view AgX, look "AgX - Punchy", exposure −0.3 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/BellyFat_v015_####.png` |
| Audio | The VO (`BellyFat_v015_VO.mp3`, 21.0 s) is packed as the sound strip `VO`, starting at frame 1. The VO ends at frame 1260; the last 13 frames are silent, as in v010. |
| Caches / sims | None: no simulations, particles or Alembic. All motion is keyframes and shape keys, plus one geometry-nodes modifier: `M_FatPoints` instances about 12.3k fat lobules from the unlinked collection `LobuleProtos`. It is driven live by the keyed empty `TipCtl` and the scene time, with nothing baked. Do not delete `LobuleProtos` or `TipCtl`. |
| Add-ons | None needed. MPFB2 was used only to build the characters. |

## Shots and visibility (expected, not a bug)
| Frames | Shot | Set |
|---|---|---|
| 1–30 | W: medium on the shop window from inside: it cracks and shatters, the bullet streaks through | store |
| 31–58 | F: her face, startled by the crash | store |
| 59–140 | H: face and belly: the bullet streaks in (impact frame 72), the shirt dents, her body jolts, she staggers and drops the box (visible fall to the floor) | store |
| 141–180 | L: closer; she looks down at her stomach, hands on it | store |
| 181–330 | One continuous push into the cross-section: nose-first bullet, pierces shirt and skin, stops in the fat (frame 278), fat jiggles under a still-pushing camera | macro |
| 331–520 | R1: medium down the aisle; she is bent in pain, a shopper reacts behind her; slow push | store |
| 521–760 | R2: her face and hands; slow arc and push | store |
| 761–960 | R3: two-shot; the shopper walks over to her | store |
| 961–1146 | R4: she lifts her hand off and looks at the hole | store |
| 1147–1192 | P: she feels the hole and pulls the bullet out | store |
| 1193–1216 | P_bullet: insert of the bullet between her fingertips, her eyes on it | store |
| 1217–1273 | P_face: relief: eyes close on the breath out, then a smile; held end | store |

The store objects render in frames 1–180 and 331–1273, and the MACRO collection renders in 181–330. The switches are constant `hide_render` keys on hard cuts.

## Suggested test frames before approving the whole job
- **12**: the window shattering, bullet streak.
- **76**: the hit: shirt dent, jolt, box leaving her hand.
- **215**: the bullet at the shirt and skin.
- **300**: the bullet stopped in the fat.
- **850**: the two-shot with the helper.
- **1205**: the bullet in her fingers.
- **1265**: the relief ending: her face, eyes and catchlight.

I did not measure cost: under the studio rule, no full-resolution frame was rendered here. Run the test frames above first.
