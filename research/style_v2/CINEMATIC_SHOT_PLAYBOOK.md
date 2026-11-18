# Cinematic Shot Playbook — plan every scene like a film

Built from the references in this folder (Yarnhub, Atrium, Fern). Each rule names the shot where we saw it.
Worked example: **Film 2, "The Phone That Killed a Banker"**, Intro + Chapter One (`all_scripts.md`). I picked it as "our next film" because it is next in the script list; any of films 2–6 uses the same template.

## 1. The scene unit: one beat = one mini-sequence

Every story beat (one or two VO sentences) gets a **coverage set**, not a single shot.

| Step | Shot | Size / lens | Length | Purpose | Reference |
|---|---|---|---|---|---|
| 1 | **Establishing** | Wide, 24–35 mm, low or high | 3–6 s | Where and when (date/place tag here) | Yarnhub 0:00 Tiger in the village lane; Atrium Lincoln 9:28 White House at dusk |
| 2 | **Character** | MCU, 50–85 mm | 2–4 s | Who wants what (name card here) | Yarnhub 0:06 commander in the hatch + archival card |
| 3 | **POV / object of attention** | Through an optic, keyhole, screen, or OTS | 2–4 s | What they see | Yarnhub gunsight 1:14; Atrium gimlet peephole 8:05 |
| 4 | **Insert** | Macro, shallow DOF | 1–2 s | The action, by the hands | Yarnhub hand on the trigger 2:00; Lincoln derringer 10:49 |
| 5 | **Result** | Wide or medium | 2–5 s | Consequence | Yarnhub top-down explosion 1:32 |
| 6 | **Reaction** | MCU/ECU face | 2–4 s | Emotion | Yarnhub 1:51 Soviet captain; 10:11 eyes |

Rule: **at least 4 of the 6 steps per beat**, in that order or with 3–4 swapped for suspense.

## 2. Shot/reverse-shot and dialogue

| Rule | Spec | Reference |
|---|---|---|
| 180° line | Keep both characters on their side; first cross only with a visible move | Atrium Lincoln cabinet meeting 2:17–2:36 |
| Sizes match | Both sides of a conversation use the same size and lens | Atrium Lincoln 4:02 Grant ↔ Lincoln |
| OTS first, singles later | Start with OTS (we see both), move to clean singles as tension rises | Atrium Alcatraz bars 15:31–15:43 |
| No lip-sync | Speaker from behind, OTS, or the listener's reaction while the line plays (subtitled) | Yarnhub "FIRE!" / "RELOAD, FASTER!" |
| Duel intercut | At the climax, alternate the two sides at 1–2 s | Yarnhub 10:41–10:53 muzzle ↔ eyes |

## 3. Motivated camera moves

| Move | Use when | Reference |
|---|---|---|
| Slow push-in (2–5% per second) | A character realises something; a key object | Yarnhub 8:00 village; Fern Puyi throne holds |
| Lateral track with the subject | Travel, procession, vehicle | Yarnhub 0:09 Tiger alongside |
| Handheld micro-shake | Inside tight spaces, under stress | Yarnhub cabins |
| Whip pan | Firing, sudden noise | Yarnhub 1:41 |
| Top-down | Geography, an aftermath, an object on a table | Yarnhub explosions; Lincoln 8:05 corridor |
| Locked-off | Dread; let the subject move | Atrium Lincoln 17:15 deathbed |
| **Never** | A move with no reason; a static frame with nothing moving (QA fails it) | Our part 2 frozen shots |

## 4. Blocking (where people stand and move)

| Rule | Why | Reference |
|---|---|---|
| Characters work **seated, in a hatch, at a desk, behind bars or a table** | Hides legs and walks; gives hands a place | Yarnhub hatches; Fern Puyi throne; Alcatraz cells |
| Entrances through a door or frame edge, ending in a still pose | Short locomotion, clear start and end | Lincoln 0:29 Booth through the door |
| Walks only from behind, in low light, through foreground, ≤2 s | Hides foot contact | Lincoln 3:14 stable; Yarnhub 14:30 field |
| One prop per hand | Clear action, no intersections | Yarnhub shell loading |
| Depth staging: foreground object, character mid, background detail | Cinematic depth | Yarnhub grass foregrounds |
| Spotlight blocking on black for "explain" beats | A character stands still in a pool of light | Fern Puyi Johnston; Fern Hansa |

## 5. Emotion beats and rhythm

| Beat type | Shot recipe | Length | Script cue |
|---|---|---|---|
| Hook | Wide in motion + date tag → MCU → danger insert | 15–20 s | Exact date + name + goal |
| Rising tension | Shorter shots (2–3 s), more POV and inserts, closer sizes | 30–90 s | "Then it happens." |
| Decision | Push-in on the face, 4–8 s, sound pulls back | 1 shot | Short line ≤5 words |
| Action peak | 1–2 s cuts, slow-mo hero shot of the key object | 10–20 s | Long chain sentence |
| Release | Wide, locked off, longer (6–12 s) | 1–2 shots | "That was close." |
| Aftermath / loss | ECU eyes or an empty object, fade to black | 5–15 s | Sensory line ("world goes black") |
| Chapter end | Cliffhanger line on a held frame | 3–5 s | Foreshadow ("Little does he know…") |

