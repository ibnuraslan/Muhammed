# Connect14: ElectricianPolice

Branch `claude/connect14-electrician-police`. Folder `blender/ElectricianPolice_v001/`. Target length about 26.0 s, so frame_end = 1560. The script below is 73 words.

## Script (ours)

He was riding his motorcycle without a helmet, and the police gave him a fine. But he was an electrician with access to the power grid. So he checked the records and found that the police station hadn't paid its electricity bill in three years. And that bill was huge, so he cut off their power. For five hours, the police station sat in the dark, all because they fined the wrong guy.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | riding his motorcycle without a helmet | A busy Indian town road by day: auto-rickshaws, dust, stalls. A man in a red shirt on a small motorcycle, no helmet, hair blowing. The camera chases alongside. |
| 2 | 2.8 | the police gave him a fine | A traffic officer in khaki waves him over. They stop; the officer writes a ticket and hands it over. He's annoyed. |
| 3 | 4.7 | he was an electrician | He pulls on a hard hat and hi-vis vest. A whip-pan reveals him at a substation fence, with transformers buzzing. |
| 4 | 6.6 | access to the power grid | The camera cranes up the pylons and lines spreading over the town. |
| 5 | 8.4 | checked the records | A small utility office: he types on a laptop. The screen shows rows of building icons and bars, with no readable text. |
| 6 | 10.3 | the police station hadn't paid… three years | One row glows red, with a police-badge icon and three calendar pages flipping. He leans in with a slow grin. |
| 7 | 14.9 | that bill was huge | The red bar grows huge, pushing off the screen; he sits back in delight. |
| 8 | 17.6 | he cut off their power | At the switchgear cabinet, his gloved hand throws a big lever with sparks and a clunk. |
| 9 | 19.4 | the police station sat in the dark | Fly over the rooftops to the police station as its windows go dark one by one. |
| 10 | 20.5 | For five hours | Inside: officers in the dark, fanning themselves with papers, one holding a phone torch. A wall clock spins five hours. |
| 11 | 23.0 | they fined the wrong guy | Outside at dusk he strolls past the dark station, hands in pockets, and smirks at the camera. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/ElectricianPolice_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
