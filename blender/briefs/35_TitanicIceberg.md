# Connect35: TitanicIceberg

Branch `claude/connect35-titanic-iceberg`. Folder `blender/TitanicIceberg_v001/`. Target length about 30.5 s, so frame_end = 1830. The script below is 90 words.

No ship names or text. A 1912 period look. The Titanic sinking is shown as a ghost replay, without people in the water.

## Script (ours)

He took a photo of an iceberg, claiming it was the exact one that sank the Titanic. You see, it was streaked with red, with one big smear along the ice, and his ship was sailing near where the Titanic had gone down just the day before. So it was most likely the same iceberg. When the film was developed, experts studied the image carefully. The red streaks lined up with the height of the Titanic's hull paint, leading many to believe this was the iceberg that sank the Titanic.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | He took a photo of an iceberg | The North Atlantic at dawn in April 1912: a steward in uniform on the deck of a steamship raises an old bellows camera at a massive jagged iceberg with mist. |
| 2 | 2.0 | the exact one that sank the Titanic | A slow push toward the iceberg. A ghost overlay of a great four-funnel liner passing beside it at night. |
| 3 | 5.8 | streaked with red, with one big smear | Macro along the ice: a dark red smear streak at the waterline height, with ice texture and crystals. |
| 4 | 10.2 | his ship was near where the Titanic had gone down | An aerial pull-up over the dark ocean: floating debris (deck chairs, wood) and the steamship approaching. |
| 5 | 15.2 | most likely the same iceberg | A ghost replay: the liner scraping along the berg at night, with sparks and ice falling, and the red paint transferring to the ice. |
| 6 | 18.2 | When the film was developed | A darkroom with red safelight: a photo print emerging in the developer tray. |
| 7 | 20.0 | experts studied the image carefully | An office with a magnifying glass over the photo and experts leaning in. |
| 8 | 22.3 | red streaks lined up with the height of the hull | Explainer: a ghost liner hull aligns beside the iceberg photo and the red paint band matches the streak. |
| 9 | 25.5 | many believe this was the iceberg | Final: the iceberg alone in the fog, drifting; the camera slowly orbits. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/TitanicIceberg_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
