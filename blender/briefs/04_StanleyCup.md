# Connect04: StanleyCup

Branch `claude/connect04-tumbler-saves-life`. Folder `blender/StanleyCup_v001/`. Target length about 25.5 s, so frame_end = 1530. The script below is 68 words.

## Script (ours)

A bullet was fired at the house and tore straight through the wall. Inside, a woman and her fiancé froze as the stray bullet raced straight toward her. But sitting on the table between them was her trusty tumbler, full of ice water. And instead of hitting her, the bullet slammed into the cup. It sparked off the metal and dropped harmlessly to the floor, saving her life.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | A bullet was fired at the house | Exterior of a suburban clapboard house at dusk. A bullet streaks in from off-screen with no shooter visible, and the camera chases it, bullet-cam style. |
| 2 | 2.3 | tore straight through the wall | Fly-through: the bullet punches through the siding and drywall in slow motion, the camera following through the hole with splinters and dust. |
| 3 | 4.5 | a woman and her fiancé | Reveal a modern living room. A couple sit at a table; the camera skims past the bullet toward them. |
| 4 | 6.5 | froze… raced straight toward her | Extreme slow-mo: her face goes wide-eyed, he reaches out, and the bullet crawls through the air. |
| 5 | 10.1 | her trusty tumbler, full of ice water | Rack focus to a large insulated steel tumbler with a handle and straw (generic, no logo) on the table between them. Ice cubes and condensation. |
| 6 | 16.2 | the bullet slammed into the cup | Macro impact: the metal dents, sparks burst and water ripples inside. |
| 7 | 21.4 | dropped harmlessly to the floor | The deformed bullet tumbles off and bounces on the wooden floor as the camera follows it down. |
| 8 | 23.6 | saving her life | Rise up to the woman, shaken, hand on her chest, holding the dented tumbler. |

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
- **Deliverable tonight:** checkpoint D package in `blender/StanleyCup_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
