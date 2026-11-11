# Connect26: DwarfGiant

Branch `claude/connect26-dwarf-giant`. Folder `blender/DwarfGiant_v001/`. Target length about 39.0 s, so frame_end = 2340. The script below is 113 words.

Real historical person (1900s Austria): use a generic face. No on-screen height numbers; show height with a door frame, an army officer and a measuring rod.

## Script (ours)

He was far too short to join the army, but a tumor was quietly growing in his brain. It flooded his body with growth hormone, and suddenly, the four-foot-six man started to grow. His hands, feet and even his tongue got bigger, and he shot up more than two feet in just a few years. But as he grew, his spine began to curve. His vision blurred, and eventually, he struggled to hear. Doctors finally removed the tumor, which slowed his growth, but didn't stop it completely. By the time he died, he was seven foot eight, making him the only man in history to live as both a dwarf and a giant.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | far too short to join the army | 1917 army recruitment office: a short young man in braces stands at a measuring rod while officers in WWI uniform shake their heads. The camera drops to his eye level. |
| 2 | 3.0 | a tumor was quietly growing in his brain | Dive through his temple into a realistic brain (real CC-BY brain model): the pituitary gland is glowing and swelling with a tumor. |
| 3 | 6.2 | flooded his body with growth hormone | Glowing hormone particles stream from the pituitary down through the bloodstream (x-ray body). |
| 4 | 7.8 | the four-foot-six man started to grow | Pull out: time-lapse as he grows taller, with clothes going tight and sleeves riding up, and the room door frame for scale. |
| 5 | 11.6 | hands, feet and even his tongue got bigger | Macro: his hands enlarging against a table, shoes bursting at the seams, and a mirror showing a thicker jaw. |
| 6 | 14.7 | shot up more than two feet in a few years | A wide orbit: he now towers over the officers, and seasons change outside the window. |
| 7 | 17.9 | his spine began to curve | An x-ray of the spine curving (scoliosis) as he stoops. |
| 8 | 20.8 | His vision blurred… struggled to hear | His POV blurs; then the camera goes to his ear as sounds muffle, and he cups his ear. |
| 9 | 24.6 | Doctors finally removed the tumor | An old operating theatre (1930s): surgeons around him, and the tumor removed from the brain (clean, non-gory). |
| 10 | 28.5 | slowed his growth, but didn't stop it | He lies in a long bed with his feet over the end; the camera slides along him. |
| 11 | 31.0 | By the time he died… seven foot eight | A tall figure beside a normal man and a door for scale, in soft light. Then a gentle pull-up over a grave in a cemetery. |
| 12 | 34.0 | both a dwarf and a giant | Final: two silhouettes, the short young man and the tall older man, side by side at dusk. The camera rises. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/DwarfGiant_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
