# Yarnhub Style Bible — reproducible spec for Seldom

Reference: "When Tigers and Joseph Stalin Clashed" (Yarnhub), 16:39, 1920×1080, 25 fps. Contact sheet of all 204 shots: `01_yarnhub-tigers-is2.jpg`.
Measurements come from the file itself (frame sampling, ffmpeg loudness). Observations are marked **obs**; numbers are **measured**.
Style inspiration only: we never reuse their assets, shots or audio.

## 0. One-line summary

**Game-cinematic photoreal:** a real-time-engine look (UE5-style GI, scanned foliage and mud), semi-real game characters, and a single continuous battle told shot by shot from inside and outside the vehicles. Characters are mostly framed from the chest up inside hatches and turrets, so legs and walks are rarely on screen.

## 1. Format

| Item | Yarnhub | Seldom target |
|---|---|---|
| Aspect | **16:9 full frame** (measured: no letterbox, crop 1920:1080) | User wants **21:9** (Fern uses 2.35:1). Render 16:9 and letterbox to 2.39:1 in the comp (1920×804 active), or render 2560×1080 |
| Frame rate | 25 fps | 24 or 25 fps |
| Runtime | 16:39 | 15–25 min |

## 2. Render look

| Item | Spec |
|---|---|
| Realism | Photoreal environment (scanned ground, mud puddles, grass and wildflowers, wooden houses), photoreal vehicles (worn paint, mud, rust). Characters semi-real (game-cinematic, slightly smooth skin). **No outlines, no toon shading** |
| Brightness (measured) | Luma p5 = 0.01 (blacks crushed), median 0.25, p95 0.80 (highlights kept below clip), mean 0.30 → darkish, filmic |
| Saturation (measured) | Median 0.32, p90 0.62 → moderate; earthy, not vivid |
| Dominant palette (measured, k-means over all shots) | `#030506` near-black 12% · `#101211` 11% · `#22221b` 10% · `#333226` 12% · `#454234` olive-grey 12% · `#5d543b` khaki 9% · `#7a6b4b` mud-tan 7% · `#8d846c` dust 7% · `#586065` steel blue-grey 5% · `#a4a18e` sky haze 5% · `#bbc0b9` 5% · `#dee0d8` overcast white 5% |
| Accent colours (obs) | Fire orange `#f39a2e`-ish, explosion core near-white yellow, tracer green, green T-34 paint, sand Tiger paint |
| Grade | Warm-neutral midtones, slightly green-olive shadows, soft overcast sky. No teal-orange. Fits our "real colours" rule |
| Contrast | High: crushed blacks in interiors (tank cabins are 70% black), soft roll-off on sky |
| DOF | Shallow on close-ups and inserts (hands, shells, eyes), deep on wides |
| Bloom / glare | Mild bloom on fire, explosions and interior practicals (white cabin lights) |
| Motion blur | Strong on fast moves (whip pans, shell fly-bys, running) |
| Lens effects | Vignette on interiors, slight chromatic softness at the edges, optics masks (gunsight reticle, binoculars) |
| Grain | Light; image is clean-digital, a little soft |

## 3. Characters

| Item | Spec (obs) | Why it works |
|---|---|---|
| Proportions | Realistic adult proportions, game-cinematic heads (MetaHuman-like) | |
| Faces | Neutral or tense. Expressions are small: frown, squint, jaw set, wide eyes at the climax. Dirt and sweat decals added as the battle goes on | Small expressions don't fall into the uncanny valley |
| Framing | **~80% of character shots are chest-up**: commanders in hatches, crews in cabins, gunners at sights | **Legs, walks and contact are almost never shown** |
| Hands | Shown only in inserts doing one clear action: crank, trigger, shell loading, hatch handle, binoculars. Gloved or dark-lit | One clear action per insert = no ambiguity, no intersections visible |
| Walks/runs | Rare: 3–4 shots (crew bailing out, two men fleeing, crawling). Hidden with motion blur, grass foreground, smoke or a long lens | Avoids weak locomotion |
| Dialogue | No lip-sync close-ups. Short shouted lines as **on-screen subtitles** ("FIRE!", "RELOAD, FASTER!", "GOOD SHOT.") | Lip-sync is skipped entirely |
| Name cards | Real person: name in bold caps + rank/unit in small caps, with a B&W archival portrait beside the 3D face | Ties the 3D actor to the real person |
| Crowds | None. Max 3–4 people per shot | |
| Death | Implied: fade to black ("world goes black"), smoke from the hatch, man falls into grass out of focus, pistol raised then cut | |

## 4. Camera language

