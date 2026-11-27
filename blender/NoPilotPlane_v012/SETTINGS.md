# NoPilotPlane_v012: farm render sheet

| Item | Value |
|---|---|
| File | `NoPilotPlane_v012_60fps.blend`, 84 MB, compressed. Everything is packed, including the VO. No linked libraries, no drivers, no Python. Stored as a regular git file (no LFS). |
| Blender | 5.2.2 |
| Engine | Cycles. The device is saved as CPU; GPU also works. |
| Resolution | 1080 × 1920 at 100 % |
| Frame rate | 60 fps (fps_base 1.0) |
| Frame range | **1–3481**, step 1 (58 s). Built to the client's VO, so no retime. |
| Camera | One camera, `CAM_Film`, keyed on every frame, in one continuous move with no cuts and no camera markers. |
| Samples | 14 max, adaptive sampling on, noise threshold 0.1 |
| Denoising | On (OpenImageDenoise) |
| Light paths | Max 3, diffuse 1, glossy 1, transmission 4, transparent 8. Caustics off. Persistent data on. |
| Colour | AgX, look Punchy |
| Output | PNG, RGB, to `//render/NoPilotPlane_v012_####.png` |
| Audio | `NoPilotPlane_v012_VO.mp3` packed as the sound strip `VO` at frame 1; the same mp3 sits next to the .blend for encoding |
| Caches and sims | None: all motion is keyframes. The sky, ground, town and field move around the plane (the empties `WORLD_ROT` and `WORLD_POS`); the plane itself never moves. |
| Add-ons | None needed. MPFB2 was used only to build the characters. |
| Measured time | 69–114 s per frame on a 4-core CPU (f20 114 s, f1780 69 s, f3065 73 s) |
