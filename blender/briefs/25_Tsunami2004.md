# Connect25: Tsunami2004

Branch `claude/connect25-tsunami-2004`. Folder `blender/Tsunami2004_v001/`. Target length about 40.0 s, so frame_end = 2400. The script below is 88 words.

**Sensitive:** a real mass-casualty disaster. Show people fleeing and destruction, never bodies or people being hit. The tone is respectful, with a quiet ending.

## Script (ours)

The sea began pulling back fast, exposing the ocean floor. People on the beach were confused, and then they noticed a wave coming toward the shore. This was a massive tsunami, triggered by an undersea earthquake. As the wave got closer, it grew taller, reaching up to 100 feet in some places. It slammed into the coast with unimaginable force, destroying everything in its path. The wave swept entire neighbourhoods away, leaving nothing behind but rubble. And in this region alone, more than 167,000 people lost their lives.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The sea began pulling back fast | Tropical beach morning: palms, fishing boats, umbrellas, tourists and locals. The waterline races out and the camera rides low over the retreating water. |
| 2 | 3.0 | exposing the ocean floor | The exposed seabed: stranded fish flapping, coral, boats tipped on the sand. |
| 3 | 5.3 | People on the beach were confused | People walk out onto the wet sand, pointing and picking up fish; kids run around. |
| 4 | 7.2 | noticed a wave coming toward the shore | On the horizon, a white line grows. Faces turn and one man shouts. |
| 5 | 10.8 | a massive tsunami | The camera rises high above the coast and sees the wave front stretching across the ocean. |
| 6 | 13.1 | triggered by an undersea earthquake | Dive into the ocean: a cross-section of the seafloor shows tectonic plates slipping and the seabed thrusting up, pushing the water column into a bulge. |
| 7 | 15.6 | As the wave got closer, it grew taller | Back at the surface: the wave rears as it hits shallow water, a towering dark wall with spray. |
| 8 | 18.3 | up to 100 feet in some places | A low angle from the beach as the wall towers over the palms and a three-storey hotel for scale. People flee. |
| 9 | 21.5 | slammed into the coast with unimaginable force | Impact: water explodes through the hotel ground floor, boats and cars tumble and palms snap (no people being hit). |
| 10 | 25.7 | destroying everything in its path | The camera rides the surge inland through streets of debris. |
| 11 | 28.0 | swept entire neighbourhoods away | Aerial pull-up over a whole town as the water churns through it and houses dissolve. |
| 12 | 31.4 | leaving nothing behind but rubble | Aftermath: still water and rubble fields, a lone standing mosque or house among the debris, dust in the light. |
| 13 | 33.8 | more than 167,000 people lost their lives | A slow, quiet crane up over the devastated coast at golden hour. Settle into stillness. |

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
- **Deliverable tonight:** checkpoint D package in `blender/Tsunami2004_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
