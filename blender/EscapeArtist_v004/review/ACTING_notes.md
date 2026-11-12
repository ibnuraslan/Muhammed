# EscapeArtist: acting review (v003 → v004)

Source: half-second sheet of v003 (`review/before_v003_half.jpg`, 270×480, 8 samples, every 30 frames). Each problem has its frames and its fix. Story-beat start frames are unchanged (`beats.json` is identical). VO not added.

| # | Time (s) / frames | Problem in v003 | Fix in v004 |
|---|---|---|---|
| 1 | 1.5–2.0 / 90–120 | The guard's back fills most of the frame as he passes the camera. | Camera key at 150 moved back and up (it looks over the guard to the prisoner); guard walk re-timed to pass earlier. The guard still crosses the left of frame briefly. |
| 2 | 3.5 / 200–232 | The ECU drifts to the prisoner's ear and hair because his head turns away. | His head now follows the key ring back toward camera (yaw 35° → 8°), so the eye stays in frame. |
| 3 | 4.0 / 240–276 | The top of his head fills the frame as the camera rises over the bars. | Rise key raised and pulled back (wider, looking down into the cell). |
| 4 | 4.5–5.0 / 274–300 | He walks to the bunk and snaps from standing to seated in about 10 frames, with a root spin. | Real in-betweens: he walks to the bunk front, turns round in two steps (274–292), then sits (292–316), with hips back and down, chest forward and hands sliding onto his thighs. Filing starts at 316. |
| 5 | 8.5 / 510 | The top of his head fills the frame. | Camera key moved to a low angle onto his face and hands. |
| 6 | 9.0–9.5 / 541–566 | A snap from seated to standing. | Stand-up in-betweens (541–566): lean over the feet, push on the thighs, rise, straighten. |
| 7 | 9–11 / 541–678 | The filed key stays floating on the bunk instead of in his hand. | The key is baked into his right hand from 541 to 678, through the walk, the lock and the exit. |
| 8 | 10–10.5 / 618–650 | The cell door swings open by itself. | Turn the key (604–626), then his right hand grips the door bar and pulls it open while he steps back (626–648); the door finishes its swing to 72°. |
| 9 | 11.5 / 690 | The frame is filled by the corridor wall (fly-through into the memory). | Kept, as the fly-through transition: about 4 frames, and the wall carries texture. |
| 10 | 14.5 / 870 | The boy's head blurs across the bottom of the frame. | Kept: a foreground pass for about 0.2 s. |
| 11 | 17–21 / 1036–1421 | After the handover the toolbox hangs in the air beside the boy for 5 s with no hands on it. | Both of the boy's hands stay on the handle through beat 6 (fingers wrapped). |
| 12 | 19–23.5 / 1100–1421 | The stepmother's arm sweeps across her face. Her desk phone is behind her, so lifting it drags her hand through her own body. | She is re-blocked behind the side table: she reaches forward to the phone, lifts it to chest height, talks into it and points with her other arm. Nothing crosses her face or body. |
| 13 | 24.5 / 1460–1470 | The frame is filled by a blurred wall on the court→corridor whip. | Kept: about 4 frames through a real doorway (since v002). |
| 14 | 25 / 1470–1512 | The gate slams by itself while the guard stands still behind it. | The guard walks the gate shut with both hands on its free end (1446–1500), then stands behind it. The camera now frames him pushing. |
| 15 | 32 / 1926–1946 | In solitary he snaps from standing to seated. | Two-step turn (1926–1946), then a sit-down (1946–1972). |
| 16 | 32–35 / 1972–2140 | His head hangs down for 3 s with no reason. | He breathes, then lifts his head and looks to the door slot (t ≈ 1.4–2.4 s), then sinks again. |
| 17 | 36 / 2148–2186 | A snap from seated to standing, and the saw teleports from the bunk to the bar. | Stand-up (2148–2170). His left hand picks the saw off the mattress beside him (2150–2156) and carries it to the window (baked to the hand). |
| 18 | 40.5–41.5 / 2440–2490 | The saw blade vanishes when he leaves, the cell door opens by itself, and bars fill the frame. | Sawing ends at 2440 and the blade stays in the cut (visible to 2898). He walks to the door (2452–2506) and pulls it open by hand (2508–2532). The camera follows him back in through the window, then out between the bars. |
| 19 | 42–44.5 / 2560–2670 | The tube pops into his hand, and the guards freeze at nothing: he is out of frame. | He walks out (2532–2582) and draws the tube from his back pocket (2566–2590). Freeze, back-away (2590–2690) and run (2690+) are shifted 30 frames inside the beat. Camera keys put him in the foreground with the guards beyond, then a reverse on his face. |
| 20 | 47.5 / 2850 | A guard's head blurs across the bottom of the frame. | Camera key raised (z 2.3) so the guards run under it. |
| 21 | 49–53 / 2898–3228 | Time-lapse pose pops: he teleports between sit, window, pace and scratch every 40 frames, and a floating fist appears at the tally wall. | One continuous action: he scratches tally marks at the wall (2898–2990), walks back (2992–3030), turns (3030–3050), sits (3050–3075), breathes and looks up at the window. The day/night light strobe and the tally reveal carry the passing years. |
| 22 | 53.5 / 3100 | The young→old swap pops on camera. | The swap is at 3166, while the camera is on the tally wall (the bunk is out of frame). The old man continues the same seated pose. |
| 23 | 54–57.5 / 3228–3450 | The old man's head hangs down for 4 s (frozen). | He breathes, lifts his head and looks toward the slot light within about 1 s, with a small head drift. |
| 24 | 57.5–58 / 3460–3498 | Seated → walking snap, then the back of his head and shoulder fill the frame. | Stand-up (3446–3470), then he walks to the window (3470–3498). The camera moves to the side wall and then over his left shoulder, and passes the window between bars. |
| 25 | 60.5 / 3630 | Chain-link and razor wire fill the frame (the camera flies through the fence). | The camera climbs first (z 4.9 at 3630), crosses above the razor wire, then descends to the window. |
| 26 | 19–23.5 / 1140–1421 | **The stepmother's phone never left the table.** The glTF contains an inner node also called "Phone", so the script animated that scaled sub-node, and she held an empty hand at her ear. | The script now animates the import root. The phone lifts from the side table into her hand at her ear. |
| 27 | 24–25 / 1446–1500 | The guard's hands were up to 30 cm off the gate bars, because the scripted angle didn't match the gate's Bezier curve. | His hands and feet are driven from the gate's own rotation curve, so his hands stay on the end bars as he swings it shut. |
| 28 | 18–23.5 / 1060–1421 | The boy's hands couldn't reach the toolbox handle: the box was 40 cm in front of him. | The box ends in front of him at handle height his arms reach (0.86, 8.06). |
| 29 | whole film | Relaxed, walking and running hands brushed into the thighs, seated hands sank 2–4 cm into the thighs, and hands swept through the body on turns. | Relaxed hands moved wider. Seated hands rest on top of the thighs with fingers along them. Turns are keyed every 2 frames. The stand-up lifts the hands off the thighs to the outside first. Running hands are at waist height. |
| 30 | 9–11, 25, 40–43 / 558–705, 1446–1512, 2508–2582 | **Build bug, present since v001:** `join()` kept the first part's origin, so the hinge offsets were wrong. The corridor gate sat outside the building (x ≈ 17). The hero cell door sat 1 m left of its opening and 1.4 m into the floor, so the cell had an open gap and the lock he "unlocked" was not there. | `join()` now bakes parts to world space before the hinge offset. The door fills its opening at full height with a real lock (keyhole, escutcheon, handle, rivets) and swings on its hinge. The gate spans the corridor and the guard swings it shut. |
| 31 | whole film | Fingers bending backwards. | Finger Limit Rotation constraints (since v002). |

