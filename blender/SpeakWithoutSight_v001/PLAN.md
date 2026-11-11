# SpeakWithoutSight — PLAN (Connect19, checkpoint A)

Branch `claude/connect19-speak-without-sight`, folder `blender/SpeakWithoutSight_v001/`.
1080×1920, 60 fps, frames 1–1980 (33.0 s). One camera `CAM_Film` on one Catmull-Rom spline (continuous velocity), aim empty + animated lens, DOF on. No cuts, no markers.

## World
One real set: a late-1800s parlour, 6 × 5 m, papered plaster walls over dark wainscot, herringbone parquet, rug.
Back wall (+Y) has a tall sash window with a tree and garden outside (Poly Haven HDRI + a tree model whose leaf colour is animated for the seasons).
- **Girl** (MPFB, ~10 yrs, 1.26 m, braid, period dress tinted dusty blue) in an armchair at room centre, facing −Y.
- **Teacher** (MPFB, young woman, bun/ponytail, high-collar blouse + long skirt tint) enters from the door at left.
- **Mother** (MPFB) on the sofa at left doing needlework; **Father** (MPFB) by the mantel, reading, turning pages; **dog** (Objaverse CC-BY GLB + `rig_quadruped.py`) at the girl's feet, barks (jaw open, head jerk, ear flap).
- Grandfather clock with swinging pendulum, mantel clock, oil lamp (real flame light, keyed for the time-lapse), tea set, books, picture frames, plants. No text, logos or brands anywhere.

**Explainer look** (beats 5–6, 9 and 11): the parlour dims; a soft **cyan-to-white gradient dome** fades in behind the pair, with studio key/rim lights. The skin on the teacher's throat and on the girl's hand and forearm turns semi-transparent (x-ray porthole). Inside you see a clean larynx (cartilage ring and vocal folds, procedural and non-gory) and a soft nerve line up the forearm. Emissive **pulse dots** run along a curve: larynx → touch point → fingertips → wrist → elbow. Their size, brightness and spacing are keyed per beat.

## Beats (frame = 1 + round(t·60)); camera framing changes about every 60 frames
| # | t (s) / frame | Line | On screen | Camera (one continuous move) |
|---|---|---|---|---|
| 1 | 0.0 / 1 | lost her sight and hearing as a baby | The parlour is alive: the clock pendulum swings, mother sews, father turns a page and laughs, the dog trots in and barks at the girl's feet. The girl sits still, eyes unfocused (pupils drift, no tracking); she doesn't flinch at the bark. | Starts high and wide from the corner behind the father (1) → crane down and drift past the clock (60) → low dolly past the barking dog (120) |
| 2 | 2.7 / 163 | trapped inside her own head | The world dims and desaturates; a dark, soft-edged **bubble** closes around her. Family motion keeps going but fades to near black. Her hands rest on her lap, moving faintly (only touch). | Fast push-in to her face (163) → orbit ¾ (225) → extreme close-up of her unfocused eye (290) → pull back to medium on the bubble (350) |
| 3 | 6.6 / 397 | her teacher placed the girl's hand on her throat | The teacher's hand breaks through the bubble wall (the bubble ripples and dissolves). She kneels (knee planted on the rug), takes the girl's right wrist and guides the hand to her own throat. The fingers settle flat on the skin. | Pull back as the teacher enters frame left (397) → arc to the side, 2-shot at eye level (460) → push to the hands meeting at the throat (530) |
| 4 | 9.9 / 595 | began to speak | The teacher speaks slowly with clear jaw and lip shapes (jaw, oris and risorius bones keyed: "ah", "oo", "ee"). The girl's head tilts towards her. | Low angle up past the girl's hand at the throat to the teacher's mouth (595) → slide across her profile (655) |
| 5 | 11.6 / 697 | The vibrations told her | Explainer look on. X-ray of the throat: the vocal folds buzz, pulse dots flow out of the larynx into the fingertips and up the arm. | Rack/push from the mouth down onto the throat (697) → macro on the fingertips (760) → track up the forearm with the pulses (830) |
| 6 | 14.9 / 895 | how strong or soft it was | The teacher opens wide: pulses become **big, bright and fast**. Then a soft mouth: **small, dim and slow**. The girl's brows lift and her lips part; her fingers press then relax. | Pull to a 2-shot over the pulses (895) → orbit to the girl's face reacting (960) → back to the throat as the pulses soften (1020) |
| 7 | 17.7 / 1063 | moved her fingers to her teacher's lips and nose | Explainer fades to the parlour. The teacher lifts the girl's hand from her throat to her lips; index and middle fingers rest on the lips, the ring finger by the nostril. Fingertips explore (small slides along the lip line, contact kept). | Crane up with the hand (1063) → macro profile of fingertips on lips (1125) → slow orbit around the macro (1190) |
| 8 | 21.0 / 1261 | different shapes… for each word | Teacher forms **O → E → M** (≈ 0.6 s each, repeated). Each shape lights faint cyan **contour lines** (emissive rings that follow the lip bones) under the fingers. | Macro push in on O (1261) → slide to the front for E (1320) → low macro for M (1385) |
| 9 | 24.2 / 1453 | practiced those same movements on her own face | The girl's left hand stays on the teacher's lips; her right hand goes to her own lips, then to her own throat. Her mouth mirrors the O/E/M (a little behind and clumsy). Faint contour lines on her own lips. | Pull back to a symmetrical 2-shot (1453) → swing across to the girl (1520) → close on her mouth and hand (1590) → pull up and out (1660) |
| 10 | 28.7 / 1723 | over and over again | **Time-lapse.** The window cycles summer → autumn → winter → spring (light colour, leaf colour, a snow cap). The oil lamp is lit and unlit, the clock hands spin and the shadows sweep. The girl and teacher repeat the practice in fast bursts; her posture goes from hunched to upright. | Fast orbit 180° around the pair (1723–1843) with the window passing behind them |
| 11 | 30.7 / 1843 | until she was finally able to speak | Her hand on her own throat, she speaks one open word. Warm pulses glow at her throat. The teacher's hands fly to her mouth (a gasp), then she hugs her. The mother stands up from the sofa, the father lowers his book, the dog's tail wags. Settle and hold the breath. | Push into the girl speaking (1843) → pull back and rise on the hug (1900) → slow crane-up settle (1980) |

