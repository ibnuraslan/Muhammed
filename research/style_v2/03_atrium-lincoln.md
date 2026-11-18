# Style 03 · Atrium — "The Most Famous Killing In American History" (Lincoln / Booth)

| | |
|---|---|
| Source | Drive `style/…Atrium (1080p).mp4`, 18:01, 1920×1080, 60 fps, **16:9 full frame** |
| Shots | 256 · **median 3.2 s** · p10 1.2 s · p90 8.1 s |
| Contact sheet | `03_atrium-lincoln.jpg` (all 256 shots) |
| Verdict | **Much stronger than Atrium's Alcatraz** and close to the target: rich period interiors, warm practical light, dramatic coverage. Best reference here for **interior drama with dialogue** |

## Look (measured + obs)

| Item | Spec |
|---|---|
| Brightness | Luma p5 0.04 · median 0.19 · p95 0.62 → **low-key**, nothing clips |
| Saturation | Median **0.44** (richest of all refs) |
| Palette | `#261511` 14% · `#3e221a` 14% · `#0d0a09` 12% · `#4d342a` 12% · `#92674d` 8% · `#20242a` 8% · `#664d43` 7% · `#723727` theatre red 7% · `#a89187` 5% · `#37414e` night blue 5% → **oxblood, walnut, brass, candle amber, one cool night blue** |
| Light | Oil lamps and gas lights motivate everything; warm key + deep falloff; exteriors at blue dusk |
| Sets | High-detail period sets (patterned wallpaper, carpets, chandeliers, theatre boxes, stables, cobbled streets) |
| Devices | **Countdown cards**: black screen, red bold number + thin caps ("10 HOURS / UNTIL ASSASSINATION", then 9, 8, 6…) · archival portrait inset in a white frame beside the 3D actor · letter text in handwriting full-frame · red/blue two-flag graphic for the war · **grey clay figures** for conspirators who are only mentioned · top-down shots of the box and corridor |

## Characters and staging

| Item | Obs | Lesson |
|---|---|---|
| Faces | Real-time digital humans with likeness to period photos, beards and hair grooms; moderate expressions | Likeness supported by the archival inset |
| Hands | **Expressive gestures in MCU** (Lincoln's open hands, the hand on the horse, the derringer insert) | Gestures are filmed waist-up so legs don't matter |
| Walks | Present (Booth crossing the theatre, leading a horse), mostly from behind or at a distance in dim light | Back view + low light hides foot contact |
| Action | The leap from the box and the fall on stage are shown in 2–3 short shots (1–3 s) | Fast cutting hides imperfect physics |
| Coverage | Shot/reverse in the cabinet meeting, OTS in the box, insert of the door hole (gimlet), top-down corridor | Classic thriller coverage |
| Crowd | Theatre audience as greyed, low-detail instanced figures | Crowd quality can be low if out of focus and desaturated |

## Sound (measured)

| Item | Value |
|---|---|
| Integrated | **−14.3 LUFS**, LRA 3.3 LU |
| Silence | **0** gaps below −45 dB longer than 0.8 s |
| Obs | Theatre laughter and the play's lines are part of the timing ("from the play's lines, Booth notes he still has about 30 minutes") |

## Script study (paraphrased)

| Metric | Value |
|---|---|
| Words / pace | ≈2,480 words · **≈139 wpm** |
| Sentences | 306 · **median 7 words** · p90 13 · 96 sentences ≤5 words |
| Questions | 6 |
| Dialogue | Short, voiced character lines with tags ("…Booth demands") |

### Hook (first 60 s)

| Time | Beat (paraphrased) | Technique |
|---|---|---|
| 0:00 | Lincoln reads his mail; one letter is a death threat; he smiles and crumples it | Character in action + danger in 15 s |
| 0:20 | Over 10,000 threats; the real danger is later tonight | Number + misdirection |
| 0:29 | A famous actor walks into Ford's Theatre | Antagonist entrance |
| 0:30 | **"10 HOURS UNTIL ASSASSINATION"** | Countdown device starts |
| 0:56 | A stagehand reveals the special guest; the actor freezes | Inciting moment |

### Structure: countdown thriller

| Time | Countdown | Beats (paraphrased) |
|---|---|---|
| 0:30–1:41 | 10 h | Booth learns the president is coming; past kidnap failures; knows the theatre |
| 1:41–2:54 | 9 h | War context (graphic); cabinet meeting; Lincoln works for peace |
| 2:54–3:51 | 8 h | Booth hires a horse; plan with accomplices (escape route) |
| 3:51–6:30 | 6 h → | Lincoln's dream of a funeral; the bodyguard situation; Booth gets in behind the stage |
| 6:30–7:30 | — | Sponsor (game), in the same visual style |
| 7:30–9:05 | — | Booth bores a peephole and prepares a bar for the door; near discovery |
| 9:05–11:10 | — | Lincoln's carriage, theatre arrival, accomplices assigned their targets |
| 11:10–15:45 | — | Waiting for the laugh line; the guard is absent; Booth reaches the box |
| 15:45–16:50 | 0 | The shot, the leap, the escape on the horse |
| 16:50–18:01 | Epilogue | Lincoln dies the next morning; the accomplices' fates; Booth is killed |

### Techniques (≤15-word examples)

| Technique | Example | Effect |
|---|---|---|
| Countdown title cards | "10 HOURS UNTIL ASSASSINATION" | Known ending becomes suspense |
| Misdirection | "But the real danger isn't in any of these." | Raises the stakes immediately |
| Freeze beat | "Booth freezes." | Two-word reaction line |
| Inside knowledge | "He knows every corner of Ford's theater." | Makes the antagonist competent |
| Precise detail | "boxes 7 and 8" | Authenticity |
| Ticking clock from diegesis | timing the shot to a laugh line in the play | Clever, specific suspense |
| Near miss | "That was too close." | Tension release |
| Ironic omen | Lincoln's dream of a death in the White House | Foreshadowing |

## What Seldom can take from Atrium Lincoln

| # | Technique | Pipeline | Effort |
|---|---|---|---|
| 1 | Countdown cards (red number + thin caps) | `title_card.py`: `countdown_card(value, unit, label)` | Easy |
| 2 | Lamp-motivated low-key interiors (oxblood/walnut/brass) | `look.py`: "period interior" preset; area lights with warm 2700 K, strong falloff | Easy |
| 3 | Archival portrait inset beside the 3D actor | Comp template (white frame, left/right third) | Easy |
| 4 | Grey clay figures for people who are only mentioned | Clay material on MakeHuman meshes | Easy |
| 5 | Gesture-driven acting in MCU (hands visible, legs not) | Shot rule: dialogue in MCU/MS; legs out of frame | Easy |
| 6 | Big action as 2–3 very short shots | Edit rule for stunts (jump, fall) | Easy |
| 7 | Out-of-focus, desaturated crowds | Instanced low-poly crowd + DOF + desaturation in comp | Medium |