| Item | Spec |
|---|---|
| Shot length (measured) | 204 shots · **median 3.9 s** · mean 4.9 s · p10 1.4 s · p90 9.6 s · max 26.6 s |
| Distribution (measured) | <1.5 s: 25 · 1.5–3 s: 46 · 3–5 s: 61 · 5–8 s: 39 · 8–12 s: 20 · >12 s: 13 |
| Shot types (obs, ≈ share) | Exterior vehicle wides/mediums ~40% · interior faces MCU/ECU ~25% · POV through optics (gunsight, periscope, binoculars, vision slit) ~12% · inserts (hands, shells, tracks, wheels) ~12% · "hero shell" slow-mo with spec text ~4% · top-down explosion ~2% |
| Lens feel | Wides ~24–35 mm at ground/hull height. Faces 50–85 mm. Inserts macro. Optics POV with a circular mask and real reticle markings |
| Height | **Low**: camera usually at track/hull height or in the grass, looking up at the vehicles |
| Moves | Slow dollies and tracking alongside vehicles, slight handheld shake inside cabins, whip pans on firing, push-in to the eyes before a decision |
| Signature sequences | (1) Commander sees → POV through the optic → hand on the trigger → **shell in slow-motion fly-by** → impact → reaction face. (2) Enemy turret turns toward camera → muzzle ECU → face ECU → cut |
| Coverage | Classic: establishing wide → medium on vehicle → interior face → POV → insert → result wide |
| Eyeline | Always clear who is looking at whom: face looks off-screen left → next shot is the POV in that direction |

## 5. Lighting

| Setup | Spec |
|---|---|
| Exterior | Overcast or soft sun, sky dome + soft directional. Low-contrast daylight, long soft shadows. Haze for depth |
| Interior | Near-black with **2–3 small hard white practicals** in frame (cabin lamps) + daylight spill from the vision slit/hatch. Faces half lit |
| Fire/explosions | Orange bounce on the hull and faces, short and bright |
| Climax | Hard rim light, sweat and dirt highlights |

## 6. Environment and VFX

| Item | Spec |
|---|---|
| Density | Very high ground detail: puddles with reflections, mud ruts, grass clumps, flowers, fences, firewood piles, telegraph poles, wooden houses, church spire |
| Layering | Foreground grass or branches in ~30% of wides (parallax and depth) |
| Smoke | Grey-black volumetric columns from wrecks, drifting |
| Fire | Volumetric flames on wrecks and inside houses |
| Explosions | Fireball + spark streaks + debris; often seen **top-down** |
| Shells | Hero object: slow-mo shell with spec overlay (name, calibre, weight, velocity) |
| Hits | Ricochets with spark showers, penetration holes with smoke |

## 7. Graphics and text

| Element | Spec |
|---|---|
| Date tag | Top-centre thin caps "JULY 22, 1944" + place, at the very first frame |
| Vehicle card | Left: small caps class ("MEDIUM TANK"), big bold name ("T-34-85"), spec table (crew, armament, armour, engine, speed, mass) in thin white text over the 3D shot |
| Person card | Bold caps name + small rank/unit lines + archival B&W photo |
| Shell card | Bold name above the slow-mo shell + small spec table |
| Distance callouts | "800 METERS." in thin caps near the target |
| Dialogue | Subtitled shouts in thin caps, lower third |
| Maps | **None** in this film (one top-down village shot with a German cross icon) |
| End card | Archival photos with captions + epilogue text, then the narrator's 3D character presents the next film |
| Font family (obs) | Geometric sans (Montserrat-like), bold for names, light for data |

## 8. Sound (measured + recreation method)

Measured from the file. Stems can't be separated; layer descriptions come from what the VO and picture describe.

| Item | Measured / obs | Seldom recreation |
|---|---|---|
| Integrated loudness | **−10.4 LUFS**, loudness range **3.4 LU** (very dense and compressed) | Master to −14 LUFS integrated (YouTube normalises anyway), LRA 4–6 LU so it keeps some dynamics |
| Silence | **No gaps below −45 dB longer than 0.8 s** anywhere; only the last 20 s drops (end card) | Never true silence: keep a room-tone or wind bed under everything. Use "relative silence" (music out, only crackling fire) for impact moments |
| Short-term level | Median −9.4 to −11.8 LUFS per 30 s window; louder in fights, quieter in tension beats (6:30, 8:30) | Plan a loudness curve per beat: −3 LU for tension, peak at kills |
| Cuts vs hits | Cuts are **not** systematically on transients (49% of cuts have a >6 dB rise vs 46% at random times) | Don't put a whoosh on every cut. Hits land on story events (fire, impact), not on edits |
| Beds (obs) | Continuous: engine rumble, track clank, wind/field ambience; interior: muffled engine + cabin rattle | Per location: exterior field bed, interior cabin bed (low-pass the exterior), fire crackle bed |
| Foley (obs, from picture/VO) | Hatch slams, shell into breech, hand crank, trigger click, radio crackle, debris pattering on armour, MG rattle | Foley list per shot from the shot plan; record or license (e.g. Soundly/Boom Library/Sonniss GDC packs) |
| Weapons | Big low-end cannon blasts + tail, ricochet whines, penetration crunch | Layer: transient + low boom + mechanical + tail; sidechain the music under each blast |
| Dialogue | Short shouted lines in character (subtitled) over the radio/intercom | Record our own short lines, band-pass for radio |
| Music | Continuous orchestral-hybrid tension bed under the VO (obs: no music drops to silence) | License or compose cues per beat: tension pulse → action ostinato → "decision" stinger → aftermath pad |
| VO vs bed | VO always on top and intelligible | VO at −16 to −18 LUFS short-term, music −26 to −30, SFX peaks −10 to −12; duck the music 6–8 dB under VO |

