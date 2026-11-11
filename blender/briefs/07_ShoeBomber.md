# Connect07: ShoeBomber

Branch `claude/connect07-shoe-bomber`. Folder `blender/ShoeBomber_v001/`. Target length about 27.0 s, so frame_end = 1620. The script below is 80 words.

## Script (ours)

In the middle of a flight, he tried to set his shoe on fire. But a flight attendant smelled burning matches and caught him in the act. Passengers and crew tackled him to the floor, and he was finally sedated. When they checked his shoes, they found a fuse sticking out of each one. Both shoes were packed with enough explosives to bring down the entire plane. And that's why you have to take your shoes off at the airport.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | set his shoe on fire | Airliner cabin at night, window seat. A tall man hunched over, striking a match near his raised sneaker. |
| 2 | 3.3 | smelled burning matches | A flight attendant in the aisle stops and sniffs, and the camera whips to her face. |
| 3 | 6.2 | caught him in the act | Her POV over the seat: match flame at the shoe. |
| 4 | 8.0 | tackled him to the floor | Struggle: passengers and crew pile on and pin him in the aisle, with seats and a dropped tray. Physical but not violent; no injuries. |
| 5 | 10.9 | finally sedated | Close: a syringe into his upper arm and he goes limp. |
| 6 | 12.8 | checked his shoes | The attendant lifts the sneakers. Macro: a fuse cord pokes out of each sole. |
| 7 | 17.8 | packed with enough explosives | The shoe floats in a cyan studio and splits into a cutaway: the sole hides a grey putty slab. Abstract only, no wiring or real device detail. |
| 8 | 20.8 | bring down the entire plane | The plane in the sky; a dramatic pull-out showing its scale (no explosion). |
| 9 | 23.2 | take your shoes off at the airport | Modern airport security: a traveller puts sneakers in a grey tray on the X-ray belt, and the camera settles on him. |

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
- **Deliverable tonight:** checkpoint D package in `blender/ShoeBomber_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
