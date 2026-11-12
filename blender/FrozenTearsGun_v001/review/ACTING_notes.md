# FrozenTearsGun: acting review of v005 (the final), for v006

Source sheet: `acting_before_v005_0.5s.jpg` (every 30 frames, 270×480, 8 samples). Frames are v005 timeline frames (frame = 1 + 60·t). Story-beat frames from `beats.json` stay unchanged in v006.

The director's `clip_scan.py` on v005 found 0 bad ranges. The problems below are about acting and staging.

| # | Frames (time) | Problem | Fix in v006 |
|---|---|---|---|
| 1 | 571–601 (9.5–10.0 s) | The frame is filled by blurred gas through the glass; nothing reads. | Pull the camera back to a 3/4 view of the chamber so the glass, the gas and the drops all read. |
| 2 | 676–706 (11.3–11.8 s) | The frame is blown almost white: white backdrop seen through the glass. | Lower the camera so the cyan part of the backdrop sits behind the chamber, and frame the ice spheres against it. |
| 3 | 781–901 (13.0–15.0 s) | The left support hand under the gun is open, palm up and fingers spread; it isn't holding anything. | Wrap the fingers up around the canister, with the thumb on the other side, without entering the spring window. |
| 4 | 349–440 (5.8–7.3 s) | Valve: index and thumb hover near the wheel rim; it's not a real pinch. | Pinch the rim with thumb and index and curl the other fingers. The wheel turns with the hand. |
| 5 | 1100–1125 (18.3–18.7 s) | The frame is filled by the photo artwork before the flash (a flat wall image). | Keep the camera about 0.35 m back until the flash starts; it passes through only under the flash. |
| 6 | 1300–1330 (21.6–22.2 s) | Whip between the mentor and her: one frame is an empty wall, and her face is cut at the edge. | Add an in-between framing at 21.9 s that holds both of them before the push-in on her. |
| 7 | 1531 (25.5 s, beat 11 start) | Her face isn't readable: the camera is behind her head. | Orbit to the front side of her for beat 11, then arc round to the side and behind for the bubble, without going over her hair. |
| 8 | 1381–1500 (23–25 s) | She holds one pose (hand at the bridge of her nose) for 2 s. Only the sob moves. | Add head shakes, a second gesture (wiping her eye with her knuckles at 24.3 s) and breaths. |
| 9 | 1140–1320 (19–22 s) | Her head hangs down through the whole lecture; she never looks at him. | Add a flinch and look up at him on the desk slap (21.0 s), then she looks down again. |
| 10 | 1681 (28.0 s) | His shielding hand fills the frame. | Widen the 28.15 s framing. |
| 11 | 1711–1871 (28.5–31.2 s) | Time-lapse: the pencil and the file move without her hand, and float above the bench. | Key the pencil to her right fingers while she sketches, and the file to both hands at the vice. |
| 12 | 1759, 1819 (29.3 s, 30.3 s) | Time-lapse: one-frame snaps between poses, and her body slides 0.32 m sideways with planted feet. | The vice is moved closer, so she only shifts her weight (her feet stay put). Each pose change is a quick 0.15 s blend, sped up but continuous. |
| 13 | 1880–1900 (31.4–31.7 s) | The camera swings behind her and passes close to her head and shoulder (blurred body fills the frame). | Add a wider waypoint at 31.7 s, beside her, looking at the mentor. |
| 14 | 1861–1880 (31.0–31.3 s) | Checked: the mentor is already standing in the room before the camera reveals him, and is never seen arriving. | No change needed. |

## Further problems found while fixing
| # | Frames | Problem | Fix |
|---|---|---|---|
| 15 | 1151–1700 (office) | **Bug.** Her lap-hand targets used the stale workshop position, so in the office her arms reached behind the chair and through the armrest. | Use the current pose position. Her hands now rest on her thighs, between the armrests, fingers forward and apart. |
| 16 | 781–1000 | During the aim the support hand interlaced with the grip hand, and its fingers went through the spring-window glass. | Support hand moved forward onto the canister, with fingers pointing forward. The aim position is 3.5 cm closer, so her arm isn't at full stretch. |
| 17 | whole film (workshop) | **Stray helpers:** rig-control widget meshes (`wdg_*`, including a "KEY" text widget) inside the rigged Poly Haven tool chest and vice were rendering at the base of the back wall. | All `wdg_*` objects are hidden from render. |
| 18 | whole film | Lettering embossed in her jeans' normal map (waistband label), and a printed badge plus small print on the red tool chest. | Blurred normal map; tool-chest texture cleaned. |

## Status in v006
- Items 1–13 and 15–18 are fixed. Item 14 needed no change.
- Every story-beat frame is unchanged (`beats.json` is identical).

## Checks
- **Director `clip_scan.py`** (every 6 frames): **0 bad ranges**.
- **Hand audit** (`hand_audit_v006.txt`, every 2 frames): 12 samples.
  - 9 are her right hand resting on the bridge of her nose and her forehead while she cries (4–15 mm skin contact).
  - 3 are mid-blend frames of the time-lapse pose change at 29.3 s.
- **Contact audit** (`audit_v006.txt`): feet and camera clean; one fingertip-on-gun frame (826).
- **Sheets and close-ups:**
  - `acting_before_v005_0.5s.jpg` vs `acting_after_v006_0.5s.jpg`
  - `hand_closeups_v006.jpg`: 15 close-ups at 270×480 of every hand contact (grip, canister, valve, trigger, two-hand aim, lap, nose, eye wipe, desk slap, shield, pencil, file, pick-up, fire, chest pat)
