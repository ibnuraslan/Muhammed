# SpeakWithoutSight_v007: the from-scratch rebuild (batch 1, film 19)

**Status: CLIENT-APPROVED (relayed by the director on Nov 27) as this exact build.** Our own last fresh review was FAIL (see `review/CHECK_FINAL.md`, last section). The client watched it and approved it as it is.
Watch `review/preview.mp4` (270x480, every 5th frame, with the VO) before rendering.

One parlour, one girl and one teacher (one MPFB model each, rotation limits on knees, hips and elbows), one continuous camera framed on the pair, built to the client's VO (the v006 timing): frames **1-1645** at 60 fps (`beats.json`). Render sheet: `SETTINGS.md`. Credits: `CREDITS.md`.
Scripts: `scripts/01_build.py` (set and characters), `02_animate.py` (seating, acting, contacts, skin ripples, pulse dots, camera, lights) and `03_package.py`.

## The film
- **Beats 1-2:** a late-1800s parlour. The girl sits unfocused on a plum settee beside her teacher, under the framed DA KRAS FILMS sampler. The room dims around her.
- **Beat 3:** the teacher lifts the girl's hand and the girl's fingers rest on the teacher's throat.
- **Beats 4-6:** the teacher speaks. Glowing ripples on the throat and pulse dots up the girl's arm show the vibrations, strong then soft.
- **Beats 7-8:** the girl's fingertips move to the teacher's lips as the teacher forms each word.
- **Beats 9-10:** the girl feels her own lips and mimics. A time-lapse runs through the window (day/night, the seasons, the lamp).
- **Beat 11:** she speaks, her throat glows, and the teacher reacts.
- **Wardrobe** (approved by the director): long-sleeve blouses and long trousers. The girl's feet rest on a footstool.

## Render check: PASS
On the exact file `SpeakWithoutSight_v007_60fps.blend` (55 MB), opened with `blender --factory-startup -b` (Blender 5.2.2):
- No linked libraries, no unpacked images, no drivers and no text/Python blocks. The VO sound is packed.
- No errors. The only console warning is the CUDA library notice of this GPU-less machine.
- Camera `CAM_Film`, 1080x1920 at 100 %, 60 fps, frames 1-1645, PNG to `//render/SpeakWithoutSight_v007_####.png`, and the VO strip at frame 1.
- Cycles: 64 adaptive samples (threshold 0.04), OpenImageDenoise, max 6 bounces, persistent data. AgX Punchy.
- Test frames at full resolution on a 4-core CPU with no GPU: f20 in 138 s, f800 in 175 s and f1600 in 169 s. None is black, empty or pink (mean luminance 0.38-0.40).
