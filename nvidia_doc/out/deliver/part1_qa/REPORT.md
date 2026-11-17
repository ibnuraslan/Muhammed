# Nvidia film, Part 1 (intro + Ch1–3): final MP4 QA

Delivered to the user directly (the files are too big for git):
- `nvidia_part1_NO_VOICE.mp4`, 140,377,798 bytes (134 MB). H.264 High, CRF 18, preset slow, yuv420p, bt709, 1920x816, 24 fps, +faststart. Audio: v3 no-voice mix, AAC 320k, 48 kHz stereo.
- `nvidia_part1_VOICE_ONLY.wav` (48 kHz stereo, 414.5417 s) and `.mp3` (320k). Aligned to frame 1, so it goes under the video at 0:00.
- Per the user's change, no with-voice MP4 was made.

## Source
- RenderStreet zip with 9949 PNGs, nvidia_film_00001–09949, stored uncompressed. Nothing missing, nothing extra.
- The zip was streamed over HTTP Range (6 parallel fetches, written to the encoder in frame order) straight into x264. The full zip was never written to disk.
- PNG alpha is below 255 on only about 0.2% of pixels, a fixed border pattern. It was dropped (treated as opaque).

## Titles
- `out/title_overlay/nvidia_title_overlay.mov` was laid over the frames frame for frame. Its visible windows are 922–1022, 4770–4870 and 7752–7852.
- **The farm render has the wrong Ch2 title baked in**: "BEHIND CLOSED DOORS", out of focus, across frames 4770–4870. The overlay's "THE MEMO" is narrower, so the wrong letters showed on both sides.
- Fix in the composite: for exactly 4770–4870, the full extent of the baked text (x 230–1690, y 330–510, 60 px feather) is covered by a soft dark plate. The plate is rebuilt from the rows just above and below the text. The overlay goes on top.
- Checked frame by frame at both edges (4766–4776 and 4864–4874): no wrong text shows.

## Audio
- The v3 mixes were not in git, so they were regenerated with `edit/sound_design.py` (seed 42, `film_edl.json` timeline). Output is 414.5417 s.
- Voice-only stem: the same `vo` buffer (EDL VO placement plus `vo/*.mp3`), the same peak normalisation, and the same −14 LUFS gain as the mixes.
- Checked against (with_voice − no_voice): lag 0 samples, correlation 0.9996, residual −31 dB below the voice.

## QA
- ffprobe frame count: 9949 frames. Video 414.5417 s, audio 414.541 s (match).
- Luma and frame-difference scan (`luma.txt`, `frame_luma_diff.csv`). No single-frame corruption outliers.
- Dark ranges are all intended:
  - 753–763 and 895–906: fades around the sting
  - 1877–1984: c1_07_remote_enter
  - 3777–3860: c1_19_remote_enter
  - 6678–6837: c2_12 warehouse lights off
- Frame-difference jumps all fall on EDL cuts, except 4820–4823 and 5179–5182. Those are 3-frame camera flashes in the Computex shots.
- Contact sheet: `nvidia_part1_contact_sheet.jpg` (12 frames, including all three title windows).
