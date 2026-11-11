# Connect23: CaveRescue

Branch `claude/connect23-cave-rescue`. Folder `blender/CaveRescue_v001/`. Target length about 51.5 s, so frame_end = 3090. The script below is 114 words.

**Sensitive:** a real tragedy with a real fallen diver. Don't depict the death. Show a lone diver's light fading into dark water, then a respectful pause. Everyone is generic. Use no text on screen, including '2 miles'; show distance with a glowing route line.

## Script (ours)

In 2018, a group of boys and their soccer coach were exploring a cave in Thailand when heavy rain suddenly flooded the tunnels, trapping them inside. They were more than two miles in, and the narrow passages leading out were now completely underwater. After 10 days, divers finally found them, but the flooded tunnels were so dangerous that even a skilled diver died during the operation. Swimming the boys out themselves seemed impossible. So rescuers chose a last resort. They sedated the boys, fitted them with full-face diving masks, and carried their unconscious bodies through the tunnels, one by one. All 12 boys and their coach made it out alive, after 18 days underground.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | In 2018, a group of boys and their soccer coach | Jungle hillside in Thailand, wet and green. Boys aged 11–16 with bikes and a young coach walk into a limestone cave mouth with torches. The camera follows them in. |
| 2 | 4.9 | heavy rain suddenly flooded the tunnels | Outside: monsoon rain. Inside: water surges through the passages behind them; they run deeper. |
| 3 | 9.6 | more than two miles in | Pull back through the rock into a huge cross-section of the mountain. A glowing route line runs from the entrance to a tiny ledge chamber deep inside. |
| 4 | 12.1 | passages… completely underwater | The cross-section floods: low sections fill with murky water, and the route line turns blue underwater. |
| 5 | 16.7 | After 10 days, divers finally found them | Dive into the chamber: the boys are huddled and thin on a muddy ledge. A diver's head torch pops out of the water and the boys squint into the light. |
| 6 | 20.2 | the flooded tunnels were so dangerous | Divers squeeze through a tiny flooded gap in zero visibility, with silt clouds and guide ropes. |
| 7 | 24.8 | even a skilled diver died | A lone diver's light slowly fades into the dark water. Silence beat; respectful, with no body. |
| 8 | 28.5 | Swimming the boys out themselves seemed impossible | A boy in the chamber looks at the dark water, terrified. |
| 9 | 33.6 | So rescuers chose a last resort | The rescue team kneels around the boys with gear. |
| 10 | 35.9 | They sedated the boys | A medic gives a careful injection in the arm, and the boy drifts off in calm close-up. |
| 11 | 38.8 | fitted them with full-face diving masks | A full-face mask is fitted and strapped; bubbles start. Close on the mask seal. |
| 12 | 40.1 | carried their unconscious bodies… one by one | A diver tows a boy in a stretcher-like harness through flooded tunnels; the camera travels with them. A chain of divers hands them along, back in the cross-section view as the lights move along the route line one by one. |
| 13 | 45.4 | All 12 boys and their coach made it out alive | At the cave mouth, in daylight, stretchers come out to the cheering crowd, ambulances and helicopters. |
| 14 | 48.8 | after 18 days underground | Crane up out of the jungle as clouds part and sunlight breaks. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/CaveRescue_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
