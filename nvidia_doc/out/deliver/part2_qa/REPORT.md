# Nvidia film, Part 2 (Ch4–5): final MP4 QA

These files went to the user directly, because they are too big for git:
- `nvidia_part2_NO_VOICE_FORMATTED.mp4`: 128,059,956 bytes. H.264 High, CRF 18, preset slow, yuv420p, bt709, 1920x816, 24 fps, +faststart.
  - Audio: `nvidia_ch45_AUDIO_no_voice.wav`, encoded as AAC 320k, 48 kHz stereo.
- `nvidia_part2_VOICE_ONLY.wav` (48 kHz stereo, 423.125 s) and `.mp3` (320k). Aligned to frame 1.
- `nvidia_part2.srt` (also in this folder) and `CREDITS.txt`.
- `c5_17_captions_overlay.mov`: the captions for the c5_17 patch window on transparency (see below).

## Source
- RenderStreet zip `nvidia_ch45-2881838.zip`, 18.40 GB.
  - 10155 PNGs, `nvidia_ch45_00001`–`10155`, stored uncompressed. Nothing missing, nothing extra.
  - Streamed over HTTP Range, never written to disk. Farm frames inside the 14 redo ranges were not downloaded, except the range edges, which were kept for seam stats.
- **c5_17 (7551–7875) is still broken in the farm render.** It is near-black from about 7651 to 7875, because the lights switch off on the old Ch2 timing.
  - The user chose to lay the patch render (`ch45_patch/nvidia_ch45_patch_c5_17.blend`) over it himself. Those frames are left as the farm rendered them.
  - The patch layer runs from 00:05:14:14 (frame 7551) to 00:05:28:02 (frame 7875).
  - No card falls in that window.
  - Captions #149–#154 overlap it. `c5_17_captions_overlay.mov` (delivered) carries exactly those cues on transparency: ProRes 4444 with alpha, 325 frames, frame 1 = master 7551, built with the same caption layer as the MP4 (`c5_17_overlay.py` here). Put it on top of the patch layer.
- **Frozen farm shots:** zero frame-to-frame motion across the whole shot. They are delivered as rendered.
  - c4_07 memo_push, 1262–1404
  - c4_11 boardroom_empty_chair, 2150–2397. The plan describes a hold, so this may be intended.
  - c4_13 boardroom_slow_push, 2594–2784
  - c5_23 courthouse_slow_push, 9016–9316
  - c5_25 memo_desk_letter_push, 9455–9613
  - c5_26 memo_close2, 9614–9904
  - Mostly static: c4_06 (92% of the shot) and c5_27 (86%).

## Step 1: redo clips
- All 14 clips decode to exactly their range's frame count: 249, 288, 114, 297, 196, 188, 199, 215, 155, 248, 136, 197, 252 and 227 frames. Each was substituted 1:1.
- c4_08 uses `c4_08_v2_redo.mp4` from `claude/nvidia-redo-w6`.
- The clips were encoded from PNGs with ffmpeg's default (bt601) matrix, and are decoded the same way.
- Seams (`seams.json`): every redo boundary falls on an EDL shot cut. The luma and colour jumps there are cuts between different sets.
  - The contact sheet shows every seam as a before/after pair.
  - No single-frame spikes and no seam mismatch within a shot.
- The farm master fades up from black over frames 1–25. The c4_01 redo clip does not, so the same smoothstep fade-up was re-applied.

## Step 2: titles (new style)
- The old title is baked into c4_01 and c5_01: title_card style, oval scrim 0.36, driver fade at local frames 18–120.
- It is removed by inversion:
  - The baked title layer is rebuilt exactly (title_card code and fonts).
  - Its measured light contribution is subtracted. It was measured on flat background in both clips; the render's view transform makes it non-linear.
  - The scrim is divided out.
  - The letter cores (alpha > 0.4) are inpainted.
- On top of that clean plate:
  - The whole frame is dimmed by 52%.
  - The clean title goes over it: "CHAPTER 4 / THE SECOND EMPLOYEE" and "CHAPTER 5 / THE PASSPORT AND THE PAPER TRAIL". Layout, fonts and two-line split match title_card; the cream text has a rim, shadow and glow, and no scrim.
  - The dim and title fade together over 10 frames (0.42 s), smoothstep.
  - They are visible over frames 19–119 (Ch4) and 4121–4221 (Ch5).
- Checked at the start, middle and end of both windows on the contact sheet. No baked text or oval shows.

## Step 3: cards and captions
- Cards use `callout.py` from killer-in-house @383c57c, unchanged. Each slides in 0.35 s, holds 3.0 s and slides out 0.3 s (88 frames):
  - COLETTE KRESS / INTERIM CEO, NVIDIA: frames 2596–2683
  - HONG KONG / CHINA (place, lower left): frames 6650–6737
  - TODD BLANCHE / U.S. ATTORNEY GENERAL: frames 9032–9119
- Skipped, because no free-license photo exists:
  - Kimberly Powell. The user pasted a press headshot into chat, but it was not available as a file and its licence is not free.
  - Harvey Jones.
  - Alice Huang.
- Licences are listed in `CREDITS.txt`.
- Captions:
  - 195 cues, the exact script text from `edit/script_ch4_ch5.md`. Every word was checked against the script.
  - One line per cue, up to 57 characters, using `callout.caption` (Courier Prime). Hard cut on and off.
  - Timing uses the Part 1 method. Aligner words come from `vo/ch45_words.json`, placed at the ch45 mix offsets: VO4 at frame 73 and VO5 at frame 4175 (+10 / +30 ms energy refinement). 120 caption starts were snapped to voice onsets.
  - Each cue shows for 1.01–3.36 s. There are no overlaps. The only gap over 2 s is the chapter break (4.6 s).
- Legibility: captions and cards get an extra soft dark halo, scaled by how bright the background under them is. Over normal or dark frames the strength is 0, so the approved look is unchanged.
  - It was needed because the courthouse and memo shots are near-white (luma 210–228), where white text with the stock shadow was unreadable.
  - It is active on 3557 caption frames and on the Todd Blanche card.

## Step 4: audio
- The video carries `nvidia_ch45_AUDIO_no_voice.wav` (423.125 s).
- Voice-only stem:
  - Built from the same `vo` buffer as `edit/sound_ch45.py`: `vo/ch4_vo.mp3` at frame 73 and `vo/ch5_vo.mp3` at frame 4175, with the same peak normalisation, soft clip and −14 LUFS gain (+2.90 dB) as the mixes.
  - Checked against the committed (with_voice − no_voice): lag 0 samples, correlation 0.99997, residual −42.8 dB.
  - Length 423.125 s, which equals the video.

## QA
- ffprobe (`ffprobe.txt`): 10155 frames. Video 423.125 s, audio 423.125 s.
- Luma and frame-difference scan (`luma.txt`, `frame_luma_diff.csv`):
  - 45 jumps over 15 fall on EDL cuts.
  - The other jumps are 7636/7650 (c5_17 lights going off in the broken farm shot) and 10145–10146 (the end fade).
  - No single-frame spikes.
- Dark ranges:
  - 1–8: the fade-up.
  - 7236–7314: c5_15 remote_enter, intended.
  - 7650–7875: c5_17, broken in the farm render; the patch goes here.
  - 10151–10155: the end fade.
- Contact sheet: `nvidia_part2_contact_sheet.jpg`, 72 tiles. It covers every redo seam, both titles (5 frames each), every card at slide-in and at hold, and c5_17.
