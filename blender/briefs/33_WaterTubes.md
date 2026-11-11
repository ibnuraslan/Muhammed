# Connect33: WaterTubes

Branch `claude/connect33-water-tubes`. Folder `blender/WaterTubes_v001/`. Target length about 33.5 s, so frame_end = 2010. The script below is 87 words.

No numbers or text on screen; show the weight with a cutaway and a pressure explainer. Use real CC-BY house models for the neighbourhood.

## Script (ours)

He filled a long tube with water in his front yard, then added more tubes until his entire house was surrounded. Then floodwater began rushing into the neighbourhood. Other homes were damaged, but at his house, the thousands of gallons of water inside the tubes made them incredibly heavy, too heavy for the flood to push through. The water hit the barrier and flowed around it instead. When it was finally over, nearby homes were wrecked, but his house stood dry, saved by water holding back water.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | filled a long tube with water | A suburban front yard with storm clouds gathering. A man unrolls a long dark flexible tube and a garden hose fills it, the tube swelling. |
| 2 | 3.7 | added more tubes until his entire house was surrounded | Crane up: tubes snake around the whole house in a ring. |
| 3 | 8.3 | floodwater began rushing into the neighbourhood | Brown floodwater surges down the street, carrying debris, bins and a floating car. |
| 4 | 11.8 | Other homes were damaged | Water pours into neighbours' garages and doors; fences topple. |
| 5 | 13.6 | at his house… gallons of water inside the tubes | Cutaway of the tube cross-section: filled with water, sagging heavy on the ground. |
| 6 | 17.2 | too heavy for the flood to push through | Explainer: arrows of flood force pushing against the tube, and the tube's weight pressing down and holding. |
| 7 | 21.4 | hit the barrier and flowed around it | The flood front slams into the tube ring and curls around, splashing, while inside stays dry grass. |
| 8 | 24.5 | When it was finally over | Aftermath: water recedes, mud and debris everywhere. |
| 9 | 26.4 | nearby homes were destroyed | A neighbour's house is wrecked: mud lines on the walls and furniture on the lawn. |
| 10 | 28.2 | his house stood dry | Inside the ring, his green lawn is dry and he stands on the porch amazed. |
| 11 | 30.3 | saved by water holding back water | Drone pull-up: a dry circle in a flooded neighbourhood. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/WaterTubes_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
