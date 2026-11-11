# PrisonKeyCake — PLAN (checkpoint A)

1080×1920, 60 fps, frame_end 1890 (31.5 s). Our script (98 words). One camera `CAM_Film` on one continuous spline; no cuts, no markers.

## World layout (one connected set so the camera never has to cut)
Everything sits on one ground plane, laid out along +Y:

```
 [ government steps, day ]   <- beyond the north prison wall (revealed by a crane over the wall)
 ======== north wall ========
 [ night/day prison yard ]--[ gate arch ]--> [ town workshop (foundry) ]
 [ corridor with 3 barred gates ] -> yard
 [ cell: bunk, table+candle, barred window to yard, iron door + box lock ]
```
- The **cell window** looks onto the yard (camera flies through the bars, beat 2→3).
- The **gate arch** is a dark stone tunnel; the camera passes through it to the workshop (3→4) and back with the cake box (5→6).
- The **cell door** opens into the corridor (gates, beat 9), which ends in the yard; the **north wall** hides the government building until the crane-up (10).
- Time of day is keyed: dusk (1–5) → night (6–9) → bright overcast day (10). Changes happen while the camera is inside a tunnel/sky move.

## Beat table (frames = 1 + t·60)
| # | t (s) | frame | Line | On screen | Camera (one framing ≈ 1 s) |
|---|---|---|---|---|---|
| 1 | 0.0 | 1 | "He got hold of the prison's master key and pressed it into melted candle wax," | Cell by candlelight. Prisoner (young, generic) hunched at a table, glance at the door, then both hands press the ornate iron key into a pool of wax in a tin lid beside a guttering candle. Flame flickers, wax drips, rat? no — moth around the flame, guard shadow passes the door grille. | 0.0 high over-shoulder push-in → 1.0 low across-table past the candle → 2.0 orbit round to his face (tense, eyes to door) → 3.0 drop to hands pressing, key sinks |
| 2 | 4.3 | 259 | "making a perfect impression." | Macro: key lifts out, crisp key-shaped imprint left, wax surface turns from glossy-wet to matte as it sets. | 4.3 macro rack focus key→imprint, 5.3 top-down slow spin over the imprint |
| 3 | 6.1 | 367 | "The mold was smuggled out of the prison," | Mold (in tin) slides into a visitor's coat pocket (hand-off at the door grille); camera rises and flies through the barred window; visitor walks across the yard (guard at the wall, crows, laundry, lantern) to the gate. | 6.1 pocket close-up, 6.9 rise + fly through window bars, 7.7 tracking dolly beside the visitor |
| 4 | 8.5 | 511 | "and his allies used it to cast a metal copy." | Through the gate arch into a town foundry: ally tips a glowing crucible into a sand mould; sparks, glow, smoke; mould opens, key shape cooling red→grey. | 8.5 fly through the dark arch, 9.5 low dolly under the crucible, 10.5 push in to the cooling key |
| 5 | 11.4 | 685 | "They hid the key inside a cake and sent it back to him." | Key pushed into a fruit cake on the bench, cake into a box, lid on, box carried back through the gate and handed to a guard. | 11.4 over-the-shoulder down on cake, 12.4 crane up following the box, 13.4 whip along to the gate |
| 6 | 14.5 | 871 | "But when he tried the key, it didn't fit." | Night. Cell door: his hand pushes the copy into the big box lock, strains, it jams, wrist twists, won't turn; he slaps the door, slumps against it. | 14.5 macro on keyhole, 15.5 pull back to his face (frustration), 16.5 low wide of the slump |
| 7 | 17.6 | 1057 | "So he sent out another wax impression and waited for the next cake." | Candle, wax, key again (repeat press). Time-lapse: candle burns from tall to stub, wax pool spreads, moonlight patch slides across floor, tally marks? (no text — just scratches), he paces/sits. | 17.6 orbit at table, 18.6 slow push past him, 19.6 moonlight patch across floor, 20.6 low angle of the candle stub |
| 8 | 21.7 | 1303 | "And this time, the key worked." | New cake on the table; knife cuts it open, he pulls the key out of the crumb, crosses to the door, key in lock — clunk, it turns, bolt slides. | 21.7 top-down on the cake cut, 22.7 whip-follow to the door, 23.3 macro on the lock as the bolt slides |
| 9 | 23.8 | 1429 | "He passed through every locked gate and simply walked out of the prison." | Door swings, he walks the corridor; three barred gates swing open one after another, sleeping guard on a stool, out into the night yard and through the open gate. | 23.8 steadicam behind him, 24.8 pass between gate bars, 25.8 orbit as gate 3 opens, 26.8 low wide out in the yard |
| 10 | 28.0 | 1681 | "Years later, he became president of Ireland." | Crane up over the north wall; reveal (day) an older him (grey, suit, generic face) on government building steps, green-white-orange flags waving, crowd cheering, hats waving, birds. | 28.0 crane-up into the sky, 29.0 tilt down over the wall to the steps, 30.0 push toward him, 31.0 settle with a slight orbit (end) |

