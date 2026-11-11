# Checkpoint B — blocking (SurgeonBrandsLivers)
- `B_blocking_1s.jpg`: one still per second, base timing (beats on frames 1/301/565/637/781/1045/1231/1501), 270×480, 8 spp.
- `B_camera_path_top.jpg`: top view of the one continuous camera (colour = beat, dots every second). The studio dome is under the OR at z = −6; the camera dives through the abdomen window at ~2.2 s and ~17.6 s and rises out at ~5 s and ~19.8 s. Wall fly-throughs: OR→home ~10.6 s, home→OR ~12.9 s, OR→hearing ~20.9 s.
- `B_camera_path.json`: every 2nd frame, [frame, cam xyz, aim xyz, lens].
## Known issues being fixed now (polish)
- 2 s / 4 s: a gloved hand passes too close to the lens; 5 s is still a dark transit frame (rise starts too late).
- Surgical caps sit too high (helmet look) and cover surgeon 2's brows at 20 s.
- 'B' brand reads close to a 'D' (waist too shallow).
- Surgeon 1's right forearm sinks into the lectern at 24 s.
- Path uses pchip (no overshoot) → a couple of hard corners (22–23 s); switching to a blended spline.
