# Connect15: GameBoxBullet

Branch `claude/connect15-game-box-bullet`. Folder `blender/GameBoxBullet_v001/`. Target length about 25.0 s, so frame_end = 1500. The script below is 65 words.

## Script (ours)

A stray bullet was fired toward his house and tore straight through the wall, heading right for his chest. But it slammed into his brand new video game collector's box set. The thick case cracked, the discs shattered, and layer by layer they soaked up the bullet's energy. By the time it was halfway through, the bullet had stopped, buried deep inside, saving his life.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | A stray bullet was fired toward his house | Suburban street by day, with no shooter visible. The bullet streaks across the lawn in slow motion and the camera rides behind it. |
| 2 | 2.5 | tore straight through the wall | Fly-through: the bullet punches through the siding and drywall, splinters and dust flying, and the camera follows. |
| 3 | 4.0 | heading right for his chest | Inside a gamer's bedroom (desk, monitor glow, posters with no readable text). A young man stands holding a thick box set against his chest. The bullet approaches; extreme slow motion. |
| 4 | 6.5 | slammed into his brand new… box set | Impact on the thick collector's box (generic dark embossed design, no title or logo). The front cover cracks. |
| 5 | 11.0 | The thick case cracked | Macro: cracks spider across the case. |
| 6 | 12.5 | the discs shattered | Cutaway: the bullet ploughs through stacked game discs inside, which shatter into glittering shards. |
| 7 | 14.0 | layer by layer… soaked up the bullet's energy | Tracking alongside: each layer (cardboard, manual pages, discs) bends and slows the bullet, with energy rings behind. |
| 8 | 18.0 | halfway through | Side cutaway of the whole box: the bullet sits halfway in. |
| 9 | 20.5 | stopped, buried deep inside | The bullet stops; the camera orbits close. |
| 10 | 22.5 | saving his life | Pull out: he lowers the box in shock, finds the bullet lodged in it, and looks at the camera. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/GameBoxBullet_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
