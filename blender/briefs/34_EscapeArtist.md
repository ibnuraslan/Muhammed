# Connect34: EscapeArtist

Branch `claude/connect34-escape-artist`. Folder `blender/EscapeArtist_v001/`. Target length about 62.5 s, so frame_end = 3750. The script below is 170 words.

Real person: generic face. Portray autism respectfully as focus and mechanical talent; no stereotypes. Show **no weapon construction**: the fake gun is just a toothpaste tube bent into an L-shape, seen briefly in silhouette. The key filing is a general shot of hands and a file, not a lockpicking tutorial.

## Script (ours)

He would glance at a guard's key and instantly memorize its pattern. Then he'd file a piece of scrap metal into the exact same shape and let himself out of prison. You see, as an autistic child, he had a special talent for mechanics, and when his father died, he left his tools to him. But his stepmother called the police, since the will hadn't been read yet. He was sentenced to four years, but after just one month, he climbed over the razor wire fence and ran. That added more time to his sentence, plus solitary confinement. But once he was back in his cell, he used a makeshift saw to cut through the bars. Another time, he shaped a toothpaste tube to look like a gun and pointed it at the guards as he ran. And after 13 escape attempts, his sentence had stretched to 34 years, with 27 of those spent in solitary confinement. And even though people have protested, he's still in prison to this day.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | glance at a guard's key and memorize its pattern | A prison corridor: a guard's key ring swings past. Macro on the young man's eyes; the key teeth glow as a memory overlay. |
| 2 | 4.6 | file a piece of scrap metal into the exact same shape | In his cell at night: hands file a scrap of metal with sparks, and a key shape emerges. |
| 3 | 9.3 | let himself out of prison | The key turns in the cell lock and he slips into the corridor. |
| 4 | 11.3 | as an autistic child… talent for mechanics | The world softens into a memory: a boy at a workbench taking apart a clock, focused and happy. |
| 5 | 15.7 | when his father died, he left his tools to him | An older father's hands passing a worn toolbox to the boy; then the father's empty chair. |
| 6 | 18.8 | his stepmother called the police | Stepmother on a phone, angry, pointing; police lights arrive at the house. |
| 7 | 23.7 | sentenced to four years | Courtroom gavel; a prison gate slams. |
| 8 | 25.8 | after just one month… razor wire fence | Night: he climbs the chain-link fence, over coils of razor wire, and drops down and runs into fields. |
| 9 | 31.0 | more time… solitary confinement | Recaptured: a tiny solitary cell with a slot of light; he sits on the bunk. |
| 10 | 36.2 | makeshift saw to cut through the bars | Close on his hands sawing a window bar with a thin blade, with metal filings. |
| 11 | 41.4 | shaped a toothpaste tube to look like a gun | Brief: a bent toothpaste tube held in silhouette as he backs away and runs. Guards freeze, then chase. |
| 12 | 48.3 | after 13 escape attempts… 34 years | Time-lapse: the cell, his hair greying, tally marks on the wall. |
| 13 | 53.8 | 27 of those spent in solitary | The camera slowly circles him in solitary, light shifting across decades. |
| 14 | 58.3 | people have protested | Outside the prison walls: protesters with blank placards (no text) and candles. |
| 15 | 60.3 | he's still in prison to this day | Final: an older man at the cell window looking out, the camera pulling back through the bars. Settle. |

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
  - Medical "inside the body" beats use the clean explainer look: a bright sky-blue gradient (cyan to near-white) behind clean, colour-coded anatomy in soft, high-key light (see `blender/STYLE_ANIMATED.md`).
  - Real-world beats use real sets.
- **Deliverable tonight:** checkpoint D package in `blender/EscapeArtist_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
