# Part 1 storyboard v2 — notes for the hub

* 54 shots, 2:38. The VO split across shots is the script verbatim (checked word for word).
* Frames: real Cycles renders at half res and low samples, with card and Courier Prime caption burned in as they will play.
* Shared library: `claude/mary-celeste-3d` @ 9499317 merged (final Deveau, Sketchfab boots, `clipcheck.py`). The lib is
  used unchanged.
* **Clipping: `lib/clipcheck.py` ran on every character shot (run.py). All 26 character shots report 0 clips.**
  See `review/clip/CLIPCHECK.txt`; the per-shot JSON is in `review/clip/`.

## Your 9 fixes
1. S16: no mannequins. S16 is the empty forecastle (seven berths, a sea chest at each, blankets thrown back). The new
   S16b ("on the Mary Celeste.") shows the little girl's rag doll on the captain's sea chest.
2. Face close-ups reframed. S07 is over the shoulder, his face turned away into the lantern light. S42 is from behind,
   looking up at her rig. S48 is over the shoulder onto the slate. I also reframed S21 (over the helmsman's shoulder),
   S23 (Morehouse in profile) and S38 (side-on, chest down).
3. S05/S06 bedding: the shared look-frame (b) recipe. Dark varnished panelling with lamp soot, a grey-brown wool blanket
   over a striped straw tick, matte, dark wet patches, a shallower child-sized hollow.
4. S12: the empty chocks with the canvas gripes lying slack and cut, frayed ends, and Deveau looking down at them. No ghost.
5. S38: the chalked sounding rod in Deveau's hands, wet and dark up to the 3½ ft mark, with a small burned-in "3½ FT".
   S39: realistic dark sea-green bilge water, no glow.
6. Maps (S43, S51–S53): P4's chart table (`terrain.py` copied unchanged, same AZORES bbox as P4). Real relief and
   bathymetry, brass pins with red heads, pencilled course, cream chart lettering, filled soft orange bands.
7. Galley (S34–S36): dark sooty planking. The "Star 6" cast-iron stove (Sketchfab CC-BY) stands askew off its hearth,
   its pipe torn down. The water is dark and rippled, with a bucket, spoon, rag, wood chips and straw afloat. In the
   final render the ripples move and the debris bobs.
8. S27: the shared brigantine in her as-found state, with torn topsails.
9. S14: real boarding. One man is in through the gap with a hand on the main shroud. The second is coming up from the
   boat with his hands on the deck edge. Deveau turns and reaches down to him.

## For the 3D chat (shared-lib bug)
* `deveau._shell`: Solidify `use_even_offset=True` throws one jacket vertex ~20 m away in strongly bent poses (seen
  in the cabin lantern pose: a sliver triangle). My shots switch even offset off on the clothes shells (`no_spikes`),
  which fixes it. Worth fixing in the lib.

## Still open
* Card photos: placeholders until the hub supplies them.
* Final render budget: your decision. The animation pipeline is ready and runs clipcheck on frames 1/mid/last before
  rendering.

## v3 (hub's last four fixes)
1. S39: the glowing X-ray is gone. I tried P4's dim cutaway, but its hold floor sits right at the 3½ ft bilge level, so
   the water can't read honestly. "The hull looks in good shape" is now a low shot along her sound black topsides from
   the sea. S38: the floating "3½ FT" label is removed; only the burned-in VO caption carries the number. Deveau holds
   the chalked rod up in one fist (no open hand).
2. S16b: a recognisable 1870s rag doll lying askew on the sea chest: a muslin head with stitched bead eyes, brows,
   a red mouth and rubbed cheeks, yarn hair, muslin arms and legs, a calico dress with a pinafore, black cloth boots.
3. S43/S51/S53: the chart highlights are now filled soft orange glows (a disc with a gradient fill fading to nothing
   at its rim), not line rings.
4. S24: both fists close on spokes within reach. The animated wheel turn uses the same grip points.
Clipping: still 0 on every character shot.