`beats.json` will hold these frames; the director retimes with `pipeline/retime_to_vo.py` when the VO arrives.

## Characters (MPFB2, MakeHuman CC0)
- **Prisoner** (young adult male, generic face, short hair, grey worksuit as prison garb). Rig + IK control rig from `pipeline/anim_lib.py`.
- **Older him** (beat 10): same build, old skin, grey hair, dark elegant suit. Generic face.
- **Visitor / ally** (coat, fedora). Reused as the foundry worker.
- **Guard** (worksuit tinted navy + fedora_cocked as cap) — background in yard, dozing in corridor, receiving the box.
- **Crowd** (beat 10): 8–12 duplicates of 3 phenotype variants with keyed idle/cheer/arm-wave, low subdiv.

## Assets (all CC0 unless stated)
| Asset | Source |
|---|---|
| large_iron_gate, large_castle_door (cell door), carrot_cake (retinted to fruit cake), brass_candleholders, WoodenTable_01, old_bed_frame, wooden stool, Lantern_01, cardboard_box_01 (re-textured as wooden box) | Poly Haven models |
| castle_brick_01, stone_wall / old_stone_wall, cobblestone_floor_01, rusty_metal, wood_planks, sand_01 (mould sand) | Poly Haven textures |
| night sky + overcast day HDRI (2K) | Poly Haven |
| Ornate key, wax pool + imprint (shape key), candle + flame, crucible, sand mould, lock box, bars, flags (cloth-like wave via keyed displacement, no sim), corridor, government portico | built procedurally in our scripts |
| Any CC-BY extras (e.g. crows) | Objaverse via `find_models.py`, credited in CREDITS.md |

No text, logos or brand marks anywhere; flags are plain tricolour.

## Trickiest shots and how
1. **Key press into wax + imprint (1–2):** wax pool is a subdivided disc with a shape key that is the key's footprint (boolean-baked once); key is parented to the right hand's IK target while pressed, both hands visibly hold it (finger curls keyed). Wax material animates gloss→matte.
2. **Window fly-through (2→3):** camera spline passes between two bars; clip_start 0.03; audit checks the camera never enters a wall.
3. **Foundry pour (4):** procedural: emissive "metal stream" curve with growing bevel, keyed spark spheres with motion blur, glow point light, light volume puff (small domain only). Key cooling = emission keyed red→off.
4. **Lock jam vs. turn (6, 8):** box-lock with a rotating key + bolt; jam = small back-and-forth rotation, hand strain, door rattle; success = 90° turn, bolt slides, door swings.
5. **Gates opening in sequence (9):** three gate instances with hinge rotations staggered 0.6 s; he walks with planted feet (`Human.walk`).
6. **Night→day crane over the wall (9→10):** world strength / sun keyed while the camera looks at sky; government steps set beyond the wall, crowd with keyed loops.
7. **Hands/feet contact:** custom audit (feet vs ground, hand-to-prop distance during grasps, camera-inside-mesh).

## Schedule
A 19:35 · B 21:45 (1 still/s) · C 23:45 (0.2 s sheets + audit) · D 01:00 package in `blender/PrisonKeyCake_v002/`.
