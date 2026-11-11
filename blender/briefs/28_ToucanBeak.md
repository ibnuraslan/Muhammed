# Connect28: ToucanBeak

Branch `claude/connect28-toucan-beak`. Folder `blender/ToucanBeak_v001/`. Target length about 37.5 s, so frame_end = 2250. The script below is 111 words.

Use a real CC-BY keel-billed toucan model with real feathers, eye and beak colours. Show the attack only as a stick striking and pieces flying, with no blood. Computer screens show 3D shapes only, no text.

## Script (ours)

A stick swung down and smashed right into the toucan's upper beak. Now, every time it tried to eat, the fruit just slipped away. So rescuers scanned the broken stump, then compared it to another toucan's beak, using its shape to rebuild the missing half on a computer. But the new beak couldn't be too heavy, or it would pull the bird's head forward. So they made it full-size, but almost hollow. Once it was ready, rescuers lined it up with the broken stump, glued the base into place, and fixed the rest with a pin. And for the first time since the attack, the toucan could pick up fruit again.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | A stick swung down and smashed | A Costa Rican jungle edge with a toucan on a branch. A shadowy stick swings into frame in slow motion and the camera rides with it. |
| 2 | 1.7 | right into the toucan's upper beak | Impact: beak fragments fly in slow motion and the bird flinches. |
| 3 | 4.7 | every time it tried to eat | Feeding beat: the toucan tries to grab a fig and it slips off the stub; frustrated head shakes. |
| 4 | 8.9 | rescuers scanned the broken stump | Wildlife rescue clinic: a vet holds the bird gently while a handheld 3D scanner sweeps a laser line over the stump. |
| 5 | 11.3 | compared it to another toucan's beak | Scan data floats in 3D: the stump mesh next to a whole beak mesh, aligning. |
| 6 | 14.1 | rebuild the missing half on a computer | On a monitor: the 3D model of the missing half extruding into place. The camera pushes through the screen into the model. |
| 7 | 17.7 | couldn't be too heavy… pull the head forward | Physics beat: a heavy beak tips the bird's head forward, shown as a ghost demonstration. |
| 8 | 22.5 | full-size, but almost hollow | Cutaway: the new 3D-printed beak's internal honeycomb lattice, and a printer nozzle laying layers. |
| 9 | 25.2 | lined it up with the broken stump | Clinic macro: gloved hands align the colourful prosthetic to the stump. |
| 10 | 28.4 | glued the base… fixed the rest with a pin | Adhesive applied, a small pin inserted with tweezers, and the vet's careful hands. |
| 11 | 33.0 | the toucan could pick up fruit again | Back in an enclosure with plants: the toucan grabs a fig, tosses it and swallows. Slow orbit. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/ToucanBeak_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
