# Connect05: SurgeonBrandsLivers

Branch `claude/connect05-surgeon-brands-liver`. Folder `blender/SurgeonBrandsLivers_v001/`. Target length about 28.5 s, so frame_end = 1710. The script below is 76 words.

**Probably an old-style reference.** Keep only the story; build it in our current grounded, textured style.

## Script (ours)

During a transplant, a surgeon used a high-powered laser to burn his initials into the patient's new liver. Then he stitched her up and acted like nothing had happened. But a week later, the new liver started to fail. She went back into surgery, but this time with a different doctor, who soon found the initials inside. The surgeon admitted it wasn't the first time he'd branded a patient, and he eventually lost his medical license.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | burn his initials into the… liver | Operating room. Macro of a glistening liver as a medical argon-beam tip writes two glowing letters, 'SB', with sparks and a wisp of smoke. Generic surgeon, no likeness. |
| 2 | 5.0 | stitched her up and acted like nothing had happened | Sutures close the abdomen. The surgeon lowers his mask with a smug, calm smile. |
| 3 | 9.4 | a week later | A wall calendar flips forward a week with motion blur; the camera drifts through the room. |
| 4 | 10.6 | the new liver started to fail | The woman at home doubles over, clutching her side. |
| 5 | 13.0 | back into surgery… a different doctor | Hospital bed rolling into the OR. A second surgeon, a different person, steps in. |
| 6 | 17.4 | found the initials inside | Macro: gloved hands lift the liver into light and the 'SB' brand is revealed. The doctor's eyes widen. |
| 7 | 20.5 | admitted it wasn't the first time | The first surgeon in a disciplinary hearing room, with a translucent anatomy overlay of other livers behind him. |
| 8 | 25.0 | lost his medical license | A gavel comes down and a license certificate gets a red stamp (no readable text). The camera pushes in and settles. |

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
- **Deliverable tonight:** checkpoint D package in `blender/SurgeonBrandsLivers_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
