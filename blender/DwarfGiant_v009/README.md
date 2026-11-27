# DwarfGiant_v009: the from-scratch rebuild (batch 1, film 26)

**Status: ON HOLD. Not delivered.** After 2 fix rounds, my own watch and a fresh reviewer still FAIL it. See `review/CHECK2.md` for the remaining faults and their exact fixes (the end framing and the second x-ray head). No .blend is pushed. The scripts rebuild it in about 5 minutes.

One office, one continuous camera, built to the v008 VO (frames 1-2083, 60 fps, beats in `beats.json`). The short young man stands at a measuring rod beside a recruiting officer. An x-ray look on his own body shows the brain, the swelling pituitary tumour and the hormone stream. He grows in camera (rig scale about the floor, IK feet planted) past the officer and the door. His hands enlarge. An x-ray shows the curving spine, a focus pull shows his vision blurring, and the officer talks while he strains to hear. The tumour is removed and he keeps growing to 2.34 m. The end shows a sepia photo of his short self (a real still of the film's opening) beside the giant.

Scripts (in order):
- `scripts/00_textures.py`: recoloured CC0 MakeHuman garments and the logo plaque.
- `01_build.py <brain_src.blend> a.blend`
- `02_animate.py -- vo.mp3 b.blend`
- `02b_photo.py -- . c.blend`
- `03_package.py -- .`

`brain_src.blend` is the CC-BY brain object taken from `DwarfGiant_v008_60fps.blend`.
