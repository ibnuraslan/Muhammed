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

## Round 2: director review of 606981f
| # | Problem | Fix |
|---|---|---|
| R1 | Grips that didn't grip: pencil, file, gun pick-up and desk slap. | A hand-shape library (flat, relaxed, wrap, writing, loose fist, cradle, hook), with a finger-spread control so the fingers close together. Each action now uses one: <ul><li>**Pencil:** writing grip, hand on its side, pencil between thumb and index.</li><li>**File:** right hand wraps the handle, left palm flat on the tip.</li><li>**Gun pick-up:** the gun lies with its grip towards her right hand; she closes her fingers round the grip block, and the grip blends into the firing grip as it lifts, thumb wrapped.</li><li>**Desk slap:** flat palm, fingers together.</li></ul> The trigger close-up is re-aimed on the index finger. |
| R2 | 6.0–7.0 s: the valve hand made an L shape (thumb straight out). | The thumb was hitting its joint limit. Now the fingers hook over the wheel rim with the thumb tucked, and the hand stays on the rim while the wheel turns. |
| R3 | 15.5–19.0 s: near-empty, out-of-focus frames. | The camera rides 0.42 m behind the pellets looking at the framed photo they fly into. The photo is in focus and the pellets are larger. |
| R4 | 23–25.5 s: thumb jutting out, and a claw on her forehead. | Her palm is over her eyes with the fingers together and relaxed. At 24.1–24.8 s her loose-fist knuckles wipe under her eye, then the palm returns. |

- **Director `clip_scan.py`** (every 6 frames): **0 bad ranges**.
- **Hand audit** (`hand_audit_v006.txt`, every 2 frames): 13 samples.
  - 11 are her palm or knuckles resting on her face while she cries (4–15 mm skin contact).
  - 2 are mid-blend frames of the time-lapse pose change at 29.3 s.
- **Contact audit** (`audit_v006.txt`): no contact problems.
- **Sheets and close-ups:**
  - `acting_before_v005_0.5s.jpg` vs `acting_after_v006_0.5s.jpg`
  - `hand_closeups_v006.jpg`: 15 close-ups at 270×480 of every hand contact (grip, canister, valve, trigger, two-hand aim, lap, nose, eye wipe, desk slap, shield, pencil, file, pick-up, fire, chest pat)

## QA flags that stay (`qa_v006.json`, every 6 frames, on the packed file)

Totals: FILL 4, CLAW 59, HOVER 108, EMPTY 109, INSIDE 18.

Fixed before this run:
- The `INSIDE` flags from back-facing wall planes: all room planes now face into their room.
- `HOVER` flags from the explainer card (it is now hidden and parked away outside the cutaway).
- Frost and gas parked outside their beats.
- The static gun parts merged into `Gun_Body`.

