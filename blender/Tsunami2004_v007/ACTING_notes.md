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

## Round 3 (director rules 14:40–15:00 UTC): hand_poses.py, 6-point self-check, qa_check.py
- All finger poses now come from `blender/pipeline/hand_poses.py`: `add_hand_limits` on every rig, `relaxed` default, `point` for the pointing tourists/kids, `power_fist` at 0.65 (loose fist) for runners, `flat_palm` for shading the eyes, `open_alarm` for the waving fisher, `wrap_grip` on the fish tail (6.75–9.0 s). No hand-set finger angles remain.
- Sheet cells fixed for the self-check: 13.0 s now looks ahead to the horizon (not bare seabed), 15.5 s shows the cross-section from above (diorama kept visible until 15.56 s), beat 1 (frame 1) is a side view of the kids (no back of heads), crowd clones are hidden by 21.40 s (none on the beat-9 frame).
- qa_check fixes: hidden face-debris and library source objects were left at the world origin with stale transforms and read as "props" next to a tourist's hand (HOVER); they now rest far away / are removed from the package.

### qa_check flags kept as intended (with reasons)
| Flag | Frames | Why it stays |
|---|---|---|
| EMPTY | 0.3–0.4 s, 2.4–3.6 s, 7.8 s, 10.3 s, 11.1–11.4 s, 12.5–18.1 s, 19.0–21.0 s, 21.7–39.9 s | No character in view by design: stranded-fish macro, the horizon push-in, aerial crane, the earthquake cross-section, the approaching wave, the impact, flood and aftermath. Everyone leaves frame before the wave hits (client rule: never show people being hit), so the second half of the film has no characters. Each of these frames shows its narration subject (fish, seabed, wave, town, mosque). |
| INSIDE | 13.2–14.2 s, 15.2–15.5 s | The camera is inside the studio backdrop sphere of the earthquake cross-section (the cyan-to-white explainer bowl); rays hit its inner faces by design. |
| CLAW | TouristW.R / TouristM.R / KidB.L / clone pointing windows (6.1–7.4 s, 10.6–12.3 s) | The `point` preset from hand_poses.py (index straight, other three curled into the palm) is detected as "curled fingers touching nothing". It is the intended pointing hand, checked in close-up. |

### Final qa_check (c6240b2) on the packed v005 file
`qa_v005.json` counts: EMPTY 295, INSIDE 15 (both intended, above). CLAW 0, HOVER 0, FACEPRESS 0, BACKHEAD 0, FILL 0. clip_scan: 0 bad ranges. Package 85 MB, nothing unpacked, one camera.

## v006: faults found by watching the moving preview of v005 (frames in the 60 fps timeline)
| Frames | Fault | Fix |
|---|---|---|
| 150–220 and every later fish shot | Fish hovering 5–9 cm above the sand (shadow apart from the fish) | They rest on the sand (side down); hops 3–7 cm |
| 660–735, 1066–1086 | Blown-out beige glare from the sun on the wet sand reads as a blur | Wet roughness 0.55, specular 0.3 |
| 911–934 | Cross-section diorama seen from outside as a tilted box in a grey void | Camera holds the level cross-section view from 15.0 s (frame 901) |
| 936 | Dark frame: camera under the sea floor | At 15.6 s (frame 937, beat 7) the camera goes to the beach in one frame; the diorama hides and the hero wave appears on that same frame (first v006 build showed the wave popping in 0.4 s after the cut, fixed) |
| 1091 (18.15 s) | Runner LocalM ran straight past the lens and filled the frame | LocalM is hidden from 13 s, while off screen; his motion is kept so the crowd layout is unchanged. Seven people still run inland |

Watched on the v006 moving preview and kept as they are:
- 25.5–26.1 s (frames 1531–1566): a tower passes on the right during the flood flyover. It is sharp, never fills the frame and sits next to beat 10, so it stays.
- Sun glints on the flood water (22.5–28 s): real reflections, never covering a subject.

## v007: director review of v006 (frames in the 60 fps timeline)
| Frames | Note | Fix |
|---|---|---|
| 786–806 | Tilted teal box in a grey void, and a frame of sand only, on the way into the cross-section | Hold the horizon view, clean cut at beat 6 (787) to a tight, level cross-section view; slow push-in; clean cut out at 937 |
| 151–241 | 1.5 s of bare seabed with no people and no sea | Camera looks more level: the receding sea is on the horizon behind the fish |
| 551–726 | Blurry aerial drift with tiny people, and frames of sand only | Low three-quarter camera on the group (x = 12, clear of everyone); the fisher's face shows on beat 5 |
| 880–936 | Diagram arrows held static for about 1.3 s | Slow push-in through the whole cross-section; the cut out is at 15.6 s |
| 1251–1746 | Flood: smooth grey-green sheet, sun-glare blobs, little debris | Muddy brown water, roughness 0.5 (no glare blobs), 72 debris pieces along the path, camera aimed higher at the town |
| 1606, 1981–1996 (first v007 build) | Black frame, and black wire bands across the mosque, after the debris change shifted the random layout | Extra debris on its own random stream; the clean layout is restored and checked on the preview |
