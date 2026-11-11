# Connect22: BelugaRescue

Branch `claude/connect22-beluga-rescue`. Folder `blender/BelugaRescue_v001/`. Target length about 36.5 s, so frame_end = 2190. The script below is 104 words.

## Script (ours)

She dove into an Arctic whale tank, but as she sank to the bottom, the freezing water sent her legs into crippling cramps, making it impossible to swim back up. But as she started to drown, a beluga whale noticed her panicking. These whales are known for being intelligent and playful with humans, and it could tell something was wrong. It swam over to the struggling woman, gently took her leg in its mouth, and began pushing her upward. And just as she was about to run out of breath, the beluga lifted her above the surface, where she could finally gasp for air.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | She dove into an Arctic whale tank | An aquarium arctic tank with icy blue water, ice-rock walls and spectators behind glass. A freediver in a grey wetsuit with fins and no tank dives in. The camera follows her down with bubbles and light rays. |
| 2 | 2.8 | as she sank to the bottom | She descends to the tiled bottom, 6 m down, as the light dims. |
| 3 | 4.4 | the freezing water sent her legs into crippling cramps | Close-up on her legs seizing and locking. X-ray flash on the calf muscles knotting (red pulse). |
| 4 | 8.7 | impossible to swim back up | She claws upward but her legs won't kick, and she sinks back. Panic bubbles. |
| 5 | 11.0 | as she started to drown | Close on her face with a mask: cheeks puffed, last bubbles escaping. |
| 6 | 12.9 | a beluga whale noticed her panicking | Reveal a white beluga gliding nearby; its head turns toward her. The camera orbits the whale. |
| 7 | 15.4 | known for being intelligent and playful | A quick vignette in the same tank: the beluga playing with a ring and nodding at a keeper by the glass. |
| 8 | 20.2 | it could tell something was wrong | The beluga's eye in close-up, then it surges toward her. |
| 9 | 22.9 | gently took her leg in its mouth | The beluga gently clamps her ankle (no teeth detail) and starts swimming up with powerful tail beats. |
| 10 | 28.3 | just as she was about to run out of breath | Her vision blurs and bubbles stop as they race up through light rays toward the surface. |
| 11 | 31.4 | lifted her above the surface | They break the surface in a splash, and the camera bursts out with them. |
| 12 | 34.2 | she could finally gasp for air | She gasps and coughs, clinging to the edge; the beluga circles beside her and spectators cheer. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/BelugaRescue_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
