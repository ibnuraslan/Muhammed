# Style 06 · Atrium — "Why Hitler Was Impossible To Kill" (the armoured Mercedes 770K)

| | |
|---|---|
| Source | Drive `style/…Atrium (1080p).mp4`, 17:09, 1920×1080, 30 fps, **16:9 full frame** |
| Shots | 177 · **median 3.3 s** · p10 0.8 s · p90 14.3 s (long X-ray/cutaway holds, fast action cuts) |
| Sound | −14.0 LUFS, LRA 2.6 LU |
| Contact sheet | `08_atrium-hitler-unkillable.jpg` (all 177 shots) |
| Verdict | **Best "object as protagonist" film**: one hero vehicle tested against 4 attack scenarios, explained with X-ray cutaways. The most reusable structure for Seldom's object-driven stories (phone, typewriter, container, drain) |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.02 · median 0.23 · p95 0.79 |
| Saturation | Median **0.11** (near-monochrome; colour reserved for fire and the UI red) |
| Palette | `#161313` 15% · `#272423` 14% · `#070606` 13% · `#393836` 12% · `#4c4c4d` 11% · `#676361` 9% · `#827d7d` 8% · `#9f9c9f` 6% · `#c1c1c7` 6% · accents `#7f422b` rust, `#d59a4d` fire |
| Hero object | Gloss-black Mercedes, photoreal paint and chrome, wet roads with reflections |
| Devices | **Red hexagon icons on a dark textured map** (target, sniper, bomb, MG van) with dashed routes · distance callout "319 FT" · **dimension lines in red on the car** ("19.6 feet") · weight tag "4800 kg" · **X-ray/ghost cutaways** (tyre cells in green, chassis in red wireframe, armoured cabin glass layers) held 13–42 s · interior studio shots of the car on black · scope POV · archival B&W factory film at the end |

## Characters and staging

| Item | Obs | Lesson |
|---|---|---|
| Attackers | Each gets 2–4 shots: a woman with a stroller, a sniper in bushes, a man under a bridge, gunners in a van | Characters are short "functions" around the hero object |
| Hitler | Barely shown (silhouette in the back seat) | The villain stays faceless; the object carries the film |
| Driver | Hands on the wheel, feet on the pedals (inserts), eyes in ECU | Seated, inserts only |
| Action | Caltrops thrown, Molotov, explosion, machine-gun fire: 0.5–2 s cuts, fire VFX | Fast cuts hide animation shortcuts |

## Script study (paraphrased)

| Metric | Value |
|---|---|
| Words / pace | ≈2,370 · **≈139 wpm** |
| Sentences | 203 · median **11 words** · p90 21 · 40 ≤5 words · 1 question |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:00 | The armoured car speeds toward the Chancellery with Hitler inside | Object + VIP + destination |
| 0:14 | What they don't know: a trap is straight ahead | Dramatic irony |
| 0:19–0:44 | Four hidden attackers listed one by one (stroller, sniper, Molotov, road bomb, MG van) | **The whole film's structure previewed as a list** |
| 0:46 | The car was never really tested, so they rebuilt it in 3D and ran 4 scenarios | Experiment premise + production promise |
| 1:00 | The first attack is 400 feet ahead | Countdown by distance |

### Structure: scenario test ×4

| Time | Block | Beats (paraphrased) |
|---|---|---|
| 1:00–1:51 | Specs | Convoy order; the car's size, engine, weight |
| 1:51–3:47 | Attack 1: caltrops | Tyres puncture; X-ray of the cellular tyres; the car keeps going |
| 3:47–6:17 | Attack 2: Molotov | Interior luxury; fire on the hood; fuel-tank protection |
| 6:17–7:38 | Sponsor | |
| 7:38–11:40 | Attack 3: road bomb | Gearbox and ground clearance; decoy cars in the convoy; the armoured floor |
| 11:40–16:10 | Attack 4: heavy machine gun | The van ambush; armour thickness; laminated glass; the car escapes |
| 16:10–17:09 | Epilogue | What happened to the car; its legacy; comments prompt |

### Techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Structure preview list | "Along the route, a man waits beneath a bridge with a Molotov." | Viewer knows the 4 acts up front |
| Hypothetical test | "put it against four scenarios to find out what Hitler could have survived" | "What if" engine |
| Spec stacking | "19.6 feet long, 6.9 feet wide, and 6.2 feet tall" | Authority; the dimension lines appear on screen |
| Doubt line | "Or at least, that is what the Nazis think." | Turns a spec dump into suspense |
| Scoreboard | "Three traps have failed." | Progress marker before the finale |

## What Seldom can take

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | **Object-as-protagonist + scenario tests** (our phone, typewriter, container, drain) | Script template; one hero asset per film | Easy |
| 2 | X-ray/ghost cutaway of the hero object (held 15–40 s) | Duplicate the object, transparent shader + coloured wireframe of internal parts; animate a section plane | Medium |
| 3 | Red dimension lines and weight tags on the object in 3D | Curve + text objects parented to the object | Easy |
| 4 | Red hexagon threat icons on a dark textured map | Map template + icon set | Easy |
| 5 | Near-monochrome grade with colour only for fire and UI | `look.py` "noir object" preset | Easy |
| 6 | Studio shots of the object on black between story beats | Void preset | Easy |
