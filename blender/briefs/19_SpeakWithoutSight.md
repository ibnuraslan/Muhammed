# Connect19: SpeakWithoutSight

Branch `claude/connect19-speak-without-sight`. Folder `blender/SpeakWithoutSight_v001/`. Target length about 33.0 s, so frame_end = 1980. The script below is 93 words.

## Script (ours)

She lost her sight and hearing as a baby, leaving her trapped inside her own head, with no way to communicate. So her teacher placed the girl's hand on her throat and began to speak. The vibrations told her when a sound was being made, and how strong or soft it was. Then she moved her fingers to her teacher's lips and nose, feeling the different shapes they made for each word. And she practiced those same movements on her own face, over and over again, until she was finally able to speak.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | lost her sight and hearing as a baby | A late-1800s parlour: a girl of about 10 in a period dress sits in a chair, eyes unfocused. Around her, life goes on (family, a clock, a dog barking) but she reacts to none of it. |
| 2 | 2.7 | trapped inside her own head | The camera pushes into her face; the world dims and falls silent around her, a dark bubble with only touch. |
| 3 | 6.6 | her teacher placed the girl's hand on her throat | A young woman teacher in a period blouse kneels and guides the girl's hand to her own throat. Hand contact is clear. |
| 4 | 9.9 | began to speak | The teacher speaks slowly with mouth shapes clear. |
| 5 | 11.6 | The vibrations told her | X-ray: glowing pulse dots travel from the teacher's throat into the girl's fingertips and up her arm. |
| 6 | 14.9 | how strong or soft it was | The pulses swell big and bright, then small and gentle, as the teacher's voice changes. The girl's face reacts. |
| 7 | 17.7 | moved her fingers to her teacher's lips and nose | The girl's fingertips explore the teacher's lips and nose; macro on fingertips and lips. |
| 8 | 21.0 | different shapes… for each word | The lips form distinct shapes (O, E, M), each lighting faint contour lines under her fingers. |
| 9 | 24.2 | practiced those same movements on her own face | The girl touches her own lips and throat and mimics the shapes. |
| 10 | 28.7 | over and over again | Time-lapse: seasons through the window, the lamp lit and unlit, the girl's posture growing confident. |
| 11 | 30.7 | until she was finally able to speak | She speaks her first word, hand on her own throat, as pulses light her throat. The teacher gasps with joy and hugs her. Settle. |

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
  - Medical "inside the body" beats use the clean explainer look: a deep teal-to-navy studio gradient behind realistic anatomy and studio lighting.
  - Real-world beats use real sets.
- **Deliverable tonight:** checkpoint D package in `blender/SpeakWithoutSight_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
