# Connect10: BellyFat

Branch `claude/connect10-belly-fat`. Folder `blender/BellyFat_v001/`. Target length about 21.5 s, so frame_end = 1290. The script below is 67 words.

## Script (ours)

A stray bullet struck her right in the stomach. It pierced her skin, but started to slow down as it pushed into her body fat. Layer by layer, the fat absorbed more of the bullet's energy, like a cushion. And by the time it reached deeper tissue, the bullet had lost most of its force, coming to a stop before it hit any organs, saving her life.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | A stray bullet struck her | Bright supermarket aisle. A plus-size woman shopping. A bullet streaks in from off-screen (no shooter) in slow motion and the camera rides with it. |
| 2 | 2.0 | right in the stomach | Impact on her shirt at the belly. The camera dives into the wound and becomes a cross-section. |
| 3 | 3.0 | pierced her skin… slow down | Cross-section: skin layer, then thick yellow fat tissue. The bullet ploughs in and decelerates. |
| 4 | 7.8 | Layer by layer… like a cushion | The camera tracks alongside: fat lobules compress and ripple, and energy rings bloom behind the bullet. |
| 5 | 12.6 | reached deeper tissue | Red muscle layer ahead; the bullet barely creeps. |
| 6 | 14.8 | lost most of its force… stop | It stops just short of the glistening intestines; the camera orbits the bullet. |
| 7 | 20.1 | saving her life | Pull out through the layers to the woman, alive and shocked, holding her side. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/BellyFat_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
