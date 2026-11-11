# Connect06: PrisonKeyCake

Branch `claude/connect06-prison-key-cake`. Folder `blender/PrisonKeyCake_v001/`. Target length about 31.5 s, so frame_end = 1890. The script below is 98 words.

## Script (ours)

He got hold of the prison's master key and pressed it into melted candle wax, making a perfect impression. The mold was smuggled out of the prison, and his allies used it to cast a metal copy. They hid the key inside a cake and sent it back to him. But when he tried the key, it didn't fit. So he sent out another wax impression and waited for the next cake. And this time, the key worked. He passed through every locked gate and simply walked out of the prison. Years later, he became president of Ireland.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | master key… melted candle wax | Grimy 1919 English stone prison cell lit by candlelight. Hands press an ornate iron key into a pool of melted wax beside a candle. |
| 2 | 4.3 | a perfect impression | Macro: the key lifts away, leaving a crisp imprint as the wax hardens. |
| 3 | 6.1 | smuggled out of the prison | The mold is hidden in a coat pocket; the camera follows a visitor walking through the prison yard to the gate. |
| 4 | 8.5 | cast a metal copy | Workshop: molten metal pours into a sand mould, with sparks, glow and smoke, and a key shape cools. |
| 5 | 11.4 | hid the key inside a cake… sent it back | The key is pushed into a fruit cake, which goes into a box, and the box goes through the gate. |
| 6 | 14.5 | it didn't fit | Night cell door: the key goes into the big iron lock, jams, and won't turn. Frustration. |
| 7 | 17.6 | another wax impression… waited | Candle, wax, key again. Time passes as the candle burns down. |
| 8 | 21.7 | this time, the key worked | A new cake is cut open, the key is pulled out, and it goes into the lock: clunk, and it turns. |
| 9 | 23.8 | passed through every locked gate | The camera follows him through corridor gates opening one after another, out into the night yard. |
| 10 | 28.0 | became president of Ireland | Wide crane-up: decades later, an older him on government building steps, Irish tricolour flags waving, crowd. Generic face. |

## Rules for this film (on top of `pipeline/CONNECT_BRIEF.md` and `PRODUCTION_RULES.md`)
- **Script:** use the script below; it's ours. The reference narration is not in this repo; don't try to get it.
- **Timing:** with no voiceover yet, build to the **target times** in the beat table (they match the reference's pacing, about 2.8–3.2 words/s).
  - Write `beats.json`: `[{"beat": 1, "frame": <start frame>, "first_words": "..."}, ...]`. When the VO arrives, the director retimes with `pipeline/retime_to_vo.py`.
- **One continuous camera.** The reference cuts all the time; we don't.
  - Turn each cut into a move: dive through skin into a cross-section, fly through a wall, whip-pan, rack focus, or orbit from the character to a macro.
- **No on-screen text or captions** (captions are added in the edit).
  - No logos, brand names or watermarks on anything: clothes, cups, monitors, props.
  - No likeness of any real person; use generic characters.
- **Look:** textured, grounded realism, with anatomy believable and clean, never gory.
  - Medical "inside the body" beats use the clean explainer look: a soft cyan-to-white studio gradient behind realistic anatomy and studio lighting.
  - Real-world beats use real sets.
- **Deliverable tonight:** checkpoint D package in `blender/PrisonKeyCake_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
