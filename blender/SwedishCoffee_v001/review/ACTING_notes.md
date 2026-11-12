# SwedishCoffee: acting review (v004 → v005)

Reviewed `review/v004_half_A.jpg` + `review/v004_half_B.jpg`: every 30 frames, 270×480, 8 spp, rendered from the v004 package. Frames below are v004 frames; story-beat frames (beats.json) are unchanged in v005.

| # | v004 time (frames) | Problem | Fix in v005 |
|---|---|---|---|
| 1 | 2.4–2.9 s (145–175) | Camera flies **into a house façade** (wall fills the frame, camera inside the wall) to get to the throne hall. | Open-air **whip-pan** (110° in 24 frames) from above the crowd into the throne hall; the set swaps mid-whip, and the camera is never inside geometry. Swap moved to f158 so the king is on screen at beat 2 (f169). |
| 2 | 2.8 s (169, beat 2) | Beat "the king suddenly stopped it" lands mid-transition; the king isn't visible. | Swap at 158, whip lands on the throne by ~170; a new key at 185 frames the king's raised hand. |
| 3 | 9.5 s (570–588) | Steam pass then a blank wall/table; beat 4 (f583) is still in the throne hall. | Steam swap moved to f575, so beat 4 shows the street with the soldiers. |
| 4 | 11.5–12.0 s (690–716) | Camera flies **into a house wall** in the street (wall fills frame). | Open-air whip-pan into the chamber, swap at f705; beat 5 (f721) shows the twins at the table. |
| 5 | 13.7–20 s (823–1290) | Servants **"pour" with a pot that just hangs from the hand** at waist height, nowhere near a cup; coffee appears in the cup by itself. | Each servant walks the pot over the drinker's resting cup, tips it, and a coffee/tea stream runs into the cup for ~14 frames. Refills happen while the cup rests on the table between sips (3 refills for twin A, 2 for twin B). The drink cycle now sets the cup down and holds it ~20 frames. |
| 6 | 16.0–16.5 s (~960–990) | Camera passes right behind the servant's red dress (dress fills a third of the frame). | Servants moved back (y 1.30); camera key re-checked with the camera-proximity audit. |
| 7 | 24.0 s (~1440–1460) | Empty frame: wall and floor only, during the time-lapse pan. | Intermediate key at 1452 keeps the doctors in frame; checked on the new sheet. |
| 8 | 27.0–27.4 s (1620–1650) | Beat 9 "both doctors died first" (f1645) is still inside the chamber window. | Chamber → churchyard swap moved to f1630, so beat 9 shows the coffins. |
| 9 | 28–30 s (1680–1810) | **Coffins ride on the bearers' heads** (bottom at 1.38 m, heads at 1.6–1.75 m); the inner hands are inside the coffin side. | Coffins carried at **hip height** (bottom at 0.72 m), each bearer gripping the side rail with the inner hand, the outer arm swinging. |
| 10 | 30.0–31.0 s (1800–1872) | Camera flies **into the cathedral façade** (wall fills frame); beat 10 (f1867) is still at the church. | Open-air whip-pan into the ballroom, swap at f1850; beat 10 shows the ball and the king. |
| 11 | 31.5–33 s (1872–1912) | **Dancers walk small solo circles** (six people each circling alone): not a dance. | Three **couples** face each other, joined raised hands, turning slowly around the couple's centre with stepping feet. At the shot they let go and hurry away from the king. |
| 12 | 33.0 s (1980–2004) | Beat 11 "the tea-drinking twin died" (f1999) lands in the doorway pass. | Ballroom → bedroom swap moved to f1985. |
| 13 | 34–38 s (2004–2230) | **Bedside: twin A's hand floats** at the bed edge touching nothing; B's hands are hidden under the blanket. Camera passes very close to A's back (36–36.5 s). | B's right hand rests on top of the blanket; A (chair moved closer, x −1.22) leans in and lays his hand on B's hand (hand target computed from B's hand bone every key). Camera proximity checked. |
| 14 | 37.0 s (2227, beat 12) | Beat "coffee drinker as the last survivor" frames the window/wall, not the old twin. | Key at 2225 now frames the very old twin with his cup. |
| 15 | 41.0–41.5 s (2460–2508) | Beat 13 "the ban on coffee was lifted" (f2503) is still in the bedroom window pass. | Bedroom → square swap moved to f2490. |
| 16 | 28–31 s | Cathedral roof band renders black (Sketchfab materials). | Still open; see README. Fewer frames now (the set ends at 1850). |
| 17 | 32.0–32.5 s (1916–1950) | King's collapse: the hand clutching his chest goes into the chest; once he's lying, both hands are inside his legs. | Knee buckle → kneel → fold onto his side kept. The chest hand rests on the coat surface, and the lying hands are placed flat on the floor beside his shoulders (computed from his shoulder bones, arms out from the body). |
| 18 | 1.4–2.5 s (85–157) | Scaffold guard's idle hand is inside his hip (clip scan: 102 points). | Idle hands for every character sit wider and slightly forward (x 0.35, y −0.11), so the fingers hang beside the coat, not in it. |
| 19 | 11.2–11.5 s (673–691) | A protester's lowering fist swings through his thigh (clip scan). | The jeer's "fist down" position is wider and forward, so the arm swings in front of the body. |
| 20 | 21–24 s (1261–1459) | The two doctors' writing hands meet in the middle of the desk (clip scan: hand inside the other doctor). | Doctors moved apart (x 2.35 / 3.65). |
| 21 | 2.0–2.5 s (121–151, v005 draft) | First whip passed within half a metre of a twin's head and through the noose. | Whip start moved to the side of the gallows (4.6, −1.2, 4.2), clear of the structure. |
| 22 | 32.5–33 s (v005 draft) | A fleeing dancer ran into the lens; the doorway pass looked straight at a flat corridor wall. | Shorter scatter (1.7 m); ballroom → bedroom is an open-air whip starting on the fleeing dancers, ending looking down onto the bed so beat 11 shows the dying twin. |
| 23 | 37.3–40.9 s (v005 draft) | Camera brushed the doctor beside the bed and the very old twin's head (camera-proximity check). | Doctor moved to the far side of the bed; a camera key at 2448 passes clear of the old twin. |

