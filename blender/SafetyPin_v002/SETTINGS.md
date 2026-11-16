# SafetyPin v002: render settings

- File: `SafetyPin_v002_60fps.blend` (all textures and the VO packed; 64 MB)
- Resolution 1080 × 1920, 100 %, **60 fps**
- **Frame range 1–1857** (VO 30.85 s; last word ends 30.44 s = frame 1828; end ≈ 0.5 s after)
- Cycles CPU/GPU, 48 samples, adaptive threshold 0.05, OpenImageDenoise, no motion blur
- Colour: AgX, look Punchy
- Output: PNG sequence to `//render/SafetyPin_v002_####.png`
- Cameras: one camera per shot with hard cuts, bound by 18 timeline markers (batch-2 rule: hard cuts). Do not delete the markers.
- VO: on the sequencer (strip "VO", from frame 1); the render is picture-only, mux the VO in the edit.
