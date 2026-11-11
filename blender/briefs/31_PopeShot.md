# Connect31: PopeShot

Branch `claude/connect31-pope-shot`. Folder `blender/PopeShot_v001/`. Target length about 27.0 s, so frame_end = 1620. The script below is 81 words.

Real historical event (1981): the Pope is shown in generic white papal robes, never a portrait likeness. **No blood and no wound close-ups**: the shot is a flash from the crowd, the bullet path is shown in x-ray only, and he collapses into aides' arms. Respectful tone.

## Script (ours)

He fired straight at the Pope in the middle of a crowded square. Two bullets tore through, hitting him in the stomach and hand. He collapsed, badly wounded, but survived after emergency surgery. And years later, the Pope publicly forgave the man who shot him, and even met him face to face in his prison cell. He later had one of the bullets placed in the crown of a statue, believing that God had guided it away from his vital organs.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | He fired straight at the Pope | A sunlit 1980s square with colonnades, a huge crowd and flags. The Pope stands in an open white vehicle waving. A hand with a pistol rises from the crowd (from behind, out of focus); muzzle flash. |
| 2 | 4.4 | Two bullets… stomach and hand | Slow-motion bullet ride, then an x-ray porthole on his torso: the bullet path passes through the abdomen, shown clinically in x-ray only, and a hand x-ray shows the second path. |
| 3 | 8.4 | He collapsed, badly wounded | He sags into the arms of aides; the crowd gasps, pigeons scatter, security rushes. No blood. |
| 4 | 10.5 | survived after emergency surgery | A hospital operating theatre: surgeons, monitors and a heartbeat trace stabilising (x-ray dome look). |
| 5 | 12.7 | years later… publicly forgave | Years later: the Pope speaks at a balcony to a crowd, hand raised in blessing. |
| 6 | 16.9 | met him face to face in his prison cell | A bare prison cell: two men sitting close on chairs, talking quietly, hand on shoulder. Warm window light; a slow orbit. |
| 7 | 19.2 | bullet placed in the crown of a statue | A church shrine: an ornate gold crown on a statue of Mary. Macro: a small bullet set among the gems. |
| 8 | 22.9 | God had guided it away from his vital organs | The x-ray returns: the bullet path curving just past the vital organs (aorta, spine), glowing softly. Pull out to the statue in candlelight. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/PopeShot_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
