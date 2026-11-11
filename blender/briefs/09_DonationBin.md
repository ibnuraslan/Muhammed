# Connect09: DonationBin

Branch `claude/connect09-donation-bin`. Folder `blender/DonationBin_v001/`. Target length about 41.5 s, so frame_end = 2490. The script below is 108 words.

## Script (ours)

She was reaching into a clothing donation bin when someone shoved her from behind. The heavy door slammed shut as she tumbled inside. These bins are built with one-way flaps that only swing inward. Once you drop through, the door locks behind you. There's no handle, no latch, just smooth metal walls too high to climb. She screamed for help, but nobody heard her. For three days, she lay curled up on a pile of old clothes, with no food or water. Finally, someone heard her cries, and firefighters cut her free. But this wasn't the first time. She'd already been rescued from a donation bin twice before.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | reaching into a clothing donation bin | Parking-lot alley in daylight. A large steel clothing bin (no logos). A woman on tiptoe reaches into the chute. |
| 2 | 2.5 | shoved her from behind | A figure's hands push; she tips in and the camera dives in with her. |
| 3 | 4.9 | door slammed shut… tumbled inside | Inside view: the flap slams, light cuts off, and she lands on bags of clothes. |
| 4 | 8.4 | one-way flaps that only swing inward | X-ray cutaway of the bin mechanism: the flap rotates inward only. Clean explainer moment. |
| 5 | 12.8 | the door locks behind you | The flap clacks shut; macro of the mechanism. |
| 6 | 16.0 | no handle, no latch… too high to climb | She pats smooth metal walls, jumps and slips. The camera cranes up to show the height. |
| 7 | 22.0 | screamed for help | Close on her face screaming. Pull out through the steel to the quiet empty lot; no one passes. |
| 8 | 25.0 | For three days… curled up | Time-lapse: the light through the slot cycles day, night, day. She is curled on the clothes, weaker. |
| 9 | 30.7 | someone heard her cries | A passer-by stops and leans toward the bin. |
| 10 | 33.0 | firefighters cut her free | Firefighters with a rotary cutter, sparks flying. The panel peels open and daylight floods in. |
| 11 | 34.9 | not the first time… twice before | She's helped out, wrapped in a blanket. The camera rises to reveal more bins nearby (subtle irony). Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/DonationBin_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
