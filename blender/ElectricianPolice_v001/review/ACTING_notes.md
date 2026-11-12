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

# v007: the director's review of v006 (hands and frames with no subject)

## Hands
The old `fingers()` turned all the finger bones about one shared palm axis, and that gave twisted claws. v007 bends each finger joint about the bone's own local X axis, so it works like a hinge. The sign is measured per bone. The distal joint is weighted 0.75, and the curl is capped at 85°. That stays inside the Limit Rotation rules in STYLE_ANIMATED.md: no backward bends and no spread, so the fingers stay together. The thumb tucks toward the palm and opposes it.

| Shot | Grip in v007 |
|---|---|
| Handlebars (0–2.5 s) | All four fingers wrap the grip (72°). The thumb sits under it, opposed (50°). The wrist is straight. |
| Card (2.0 s, both) | A pinch: index and middle are lightly curled, ring and pinky curled in, the thumb opposed onto the card. |
| Board (3–4 s) | The officer's left hand curls over the board's top edge, with the thumb on the front. |
| 8.0 s raised hand | Relaxed (20°), the fingers loosely curved and together. |
| Hat on and off (5 s) | The fingertips are on the brim, with the thumb under it. |
| 10–11 s fanning and tap file | A light pinch (24–52°) with the thumb opposed. It is no longer a clenched claw over the head. |
| 12 s phone | The palm is under the phone and the fingers are on its back. The thumb tucks onto the front edge. |
| 13–15 s idle hands | They hang beside the leg, 27 cm out to the side, with the fingers gently curled (22°) and the thumb relaxed. |

### Contact: the hands touch what they hold (director's self-check, 14:40 UTC)
- **Grip solver** (`grip_fix` in `03_animate.py`): after the fist is posed, it measures the centre of the curled fist's hole (the finger joints) and moves the hand's IK target so the object runs through it. This covers the bike grips (1–250) and the lever (1044–1088); the residual error is 1.5 cm or less.
  - The bike grip target had been 4 cm past the real bar end, so the left hand gripped air. It now sits on the measured grip (bar tip at ±0.253 m, grip centre at ±0.205 m).
- **Pinch placement** (`pinch_frame` in `03b_fx_camera.py`): flat props now sit with their edge in the actual pinch between the thumb tip and the index (or middle) tip, measured on the posed hand. This covers:
  - the ticket slip (officer, then rider)
  - the board (fingers over its top edge, thumb on the front)
  - the fanning papers and the tapped file
  - the phone (thumb on the front, fingers on the back)
- After the hand-over, the officer's hand opens (relaxed) instead of pinching air.
- **Close-up camera** (`hand_closeups.py`): it aims at the centre of the hand, not the wrist. It tries several directions and takes the first with a clear ray-cast to the hand, then adds a small review-only fill light so dark sets read. Two shots moved to a frame where the hand is holding: the officer at 268 (holding the slip) and the key hand at 360 (key ring in the fist).

## Frames with no subject
| Time | v006 | v007 |
|---|---|---|
| 7.5–9.0 s (f451–541) | The camera craned up the pylon with no one in frame. | It follows him low from behind as he walks through the yard. He then stops at the line and looks up at the pylon, which is above him in the frame. He stays in frame to f538, then the camera whips to the office. |
| 10.5–11.5 s, 13.5 s | The screen filled the frame. | The camera pulls back, so his head, shoulder and hands at the keyboard are in frame with the screen. |
| 19.1–20.0 s (f1146–1201) | It flew over an empty rooftop. | It leaves through the office door at street level. A pedestrian walks up the street toward the dark station, and the camera follows him into the station shot. The path was checked with ray casts for walls. |

The beat frames are unchanged and beats.json is identical. Everything kept from v006 is unchanged: the 3–4 s framings, the key ring, the two-step turn, the brow wipe and the final stroll.

## v007: shared hand library and the QA gate (director, 14:40–15:40 UTC)
- **Hand library:** every finger pose now comes from `../pipeline/hand_poses.py` (`apply_pose`), with the library's joint limits (`add_hand_limits`). There are no hand-set finger angles; the legacy curl numbers map to the nearest library pose. The explicit poses are:
  - **pinch:** the card, the papers, the tapped file, the writing hand, the phone and the hat brim
  - **hold_flat_object:** the board
  - **wrap_grip:** the grips and the lever
  - **relaxed:** idle hands
- **Contact solvers:**
  - `grip_fix`: the object runs through the fist.
  - `touch_fix`: the fingertips rest on the surface. This covers the writing hand on the pad and the fingers on the hat brim.
  - `snap_W`: the nearest fingertip sits on the prop. This covers the slip, the board, the papers, the file, the phone and the key ring.
  - Hidden props (the slip before 261 and after 345, the key ring after 430) are parked off-set, so they don't float beside a hand.
