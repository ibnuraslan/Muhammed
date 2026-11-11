# Connect02: MonkeyHeadTransplant

Branch `claude/connect02-monkey-head-transplant`. Folder `blender/MonkeyHeadTransplant_v001/`. Target length about 29.5 s, so frame_end = 1770. The script below is 80 words.

## Script (ours)

In 1970, a surgeon removed the head of a monkey and attached it to the body of another one. He spent hours carefully joining the tissue in the neck to the new head. And incredibly, the monkey survived. It woke up, and it could still see and hear. But the spinal cord couldn't be reconnected, so the monkey couldn't move its body at all. The operation was technically a success, but the monkey only lived for a few more days.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | In 1970, a surgeon removed the head | A rhesus-like monkey on a 1970s operating table under an old surgical lamp, with a cyan studio gradient beyond. A neck line is marked. Clinical, no blood spray. |
| 2 | 4.3 | attached it to the body of another one | A second, ginger-furred monkey body on the next table. The head is placed onto the new body, and the camera cranes over the top. |
| 3 | 6.5 | carefully joining the tissue in the neck | Macro orbit around the neck seam as a needle and thread stitch it closed, with tools moving and lamp light glinting. |
| 4 | 11.2 | incredibly, the monkey survived | Slow push-in to the face as the eyes flicker open and blink. |
| 5 | 14.8 | could still see and hear | Eyes track the camera and an ear twitches toward a sound. The camera orbits. |
| 6 | 17.1 | spinal cord couldn't be reconnected | X-ray: the body turns translucent green, glowing brain and spine, with a visible gap at the neck. |
| 7 | 20.1 | couldn't move its body at all | Pull back to a wide: the monkey slumped in a chair, arms limp, only the eyes moving. |
| 8 | 23.2 | technically a success | Camera drifts to a 1970s heart monitor with a beeping trace. |
| 9 | 26.0 | only lived for a few more days | The trace slows to flat as the light dims. Slow pull-out. |

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
- **Deliverable tonight:** checkpoint D package in `blender/MonkeyHeadTransplant_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
