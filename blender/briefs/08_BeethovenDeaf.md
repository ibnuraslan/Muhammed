# Connect08: BeethovenDeaf

Branch `claude/connect08-beethoven-deaf`. Folder `blender/BeethovenDeaf_v001/`. Target length about 26.5 s, so frame_end = 1590. The script below is 69 words.

## Script (ours)

He would bite down on a metal rod attached to his piano as he played. The piano's vibrations traveled up the rod, into his jawbone, and on to his inner ear. This sent the sound straight through the bones of his skull, completely skipping his damaged eardrums, so he could still hear. And by using this trick, Beethoven was able to keep composing music, even after he went deaf.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | bite down on a metal rod | An 1820s composer with wild grey hair, a black coat and a red cravat (generic face, not a portrait copy) at a grand piano in a candlelit Viennese room. A thin brass rod runs from his teeth to the piano lid. |
| 2 | 3.9 | as he played | His hands crash across the keys; the camera orbits from the keys up the rod to his face. |
| 3 | 5.2 | vibrations traveled up the rod | Visual ripples (cyan rings) pulse from the piano up the rod as the camera rides along the rod. |
| 4 | 8.6 | into his jawbone… inner ear | X-ray dive: the skull goes translucent and the rings travel through the jaw to the cochlea. |
| 5 | 11.9 | through the bones of his skull | The skull glows as the vibration spreads. Cross-section of the ear. |
| 6 | 16.4 | skipping his damaged eardrums | The eardrum is shown dull and torn; the ripples bypass it. A red pulse marks the 'skipped' path. |
| 7 | 18.4 | so he could still hear | The cochlea lights up and his eyes close in bliss. |
| 8 | 20.1 | keep composing… even after he went deaf | Pull out and crane up overhead: candles, scattered sheet music, playing passionately. The camera spirals up. |

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
- **Deliverable tonight:** checkpoint D package in `blender/BeethovenDeaf_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
