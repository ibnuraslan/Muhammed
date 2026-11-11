# Connect03: LegoInNose

Branch `claude/connect03-lego-in-nose`. Folder `blender/LegoInNose_v001/`. Target length about 38.5 s, so frame_end = 2310. The script below is 97 words.

## Script (ours)

He pushed a Lego piece up his nose, and it got stuck. So he pushed a second piece into the same nostril, hoping the two would click together so he could pull them both out. It seemed like a clever plan. But instead, both pieces got stuck. His mom pulled out the bigger one, never realizing the smaller piece was still lodged deep inside. For 26 years, he battled congestion, asthma and sleep apnea, without knowing why. Then one day, while blowing his nose in the shower, the tiny Lego piece suddenly shot out, 26 years later.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | pushed a Lego piece up his nose | A 7-year-old boy on a living-room floor with a box of generic toy bricks (no logo; studs only). He pushes a brick into his nostril; cutaway of the nasal passage. |
| 2 | 4.0 | pushed a second piece | He grabs a second, smaller brick. The camera follows his hand from the box to his nose. |
| 3 | 7.6 | click together… pull them both out | Floating macro: the two bricks snap together with a click and a flash. |
| 4 | 10.5 | a clever plan | The boy looks proud, then pushes it in. Cross-section of the nasal cavity. |
| 5 | 12.6 | both pieces got stuck | Cross-section: both bricks wedge deeper, and he panics. |
| 6 | 15.8 | His mom pulled out the bigger one | Mother kneels with tweezers and pulls the larger brick free; relief. |
| 7 | 18.1 | the smaller piece… lodged deep inside | Dive into the cross-section: the small brick, glowing, sits hidden high in the passage. |
| 8 | 22.5 | For 26 years | Time-lapse. The camera orbits as the boy ages to a teen and then a 33-year-old man. Seasons and light change through the window. |
| 9 | 24.6 | congestion, asthma and sleep apnea | The man on a bench sniffing, then using an inhaler, then restless in bed at night. |
| 10 | 31.1 | blowing his nose in the shower | Bathroom, steam and water. He blows his nose. |
| 11 | 34.6 | the tiny Lego piece suddenly shot out | Slow-mo macro: the brick shoots out into his palm. He stares; the camera pulls back as he laughs in disbelief. |

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
- **Deliverable tonight:** checkpoint D package in `blender/LegoInNose_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
