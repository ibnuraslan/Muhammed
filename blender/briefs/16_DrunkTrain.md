# Connect16: DrunkTrain

Branch `claude/connect16-drunk-train`. Folder `blender/DrunkTrain_v001/`. Target length about 34.5 s, so frame_end = 2070. The script below is 96 words.

**Sensitive:** show the train impact as motion and force only, never injury detail. The ending reveals he's fine apart from a few small cuts.

## Script (ours)

He stumbled drunk across the train tracks and passed out with his head resting on the rail. Within seconds, a cargo train came rushing toward him. It slammed into his head, spinning him around and dragging him beneath the train. When it finally screeched to a stop, witnesses were sure he was dead. But then, he stood up. Because he was so drunk, his muscles were completely relaxed and his limbs were loose, so his body moved with the train's force instead of fighting it. He walked away with only a few cuts on his hand.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | He stumbled drunk across the train tracks | Suburban rail line in bright daylight, with gravel ballast and houses beyond. A young man in a bright tee and shorts staggers and trips over the rail with big off-balance stumbling. The camera weaves with him. |
| 2 | 2.5 | passed out with his head resting on the rail | He collapses and lies with his head on the steel rail. Snore breathing. Close-up low along the rail. |
| 3 | 5.5 | a cargo train came rushing toward him | Along-the-rail low shot: the rail starts to vibrate, gravel bounces, and a huge freight locomotive (no livery text) looms with horn and headlight. |
| 4 | 9.0 | slammed into his head, spinning him around | The impact is shown with motion blur and debris and no injury detail. His body spins like a rag doll. |
| 5 | 11.0 | dragging him beneath the train | Under the train: wheels, sparks and darkness. The camera skims beside him as he tumbles among the bogies (dark, fast, readable but not graphic). |
| 6 | 14.5 | finally screeched to a stop | Wheels lock, sparks shower and the train grinds to a halt. Dust settles. |
| 7 | 17.0 | witnesses were sure he was dead | Bystanders and a rail worker in a hi-vis vest run up, hands to their mouths. |
| 8 | 19.5 | But then, he stood up | Under the wagon he stirs, crawls out and stands up wobbling, blinking. The bystanders stagger back. |
| 9 | 21.0 | Because he was so drunk | Rewind-style: a quick flash of him swigging from an unlabelled bottle. |
| 10 | 23.5 | muscles completely relaxed… limbs loose | X-ray explainer: his body goes translucent and the muscles show loose and relaxed, swaying like rope. |
| 11 | 26.5 | moved with the train's force | Replay in slow motion with the x-ray on: force arrows from the train, and his limp body flowing with them instead of resisting. |
| 12 | 31.0 | walked away with only a few cuts on his hand | Back to the real scene: he wanders off along the platform and looks at his palm (a few small cuts, clean). Settle on his dazed grin. |

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
- **Deliverable tonight:** checkpoint D package in `blender/DrunkTrain_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
