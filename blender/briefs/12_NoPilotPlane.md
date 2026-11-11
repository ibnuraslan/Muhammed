# Connect12: NoPilotPlane

Branch `claude/connect12-no-pilot-plane`. Folder `blender/NoPilotPlane_v001/`. Target length about 72.5 s, so frame_end = 4350. The script below is 183 words.

**Format:** a first-person POV hypothetical. The camera is your head, and your hands appear in frame. It's long (72 s), so blocking speed matters. Reuse the cabin and cockpit sets, and keep the cockpit instruments as symbols with no readable text.

## Script (ours)

Imagine you wake up and everyone on your flight is unconscious. But the plane is still flying perfectly level. So the pilots must be fine, right? You make your way to the cockpit. One pilot has collapsed in the doorway. The other is slumped over in his seat. This could be a dream, but you grab the radio and scream for help anyway. No one answers. You decide to pull the pilot out of his seat, but his arm catches the controls and jerks them. Alarms blare. Lights flash. The plane is diving fast. You grab the controls. They're heavy and confusing. But after a few terrifying minutes, you sort of figure it out. You're keeping the plane roughly level, but it's still slowly losing height. Now you're low enough to see a long stretch of open field. You could try to land right now. You've got a feel for the controls, and you think you could work out the throttle. Or you could keep flying and hope someone wakes up. But this field might be your only chance. What do you do?

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | Imagine you wake up | FIRST-PERSON POV (head-mounted camera, your hands visible) in an airliner cabin by day. You stir and look around: every passenger is slumped asleep, heads lolling, a drink tipping in a tray table. |
| 2 | 5.8 | flying perfectly level | Look out of the window: a level horizon, clouds and fields far below. |
| 3 | 9.0 | the pilots must be fine, right? | Stand up and walk the aisle with natural head bob, past unconscious passengers and dangling headphones. |
| 4 | 12.0 | You make your way to the cockpit | Reach the cockpit door (no text) and push it open. |
| 5 | 14.1 | One pilot has collapsed in the doorway | Look down at a pilot crumpled on the floor; step over him. |
| 6 | 16.8 | The other is slumped over in his seat | The co-pilot is slumped against the side window. |
| 7 | 19.7 | grab the radio and scream for help | Your hand grabs the handset and holds it to your mouth (shake of panic). Static. |
| 8 | 25.2 | No one answers | Silence: the radio panel lights blink. |
| 9 | 26.9 | pull the pilot out of his seat | Your hands grip the pilot's shoulders and haul; his arm snags the yoke and shoves it forward. |
| 10 | 33.7 | Alarms blare. Lights flash. | Red warning lights strobe and the cabin shakes. The horizon tilts and the nose drops. |
| 11 | 36.5 | diving fast | Through the windscreen the ground rushes up; a city spins below. |
| 12 | 38.8 | You grab the controls… heavy and confusing | Sit in the seat, both hands on the yoke, arms straining. Gauges spin (symbols only, no readable text). |
| 13 | 42.5 | you sort of figure it out | Pull back slowly; the horizon creeps level and your breathing calms. |
| 14 | 47.1 | roughly level… still slowly losing height | An altimeter needle (no numbers) unwinds slowly. The ground is closer. |
| 15 | 53.5 | a long stretch of open field | Through the windscreen: a long green field beyond the town. |
| 16 | 56.8 | You could try to land right now | Your hand hovers over the throttle levers, then the field, then the yoke: an indecisive look around. |
| 17 | 64.6 | keep flying and hope someone wakes up | Look back over your shoulder at the unconscious crew and the cabin. |
| 18 | 68.9 | this field might be your only chance | Turn back to the field filling the windscreen, sunlight flaring. |
| 19 | 71.9 | What do you do? | Final beat: the camera floats out of your head and turns around to show your own face (a generic young man, wide-eyed) in the pilot seat. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/NoPilotPlane_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
