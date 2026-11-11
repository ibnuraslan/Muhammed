# Connect27: SwedishCoffee

Branch `claude/connect27-swedish-coffee`. Folder `blender/SwedishCoffee_v001/`. Target length about 44.5 s, so frame_end = 2670. The script below is 109 words.

Historical figures (18th-century Sweden): use generic faces. Show the assassination only as a masked ball, a pistol flash from behind and the king collapsing, with no blood.

## Script (ours)

The twins were about to be executed, but the king suddenly stopped it. You see, the king hated coffee and was convinced it was poison. He'd even banned it across his kingdom. So instead of killing them, he ordered one twin to drink three pots of coffee every day, while the other drank three pots of tea. Two doctors watched them for years, expecting the coffee drinker to die early. But as time passed, both doctors died first, and then the king was assassinated. Finally, the tea-drinking twin died, leaving the coffee drinker as the last survivor of the experiment. And years later, the ban on coffee was lifted.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The twins were about to be executed | An 18th-century stone courtyard with a scaffold. Two identical young men in shackles, guards and a crowd. The camera pushes in. |
| 2 | 2.8 | the king suddenly stopped it | Throne hall: the king in a powdered wig and ermine raises his hand; a guard runs out. |
| 3 | 4.9 | the king hated coffee… poison | Close on the king glaring at a steaming coffee cup; a thought image of a skull forms in the steam (3D smoke, no text). |
| 4 | 9.7 | banned it across his kingdom | Soldiers smash coffee pots and pour beans into the street; townsfolk protest. |
| 5 | 12.0 | instead of killing them | Inside a castle chamber: the twins at a table, guards behind them. |
| 6 | 13.7 | three pots of coffee every day | Twin A drinks cup after cup of black coffee; servants pour from silver pots and the camera orbits. |
| 7 | 18.3 | the other drank three pots of tea | Twin B drinks tea from fine porcelain. |
| 8 | 21.6 | Two doctors watched them for years | Two elderly doctors with quills and ledgers (no text) observing. A time-lapse: candles burn, seasons pass and the twins age. |
| 9 | 27.4 | both doctors died first | Two coffins carried out of a church; the twins attend, older now. |
| 10 | 31.1 | the king was assassinated | A masked ball with candle chandeliers: a pistol flash from behind a masked figure, the king collapses, and dancers scatter (no blood). |
| 11 | 33.3 | the tea-drinking twin died | An old twin B lies peacefully in bed; twin A, older, at his side. |
| 12 | 37.1 | coffee drinker as the last survivor | Twin A, very old, sipping coffee by a window with a smile. |
| 13 | 41.7 | the ban on coffee was lifted | A town square celebration: coffee stalls reopen, steam rises and people toast with cups. Crane up and settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/SwedishCoffee_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
