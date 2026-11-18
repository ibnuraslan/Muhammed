# Style 07 · Atrium — "The First Man to Escape Camp 14 (North Korea)"

| | |
|---|---|
| Source | Drive `style/…Atrium (1080p).mp4`, 21:20, 1920×1080, 60 fps, **16:9 full frame** |
| Shots | 247 · **median 3.9 s** · p10 1.8 s · p90 7.7 s (the most even rhythm of all refs) |
| Sound | −14.4 LUFS, LRA 2.6 LU |
| Contact sheet | `10_atrium-camp14.jpg` (all 247 shots) |
| Verdict | **Atrium's best character drama.** Close faces with tears and frostbite, group staging indoors, a chase at night: the closest Atrium gets to Yarnhub's emotional intensity |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.03 · median 0.21 · p95 0.68 → low-key, no clipping |
| Saturation | Median 0.17 |
| Palette | `#1d1f25` 14% · `#121216` 13% · `#2d2e31` 12% · `#4c525c` 10% · `#404040` 10% · `#5f6874` 9% · `#050506` 9% · `#7b8490` 8% · `#9ea6b4` 6% · `#2c374f` night navy 5% · accent `#3e1716` blood/uniform red → **frozen blue-grey, snow white, navy night; red only on uniforms and maps** |
| Devices | **Time-of-day plan cards** (red-framed "memory" frame + "12:00" clock); the morning-noon-evening plan structures the film · red satellite map with camp outlines · dark red territory map with camp stars · B&W/grey **3D book in a vitrine** for sources (and at the end) · green/white framed flashback windows |

## Characters and staging

| Item | Obs | Lesson |
|---|---|---|
| Faces | **ECU faces with tears, red eyes, frost**; a woman before execution, the protagonist in a bowl haircut, an old man | Atrium's best facial work: small, held, wet eyes |
| Indoor group scene | Prisoners kneeling in rows, hands on heads, guards walking between them, a beating | Kneeling crowds hide legs; guards are the only walkers |
| Labour | Axe on a tree in the snow (inserts and wides) | Repetitive mocap loop |
| Escape | Running to the fence, shielding behind a friend's body (implied), crawling, night run with a dog | Night + snow + motion blur |
| Disguise | Later in a stolen soldier's uniform, seated, crouching in a hut | Seated/crouching again |
| Interrogation | Two figures on black with a single spotlight | Void staging |

## Script study (paraphrased)

| Metric | Value |
|---|---|
| Words / pace | ≈3,150 · **≈148 wpm** |
| Sentences | 366 · **median 8 words** · p90 15 · **114 sentences ≤5 words** (31%) · 2 questions |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:03 | 6 a.m.: the protagonist is forced to watch a recaptured escapee | Time stamp + brutal image |
| 0:09 | He has seen this almost 100 times; he was born in the camp and can never leave | Number + life sentence |
| 0:27 | "But today, he'll try." Nobody has done it before; failure means death | Goal + stakes in 3 short lines |
| 0:34 | "Through the first-hand experience of…" | Source-based POV promise |
| 1:09 | **Plan in three time slots**: morning (find weaknesses) → midday (steal items) → evening (escape) | Ticking-clock structure announced |

### Structure: one day, three phases

| Time | Phase | Beats (paraphrased) |
|---|---|---|
| 0:00–1:28 | Setup | Execution parade; the plan for the day |
| 1:28–3:44 | Morning: study | Firewood station; the fence; sand strip for footprints; guard gap every 10 minutes |
| 3:44–8:31 | Backstory | Born in the camp; the family curse (relatives' "crimes"); camp society |
| 8:31–12:25 | Midday: gather | Extra winter clothes; a scrap of food begged for a grandson; a partner joins |
| 12:25–15:00 | Complication | A crackdown and a beating; doubts |
| 15:00–18:45 | Evening: escape | Waiting for the gap; the partner's doubt; the fence; using his friend as a shield |
| 18:45–20:13 | Pursuit | Alarm; night run; a hut; a stolen uniform; a truck |
| 20:13–21:20 | Epilogue | China; first food and music; the book; sole survivor |

### Techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Time stamp opener | "It's 6 a.m." | Day-structure clock |
| Pivot line | "But today, he'll try." | Goal in 4 words |
| Plan preview | morning weaknesses, midday items, evening escape | Viewer tracks progress |
| Rule of the world | "Everyone is told that it's electric…" | Raises the stakes of the obstacle |
| Interval number | "a gap in the guard patrol every 10 minutes" | Precise ticking clock |
| Binary choice | "Work to death or escape." | Clear stakes |
| Moral cost | he doesn't look at his friend's face | Emotional climax without showing gore |

## What Seldom can take

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | One-day, three-phase plan structure with clock cards | Script template + `countdown_card()` with a clock | Easy |
| 2 | Wet-eye ECU faces (tears, frost, red rims) | Eye shader: tear-line wetness, redness map, specular; hold 3–5 s | Medium |
| 3 | Kneeling/seated crowd interiors, only the guards walking | Staging rule + mocap kneel/idle loops | Medium |
| 4 | Night chase hidden by snow, motion blur and darkness | Volumetric snow + motion blur + low key | Medium |
| 5 | 3D book-in-vitrine source card | One reusable vitrine scene | Easy |
| 6 | 31% very short sentences | Script rule for tension chapters | Easy |
