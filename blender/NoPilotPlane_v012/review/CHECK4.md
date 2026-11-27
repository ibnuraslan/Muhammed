# v012 check 4 (after the director-approved round 3)
`review/preview.mp4` at commit bdc824e is the check 4 preview of the packaged file (270x480, every 5th frame, VO).

**Verdict: FAIL.** A fresh reviewer graded all 29 time-stamped pages, and I confirmed its severe items in the frames. No .blend is pushed.

## Round 3 items, as they read in motion
- Mic: in his fist at his mouth (f1091–1226). OK.
- Altimeter: lit panel top → dial → back. About 1 s with no person, no under-panel dark frames. The reviewer rates it borderline (the panel fills the frame for about 0.2 s on the way in and out).
- Stand-up: no cut-like swing. OK.
- Dive: the tilted ground reads through the windscreen. OK.
- Throttle: fist on the knob, bigger lever travel. OK.

## Render time (the package settings now in `scripts/03_package.py`)
Full-res 1080x1920 test frames, 4-core CPU, no GPU, at 14 adaptive samples + OIDN with short light paths:
- f20: 112 s
- f1160: 76 s
- f2880: 73 s

All three are at or under 120 s. The earlier 64-sample settings took 516, 312 and 281 s. The 16-sample frame matched the 64-sample frame by eye; 14 was not compared separately.

## Severe faults that remain (confirmed), with the fix I propose
| Frames | Fault | Fix |
|---|---|---|
| 1240–1280 | Lowering the mic, his left hand and the mic sink behind or into the left yoke horn | Lower the mic to his left side, outboard of the yoke (side 0.20, forward 0.08), not down in front of him |
| 1717–1831 | The dive: his hands hover open near the yoke and clasp in mid-air (f1816) before he grabs at f1832 | Grab at f1780 (the dive peak); hands in "brace" on the armrests before that |
| 3036–3096 | The look-back pans about 150° through the aisle, which reads as a jump | Hold FC with a wide lens (16 mm) on the midpoint of him and the FO: a ~30° pan, no aisle |

## Minor
- f2281–2455: near-static framing for about 2.8 s → add an orbit key at f2370.
- f1541–1556: top-down as he drops into the seat, arms flung wide → lower camera, hands out 0.16.
- f1–115: logo cropped at the left edge (fully readable at f481–630).
