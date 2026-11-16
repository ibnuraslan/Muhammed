# B12 IronRodHead: plan (Phase 1, before the VO)

Film: 1080×1920, 60 fps, Cycles, hard cuts, one camera object per shot (`CAM_Sxx`, bound by timeline markers).
Reference: `briefs/batch2/B12_IronRodHead_reference_1fps.jpg` (39 s). It's an **OLD-style** reference (flat sky-blue backdrop),
so only the story and beat order come from it. Every scene is a real set in our current look: an 1848 railroad cutting
(rock walls, ballast, wooden sleepers and iron rails, plank crates, a wheelbarrow and a pickaxe). The skull/brain diagram floats above
the track, with the cutting as its real background.

Phase-1 timeline: every shot is its own clip, about 30% longer than the reference beat, laid end to end (frames below).
All action is keyed from offsets in `scripts/timing.py`. In Phase 2 only that table changes to the VO word frames, then a rebuild. Nothing is time-stretched.

## Cast (generic MPFB characters from our WW1Assassination_v007 package, with the eye fix and hand limits; elbow IK limit opened per rig)
| Name in file | Role | Look |
|---|---|---|
| `Gage` | the railroad foreman (generic, no likeness) | light-blue shirt, denim-blue bib overalls, short dark hair; white head bandage from S11 on |
| `WorkerB` | co-worker | brown suit, felt hat |
| `WorkerC` | co-worker | olive suit, bare head |
| `ExtraA`, `ExtraB` | background workers (S01, S05) | grey suit + hat, rust work suit |

## Shots (P1 frames; the reference VO idea is in brackets)
| # | Beat | Camera | Who and what they physically do | Frames P1 |
|---|---|---|---|---|
| S01 | "In 1848" | Crane down from 5 m to eye level, over the track toward Gage at the rock wall; logo crate stack beside him | Gage tamps the iron bar in the drill hole (lifts ~11 cm and drops it, a 46-frame cycle). Two extras walk along the far side, arms swinging | 1–156 |
| S02 | "a large iron rod" | Low 3/4 front of Gage, slight push-in | Same tamping, closer: the bar in his right fist, left arm hanging relaxed, face readable | 157–276 |
| S03 | "drove" | Ground-level close-up on the hole, f/8-equivalent (no DOF). Hands are framed out above | Bar tamps twice, then a stylised orange flash, a dust puff and grit, and the bar shoots straight up out of frame (≈6 frames). Cut on the flash | 277–360 |
| S04 | "through the face and head of a man" | Side medium from the track side | No rod-into-face shot. Gage is thrown back: head snaps back, hands fly open to the sides (below the shoulders), two stagger steps, drops to sitting with his palms flat on the ground behind him | 361–516 |
| S05 | "he was working on a railroad" | Low camera beside the track; Gage small, sitting in the background | The bar falls from the sky, sticks in the dirt in the foreground and quivers, with a dust puff. WorkerB and WorkerC run in from the far side toward Gage (arms swinging). The extras turn | 517–672 |
| S06 | "It passed behind…" | Diagram: slow orbit, 3/4 front-left of the skull | Cream skull (4× life size) with a cutaway window in its left side showing the pink brain. The iron slides up under the left cheekbone, behind the eye socket, and out of the top | 673–828 |
| S07 | "…his left eye" | Push-in on the left eye socket / window | The iron sits behind the orbit, creeping up slightly | 829–924 |
| S08 | "through the top of his skull" | High front, looking down at the crown | The tip breaks out of the top, and small cream bone chips fly up and fall | 925–1080 |
| S09 | "and he somehow managed to stay conscious" | Low medium two-shot | Gage sits up (forearm on his knee), breathes, turns his head to WorkerB, who squats in front of him with his hands on his own knees | 1081–1314 |
| S10 | "while the rod was removed" | Diagram side view | The iron slides back down and out; dark entry and exit holes remain | 1315–1470 |
| S11 | "Now he did survive this incident" | Camera backs away in front of him along the track | Weeks later: Gage walks toward the camera with a white head bandage, arms swinging, a small head turn | 1471–1704 |
| S12 | "but he wasn't the same person" | Medium wide, logo crate stack between them | WorkerB and WorkerC at the crates look toward each other. WorkerB shrugs, palms up at waist height. WorkerC shakes his head | 1705–1860 |
| S13 | "You see, the rod went…" | Diagram (brain only), orbit | The iron passes up through the brain's left frontal area | 1861–2016 |
| S14 | "…through his frontal lobe" | Push-in | The frontal lobe turns yellow (keyed mask on the front of the brain) | 2017–2172 |
| S15 | "this area of the brain is responsible for decision making" | Orbit from the front | The iron is gone. The frontal lobe turns violet and pulses | 2173–2406 |
| S16 | "and self-control" | High 3/4 orbit | Pulses continue | 2407–2562 |
| S17 | "was damaged" | Slow push | The glow flickers out and the frontal area greys (damaged) | 2563–2670 |
| S18 | "his entire personality" | Close-up of Gage's face (bandage) | Glare, fists close, head turns toward the crate stack | 2671–2778 |
| S19 | "changed" | Side medium | Gage winds up and kicks the bottom crate: the bottom crate slides back, the two on top topple off the far side and land, with a dust puff | 2779–2934 |
| S20 | "impulsive" | Camera backs away in front of him | Gage storms along the track toward the camera, head down, arms swinging hard | 2935–3054 |
| S21 | "erratic" | Side two-shot, faces 3/4 | Gage jabs a pointing finger at WorkerC (30 cm short of him, no contact). WorkerC leans back, open palms up at chest height | 3055–3210 |
| S22 | "and unpredictable" | Close-up of Gage, push-in | His head jerks round to the camera with a glare, then he looks away. Hard cut to end | 3211–3366 |

P1 total: 3366 frames (56.1 s). The VO sets the real lengths.

## Logo (DA KRAS FILMS)
- Dark logo on the front of the large supply crate beside Gage's work spot: **S01** (wide, flat to the camera at the end of the crane) and **S12** (between the two co-workers, flat to the camera, about 25% of frame width).
- Not on the accident, diagram or anger beats. The crates Gage kicks carry no logo.

## Risky shots: the simplest safe staging
| Risk | Staging |
|---|---|
| Rod in hand | One-hand grip only (right fist on the bar, `grip_object` wrap, IK hand driven from the bar's transform so the bar never moves without the hand). The left arm hangs relaxed. In S03 the hands are framed out, and the bar leaves on the flash. |
| Rod through the face | Never shown on the man. S04 shows only the reaction (thrown back, sits down). The path is shown only on the clean anatomy diagram (cream skull, pink brain, dark iron, no blood). |
| Bone breaking | Stylised cream chips only (S08). Entry and exit are dark discs (S10). |
| Fall | Two stagger steps and a sit-down. Palms flat on the ground, feet planted, no hand near the face. |
| Kick | The foot meets the crate face (ankle at 2.50 m, crate face at 2.625 m). The crates fall away from him on a keyed pivot, with no hands involved. |
| Pointing | The finger stops 30 cm short of WorkerC's chest. No arm crosses another body. |
| Bandage | A band fitted to the evaluated head shape (forehead height, 6 mm off the skin) plus a crown pad, both Child Of the head bone. |
