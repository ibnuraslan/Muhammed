# Connect17: ToddlerWell

Branch `claude/connect17-toddler-well`. Folder `blender/ToddlerWell_v001/`. Target length about 32.5 s, so frame_end = 1950. The script below is 98 words.

## Script (ours)

The toddler fell 50 feet down a narrow well. Rescuers lowered ropes, trying to loop them around the little boy. They even brought in heavy machinery to dig the pipe out. But after 11 hours, they had only dug a few feet down. Finally, a teenager passing by offered to go in himself. A rope was tied around his waist, and he was lowered in head first. With a flashlight strapped to his forehead, he reached out his arms and grabbed the child. And when they pulled him back to the surface, he brought the toddler up alive.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The toddler fell 50 feet down a narrow well | Dusty farm field with trees and a small round well-pipe opening. The toddler steps too close and slips in. The camera dives down the shaft with him; he lands unhurt, crying, arms up. |
| 2 | 4.0 | Rescuers lowered ropes | Up top, rescuers in hi-vis vests and hard hats lower a looped rope. Shaft view: the loop dangles and misses his arms. |
| 3 | 7.7 | heavy machinery to dig the pipe out | Wide: an excavator rolls in and digs beside the well, with dirt flying and the crowd behind a tape line. |
| 4 | 11.2 | after 11 hours… a few feet down | Time-lapse: the sun crosses the sky, the hole grows only a little, and the workers are exhausted. |
| 5 | 15.2 | a teenager passing by offered to go in himself | A slim teen pushes through the crowd, hand raised, and talks to the rescuers. |
| 6 | 18.9 | A rope was tied around his waist | Close-up on the hands knotting the rope around his waist. |
| 7 | 21.6 | lowered in head first | Rescuers hold his legs and lower him upside down into the pipe. The camera follows down beside him. |
| 8 | 22.6 | flashlight strapped to his forehead | His head torch beam swings across the shaft walls: dust, roots and trickling sand. |
| 9 | 25.0 | reached out his arms and grabbed the child | Bottom of the shaft: his hands reach and grip the toddler's arms; the toddler clings. |
| 10 | 27.1 | pulled him back to the surface | Cross-section side view: the rope tightens and they rise together. Up top, the crew hauls hand over hand. |
| 11 | 29.4 | brought the toddler up alive | Both emerge to cheers; the teen holds the toddler up and the mother rushes in. Crane up and settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/ToddlerWell_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
