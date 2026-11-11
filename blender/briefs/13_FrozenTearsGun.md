# Connect13: FrozenTearsGun

Branch `claude/connect13-frozen-tears-gun`. Folder `blender/FrozenTearsGun_v001/`. Target length about 35.0 s, so frame_end = 2100. The script below is 99 words.

## Script (ours)

As she cries, her tears roll down into a tube and drop into the gun. When she turns the valve, a CO2 canister releases gas, freezing the tears into tiny balls of ice. And when the trigger is pulled, a spring fires the frozen tears just like a real gun. You see, a while back, she had a stressful meeting with her mentor and burst into tears. She was so upset, she wished she could shoot him with her tears. So she designed this tear gun. And when it was finished, her mentor agreed to let her shoot him.

## Beats (target start times in seconds, ±0.3)

| # | t (s) | Line starts | What happens and how the camera moves |
|---|---|---|---|
| 1 | 0.0 | As she cries | A young woman in her 20s, close on her face. A curved brass collector sits under one eye like a monocle-funnel. Tears well up and roll down. |
| 2 | 2.3 | tears roll down into a tube | Macro: a tear slides into the funnel, then down a clear tube. The camera rides along the tube. |
| 3 | 4.5 | drop into the gun | Into a glass-and-brass handheld device (cutaway, clean studio cyan gradient). Droplets fall into a chamber. |
| 4 | 5.8 | When she turns the valve | Her fingers turn a small brass valve wheel. |
| 5 | 7.3 | a CO2 canister releases gas | A plain unbranded canister vents white gas into the chamber. |
| 6 | 10.1 | freezing the tears into tiny balls of ice | Macro: droplets frost over and become tiny ice pellets, with frost crystals spreading. |
| 7 | 13.4 | when the trigger is pulled | Her finger squeezes the trigger; cutaway of the spring compressing and releasing. |
| 8 | 15.0 | fires the frozen tears | Slow motion: ice pellets shoot out of the barrel and sparkle through the air. |
| 9 | 18.7 | a while back… stressful meeting with her mentor | The pellets fly into a memory (the world blurs and becomes an office). A bald older mentor across a desk lectures her. |
| 10 | 22.4 | burst into tears | She breaks down, hands to her face, shoulders shaking. |
| 11 | 25.5 | wished she could shoot him with her tears | A thought-bubble in 3D: tiny tear projectiles pelt the startled mentor. |
| 12 | 28.3 | designed this tear gun | Workshop desk: she sketches, machines brass parts and assembles. A time-lapse with sparks and parts. |
| 13 | 31.2 | her mentor agreed to let her shoot him | She lifts the finished gun. The mentor stands, arms out, bracing with a wince and a smile; she fires and a puff of ice sparkles hits his shirt. Settle. |

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
- **Deliverable tonight:** checkpoint D package in `blender/FrozenTearsGun_v002/`, committed as a normal git file with no LFS. Keep the .blend under 95 MB (1K textures, 2K only for hero close-ups, 1K HDRI).
