# GoatOwner_v006b: camera whip polish (Connect32)

This is v006 (approved, ede45c6) with one change: the camera turn around f800 (13.3 s), which qa_check CAMJUMP flagged as a 76°-in-one-frame cut, is eased into a whip.

- The camera orientation is slerped with smoothstep from f793 to f807, with the same start and end framings.
- Only frames 794–806 differ from v006: a per-frame camera-matrix comparison across all 2190 frames shows 13 changed.
- Peak turn is 17.4°/frame, under the 20° limit.
- The turn totals 152°, so it needs 14 frames. In the requested 6–8 frames it would break the 20°/frame limit.
- Animation, look, hands and beat frames are untouched.

`GoatOwner_v006b_60fps.blend` is 69 MB: packed, compressed, and a plain git file.

## Files in `review/`
- `whip_f790-812.jpg`: frames 790, 793, 797, 800, 803, 807 and 812 across the whip.
- `qa_check_v006b.json`: **CAMJUMP 0**. The rest is unchanged from v006: BACKHEAD 3, EMPTY 241, INSIDE 3, all accepted as before.

The source is `../GoatOwner_v001/scripts/03_animate.py` (`whip_ease`, after the camera bake). It eases any view-direction change over 20°/frame; in this film that is only f800.