Not changed (checked, plausible): soldier smashing the pot (both hands on it, shards on impact); the sack pour (beans from the sack mouth); crowd jeering/toasting with planted feet and weight shifts; doctors writing and looking up; the old twin's sips by the window (cup in a curled hand, to the lips and back).


## Re-check (v005 package)
- Half-second sheets: before `v004_half_A/B.jpg`, after `v005_half_A/B.jpg`. Hand close-ups (20 hand contacts): `v005_hand_closeups.jpg`.
- `pipeline/clip_scan.py` (director, unchanged): **bad ranges []** → `v005_clip_scan_director.json`.
  - This film swaps sets with `hide_render` keys and moves characters by their root bone. The unchanged script therefore only sees the 14 courtyard characters (it collects characters by visibility at frame 1).
  - `scripts/clip_scan_setaware.py` is the same scan with per-frame visibility and the root-bone position, covering all 73 characters: **bad ranges [[1915, 1915]]** → `v005_clip_scan_setaware.json`.
  - The one remaining frame is f1915 (31.9 s): the king's hand on his chest during the first frames of the knee buckle, a single 6-frame sample below the 25-point range threshold elsewhere.
- `pipeline/qa_check.py` (c6240b2), unchanged → `v005_qa_check_director.json`: BACKHEAD 2, EMPTY 241, FILL 19, INSIDE 34.
  - Almost all of these come from hidden sets: the script ray-casts the viewport, where every set is present at once. For example, it reports the church in the ballroom and in the square.
- Re-run with viewport visibility synced to render visibility each frame (`scripts/qa_setaware.py`, qa_check itself unchanged) → `v005_qa_check_setaware.json`: **INSIDE 0, FILL 0**, BACKHEAD 1, EMPTY 206.
  - All 206 EMPTY are "no character in view" from f169 on, because qa_check builds its character list at frame 1 (only the courtyard cast renders then). They are not empty frames: see the after sheets.
  - BACKHEAD 1 is f1: the camera starts behind the crowd facing the scaffold.
- `scripts/cam_proximity.py` (camera within 0.35 m of any character's bone axis, every 3 frames): 1 borderline sample (f1939, the masked figure's forearm at 0.30 m as he turns away).


## v006 (director review of v005)
- **Hands:** all hands use `pipeline/hand_poses.py` (add_hand_limits plus the pose table): relaxed idle hands, wrap grips on the pots and the couple's joined hands, flat palms for the king (raised hand and on the floor), a fist for the masked man. Close-ups: `v006_hand_closeups.jpg`. Two close-ups (3: sack pour, 13: coffin grip) still render black from every tested camera position; not resolved.
- **Empty cells:** 7.5–9 s now holds the king behind the cup and the steam; 31–33 s couples are closer to the camera; 40.5 s holds on the old twin; the square starts closer.
  - Still weak: 9.5 s (table and cup), 26.5–27 s (wall, then house façades through the window), 41.0 s (façade through the window).
