# CaveRescue acting review (v004 → v005)

Source: half-second sheet of v004 (`review/ACTING_v004_before_halfsec_a.jpg` and `_b.jpg`, 270×480, 8 samples, every 30 frames).
Story-beat frames are unchanged (`beats.json`).

| # | Time / frames (v004) | Problem | Fix in v005 |
|---|---|---|---|
| 1 | 5.5 s / ~331 | Camera so close to the running boys that a head fills the bottom of the frame. | Camera keys 335–370 moved up and back. |
| 2 | 6.5 s / ~391 | Camera skims the floor; the frame is floor and wall only. | Raised; the runners are kept in frame. |
| 3 | 7.0–9.0 s / 421–541 | Camera passes beside or through runners: a jacket at the frame edge, legs over the lens. | Low chase key moved to the open side of the tunnel, 1 m+ from the lanes. |
| 4 | 7.5–9.0 s | Runners pump their arms with elbows flared out like wings. | Elbow pole tucked in (out 0.25 → 0.08) and hand path closer to the body. |
| 5 | 17.0–19.5 s / 1021–1171 | Huddled boys hold an identical head-down pose (frozen, head hanging for no reason). | Each boy gets its own slow breathing, head turns and glances (keys every ~45 frames, random phase). Heads lift to the diver's light at 1085. |
| 6 | 20.0 s / 1201 | Diver's head at the frame bottom and torch flare; nobody's face reads. | Camera holds on the boys' faces a little longer before diving (1205 key). |
| 7 | 23.0–24.5 s / 1381–1471 | In the squeeze, the divers swim straight at the lens: fins, a hand and the body fill the frame. | Camera kept 2.5 m+ ahead and offset to the side, so the divers pass beside it. |
| 8 | 25.0 s / 1501 | A diver's body fills the frame as he passes the camera. | Same as 7. |
| 9 | 31.5–33.0 s / 1891–1981 | Boy at the water's edge hangs his head straight down; the camera sees the top of his head and the face is unreadable on beat 8 ("seemed impossible"). | He looks at the water ahead (head 15–25° down), with breathing and small glances. The camera sits low in front at eye level, so his frightened face reads. |
| 10 | 33.0–35.5 s / 1981–2131 | Kneeling divers are frozen statues during the orbit. | Kneel keys vary lean and head, so they lean in, nod and look at each other. |
| 11 | 36.0 s / ~2161 | The orbit passes right behind the medic's tanks; a tank fills the frame. | Orbit widened at 2130/2180; it stays 1.2 m+ from the tanks. |
| 12 | 40.0–40.5 s / 2406–2440 | The sedated boy snaps from seated on the ledge to lying in the water with the diver (an in-view drift and spin). | Both hold their poses until the camera dives through the water surface at 2421 (water-line wipe), then continue as the tow. |
| 13 | 41.5 s / ~2491 | Camera inside rock or murk: a blank grey frame. | Tow camera re-keyed to travel ahead of the pair in open water. |
| 14 | 42.0–42.5 s / 2521–2551 | The boy's shoe soles fill the frame. | Camera ahead of the pair looking back: the diver's head and the boy's masked face lead. |
| 15 | 46.5–47.5 s / 2791–2851 | The back carrier's tanks fill the centre of the frame. | Camera moved to the side of the stretcher; the boy and both carriers read. |

Checked and fine: beats 1, 3–4 (cross-section), 7 (lone light), 10–11 (hands, grips, mask), 13–14 (carry-out, crowd, crane). The feet audit gives 0 hover/sink. Hands are as in v004 (the hand audit is clean apart from intended contacts).

## Re-check (v005)
- **Half-second sheet after:** `ACTING_v005_after_halfsec_a.jpg`/`_b.jpg` (rendered before the last lane tweak; the run beat was re-checked separately afterwards).
- **clip_scan:** 0 bad ranges. The only sub-threshold hit is 6 probe vertices of the back carrier's hand against the stretcher boy at f2773.
- **Extra fixes found by clip_scan:**
  - The running boys' pumping hands dipped into their own hips (7.9 s, 9.0 s), so the arm path moved out.
  - Runners' hands touched the boy beside them (8.2 s), so the lanes are wider (±0.7 m) with more spacing.
- **Hand close-ups:** `ACTING_v005_hand_closeups.jpg`. Grips and contacts are as in v004.

## Round 2 (director review of v005) → v006
| Item | Fix |
|---|---|
| Hand close-ups showed feet, blurs and black | `05_closeups.py` rewritten: a lit camera 0.4 m from the **hand** (wrist tail) for every hand action (19 shots). |
| Claw hand on the edge boy (10 s close-up) | Palms flat on the rock (`hand_poses` flat_palm). |
| Hand reaching into empty air (crowd) | The crowd now claps in front of the chest. The rescued boys and coach give an open-palm wave at head height. |
| 22–23 s murky water | Camera fill (no volume scatter) at 160 W underwater, with exposure lifted. |
| 29–30.5 s dark and blurred, then grey | A diver swims back up the passage ahead of the rising camera and surfaces beside the edge boy. The murk thins on the rise. |
| 18 s and 42.5 s rock fills the frame | Waterline key moved to the pool side, facing the boys. Tow exit re-keyed so the pair stays in frame until the wall entry (4-frame wipe). |
| 40.5 s tow with no one in frame | The camera turns back after the dive to find the pair swimming in. |
| Hand contacts | Every finger key now uses the shared `hand_poses.py` presets (relaxed, cup_hold, flat_palm, wrap_grip, pinch, tripod, shield) plus `add_hand_limits`. The mask fit and syringe use `grip_object`. |
| Printed logo on MPFB `male_casualsuit02` / `female_casualsuit02` / `female_casualsuit01` | Clothes swapped or flat-tinted (no logos). |

### qa_check (c6240b2) on the v006 package: remaining flags and why they stay
- **HOVER 0.**
- **CLAW 3** (DiverB, f2335–2365): in-between frames while his hands close on the mask rim between `grip_object` keys. The hands are on the mask; see `mask_fit_L/R` in the close-ups.
- **BACKHEAD 3:** f1 is the opening wide crane (the boys walk into the cave). f1489 and f1711 are beats 7 and 8 starting on the lone diver swimming away into the dark. The diver who died is deliberately never shown facing the camera.
- **EMPTY 262:**
  - 577–1015 and 2545–2725 are the mountain cutaway, which has no characters by design (route line, sumps, tiny figures).
  - The underwater ranges (1207–1513, 1555–1783, 2413–2527) show the divers in frame on the sheets, but the check's head/hand visibility rays are blocked in the narrow passage. Verified on the half-second sheet.
- **INSIDE 126 and FILL 3:**
  - The cutaway ranges are the camera inside the studio dome.
  - The tunnel and passage ranges are the camera inside the rock tubes, which are seen from inside by design. Flipping their normals made the count worse (216), so they were left as built.
  - FILL 577, 1009 and 1219 are the 4-frame rock-wipe entries and the water-line crossing.
