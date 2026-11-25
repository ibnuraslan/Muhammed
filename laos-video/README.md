# Laos: The Bombs That Stayed (documentary)

`laos.mp4` is the finished 9:50 cel-shaded documentary (720p, am_fenrir narration) about unexploded ordnance in Laos and Nachat Primary School.

## Source
- `src/lx1.js`–`lx5.js`: the five section modules (cues 0–24, 25–45, 46–78, 79–106, 107–133).
- `src/lao.js`: characters, props and terrain. `src/laosets.js`: sets. `src/laomaps.js`: animated maps and cards.
- `src/lib3.js`, `film3.js`, `film3.html`, `cap3.js`: the shared three.js toon renderer and frame capture (same pipeline as `legion-video`).
- `src/tl_laos.json`: narration timeline (134 cues, 590.2 s).
- `audio/audio_laos.py`: music, sound effects and narration mix.

Render a section: serve `src/` on port 8765, then
`FQ='&tl=tl_laos.json&pre=lx' node cap3.js <section> out_laos 4 all`, and encode with ffmpeg at 24 fps.
