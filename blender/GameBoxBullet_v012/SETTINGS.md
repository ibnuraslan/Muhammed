# GameBoxBullet_v012: farm render sheet

| Item | Value |
|---|---|
| File | `GameBoxBullet_v012_60fps.blend`, 64 MB, compressed. Everything is packed, including the VO. There are no linked libraries, no drivers and no Python. It is stored as a regular git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU also works. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–1311**, step 1 (21.85 s). Built to the client's VO from the start, so no retime. |
| Camera | One camera, `CAM_Film`, keyed on every frame, in one continuous move with no cuts and no markers. DOF is off. Clip start is 4 mm, for the macros. |
| Samples | 64 max, adaptive sampling on, noise threshold 0.04 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 6, diffuse 3, glossy 3, transmission 6, transparent 16. Caustics off. Persistent data on. Simplify: subdivision 2, texture limit 2048. |
| Motion blur | Off (animated look) |
| Colour | View **Filmic**, look **High Contrast**, exposure −1.0 |
| Output | PNG, RGB, 8-bit, to `//render/GameBoxBullet_v012_####.png` |
| Audio | `GameBoxBullet_v012_VO.mp3` is packed as the sound strip `VO` at frame 1 (frames 1–1285). The same mp3 sits next to the .blend for encoding; add it at frame 1. |
| Caches and sims | None. All motion is keyframes. The crack and the entry hole are shader values keyed in the box art material (`CrackRadius`, `HoleRadius`). |
| Add-ons | None needed. MPFB2 was used only to build the characters. |

## Logo
DA KRAS FILMS appears on the box set's front and on the framed poster on the back wall. The poster reads in full at f256–446, the box logo at f256–446 and f1026–1250.

## Suggested test frames before the full job
- **1**: the shooter on the sidewalk
- **200**: the bullet in silhouette inside the room
- **350**: his face and the box with the logo
- **720**: the bullet in the box channel
- **1290**: the ending, his relieved face