Not changed, but checked: the fence climb (hands on the mesh, feet on the mesh, over the top, drop, crouch-land, run), the guards' freeze and chase, the gavel strike, the father's handover, the protesters' placard sway and the candles.

## Clip scan (`blender/pipeline/clip_scan.py`, director branch)
`clip_scan.py` picks the characters it scans once, at the first frame of the scene range, by viewport visibility. In this film the cast changes mid-film: the boy, father, stepmother, judge, old man and protesters are hidden at frame 0, and the young prisoner is hidden after 3166. Run once over the whole film, it would never scan the characters who appear later, and it would keep scanning hidden ones. So:
- `vis_key` now keys viewport visibility on character meshes too (render is unaffected).
- `scripts/clip_scan_windows.py` runs the unmodified `clip_scan.py` once per cast window (0–677, 678–941, 942–1379, 1380–1547, 1548–1859, 1860–2483, 2484–2898, 2899–3165, 3166–3228, 3229–3479, 3480–3750), step 6, depth 2 cm.

| Pass | Bad ranges |
|---|---|
| v004 first pass (whole film) | 18 |
| after the hand fixes (windowed) | 13 → 4 → 3 → **0** |

See `review/clip_scan_v004.json`.

## Other checks on v004
- Hand audit (`scripts/hand_audit.py`, every 20 frames): 2 flags, both at the fence top (1740–1760), hands passing over the razor wire.
- Contact audit (`scripts/audit.py`): hover 0, sink 0, camera inside geometry 0.
- Hand close-ups: `review/hand_closeups_v004.jpg` (28 contacts) and `review/hand_closeups_v004_targeted.jpg` (side angles on the new contacts).
