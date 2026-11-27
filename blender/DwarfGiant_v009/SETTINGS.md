# Render settings: DwarfGiant v009
- File: `DwarfGiant_v009_60fps.blend` (everything packed, VO included).
- Engine: Cycles, 64 samples, adaptive threshold 0.05, OpenImageDenoise. Max bounces 6. Simplify: subdivision 2 and textures 2048.
- Colour: Filmic, look High Contrast, exposure -0.3.
- Output: 1080x1920 at 100 %, 60 fps, frames 1-2083, PNG RGB to `//render/DwarfGiant_v009_####.png`.
- Camera: `CAM_Film` (one continuous camera). The VO strip starts at frame 1.
- Join the PNGs at 60 fps and lay `DwarfGiant_v009_VO.mp3` from frame 1.
- Measured: about 235 s a frame on a 4-core CPU with no GPU (much faster on a render farm GPU).
