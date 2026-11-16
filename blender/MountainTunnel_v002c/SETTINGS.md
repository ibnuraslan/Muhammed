# MountainTunnel_v002c: render settings

- File: `MountainTunnel_v002c_60fps.blend` (all textures and the VO packed; open with factory startup)
- Resolution 1080×1920, 100 %, **60 fps**
- **Frame range 1–1991** (33.2 s: VO speech 0.00–32.66 s + 0.5 s tail)
- Engine Cycles, 48 samples, adaptive threshold 0.05, OpenImageDenoise
- Colour: AgX, look Punchy. Motion blur off.
- Cameras: one per shot, bound by timeline markers (22 hard cuts). Scene camera at frame 1 = CAM_1a.
- Output path `//render/MountainTunnel_` (PNG frames). Audio: the VO strip in the sequencer (AAC when muxing).
