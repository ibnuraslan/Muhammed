# The Killer Was Still in the House · STORYBOARD v2

**Goal:** replace the literal, generic shots ("a man in a room while the narrator says it") with physical-fact devices: one dominant light, evidence objects that come back, and one long take per chapter.

**Rules unchanged:**
- Realistic 3D in Cycles under look v5. No flat 2D, vector or cartoon graphics.
- Every fact is a real object in a lit set: paper, chalk, pencil, string, a clock, a scale model.
- No gore, no faces for the real people (only a faceless file print), no hand close-ups.
- 1920×816, 24 fps.
- The fern references were used for scene ideas only. No Fern shot or design was copied.

**Code and media:**
- New sets live in `scenes/sc_evid.py`, the "evidence world". Its palette is a black void or a dark desk, one hard practical light, and cream paper. Red is used only for the investigators' pencil, string and pins.
- One new move uses the real house: `hatch_measure` in `scenes/sc_hint.py`.
- Shot list: `scenes/shots.py`. Changed shots are tagged `[v2: …]`.
- Before/after sheet: `review/storyboard_v2_before_after.jpg`.
- Motion previews: `review/storyboard_v2_previews/*.mp4` (~480p, 8 samples).

## Changed shots

| Shot | Old idea (v1) | New idea (v2) | Why it's stronger |
|---|---|---|---|
| **1-8B** "an iron tool used to shake ash loose in a stove" | `hint:kitchen_glide`: a detective sitting in the kitchen | `evid:tool_black`: the stove shaker alone on black under one top light, with an "EXHIBIT 4" tag on red string. Slow low arc and push; dust drifts in the beam | The line is about the object, so the shot is the object. It becomes the film's **recurring evidence object** (1-7B floor → 1-8B exhibit → 3-6B desk → 3-7B swing) |
| **1-9A** "signs of a struggle in more than one room… search… Philip's past" | `hint:flash_hall`: two men with a torch in a hallway | `evid:board` (**Ch1 long take, 15–20 s**): the detectives' cork board with the floor plan, sepia prints of our own crime-scene shots, red string from each print to its room, and cards for "FORCED ENTRY: none found" and "STRUGGLE: more than one room". A slow push with rack focus ends on an **empty SUSPECT card**. One print still sways on its pin | It turns three abstract facts (several rooms, no entry, no suspect) into one readable physical image. The empty card *is* "no one they can charge". 1-9B `tilt_ceiling` (kept) then answers it: the camera rises to the ceiling where he is |
| **2-8B** "the captain identifies Theodore Coneys" | `station:photo`: the captain lifts a photo at the table | `evid:file_card`: under the interview lamp, a **faceless** file print (height chart, silhouette) slides across the desk. On the police record card the false name is X'd out and the real name types itself in | It shows the *identification*, not a room. It keeps the real man faceless (playbook rule), and the typing beat lands on the name |
| **2-9B** "about eight inches by fifteen" | `hint:attic_torch`: empty joists | `hint:hatch_measure`: looking straight up the **real** closet at the hatch. A torch searches, then settles; chalk lines are drawn along both edges and **"8 in" / "15 in"** are chalked on the plaster | It makes the scale physical and unforgettable: a grown man went through *that*. The measurement sits on the real set, not as an overlay |
| **2-13B** "before Philip was killed" (five weeks) | `hint:joist_drift`: an empty attic drift | `evid:calendar`: a 1941 wall calendar in raking window light. October (17 circled in red) **flips back** to September; red pencil ticks run day by day from the 12th; "five weeks" is pencilled on the page | It turns time into an object. The chapter ends on the reveal that he was there *before* the murder, and the page physically going *back* is that reveal |
| **3-6B** "kitchen, front door, front bedroom" | `hint:walk_track`: a wall and two hats | `evid:plan_route`: top-down on the ground-floor plan on the detectives' desk. A red pencil **draws his route** room by room and ends in an X in the front bedroom; the iron tool lies at the frame edge | A route on a map is the clearest way to say a route. It is silent and restrained, which suits the attack: implied, never shown |
| **3-7B** "the heavy iron stove tool" | `hint:door_closing`: an empty room, a door | `evid:tool_swing`: **callback** to 1-8B, the same exhibit, now under a slowly swinging, flickering bulb; its shadow sweeps back and forth | It brings back the recurring object at the moment it matters. The swinging light gives violence through motion and shadow, with no act shown |
| **3-9B → 11B** "Coneys stays… preserves… through the winter… nine months" (five shots) | `hx:seasons_push`, `hint:jar_track`, `hint:candle_steps`, `hx:attic_vent`, `hx:summer_still`: five separate exteriors and cellar inserts | `evid:cutaway` (**Ch3 HERO LONG TAKE, ~36 s**): one continuous take on a **cut-away scale model of the house** on a plinth, explained in the rows below | It is the film's central idea (he lived *above* them for nine months) in one image you can read at a glance. It is the chapter's emotional peak as a single unbroken take, per the 30–90 s rule |
| **3-14A** "less than two hours… guilty" | `court42:jury_in`: a jury box | `evid:clock`: the courtroom clock on dark panelling under one top light. The minute hand sweeps 1 h 46 m and stops | "Less than two hours" is the fact, and a clock is the fact. It stays tight and quiet before 14B `gavel` (kept) |

