# Tsunami2004 — acting review of v004 (approved final) → fixes in v005

Source sheet: `review/before_v004_0.5s_part1.jpg` (0–19.5 s) and `part2.jpg` (20–39.5 s), 270×480, 8 samples, every 30 frames, rendered from the packed v004 file.
Story-beat frames (beats.json) are unchanged in v005.

| # | Time (frames) | Problem in v004 | Fix in v005 |
|---|---|---|---|
| 1 | 0–12.9 s and 17.2–21.1 s (1–775, 1033–1267) | Arms held stiffly out to the sides on every standing/walking person ("penguin" arms) — the hang/swing hand target was 26 cm out from the shoulder; runners' hands 23 cm out | Hang/swing hand 10 cm out with a slight elbow bend, run 12 cm; palms face the thigh. Clothes clearance checked with the hand audit |
| 2 | 0–5.4 s (1–325) | Adults stand frozen facing the sea for up to 5 s (only a tiny sway) | Every stand now breathes, shifts weight side to side (±2.5 cm, slow) and scans with the head (±14° yaw, ±3° pitch), each person on a different phase |
| 3 | 7.4–12.4 s (445–745) | Kids stand still for ~5 s with a fixed upward head | Kids walk over next to the adults (8.6–10.6 s), then stand, look around and point at the horizon (10.9–12.3 s) |
| 4 | 8.2–12.4 s (493–745) | Adults hold the same pose for 4 s; pointing arms are rigid | Idle life as in #2; pointing arm bobs gently; head turns between the horizon and the others |
| 5 | 12.4–12.95 s (745–778) | Everyone bursts from standing into an 11 m/s sprint in 0.5 s (visible over the shoulder at 12.4 s) | A realistic first stride: turn and 2.5 m of acceleration before the camera dives away |
| 6 | 7.2 s (433, beat 4 "noticed a wave") | Camera behind the group: no faces on the beat | Camera in front of the group at face height looking back at them (faces turning), then swings round to the horizon for the white line at 8.2 s |
| 7 | 15.5 s (931) | Black frame: camera between the cross-section bowl and the seabed underside on the way out | Terrain underside renders as wet sand (macro surface) so the pass reads as coming up through the sea floor; no black frame |
| 8 | 20.5 s (1231) | Food-stall model shows Japanese characters on its sign (on-screen text) | Stall sign/paper material replaced with plain cloth; no glyphs anywhere |
| 9 | 21.0–21.15 s (1261–1270) | Runners stop at the beach road and are hidden at 21.15 s while still possibly in the wide shot | Runs extended inland past the hotel (to y −40) and hidden at 21.45 s, out of the wide's view; checked in close frames |
| 10 | 22.5 s (1351) | Hotel spray is 9 huge white blobs that read as cotton clouds | Smaller, more numerous bursts low at the ground-floor openings |
| 11 | 33.0–33.5 s (1981–2011) | Camera skims the mosque: facade/minaret fills most of the frame | Path moved out: mosque stays whole in frame |
| 12 | Crowd clones (0–21 s) | Same gestures repeated by copies at a distance | Clones are time-shifted 3–15 frames and use the new idle; acceptable at their distance (noted) |
| 13 | Fisher fish (6.45–9.25 s) | Hand grip OK (accepted) — fish dropped at 9.0 s falls straight with the hand opening | Kept |

## Director review of v005 (32ce79b) — second round, fixed in the same v005 folder
| # | Time | Problem | Fix |
|---|---|---|---|
| 14 | 6.7, 8.6, 9.5, 10.6–12.3 s | Pointing hands were a limp wrist or a flat open hand | Index finger straight, middle/ring/little curled into the palm, thumb tucked; wrist straight along the arm, which aims at the sea |
| 15 | 0.5 s, 4.0 s (kids jogging) | Arms spread at chest height | Running arms pump front-to-back close to the ribs (6 cm out from the shoulder line) |
| 16 | 17.4–21.4 s and the kids | Limp, dangling wrists on runners | Loose fists, wrist continues the forearm |
| 17 | 15.5 s | Flat brown/teal frame on the seabed exit | Sea surface transparent from below and the sea-floor underside shows the textured sand, so the exit reads as passing up through the sea floor |
| 18 | 10.5–11.0 s | Blown-out sun highlight on the wet sand | Wet-sand roughness 0.18 → 0.42 |
| 19 | 22–29.5 s | Flood read as smooth grey clay | Glossy water (roughness 0.09) reflecting the sky, murky brown-teal tint, stronger foam lines along the current and white water at the front, Ocean-modifier ripples, floating debris bobbing |
| 20 | close-up 08.40 | Close-up showed only his back | Re-aimed from the front: fist on the tail and the hanging fish visible |
