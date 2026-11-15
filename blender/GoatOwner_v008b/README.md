# GoatOwner_v008b: director notes on v008 (Connect32)

This is v008 (ef5ade2) with the four remaining notes fixed. Beat frames (`beats.json`) are unchanged and no VO was added. The brief requires one continuous camera ("the camera never cuts"), so where the notes offered a cut, the fix is made inside the move.

## 1. Goat passing through the official, f1741–1781
The goat was walking on the ground the whole time. The official in blue walked a path only about 1 m beside it, so the goat passed through him, and from the high camera it read as floating at his hip.
- He now walks wide alongside, 1.7 m or more from the goat at every frame (measured f1700–1905).
- His hand-on-its-back pose is removed.
- The officer with the catch-pole leads the goat with the loop over its neck, and all four hooves stay on the ground.

## 2. Hoist into the truck, f1861–1896
The goat walks up the ramp; it was never lifted. The camera hid the ramp, and the pole officer stayed back at the ramp foot, so the pole came from off-frame.
- From f1775 to f1815 the pole officer moves from the goat's front-left to walk beside the ramp, outside the truck's left side (x −3.0).
- He has both hands on the pole all the way up.
- The camera at f1860–1895 frames the ramp, the goat and the officer together (new tracker `ga`, between the goat and the officer).

## 3. Empty frames, f1906–1916
The fly-over to the sanctuary is shortened from 11 frames to 5 (f1906–1910). It lands at f1911 already framing the rescuer and the goat. This keeps it under the six-frame limit on blank frames, with no cut.

## 4. Goat head near the lens, f661–786
The eye-macro and horn keys (f690 and f740) now frame the whole goat in front, with the owner coming back down the porch steps behind it (tracker `go`). The f790 key is now an absolute position, so the path to it no longer passes through the goat.

## Also fixed after watching the first v008b preview
- **f636–646 were black.** The goat-relative f630 camera key put the camera inside the shed. It is now an absolute position (−2.2, 4.4), and the path stays at x ≥ −2.36, clear of the shed wall at x −2.8.
- **f1915–1924: the camera flew through the goat.** After the 48 m fly-over jump, the camera spline overshot to y 62.3, the goat's position, then swung back. Settle keys at f1910 and f1916 stop the overshoot, and a hold key at f1903 limits the dip before the jump to one frame.

`GoatOwner_v008b_60fps.blend` is 69 MB: packed, compressed, and a plain git file. Packaging reported no problems.

## Files in `review/`
- `preview.mp4` and `pages/p01–p09.jpg`: the moving preview, every 5th frame, rendered from the packaged file itself.
- `qa_check_v008b.json`
