# ShoeBomber: checkpoint B (blocking)

- **Sheet:** `review/B_blocking_1s.jpg`, 1 still per second, 270×480, 8 samples.
- **Camera path:** `review/camera_path.csv`, every 15 frames. One camera, `CAM_Film`. Its framing keys are in `scripts/04_fx_camera.py` (the `SEG`…`SEG4` lists).
- **Beat frames:** `beats.json`.

## Build
| Script | What it does |
|---|---|
| `scripts/01_build_humans.py` | MPFB humans |
| `scripts/02_build_scene.py` | The four sets |
| `scripts/03_animate.py` | Character and prop animation |
| `scripts/04_fx_camera.py` | Attachments, fx, lights, grade and camera |

## What reads already
- **Beat 2 (4–6 s):** the attendant with the trolley down the aisle, then a push to her face.
- **Beat 3 (7–8 s):** her over-the-shoulder view onto the bomber at the window.
- **Beat 4 (9 s):** a top-down view of the pile in the aisle.
- **Beat 6 (16–17 s):** she holds up the sneakers.
- **Beat 7 (18–20 s):** the studio cutaway with the grey slab and its glow.
- **Beat 8 (22–23 s):** the plane above the clouds.
- **Beat 9 (24–25 s):** the traveller takes his sneakers off at the belt.

## Known blocking problems, being fixed for C
- **Beat 1 (0–3 s):** the camera sees his back; the match and shoe are hidden by his hunch. I'm restaging it as a side 3/4 from the empty middle seat.
- **12 s and 14–15 s:** the camera passes through crew bodies. Re-routing.
- **21 s:** a black frame at the start of the sky beat (the camera is inside the fuselage or wing). Re-routing.
- **26 s:** the final airport framing loses the traveller.
- **Look:** the airport is overexposed. Cloud puffs are lumpy. The traveller ends barefoot, not in socks.
- **Polish list:** the smoke wisp, hand contact audit, the struggle impact accent, the putty slab look and a plunger push.