`beats.json` will hold these 11 start frames for `retime_to_vo.py`.

## Assets (all CC0 unless noted)
- Poly Haven (CC0): ArmChair_01, Sofa_01, vintage_grandfather_clock_01, mantel_clock_01, vintage_oil_lamp, tea_set_01, round_wooden_table_01, vintage_cabinet_01, book_encyclopedia_set_01, wooden_candlestick, WoodenChair_01, hanging_picture_frame_01, potted_plant_01, island_tree_01; textures herringbone_parquet, painted_plaster_wall, dark_wood, fabric_pattern_05, quatrefoil_jacquard_fabric; HDRI belfast_farmhouse 2k.
- MPFB2 / MakeHuman system assets (CC0): the 4 humans, hair, clothes (tinted for period), skins.
- Dog: an Objaverse/Sketchfab CC-BY GLB (chosen from the thumbnail sheet; credited in CREDITS.md). Fallback if no good rigged-able dog: a sleeping dog with only head and tail animation.
- Procedural (ours): room shell, window, larynx, nerve line, pulse dots, contour lines, gradient dome, bubble.

## Trickiest shots and how
1. **Hand on throat / fingers on lips (beats 3, 7–9).** IK hand targets are computed every key from the *teacher's* posed neck and head bones (Child-Of-style world maths, like the goat film's bottle grip). The fingertips get a skin-surface offset by ray-casting the evaluated teacher body. A BVH audit checks finger↔face depth each frame (< 3 mm penetration, < 5 mm gap).
2. **Mouth shapes.** MPFB default rig face bones: `jaw`, `oris01/02/03-07`, `risorius`, `levator`. I'll build O/E/M/AH pose presets once, check them in close-up stills, then key them on a phoneme track.
3. **X-ray porthole.** Mix Shader driven by a world-space sphere mask (an empty parented to the neck or forearm bone) on the body, clothing and hair materials. Pulse dots are instanced spheres on a curve, hooked to bones, with emission strength and scale keyed.
4. **Time-lapse with no cut.** A single orbit; the world, lamp, window, clock and posture are all keyed at high speed. Character repetition is done as fast keyed cycles of the beat-9 poses.
5. **Hug (beat 11).** A gentle shoulder hug from a kneel. The teacher's hands are placed on the girl's back via IK, with targets offset along the girl's ray-cast back normal. Audited for overlap.

## Schedule
B (1 still/s blocking) by 23:00 UTC · C (0.2 s sheets + audit) by 00:30 · D (package in `SpeakWithoutSight_v002/`) by 01:15.
