# PrisonKeyCake: acting review of the approved v005 (half-second sheet `review/before_v005_halfsec.jpg`)

Frames are v005 frames (the same as the beat frames in `beats.json`; story-beat frames are unchanged in v007).

| # | Time | Frames | Problem | Fix in v007 |
|---|---|---|---|---|
| 1 | 0.0 s (beat 1) | 1–30 | The beat opens on his back, so his face isn't readable | First framings moved to the window side: his face over the table as he glances at the door |
| 2 | 0.5–1.0 s | 30–70 | The frame is filled by his shirt, because the key macro sits too close to his chest | Camera clearance pass (see 13) plus the key macro pulled back |
| 3 | 2.5 s | ~151 | The frame is filled by his crotch: the camera swoops through his torso between the face and press framings | The path is routed above and in front of him |
| 4 | 3.0–4.5 s | 181–271 | A pressing hand fills the frame (a blob at 4.5 s) | Wider macro: the key, both fingertip hands and the tin all in frame |
| 5 | 6.5 s | ~391 | The visitor's coat and leg fill the frame at the pocket | Pocket framing pulled back: hip, hand and tin in frame |
| 6 | 9.5 s | ~571 | The ally's back fills the frame | Framing moved to the front-right of the pour |
| 7 | 15.0 s | ~901 | His back fills the frame on the dive to the lock | Clearance pass |
| 8 | 16.5–17.5 s | 991–1051 | His shirt and shoulder fill the frame (slap and slump) | Clearance pass |
| 9 | 19.0–19.5 s | 1141–1171 | His arm, then the top of his head, fill the frame | Clearance pass; he looks up at the window, face readable |
| 10 | 20.5–21.0 s | 1231–1261 | Frozen hunch on the stool, head hanging | Waiting has life: he breathes, rubs his hands, looks up at the window and the candle, shifts weight |
| 11 | 23.0–24.5 s | 1381–1471 | His shirt, his back and the back of his head fill the frame | Clearance pass |
| 12 | 28.0 s (beat 10 start) | 1681 | The beat starts on his back | Camera ahead in the yard looking back at his face as he steps out, then crane up over him |
| 13 | everywhere | — | The camera passes within ~0.2 m of bodies | Per-frame clearance: the camera is pushed out to at least 0.38 m from every body, head and leg bone (0.22 m from hands for macros), smoothed over ±12 frames |
| 14 | 5.6, 6.4–7.1 s | 337–427 | clip_scan: the visitor's hand goes into his hip at the coat pocket | Pocket target moved 4 cm out |
| 15 | 20.8–21.1 s | 1249–1267 | clip_scan: hands sunk into the thighs on the stool | Hands rest on top of the thighs, palms down |
| 16 | 24.0–25.0 s | 1441–1501 | clip_scan: the sleeping guard's hands are inside his thighs | Hands rest on top of the thighs |
| 17 | 17.3–17.7, 25.6–26.2 s | 1039–1063, 1537–1573 | clip_scan: walking hands brush the thighs | The arm swing hangs 3.5 cm wider |
| 18 | 19.4, 21.7, 23.0–23.3 s | 1165, 1303, 1381–1399 | clip_scan: the pocket, the cake and the step to the door | Re-checked after the fixes (see the after scan) |

## qa_check.py (c6240b2) flags left in v007, with reasons
- EMPTY, 97 sampled frames: all are deliberate hand/prop macros. The hands and the prop fill the frame and the character's body is under 15%. Ranges:
  - 307–355: the visitor's hand and the mould at the window;
  - 547–739: the pour, casting and mould top;
  - 769–781: the cake;
  - 865–907: key into the lock;
  - 961: the jam;
  - 1081–1093 and 1171–1225: the second press and the window tin;
  - 1261–1303: the candle and the knife;
  - 1411–1441: the lock turn and door push;
  - 1483–1495: the corridor gates;
  - 1681–1735: the crane over the wall.
  The close-ups sheet shows the hands in contact in each of these.
- FILL 331 (table) and 337 (wall): the move from the press to the window. These are not intended and were not fixed for the 16:20 deadline.
- BACKHEAD:
  - 511 (beat 4): the nearest character is the guard; the acting character, the ally, is facing the camera at the crucible.
  - 367 (beat 3, visitor) and 1057 (beat 7, prisoner): not intended and not fixed for the deadline.
- HOVER, CLAW, FACEPRESS and INSIDE: 0.
