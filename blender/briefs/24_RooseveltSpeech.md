# Connect24: RooseveltSpeech

Branch `claude/connect24-roosevelt-speech`. Folder `blender/RooseveltSpeech_v001/`. Target length about 25.0 s, so frame_end = 1500. The script below is 68 words.

**Historical figure:** period clothes and a moustache with round spectacles are fine. Don't copy a portrait likeness. Show the wound only as a small hole and a dark spot on the shirt; no blood flow.

## Script (ours)

The bullet hit him in what should have been a deadly spot, but somehow, he stayed on his feet. So how was that possible? Well, Roosevelt had a thick, folded-up speech in his coat pocket, along with a metal glasses case. The bullet tore through both, which slowed it down and kept it from reaching his lungs. And despite the wound, he insisted on finishing his 90-minute speech.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | The bullet hit him in what should have been a deadly spot | 1912 Milwaukee: night street outside a hotel, crowds, car headlamps. A stout man in a dark overcoat stands in an open car waving his hat. Muzzle flash from the crowd (shooter as a silhouette), and the bullet in slow motion hits his chest. He jolts. |
| 2 | 3.1 | somehow, he stayed on his feet | He sways, then plants his feet and straightens. The crowd gasps. |
| 3 | 5.6 | So how was that possible? | Freeze-frame feel: the world slows nearly to a stop and the camera glides around him to his coat. |
| 4 | 7.4 | a thick, folded-up speech in his coat pocket | Dive through the coat into an x-ray cutaway: a thick folded paper manuscript in the breast pocket. |
| 5 | 12.0 | along with a metal glasses case | Beside it, a steel spectacle case. |
| 6 | 14.6 | The bullet tore through both | Slow-motion cutaway: the bullet punches through about 50 sheets of paper, shredding and slowing, then dents the steel case. |
| 7 | 16.7 | kept it from reaching his lungs | X-ray: the ribs and lungs behind, and the bullet stopping in the chest muscle short of the lung. |
| 8 | 19.8 | despite the wound | Pull out of the cutaway: at the auditorium podium, he lifts the bullet-holed manuscript to the audience. |
| 9 | 21.4 | insisted on finishing his 90-minute speech | He speaks passionately to a packed hall with flags and bunting, fist raised, and the crowd roars. A clock spins. Crane up and settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/RooseveltSpeech_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