- **Re-staged for QA:**

  | Frames | Change |
  |---|---|
  | 169 (beat 2) | Rider and officer side-on; no back of head. |
  | 330 | A quick whip onto the worker at the gate. |
  | 430 | Him low in frame at the gate. |
  | 600–805 | The office camera at his side: face, hands and screen together. |
  | 619 (beat 6) | Profile, no back of head. |
  | 925–960 | The celebration framed at his chest and head. |
  | 1004–1016 | Hold on him at the desk, then a whip to the cabinet. The switch between his two rigs happens off screen (ManW ends at 1012). |
  | 1075, 1100 | The lever with his face. |
  | 1215 | The station with the pedestrian. |
  | 1232 (beat 10) | Through the window onto the fanning officer. |
  | 1334 | A wide shot of two officers. |
  | 1370–1381 (beat 11) | The sweating officer instead of a bare clock. |
  | 1424–1440 | Out through the real doorway onto the final stroll; no black frames. |
- **DustHaze:** a render-only fog volume. It is excluded from the viewport depsgraph (`hide_viewport`) so that scene ray casts don't treat it as a wall. It still renders, because `hide_render` stays False.

### qa_check.py flags kept as intended (reasons)
| Frames | Flag | Reason |
|---|---|---|
| 1–13 | EMPTY (rider 7–9 %) | The opening establishing shot: the rider rides toward the camera along the street and is clearly in frame. |
| 487–529, 1147–1171 | EMPTY, INSIDE, FILL Fence_8_* | The subject is seen through a chain-link fence: the worker at the substation line, and the pedestrian on the street. The fence is a see-through alpha-mapped mesh, but the QA ray cast treats it as opaque. The renders show the character clearly. |
| 547–565 | EMPTY | A 0.2 s whip pan from the substation to the office in the one continuous camera. |
| 607–817 (some) | EMPTY (character 10–14 %) | The office: his face and hands share the frame with the laptop screen, which must stay readable (beats 5–7). |
| 937, 1087–1093 | EMPTY (7–9 %) | Short pull-backs between close framings. He is in frame. |
| 1093 | HOVER LeverGrip | The hand opening off the lever, 5 frames after the throw. |
| 1099 | HOVER Spark_* | Sparks fly past his hands. |

## v007 rev 2: the director's review of 3dddeab (16:11 UTC)
| Note | Fix |
|---|---|
| 9 clip ranges | **Cause:** the library's wrist cone (±25° side) clamped hanging hands, so the palm turned into the thigh. Muting it moved the fingertips 12–14 cm. **Fix:** keep the library's finger and thumb limits, and use the v006 wrist limit (±60° flex, ±35° side, ±50° twist, per STYLE_ANIMATED). All hanging hands sit 6 cm further out (lateral 0.33 m), because the relaxed curl faces the thigh. The arm-swing keys during the gate walk are now every 8 frames instead of 16; the body turns while he walks. Two hang keys were added after the lever (1092, 1100). |
| 5.0 s hat | At 302, `grip_object(..., grip="pinch")` grips the brim edge nearest the hand, before the hat is parented to the hand. The hat is then snapped onto the fingertips (`snap_W`). The same pinch is held through the carry, so there is no in-between claw. |
| 20.0 s, f1225 | The camera follows the pedestrian until 1222. On beat 10 (1231), the dark station front is in frame with a second pedestrian walking past it. The camera then enters through the centre of the window. |
| 940 celebration | The hands are above his head (z 1.72, lateral 0.5), so his face reads. |

Kept as intended, in addition to the table above: f1243, one 0.1 s sample as the camera passes through the station window frame.

## v007 rev 3: CAMJUMP (director, 17:45 UTC)
Three aim snaps came from fast whips, where the interpolated aim point swung past close to the camera. `03b_fx_camera.py` now keys the camera and aim on every frame. Wherever the view direction turns more than 15° in one frame, it re-interpolates the direction with an eased slerp across a window. The framings at each end of the window are unchanged.

| Frames | Turn | Eased window |
|---|---|---|
| 324–325 | 143° | 316–332 |
| 1013–1014 | 144° | 1005–1021 |
| 1418–1419 | 164° | 1409–1427 |

The largest step is now 13.6° per frame, and CAMJUMP is 0. Turns this large can't stay under 20° per frame in 6–8 frames, so the windows are 16–18 frames (about 0.3 s).

Two more QA EMPTY samples are kept as intended: 1015 and 1417, each in the middle of one of these whips.