## 9. Script study (paraphrased; no verbatim transcript)

### Stats (measured)

| Metric | Value |
|---|---|
| VO words | ≈2,470 in 16:20 of VO → **≈151 words/min** |
| Sentences | 164 · median **14 words** · mean 15 · p10 7 · p90 24 |
| Very short sentences (≤5 words) | 10, all at turning points ("It's too late.") |
| Long sentences (≥25 words) | 14, used for action chains (aim → fire → impact) |
| Questions | **0**. Pure present-tense narration, no rhetorical questions |
| Tense / POV | Present tense, third person, swapping POV between the German and Soviet commanders |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:00 | Exact date + named German ace + mission in one sentence | Specific date, name, goal |
| 0:16 | Immediate enemy: a seemingly abandoned Soviet tank | Danger in the first 20 s |
| 0:22 | POV switch: a sleeping Soviet captain wakes up inside it | Dramatic irony (we know both sides) |
| 0:33 | Ace passes by; Soviet crew hand-cranks the turret to aim at him | Ticking clock |
| 0:51 | Twist: a second Tiger they didn't see | Reversal |
| 1:09 | Faster hydraulic traverse wins; first kill at 1:19 | Payoff in under 90 s, with a technical reason |

### Chapter structure (no title cards; flow by POV and location)

| Time | Act | Beat (paraphrased) |
|---|---|---|
| 0:00–1:45 | Act 1a — South road | Tigers enter; first T-34 destroyed thanks to the wingman |
| 1:45–4:26 | Act 1b — North side | Soviet captain fights assault guns; calls in an IS-2 "ace card"; Soviets gain confidence |
| 4:26–5:45 | Act 2a — Tigers advance | T-34 ambush fails; crew bails; ace spares them to save time |
| 5:45–8:03 | Act 2b — The mystery tank | Ace sees an unknown huge gun, hesitates, identifies an IS-2, kills it with two shots |
| 8:03–11:12 | Act 2c — Collision | Soviets unaware; radio call cut off; the Soviet captain faces the ace; his shot glances off; he is killed |
| 11:12–14:13 | Act 3a — Rout and duel | T-34s flee; a slow IS-2 duels the Tiger; both miss; reload race; Tiger wins |
| 14:13–15:53 | Act 3b — Aftermath chase | Surviving Soviet crew flee on foot; MG fire; the captain chooses his pistol |
| 15:53–16:39 | Epilogue | Silence of the burning field; real-world outcome; ace's later life; next-video plug |

### Writing techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Exact date and place up front | "It's July 22, 1944…" | Instant authenticity |
| Dual POV / dramatic irony | "…they don't see the second Tiger advancing…" | Viewer knows more than the characters |
| Technical reason for every outcome | "The Tiger gunner's hydraulic traverse is far quicker than Orlowski's hand cranks" | Smart payoff, not luck |
| Specific numbers | "…a 122mm shell slams into the grass…" | Concrete, visual |
| Short sentence at the turning point | "It's too late." | Rhythm break = tension spike |
| Interior sensation | "…his heart pounding." | Puts us in the cabin |
| Time dilation | "Time slows to a crawl…" | Licenses slow motion on screen |
| Sensory cut to black | "Moroz's world goes black." | Death without gore |
| Hesitation beat | "…for a moment they freeze." | Suspense before action |
| Reload race | "Now it's a race to reload." | Clear stakes, ticking clock |
| Ironic epilogue | ace later opened a pharmacy named after his tank | Human ending |

### Seldom script template (from these patterns)