| Flag | Frames | Why it stays |
|---|---|---|
| CLAW Inventor.R | 271–277 (4.5–4.6 s), 301–313 (5.0–5.2 s), 331 (5.5 s), 343–391 (5.7–6.5 s), 631–637 (10.5–10.6 s), 919–925 (15.3–15.4 s), 1705–1759 (28.4–29.3 s), 1921–1939 (32.0–32.3 s), 2059–2095 (34.3–34.9 s) | Intended. The right hand holds the gun with the index finger extended on the trigger, so the fan test trips. The same goes for the writing grip at 28.4–29.3 s (index and thumb pinch the pencil while the other fingers curl). |
| CLAW Mentor.R | 1153–1237 (19.2–20.6 s), 1279–1297 (21.3–21.6 s) | Intended. His lecture point (index straight, other fingers curled) at 19.2–21.6 s. |
| EMPTY | 445–457 (7.4–7.6 s), 517–541 (8.6–9.0 s), 589–619 (9.8–10.3 s), 637–661 (10.6–11.0 s), 673 (11.2 s), 685–757 (11.4–12.6 s), 883–907 (14.7–15.1 s), 931–943 (15.5–15.7 s), 955–1129 (15.9–18.8 s), 1303 (21.7 s), 1567 (26.1 s), 1699 (28.3 s), 1723–1729 (28.7–28.8 s) | Device macro and explainer beats (7.4–15.7 s): the device itself is the subject, as the reference's cutaway grammar does. Pellet flight (15.9–18.8 s): the pellets and the photo they fly into are the subject. 21.7, 26.1, 28.3 and 28.7 s are single transition frames inside the white flash or the arc. |
| FILL | 19 (0.3 s), 133–139 (2.2–2.3 s), 1543 (25.7 s) | 0.3 s: her hair at the top of the opening face close-up. 2.2 s: macro of the funnel, the subject of the line. 25.7 s: her hair passes the frame edge as the camera orbits her into beat 11. |
| HOVER Inventor.L near Frost | 655–673 (10.9–11.2 s), 715–739 (11.9–12.3 s), 793–859 (13.2–14.3 s), 901 (15.0 s), 931 (15.5 s) | False positive. `Frost` is the frost-crystal layer inside the glass chamber, and the QA checks the first prop within 12 cm alphabetically. The left hand is on the canister or valve outside the glass. |
| HOVER Inventor.L near Gas_0 | 907–925 (15.1–15.4 s), 1819 (30.3 s), 1933–1945 (32.2–32.4 s) | False positive. The volume gas belongs to the chamber (hidden outside 7.3–12.7 s; see-through FX). The hand is on the canister or grip. |
| HOVER Inventor.L near Gas_2 | 1927 (32.1 s) | Same as above. |
| HOVER Inventor.L near Gun_Body | 367–409 (6.1–6.8 s), 1705–1753 (28.4–29.2 s), 1879–1885 (31.3–31.4 s) | 6.1–6.8 s: the left hand holds the valve wheel rim (`Gun_ValveRim`, a separate moving part) next to the merged body (close-up `valve_pinch`). 28.4–29.2 s and 31.3 s: the gun is hidden or lying on the bench while she sketches beside it; the QA also counts hidden objects. |
| HOVER Inventor.L near bench_vice_bar | 1759–1813 (29.3–30.2 s) | Time-lapse filing: her hands hold the file (`TL_File`) across the vice jaws, so they sit beside the vice bar. |
| HOVER Inventor.R near Gas_0 | 1921 (32.0 s) | Same as above. |
| HOVER Inventor.R near Gas_4 | 1927–1945 (32.1–32.4 s) | Same as above. |
| HOVER Inventor.R near Gun_Body | 1705–1753 (28.4–29.2 s), 1849 (30.8 s), 1861 (31.0 s) | 28.4–29.2 s: the gun is still hidden (not built yet) next to her sketching hand; the QA counts hidden objects. 30.8–31.0 s: her hand passes the finished gun on the bench just before the pick-up. |
| HOVER Inventor.R near bench_vice_bar | 1873–1885 (31.2–31.4 s) | Same as above. |
| HOVER Inventor.R near bench_vice_clamp | 1777–1813 (29.6–30.2 s), 1837–1843 (30.6–30.7 s), 1867 (31.1 s) | Same as above. |
| HOVER Mentor.L near ImpactPuff | 2017 (33.6 s) | Same as above. |
| HOVER Mentor.L near Spark_09 | 2011 (33.5 s) | Single frame: the tear projectile or spark passes his hand during the pelting (not a held prop). |
| HOVER Mentor.R near ImpactPuff | 2017–2095 (33.6–34.9 s) | False positive. `ImpactPuff` is the frost-puff volume on his chest; his hand pats his shirt (close-up `mentor_chest_pat`). |
| HOVER Mentor.R near TearR_05 | 1675 (27.9 s) | Single frame: the tear projectile or spark passes his hand during the pelting (not a held prop). |
| HOVER Mentor.R near Tear_11 | 1615 (26.9 s) | Single frame: the tear projectile or spark passes his hand during the pelting (not a held prop). |
| INSIDE | 1573–1645 (26.2–27.4 s), 1663–1675 (27.7–27.9 s), 1693–1699 (28.2–28.3 s) | The camera is inside the thought bubble (26.2–28.2 s, intended: a translucent see-through shell), and the 28.3 s white flash as the camera passes into the workshop. |

## Six-point self-check (I looked at my own after-sheet and close-ups)
1. **Hands visibly touch what they hold:** checked. These all show contact:
   - grip, canister, valve rim, trigger and two-hand aim
   - the lap, and her palm on her eyes
   - desk slap, chest pat and gun pick-up
   - pencil and file are in the hands, but small in the close-ups
2. **No claws:** checked. Every hand uses a named shape (flat, relaxed, wrap, writing, hook, loose fist). The remaining open hands are the mentor's palms-out "stop" shield.
3. **Nothing pressed into a face:** checked. The only face contact is her palm resting over her eyes and the knuckle wipe (intended, under 1.5 cm). The mentor's shielding hand stays in front of his face.
4. **No empty, blurred or black cells, and no back of the head on beats:** checked.
   - Beat 11 opens on her face.
   - The pellet-flight cells show the pellets and the photo.
   - The only head-from-behind cell is 26.0 s, inside beat 11's bubble move, as an over-the-shoulder towards the mentor.
5. **Close-ups show hands:** checked. All 15 close-ups are aimed at a hand and lit. The trigger close-up is re-aimed.
6. **hand_poses.py:** checked. Not on `claude/beautiful-ptolemy-c5vrcq` yet (fetched at submission). The named shape library in `03_animate.py` (`SHAPE`, `mix_shape`) is used meanwhile.
