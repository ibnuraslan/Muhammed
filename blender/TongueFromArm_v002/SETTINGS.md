# Render settings — TongueFromArm_v002

- File: `TongueFromArm_v002_60fps.blend` (all textures and the VO packed; factory-startup clean)
- Frames **1–1404** at **60 fps** (23.4 s). VO `TongueFromArm_v002_VO.mp3` starts at frame 1 (also packed on the sequencer).
- 1080×1920, Cycles 48 samples, adaptive threshold 0.05, OpenImageDenoise, AgX "Punchy", motion blur off.
- Output: PNG frames to `//render/TongueFromArm_v002_`; join at **60 fps** with the VO.
- Cameras: one camera per shot, switched by the 19 timeline markers (hard cuts, as the batch-2 brief asks). The farm renders the active marker camera per frame; do not override the camera.
