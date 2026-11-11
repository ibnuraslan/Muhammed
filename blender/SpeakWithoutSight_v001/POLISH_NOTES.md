# Checkpoint C: changes since B

- **Streaks at 0–2 s fixed.** These were glossy reflections of the fill and ceiling area lights in the parquet. Those lights are now hidden from glossy rays, and no light is visible to the camera.
- **No more black frames.** Three lip macros (20–21 s) put the camera inside the girl's head. All teacher-lip and fingertip framings now sit on the open side, the teacher's right.
- **Camera clearance pass.** After the spline is built, every camera key within 1 m of the pair is pushed out to at least 18 cm from either character's skin, clothes or hair, then smoothed. 227 of 661 keys were nudged.
- **Throat contact fixed.** The girl's arm target was out of reach in beats 5–6 (0.62 m from the shoulder), and the fingertip correction then ran away. Now the teacher stays leaning in, the girl leans further towards her, the correction is capped at the arm's reach, and the throat point sits lower on the neck, under the chin.
- **Dense contact keys.** The throat, lips and the girl's own lips and throat are keyed every 6–10 frames, so the hand follows the speaking head instead of drifting between sparse keys.
- **Palm orientation.** The IK hand basis takes the palm normal, so every hand was inverted (fingers curling away from the contact). Fixed globally.
- **Teacher's sleeve.** It no longer fills the foreground (9–14 s): after guiding the girl's hand, her right hand returns to her own thigh.
- **Lip touch.** The fingers now angle slightly down across the lips, so the hand no longer covers the teacher's eyes in low macros.
- **Beat 11 push-in.** It now comes from the front, not through the girl's raised arm.
- **Explainer dome.** Reduced to 1.7 m radius so no wall pierces it, and the dome edge no longer cuts across the frame.
- **Long Victorian skirts dropped.** They ballooned when kneeling. Both women wear the MPFB knee-length suit, which deforms cleanly.

## Director's B notes and the realism pass (applied before C)
- **Costumes (period).** Both women wear long skirts: a measured cone weighted waist to thighs to shins, shrinkwrapped and smoothed over the posed legs, and floor-clamped with a small geometry-nodes group. The body below the waist carries a petticoat/stockings fabric, so a drape gap never shows skin.
- **The girl** is younger and smaller (MPFB age 0.17, child proportions), in a mid-calf dress with braids.
- **Arms.** Every IK hand target is capped at 92% of the rest arm length, so arms are never straight or stretched. The teacher kneels closer, leans in, and keeps her left hand on her own thigh.
- **Throat contact.** The fingers sit on the front of the neck over the larynx, below the jaw. The teacher lifts her chin for this beat, the throat point is raycast with chin hits rejected, and the fingers point away from the girl's shoulder (shortest reach). For the lips the chin comes back down.
- **Skin press.** VertexWeightProximity plus Displace makes a 2.5 mm dent wherever the girl's middle fingertips touch.
- **"Trapped" beat.** It's a lighting vignette: the room fades to 14%, with a soft key on her face. There's no visible sphere.
- **Real anatomy.**
  - X-ray hand: the CC-BY "Hand" skeleton (Team Skeleton Wars), fitted to the wrist, middle fingertip and thumb.
  - X-ray throat: the CC-BY "Larynx" (Vikrama Raghuraman), decimated to 40k vertices, in wet SSS cartilage, ligament and mucosa materials, buzzing with the voice.
  - Warm pulse dots travel along three fingers.
- **Props.** A CC-BY Chesterfield footstool replaces the box stool, and a CC-BY open book (blank pages) replaces the box book.
- **Removed as primitive-looking.** The bubble sphere and a sphere-built hair ribbon.
- **Explainer gradient.** Deeper and more saturated (dark teal to pale cyan), with a 1.7 m dome so no wall cuts through it.
- **Camera.**
  - Every blank or near-blank stretch was re-pathed: 4.2–4.8, 9.4–10.2, 17.4–18.4, 22.4 and 30.4–30.6 s.
  - The clearance pass uses unsigned distance for hair and caps its push at 0.3 m. Before this it threw the camera 3.6 m at frames 250–290, which read as a cut.
  - The audit now reports the largest per-frame camera move.
- **Time-lapse.** Day/night cycles every 0.5 s, the lamp lights at night, the leaves go from green to orange to bare to green, snow comes and goes, the clock spins, and the girl goes from hunched to upright.
