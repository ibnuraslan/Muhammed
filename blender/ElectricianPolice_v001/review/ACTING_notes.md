# ElectricianPolice: acting review of v005 (the approved final)

Sheets:
- `ACTING_before_v005_0.5s_a.jpg` (0–13 s)
- `ACTING_before_v005_0.5s_b.jpg` (13.5–25.5 s)

They are a half-second sheet at 270×480, 8 samples, every 30 frames. Frames are film frames (f = 1 + 60·t). Story-beat frames (beats.json) stay where they are.

| # | Time / frames | Problem | Fix in v006 |
|---|---|---|---|
| 1 | 3.0–4.0 s (f181–241) | The camera sits behind the rider, so the back of his head and shirt fill the frame at 4.0 s. The officer's face and the writing are hidden. | Re-key the camera in front-left of the pair: we see the rider's face in profile, the officer's face and the pad being written on, then the hand-over. |
| 2 | 5.3–6.5 s (f318–392) | At the gate he "holds a key" that doesn't exist: his hand is curled around nothing. He also stands almost frozen. | Add a key ring prop in his right hand (Child Of the wrist). Add weight shifts, a breath and a small nod between the keys. |
| 3 | 6.5–6.8 s (f392–410) | He spins 164° on the spot in 18 frames while his feet stay planted (a root spin). | Two real steps: the left foot lifts and turns, then the right. The body yaws through an in-between key. |
| 4 | 12.0–13.0 s (f720–781) | His face drifts to the frame edge; at 13.0 s only his forehead shows. Beat 6 is about his slow grin. | Aim keys computed from the actual face point (head bone + facing), so the face stays centred while the camera orbits. |
| 5 | 17.5 s (f1051–1057, beat 8 "cut off their power") | A macro of the glove and lever only, so his face is unreadable on the beat. | Reframe to a 3/4 profile showing his face (smirk), his gloved hand on the grip and the lever in one framing. Then the throw. |
| 6 | 22.5 s (f1344–1360) | The camera swings off the sweating officer onto a bare wall and window for about 0.3 s before the clock. | Hold the aim on the officer longer. The swing to the clock starts later, so the wall-only frames are gone. |
| 7 | 23.5 s (f1406–1424) | The slumped officer is framed only for an instant; the aim swings into an empty room corner. | Hold on him through f1416, then turn to the doorway. |
| 8 | 24–26 s (f1381–1560) | "Hands in pockets" aren't in the pockets: they hover at the hip line with curled fingers. | Natural relaxed arm swing for the swagger. Arms hang and swing opposite the feet, with a relaxed curl. |
| 9 | 2.5 s (f151) | Checked: both wrists are exactly on the bike grips (wrist-to-grip 0.03 m). It reads fine at speed. | No change. |
| 10 | 15.5–16.5 s (f925–985) | He is partly off frame while celebrating, but beat 7 (f895) has his face and the bar. | No change. The bar leads the camera, as approved. |

## Found by `clip_scan.py`, then fixed in v006
| # | Frames | Problem | Fix |
|---|---|---|---|
| 11 | 181–193 (3.0–3.2 s) | The officer's waving hand passes close to his chest, and his idle left hand sits inside his hip. | The wave arc moves further out (lateral 0.62/0.44 m, forward 0.48 m) with an outward elbow pole. His left arm hangs 7 cm off his body. |
| 12 | 302–310 (5.1 s) | The hat swings from the seat to his head straight through his chest. | An in-between key swings the hat out wide at shoulder height, then up onto his head. |
| 13 | 397 (6.6 s) | During the new two-step turn, his key hand stays still while his body turns into it. | The hand is keyed at the turn's in-between, so it moves with his body. |
| 14 | 1261–1327 (21–22 s) | The phone officer's idle left hand sits inside his thigh. | It hangs 10 cm further out. |
| 15 | 1339–1399 (22.3–23.3 s) | The sweating officer's idle left hand grazes his thigh. | It hangs 7 cm out. |

## Results (v006)
- `clip_scan.py` comes in two forms:
  - **The director's stock script:** it reads character positions from the armature objects. In this film those sit at the origin, and it only sees characters visible at frame 1, so it scans almost nothing. Its result is in `v006_clip_scan.json`.
  - **The patched copy:** `../scripts/clip_scan_ep.py` uses the root bone position and checks visibility per frame. Its result is in `v006_clip_scan_ep.json`, and it is the one that counts.
- The hand audit (`05_hands.py`, BVH every 2 frames) is in `v006_hand_audit.txt`.
- Hand close-ups: `v006_hand_closeups.jpg`.
- After-sheets: `ACTING_after_v006_0.5s_a.jpg` and `ACTING_after_v006_0.5s_b.jpg`.
- Story-beat frames are unchanged; `beats.json` is identical to v005.
