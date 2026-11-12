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
