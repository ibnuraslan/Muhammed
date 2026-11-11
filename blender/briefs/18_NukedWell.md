# Connect18: NukedWell

Branch `claude/connect18-nuked-well`. Folder `blender/NukedWell_v001/`. Target length about 36.0 s, so frame_end = 2160. The script below is 95 words.

**Sensitive:** the device is a plain cylinder; show no weapon internals. The explosion is underground, so show it as a glow, the rock compressing and a surface jolt with a dust ring.

## Script (ours)

The massive nuclear device was lowered down the shaft, and then concrete was poured on top. You see, three years earlier, a gas well had erupted into flames, and a fireball over 400 feet tall had been burning nonstop. Engineers tried to put it out with water, but it did nothing. And capping it with a lid only forced the gas to escape somewhere else. So finally, they sent down a nuclear bomb. When it detonated, the enormous blast squeezed the earth around the well, sealing the pipe shut and finally putting out the fire.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | lowered down the shaft | 1960s Central Asian desert drill site. A long dark-green cylindrical device on a cable descends the bore. The camera goes underground in cross-section (layered rock strata). |
| 2 | 3.2 | concrete was poured on top | A concrete mixer pours down the shaft and the plug fills above the device. |
| 3 | 5.7 | three years earlier | Rewind: everything reverses and the sky shifts. The camera pulls up to the surface. |
| 4 | 9.0 | erupted into flames | Cross-section: high-pressure gas surges up the pipe and bursts out at the surface into a roaring flame column. |
| 5 | 10.3 | a fireball over 400 feet tall… nonstop | Wide desert: a huge fire column with heat shimmer and smoke; a derrick nearby for scale; the day and night cycle while it burns. |
| 6 | 14.9 | tried to put it out with water | Water cannons and fire trucks spray into the flames; steam bursts but the fire roars on. |
| 7 | 18.5 | capping it with a lid… somewhere else | A steel cap is lowered on, and then the ground cracks: new gas jets and flames burst out of fissures around the site. |
| 8 | 23.0 | they sent down a nuclear bomb | Soldiers and engineers in 1960s gear guide the device into the bore (the same shot as the opening, now in context). |
| 9 | 26.4 | When it detonated | Underground cross-section: a blinding white sphere expands deep in the rock. On the surface, the ground jolts and a dust ring shoots out (no mushroom cloud, since it's underground). |
| 10 | 28.0 | squeezed the earth around the well | The pressure wave compresses the rock strata inward and pinches the gas pipe closed. |
| 11 | 31.6 | sealing the pipe shut… putting out the fire | Surface: the flame column chokes, sputters and dies to a smoke wisp. The crew stands at a distance, and the camera rises over the calm desert. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/NukedWell_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