| Block | Length | Rules |
|---|---|---|
| 1. Cold open | 0:00–1:30 | Sentence 1 = exact date + named person + goal. Danger by 0:20. Show both sides by 0:40. First payoff by 1:30 with a technical/factual reason |
| 2. Second front | 1:30–4:30 | New POV character with their own goal. End on an "ace card" or reversal |
| 3. Escalation ×3 | 4:30–11:00 | Three encounters, each harder. Each = see → hesitate → act → result. One short sentence per climax |
| 4. Collision | 11:00–14:00 | The two POV lines meet. Ticking-clock duel (reload/time/distance) |
| 5. Human aftermath | 14:00–15:30 | Slow down: one person, one choice. Sensory language, fade to black |
| 6. Epilogue | last 45 s | Real outcome with numbers + one ironic or human detail + next film |
| Style rules | all | Present tense · median 14 words/sentence · ≈150 wpm · no rhetorical questions in action · every number visual · a short line (≤5 words) at every turning point |

## 10. Scene-by-scene breakdown (grouped beats)

| TC | Shots | On screen | Camera | Light | Why it works |
|---|---|---|---|---|---|
| 0:00–0:19 | 0–5 | Tiger in a village lane, date tag, commander in the hatch + archival portrait card, second Tiger, POV over the hull | Low tracking, MCU | Overcast | Place, time, hero, vehicle in 19 s |
| 0:19–0:58 | 6–12 | T-34 with spec card, Soviet captain waking in a dark cabin, vision-slit POV of the passing Tiger, turret crank insert | Static wide, dark interior ECU, POV | Interior near-black | Dramatic irony set up visually |
| 0:58–1:45 | 13–22 | Second commander in a lit cabin (name card), gunsight POV, black, shell slow-mo with spec card, **top-down explosion**, commander turns, fast forward dolly | POV, slow-mo, top-down | Cabin practicals, fire | Signature "sight → shell → impact" chain |
| 1:45–2:31 | 23–31 | Soviet captain (archival card), StuG hit at 800 m callout, sight POV, hand on firing lever, Soviet shell slow-mo, vision-slit POV of a StuG | Interior MCU, POV | Dusty | Same chain from the other side |
| 2:31–3:23 | 32–43 | Top-down village with icon, whip dolly, Soviet tankers' faces, IS-2 emerges (spec card), Tiger barrel through haze, IS-2 muzzle (20 s hold) | Long hold on the IS-2 | Haze | The "ace card" gets a 20 s reveal |
| 3:43–4:26 | 44–53 | Shell bounces off, top-down explosion, burning StuG, T-34 advancing, captain shouting, sight POV hit | Mixed | Fire orange | Momentum swing |
| 4:26–5:45 | 52–71 | Tiger advancing (15 s), commander POV over the hull, T-34 behind a house, hand on the trigger, **shell "SUBSCRIBE" mid-roll joke**, T-34 burns, crew bails, Tigers' faces | Hull-height tracking | Overcast | One clean ambush |
| 5:45–8:03 | 72–103 | Commander with binoculars, binocular POV of a strange muzzle behind a barn, cut-in on a blue cobbled street (other vehicle), faces freeze, IS-2 wheels ECU (9 s), muzzle brake, **sponsor card (game) in the same look**, green tracer, two penetration holes smoking, IS-2 burns, commander slumps | Binocular POV, ECU wheels | Overcast | Hesitation beat built from 3 POVs |
| 8:03–9:26 | 103–121 | Village with smoke columns, T-34 452 crew, vision slit "Germans behind us! Tigers!", burning T-34, Soviet captain climbs out, faces in close-up with dirt | Wides with smoke, MCU | Haze + fire | Collision of the two lines |
| 9:26–10:54 | 121–144 | Loader with shell insert, "Tiger, 300 meters!", "FIRE!", shell slow-mo, ricochet sparks off the Tiger, "RELOAD, FASTER!" interior chaos, **Tiger muzzle ↔ captain's eyes intercut (1–2 s)**, black | Intercut ECUs | Interior dark, faces lit | Shot/reverse at 1 s = maximum tension |
| 11:01–12:11 | 145–156 | Sight POV on the fleeing T-34s, Tiger barrel tracking, T-34s across fields, binocular POV | Tracking, POV | Sunny field | Rout |
| 12:13–14:01 | 157–180 | "3 O'CLOCK!", sight POV, hand on the crank, IS-2 turret turns, shell slow-mo, eyes in the sight, "WATCH OUT, IT'S FIRING!", near miss, reload race, hit | Rapid ECUs 1–2 s | Cabin practicals | Duel with a ticking clock |
| 14:01–15:53 | 180–201 | Commander breathes, binocular POV, two men flee across grass, MG bursts, wounded man, dragging his comrade (12 s), pistol raised, cut to black | Long lens through grass, handheld | Low sun | Human ending, violence implied |
| 15:52–16:39 | 202–203 | Archival photos with captions, narrator character in front of the burning village presents the next film | Static | Fire behind | Real-world payoff + channel brand |