- **Cathedral roof:** roof faces reassigned to our roof material, but the band still renders black at 27.5–30 s. Not resolved.
- **QA:** `v006_qa_check_director.json` (unchanged script) and `v006_qa_check_setaware.json` (viewport synced to render each frame): INSIDE 0, FILL 0. EMPTY are all "no character in view" (character list built at frame 1). BACKHEAD 1 is f1 (intended).
- Ledger cover changed to plain leather (the model's spine had lettering).


## v007 (director review of v006)
- **Cathedral roof band:** not a holdout, shadow catcher, unconnected output or culled material (checked in that order). The faces are recessed under the eaves and receive no light, so they render black. Fix: the roof faces use our slate roof material and the recessed band faces our stone, both with a gentle self-illumination (emission 0.6 of their own texture), so they read as dark slate and stone at 27.5–30 s.
- **Empty cells:**
  - 9.5 s: the steam pass now looks through the steam toward the king (exit yaw −29°).
  - 26.5–27.0 s: the camera holds on the twins and servants until 8 frames before the window, then whips out.
  - 41.0 s: same treatment for the very old twin; the cell now lands on the whip, showing the side table, candle and the twin at the edge.
- **Close-up 2:** `grip_object` on the soldier's pot at every pot key; both hands wrap the pot.
- **Found on review and fixed:**
  - The old twins walking behind the coffins held their arms out (their hand targets didn't follow the walk).
  - The guard who runs out of the throne hall had the same bug.
  - The coffin bearers walked inside the coffin's width, with their inner hands inside their own hips. They now walk at ±0.55 m with the hand on the side rail.
- **Re-check:**
  - set-aware clip scan: bad ranges [(1915, 1915)], a single sample of a fleeing dancer's raised hands.
  - camera proximity: 1 sample at 0.31 m.
  - qa_check set-aware: INSIDE 0, FILL 0, BACKHEAD 1 (f1, intended), EMPTY 413 (all "no character in view", character list built at frame 1).
  - qa_check unchanged: INSIDE 74, FILL 42, EMPTY 525, BACKHEAD 2 (hidden sets).
  - Close-ups 3 and 13 are still black review images; the film frames at those moments are fine (see the sheets).


## v008 (director review of v007/v006, 7 items)
1. **Cathedral roof band:** the roof faces use our slate material, the recessed band our stone; both self-lit at 0.6 of their own texture. At 28.5 s it reads as dark slate over light stone, with no black band (see `v008_half_B.jpg`, 27.5–30 s, and `v008_f1711_28p5s.jpg`). The upper roof is still very dark (textured dark slate, not flat black). If it should be lighter, the plain slab at base 0.35/0.33/0.30 is a one-line change.
2. **Close-ups 3 (sack pour) and 13 (coffin grip): dropped.** In the film both contacts are hidden behind the bodies from the film camera. A camera placed 0.5–0.8 m from the hand on the film-camera side with line of sight to the wrist doesn't exist: every candidate direction hits the character's own torso or the sack/coffin first. They aren't seen in any frame of the film, so the close-up sheet has 18 shots instead of 20.
3. **Close-up 1 (blue twin's shackled hand):** now `relaxed` from hand_poses (no splay).
4–5. **Servants' pots (red silver pot, green porcelain pot): NOT fixed in v008.** I applied `wrap_grip` on the pot body, not `grip_object` on the handle. In `v008_hand_closeups.jpg` (cells 3.0 s and 4.0 s) the hand is still hidden behind the pot; only the sleeve shows. Next: `grip_object` on each pot's handle at every pour key (v009).
6. **Empty cells:**
   - 26.5 and 27.0 s: the camera holds on the twins and the green servant until 8 frames before the window.
   - 31.0 s: the ball opens on the couples (closer to the camera).
   - 41.0 s: the old twin stays in frame until the window whip.
   - 9.5 s is the coffee-cup-and-steam beat (kept on purpose).
7. **qa_check EMPTY:** the toggle was **viewport visibility**. Sets were swapped only with `hide_render` keys. qa_check's scene ray casts use the viewport depsgraph, so every hidden set was still there and blocked the rays (example: f900, the ray hit `house3_i.001` from the street set inside the chamber).
   - v008 keys `hide_viewport` together with `hide_render` on every set, portal plane and swap. qa_check now runs unchanged and no wrapper is needed.
   - Room walls also faced outward (normals), which gave the INSIDE flags; they now face inward.
   - Result with the unchanged `pipeline/qa_check.py` → `v008_qa_check_director.json`: **BACKHEAD 2, EMPTY 24, INSIDE 1, FILL 2** (was INSIDE 74, FILL 42, EMPTY 525 on v007).
   - INSIDE 1 and FILL 2 are f577, the steam pass: the camera passes through the steam volume on purpose.
   - BACKHEAD: f1 is the opening behind the crowd; f169 is the guard nearest the camera while the king (the subject) faces it.
   - EMPTY 24 are frames where the characters are small or partly framed, which the script counts as no character:
     - 8.6–9.5 s: the cup-and-steam beat;
     - 10.7–11 s: street soldiers far off;
     - ~35–36.8 s: the dying twin under the blanket;
     - single whip frames at 20.8, 27.1, 30.4–30.6 and 41.4 s.
- Found on review and fixed: the king's raised hand is `relaxed` (it read as splayed); the front bed curtains were removed (they filled the frame at 34–36 s).
