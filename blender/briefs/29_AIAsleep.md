# Connect29: AIAsleep

Branch `claude/connect29-ai-asleep`. Folder `blender/AIAsleep_v001/`. Target length about 43.5 s, so frame_end = 2610. The script below is 107 words.

Respectful depiction: a generic East Asian man, never a caricature. Eye anatomy must be accurate and dignified. The car UI is icons only (a red eye icon); no 'WAKE UP' text.

## Script (ours)

As he drove, the car's AI scanned his face and flashed red, warning him to wake up. He was confused, because he wasn't sleeping, so he sat up straighter to look more alert. But nothing worked until he forced his eyes wide open. The moment they relaxed, the alarm went off again, twenty times on a single trip. You see, the AI was designed to beep whenever it couldn't see the iris. But the man naturally had epicanthic folds, where the skin of the upper eyelid overlaps near the nose, forming a smooth flap that covers part of the iris, making the AI think he was asleep.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | As he drove, the car's AI scanned his face | Night highway in a modern car interior. A dashboard camera's scanning beam sweeps his face; a face-mesh overlay ghosts on his skin. |
| 2 | 3.9 | flashed red, warning him to wake up | The dash screen flashes red with a closed-eye icon and an alarm pulse; red light floods the cabin. |
| 3 | 6.9 | confused, because he wasn't sleeping | Close on his face: puzzled, eyes open and normal, looking at the screen. |
| 4 | 10.1 | sat up straighter to look more alert | He adjusts posture, shakes his head and grips the wheel. The camera orbits the cabin. |
| 5 | 13.0 | nothing worked until he forced his eyes wide open | He widens his eyes comically; the screen turns green. |
| 6 | 18.0 | The moment they relaxed, the alarm went off again | His eyes relax and red floods again. Frustrated, he exhales. |
| 7 | 21.7 | twenty times on a single trip | A time-lapse drive: highway lights streaking, the red flash recurring rhythmically, a cityscape passing. |
| 8 | 24.4 | designed to beep whenever it couldn't see the iris | Explainer: inside the AI's view, a camera feed with a tracking box around the eye and the iris circle detection. |
| 9 | 28.8 | naturally had epicanthic folds | Macro on his eye: realistic eyelid skin. A cross-section dive shows the upper lid's skin and fat layer folding over the inner corner. |
| 10 | 36.9 | forming a smooth flap that covers part of the iris | Macro: the fold partially covers the iris near the nose, and the detection circle fails and flickers red. |
| 11 | 40.8 | making the AI think he was asleep | Pull back to the cabin: he sighs, the red icon blinks, and the car drives on into the night. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/AIAsleep_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
