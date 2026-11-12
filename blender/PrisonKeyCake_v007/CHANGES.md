# PrisonKeyCake v007: acting pass (from approved v005, no VO)

The story-beat frames are unchanged (beats.json). There are no new extras.

## Camera
- Per-frame clearance from the posed skeletons: at least 0.38 m from body, head and leg bones and 0.22 m from hand bones, smoothed over ±12 frames, clipped against walls.
- At least 0.15 m from any prop surface. It threads the cell-window bars on their centre line.
- Beat 1 now opens on his face from the window side (it was his back).
- The 2.5 s swoop now goes over and in front of him; the press macro is wider; the pocket framing is pulled back; the ally's pour is framed from the front-right.
- Beat 10: the camera is ahead in the yard looking back at his face, then cranes up.

## Acting and hands
- Stool wait: looks to the candle, then the door, then up at the window (no frozen hunch). Seated hands rest on the thighs (guard too), not sunk into them.
- The visitor's mould goes out to his side and into the pocket, not through his belly.
- The door slap and lean: the hand stays on the wall above and beside his head. The lean moves away from the lock hand. The jammed key is pulled out to his side.
- Hanging and walking hands are wider, so the fingertips stay off the thighs. The key carry to the lock arcs ahead of him.
- Every prop grip eases on and off over 10 frames. There are no single-frame hand jumps:
  - grip-to-grip hand-offs: knife → key, cake → lid, shank → mould top;
  - the parcel box settles into the guard's carry.
- The mould waits in the tin until the hand arrives and lifts on his right. The knife lifts to his right, away from the slice hand.
- Keyed hand motion is speed-limited (0.07 m per frame, body-relative).

## Checks (on work/film_v7.blend)
- audit_camera every frame: 0 bad frames (v005: 11).
- clip_scan.py: 0 bad ranges (v005: 11 ranges).
- audit_hands step 2: 0 flagged frames (v005: 8).
- qa_check.py (c6240b2), step 6: HOVER 0, CLAW 0, FACEPRESS 0, INSIDE 0. Still flagged:
  - EMPTY 97 on the hand/prop macro shots: the pour, the casting, the cake, the press, the lock;
  - FILL 2 (frames 331 and 337);
  - BACKHEAD 3 (frames 367, 511 and 1057).
