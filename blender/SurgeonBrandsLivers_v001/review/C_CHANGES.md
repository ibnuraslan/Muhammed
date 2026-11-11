# Checkpoint C — polish (SurgeonBrandsLivers)

Files: `C_polish_0.2s_0-10s.jpg`, `C_polish_0.2s_10-20s.jpg`, `C_polish_0.2s_20-28.5s.jpg` (every 0.2 s, 270×480, 8 spp, no motion blur), `C_audit.txt`.

## What changed since B
**Characters and faces**
- Surgical caps and pleated masks are now fitted to each person's real head mesh (measured from the evaluated body), with ear loops. Surgeon 1's mask is pulled down by his gloved hand onto his chin. Surgeon 2's widening eyes read over her mask.
- Nitrile gloves on every surgeon's and the nurse's hands (a material layer over the skin). Surgeon 1's come off for the hearing.
- Textured eyes replace the procedural eye shader, which rendered as dark holes.
- The smug smile is toned to a closed-mouth smirk with narrowed eyes.
- The patient's legs were deleted under the hidden gown. Clothing delete-modifiers now follow the outfit shown.
- On the table she has an anaesthesia mask, a tube to the cart and a neck towel; this also hides the head-only seam.

**Story beats**
- The studio argon pen now writes on the liver's surface, with the tip on the stroke. Sparks, smoke and the tip glow follow it. Before this they were keyed in the liver's local space.
- The 'B' has a proper waist, and the brand cools to a dark sear with a faint ember.
- The calendar faced the wall. It is turned round now, and the flipped pages leave instead of covering the lens.
- The home x-ray liver sits on her right ribs, in front of the shirt, and pulses blue to red.
- She drops the mug at the first spasm: it falls, bounces and tips. Her hand no longer ends up behind her head when she doubles over.
- The bed bursts through the doors as beat 5 starts (13.0 s), not 0.6 s later.
- The red stamp mark is a framed seal on the licence, and the folder that overlapped it has been moved.
- The ending is now a rise over the stamped licence toward the surgeon at the lectern, with the ghost livers behind him. Before, it was a held push on paper.

**Camera**
- The spline is now a blend of Catmull-Rom and monotone pchip. Catmull-Rom alone overshot after the dives (once by 0.6 m into the ceiling); pchip alone made corners.
- No longer passes through surgeon 1's head (2 s, 5.5 s). The studio macro is lower, so the pen no longer covers the letters. The rise out of the studio starts earlier.
- The 24.2 s whip-pan no longer swings the aim through the lens. A sideways aim key was added.
- More motion at 14 s and 18.5 s. A new framing at 22 s keeps the surgeon in shot.

**Contacts (audit)**
- Hands into desk/lectern went from 3,300 hits to 0. Wrists now sit on the surface and fingers lie flat.
- The camera is inside a body or wall only during the planned dives and fly-throughs.
- The needle-driver hand-off is slower, and the tray moved within reach.
- The patient's stagger step has a lift (no slide).

## Audit summary (every 3rd frame)
See `C_audit.txt`. What remains:
- Gavel and stamp pick-ups: the finger base is 9–12 cm from the grip point for about 20 frames while the hand closes. The wrist is on target.
- Surgeon 2's left foot slides 0.10–0.14 m/s for 2 samples as her walk settles (f994–997).
- The camera is inside geometry only during the planned transits (dives at ~2.2 s / 17.6 s, rises at ~4.7 s / 19.7 s, wall fly-throughs at ~10.6 s, 12.9 s and 20.7 s). Each one is ≤ 0.3 s, and they will be motion-blurred in the farm render.

## Known / unsure
- Transit frames read as a short black or grey "whoosh". With motion blur on the farm they should read as a dive. If you'd rather see a skin-texture wipe, I can add one.
- The patient wears a casual T-shirt with a small abstract print (MakeHuman CC0 asset). There is no text or logo.
