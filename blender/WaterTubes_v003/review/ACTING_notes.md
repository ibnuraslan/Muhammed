# WaterTubes: acting review of the approved v002 (commit c2c606d)

Sheet: `before_v002_halfsec.jpg`, rendered every 30 frames (0.5 s), 270×480, 8 samples. Times are film seconds (frame = 1 + 60 t). Story-beat frames stay unchanged in v003.

| # | Time (frames) | Problem | Fix in v003 |
|---|---|---|---|
| 1 | 0.0–0.5 s (1–31) | A sidewalk slab fills the bottom half of the opening frame, and the man is small behind it. | Opening camera raised to 0.6 m inside the yard and aimed at him: man, valve and house read at once. |
| 2 | 0.5–2.5 s (31–151) | **Hand not on the prop.** His right hand floats behind the brass nozzle without touching it, and the nozzle is pushed through the valve's lug. | The nozzle stands upright on the valve cap (no clipping). The right fist wraps the nozzle: palm on it, fingers curled round, thumb opposed. The left hand holds the hose, and the hose runs through that hand. |
| 3 | 1.5–2.5 s (91–151) | The camera is behind the tube, so the tube surface fills the lower half of the frame. | Camera raised and moved to the side: valve, hands and face read. |
| 4 | 1.0–2.5 s | His head hangs down the whole time. | His head now lifts to check the swelling tube about once a second (reason: watching it fill), then goes back to the valve. |
| 5 | 2.5–3.5 s (151–211) | Crouch to stand is quick and stiff. | Stand-up passes through a half-crouch with a hand on his knee, then stands and wipes his brow. |
| 6 | 3.7–8.3 s | Tubes inflate around the house with nobody filling them. | **Partly fixed.** He pulls the nozzle off the valve at 2.5 s and carries it in his right fist round the ring through beat 2, with the hose trailing. The other segments still swell as a time-lapse, without the hose visibly attached to each one. |
| 7 | 8.5 s (511) | A street tree fills the frame during the whip to the street. | The tree is moved off the camera path. |
| 8 | 10.0–10.5 s (601–631) | Surge spray reads as white balls or pebbles right in front of the lens; the camera sits inside the surge lip. | Drops are about half the size, the spray sits 0.5 m behind the front, and the foam is toned to muddy beige. The camera is raised to 2.0–2.2 m, out of the lip. The foam still fills the lower frame for about 0.3 s as the wave passes under the lens. |
| 9 | 21.0–22.5 s (1261–1351) | The camera skims the tube top, so dark tube fills half the frame (22 s almost all). | Camera raised to 2.9–3.3 m and aimed further out at the slam. The tube still takes the bottom third because it is the subject of the beat. |
| 10 | 26.0–27.0 s (1561–1621) | The neighbour's grey wall fills most of the frame. | Camera pulled back to show the mud line, the sofa on the lawn and the neighbour together. |
| 11 | 30.5 s (1831) | **The acting face is cut off.** The porch column and his torso fill the frame and his head is out of frame, on the "his house stood dry" beat. | Beat 10 camera re-aimed at his head height (2.75 m) from the lawn side. His face reads at 29.5–30.5 s. |
| 12 | 31.5–32.0 s (1891–1921) | The rise behind him passes low over the roof, so roof fills the frame. | The 31.3 s key is moved in front of the porch at 3.4 m: no roof fill and no camera inside the roof. |
| 13 | 29.0–30.0 s | The hands-to-head "amazed" pose is held, with little life in it. | Not changed: the existing head turns and pose changes every ~0.5 s are kept. |
| 14 | 12.0–14.0 s | Neighbour B's feet slide as he backs away from the water. | He backs away with real steps (IK walk backwards, feet planted). |
| 15 | whole film | Background people could hold one pose for a long time. | Checked, not changed: they already shift every 0.5–1 s (hero porch loop every 30 frames, Neighbour A every 60). |

Checked and OK: feet planted while walking (IK plants), the bin wheeled with both hands, falls (none), floating car and debris (moved by the water), the fence (pushed over by the flood), hand audit (0), and the camera never inside a body or wall (audit).

## Extra fixes found while re-checking
- The hose was a Bezier with animated points and stale AUTO handles, so it drew as several straight spikes. It is now a NURBS spline that stays smooth.
- An in-between key was added to his stand-up so his left hand no longer brushes the shirt on the way up to wipe his brow.
- He crouches deeper at the start so his fist reaches the low nozzle, and his left hand holds the hose lower so it no longer covers his face.

## Re-check results (v003)
- `clip_scan.py` (director branch), step 6: **0 bad ranges** (`clip_scan_v003.json`).
- Hand audit, every 2 frames: **0 hits** (`hand_audit_v003.txt`).
- Camera inside geometry: 0; below ground: 0 (`contact_audit_v003.txt`).
- Contact audit, feet: 34 samples more than 4 cm up, mostly mid-swing and on the porch steps; same as v002.
- Story-beat frames are unchanged (`beats.json` is identical to v002).

## Round 2 (director review of e36d3d3), Nov 12
- **Nozzle grip:** `hand_poses.py` `wrap_grip` on both hands. The nozzle is placed in the curled-finger ring from frame 1, seated on the valve cap in beat 1 and carried in the fist after. No gap (`after_v003_nozzle_grip.jpg`).
- **No claws:** every free hand uses a `hand_poses.py` preset: `relaxed`, `open_alarm` for raised alarm hands, and `cup_hold` for the hero's hands on top of his head at beat 10. Neighbour B's alarm is an open hand raised in front, then lowering. Joint limits come from `add_hand_limits`.
- **Neighbour B:** no T-pose in-betweens; his arms stay in front.
- **Camera:** pulled back at 2.0–2.5 s; at 10.5–11.5 s moved up over the verge (no foam fill); the 31.3 s key is clear of the porch roof.
- **Hidden objects:** now hidden in the viewport too, so the QA ray-casts match the render.

## qa_check.py (qa_v003.json, step 6): flags that stay, and why
- **HOVER, CLAW, FACEPRESS, BACKHEAD, FILL: 0.**
- **EMPTY (183 samples):** no character in the frame by design:
  - the beat 2 crane over the ring (7.5–8.3 s)
  - the flood surging down the street (8.3–11.9 s)
  - the tube cutaway and explainer on the sky-blue gradient (14.3–20.8 s)
  - the slam at the barrier (22–22.8 s)
  - the aftermath street (24.9–25.8 s)
  - the drone pull-up (31–33.5 s)

  The early beat 1 samples flag "character under 15 %" because the swelling tube shares the frame with him. Hands, valve and tube read together, as asked.
- **INSIDE (18 samples):** false positives. The camera is outside all geometry (ray-parity audit: 0 frames inside).
  - 1.2–2.6 s: the rays hit the inside-facing side of the tube mesh.
  - 20.8–20.9 s: the cutaway shell fading out.
  - 31.1 s: one sample.

## Hand audit
5 hits, all at f371–375: Neighbour B finishing his walk at his door, about 6 s, off-camera behind the street whip. Everything else is 0. clip_scan has 0 bad ranges.

## Self-check (6 points)
1. Hands touch what they hold: checked (nozzle, hose, bin)
2. No claws: checked
3. Nothing pressed into a face: checked (QA FACEPRESS 0)
4. No empty, blurred or black cells, and no back of head on beats: checked (QA BACKHEAD 0; the no-character cells are the intended water/cutaway/aerial shots listed above)
5. Close-ups show the hands: checked
6. hand_poses.py used: checked
