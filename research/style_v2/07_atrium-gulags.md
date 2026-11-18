# Style 05 · Atrium — "The Evil Design of Soviet Gulags" (Kolyma)

| | |
|---|---|
| Source | Drive `style/…Atrium (1080p).mp4`, 21:23, 1920×1080, 30 fps, **16:9 full frame** |
| Shots | 305 · **median 3.2 s** · p10 1.0 s · p90 8.2 s |
| Sound | **−28.0 LUFS**, LRA 3.4 LU (peak −15 dB; this file looks like a quiet re-encode, so don't use it as a loudness reference) |
| Contact sheet | `07_atrium-gulags.jpg` (all 305 shots) |
| Verdict | Atrium's best **survival-drama** staging: one prisoner's POV through a whole system. Shows their behind-the-scenes too (viewport, wireframe and ID-pass shots at 0:27–0:29) |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.01 · median 0.28 · p95 0.85 |
| Saturation | Median 0.21 |
| Palette | `#1a1818` 15% · `#676a72` 11% · `#2d3037` 11% · `#060505` 11% · `#464a53` 10% · `#878d99` 10% · `#acb6c6` snow-blue 10% · `#3f2c1e` / `#644d39` wood 14% · `#b75b41` rust 2% → **cold blue-grey snow outside, amber lantern light inside** |
| Two-world grade | Exteriors: blue overcast snow · interiors (barracks, mine): amber lanterns, smoke, dust |
| Devices | Red map with tower icons and a dashed route · **white 3D maquette of the camp** with the barracks highlighted in red (40 s) · energy/stamina bar ("80%" with a lightning icon) as a game-like survival meter · B&W archival intercut · grey clay baby head (a memory) · prisoner number stencilled on clothing |

## Characters and staging

| Item | Obs | Lesson |
|---|---|---|
| Protagonist | Prisoner in a fur hat; mostly MCU in dark interiors, seated on bunks, kneeling in the mine | Seated/kneeling labour hides walks |
| Labour actions | Pickaxe swings, pushing carts, eating bread: shown in MCU and inserts with motion blur | Repetitive work = easy mocap loops |
| Group scenes | Card game around a table, a fight over a sweater, a queue | Coverage of groups from a seated eye line |
| Violence | Implied: a pistol raised, a shot, a body in the snow from a distance | Same rule as Yarnhub |
| Faces | Dirty, frost-covered; small expressions, clear eyelines | |

## Script study (paraphrased)

| Metric | Value |
|---|---|
| Words / pace | ≈2,980 · **≈140 wpm** |
| Sentences | 331 · **median 8 words** · p90 15 · 91 ≤5 words · **0 questions** |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:07 | A named prisoner chained in the hold of a ship heading to the Kolyma camps; five years' hard labour | Name + place + sentence in 3 lines |
| 0:17 | Sensory: cuffs cutting in, the smell of the hold | Senses before facts |
| 0:24 | "It only gets worse from here." | Promise of escalation |
| 0:27 | "We spent over 200 hours researching and modeling the entire Gulag" | Production promise (same as Obersalzberg) |
| 0:32 | Arrival; processing: shaved head, a number replaces his name | Identity loss as the inciting moment |

### Structure: a day/system tour through one body

| Time | Block | Beats (paraphrased) |
|---|---|---|
| 0:00–2:02 | Arrival | Ship, bathhouse, number, convoy, camp layout on the maquette |
| 2:02–4:01 | Barracks | Cold, bunks, criminals vs politicals, food = survival |
| 4:01–7:30 | Mine | Quotas (150 carts), injuries, self-harm to escape work, purges |
| 7:30–8:26 | Sponsor | Website builder |
| 8:26–12:04 | Camp society | Thieves rule; a murder for a sweater; a protector; bread |
| 12:04–14:06 | The wider system | Road of Bones, camp sizes, gold quotas |
| 14:06–19:34 | Breaking point | Tool breaks, the cold, a march where falling behind means death, a beating, a pistol to his head, survival |
| 19:34–21:23 | Epilogue | Real outcome, purge numbers, return to his family |

### Techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Sensory opening | "Cuffs dig into his flesh." | Instant immersion |
| Escalation promise | "It only gets worse from here." | Retention line |
| Identity loss | "A number replaces his name." | Emotional core in 5 words |
| Quota as a ticking clock | "10 more to go." | Game-like progress |
| Conditional threat | "If it breaks again, so will he." | Stakes in parallel structure |
| Cut on the trigger | the trigger is pulled, then he is shown alive in the snow | Fake-out cliffhanger |

## What Seldom can take

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | Cold-outside / amber-inside two-world grade | `look.py` presets per location | Easy |
| 2 | White 3D maquette of a site with a highlighted building | Simplified set + white material + red highlight | Medium |
| 3 | Survival/quota meter overlay | `title_card.py` bar overlay | Easy |
| 4 | Repetitive labour actions from mocap loops (pick, push, carry) | Mocap library | Medium |
| 5 | Show our own behind-the-scenes (viewport, wireframe) as a credibility beat | Screen capture of Blender | Easy |
| 6 | Sensory first lines, 0 questions, short declaratives | Script template | Easy |
