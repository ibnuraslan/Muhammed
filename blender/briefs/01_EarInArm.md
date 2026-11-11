# Connect01: EarInArm

Branch `claude/connect01-ear-in-arm`. Folder `blender/EarInArm_v001/`. Target length about 29.5 s, so frame_end = 1770. The script below is 90 words.

## Script (ours)

Lose an ear in an accident, and doctors can actually grow you a new one. A surgeon takes some cartilage from your rib cage and carves it into the shape of an ear. Then it's slipped into a pocket of skin on your forearm. Inside your arm, it grows new blood vessels and skin. Once it's fully developed, the new ear is removed from your arm. The blood vessels are connected beside your ear canal, and the skin is carefully stitched to your head, giving you a brand new ear.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | Lose an ear… | Bald adult man in a plain tee, side profile. Torn ear area is a clean bandaged wound, not graphic. Camera pushes from a wide on his shocked face to the bandage. |
| 2 | 2.1 | A surgeon takes… rib cage | Camera dives through his chest into a clean cross-section of the rib cage. A gloved scalpel lifts out a block of pale cartilage. |
| 3 | 5.7 | carves it into the shape of an ear | Surgeon in scrubs and mask carves the block. Shavings fly, and the ear shape emerges. The camera orbits his hands. |
| 4 | 9.4 | slipped into a pocket of skin on your forearm | Macro: the forearm incision opens and the cartilage ear slides into the pocket. The skin closes into a bump. |
| 5 | 12.9 | Inside your arm… blood vessels… skin | X-ray dive under the skin. Red vessels grow over the cartilage and pink skin creeps across it; tissue gently pulses. |
| 6 | 17.7 | cut free from your arm | Pull back to the arm. The incision opens and the finished pink ear is lifted out with forceps. |
| 7 | 21.8 | connected beside your ear canal | Fly to the head. The ear is lowered into place and the vessels reach and join, with a small glow on the join. |
| 8 | 25.0 | carefully stitched to your head | Macro on the stitches. The needle pulls through and stitches appear in sequence along the edge. |
| 9 | 27.4 | giving you a brand new ear | Pull out and orbit to the front: he touches the new ear and smiles, and the camera settles. |

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
- **Deliverable tonight:** checkpoint D package in `blender/EarInArm_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
