# Connect20: HeadsetBullet

Branch `claude/connect20-headset-bullet`. Folder `blender/HeadsetBullet_v001/`. Target length about 25.0 s, so frame_end = 1500. The script below is 69 words.

## Script (ours)

A bullet was fired toward the house, smashed through the window, and headed straight for his head. But he was gaming at his desk, wearing a headset. And instead of piercing his skull, the bullet hit the headset first. The thick padding and the metal frame inside deflected the bullet, sending it safely away. Shocked, he pulled off the broken headset and realized it had just saved his life.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | A bullet was fired toward the house | A tiled-roof suburban house on a sunny lawn. A bullet streaks in slow motion with no shooter shown, and the camera chases it. |
| 2 | 2.2 | smashed through the window | Glass shatters into a slow-motion shard cloud as the camera follows through the window. |
| 3 | 4.0 | headed straight for his head | Inside: a teen at a gaming desk with a big monitor, back to us. The bullet crawls toward the back of his head. |
| 4 | 5.9 | gaming at his desk, wearing a headset | Orbit around him: hands on the keyboard and mouse, monitor glow, an over-ear headset (generic, no logo). |
| 5 | 9.5 | instead of piercing his skull | Extreme slow motion; the bullet nears his temple. |
| 6 | 11.6 | the bullet hit the headset first | Impact on the ear cup: the plastic cracks and fragments fly. |
| 7 | 13.9 | thick padding and the metal frame inside | Cutaway of the ear cup: foam padding and a metal band. The bullet compresses the foam, hits the metal and tilts. |
| 8 | 15.8 | deflected the bullet, sending it safely away | The bullet ricochets off at an angle, with sparks, and thuds into the wall behind. |
| 9 | 19.4 | pulled off the broken headset | He rips the headset off in shock and turns it in his hands: cracked cup, bent band. |
| 10 | 21.9 | realized it had just saved his life | Close-up on his stunned face, then he looks at the bullet hole in the wall. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/HeadsetBullet_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