Targets: median 3.5–4.5 s, p90 ≈ 10 s, one 15–30 s hero take per chapter (measured refs: Yarnhub 3.9, Atrium 3.2–4.3, Fern 2.6–6.4).

## 6. Shot-plan template (one row per shot, for `chapter_shots.py`)

| Field | Example |
|---|---|
| id | ch1_04 |
| VO words | "By the time he reaches the hospital, he's in a coma." |
| beat type | decision / tension / peak / release |
| shot | MCU · 85 mm · seated · push-in 3%/s |
| action verb + reason | "eyes close" ← "losing consciousness" |
| hands | none / insert only / one prop |
| legs visible | no |
| light | practical: ambulance ceiling strip, cold |
| sound | siren muffled, monitor beep, room tone |
| QA | motion > 0.5% · no intersections · eyeline matches previous shot |

## 7. Worked example — Film 2 Intro + Chapter One (paraphrased beats)

| # | VO beat (paraphrased) | Shot | Size / move | Blocking / action | Light | Ref |
|---|---|---|---|---|---|---|
| 1 | Look at this phone; a faint stain | **Insert**: white 1990s desk phone, macro on the handset plastic | Macro, slow push, f/2 | No people | Single desk lamp, dust in the air | Ötzi mummy macro |
| 2 | It belongs to a Moscow banker; he and his secretary are dead | **Establishing**: Moscow bank office at night, empty chair | Wide, low, locked | Empty chair = absence | Window blue + lamp | Lincoln deathbed |
| 3 | The substance still affects people; eight police officers | **Wide**: officers in the doorway, one coughing | Medium wide from inside the office | Standing at the door frame, no walking | Hall light backlight | Alcatraz guards |
| 4 | The clue is on his desk; the telephone | **Push-in** to the phone, rack focus from officers to phone | MCU → ECU | — | Lamp | Yarnhub muzzle reveal |
| 5 | Date tag: August 1, 1995, Moscow | **Date card** + establishing bank exterior, dusk | Wide, slow lateral | Cars passing in haze | Dusk | Yarnhub 0:00 |
| 6 | He makes calls in the afternoon | **MCU**: banker at desk, phone to ear, **back three-quarter** | MCU, handheld micro | Seated; hand + phone = one prop | Afternoon window | Hansa desk scenes |
| 7 | His brother finds him unwell | **OTS** brother → banker; **reaction** banker rubs his eyes | OTS then MCU | Brother stands in the door, no walk | Same | Lincoln cabinet |
| 8 | By the hospital he is in a coma | **ECU** eyes closing in the ambulance | ECU, push-in | Lying down | Cold ceiling strip | Yarnhub 10:51 |
| 9 | Next evening: his secretary to another hospital | **Wide**: ambulance doors closing at night | Wide, locked | — | Rain, red/blue lights | Fern Puyi colour script |
| 10 | Pathologist sees two diagnoses with question marks | **Insert**: hand on the file, two pencil marks "?" | Macro, top-down | Hand + file | Desk lamp | Fern Heydrich desk props |
| 11 | He hears on the radio the banker died | **Insert** radio + **MCU** pathologist stops writing | Insert → MCU push-in | Seated | Lamp | Fern Chernobyl radio |
| 12 | Both patients: constricted pupils, enzyme near zero | **Graphic in 3D**: two pupils shrinking side by side; "CHOLINESTERASE → 0" written on the wall | Static, 20 s hold | — | Clinical white | Ötzi facts in the room |
| 13 | How the nerve signal works | **Science on black**: one-line equation, 30 s | Static | — | Black | Chernobyl "→ MELANIN →" |
| 14 | Faint mark under a rubber plug in the handset | **Macro**: gloved hand unscrews the plug, residue | Macro, 1 prop | Gloved hands only | Torch beam | Yarnhub shell insert |
| 15 | "It's Kivelidi's phone." | **Hold** on the phone, light flickers off | ECU, locked, 4 s | — | Lamp off | Short line ≤5 words |
| 16 | The phone is still a hazard; a cleaner, officers | **Top-down** office, figures frozen as clay statues | Top-down, slow rotate | Clay figures = people only mentioned | Cold | Atrium clay conspirators |
| 17 | Memorial with Gorbachev and the PM | **Archival photo** framed + 3D hall wide | Static | — | Cold daylight | Fern archival cards |
| 18 | Who was in the office before he fell ill? | **Push-in** on the empty chair from shot 2 (callback) | MCU, slow | — | Lamp | Ring structure |

Checks for this sequence: 18 shots ≈ 3:40 → median ≈ 4 s ✔ · no full-body walks ✔ · hands only in inserts (6, 10, 14) ✔ · every shot has a verb or a move ✔ · one long hold (13, 30 s) ✔ · one callback (18 ↔ 2) ✔.
