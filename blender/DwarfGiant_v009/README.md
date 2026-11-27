# DwarfGiant_v009: the from-scratch rebuild (batch 1, film 26)

**Status: READY FOR THE DIRECTOR'S WATCH.** The director (with the client's authority) approved a final round on the 4 CHECK2 items. All 4 are fixed and watched in motion (`review/CHECK3.md`). Watch `review/preview.mp4` before it goes to the client.

One office, one continuous camera, built to the v008 VO (frames 1-2083, 60 fps, beats in `beats.json`). The short young man stands at a measuring rod beside a recruiting officer. An x-ray look on his own body shows the brain, the swelling pituitary tumour and the hormone stream. He grows in camera (rig scale about the floor, IK feet planted) past the officer and the door. His hands enlarge. An x-ray shows the curving spine, a focus pull shows his vision blurring, and the officer talks while he strains to hear. The tumour is removed and he keeps growing to 2.34 m. The end shows a sepia photo of his short self (a real still of the film's opening) beside the giant.

Scripts (in order):
- `scripts/00_textures.py`: recoloured CC0 MakeHuman garments and the logo plaque.
- `01_build.py <brain_src.blend> a.blend`
- `02_animate.py -- vo.mp3 b.blend`
- `02b_photo.py -- . c.blend`
- `03_package.py -- .`

`brain_src.blend` is the CC-BY brain object taken from `DwarfGiant_v008_60fps.blend`.

Render: frames **1-2083** at 60 fps (34.7 s). Join the frames into a video at **60 fps**. Settings: `SETTINGS.md`. Credits: `CREDITS.md`.

## Render check: PASS
On the exact file `DwarfGiant_v009_60fps.blend` (26 MB), opened with `blender --factory-startup -b`:
- No linked libraries, no unpacked images, and the VO sound is packed.
- No drivers, no Python text blocks, and no errors or warnings, apart from one Blender deprecation notice from the check script itself.
- Camera `CAM_Film`, 1080x1920 at 100 %, 60 fps, frames 1-2083, PNG to `//render/DwarfGiant_v009_####.png`, and the VO strip at frame 1.
- Test frames at full resolution, 64 adaptive samples, on a 4-core CPU with no GPU: f600 in 233 s and f2000 in 238 s. Neither is black, empty or pink (`review/rc_f0600.jpg`, `review/rc_f2000.jpg`).
- Checks: clip_scan 0 bad ranges. body_prop_cross (rod, desk, door) 0 crossings. limb_check ARMBODY hits are only 2 shoulder points (the documented upperarm01 false positive); PROPHEAD hits are the intended hormone beads inside the x-ray head. qa_check PROPMOVE is the hormone beads (no hands involved); EMPTY at f139 and f445-463 is a detector miss (the hero is in frame in the pages).
