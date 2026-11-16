# LincolnAssassination_v002b: render settings

- File: `LincolnAssassination_v002b_60fps.blend` (all textures and the VO packed, compressed, opens with factory startup).
- **Frame range: 1–1503** (25.05 s at 60 fps; the VO ends at 24.54 s, last frame ~0.5 s later).
- Resolution 1080×1920, 100%, 60 fps.
- Engine Cycles, CPU or GPU, 48 samples, adaptive threshold 0.05, OpenImageDenoise. Motion blur off.
- Colour: AgX, look "AgX - Punchy". Exposure is keyed per set (constant keys): theatre 0.3, street 0.9, barn 0.2.
- Cameras: 17 camera objects bound to 17 timeline markers (hard cuts). Do not delete the markers.
- Output: `//render/LincolnAssassination_v002b_` PNG sequence (set your farm output). The VO is in the sequencer at frame 1 for an audio-synced mux.
- No simulation caches. Fire is Geometry Nodes driven by keyed values; nothing reads Scene Time.
