# B03 WeepingStatue — Phase 1 plan (no VO yet)

Reference: `briefs/batch2/B03_WeepingStatue_reference_1fps.jpg` (33 s). We match its shot order, subjects and framing,
rebuilt in our look (bright clean 3D, AgX Punchy, clear sky). **Changes from the reference, on purpose:**
- The reference paints **red streaks** on the statue's feet. We use **clear water drips only** (no blood look).
- The reference's **yellow highlight ellipse** over the pipe is a 2D overlay; we drop it (no graphics) and use a push-in instead.
- The reference prints its logo on the man's bag; we put **DA KRAS FILMS** on the trolley case (see Logo).
- Generic characters only (no likeness of the real investigator). The real church is not named or copied.

Timing below is the reference's (s). Real frames come from the client's VO in Phase 2. Every clip is animated about 30% longer
than its slot so it can be trimmed, never stretched. Hard cuts only.

Cast: **Woman** (devotee, green saree-coloured dress + dark hair), **Investigator** (blue blazer, white shirt, dark trousers, beard),
**Caretaker** (grey-blue kurta-style long shirt), **Crowd** 10–12 people in clearly non-skin solid colours.

| # | Beat (ref VO) | Shot (ref s) | Who / action | Camera | Risk → safe staging |
|---|---|---|---|---|---|
| 1 | "A statue of Jesus started weeping holy water" | S01 0–2.2 macro feet | White marble feet nailed to concrete cross; a clear drop swells at the toes, runs and falls | Front macro, slow push-in + slight drift down, f/11 | Water only, no red. Drops keyed (not Scene Time). |
| 1 | "holy water / from its feet" | S02 2.2–3.4 low feet | Second drop falls off the toes into the wet patch below | Low angle up at feet, tilt with the drop, f/8 | — |
| 1 | "in 2012" | S03 3.4–5.2 statue full | Whole statue on the big concrete cross on the courtyard wall, sky above | Front, slow pull-out/crane-down | Respectful, statue upright, no roll |
| 2 | "Now no one knew where the water was coming from" | S04 5.2–7.4 crowd wide | 10–12 people gather at the wall, look up, two point at the feet, heads turn | High over the crowd's shoulders toward the cross, slow push | Pointing arms kept outside other bodies; crowd spaced ≥0.6 m |
| 2 | "and assumed" | S05 7.4–9.2 crowd 3/4 | Crowd murmurs, some cross arms, one woman lifts hands to chest | 3/4 side, crowd faces visible, statue top of frame | Hands-to-chest: palms 2 cm off clothes |
| 2 | "it was a miracle" | S06 9.2–11.4 Woman CU | Woman looks up at the statue, small smile, head tilt, breath | Low-ish CU, sky + cross pillar behind, f/8 | Eye fix + catchlight; fringe parted |
| 3 | "Crowds gathered the water" | S07 11.4–13.2 cup | A white cup stands on the plinth under the feet; drops fall into it and it fills (no hand: two grip attempts failed the contact check) | Low 3/4 on the plinth, feet at the top of frame | No hand contact |
| 3 | "and touching the weeping statue" | S08 13.2–15.4 touch | A man reaches up and lays his fingertips on the statue's foot; others watch / one reaches but stops short | From behind/side of crowd toward the cross, as ref | Fingertips ON the surface (place_hand, 1 cm skin), never through; only one hand contact |
| 4 | "But a man discovered" | S09 15.4–17.2 bathroom wide | Investigator (blue blazer) and Caretaker stand in a small tiled bathroom beside the toilet; damp stain on the wall | Wide from the door, both full-body, faces 3/4 | Arms relaxed, feet planted |
| 4 | "from the bathroom" | S10 17.2–18.6 point | Investigator turns and points at the pipe on the wall; Caretaker turns his head | Medium side | `point` preset; arm clear of Caretaker |
| 4 | "caused a drain" | S11 18.6–19.6 drain | Floor drain/pipe joint overflowing (water spreading) | Macro f/8 on the joint, push | — |
| 4 | "to overflow" | S12 19.6–21.6 pipe | Leaking joint on the horizontal pipe, water seeping into the wall, dark damp streak below | Medium-close on the pipe, slow push-in (replaces the ref's yellow ring) | No overlay graphics |
| 4 | "collected on the wall" | S13 21.6–24.0 streak | Camera tilts down the wet green-dark streak, water trickle runs down | Tilt-down along wall, f/8 | Background never empty: tiles + pipe in frame |
| 4 | "causing the water to leak" | S14 24.0–26.0 leak | Trickle reaches the bottom; cut-in to statue feet dripping (link the two) | Low on the streak, then (cut) S01 angle | — |
| 5 | "Angered by his findings" | S15 26.0–27.6 crowd glare | Investigator stands in front of the crowd at the cross wall; crowd behind with crossed arms, frowns | Medium, he's in front, crowd + cross behind | Generic faces, no hostile gestures beyond frowning/crossed arms |
| 5 | "religious groups accused him" | S16 27.6–29.4 | Two crowd men point at him; he lowers his head | Reverse 3/4 | Pointing arms not crossing anyone |
| 5 | "of blasphemy" | S17 29.4–31.0 CU | Investigator CU, eyes down, sigh, one hand on the trolley-case handle | CU like ref, case top in frame | Handle = wrap_grip on the telescopic handle, Child Of not needed (case is static until S18) |
| 5 | "causing him to flee the country" | S18 31.0–33.5 leave | He turns and walks off pulling the case; crowd stays behind | Behind/side, follows him | Case Child Of the hand at the handle bar; wheels on ground |

## Logo (DA KRAS FILMS)
- **1 placement:** white logo decal on the side of the dark trolley case, S17–S18 (flat to camera in S18 for ≥1 s, ≥15% frame width, f/8).
  This mirrors the reference (its logo is on the bag). **Unsure:** it is the "he flees" beat; it is not a death/victim/funeral
  moment, but I'd like the director's OK. Fallback: logo on a parked van in the S04 courtyard wide.

## Sets
- **Courtyard:** weathered concrete wall (Poly Haven concrete_wall_008, softened), tall concrete cross mounted on it with the
  white marble corpus (CC0 scan "Crucified Christ", recoloured white), paving, trees behind (Poly Haven jacaranda/island tree), clear sky.
- **Bathroom:** small room, white long tiles to dado height, plaster above (worn_mossy_plasterwall for the damp patch, softened),
  floor tiles, toilet (CC-BY HippoStance), horizontal drain pipe with a joint (Poly Haven modular_pipes_plastic_01 / CC-BY PVC pipe), door.

## Props
Cup (white ceramic, built), trolley case (CC-BY The Motion Tree, recoloured dark grey, its printed mark removed), water drops/trickle (keyed).

## Phase 1 status (built)
- Build chain (all in `scripts/`): `01_chars.py` → `02_sets.py` → `03_statue.py` → `04_anim.py -- shots.json out.blend`.
  `shots_phase1.json` holds provisional blocks (reference timing × 1.3, 2613 frames). In Phase 2 the same `04_anim.py`
  runs with VO-derived blocks (each clip built at 1×, trimmed, never stretched). The camera is one object that jumps at the cuts (hard cuts).
- **Cast source:** the MakeHuman asset server (files.makehumancommunity.org) returns 502 from the cloud, so MPFB clothes/hair
  can't be installed. The cast reuses MPFB characters from our own delivered packages (PopeShot_v012, Tsunami2004_v012),
  stripped and re-rigged, eye fix on every EnhancedEye group, camera catchlight, elbow IK limit opened to −40°.
  Printed T-shirt emblems are flat-recoloured (Woman: green; Caretaker role = CrowdM5 in green overalls).
- **Statue:** the CC0/CC-BY crucifix scans have crude stump feet (bad for the opening macro), so the statue is an MPFB body
  posed on the cross in white marble with a fitted draped loincloth; feet hang toes-down with real toes (matches ref S01).
- Investigator: black elegant suit recoloured to a royal-blue blazer above the hips, white shirt kept, dark trousers.

## Unsure / for the director
1. Logo on the trolley case in S15–S18 (the "flees" beat), as in the reference. OK, or move it to a courtyard prop?
2. The statue has short marble hair, no beard (MPFB). Reads as a crucifix statue; say if you want long hair.
3. S13/S14 trickle is a glossy ribbon; S11 drain overflow is a dark spreading wet patch with bubbles (no overlay ring).
4. Woman's outfit is a green dress/top (no saree asset available).

## Known to check in Phase 2
- S18 first frames: his left arm swings near a crowd member at the edge; check with clip_scan / limb_check.
- Drops (S01/S02/S12) are small: verify they read in the moving preview.

## P1b (director notes, Nov 15)
- Statue: shoulder-length marble hair + short sculpted beard (no likeness, no damage).
- Contacts: S07 re-staged without a hand (cup on the plinth fills from the drips). S08 palm on the flat wet stone of the cross under the feet.
  Idle arms hang wider (women +4 cm, CrowdM4 +6 cm); S18 trailing hand further out.
- Checks on the final file (`review/`): body_prop_cross (13 props: cross beam/bar, plinth, wall, statue body + loincloth, cup, trolley,
  pipe runs + joint, floor drain, toilet; all 11 cast rigs, every 3rd frame) = **0 visible crossings**; statue rig vs its cross = 0.
  clip_scan: one range 1039–1045 (S08, CrowdM4 reaching in past the statue's leg, no prop crossing). limb_check: remaining ARMBODY hits are the
  known shoulder-root false positives (2–3 pts at upperarm01), statue ARMBACK = arms along the crossbar (intended).
