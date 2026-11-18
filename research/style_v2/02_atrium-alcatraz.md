# Style 02 · Atrium — "The Genius Escape of Alcatraz Prison"

| | |
|---|---|
| Source | Drive `style/…Atrium (1080p).mp4`, 26:25, 1920×1080, 60 fps, **16:9 full frame** (no letterbox) |
| Shots | 251 (detected at a lower threshold because Atrium uses slow moves and dark scenes) · **median 4.3 s** · p10 1.2 s · p90 13.0 s |
| Contact sheet | `02_atrium-alcatraz.jpg` (all 251 shots) |
| Verdict | **A script and pacing reference, not a visual bar.** The render and character animation are clearly below Yarnhub and Fern: flat lighting, generic game faces, full-body walks with visible foot sliding |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.00 · median 0.28 · p95 0.92 (more highlight clipping than Yarnhub) |
| Saturation | Median 0.22 (more muted than Yarnhub at 0.32) |
| Palette | `#060505` 17% · `#1d1919` 16% · `#382e2a` 12% · `#69523c` 9% · `#444548` 8% · `#f0f0ee` 7% · `#d4d1c6` 6% · `#887756` 6% · `#636666` 6% · `#ab9d77` 6% → institutional green-grey walls, prison-blue uniforms, warm bulbs |
| Render | Real-time game engine; cleaner and flatter than Yarnhub; little GI depth, soft contact shadows |
| Night | The escape is graded blue-monochrome (day-for-night) |
| Devices | **Red neon frame "memory window"** for flashbacks/plans · **game-style progress bar** ("DIGGING COMPLETE 29% / 53%") · white line-art 3D route diagram · satellite map · vintage magazine pages (life-vest article) as inserts |

## Characters and staging

| Item | Obs | Lesson for Seldom |
|---|---|---|
| Faces | Generic real-time human faces, small expressions, shaved/shirtless shower scene | Even mid-quality faces pass if shots are short and eyelines clear |
| Walks | **Many full-body walks** (yard, cell block, workshop), visibly game-like | This is exactly our "weird walk" problem; Yarnhub hides walks, Atrium doesn't, and it shows |
| Hands | Many hand-object actions: spoon digging, vent grille, drill, paintbrush, concertina | Each action is one insert, close and short |
| Coverage | Two-shots over the lunch table, OTS through bars, guard POV down the cell row | Classic drama coverage at modest quality |
| Crowds | Rows of seated prisoners (instanced), guards in the background | Seated crowds hide locomotion |

## Sound (measured)

| Item | Value |
|---|---|
| Integrated | **−15.9 LUFS**, LRA 3.8 LU (much quieter master than Yarnhub at −10.4) |
| Silence | 1 gap below −45 dB longer than 0.8 s in 26 min |
| Obs from the script | Diegetic sound **is the plot**: concertina music masks the drill, a dropped plate is a distraction, the guard "Boots" is named after his footsteps, a bang on the roof, prisoners stomping |
| Lesson | Write sound into the story: an object that makes noise, a sound that hides another, footsteps that announce danger |

## Script study (paraphrased)

| Metric | Value |
|---|---|
| Words / pace | ≈3,770 words · **≈143 wpm** |
| Sentences | 447 · **median 7 words** (half of Yarnhub's 14) · p90 15 · 136 sentences ≤5 words · only 4 ≥25 words |
| Questions | 14 (mostly dialogue and one end-of-act "did they make it?") |
| Dialogue | Narrator voices the characters' lines with tags ("…says Frank") |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:00 | A prisoner runs for the shore with guards chasing, shot down | Cold open on a failed attempt |
| 0:15 | Score: 34 attempts, 34 failures | Stat as a drumbeat |
| 0:21 | Promise: the real breakout will look nothing like this; no gunshots, a genius plan already underway | Contrast + promise |
| 0:38 | Meet Frank at lunch, his idea, his partner, the 3-phase plan | Protagonist + plan in 50 s |

### Structure (heist in phases)

| Time | Phase | Beats (paraphrased) |
|---|---|---|
| 0:38–4:12 | Phase 1a: dig with spoons | Plan at lunch; nightly digging; a cell inspection with a wet patch; lockdown risk |
| 4:12–7:38 | Phase 1b: build a drill | Steal a motor and cable; the drill is too loud; music hides it |
| 7:38–9:13 | Sponsor | Software read, introduced via "communication between team members" |
| 9:13–12:55 | Close calls | Strict guard checks cells; painted fake vents; first breakthrough into the utility corridor; secret room; race back |
| 12:55–16:31 | Phase 2: deception and plan | Dummy heads; the route explained; a library magazine on rubber rafts; a slip of the tongue |
| 16:31–19:20 | Phase 2b: materials | Steal raincoats in the yard; a near fight; build vests and raft with the steam pipe |
| 19:20–24:46 | Phase 3: the night | One partner can't get out; the choice to leave him; a noise on the roof; searchlights; down the pipe; the raft floats; they push off |
| 24:46–26:25 | Epilogue | The partner who stayed behind; evidence found; case still open; flowers for their mother every year |

### Techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Stat drumbeat | "34 tries. 34 failures." | Rhythm + stakes |
| Promise of contrast | "No gunshots, no chaos." | Sets the genre (heist, not action) |
| Phase labelling | "…this is only the first phase." | The viewer tracks progress |
| Progress number | "he's barely 30% done" | Concrete ticking clock (also shown as a UI bar) |
| One-line beats | "Then it happens." | Fast suspense pacing |
| Stakes conditional | "If one person is missing, the prison will go into complete lockdown." | Every scene states what failure costs |
| Close-call release | "It's the closest call yet." | Tension/release cycle every 2–3 min |
| Foreshadowing | "Little does he know, a single mistake will cost them greatly." | Carries suspense across a cut |
| Moral dilemma | Do they leave their friend behind or risk staying? | Emotional climax |
| Ambiguous epilogue | Flowers arriving every Mother's Day | Mystery ending, comments bait |

## What Seldom can take from Atrium

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | Plan-in-phases structure with progress % | Script template + `title_card.py` progress-bar overlay | Easy |
| 2 | Tension/release every 2–3 min (inspection → close call → relief) | Beat sheet rule | Easy |
| 3 | Diegetic sound as a plot device | Script + sound design (`sound_design.py`) | Easy |
| 4 | Red-frame "memory/plan window" | Comp overlay template | Easy |
| 5 | 3D line-art route diagram | Freestyle line render of the set + dashed red route | Medium |
| 6 | Don't copy: full-body walks on visible floors | Use Yarnhub staging instead (see GAP_ANALYSIS) | n/a |