**The 3-9B → 11B cutaway take, in order:**
- **Opening:** the model house on a plinth. The rooms below are lit, then go dark when Helen leaves. **Only the attic glow stays on.**
- **Seasons:** outside, autumn leaves fall, snow comes (snow falls and settles on the roof), then summer green. The key light changes with each season.
- **Date card:** a museum-style card on the plinth counts "OCTOBER 1941 … JULY 1942" and "day 1 … day 286 · more than nine months".
- **Camera:** a slow orbit, then a push into the attic.

**Kept shots (reviewed and judged strong):**
- intro, all shots
- 1-6B, 1-7A and 1-7B (the discovery)
- 1-9B (tilt to the ceiling)
- 2-5B (legs at the hatch: Ch2 hero), 2-6A/B
- 2-12A (eyes at the hatch)
- 3-5A (icebox)
- 3-8A/B (hatch shut / search below him)
- 3-12A/B (press / newsboy)
- 3-14B, 3-15A–16B (the ring ending)

**Illustrative details, to flag in the edit as "reconstruction":**
- the exhibit number
- the record card layout
- the clock times (only "less than two hours" is sourced)

## Long take per chapter

| Chapter | Long take | Length (VO-driven) | Inserts around it |
|---|---|---|---|
| Ch1 | `evid:board` (9A): push from the whole board to the empty SUSPECT card, with rack focus | 15–20 s | 8A latch, 8B tool on black (2–4 s each), then 9B tilt |
| Ch2 | `hint:legs_hatch` (5B), already the chapter hero: hold it, no cut until the grab | 8–12 s | 4A/4B/5A short (2–3 s), 9B measure, 13B calendar |
| Ch3 | `evid:cutaway` (9B–11B): seasons and day counter | ~36 s | 6B route, 7B tool swing, 14A clock (3–5 s each) |

Rhythm: inserts of 2–4 s around each long take. Final cut points come from the VO word times when they arrive.

## Animation improvements

**Characters:**
- New `house.idle()`, applied automatically by `stand_at()` in every `sc_hint` / `sc_hx` move.
  - Slow weight shift from hip to hip (spine05/spine03 counter-roll).
  - Breathing in the chest, and a small drifting head turn with a little pitch.
  - Each person has a different phase, so groups never move in sync.
  - Arms and hands are untouched, so the 118-crop hand QA still holds.
- See the `hint_tilt_ceiling` preview: the two detectives now stand like people, not statues.

**Motivated camera moves:**

| Shot | Move | Motivation |
|---|---|---|
| board | push in with rack focus (plan → SUSPECT card) | finds the missing piece |
| tool_black | low arc and push | inspects the exhibit |
| hatch_measure | rise toward the opening | follows the torch |
| plan_route | slow descend and rotate | follows the pencil |
| calendar | push | lands on the ticks |
| clock | push in | tightens as time runs out |
| cutaway | slow orbit, then push into the attic glow | the reveal of where he lived |

**Animated objects:**

| Object | Motion |
|---|---|
| Pinned print | sways on its pin and settles |
| Calendar page | bends, lifts and flips; ticks appear day by day; "five weeks" pencilled |
| Red pencil | draws the route; an X lands at the end |
| File print | slides across the desk; the name types in |
| Bulb | swings like a pendulum and flickers |
| Torch beam | searches, then settles |
| Chalk lines | drawn on |
| Air | dust motes in the beams; snow falls |
| Cutaway model | trees change, ground and roof snow come and go, room lights go out, the attic hot-plate glow flickers |

## Deliverables

- `review/storyboard_v2_before_after.jpg`: before/after per changed shot.
- `review/storyboard_v2_previews/`, low-res motion previews (~480p, 8 samples, 8–12 fps rendered, motion-interpolated to 24 fps):

| Preview | Content |
|---|---|
| `evid_tool_black.mp4` | 1-8B, the exhibit (recurring object) |
| `evid_board.mp4` | 1-9A, Ch1 long take (shortened to 7 s for the preview) |
| `hint_hatch_measure.mp4` | 2-9B, chalked 8 in / 15 in on the real hatch |
| `evid_calendar.mp4` | 2-13B, five weeks back |
| `evid_plan_route.mp4` | 3-6B, the route |
| `evid_cutaway.mp4` | 3-9B–11B, Ch3 hero long take (36 s) |
| `hint_tilt_ceiling.mp4` | 1-9B, kept shot with the new idle motion on the detectives |

Stills: `tools/stills.sh <dir> evid:<move>[:t]`. Previews: `tools/preview_mp4.sh <set> <move> <seconds> <fps> <outdir>`.
