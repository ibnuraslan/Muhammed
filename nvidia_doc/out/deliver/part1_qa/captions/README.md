# nvidia_part1.srt: how it was made and checked

**Text.** Taken word for word from `all_scripts.md` (Nvidia intro + Ch1–3), 1,082 words. It is not speech-recognition output. A check confirms the caption text equals the script text exactly.

**Timing.**
- Word times come from `vo/intro_words.json` and `vo/ch_words.json`, the existing aligner output, matched onto the script words with difflib.
- Where the aligner and the script differ, the script wording is kept. These are mostly digits vs words: "33" → "thirty-three", "$4.5 billion" → "four and a half billion dollar", "june" → "Joon", "megaspede" → "Megaspeed".
- Each VO file is placed at its EDL frame (61 / 952 / 4800 / 7782), with the offset refined against the voice energy (+40 to +90 ms).
- 98 of 124 caption starts are snapped to the real voice onset in `nvidia_part1_VOICE_ONLY.wav`, 50 ms early. This is needed because the raw aligner starts are off by up to 324 ms after pauses (p90 187 ms). In particular, the aligner stretches the first word after a pause across the silence.

**Style.**
- At most 42 characters per line and 2 lines per caption.
- Each caption is shown for 1.08–5.8 s.
- Captions break at phrase boundaries: no splits inside names, "U.S.", numbers or dates.
- No overlaps.
- Gaps over 2 s happen only at the three chapter-title breaks (10.7 s at the sting and Ch1 card, 3.5 s at Ch2, 3.6 s at Ch3). Nothing is captioned while the music-only cards play.
- UTF-8 with curly quotes, as in the script.

**Files.**
- `captions_final.txt`: the edited caption grouping, one caption per line, `|` marks a line break.
- `build_srt.py`: aligns the script to the word timings.
- `segment_srt.py`: first-pass automatic grouping.
- `rebuild_srt.py`: builds the SRT from `captions_final.txt` with onset snapping and checks.

**QA (`spotcheck.txt`).**
- 10 captions spread across the film all start 43–50 ms before the voice (inside ±150 ms).
- Of all 102 caption starts where an onset can be measured, 100 are within ±150 ms.
- The other 2 (#40, #94) start in continuous speech with no pause. The checker latched onto a consonant dip inside the next words ("the p|air", "were | unable"), so those two can't be measured, rather than being wrong.
- Not done: an independent speech-recognition re-check (faster-whisper could not be installed in this session).
