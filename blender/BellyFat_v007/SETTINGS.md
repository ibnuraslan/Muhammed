# BellyFat_v007: farm render sheet

These values were read back from `BellyFat_v007_60fps.blend` opened in factory-startup Blender 5.2.2, with no add-ons.

| Item | Value |
|---|---|
| File | `BellyFat_v007_60fps.blend`: 71 MB, compressed (the bowel model and the bevelled store products add the extra size). All images are packed: 1K, except the woman's skin, hair and SSS map at 2K; it has no linked libraries and no drivers. Stored as a regular git file, because the Git LFS upload was refused (verify: Forbidden). |
| Blender | 5.2.2 LTS |
| Engine | Cycles. The device is saved as CPU; GPU is fine. No special features are used. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1290**, step 1 (21.5 s) |
| Camera | One camera, `CAM_Film`, on one baked continuous path. There are no camera markers or switches. Lens, clip start, focus distance and f-stop are keyed per frame; DOF is on, at f/5.6 or higher everywhere (shallow only in the macro section). The clip start drops to 0.2 mm in the macro section, so do not override it. |
| Samples | 48, adaptive; noise threshold 0.05 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 8, diffuse 3, glossy 3, transmission 8, transparent 8. Caustics off. Persistent data on. |
| Motion blur | Off (animated look: no heavy motion blur) |
| Colour | Display sRGB, view AgX, look "AgX - Punchy", exposure −0.3 |
| Output | PNG, RGB, 8-bit, compression 15, to `//render/BellyFat_v007_####.png` |
| Audio | None yet: the voiceover has not been delivered. See "Voiceover" below. |
| Caches / sims | None: no simulations, particles or Alembic. All motion is keyframes and shape keys, plus one geometry-nodes modifier: `M_FatPoints`, which instances about 7.5k fat lobules from the unlinked collection `LobuleProtos`. It is driven live by the keyed empty `TipCtl` and the scene time, with nothing baked. Do not delete `LobuleProtos` or `TipCtl`. |
| Add-ons | None needed. MPFB2 only built the characters. |

## Visibility swap (expected, not a bug)
The supermarket objects render-hide at frames **154–1224** and the cross-section (MACRO collection) renders only in those frames. Both switches happen while shirt fabric fills the frame about 1.8 cm from the lens. Keep `hide_render` animation enabled, and do not force collections visible.

## Suggested test frames before approving the whole job
- **100**: riding the bullet in the store, with DOF.
- **140**: macro at the impact on the shirt, the smallest focus distance.
- **361**: wide cross-section of the packed fat (geometry-nodes instances), on the cyan studio backdrop.
- **1000**: the bullet stopped in muscle beside the coiled bowel loops (SSS and coat).
- **1280**: the ending; the woman, hands and face.

Cost was not measured: no full-resolution frame was rendered here, under the studio rule. Expect noticeably less per frame than GoatRescue2 (125 s per frame on 4 CPU cores), because the macro section is a small studio set. Run the test frames above on RenderStreet first.

## Voiceover
When the mp3 arrives:
1. Get word times with `pipeline/transcribe.py`.
2. Fill in `anchors_template.json`, giving the start second of each beat's first words from `beats.json`.
3. Run `blender -b BellyFat_v007_60fps.blend --python pipeline/retime_to_vo.py -- anchors.json vo.mp3 BellyFat_v007_60fps.blend`.

The camera, the bullet and the tissue animation are all ordinary keyframes, so the warp moves them together. The swap frames (154/1225) are constant-interpolated `hide_render` keys and warp with them.
