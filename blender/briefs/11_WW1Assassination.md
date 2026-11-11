# Connect11: WW1Assassination

Branch `claude/connect11-ww1-assassination`. Folder `blender/WW1Assassination_v001/`. Target length about 35.5 s, so frame_end = 2130. The script below is 91 words.

**Sensitive:** this is a real historical killing. Show it without blood or wounds, generic faces, and no text on the map.

## Script (ours)

He fired at the car as it turned the corner, aiming at the Archduke and Duchess of Austria-Hungary. But he wasn't the first assassin to try. Earlier, two would-be assassins lost their nerve. Then a third threw a bomb at the couple, but it bounced off and exploded under the car behind them. Later, their driver turned onto the wrong street, right where another assassin was waiting. He fired twice, killing the Archduke and his wife. Their country declared war, dragging in its allies, and that's how World War One began.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | He fired at the car | Sarajevo, 1914: sunny stone street, crowds, flags and bunting. An open-top 1910s touring car with the uniformed Archduke (plumed helmet) and the Duchess (white hat, parasol). The camera rides alongside the car. |
| 2 | 3.0 | aiming at the Archduke and Duchess | Orbit to the couple's faces as they react. A gunman's hand and pistol rise in the foreground, seen from behind, out of focus. |
| 3 | 6.9 | he wasn't the first assassin | Time-rewind effect: the crowd and car reverse, and the camera sweeps back along the street. |
| 4 | 10.1 | two would-be assassins lost their nerve | Two young men in the crowd. One grips something in his coat, then both turn away and melt into the crowd. |
| 5 | 12.4 | a third threw a bomb… bounced off | A third man throws a small dark object; slow motion as it hits the folded car roof and bounces off onto the cobbles. |
| 6 | 15.5 | exploded under the car behind them | It rolls under the following car, then a flash, smoke and debris (no bodies). The crowd scatters and horses rear. |
| 7 | 18.5 | driver turned onto the wrong street | Later: the car takes a corner into a narrow side street, stalls and reverses. The camera cranes overhead. |
| 8 | 22.4 | another assassin was waiting | A young man by a café awning steps forward. Push in on his eyes. |
| 9 | 24.8 | fired twice, killing the Archduke and his wife | From behind the gunman: two muzzle flashes, then the couple slump in the car. No blood or wounds; cut away with the camera rise as the crowd surges. |
| 10 | 28.1 | declared war, dragging in its allies | The camera rises above the city through clouds onto a 3D relief map of 1914 Europe, with no text. The two countries light up with flags, then alliances spread like fire across the map. |
| 11 | 32.0 | that's how World War One began | Pull out over the whole continent ablaze, with marching columns and smoke as tiny animated elements. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/WW1Assassination_v002/`, pushed with Git LFS. Keep the .blend under about 150 MB (1K–2K textures, 2K HDRI).
