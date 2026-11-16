# SodaMouse_v003: director fixes on v002 (Connect B10)

Built straight to the word frames of `SodaMouse_v003_VO.mp3`:
- beat frame = 1 + round(s × 60), as listed in `beats.json`
- no retime and no time-stretching: every clip is authored at normal speed about 30% longer than its span and cut at the next word
- spans longer than about 2.5 s get a second camera angle on the same continuous action

| Shot | Frames | VO | Picture |
|---|---|---|---|
| S01 | 1–77 | A man claimed he found a | Man drinks from the green can (kitchen) |
| S02 | 78–164 | dead mouse inside a can | Macro: tail tip curling out of the can opening |
| S03 | 165–212 | of Mountain Dew | Hero can, man behind (logo on his shirt) |
| S04 | 213–275 | he had been drinking | Mouse on the plate; he recoils in disgust |
| S05 | 276–338 | so he sued | He points at the mouse |
| S06 | 339–398 | PepsiCo. | Close-up of the dead mouse on the plate |
| S07B | 399–560 (B angle at 464) | But the company's defense was bizarre. | Scientist at his lab table, talking |
| S07 | 561–644 | PepsiCo argued that Mountain Dew | Scientist raises a finger |
| S08 | 645–722 | was so acidic that | He pours the can into a beaker, 9 cm above the rim |
| S10 | 723–943 (B angle at 839) | if a mouse had really been inside the can for that long, its body would have | Macro: the mouse sinks in the fizz, shrinks and becomes jelly (all inside the liquid) |
| S11 | 944–1061 | dissolved into a jelly-like substance | The jelly lump settles on a steel tray (no hands) |
| S12 | 1062–1196 | before the drink was ever opened. | Top-down push on the jelly, can beside it |
| S13 | 1197–1361 (B angle at 1275) | That explanation only made people more disturbed, | Man studies the can, worried |
| S14 | 1362–1434 | because now they were wondering | He sets the can down and slides it away |
| S15 | 1435–1558 | what Mountain Dew could do to the human body | He looks down, hand on his stomach |
| S16 | 1559–1702 | if it could supposedly dissolve a mouse. | Final worried close-up |

- **On screen:** no real brands; the can is a generic green print with no text.
- **Logo:** DA KRAS FILMS, once, on the man's shirt chest (front-on in S03–S05 and S13–S15).
- **Checks (on this packed file):** see `review/CHECKS.md` (body_prop_cross 0 on every frame).
- **Preview:** `review/preview.mp4` (every 5th frame, with the VO).

Render settings: `SETTINGS.md`. Credits: `CREDITS.md`.
Build scripts: `scripts/` (01 chars → 02 sets → 03 anim with `timing_vo.json` → 04 lights → pipeline/anim_look.py).

## v002b changes (director review of v002, 7c5651c)
- **S10 (f723–943):**
  - clear glass (roughness 0)
  - lighter green soda
  - both macro cameras sharp (no depth of field), framed above the glass base
  - the B angle mirrors angle A from the other side (the old B angle saw distorted refraction)
  - the mouse reads sharp as it sinks and dissolves
- **S03 (f165–212):** he leans in, turns his head and looks down at the can, with relaxed arms and bent elbows. No mannequin stance.
- **Relaxed arms everywhere:** hands hang 5 cm closer to the body, so no finger clips a table edge.
- **S07:** the hand lifts before coming forward, clear of the lab table's front edge.
- **S08:** the scientist's left arm hangs relaxed instead of resting on the table.
- **Check:** `body_prop_cross` now also includes KitchenTable and LabTableTop as props: 0 crossings on every frame.
