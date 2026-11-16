# B13 WomanSuckedOut: Phase 1 plan (ConnectB13)

**Reference:** `briefs/batch2/B13_WomanSuckedOut_reference_1fps.jpg` (31 s, current style). The shot order below follows it frame by frame: interior row → exterior woman at the window → engine → engine breaks → window row → cabin → hold → pulled back → lying → fuselage → damaged engine.

**Format:** 1080×1920, 60 fps, Cycles. Hard cuts: one camera per shot, switched by timeline markers. Every shot is its own 1× clip about 30% longer than the expected beat (17 clips, 2184 frames in total). Phase 2 trims the tails to the VO words. Nothing is time-stretched.

**Sets:**
- **Cabin.** Reused from NoPilotPlane_v011: the 2+2 cabin, the CC-BY "Seat" model and the oxygen-mask drops. The 37 passengers (MPFB, CC0) are re-posed **awake**: upright, breathing, looking around, and after the blast heads up toward the masks. The skin-tight sport-suit variant is removed.
- **The broken window.** A real hole at row 5 left (y −5.58, 0.46 × 0.56 m) cut through the cabin wall, the wall trim and the outer skin, with a liner tunnel and a trim frame. A glass pane sits in it until it breaks.
- **Exterior (new, procedural):**
  - white fuselage with painted dark windows and a grey belly
  - swept wings with winglets
  - two engines, each with a lathe nacelle, an 18-blade fan on a spinning hub, a spinner, a pylon and an exhaust plug
  - a blue tail with stabilizers
  - drifting puffy cloud clusters in a blue sky (the ground plane is hidden)

  The left inlet's inboard arc and one fan blade are separate pieces that break away in S06. The damage stays to S17.

**Characters** (all MPFB, CC0, reused from finished films because the MakeHuman asset server returned 502):
- **W (the victim, generic):** CaveRescue "Crowd3". Charcoal top and grey slacks (recoloured texture), blonde bob, eye fix, eyes closed whenever she is out of the window or lying.
- **HA (the helper):** ShoeBomber "PaxB". Olive jacket and jeans.
- **HB:** BelugaRescue "SpecD". Sweater with the MakeHuman chest emblem painted out. Currently parked off-set (see the open questions).

All three have the eye fix, hand limits and the elbow IK limit opened to −40°. Hands use the `hand_poses` presets.

| Shot | Beat (reference words) | Who / what physically happens | Camera | Clip (f) |
|---|---|---|---|---|
| S01 | In 2018 a woman was… | W in the window seat (row 5L), HA beside her in the aisle seat. W turns her head from the window toward the cabin; HA breathes and shifts. Awake passengers around them. | From the aisle ahead and above, push-in, 30→34 mm | 100 |
| S02 | …sucked out of a window | At f+24 the pane bursts (shards outward, napkins fly to the hole). W is yanked toward the window: body slides, torso folds toward the hole, arms flung up. HA leans away. **Seen from behind, so no distress face.** | Aisle behind and high, slow push | 150 |
| S03 | on a Southwest flight | Exterior, right side: rear fuselage and blue tail with **the DA KRAS FILMS logo**, clouds drifting | Low, looking up, dolly 40 mm f/11 | 120 |
| S04 | headed to Dallas | Exterior: W's upper body out of the window, face down, arms trailing back in the wind (flutter) | Low wide from ahead, 44→48 mm | 120 |
| S05 | It happened when an engine | Left engine front, fan spinning | Low ¾ front push-in | 120 |
| S06 | broke in the air | At f+30 the inboard inlet arc and one blade break away: 10 debris chunks fly back and inboard, grey stylised smoke puffs | Low ¾ front, drift | 100 |
| S07 | causing debris to break a window | Window row: a chunk flies up into the row-5 window, and at f+46 the pane shatters (shards blown out and back) | Low side, push | 150 |
| S08 | the cabin to depressurize | Oxygen masks drop and swing; passengers look up and toward the hole; HA reacts | Aisle wide looking aft, slow push | 120 |
| S09 | and suck the nearby woman out | Exterior: W's upper body slides out through the hole (head first, face down), arms lift into the wind | Low from behind the window | 120 |
| S10 | out of the plane | Interior wide: W's hips at the hole, legs inside over the seats. HA stands in the aisle and holds both her shins | Aisle ahead, high, push | 120 |
| S11 | The other passengers held on to her | Closer on HA holding her legs (both hands on her shins, palms on top) | From the right aisle seats, ahead | 156 |
| S12 | as she hung halfway out | Exterior: W hanging out, arms fluttering in the wind | Slow low orbit ahead of the wing, 55 mm f/11 | 156 |
| S13 | after a few minutes they were able to [get her back] | HA steps back and pulls: her body slides 0.6 m back in through the hole, and his hands follow her shins | Aisle ahead, push | 156 |
| S14 | get her back into the plane | W lies on her back in the aisle, eyes closed, calm. HA kneels at her head, leaning in | Aisle from her feet, high, push | 156 |
| S15 | But she had head trauma | Closer on HA kneeling, worried; W's calm face, eyes closed. No injury shown | Aisle, lower, push | 120 |
| S16 | which unfortunately | Exterior: window row with the broken window, plane flying on | Above the wing looking aft | 100 |
| S17 | caused her death | Exterior: the damaged engine (inlet arc missing, fan windmilling slowly, light smoke). Her death stays off-screen | Low ¾ front push-in | 120 |

## Logo: DA KRAS FILMS
- **One placement:** the white logo on the right side of the blue tail fin, where an airline brand would be. It is flat-on (about 22°), about 33% of the frame width, and on screen for the whole of S03 (2 s).
- It is not visible in any tragic shot: the incident shots are all on the left side, and the fin is thin.
- No real airline name, livery or brand anywhere.

## Risky shots: the simplest safe staging used
| Risk (brief) | Staging |
|---|---|
| Real victim, no face shown in distress | Generic character. S02 is seen from behind. Outside she is face down with her eyes closed. Lying, her face is calm with eyes closed. No injury or blood anywhere. Her death is not shown; the film ends on the engine. |
| Passengers' hands on her (contact, not through bodies) | One helper only. His hands go on top of her shins (`place_hand` palm down, 6 cm skin offset), never near the hips or backside. HB's brace on a seat back was dropped after it read badly. |
| Exterior shot, no gore | Clothed body out of the window, face down, arms in the wind. The broken window is a clean hole with a liner. |
| Oxygen masks fitted on faces | **Not fitted:** the masks drop and dangle, with no hands on them. This avoids a mask that floats off a face (a known client fault). |
| Body through the wall | The hole is sized to her cross-section (hips 0.36 m in 0.56 m). She only moves straight out and in along the hole axis. The seated lurch (S02) stops at the window. |
| Lens blockers | Cameras clear the overhead bins (bin bottom z 1.56) and the wing (S12 and S16 were moved off the wing after the first test). |

## Open questions for the director
1. **HB** is parked off-set: his seat-back brace read as a hand on his head. One helper holds her. Do you want a second passenger holding her too (another hand contact on her legs)?
2. **The victim's hair is blonde** (the only clean female rig with trousers in the repo; MakeHuman assets can't be downloaded today). The reference woman is dark-haired. I can darken the hair texture if you like.
3. **The hold shots (S10, S11, S13)** show HA mostly in profile from behind, because he faces the window. Is that OK, or should I swap to a camera from the window side?
