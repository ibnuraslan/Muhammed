# PrisonKeyCake v011, check 3 (after fix rounds 1 and 2): FAIL, stopped (both fix rounds used)

`review/preview.mp4` is this check: every 5th frame, 270x480, with the VO, frames 1-1836. I watched it start to finish.
Frames below are film frames (60 fps).

## Now reads well
- Real MPFB/MakeHuman garments (director's lesson from 05):
  - prisoner: striped shirt + jeans, later the elegant suit
  - visitor: blouse + skirt
  - locksmith: work overalls
- Wax press with his face in frame and a clear red imprint (1-262).
- The visitor leaves the prison with the basket. The lane has houses, and the DA KRAS FILMS sign is readable (about 385-470), as is the board inside the workshop (700-745).
- The pour into the sand mould (560-610).
- The cake match from workshop to cell (790-810). He pulls the key from the cut cake (850-900).
- The jam at the lock (970-1010). The second impression and the waiting beat (1080-1210). The cake with the key hollow (1226-1246).
- Gate unlock (1420-1446).
- Finale: the black suit, both allies waving on the platform, tricolour flags and a wooden door (1630-1836).

## Remaining faults (not fixed; fix rounds exhausted)
1. **Glows:** the molten stream, the hot key and the candle flame still render peach/cream, not orange (330-346, 565-640).
2. **Locksmith carrying the key:** his hand is 25-117 mm off the key while he carries it to the cake (REACH_ERR 712-748).
3. **Camera blockers and odd angles:**
   - workshop: a white panel, then his arm, fill the frame at 686-696 (camcheck: camera inside the crucible at 691); his torso at 741-766
   - top-down over the prisoner's head at 956-966, 1021-1026 and 1331
   - the open small door in the gate (wicket) panel at 1556-1571
4. **Second key turn:** his fingers come off the key during the 50 deg turn (GRIP_ERR 1306-1320). The key turns with the hand beside it.
5. **Back of head:**
   - leaving the cell, 1366-1411
   - walking out of the prison, 1576-1611 (he glances back only at the end)
6. **Plain-wall frames:** 1046-1056 and 1221.
7. **Ending:** the arm hangs straight in the last frames, and the hold is near-static from about 1800.

## Suggested next step (needs the director's OK)
1. Re-stage the locksmith's key into the cake as a macro with his hand out of frame.
2. Pull the lock macros back so the turn is seen from the side.
3. Replace the two walk-out back views with a leading camera.
4. Glows: emission on a black base (or lower exposure), and check one still.
