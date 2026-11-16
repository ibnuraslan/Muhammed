# B23 HandlessWarrior: plan (Phase 1, before the VO)

Film: 1080×1920, 60 fps, Cycles, hard cuts, one camera object per shot (timeline markers bind them).
Reference: `briefs/batch2/B23_HandlessWarrior_reference_1fps.jpg` (29 s, current style). Shot order, subjects and framing
ideas follow it: meadow + soldier at a chopping stump → he lifts his stumps → sent back → thatched meeting hut with
patterned-robe villagers → forge/anvil sealing → knives tied to the forearms → meadow fights with armoured soldiers →
pink dusk flag → the army with spears → he fights to the end.

Phase-1 timeline: every shot is its own clip, ~30% longer than the reference shot, laid end to end (frames below).
All action is keyed from offsets to the shot starts in `scripts/timing.py`, so Phase 2 only changes that table to the
VO word frames and rebuilds (nothing time-stretched).

Build: `scripts/01_chars.py` → `02_sets.py` → `03_anim.py` (assets: CC-BY Sketchfab via Objaverse, CC0 Poly Haven, see
`review/model_credits.json`; MPFB cast appended from our ShoeBomber, Tsunami and WW1 packages).

## Cast (generic MPFB characters, no real likeness)
| Name in file | Role | Look |
|---|---|---|
| `Warrior` | the warrior | tan skin, short dark hair (fringe trimmed so both eyes show), deep-red tunic with woven bands, brown trousers. **Hands removed** by a Mask modifier (wrist + finger groups) from S02 on; each stump is closed by a rounded cream cloth bandage (no wound geometry, no blood) |
| `Elder`, `VillagerW`, `VillagerM1`, `VillagerM2` | his people | solid-colour robes with woven bands (cream/blue, ochre, green, cream/maroon), non-skin colours |
| `SoldierA` | soldier at the stump (S01–S03) | red doublet, steel cuirass (deforms with the body), steel morion helmet, sword |
| `SoldierB` | soldier he cuts down (S13) + master of the guard ring (S17) | blue doublet, steel cuirass and morion; spear in S17 |
| `Second` | the general's second-in-command (S14) | red doublet, **brass** cuirass and brass morion (reads as the officer), sword |
| `SoldierC` (+14 copies) | the invading army (S16–S17) | red doublet, steel cuirass/morion, spear; copies share the master's march action |

## Shots (Phase-1 frames; reference second in brackets)
| # | Beat (ref VO) | Camera | Who and what they physically do | Frames P1 |
|---|---|---|---|---|
| S01 | They cut off (0–1.5) | wide, low front-left, slow push | Warrior kneels behind the stump, palms flat on its top; SoldierA beside it lifts his sword from his side to his shoulder (hand stays below the hair line). **Cut before any blow.** | 1–117 |
| S02 | as punishment (1.5–2.5) | low front medium, push-in | Still kneeling, he lifts both bandaged forearms to his face, head tilting back in pain (mouth closed) | 118–225 |
| S03 | then sent him back (2.5–3.5) | side medium from the left | SoldierA points to the village with his free hand (sword point-down in the other); the warrior turns and walks away, arms swinging | 226–375 |
| S04 | to his people (3.5–4.5) | tracking 3/4 front, village huts behind | He walks across the meadow toward the huts | 376–495 |
| S05 | with instructions to surrender (4.5–6) | over his right shoulder, inside the open thatched hut | Villagers stand in a loose arc facing him; the elder raises an open hand (surrender gesture) | 496–645 |
| S06 | But the warrior convinced them (6–8) | front close-medium | He raises his bandaged right forearm, argues, head moving | 646–801 |
| S07 | to keep fighting (8–9.5) | wide from the right, the logo crate behind them | The villagers raise their right fists to shoulder height, nod | 802–921 |
| S08 | and instead of (9.5–11) | forge close-up, push-in | Iron plate glowing on the embers, flames (keyed GN clock) | 922–1041 |
| S09 | he sealed with hot metal (11–13) | from behind the anvil toward his face | He presses the bandaged right stump down onto the glowing plate on the anvil; steam puffs; pain (head back) | 1042–1197 |
| S10 | Next (13–14) | top-down push-in | Two knives and coiled leather straps on the table (no hands) | 1198–1287 |
| S11 | he tied knives to his wrists (14–16) | front medium, logo crate at the side | The knives are already strapped along both forearms (two leather straps each, around forearm + handle, blade past the stump); he lifts both forearms and looks at them; a villager nods beside him | 1288–1443 |
| S12 | and when they went to war (16–18) | dolly back in front of him | He strides toward camera with the blades; two villagers walk behind | 1444–1599 |
| S13 | he cut down (18–19.5) | side profile of both | He winds up and sweeps the right blade across ~15 cm in front of SoldierB's chest; stylised spark on the cuirass; the soldier staggers back (no wound) | 1600–1719 |
| S14 | including the general's second-in-command (19.5–22) | side 3/4 | The officer (brass helmet) advances, sword raised, cuts beside him; he ducks in and sweeps; spark; the officer reels back | 1720–1899 |
| S15 | Eventually (22–23.5) | low, looking up | The invaders' flag (plain white with a red band) waving against the pink dusk sky | 1900–2019 |
| S16 | they were defeated (23.5–25.5) | high side view | The army (15 marchers with spears) advances; the warrior faces them, blades raised | 2020–2175 |
| S17 | they lost, but he fought till the very end (25.5–29) | push-in from the ring gap to his face | Guards with spears stand in a ring around him; he turns, slashes, then stands defiant; hard cut to end | 2176–2415 |

Phase-1 total 2415 frames (40.3 s); the VO will set the real lengths.

## Logo (DA KRAS FILMS)
- White logo on two faces of a wooden supply crate in the meeting hut: seen in **S07** (villagers raise fists) and at
  the side of **S11** (knives). Flat to camera, about 20% of frame width, f/8 equivalent (no DOF).
- Not in S01–S04 (punishment), S09 (sealing) or the defeat beats S15–S17.

## Risky shots: the simplest safe staging
| Risk | Staging |
|---|---|
| Amputation | **not shown.** S01 ends while the sword is still at the shoulder; S02 already shows clean bandaged stumps. No blood, no wound. |
| Stumps | rounded cloth bandages built from the measured cut ring, bone-parented to the forearm (`lowerarm02`), wrist copy-rotation muted so nothing twists. |
| Sealing with hot metal | glowing plate on the anvil; only the bandaged stump end touches its top surface; steam + orange glow; the face shows pain without teeth. |
| Knives on the forearms | knife lies along the outside of each forearm, butt 11 cm up the arm, blade past the stump; two leather straps wrap the convex hull of forearm + bandage + handle (nothing passes through the arm); bone-parented, visible from S11. |
| Battle | impact = spark on the cuirass and a stagger; no blood sprays, no deaths on screen. The blade sweeps in front of the body, never through it. |
| Swords | SoldierA/Second: the sword is keyed and the IK hand follows its grip (wrap grip), so it never floats. Hand at or below shoulder height. |
| Spears | shaft through the closed fist (wrap grip), Child Of the wrist; the army copies inherit it. |
| Crowds | army and guard ring are copies of one master each (shared action), dressed, eye-fixed, not in a camera-facing row. |

## Cameras
One camera per shot (`CAM_Sxx`), Track-To an empty (level horizon), no DOF (everything sharp), each with a small glossy-only catchlight.
First/middle/last frames checked on the P1 sheet for lens blockers and cut framing.
